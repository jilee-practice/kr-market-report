"""네이버 금융의 공개(비공식) 시세 API로 KOSPI/KOSDAQ(+최근 추이)을 가져온다.

Twelve Data/Finnhub 둘 다 무료 티어에서는 KRX(한국거래소) 데이터를 지원하지
않아, 별도 인증 없이 접근 가능한 네이버 금융 API로 국내 지수만 받는다.
비공식 API라 필드가 바뀔 수 있으니 주의.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import requests

PRICE_URL = "https://m.stock.naver.com/api/index/{code}/price"

HISTORY_DAYS = 15

# 표시 이름: 네이버 지수 코드
INDICES = {
    "KOSPI": "KOSPI",
    "KOSDAQ": "KOSDAQ",
}


@dataclass
class IndexPrice:
    """kis_client.IndexPrice와 같은 필드명 (infographic.py의 indices 카드가 이 형태를 기대함)."""

    index_code: str
    label: str
    price: float
    change: float
    change_rate: float
    history: list[float] = field(default_factory=list)  # 과거->최신 순 종가


def _fetch_index(code: str, label: str) -> IndexPrice | None:
    resp = requests.get(
        PRICE_URL.format(code=code),
        params={"pageSize": HISTORY_DAYS, "page": 1},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    rows = resp.json()  # 최신 -> 과거 순
    if not rows:
        return None

    latest = rows[0]
    sign = -1 if latest["compareToPreviousPrice"]["name"] == "FALLING" else 1
    history = [float(r["closePrice"].replace(",", "")) for r in reversed(rows)]

    return IndexPrice(
        index_code=code,
        label=label,
        price=float(latest["closePrice"].replace(",", "")),
        change=sign * float(latest["compareToPreviousClosePrice"].replace(",", "").lstrip("-")),
        change_rate=sign * float(latest["fluctuationsRatio"].replace(",", "").lstrip("-")),
        history=history,
    )


def get_kr_indices() -> list[IndexPrice]:
    results = []
    for code, label in INDICES.items():
        idx = _fetch_index(code, label)
        if idx is not None:
            results.append(idx)
    return results
