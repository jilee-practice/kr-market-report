"""Twelve Data API로 미국 지수(+최근 추이)를 가져온다.

Twelve Data 무료 티어는 실제 지수(예: DJI) 접근이 제한돼 있어, 대신 각
지수를 추종하는 ETF(다우->DIA, S&P500->SPY, 나스닥종합->ONEQ,
필라델피아반도체->SOXX)의 등락률을 대리 지표로 쓴다. 무료 티어 레이트리밋은
분당 8 크레딧이라 호출 사이에 지연을 둔다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from .config import settings

TIME_SERIES_URL = "https://api.twelvedata.com/time_series"

_REQUEST_DELAY_SECONDS = 8  # 무료 티어: 분당 8 크레딧
HISTORY_DAYS = 15

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
    history: list[float] = field(default_factory=list)  # 과거->최신 순 종가


def _fetch_quote(ticker: str, label: str) -> Quote | None:
    resp = requests.get(
        TIME_SERIES_URL,
        params={"symbol": ticker, "interval": "1day", "outputsize": HISTORY_DAYS, "apikey": settings.TWELVEDATA_API_KEY},
        timeout=15,
    )
    data = resp.json()
    values = data.get("values")
    if not values or len(values) < 2:
        return None

    latest_close = float(values[0]["close"])
    prev_close = float(values[1]["close"])
    change = latest_close - prev_close
    change_pct = change / prev_close * 100
    history = [float(v["close"]) for v in reversed(values)]

    return Quote(ticker=ticker, label=label, price=latest_close, change=change, change_pct=change_pct, history=history)


def get_us_indices() -> list[Quote]:
    quotes = []
    for i, (ticker, label) in enumerate(US_INDEX_PROXIES.items()):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)
        quote = _fetch_quote(ticker, label)
        if quote is not None:
            quotes.append(quote)
    return quotes


def get_history_map(tickers: dict[str, str]) -> dict[str, list[float]]:
    """관심 종목 등 임의 티커의 최근 종가 추이만 필요할 때 쓴다 (배지 스파크라인용).
    가격/등락률 자체는 Finnhub 등 다른 소스가 이미 담당하는 경우를 위한 보조 함수."""
    history_map: dict[str, list[float]] = {}
    for i, (ticker, label) in enumerate(tickers.items()):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)
        quote = _fetch_quote(ticker, label)
        if quote is not None:
            history_map[ticker] = quote.history
    return history_map
