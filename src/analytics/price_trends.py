from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_float(value: object, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add trend, volatility, and anomaly features to a single time series."""
    if df.empty:
        return df.copy()

    result = df.sort_values("date").copy()
    result["ma_7"] = result["modal_price"].rolling(7, min_periods=1).mean()
    result["ma_30"] = result["modal_price"].rolling(30, min_periods=1).mean()
    result["ma_90"] = result["modal_price"].rolling(90, min_periods=1).mean()
    result["wow_change_pct"] = result["modal_price"].pct_change(7) * 100
    result["mom_change_pct"] = result["modal_price"].pct_change(30) * 100
    result["volatility_14"] = result["modal_price"].rolling(14, min_periods=2).std()
    result["volatility_pct"] = result["volatility_14"] / result["ma_30"].replace(0, np.nan) * 100

    rolling_mean = result["modal_price"].rolling(30, min_periods=10).mean()
    rolling_std = result["modal_price"].rolling(30, min_periods=10).std()
    result["anomaly"] = (result["modal_price"] - rolling_mean).abs() > (2 * rolling_std)
    result["anomaly"] = result["anomaly"].fillna(False)
    result["volatility_label"] = result["volatility_pct"].apply(label_volatility)

    return result


def add_grouped_price_features(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["state", "district", "market", "commodity", "variety", "grade"]
    available_group_cols = [col for col in group_cols if col in df.columns]
    if not available_group_cols:
        return add_price_features(df)

    return (
        df.groupby(available_group_cols, group_keys=False)
        .apply(add_price_features)
        .reset_index(drop=True)
    )


def label_volatility(volatility_pct: float | int | None) -> str:
    if pd.isna(volatility_pct):
        return "Unknown"
    if volatility_pct >= 12:
        return "High"
    if volatility_pct >= 5:
        return "Medium"
    return "Low"


def latest_market_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "current_price": 0.0,
            "ma_7": 0.0,
            "ma_30": 0.0,
            "wow_change_pct": 0.0,
            "mom_change_pct": 0.0,
            "volatility_label": "Unknown",
            "volatility_pct": 0.0,
            "max_30d": 0.0,
            "min_30d": 0.0,
            "avg_30d": 0.0,
            "arrival_change_pct": 0.0,
            "latest_arrivals_tonnes": 0.0,
        }

    featured = add_price_features(df)
    latest = featured.iloc[-1]
    last_30 = featured.tail(30)

    arrival_change_pct = 0.0
    if "arrivals_tonnes" in featured.columns and featured["arrivals_tonnes"].notna().sum() >= 8:
        current_arrival = featured["arrivals_tonnes"].tail(7).mean()
        previous_arrival = featured["arrivals_tonnes"].iloc[-14:-7].mean()
        if previous_arrival and not pd.isna(previous_arrival):
            arrival_change_pct = ((current_arrival - previous_arrival) / previous_arrival) * 100

    return {
        "current_price": round(_safe_float(latest["modal_price"]), 2),
        "ma_7": round(_safe_float(latest.get("ma_7", 0)), 2),
        "ma_30": round(_safe_float(latest.get("ma_30", 0)), 2),
        "wow_change_pct": round(_safe_float(latest.get("wow_change_pct", 0)), 2),
        "mom_change_pct": round(_safe_float(latest.get("mom_change_pct", 0)), 2),
        "volatility_label": str(latest.get("volatility_label", "Unknown")),
        "volatility_pct": round(_safe_float(latest.get("volatility_pct", 0)), 2),
        "max_30d": round(_safe_float(last_30["modal_price"].max()), 2),
        "min_30d": round(_safe_float(last_30["modal_price"].min()), 2),
        "avg_30d": round(_safe_float(last_30["modal_price"].mean()), 2),
        "arrival_change_pct": round(float(arrival_change_pct), 2),
        "latest_arrivals_tonnes": round(_safe_float(latest.get("arrivals_tonnes", 0)), 2),
    }


def compare_markets(df: pd.DataFrame, commodity: str, state: str | None = None) -> pd.DataFrame:
    filtered = df[df["commodity"].str.lower() == commodity.lower()].copy()
    if state:
        filtered = filtered[filtered["state"].str.lower() == state.lower()]
    if filtered.empty:
        return pd.DataFrame(columns=["state", "district", "market", "avg_price", "latest_price", "volatility", "data_points"])

    latest_date = filtered["date"].max()
    recent = filtered[filtered["date"] >= latest_date - pd.Timedelta(days=30)]

    comparison = (
        recent.groupby(["state", "district", "market"], as_index=False)
        .agg(
            avg_price=("modal_price", "mean"),
            latest_price=("modal_price", "last"),
            volatility=("modal_price", "std"),
            arrivals_tonnes=("arrivals_tonnes", "mean"),
            data_points=("modal_price", "size"),
        )
        .sort_values("avg_price", ascending=False)
    )
    comparison["avg_price"] = comparison["avg_price"].round(2)
    comparison["latest_price"] = comparison["latest_price"].round(2)
    comparison["volatility"] = comparison["volatility"].fillna(0).round(2)
    comparison["arrivals_tonnes"] = comparison["arrivals_tonnes"].fillna(0).round(2)
    return comparison.reset_index(drop=True)


def top_price_movers(df: pd.DataFrame, days: int = 7, limit: int = 8) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    latest_date = df["date"].max()
    recent = df[df["date"] >= latest_date - pd.Timedelta(days=days + 1)]
    if recent.empty:
        return pd.DataFrame()

    grouped = (
        recent.sort_values("date")
        .groupby(["state", "market", "commodity"])
        .agg(first_price=("modal_price", "first"), last_price=("modal_price", "last"), data_points=("modal_price", "size"))
        .reset_index()
    )
    grouped = grouped[grouped["data_points"] >= 2]
    grouped["change_pct"] = (grouped["last_price"] - grouped["first_price"]) / grouped["first_price"] * 100
    return grouped.sort_values("change_pct", ascending=False).head(limit).reset_index(drop=True)
