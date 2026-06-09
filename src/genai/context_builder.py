from __future__ import annotations

import pandas as pd

from src.recommendations.strategy_engine import SellingRecommendation


def build_market_context(
    commodity: str,
    state: str,
    district: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    market_comparison: pd.DataFrame,
    max_markets: int = 5,
) -> str:
    """Build a compact, grounded context block for LLM chat/report prompts."""
    top_markets = ""
    if not market_comparison.empty:
        rows = []
        for _, row in market_comparison.head(max_markets).iterrows():
            rows.append(
                f"- {row['market']}, {row['district']}: "
                f"avg INR {row['avg_price']}/quintal, latest INR {row['latest_price']}/quintal"
            )
        top_markets = "\n".join(rows)

    reasons = "\n".join(f"- {reason}" for reason in recommendation.reasoning)
    pressure_reasons = "\n".join(f"- {reason}" for reason in market_pressure.get("reasons", []))

    return f"""Selected market context:
- Commodity: {commodity}
- Market: {market}, {district}, {state}
- Current modal price: INR {summary.get('current_price')}/quintal
- 7-day average: INR {summary.get('ma_7')}/quintal
- 30-day average: INR {summary.get('ma_30')}/quintal
- Week-over-week change: {summary.get('wow_change_pct')}%
- Month-over-month change: {summary.get('mom_change_pct')}%
- Volatility: {summary.get('volatility_label')}
- Forecast price: INR {forecast.get('forecast_price')}/quintal
- Forecast range: INR {forecast.get('forecast_lower')} to INR {forecast.get('forecast_upper')}/quintal
- Forecast trend: {forecast.get('forecast_trend')}
- Market pressure: {market_pressure.get('pressure')}
- Risk level: {recommendation.risk_level}
- Confidence: {int(recommendation.confidence_score * 100)}%
- Recommended action: {recommendation.action}
- Recommended market: {recommendation.recommended_market}
- Expected net gain: INR {recommendation.expected_net_gain}/quintal

Recommendation evidence:
{reasons}

Market pressure evidence:
{pressure_reasons}

Top comparable mandis for {commodity} in {state}:
{top_markets or "- No comparable mandi data available."}
"""

