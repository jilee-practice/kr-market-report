"""Finnhub API로 미국 관심 종목(반도체 관련주 등) 시세와 실적 발표 일정을 가져온다."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import date, timedelta

import requests

from .config import settings

QUOTE_URL = "https://finnhub.io/api/v1/quote"
EARNINGS_URL = "https://finnhub.io/api/v1/calendar/earnings"

_REQUEST_DELAY_SECONDS = 1.0  # 무료 티어: 분당 60 호출
EARNINGS_LOOKAHEAD_DAYS = 30

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
    history: list[float] = field(default_factory=list)  # 과거->최신 순 종가 (Twelve Data로 채워짐)


def _fetch_quote(ticker: str, label: str) -> Quote | None:
    resp = requests.get(QUOTE_URL, params={"symbol": ticker, "token": settings.FINNHUB_API_KEY}, timeout=15)
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


@dataclass
class EarningsEvent:
    ticker: str
    label: str
    date: str
    hour: str  # "bmo"=장전, "amc"=장마감후, ""=미정
    eps_estimate: float | None


def get_earnings_calendar(tickers: dict[str, str] | None = None) -> list[EarningsEvent]:
    """관심 종목 중 앞으로 EARNINGS_LOOKAHEAD_DAYS일 내 실적 발표가 예정된 것만 골라온다.
    Finnhub 캘린더는 전체 시장分 한 번에 내려주므로 워치리스트로 필터링한다."""
    tickers = tickers or _parse_watchlist_env()
    today = date.today()
    resp = requests.get(
        EARNINGS_URL,
        params={
            "from": today.isoformat(),
            "to": (today + timedelta(days=EARNINGS_LOOKAHEAD_DAYS)).isoformat(),
            "token": settings.FINNHUB_API_KEY,
        },
        timeout=20,
    )
    resp.raise_for_status()
    rows = resp.json().get("earningsCalendar", [])

    events = []
    for row in rows:
        ticker = row.get("symbol")
        if ticker not in tickers:
            continue
        events.append(
            EarningsEvent(
                ticker=ticker,
                label=tickers[ticker],
                date=row["date"],
                hour=row.get("hour", ""),
                eps_estimate=row.get("epsEstimate"),
            )
        )
    events.sort(key=lambda e: e.date)
    return events
