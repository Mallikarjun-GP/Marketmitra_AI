from __future__ import annotations

import streamlit as st

from src.config import APP_TITLE
from src.ui.theme import apply_theme


st.set_page_config(page_title=APP_TITLE, page_icon="MM", layout="wide")
apply_theme()

page = st.navigation(
    {
        "Dashboard": [
            st.Page("pages/Home.py", title="Home", default=True),
            st.Page("pages/0_Market_Filters.py", title="Market Filters"),
        ],
        "Analytics": [
            st.Page("pages/1_market_overview.py", title="Market Overview"),
            st.Page("pages/2_price_trends.py", title="Price Trends"),
            st.Page("pages/3_forecasting.py", title="Forecasting"),
            st.Page("pages/4_best_mandi_finder.py", title="Best Mandi Finder"),
            st.Page("pages/5_selling_strategy.py", title="Selling Strategy"),
        ],
        "GenAI": [
            st.Page("pages/6_weekly_reports.py", title="Weekly Reports"),
            st.Page("pages/7_ai_assistant.py", title="AI Assistant"),
        ],
        "Governance": [
            st.Page("pages/8_data_quality.py", title="Data Quality"),
        ],
    },
    expanded=True,
)

page.run()

