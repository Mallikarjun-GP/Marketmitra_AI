from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.cleaning import clean_market_data


DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_OUTPUT = DEFAULT_RAW_DIR / "final_marketmitra_dataset.csv"


def prepare_final_dataset(raw_dir: Path, output: Path) -> None:
    csv_files = sorted(path for path in raw_dir.glob("*.csv") if path.resolve() != output.resolve())
    if not csv_files:
        raise FileNotFoundError(f"No original CSV files found in {raw_dir}")

    cleaned_frames = []
    for csv_file in csv_files:
        print(f"Reading {csv_file}")
        raw = pd.read_csv(csv_file)
        cleaned = clean_market_data(raw, source=csv_file.stem)
        cleaned_frames.append(cleaned)

    combined = pd.concat(cleaned_frames, ignore_index=True)
    combined = combined.sort_values(["date", "state", "district", "market", "commodity", "variety", "grade"])
    combined = combined.drop_duplicates(
        subset=["date", "state", "district", "market", "commodity", "variety", "grade"],
        keep="last",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False, encoding="utf-8")
    print(f"Saved final dataset with {len(combined)} rows to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine original mandi CSV files into one final MarketMitra dataset.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="Folder containing original CSV files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Final combined CSV path.")
    args = parser.parse_args()

    prepare_final_dataset(Path(args.raw_dir), Path(args.output))


if __name__ == "__main__":
    main()
