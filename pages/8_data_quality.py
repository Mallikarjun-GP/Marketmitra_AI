from __future__ import annotations

import streamlit as st

from src.ui.dashboard_state import build_market_context
from src.ui.theme import metric_card, page_header, section_header, setup_page


setup_page("Data Quality")
ctx = build_market_context()

page_header(
    "Data Quality and Traceability",
    "Show judges that the system uses an original market-price dataset, tracks coverage, and exposes quality checks.",
)

source_counts = ctx.df_full["source"].value_counts().reset_index()
source_counts.columns = ["source", "rows"]
selected_missing = ctx.df_selected.isna().mean().mul(100).round(2).reset_index()
selected_missing.columns = ["column", "missing_percent"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Rows", f"{ctx.profile['rows']:,}", "Curated analytics table", "green")
with col2:
    metric_card("Selected Rows", f"{len(ctx.df_selected):,}", ctx.selected_market, "gold")
with col3:
    metric_card("Date Range", f"{ctx.profile['date_min'].date()}", f"to {ctx.profile['date_max'].date()}", "blue")
with col4:
    metric_card("Forecast-Ready Series", f"{len(ctx.ready_groups):,}", "120+ unique dates", "green")

left, right = st.columns(2)
with left:
    section_header("Source Rows")
    st.dataframe(source_counts, use_container_width=True, hide_index=True)
with right:
    section_header("Missing Values for Selected Series")
    st.dataframe(selected_missing, use_container_width=True, hide_index=True)

if not ctx.ready_groups.empty:
    section_header("Top Forecast-Ready Series")
    st.dataframe(
        ctx.ready_groups[["commodity", "state", "district", "market", "dates", "rows", "start", "end", "avg_price"]].head(30),
        use_container_width=True,
        hide_index=True,
    )

section_header("Selected Data Preview", "Latest rows after cleaning and normalization.")
preview_cols = ["date", "state", "district", "market", "commodity", "variety", "grade", "min_price", "max_price", "modal_price"]
available_cols = [col for col in preview_cols if col in ctx.df_selected.columns]
st.dataframe(ctx.df_selected.sort_values("date", ascending=False)[available_cols].head(50), use_container_width=True, hide_index=True)
