from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from src.analytics.dataset_profile import dataset_summary, forecast_ready_groups, format_group_label
from src.analytics.market_pressure import compute_market_pressure
from src.analytics.price_trends import compare_markets, latest_market_summary
from src.config import (
    DEFAULT_HOLD_DAYS,
    DEFAULT_STORAGE_COST_PER_QUINTAL_PER_DAY,
    DEFAULT_TRANSPORT_COST_PER_QUINTAL,
)
from src.forecasting.prophet_model import forecast_summary, run_price_forecast
from src.genai.rag_store import MarketRAGStore
from src.ingestion.data_loader import filter_market_data, load_market_data
from src.recommendations.strategy_engine import SellingRecommendation, generate_selling_recommendation


FORECAST_MODELS = ["auto", "prophet", "baseline"]


@dataclass
class MarketContext:
    df_full: pd.DataFrame
    df_selected: pd.DataFrame
    profile: dict
    ready_groups: pd.DataFrame
    selected_commodity: str
    selected_state: str
    selected_district: str
    selected_market: str
    summary: dict
    market_pressure: dict
    market_comparison: pd.DataFrame
    forecast_df: pd.DataFrame
    forecast_mape: float | None
    model_name: str
    forecast_info: dict
    recommendation: SellingRecommendation
    forecast_model_choice: str
    transport_cost: float
    storage_cost: float
    hold_days: int

    @property
    def selected_label(self) -> str:
        return (
            f"{self.selected_commodity} in {self.selected_market}, "
            f"{self.selected_district}, {self.selected_state}"
        )


@st.cache_data(show_spinner=False)
def get_data(force_rebuild: bool = False) -> pd.DataFrame:
    return load_market_data(force_rebuild=force_rebuild)


@st.cache_data(show_spinner=False)
def get_forecast_cached(
    data: pd.DataFrame,
    periods: int = 30,
    model_strategy: str = "auto",
) -> tuple[pd.DataFrame, float | None, str]:
    return run_price_forecast(data, periods=periods, model_strategy=model_strategy)


@st.cache_resource(show_spinner=False)
def get_rag_store() -> MarketRAGStore:
    return MarketRAGStore()


def _pick_option(options: list[str], current: object | None, preferred: str | None = None) -> str:
    if not options:
        return ""
    if current in options:
        return str(current)
    if preferred in options:
        return str(preferred)
    return str(options[0])


def resolve_filter_state(df_full: pd.DataFrame, ready_groups: pd.DataFrame) -> dict:
    use_ready_series = bool(st.session_state.get("sidebar_use_ready_series", True)) and not ready_groups.empty
    st.session_state["sidebar_use_ready_series"] = use_ready_series

    if use_ready_series:
        labels = [format_group_label(row) for _, row in ready_groups.iterrows()]
        selected_label = _pick_option(labels, st.session_state.get("sidebar_ready_series"))
        st.session_state["sidebar_ready_series"] = selected_label
        ready_row = ready_groups.iloc[labels.index(selected_label)]
        selected_commodity = str(ready_row["commodity"])
        selected_state = str(ready_row["state"])
        selected_district = str(ready_row["district"])
        selected_market = str(ready_row["market"])
        ready_caption = (
            f"{int(ready_row['dates'])} unique dates from "
            f"{ready_row['start'].date()} to {ready_row['end'].date()}."
        )
    else:
        commodities = sorted(df_full["commodity"].dropna().unique().tolist())
        selected_commodity = _pick_option(commodities, st.session_state.get("sidebar_commodity"), "Onion")
        st.session_state["sidebar_commodity"] = selected_commodity

        commodity_df = df_full[df_full["commodity"] == selected_commodity]
        states = sorted(commodity_df["state"].dropna().unique().tolist())
        selected_state = _pick_option(states, st.session_state.get("sidebar_state"), "Maharashtra")
        st.session_state["sidebar_state"] = selected_state

        state_df = commodity_df[commodity_df["state"] == selected_state]
        districts = sorted(state_df["district"].dropna().unique().tolist())
        selected_district = _pick_option(districts, st.session_state.get("sidebar_district"))
        st.session_state["sidebar_district"] = selected_district

        district_df = state_df[state_df["district"] == selected_district]
        markets = sorted(district_df["market"].dropna().unique().tolist())
        selected_market = _pick_option(markets, st.session_state.get("sidebar_market"))
        st.session_state["sidebar_market"] = selected_market
        ready_caption = "Manual market selection."

    forecast_model_choice = _pick_option(
        FORECAST_MODELS,
        st.session_state.get("sidebar_forecast_model"),
        "auto",
    )
    st.session_state["sidebar_forecast_model"] = forecast_model_choice

    transport_cost = float(st.session_state.get("sidebar_transport_cost", DEFAULT_TRANSPORT_COST_PER_QUINTAL))
    storage_cost = float(st.session_state.get("sidebar_storage_cost", DEFAULT_STORAGE_COST_PER_QUINTAL_PER_DAY))
    hold_days = int(st.session_state.get("sidebar_hold_days", DEFAULT_HOLD_DAYS))
    transport_cost = max(0.0, transport_cost)
    storage_cost = max(0.0, storage_cost)
    hold_days = max(3, min(30, hold_days))
    st.session_state["sidebar_transport_cost"] = transport_cost
    st.session_state["sidebar_storage_cost"] = storage_cost
    st.session_state["sidebar_hold_days"] = hold_days

    return {
        "selected_commodity": selected_commodity,
        "selected_state": selected_state,
        "selected_district": selected_district,
        "selected_market": selected_market,
        "forecast_model_choice": forecast_model_choice,
        "transport_cost": transport_cost,
        "storage_cost": storage_cost,
        "hold_days": hold_days,
        "ready_caption": ready_caption,
    }


