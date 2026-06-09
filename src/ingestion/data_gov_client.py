from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

from src.config import DATA_GOV_API_URL
from src.processing.cleaning import clean_market_data


def fetch_data_gov_mandi_prices(
    api_key: str | None = None,
    limit: int = 1000,
    offset: int = 0,
    filters: dict[str, str] | None = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """Fetch current mandi prices from data.gov.in.

    This function is intentionally small and explicit so the app can use live
    data when credentials/network are available while staying demo-safe offline.
    """
    params: dict[str, Any] = {
        "api-key": api_key or os.getenv("DATA_GOV_API_KEY", "DEMO_KEY"),
        "format": "json",
        "limit": limit,
        "offset": offset,
    }
    if filters:
        params.update(filters)

    response = requests.get(DATA_GOV_API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    records = payload.get("records", [])
    if not records:
        return pd.DataFrame()

    return clean_market_data(pd.DataFrame(records), source="data.gov.in")

