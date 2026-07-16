"""yfinance로 국내외 지수 및 반도체 관련 관심 종목 시세를 가져온다.

FRED/EIA/EXIM 조합만으로는 다우/S&P500/나스닥/필라델피아 반도체지수나
개별 종목(마이크론, IBM, ASML 등) 등락률을 얻을 수 없어 yfinance로 보완한다.
KOSPI/KOSDAQ도 KIS Open API가 클라우드 실행 환경에서 비표준 포트(9443)로 인해
막히는 경우가 있어 yfinance(^KS11/^KQ11)를 기본으로 사용한다.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import yfinance as yf

# 티커를 연속으로 빠르게 요청하면 Yahoo Finance가 봇 트래픽으로 보고 429를 돌려주는
# 경우가 있어, 요청 사이 간격을 두고 실패 시 짧게 재시도한다.
_REQUEST_DELAY_SECONDS = 1.5
_MAX_ATTEMPTS = 3

# ticker: 표시 이름
KR_INDICES = {
    "^KS11": "KOSPI",
    "^KQ11": "KOSDAQ",
}

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
    last_error: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
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
        except Exception as exc:  # noqa: BLE001 - retry on any transient fetch failure (e.g. rate limiting)
            last_error = exc
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_REQUEST_DELAY_SECONDS * attempt * 2)
    raise RuntimeError(f"Failed to fetch {ticker} after {_MAX_ATTEMPTS} attempts") from last_error


def _fetch_quotes(items: dict[str, str]) -> list[Quote]:
    quotes = []
    for i, (ticker, label) in enumerate(items.items()):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)
        quote = _fetch_quote(ticker, label)
        if quote is not None:
            quotes.append(quote)
    return quotes


def get_us_indices() -> list[Quote]:
    return _fetch_quotes(US_INDICES)


def get_watchlist() -> list[Quote]:
    return _fetch_quotes(_parse_watchlist_env())


@dataclass
class IndexPrice:
    """kis_client.IndexPrice와 같은 필드명 (infographic.py의 indices 카드가 이 형태를 기대함)."""

    index_code: str
    label: str
    price: float
    change: float
    change_rate: float


def get_kr_indices() -> list[IndexPrice]:
    quotes = _fetch_quotes(KR_INDICES)
    return [
        IndexPrice(index_code=q.ticker, label=q.label, price=q.price, change=q.change, change_rate=q.change_pct)
        for q in quotes
    ]
