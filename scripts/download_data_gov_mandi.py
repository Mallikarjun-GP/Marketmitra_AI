from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests import Session
from requests.exceptions import RequestException, Timeout

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


CURRENT_API_URL = "https://api.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi"
VARIETY_WISE_API_URL = "https://api.data.gov.in/resource/variety-wise-daily-market-prices-data-commodity"
LEGACY_API_URL = "https://data.gov.in/resources/current-daily-price-various-commodities-various-markets-mandi/api"
LEGACY_PLURAL_API_URL = "https://data.gov.in/resources/current-daily-price-various-commodities-various-markets-mandis/api"

API_URLS = {
    "current": CURRENT_API_URL,
    "variety": VARIETY_WISE_API_URL,
    "legacy": LEGACY_API_URL,
    "legacy_plural": LEGACY_PLURAL_API_URL,
}


def fetch_page(
    session: Session,
    api_url: str,
    api_key: str,
    offset: int,
    limit: int,
    timeout: int,
    retries: int,
    sleep_seconds: float,
) -> list[dict]:
    params = {
        "api-key": api_key,
        "format": "json",
        "offset": offset,
        "limit": limit,
    }
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(api_url, params=params, timeout=(10, timeout))
            break
        except Timeout as exc:
            last_error = exc
            print(f"Timeout at offset={offset}, attempt {attempt}/{retries}. Retrying...")
            time.sleep(sleep_seconds * attempt)
        except RequestException as exc:
            last_error = exc
            print(f"Request failed at offset={offset}, attempt {attempt}/{retries}: {exc}. Retrying...")
            time.sleep(sleep_seconds * attempt)
    else:
        raise RuntimeError(
            f"Failed after {retries} attempts at offset={offset}. "
            f"Try lower --limit, higher --timeout, or --legacy-url. Last error: {last_error}"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"data.gov.in returned HTTP {response.status_code}. "
            f"Response preview: {response.text[:300]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "data.gov.in did not return JSON. Check the API URL and API key. "
            f"Response preview: {response.text[:300]}"
        ) from exc

    if "error" in payload:
        raise RuntimeError(f"data.gov.in API error: {payload['error']}")

    if payload.get("status") == "error":
        raise RuntimeError(f"data.gov.in API status error: {payload.get('message', payload)}")

    if isinstance(payload.get("message"), str) and "Invalid" in payload["message"]:
        raise RuntimeError(f"data.gov.in API message: {payload['message']}")

    records = payload.get("records", [])
    if not records:
        print(f"No records at offset={offset}. Response keys: {list(payload.keys())}")
        for key in ["title", "desc", "message", "status", "total", "count"]:
            if key in payload:
                print(f"{key}: {payload[key]}")
    return records


def download_dataset(
    api_url: str,
    api_key: str,
    output: Path,
    limit: int,
    max_records: int,
    timeout: int,
    retries: int,
    sleep_seconds: float,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    offset = 0
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "MarketMitraAI/1.0 (+https://data.gov.in)",
            "Accept": "application/json",
        }
    )

    while offset < max_records:
        records = fetch_page(
            session=session,
            api_url=api_url,
            api_key=api_key,
            offset=offset,
            limit=limit,
            timeout=timeout,
            retries=retries,
            sleep_seconds=sleep_seconds,
        )
        if not records:
            break

        all_records.extend(records)
        print(f"Fetched {len(all_records)} records")

        # Save partial progress after each successful page.
        pd.DataFrame(all_records).to_csv(output, index=False, encoding="utf-8")

        if len(records) < limit:
            break

        offset += limit

    if not all_records:
        raise RuntimeError(
            "No records returned from this endpoint. The current-price endpoint is sometimes empty. "
            "Try: --variety-wise, or copy the exact API URL from the data.gov.in Data API tab using --api-url."
        )

    df = pd.DataFrame(all_records)
    df.to_csv(output, index=False, encoding="utf-8")
    print(f"Saved {len(df)} records to {output}")


def try_download_dataset(
    api_urls: list[str],
    api_key: str,
    output: Path,
    limit: int,
    max_records: int,
    timeout: int,
    retries: int,
    sleep_seconds: float,
) -> None:
    errors: list[str] = []
    for api_url in api_urls:
        print(f"Trying API URL: {api_url}")
        try:
            download_dataset(
                api_url=api_url,
                api_key=api_key,
                output=output,
                limit=limit,
                max_records=max_records,
                timeout=timeout,
                retries=retries,
                sleep_seconds=sleep_seconds,
            )
            return
        except Exception as exc:
            error = f"{api_url} -> {exc}"
            errors.append(error)
            print(f"Failed: {error}")

    joined_errors = "\n".join(errors)
    raise RuntimeError(
        "All known data.gov.in API URL patterns failed.\n"
        "Best next option: download an AGMARKNET-derived Kaggle CSV and place it in data/raw/.\n\n"
        f"Errors:\n{joined_errors}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download official mandi prices from data.gov.in as CSV.")
    parser.add_argument("--api-url", default=None, help="Exact data.gov.in API URL copied from the Data API tab.")
    parser.add_argument(
        "--source",
        choices=["auto", "current", "variety", "legacy", "legacy_plural"],
        default="auto",
        help="Which data.gov.in endpoint pattern to use.",
    )
    parser.add_argument("--variety-wise", action="store_true", help="Use the official variety-wise daily market prices endpoint.")
    parser.add_argument("--legacy-url", action="store_true", help="Use the older data.gov.in /resources/.../api endpoint.")
    parser.add_argument("--api-key", required=True, help="Your data.gov.in API key.")
    parser.add_argument("--output", default="data/raw/agmarknet_current_mandi_prices.csv", help="Output CSV path.")
    parser.add_argument("--limit", type=int, default=100, help="Records per API page. Keep this low if data.gov.in is slow.")
    parser.add_argument("--max-records", type=int, default=20000, help="Maximum records to download.")
    parser.add_argument("--timeout", type=int, default=180, help="Read timeout in seconds per request.")
    parser.add_argument("--retries", type=int, default=5, help="Retry attempts per page.")
    parser.add_argument("--sleep", type=float, default=3.0, help="Base sleep seconds between retries.")
    args = parser.parse_args()

    if args.api_url:
        api_urls = [args.api_url]
    elif args.variety_wise:
        api_urls = [VARIETY_WISE_API_URL]
    elif args.legacy_url:
        api_urls = [LEGACY_API_URL, LEGACY_PLURAL_API_URL]
    elif args.source == "auto":
        api_urls = [CURRENT_API_URL, LEGACY_API_URL, LEGACY_PLURAL_API_URL, VARIETY_WISE_API_URL]
    else:
        api_urls = [API_URLS[args.source]]

    try_download_dataset(
        api_urls=api_urls,
        api_key=args.api_key,
        output=Path(args.output),
        limit=args.limit,
        max_records=args.max_records,
        timeout=args.timeout,
        retries=args.retries,
        sleep_seconds=args.sleep,
    )


if __name__ == "__main__":
    main()
