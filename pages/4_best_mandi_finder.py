from __future__ import annotations

import streamlit as st

from src.ui.dashboard_state import build_market_context
from src.ui.theme import metric_card, money, page_header, section_header, setup_page
from src.visualization.charts import mandi_comparison_chart


setup_page("Best Mandi Finder")
ctx = build_market_context()

page_header(
    "Best Mandi Finder",
    "Rank nearby mandis by recent average modal price and estimate the net opportunity after transport cost.",
)

section_header("Mandi Opportunity Ranking", f"{ctx.selected_commodity} markets in {ctx.selected_state}.")
if ctx.market_comparison.empty:
    st.info("No comparable markets are available for this commodity and state.")
else:
    enriched = ctx.market_comparison.copy()
    enriched["net_gain_vs_selected"] = (enriched["avg_price"] - ctx.summary["current_price"] - ctx.transport_cost).round(2)
    top = enriched.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Top Mandi", str(top["market"]), str(top["district"]), "green")
    with col2:
        metric_card("Top Avg Price", f"{money(top['avg_price'])}/qtl", "Recent 30-day average", "gold")
    with col3:
        metric_card("Net Gain", f"{money(top['net_gain_vs_selected'])}/qtl", "After transport assumption", "blue")
    with col4:
        metric_card("Transport Cost", f"{money(ctx.transport_cost)}/qtl", "Sidebar assumption", "red")

    st.plotly_chart(
        mandi_comparison_chart(enriched, f"Average {ctx.selected_commodity} price across mandis"),
        use_container_width=True,
    )
    st.dataframe(
        enriched[
            [
                "state",
                "district",
                "market",
                "avg_price",
                "latest_price",
                "arrivals_tonnes",
                "net_gain_vs_selected",
                "data_points",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
