"""한국수출입은행 환율 API에서 원화 환율을 가져온다."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import requests

from .config import settings

BASE_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"

# 통화 단위(cur_unit): 표시 이름
CURRENCIES = {
    "USD": "미국 달러",
    "JPY(100)": "일본 엔(100엔)",
    "EUR": "유로",
    "CNH": "위안화",
}

MAX_LOOKBACK_DAYS = 7  # 주말/공휴일에는 데이터가 없어 최근 영업일까지 거슬러 조회


@dataclass
class FxRate:
    cur_unit: str
    label: str
    date: str
    deal_bas_r: float  # 매매기준율


def _fetch_rates_for_date(search_date: date) -> list[dict]:
    params = {
        "authkey": settings.EXIM_API_KEY,
        "searchdate": search_date.strftime("%Y%m%d"),
        "data": "AP01",
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_fx_rates() -> list[FxRate]:
    search_date = date.today()
    rows: list[dict] = []
    used_date = search_date

    for _ in range(MAX_LOOKBACK_DAYS):
        rows = _fetch_rates_for_date(search_date)
        if rows:
            used_date = search_date
            break
        search_date -= timedelta(days=1)

    by_unit = {row["cur_unit"]: row for row in rows}

    results = []
    for cur_unit, label in CURRENCIES.items():
        row = by_unit.get(cur_unit)
        if not row:
            continue
        deal_bas_r = float(row["deal_bas_r"].replace(",", ""))
        results.append(
            FxRate(
                cur_unit=cur_unit,
                label=label,
                date=used_date.isoformat(),
                deal_bas_r=deal_bas_r,
            )
        )
    return results
