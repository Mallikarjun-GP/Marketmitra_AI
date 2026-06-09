from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.data_loader import load_market_data


def evaluate_series(series: pd.DataFrame, horizon: int) -> dict:
    data = series.sort_values("date")[["date", "modal_price"]].dropna()
    daily = data.groupby("date", as_index=False)["modal_price"].mean().sort_values("date")
    if len(daily) < horizon + 45:
        return {}

    train = daily.iloc[:-horizon]
    test = daily.iloc[-horizon:]

    # Robust baseline used when Prophet is unavailable: recent rolling average + simple trend.
    rolling_mean = train["modal_price"].tail(7).mean()
    if len(train) >= 21:
        trend = (train["modal_price"].tail(7).mean() - train["modal_price"].tail(21).head(7).mean()) / 14
    else:
        trend = 0.0

    pred = np.array([rolling_mean + trend * (i + 1) for i in range(horizon)])
    actual = test["modal_price"].to_numpy(dtype=float)
    errors = actual - pred
    nonzero = actual != 0
    mape = np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))

    return {
        "mape": float(mape),
        "mae": float(mae),
        "rmse": float(rmse),
        "train_days": int(len(train)),
        "test_days": int(len(test)),
    }


def evaluate_series_prophet(series: pd.DataFrame, horizon: int) -> dict:
    try:
        from prophet import Prophet
    except Exception as exc:
        raise RuntimeError("Prophet is not installed. Run: python -m pip install prophet") from exc

    data = series.sort_values("date")[["date", "modal_price"]].dropna()
    daily = data.groupby("date", as_index=False)["modal_price"].mean().sort_values("date")
    if len(daily) < horizon + 60:
        return {}

    prophet_df = daily.rename(columns={"date": "ds", "modal_price": "y"})
    train = prophet_df.iloc[:-horizon]
    test = prophet_df.iloc[-horizon:]

    model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.8,
    )
    model.fit(train)
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)

    pred = forecast.tail(horizon)["yhat"].to_numpy(dtype=float)
    actual = test["y"].to_numpy(dtype=float)
    errors = actual - pred
    nonzero = actual != 0
    mape_score = np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))

    return {
        "mape": float(mape_score),
        "mae": float(mae),
        "rmse": float(rmse),
        "train_days": int(len(train)),
        "test_days": int(len(test)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MarketMitra baseline forecast accuracy.")
    parser.add_argument("--horizon", type=int, default=7, help="Forecast horizon in days.")
    parser.add_argument("--min-dates", type=int, default=120, help="Minimum unique dates per commodity-market series.")
    parser.add_argument("--max-series", type=int, default=50, help="Maximum number of series to evaluate in overall mode.")
    parser.add_argument("--series-per-commodity", type=int, default=10, help="Series per commodity in balanced mode.")
    parser.add_argument("--overall", action="store_true", help="Evaluate strongest overall series instead of balanced commodity coverage.")
    parser.add_argument("--model", choices=["baseline", "prophet"], default="baseline", help="Forecast model to evaluate.")
    args = parser.parse_args()

    df = load_market_data(force_rebuild=False)
    group_cols = ["commodity", "state", "district", "market"]
    all_candidates = (
        df.groupby(group_cols)
        .agg(rows=("modal_price", "size"), dates=("date", "nunique"))
        .query("dates >= @args.min_dates")
        .sort_values(["dates", "rows"], ascending=False)
        .reset_index()
    )

    if args.overall:
        candidates = all_candidates.head(args.max_series)
    else:
        candidates = (
            all_candidates.groupby("commodity", group_keys=False)
            .head(args.series_per_commodity)
            .reset_index(drop=True)
        )

    results = []
    for _, row in candidates.iterrows():
        mask = (
            (df["commodity"] == row["commodity"])
            & (df["state"] == row["state"])
            & (df["district"] == row["district"])
            & (df["market"] == row["market"])
        )
        if args.model == "prophet":
            metrics = evaluate_series_prophet(df.loc[mask], horizon=args.horizon)
        else:
            metrics = evaluate_series(df.loc[mask], horizon=args.horizon)
        if metrics:
            results.append({**row.to_dict(), **metrics})

    if not results:
        raise RuntimeError("No forecast-ready series found.")

    result_df = pd.DataFrame(results)
    mode = "overall strongest series" if args.overall else "balanced commodity coverage"
    print(f"Evaluated {len(result_df)} series with {args.horizon}-day horizon ({mode}, model={args.model})")
    print()
    print("Overall accuracy")
    print(f"Median MAPE: {result_df['mape'].median():.2f}%")
    print(f"Mean MAPE:   {result_df['mape'].mean():.2f}%")
    print(f"Approx Median Accuracy: {max(0, 100 - result_df['mape'].median()):.2f}%")
    print(f"Approx Mean Accuracy:   {max(0, 100 - result_df['mape'].mean()):.2f}%")
    print(f"Median MAE:  INR {result_df['mae'].median():.2f}/quintal")
    print(f"Mean MAE:    INR {result_df['mae'].mean():.2f}/quintal")
    print(f"Median RMSE: INR {result_df['rmse'].median():.2f}/quintal")
    print(f"Mean RMSE:   INR {result_df['rmse'].mean():.2f}/quintal")
    print()
    print("By commodity")
    by_commodity = result_df.groupby("commodity").agg(
        series=("market", "count"),
        median_mape=("mape", "median"),
        mean_mape=("mape", "mean"),
        median_mae=("mae", "median"),
    )
    print(by_commodity.round(2).to_string())
    print()
    print("Best series")
    print(
        result_df.sort_values("mape")
        [["commodity", "state", "district", "market", "dates", "mape", "mae", "rmse"]]
        .head(10)
        .round(2)
        .to_string(index=False)
    )
    print()
    print("Worst series")
    print(
        result_df.sort_values("mape", ascending=False)
        [["commodity", "state", "district", "market", "dates", "mape", "mae", "rmse"]]
        .head(10)
        .round(2)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
