from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.dataset_profile import dataset_summary, forecast_ready_groups, format_group_label
from src.config import (
    DEFAULT_HOLD_DAYS,
    DEFAULT_STORAGE_COST_PER_QUINTAL_PER_DAY,
    DEFAULT_TRANSPORT_COST_PER_QUINTAL,
)
from src.ingestion.data_loader import filter_market_data
from src.ui.dashboard_state import FORECAST_MODELS, get_data, get_forecast_cached, resolve_filter_state
from src.ui.theme import metric_card, money, page_header, section_header, setup_page
from src.visualization.charts import price_trend_chart


setup_page("Market Filters")

with st.sidebar:
    st.markdown("### MarketMitra AI")
    st.caption("Configure the active market once, then every page uses the same selection.")
    st.page_link("pages/Home.py", label="Back to Home")

page_header(
    "Market Filters and Demo Setup",
    "Choose the commodity, state, district, mandi, forecast model, and cost assumptions used across all dashboard pages.",
)

force_reload = st.button("🔄 Reload data", key="filters_reload_data")
if force_reload:
    get_data.clear()
    get_forecast_cached.clear()

try:
    df_full = get_data(force_rebuild=force_reload)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info(
        "Add your official dataset CSV to `data/raw/`, then click Reload data or restart the app. "
        "Recommended sources: AGMARKNET/data.gov.in mandi prices or Kaggle agricultural commodity price CSV sourced from AGMARKNET."
    )
    st.stop()

df_full = df_full.copy()
df_full["date"] = pd.to_datetime(df_full["date"])
profile = dataset_summary(df_full)
ready_groups = forecast_ready_groups(df_full, min_dates=120, limit=75)
resolve_filter_state(df_full, ready_groups)

section_header("Dataset Coverage", "This confirms the dashboard is using the original curated market dataset.")
coverage_cols = st.columns(4)
with coverage_cols[0]:
    metric_card("Rows", f"{profile['rows']:,}", "Curated records", "green")
with coverage_cols[1]:
    metric_card("Commodities", f"{profile['commodities']:,}", "Available crops", "gold")
with coverage_cols[2]:
    metric_card("Markets", f"{profile['markets']:,}", "Mandis", "blue")
with coverage_cols[3]:
    metric_card("Forecast-Ready", f"{len(ready_groups):,}", "120+ unique dates", "green")

section_header("Active Market Selection", "Use forecast-ready demo series for reliable live demos, or switch to manual selection.")
selection_col, assumption_col = st.columns([1.25, 1])