def build_market_context() -> MarketContext:
    with st.sidebar:
        st.markdown("### MarketMitra AI")
        st.caption("Real mandi data, price intelligence, forecasts, GenAI reports, and advisory workflows.")
        force_reload = st.button("Reload data", key="sidebar_reload_data")
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
    filters = resolve_filter_state(df_full, ready_groups)

    selected_commodity = filters["selected_commodity"]
    selected_state = filters["selected_state"]
    selected_district = filters["selected_district"]
    selected_market = filters["selected_market"]
    forecast_model_choice = filters["forecast_model_choice"]
    transport_cost = filters["transport_cost"]
    storage_cost = filters["storage_cost"]
    hold_days = filters["hold_days"]

    with st.sidebar:
        st.divider()
        st.markdown("### Current Market")
        st.caption(f"**{selected_commodity}**")
        st.caption(f"{selected_market}, {selected_district}, {selected_state}")
        st.caption(filters["ready_caption"])
        st.page_link("pages/0_Market_Filters.py", label="Change Market Filters")
        st.divider()
        st.markdown("### Assumptions")
        st.caption(f"Forecast model: **{forecast_model_choice}**")
        st.caption(f"Transport: **INR {transport_cost:,.0f}/qtl**")
        st.caption(f"Storage: **INR {storage_cost:,.0f}/qtl/day**")
        st.caption(f"Holding period: **{hold_days} days**")
        st.divider()
        st.markdown("### Dataset")
        st.caption(
            f"{profile['rows']:,} rows | {profile['commodities']} commodities | "
            f"{profile['markets']:,} markets"
        )

    df_selected = filter_market_data(
        df_full,
        commodity=selected_commodity,
        state=selected_state,
        district=selected_district,
        market=selected_market,
    )

    if df_selected.empty:
        st.error("No data available for the selected filters.")
        st.stop()

    summary = latest_market_summary(df_selected)
    market_pressure = compute_market_pressure(summary)
    market_comparison = compare_markets(df_full, selected_commodity, selected_state)

    with st.spinner("Preparing short-term forecast..."):
        forecast_df, forecast_mape, model_name = get_forecast_cached(
            df_selected,
            periods=30,
            model_strategy=forecast_model_choice,
        )
    forecast_info = forecast_summary(forecast_df, days_ahead=hold_days)
    if not forecast_info.get("available"):
        forecast_info = {
            "forecast_price": summary["current_price"],
            "forecast_lower": summary["current_price"],
            "forecast_upper": summary["current_price"],
            "forecast_trend": "Insufficient history",
            "available": False,
        }

    recommendation = generate_selling_recommendation(
        commodity=selected_commodity,
        local_market=selected_market,
        summary=summary,
        forecast=forecast_info,
        market_pressure=market_pressure,
        market_comparison=market_comparison,
        transport_cost_per_quintal=transport_cost,
        storage_cost_per_quintal_per_day=storage_cost,
        hold_days=hold_days,
    )

    return MarketContext(
        df_full=df_full,
        df_selected=df_selected,
        profile=profile,
        ready_groups=ready_groups,
        selected_commodity=selected_commodity,
        selected_state=selected_state,
        selected_district=selected_district,
        selected_market=selected_market,
        summary=summary,
        market_pressure=market_pressure,
        market_comparison=market_comparison,
        forecast_df=forecast_df,
        forecast_mape=forecast_mape,
        model_name=model_name,
        forecast_info=forecast_info,
        recommendation=recommendation,
        forecast_model_choice=forecast_model_choice,
        transport_cost=float(transport_cost),
        storage_cost=float(storage_cost),
        hold_days=int(hold_days),
    )
