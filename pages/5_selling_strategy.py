from __future__ import annotations

import streamlit as st

from src.ui.dashboard_state import build_market_context
from src.ui.theme import advisory_card, metric_card, money, page_header, section_header, setup_page


setup_page("Selling Strategy")
ctx = build_market_context()

page_header(
    "Optimal Selling Strategy",
    "Convert market data, forecast direction, pressure signals, and cost assumptions into a clear action plan.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Action", ctx.recommendation.action, ctx.selected_commodity, "green")
with col2:
    metric_card("Recommended Market", ctx.recommendation.recommended_market, ctx.selected_state, "blue")
with col3:
    metric_card("Expected Net Gain", f"{money(ctx.recommendation.expected_net_gain)}/qtl", "Best available path", "gold")
with col4:
    metric_card("Risk", ctx.recommendation.risk_level, f"Confidence {int(ctx.recommendation.confidence_score * 100)}%", "red")

section_header("Farmer Advisory", ctx.selected_label)
advisory_card(
    action=ctx.recommendation.action,
    market=ctx.recommendation.recommended_market,
    gain=ctx.recommendation.expected_net_gain,
    risk=ctx.recommendation.risk_level,
    confidence=ctx.recommendation.confidence_score,
    current_price=ctx.recommendation.current_price,
    forecast_price=ctx.recommendation.forecast_price,
)

left, right = st.columns(2)
with left:
    section_header("Recommendation Evidence")
    for reason in ctx.recommendation.reasoning:
        st.markdown(f"- {reason}")

with right:
    section_header("Market Pressure")
    st.markdown(f"- {ctx.market_pressure['pressure']}")
    for reason in ctx.market_pressure["reasons"]:
        st.markdown(f"- {reason}")

section_header("Cost Assumptions Used")
st.markdown(
    f"""
    - Transport cost: **{money(ctx.transport_cost)}/qtl**
    - Storage cost: **{money(ctx.storage_cost)}/qtl/day**
    - Holding period: **{ctx.hold_days} days**
    - Forecast model: **{ctx.model_name.replace('_', ' ')}**
    """
)
