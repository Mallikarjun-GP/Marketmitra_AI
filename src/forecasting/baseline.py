from __future__ import annotations

import numpy as np
import pandas as pd

from src.forecasting.metrics import mape


def baseline_forecast(df: pd.DataFrame, periods: int = 30) -> tuple[pd.DataFrame, float | None]:
    series = df[["date", "modal_price"]].dropna().sort_values("date")
    if len(series) < 10:
        return pd.DataFrame(), None

    test_size = min(14, max(3, len(series) // 5))
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    rolling_mean = train["modal_price"].tail(7).mean()
    trend = (train["modal_price"].tail(7).mean() - train["modal_price"].tail(21).head(7).mean()) / 14 if len(train) >= 21 else 0

    preds = np.array([rolling_mean + trend * (i + 1) for i in range(test_size)])
    mape_score = mape(test["modal_price"], preds)

    last_date = series["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    recent_std = series["modal_price"].tail(30).std()
    if pd.isna(recent_std) or recent_std == 0:
        recent_std = series["modal_price"].std() or 1

    future_values = [series["modal_price"].tail(7).mean() + trend * (i + 1) for i in range(periods)]
    forecast = pd.DataFrame(
        {
            "ds": future_dates,
            "yhat": future_values,
            "yhat_lower": np.array(future_values) - 1.28 * recent_std,
            "yhat_upper": np.array(future_values) + 1.28 * recent_std,
            "is_future": True,
            "model_name": "baseline_rolling_trend",
        }
    )

    history = pd.DataFrame(
        {
            "ds": series["date"],
            "yhat": series["modal_price"],
            "yhat_lower": series["modal_price"],
            "yhat_upper": series["modal_price"],
            "is_future": False,
            "model_name": "actual",
        }
    )

    return pd.concat([history, forecast], ignore_index=True), round(float(mape_score), 2)
