from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from src.analytics.dataset_profile import forecast_ready_groups
from src.config import CHROMA_DIR, RAG_COLLECTION_NAME, RAG_EMBEDDING_DIMENSIONS


TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashEmbeddingFunction:
    """Small deterministic embedding function for local ChromaDB demos.

    This avoids downloading external embedding models during the hackathon demo.
    It is not semantically as rich as a transformer embedding, but it is stable,
    offline, and good enough for retrieving commodity/market/context documents.
    """

    def __call__(self, input):  # ChromaDB expects this exact argument name.
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * RAG_EMBEDDING_DIMENSIONS
        tokens = TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % RAG_EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


@dataclass
class RAGDocument:
    id: str
    text: str
    metadata: dict


def _slug(*parts: object) -> str:
    joined = "_".join(str(part) for part in parts)
    return re.sub(r"[^a-z0-9]+", "_", joined.lower()).strip("_")


def build_market_documents(df: pd.DataFrame, min_dates: int = 90, limit: int = 500) -> list[RAGDocument]:
    ready = forecast_ready_groups(df, min_dates=min_dates, limit=limit)
    documents: list[RAGDocument] = []

    for _, row in ready.iterrows():
        mask = (
            (df["commodity"] == row["commodity"])
            & (df["state"] == row["state"])
            & (df["district"] == row["district"])
            & (df["market"] == row["market"])
        )
        series = df.loc[mask].sort_values("date")
        if series.empty:
            continue

        latest = series.iloc[-1]
        first = series.iloc[0]
        avg_price = float(series["modal_price"].mean())
        min_price = float(series["modal_price"].min())
        max_price = float(series["modal_price"].max())
        latest_price = float(latest["modal_price"])
        first_price = float(first["modal_price"])
        overall_change = ((latest_price - first_price) / first_price * 100) if first_price else 0.0

        doc_text = f"""
Commodity market knowledge document.
Commodity: {row['commodity']}
State: {row['state']}
District: {row['district']}
Market/Mandi: {row['market']}
Date coverage: {row['start'].date()} to {row['end'].date()}
Unique dates: {int(row['dates'])}
Rows: {int(row['rows'])}
Latest modal price: INR {latest_price:.2f} per quintal
Average modal price: INR {avg_price:.2f} per quintal
Minimum modal price: INR {min_price:.2f} per quintal
Maximum modal price: INR {max_price:.2f} per quintal
Overall price change from first to latest record: {overall_change:.2f} percent
This document is useful for answering questions about price history, market comparison, mandi opportunity, and commodity-specific selling strategy.
""".strip()

        metadata = {
            "commodity": str(row["commodity"]),
            "state": str(row["state"]),
            "district": str(row["district"]),
            "market": str(row["market"]),
            "dates": int(row["dates"]),
            "rows": int(row["rows"]),
            "start": row["start"].date().isoformat(),
            "end": row["end"].date().isoformat(),
            "latest_price": latest_price,
            "avg_price": avg_price,
        }
        doc_id = _slug(row["commodity"], row["state"], row["district"], row["market"])
        documents.append(RAGDocument(id=doc_id, text=doc_text, metadata=metadata))

    return documents


class MarketRAGStore:
    def __init__(self, path: str | None = None, collection_name: str = RAG_COLLECTION_NAME):
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        try:
            import chromadb
            from chromadb.config import Settings
        except Exception as exc:
            raise RuntimeError("ChromaDB is not installed. Run: python -m pip install chromadb==0.5.23") from exc

        self.path = str(path or CHROMA_DIR)
        self.embedding_function = HashEmbeddingFunction()
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def reset(self) -> None:
        name = self.collection.name
        try:
            self.client.delete_collection(name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_documents(self, documents: Iterable[RAGDocument]) -> int:
        docs = list(documents)
        if not docs:
            return 0

        self.collection.upsert(
            ids=[doc.id for doc in docs],
            documents=[doc.text for doc in docs],
            metadatas=[doc.metadata for doc in docs],
        )
        return len(docs)

    def query(
        self,
        question: str,
        commodity: str | None = None,
        state: str | None = None,
        n_results: int = 4,
    ) -> list[dict]:
        where = None
        if commodity and state:
            where = {"$and": [{"commodity": commodity}, {"state": state}]}
        elif commodity:
            where = {"commodity": commodity}
        elif state:
            where = {"state": state}

        kwargs = {
            "query_texts": [question],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        result = self.collection.query(**kwargs)
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        matches = []
        for doc, metadata, distance in zip(docs, metadatas, distances):
            matches.append({"document": doc, "metadata": metadata, "distance": distance})
        return matches


def format_rag_matches(matches: list[dict]) -> str:
    if not matches:
        return "No vector-store matches found."

    blocks = []
    for index, match in enumerate(matches, start=1):
        metadata = match.get("metadata", {})
        blocks.append(
            f"Retrieved document {index} "
            f"({metadata.get('commodity')} | {metadata.get('state')} | "
            f"{metadata.get('district')} | {metadata.get('market')}):\n"
            f"{match.get('document')}"
        )
    return "\n\n".join(blocks)
