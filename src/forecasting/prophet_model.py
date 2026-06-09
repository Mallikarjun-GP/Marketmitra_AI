from __future__ import annotations

import pandas as pd

from src.forecasting.baseline import baseline_forecast
from src.forecasting.metrics import mape


def _run_prophet_forecast(model_df: pd.DataFrame, periods: int) -> tuple[pd.DataFrame, float | None, str]:
    from prophet import Prophet

    prophet_df = model_df.rename(columns={"date": "ds", "modal_price": "y"})
    test_size = min(14, max(7, len(prophet_df) // 6))
    train = prophet_df.iloc[:-test_size]
    test = prophet_df.iloc[-test_size:]

    eval_model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.8,
    )
    eval_model.fit(train)
    eval_future = eval_model.make_future_dataframe(periods=test_size)
    eval_forecast = eval_model.predict(eval_future)
    preds = eval_forecast.tail(test_size)["yhat"].values
    mape_score = mape(test["y"].values, preds)

    full_model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.8,
    )
    full_model.fit(prophet_df)
    future = full_model.make_future_dataframe(periods=periods)
    forecast = full_model.predict(future)
    forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast["is_future"] = forecast["ds"] > prophet_df["ds"].max()
    forecast["model_name"] = "prophet"
    return forecast, round(float(mape_score), 2), "prophet"


def run_price_forecast(
    df: pd.DataFrame,
    periods: int = 30,
    model_strategy: str = "auto",
) -> tuple[pd.DataFrame, float | None, str]:
    """Run Baseline, Prophet, or auto-select the lower backtest-MAPE model."""
    model_df = (
        df[["date", "modal_price"]]
        .dropna()
        .groupby("date", as_index=False)["modal_price"]
        .mean()
        .sort_values("date")
    )
    baseline_result = baseline_forecast(df, periods=periods)

    if model_strategy == "baseline":
        forecast, mape_score = baseline_result
        return forecast, mape_score, "baseline_rolling_trend"

    if len(model_df) < 45:
        forecast, mape_score = baseline_result
        return forecast, mape_score, "baseline_rolling_trend"

    try:
        prophet_result = _run_prophet_forecast(model_df, periods=periods)
    except Exception:
        forecast, mape_score = baseline_result
        return forecast, mape_score, "baseline_rolling_trend"

    if model_strategy == "prophet":
        return prophet_result

    baseline_forecast_df, baseline_mape = baseline_result
    prophet_forecast_df, prophet_mape, _ = prophet_result

    if baseline_mape is None:
        return prophet_result
    if prophet_mape is None:
        return baseline_forecast_df, baseline_mape, "baseline_rolling_trend"
    if prophet_mape <= baseline_mape:
        return prophet_forecast_df, prophet_mape, "prophet_auto_selected"
    return baseline_forecast_df, baseline_mape, "baseline_auto_selected"


def forecast_summary(forecast: pd.DataFrame, days_ahead: int = 7) -> dict:
    if forecast.empty:
        return {
            "forecast_price": 0.0,
            "forecast_lower": 0.0,
            "forecast_upper": 0.0,
            "forecast_trend": "Unknown",
            "available": False,
        }

    if "is_future" in forecast.columns:
        future = forecast[forecast["is_future"] == True].copy()
    else:
        future = pd.DataFrame()
    if future.empty:
        future = forecast.tail(days_ahead).copy()
    horizon = future.head(days_ahead)
    start = float(horizon["yhat"].iloc[0])
    end = float(horizon["yhat"].iloc[-1])

    if end > start * 1.02:
        trend = "Upward"
    elif end < start * 0.98:
        trend = "Downward"
    else:
        trend = "Flat"

    return {
        "forecast_price": round(end, 2),
        "forecast_lower": round(float(horizon["yhat_lower"].min()), 2),
        "forecast_upper": round(float(horizon["yhat_upper"].max()), 2),
        "forecast_trend": trend,
        "available": True,
    }
