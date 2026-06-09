from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.genai.rag_store import MarketRAGStore, build_market_documents
from src.ingestion.data_loader import load_market_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChromaDB RAG index from MarketMitra mandi data.")
    parser.add_argument("--min-dates", type=int, default=90, help="Minimum unique dates per market series.")
    parser.add_argument("--limit", type=int, default=500, help="Maximum market documents to index.")
    parser.add_argument("--reset", action="store_true", help="Delete existing collection before indexing.")
    args = parser.parse_args()

    df = load_market_data(force_rebuild=False)
    docs = build_market_documents(df, min_dates=args.min_dates, limit=args.limit)

    store = MarketRAGStore()
    if args.reset:
        store.reset()

    inserted = store.upsert_documents(docs)
    print(f"Built RAG index with {inserted} documents.")
    print(f"Collection count: {store.count()}")


if __name__ == "__main__":
    main()

