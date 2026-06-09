from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.config import HIGH_VOLATILITY_CROPS, PERISHABLE_CROPS, STORABLE_CROPS


@dataclass
class SellingRecommendation:
    action: str
    recommended_market: str
    current_price: float
    forecast_price: float
    expected_net_gain: float
    risk_level: str
    confidence_score: float
    reasoning: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "recommended_market": self.recommended_market,
            "current_price": self.current_price,
            "forecast_price": self.forecast_price,
            "expected_net_gain": self.expected_net_gain,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
        }


def generate_selling_recommendation(
    commodity: str,
    local_market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    market_comparison: pd.DataFrame,
    transport_cost_per_quintal: float,
    storage_cost_per_quintal_per_day: float,
    hold_days: int,
) -> SellingRecommendation:
    commodity_key = commodity.lower()
    current_price = float(summary.get("current_price", 0) or 0)
    forecast_price = float(forecast.get("forecast_price", current_price) or current_price)
    forecast_trend = forecast.get("forecast_trend", "Flat")
    volatility = summary.get("volatility_label", "Unknown")
    avg_30d = float(summary.get("avg_30d", current_price) or current_price)
    pressure = market_pressure.get("pressure", "Balanced")

    is_perishable = commodity_key in PERISHABLE_CROPS
    is_storable = commodity_key in STORABLE_CROPS
    is_high_volatility_crop = commodity_key in HIGH_VOLATILITY_CROPS

    reasoning: list[str] = []
    confidence = 0.64
    risk = market_pressure.get("risk", "Medium")
    action = "Sell today"
    recommended_market = local_market

    best_market_price = current_price
    if not market_comparison.empty:
        top = market_comparison.iloc[0]
        best_market = str(top["market"])
        best_market_price = float(top["avg_price"])
        if best_market.lower() != local_market.lower():
            recommended_market = best_market

    hold_gain = (forecast_price - current_price) - (storage_cost_per_quintal_per_day * hold_days)
    transport_gain = (best_market_price - current_price) - transport_cost_per_quintal
    sell_now_gain = max(current_price - avg_30d, 0)

    if current_price > avg_30d * 1.08:
        reasoning.append("Current price is above the 30-day average, so selling has attractive timing.")
    if is_perishable:
        reasoning.append("The crop is perishable, so long holding increases quality and spoilage risk.")
    if volatility == "High" or is_high_volatility_crop:
        reasoning.append("The commodity or market is volatile, so split selling can reduce timing risk.")
    if pressure != "Balanced":
        reasoning.append(f"Market pressure signal: {pressure}.")

    if transport_gain > max(150, current_price * 0.04):
        action = f"Transport to {recommended_market}"
        reasoning.append(f"{recommended_market} shows a stronger net opportunity after transport cost.")
        confidence = 0.7
        risk = "Medium" if risk != "High" else "High"
    elif forecast_trend == "Upward" and hold_gain > 0 and not is_perishable:
        if volatility == "High":
            action = f"Sell 50% today and hold 50% for {hold_days} days"
            reasoning.append("Forecast is positive, but volatility is high, so a split sale balances upside and risk.")
            confidence = 0.68
            risk = "Medium"
        else:
            action = f"Hold for {hold_days} days"
            reasoning.append("Forecasted gain is higher than estimated storage cost.")
            confidence = 0.74 if is_storable else 0.67
            risk = "Low" if is_storable and volatility == "Low" else "Medium"
    elif forecast_trend == "Downward" or is_perishable:
        action = "Sell today"
        reasoning.append("Forecast or crop perishability favors locking in the current price.")
        confidence = 0.76
        risk = "Low" if volatility != "High" else "Medium"
    elif volatility == "High":
        action = f"Sell 50% today and hold 50% for {hold_days} days"
        reasoning.append("Price direction is uncertain, so split selling reduces downside risk.")
        confidence = 0.64
        risk = "Medium"
    else:
        action = "Sell today"
        reasoning.append("Expected benefit from waiting or transport is limited after costs.")
        confidence = 0.66

    expected_gain = max(sell_now_gain, hold_gain, transport_gain, 0)
    if not reasoning:
        reasoning.append("Current market signals are balanced, so the safer action is preferred.")

    return SellingRecommendation(
        action=action,
        recommended_market=recommended_market,
        current_price=round(current_price, 2),
        forecast_price=round(forecast_price, 2),
        expected_net_gain=round(float(expected_gain), 2),
        risk_level=risk,
        confidence_score=round(float(max(min(confidence, 0.92), 0.35)), 2),
        reasoning=reasoning,
    )

