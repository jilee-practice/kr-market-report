"""yfinance로 미국 지수 및 반도체 관련 관심 종목 시세를 가져온다.

FRED/EIA/EXIM/KIS 조합만으로는 다우/S&P500/나스닥/필라델피아 반도체지수나
개별 종목(마이크론, IBM, ASML 등) 등락률을 얻을 수 없어 yfinance로 보완한다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import yfinance as yf

# ticker: 표시 이름
US_INDICES = {
    "^DJI": "다우",
    "^GSPC": "S&P500",
    "^IXIC": "나스닥",
    "^SOX": "필라델피아 반도체지수",
}

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
    hist = yf.Ticker(ticker).history(period="5d")
    if len(hist) < 2:
        return None
    latest = hist.iloc[-1]
    prev = hist.iloc[-2]
    price = float(latest["Close"])
    prev_close = float(prev["Close"])
    change = price - prev_close
    change_pct = change / prev_close * 100
    return Quote(ticker=ticker, label=label, price=price, change=change, change_pct=change_pct)


def get_us_indices() -> list[Quote]:
    quotes = [_fetch_quote(t, label) for t, label in US_INDICES.items()]
    return [q for q in quotes if q is not None]


def get_watchlist() -> list[Quote]:
    watchlist = _parse_watchlist_env()
    quotes = [_fetch_quote(t, label) for t, label in watchlist.items()]
    return [q for q in quotes if q is not None]
