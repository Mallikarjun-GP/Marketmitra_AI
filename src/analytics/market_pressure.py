from __future__ import annotations


def compute_market_pressure(summary: dict) -> dict:
    """Infer demand-supply pressure from price and arrival behavior."""
    price_change = summary.get("wow_change_pct", 0) or 0
    arrival_change = summary.get("arrival_change_pct", 0) or 0
    volatility = summary.get("volatility_label", "Unknown")

    reasons: list[str] = []
    pressure = "Balanced"
    risk = "Medium"
    liquidity_score = 0.65

    if price_change > 3 and arrival_change < -3:
        pressure = "Strong demand or low supply pressure"
        reasons.append("Prices are rising while arrivals are falling.")
        risk = "Medium"
        liquidity_score = 0.7
    elif price_change > 3 and arrival_change >= 3:
        pressure = "Healthy demand absorbing supply"
        reasons.append("Prices are rising even though arrivals increased.")
        risk = "Low"
        liquidity_score = 0.8
    elif price_change < -3 and arrival_change > 3:
        pressure = "Oversupply risk"
        reasons.append("Prices are falling while arrivals are increasing.")
        risk = "High"
        liquidity_score = 0.55
    elif price_change < -3 and arrival_change <= -3:
        pressure = "Weak demand or thin market"
        reasons.append("Prices are falling despite lower arrivals.")
        risk = "High"
        liquidity_score = 0.45
    else:
        reasons.append("Price and arrival movement are not showing a strong imbalance.")

    if volatility == "High":
        risk = "High"
        reasons.append("Price volatility is high, so timing risk is elevated.")
    elif volatility == "Low" and risk == "Medium":
        risk = "Low"

    return {
        "pressure": pressure,
        "risk": risk,
        "liquidity_score": round(liquidity_score, 2),
        "reasons": reasons,
    }

