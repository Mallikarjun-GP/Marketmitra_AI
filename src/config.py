from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
CHROMA_DIR = VECTOR_STORE_DIR / "chroma"

PROCESSED_PARQUET_PATH = PROCESSED_DATA_DIR / "market_prices.parquet"
PROCESSED_CSV_PATH = PROCESSED_DATA_DIR / "market_prices.csv"

APP_TITLE = "MarketMitra AI"
APP_SUBTITLE = "Agricultural Market Intelligence and Selling Strategy Generator"

PILOT_STATES = ["Maharashtra", "Karnataka"]
PILOT_COMMODITIES = ["Onion", "Tomato", "Soybean", "Wheat", "Maize", "Cotton"]

PERISHABLE_CROPS = {"tomato", "spinach", "green peas", "cucumber", "leafy vegetables"}
HIGH_VOLATILITY_CROPS = {"onion", "tomato", "potato"}
STORABLE_CROPS = {"wheat", "soybean", "cotton", "maize", "gram", "rice"}

DEFAULT_TRANSPORT_COST_PER_QUINTAL = 80.0
DEFAULT_STORAGE_COST_PER_QUINTAL_PER_DAY = 4.0
DEFAULT_HOLD_DAYS = 7

DATA_GOV_RESOURCE = "current-daily-price-various-commodities-various-markets-mandi"
DATA_GOV_API_URL = f"https://api.data.gov.in/resource/{DATA_GOV_RESOURCE}"

RAG_COLLECTION_NAME = "marketmitra_market_knowledge"
RAG_EMBEDDING_DIMENSIONS = 384
