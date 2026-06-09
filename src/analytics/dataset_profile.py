from __future__ import annotations

import pandas as pd


def dataset_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "rows": 0,
            "date_min": None,
            "date_max": None,
            "states": 0,
            "districts": 0,
            "markets": 0,
            "commodities": 0,
        }

    return {
        "rows": int(len(df)),
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "states": int(df["state"].nunique()),
        "districts": int(df["district"].nunique()),
        "markets": int(df["market"].nunique()),
        "commodities": int(df["commodity"].nunique()),
    }


def forecast_ready_groups(df: pd.DataFrame, min_dates: int = 120, limit: int = 50) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    group_cols = ["commodity", "state", "district", "market"]
    groups = (
        df.groupby(group_cols)
        .agg(
            rows=("modal_price", "size"),
            dates=("date", "nunique"),
            start=("date", "min"),
            end=("date", "max"),
            avg_price=("modal_price", "mean"),
        )
        .reset_index()
    )
    groups = groups[groups["dates"] >= min_dates]
    groups["avg_price"] = groups["avg_price"].round(2)
    return groups.sort_values(["dates", "rows"], ascending=False).head(limit).reset_index(drop=True)


def format_group_label(row: pd.Series) -> str:
    return (
        f"{row['commodity']} | {row['state']} | {row['district']} | {row['market']} "
        f"({int(row['dates'])} dates)"
    )

