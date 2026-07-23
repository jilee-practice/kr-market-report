"""Twelve Data API로 미국 지수를 가져온다.

Twelve Data 무료 티어는 실제 지수(예: DJI) 접근이 제한돼 있어, 대신 각
지수를 추종하는 ETF(다우->DIA, 나스닥종합->ONEQ, 필라델피아반도체->SOXX)의
등락률을 대리 지표로 쓴다. 무료 티어 레이트리밋은 분당 8 크레딧이라 호출
사이에 지연을 둔다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from .config import settings

BASE_URL = "https://api.twelvedata.com/quote"

_REQUEST_DELAY_SECONDS = 8  # 무료 티어: 분당 8 크레딧

# ticker: 표시 이름 (실제 지수를 추종하는 ETF)
US_INDEX_PROXIES = {
    "DIA": "다우",
    "SPY": "S&P500",
    "ONEQ": "나스닥",
    "SOXX": "필라델피아 반도체지수",
}


@dataclass
class Quote:
    ticker: str
    label: str
    price: float
    change: float
    change_pct: float


def _fetch_quote(ticker: str, label: str) -> Quote | None:
    resp = requests.get(BASE_URL, params={"symbol": ticker, "apikey": settings.TWELVEDATA_API_KEY}, timeout=15)
    data = resp.json()
    if data.get("status") == "error" or "close" not in data:
        return None
    return Quote(
        ticker=ticker,
        label=label,
        price=float(data["close"]),
        change=float(data["change"]),
        change_pct=float(data["percent_change"]),
    )


def get_us_indices() -> list[Quote]:
    quotes = []
    for i, (ticker, label) in enumerate(US_INDEX_PROXIES.items()):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)
        quote = _fetch_quote(ticker, label)
        if quote is not None:
            quotes.append(quote)
    return quotes
