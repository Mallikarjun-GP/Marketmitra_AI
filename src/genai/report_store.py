from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from src.config import REPORTS_DIR


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def save_report_text(commodity: str, market: str, provider: str, report_text: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{_slug(commodity)}_{_slug(market)}_{_slug(provider)}.md"
    path = REPORTS_DIR / filename
    path.write_text(report_text, encoding="utf-8")
    return path


def save_report_pdf(commodity: str, market: str, provider: str, pdf_bytes: bytes) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{_slug(commodity)}_{_slug(market)}_{_slug(provider)}.pdf"
    path = REPORTS_DIR / filename
    path.write_bytes(pdf_bytes)
    return path