with selection_col:
    if ready_groups.empty:
        st.session_state["sidebar_use_ready_series"] = False
        st.info("No forecast-ready series found. Manual selection is enabled.")

    use_ready_series = st.checkbox(
        "Use forecast-ready demo series",
        value=bool(st.session_state.get("sidebar_use_ready_series", not ready_groups.empty)),
        disabled=ready_groups.empty,
        key="sidebar_use_ready_series",
    )

    if use_ready_series and not ready_groups.empty:
        labels = [format_group_label(row) for _, row in ready_groups.iterrows()]
        if st.session_state.get("sidebar_ready_series") not in labels:
            st.session_state["sidebar_ready_series"] = labels[0]
        selected_label = st.selectbox("Forecast-ready series", labels, key="sidebar_ready_series")
        ready_row = ready_groups.iloc[labels.index(selected_label)]
        selected_commodity = str(ready_row["commodity"])
        selected_state = str(ready_row["state"])
        selected_district = str(ready_row["district"])
        selected_market = str(ready_row["market"])
        st.session_state["sidebar_commodity"] = selected_commodity
        st.session_state["sidebar_state"] = selected_state
        st.session_state["sidebar_district"] = selected_district
        st.session_state["sidebar_market"] = selected_market
        st.caption(
            f"{int(ready_row['dates'])} unique dates from "
            f"{ready_row['start'].date()} to {ready_row['end'].date()}."
        )
    else:
        commodities = sorted(df_full["commodity"].dropna().unique().tolist())
        if st.session_state.get("sidebar_commodity") not in commodities:
            st.session_state["sidebar_commodity"] = "Onion" if "Onion" in commodities else commodities[0]
        selected_commodity = st.selectbox("Commodity", commodities, key="sidebar_commodity")

        commodity_df = df_full[df_full["commodity"] == selected_commodity]
        states = sorted(commodity_df["state"].dropna().unique().tolist())
        if st.session_state.get("sidebar_state") not in states:
            st.session_state["sidebar_state"] = "Maharashtra" if "Maharashtra" in states else states[0]
        selected_state = st.selectbox("State", states, key="sidebar_state")

        state_df = commodity_df[commodity_df["state"] == selected_state]
        districts = sorted(state_df["district"].dropna().unique().tolist())
        if st.session_state.get("sidebar_district") not in districts:
            st.session_state["sidebar_district"] = districts[0]
        selected_district = st.selectbox("District", districts, key="sidebar_district")

        district_df = state_df[state_df["district"] == selected_district]
        markets = sorted(district_df["market"].dropna().unique().tolist())
        if st.session_state.get("sidebar_market") not in markets:
            st.session_state["sidebar_market"] = markets[0]
        selected_market = st.selectbox("Market/Mandi", markets, key="sidebar_market")

with assumption_col:
    if st.session_state.get("sidebar_forecast_model") not in FORECAST_MODELS:
        st.session_state["sidebar_forecast_model"] = "auto"
    st.selectbox(
        "Forecast model",
        FORECAST_MODELS,
        help="Auto compares baseline and Prophet on recent backtest MAPE and selects the lower-error model.",
        key="sidebar_forecast_model",
    )

    st.session_state.setdefault("sidebar_transport_cost", DEFAULT_TRANSPORT_COST_PER_QUINTAL)
    st.session_state.setdefault("sidebar_storage_cost", DEFAULT_STORAGE_COST_PER_QUINTAL_PER_DAY)
    st.session_state.setdefault("sidebar_hold_days", DEFAULT_HOLD_DAYS)
    st.number_input("Transport cost per quintal", min_value=0.0, step=10.0, key="sidebar_transport_cost")
    st.number_input("Storage cost per quintal/day", min_value=0.0, step=1.0, key="sidebar_storage_cost")
    st.slider("Holding period", min_value=3, max_value=30, step=1, key="sidebar_hold_days")

selected_commodity = str(st.session_state["sidebar_commodity"])
selected_state = str(st.session_state["sidebar_state"])
selected_district = str(st.session_state["sidebar_district"])
selected_market = str(st.session_state["sidebar_market"])
df_selected = filter_market_data(
    df_full,
    commodity=selected_commodity,
    state=selected_state,
    district=selected_district,
    market=selected_market,
)

st.success(
    f"Filters saved: {selected_commodity} in {selected_market}, "
    f"{selected_district}, {selected_state}."
)

section_header("Selected Series Preview", "A quick check before opening analysis pages.")
preview_cols = st.columns(4)
with preview_cols[0]:
    metric_card("Selected Rows", f"{len(df_selected):,}", selected_market, "green")
with preview_cols[1]:
    metric_card("Date Range", str(df_selected["date"].min().date()), f"to {df_selected['date'].max().date()}", "blue")
with preview_cols[2]:
    metric_card("Transport Cost", f"{money(st.session_state['sidebar_transport_cost'])}/qtl", "Assumption", "gold")
with preview_cols[3]:
    metric_card("Holding Period", f"{int(st.session_state['sidebar_hold_days'])} days", "Selling horizon", "green")

if not df_selected.empty:
    st.plotly_chart(
        price_trend_chart(df_selected, f"{selected_commodity} price trend in {selected_market}"),
        use_container_width=True,
    )
