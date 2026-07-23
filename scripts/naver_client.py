"""네이버 금융의 공개(비공식) 실시간 시세 API로 KOSPI/KOSDAQ을 가져온다.

Twelve Data/Finnhub 둘 다 무료 티어에서는 KRX(한국거래소) 데이터를 지원하지
않아, 별도 인증 없이 접근 가능한 네이버 금융 폴링 API로 국내 지수만 받는다.
비공식 API라 필드가 바뀔 수 있으니 주의.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

BASE_URL = "https://polling.finance.naver.com/api/realtime/domestic/index/KOSPI,KOSDAQ"

LABELS = {
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


def get_kr_indices() -> list[IndexPrice]:
    resp = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    datas = resp.json()["datas"]

    results = []
    for item in datas:
        code = item["itemCode"]
        label = LABELS.get(code, code)
        price = float(item["closePriceRaw"])
        change_magnitude = float(item["compareToPreviousClosePriceRaw"])
        pct_magnitude = float(item["fluctuationsRatioRaw"])
        sign = -1 if item["compareToPreviousPrice"]["name"] == "FALLING" else 1
        results.append(
            IndexPrice(
                index_code=code,
                label=label,
                price=price,
                change=sign * change_magnitude,
                change_rate=sign * pct_magnitude,
            )
        )
    return results
