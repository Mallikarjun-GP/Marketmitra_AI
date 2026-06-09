from __future__ import annotations

import streamlit as st

from src.ui.dashboard_state import build_market_context
from src.ui.theme import metric_card, money, page_header, section_header, setup_page
from src.visualization.charts import forecast_chart


setup_page("Forecasting")
ctx = build_market_context()

page_header(
    "Demand and Price Forecasting",
    "Short-term modal price outlook using Prophet, baseline rolling trend, or auto-selection based on recent backtest MAPE.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Forecast Model", ctx.model_name.replace("_", " "), "Selected from sidebar", "blue")
with col2:
    metric_card("Backtest MAPE", "N/A" if ctx.forecast_mape is None else f"{ctx.forecast_mape:.1f}%", "Lower is better", "gold")
with col3:
    metric_card(f"{ctx.hold_days}-Day Forecast", f"{money(ctx.forecast_info['forecast_price'])}/qtl", "Selling horizon", "green")
with col4:
    metric_card("Forecast Trend", ctx.forecast_info["forecast_trend"], "Upward, flat, or downward", "blue")

section_header("Forecast Curve", ctx.selected_label)
if ctx.forecast_df.empty:
    st.warning(
        "Not enough historical records for forecasting. Add a longer historical AGMARKNET/Kaggle CSV for richer trend forecasting."
    )
else:
    st.plotly_chart(
        forecast_chart(ctx.df_selected, ctx.forecast_df, f"{ctx.selected_commodity} {ctx.hold_days}-day selling horizon"),
        use_container_width=True,
    )

section_header("Forecast Interpretation", "How this result is used in the selling strategy.")
st.markdown(
    f"""
    - The engine forecasts the expected modal price after **{ctx.hold_days} days**.
    - The recommendation compares forecast gain against storage cost of **INR {ctx.storage_cost:,.0f}/qtl/day**.
    - Auto mode compares Prophet and the baseline on recent backtest MAPE, then uses the lower-error model.
    - Current forecast range: **{money(ctx.forecast_info['forecast_lower'])} to {money(ctx.forecast_info['forecast_upper'])}/qtl**.
    """
)
