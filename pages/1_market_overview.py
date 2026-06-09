from __future__ import annotations

import streamlit as st

from src.analytics.price_trends import top_price_movers
from src.ui.dashboard_state import build_market_context
from src.ui.theme import advisory_card, metric_card, money, page_header, pct, section_header, setup_page
from src.visualization.charts import movers_chart, price_trend_chart


setup_page("Market Overview")
ctx = build_market_context()

page_header(
    "Market Overview",
    "Live snapshot of the selected commodity, mandi, current price signal, and recommended action.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Current Modal Price", f"{money(ctx.summary['current_price'])}/qtl", ctx.selected_market, "green")
with col2:
    metric_card("7-Day Change", pct(ctx.summary["wow_change_pct"]), "Recent momentum", "gold")
with col3:
    metric_card("30-Day Average", f"{money(ctx.summary['avg_30d'])}/qtl", "Short-term reference", "blue")
with col4:
    metric_card("Volatility", ctx.summary["volatility_label"], f"{ctx.summary['volatility_pct']:.1f}% band", "red")

section_header("Market Snapshot", ctx.selected_label)
left, right = st.columns([1.45, 1])
with left:
    st.plotly_chart(
        price_trend_chart(ctx.df_selected, f"{ctx.selected_commodity} price trend in {ctx.selected_market}"),
        use_container_width=True,
    )
with right:
    advisory_card(
        action=ctx.recommendation.action,
        market=ctx.recommendation.recommended_market,
        gain=ctx.recommendation.expected_net_gain,
        risk=ctx.recommendation.risk_level,
        confidence=ctx.recommendation.confidence_score,
    )
    st.markdown("**Why this recommendation**")
    for reason in ctx.recommendation.reasoning:
        st.markdown(f"- {reason}")

movers = top_price_movers(ctx.df_full[ctx.df_full["state"] == ctx.selected_state], days=7, limit=8)
if not movers.empty:
    section_header("Top Price Movers", f"Highest 7-day commodity price changes in {ctx.selected_state}.")
    st.plotly_chart(movers_chart(movers, f"Top 7-day price movers in {ctx.selected_state}"), use_container_width=True)
