# MarketMitra AI

MarketMitra AI is an agricultural market intelligence dashboard that helps farmers decide when and where to sell produce. It combines mandi price data, price trend analysis, short-term forecasting, market pressure signals, and GenAI-generated advisory reports.

## What This MVP Includes

- Commodity market data loader with AGMARKNET/data.gov.in-ready schema.
- Original dataset enforcement for hackathon compliance.
- Price trend analytics with moving averages, volatility, and market comparison.
- Forecasting layer with Prophet when available and a robust baseline fallback.
- Sell, hold, split, or transport recommendation engine.
- Polished multipage Streamlit + Plotly dashboard for judges and mentors.
- GenAI report generator with no-key template fallback.

## Recommended Data Strategy

- Primary: AGMARKNET/data.gov.in mandi prices.
- Backup/historical seed: Kaggle agricultural commodity price datasets.
- Supplemental: FAOSTAT, MSP, weather, crop calendars, and transport distance.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app requires an original dataset. Place an AGMARKNET/data.gov.in/Kaggle CSV in `data/raw/` before running. The home screen opens from `app.py`; use the `Market Filters` page to choose the active commodity, mandi, forecast model, and cost assumptions. Individual deliverables are available as separate Streamlit pages in the sidebar.

## Add Your Own Data

Place an original CSV in `data/raw/` with fields similar to:

```text
date, state, district, market, commodity, variety, grade, min_price, max_price, modal_price, arrivals_tonnes
```

The cleaning layer also recognizes common AGMARKNET/data.gov.in column names such as `State`, `District`, `Market`, `Commodity`, `Variety`, `Grade`, `Min Price`, `Max Price`, `Modal Price`, and `Arrival_Date`.

Important: synthetic/demo data fallback is disabled. If no original CSV exists in `data/raw/`, the app stops and asks for the dataset.

## If data.gov.in CSV Download Fails

Use the Data API instead of the CSV button:

1. Open the data.gov.in mandi dataset page.
2. Click `Data API`.
3. Generate or copy your API key from data.gov.in.
4. Run:

```bash
python scripts/download_data_gov_mandi.py --api-key YOUR_DATA_GOV_API_KEY
```

This saves:

```text
data/raw/agmarknet_current_mandi_prices.csv
```

Then start the dashboard:

```bash
streamlit run app.py
```

## Prepare One Final Dataset From Multiple Original CSVs

If you downloaded multiple original files, combine them into one final dataset:

```bash
python scripts/prepare_final_dataset.py
```

This creates:

```text
data/raw/final_marketmitra_dataset.csv
```

## Run Tests

```bash
python -m compileall src app.py pages
```

## Hackathon Pitch

MarketMitra AI is not just a mandi price dashboard. It is a selling decision engine that tells farmers whether to sell today, hold, split quantity, or transport to another mandi, with expected gain, risk, confidence, and a farmer-friendly explanation.

## GenAI Features

- Groq and Gemini report generation.
- Multilingual weekly reports through live LLM APIs.
- Grounded AI assistant using selected market context.
- ChromaDB vector-store RAG over forecast-ready market knowledge documents.
- Markdown and PDF report download.
- Optional saved reports in `data/reports`.

Test API keys:

```bash
python scripts/test_genai_keys.py --provider all
```

Build the RAG index:

```bash
python scripts/build_rag_index.py --reset --min-dates 90 --limit 500
```


