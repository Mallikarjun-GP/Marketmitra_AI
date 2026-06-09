from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PROCESSED_CSV_PATH, PROCESSED_PARQUET_PATH, RAW_DATA_DIR
from src.processing.cleaning import clean_market_data


def _read_any_processed() -> pd.DataFrame | None:
    if PROCESSED_PARQUET_PATH.exists():
        try:
            return pd.read_parquet(PROCESSED_PARQUET_PATH)
        except Exception:
            pass

    if PROCESSED_CSV_PATH.exists():
        return pd.read_csv(PROCESSED_CSV_PATH, parse_dates=["date"])

    return None


def _save_processed(df: pd.DataFrame) -> None:
    PROCESSED_PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(PROCESSED_PARQUET_PATH, index=False)
    except Exception:
        df.to_csv(PROCESSED_CSV_PATH, index=False)


def discover_raw_csvs(raw_dir: Path = RAW_DATA_DIR) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    return sorted(raw_dir.glob("*.csv"))


def load_first_raw_csv() -> pd.DataFrame | None:
    csv_files = discover_raw_csvs()
    if not csv_files:
        return None

    final_dataset = RAW_DATA_DIR / "final_marketmitra_dataset.csv"
    if final_dataset.exists():
        return pd.read_csv(final_dataset)

    # Use the newest file so teams can replace data without changing code.
    path = max(csv_files, key=lambda p: p.stat().st_mtime)
    return pd.read_csv(path)


def build_processed_dataset(force_rebuild: bool = False) -> pd.DataFrame:
    if not force_rebuild:
        existing = _read_any_processed()
        if existing is not None and not existing.empty:
            existing["date"] = pd.to_datetime(existing["date"])
            return existing

    raw_df = load_first_raw_csv()
    if raw_df is None:
        raise FileNotFoundError(
            "No original dataset found. Place an AGMARKNET/data.gov.in/Kaggle CSV file in data/raw/ "
            "and reload the app. Synthetic or demo data fallback is disabled for hackathon compliance."
        )

    cleaned = clean_market_data(raw_df, source="original_dataset")

    _save_processed(cleaned)
    return cleaned


def load_market_data(force_rebuild: bool = False) -> pd.DataFrame:
    return build_processed_dataset(force_rebuild=force_rebuild)


def filter_market_data(
    df: pd.DataFrame,
    commodity: str | None = None,
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
) -> pd.DataFrame:
    filtered = df.copy()

    for col, value in {
        "commodity": commodity,
        "state": state,
        "district": district,
        "market": market,
    }.items():
        if value and col in filtered.columns:
            filtered = filtered[filtered[col].str.lower() == value.lower()]

    return filtered.sort_values("date").reset_index(drop=True)
