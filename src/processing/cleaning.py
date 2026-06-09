from __future__ import annotations

import re

import pandas as pd


CANONICAL_COLUMNS = {
    "date": [
        "date",
        "price_date",
        "arrival_date",
        "reported_date",
        "pricedate",
        "dt_date",
    ],
    "state": ["state", "state_name", "statename"],
    "district": ["district", "district_name", "districtname"],
    "market": ["market", "market_name", "mandi", "mandi_name", "marketname"],
    "commodity": ["commodity", "commodity_name", "crop", "crop_name", "commodityname"],
    "variety": ["variety", "variety_name", "varietyname"],
    "grade": ["grade", "grade_name", "gradename"],
    "min_price": ["min_price", "minimum_price", "min price", "minprice", "min_pr"],
    "max_price": ["max_price", "maximum_price", "max price", "maxprice", "max_pr"],
    "modal_price": ["modal_price", "modal price", "modalprice", "modal_pr", "price"],
    "arrivals_tonnes": [
        "arrivals_tonnes",
        "arrival_tonnes",
        "arrivals",
        "arrival",
        "quantity",
        "arrivals_in_tonnes",
    ],
}


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_lookup = {_normalize_name(col): col for col in df.columns}
    rename_map = {}

    for canonical, aliases in CANONICAL_COLUMNS.items():
        for alias in aliases:
            normalized_alias = _normalize_name(alias)
            if normalized_alias in normalized_lookup:
                rename_map[normalized_lookup[normalized_alias]] = canonical
                break

    return df.rename(columns=rename_map)


def parse_market_dates(values: pd.Series) -> pd.Series:
    """Parse common AGMARKNET/Kaggle date formats without flipping month/day.

    Some exports use DD-MM-YYYY, while this Kaggle historical file uses
    MM/DD/YYYY. We choose the date order from unambiguous samples.
    """
    text_values = values.astype(str).str.strip()
    parsed_iso = pd.to_datetime(text_values, format="%Y-%m-%d", errors="coerce")
    remaining = parsed_iso.isna()
    if not remaining.any():
        return parsed_iso

    slash_or_dash = text_values[remaining].str.extract(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$")
    first = pd.to_numeric(slash_or_dash[0], errors="coerce")
    second = pd.to_numeric(slash_or_dash[1], errors="coerce")

    day_first_votes = int((first > 12).sum())
    month_first_votes = int((second > 12).sum())
    dayfirst = day_first_votes > month_first_votes

    parsed_remaining = pd.to_datetime(
        text_values[remaining],
        dayfirst=dayfirst,
        errors="coerce",
    )
    parsed_iso.loc[remaining] = parsed_remaining
    return parsed_iso


def clean_market_data(df: pd.DataFrame, source: str = "uploaded") -> pd.DataFrame:
    df = standardize_columns(df).copy()

    required = ["date", "state", "district", "market", "commodity", "modal_price"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns after standardization: {missing}")

    df["date"] = parse_market_dates(df["date"])

    for col in ["min_price", "max_price", "modal_price", "arrivals_tonnes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "min_price" not in df.columns:
        df["min_price"] = df["modal_price"]
    if "max_price" not in df.columns:
        df["max_price"] = df["modal_price"]
    if "arrivals_tonnes" not in df.columns:
        df["arrivals_tonnes"] = pd.NA

    for col in ["state", "district", "market", "commodity", "variety", "grade"]:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = (
            df[col]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    df["source"] = df.get("source", source)
    df["source"] = df["source"].fillna(source).astype(str)

    df = df.dropna(subset=["date", "modal_price"])
    df = df[df["modal_price"] > 0]
    df = df[df["min_price"] <= df["max_price"]]

    sort_cols = ["date", "state", "district", "market", "commodity", "variety", "grade"]
    df = df.drop_duplicates(subset=sort_cols, keep="last")
    df = df.sort_values(sort_cols).reset_index(drop=True)

    return df[
        [
            "date",
            "state",
            "district",
            "market",
            "commodity",
            "variety",
            "grade",
            "min_price",
            "max_price",
            "modal_price",
            "arrivals_tonnes",
            "source",
        ]
    ]
