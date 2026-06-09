from __future__ import annotations


import streamlit as st

from src.analytics.price_trends import top_price_movers
from src.config import APP_SUBTITLE, APP_TITLE
from src.ui.dashboard_state import build_market_context
from src.ui.theme import advisory_card, metric_card, money, page_header, section_header, setup_page
from src.visualization.charts import movers_chart, price_trend_chart


setup_page("Home")
ctx = build_market_context()

page_header(
    "Agricultural Market Intelligence Command Center",
    APP_SUBTITLE
    + ". Built for real mandi data, short-term price forecasting, market opportunity discovery, and farmer-friendly GenAI advisory.",
    eyebrow=APP_TITLE,
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Dataset", f"{ctx.profile['rows']:,} rows", f"{ctx.profile['markets']:,} markets", "green")
with col2:
    metric_card("Current Price", f"{money(ctx.summary['current_price'])}/qtl", ctx.selected_commodity, "gold")
with col3:
    metric_card(
        "Forecast Model",
        ctx.model_name.replace("_", " "),
        f"MAPE: {ctx.forecast_mape:.1f}%" if ctx.forecast_mape is not None else "MAPE: N/A",
        "blue",
    )
with col4:
    metric_card("Decision", ctx.recommendation.action, f"Confidence {int(ctx.recommendation.confidence_score * 100)}%", "green")

section_header(
    "Selected Market",
    "Change the commodity, mandi, forecast model, and cost assumptions from the Market Filters page.",
)
left, right = st.columns([1.45, 1])
with left:
    st.plotly_chart(
        price_trend_chart(ctx.df_selected, f"{ctx.selected_commodity} modal price trend in {ctx.selected_market}"),
        use_container_width=True,
    )
with right:
    advisory_card(
        action=ctx.recommendation.action,
        market=ctx.recommendation.recommended_market,
        gain=ctx.recommendation.expected_net_gain,
        risk=ctx.recommendation.risk_level,
        confidence=ctx.recommendation.confidence_score,
        current_price=ctx.recommendation.current_price,
        forecast_price=ctx.recommendation.forecast_price,
    )
    st.markdown("**Recommendation Evidence**")
    for reason in ctx.recommendation.reasoning:
        st.markdown(f"- {reason}")


movers = top_price_movers(ctx.df_full[ctx.df_full["state"] == ctx.selected_state], days=7, limit=8)
if not movers.empty:
    section_header("Recent State Movers", f"Fastest 7-day price changes in {ctx.selected_state}.")
    st.plotly_chart(movers_chart(movers, f"Top 7-day price movers in {ctx.selected_state}"), use_container_width=True)
