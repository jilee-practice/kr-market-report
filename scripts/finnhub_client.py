"""Finnhub API로 미국 관심 종목(반도체 관련주 등) 시세를 가져온다."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests

from .config import settings

BASE_URL = "https://finnhub.io/api/v1/quote"

_REQUEST_DELAY_SECONDS = 1.0  # 무료 티어: 분당 60 호출

DEFAULT_WATCHLIST = {
    "MU": "마이크론",
    "IBM": "IBM",
    "ASML": "ASML",
    "TSM": "TSMC",
    "NVDA": "엔비디아",
    "INTC": "인텔",
}


def _parse_watchlist_env() -> dict[str, str]:
    raw = os.environ.get("WATCHLIST_TICKERS", "")
    if not raw:
        return DEFAULT_WATCHLIST
    result = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            ticker, label = item.split(":", 1)
        else:
            ticker, label = item, item
        result[ticker.strip()] = label.strip()
    return result


@dataclass
class Quote:
    ticker: str
    label: str
    price: float
    change: float
    change_pct: float


def _fetch_quote(ticker: str, label: str) -> Quote | None:
    resp = requests.get(BASE_URL, params={"symbol": ticker, "token": settings.FINNHUB_API_KEY}, timeout=15)
    data = resp.json()
    if not data.get("c"):
        return None
    return Quote(
        ticker=ticker,
        label=label,
        price=float(data["c"]),
        change=float(data["d"]),
        change_pct=float(data["dp"]),
    )


def get_watchlist() -> list[Quote]:
    watchlist = _parse_watchlist_env()
    quotes = []
    for i, (ticker, label) in enumerate(watchlist.items()):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)
        quote = _fetch_quote(ticker, label)
        if quote is not None:
            quotes.append(quote)
    return quotes
