from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.dashboard_state import build_market_context
from src.ui.theme import page_header, section_header, setup_page
from src.visualization.charts import price_band_chart, price_trend_chart


setup_page("Price Trends")
ctx = build_market_context()

page_header(
    "Price Trend Analysis",
    "Analyze historical modal price movement, moving averages, price bands, volatility, and arrivals for the selected mandi.",
)

left, right = st.columns(2)
with left:
    st.plotly_chart(
        price_trend_chart(ctx.df_selected, f"{ctx.selected_commodity} trend with moving averages"),
        use_container_width=True,
    )
with right:
    st.plotly_chart(
        price_band_chart(ctx.df_selected, f"{ctx.selected_commodity} min-max-modal price band"),
        use_container_width=True,
    )

section_header("Latest Analytics", "Signals used by the advisory and forecasting engines.")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Current price": ctx.summary["current_price"],
                "7-day average": ctx.summary["ma_7"],
                "30-day average": ctx.summary["ma_30"],
                "90-day context": "Available" if len(ctx.df_selected) >= 90 else "Limited",
                "7-day change %": ctx.summary["wow_change_pct"],
                "30-day change %": ctx.summary["mom_change_pct"],
                "Arrival change %": ctx.summary["arrival_change_pct"],
                "Volatility": ctx.summary["volatility_label"],
            }
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

section_header("Recent Records", "Most recent observations from the selected official dataset series.")
recent_cols = ["date", "commodity", "state", "district", "market", "min_price", "max_price", "modal_price", "arrivals_tonnes"]
available_cols = [col for col in recent_cols if col in ctx.df_selected.columns]
st.dataframe(ctx.df_selected.sort_values("date", ascending=False)[available_cols].head(40), use_container_width=True, hide_index=True)
