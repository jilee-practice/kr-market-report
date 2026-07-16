"""EIA(U.S. Energy Information Administration)에서 유가 스팟 가격을 가져온다."""
from __future__ import annotations

from dataclasses import dataclass

import requests

from .config import settings

BASE_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"

# series id: 표시 이름
SERIES = {
    "RWTC": "WTI 현물유가 ($/bbl)",
    "RBRTE": "브렌트유 현물유가 ($/bbl)",
}


@dataclass
class OilPrice:
    series_id: str
    label: str
    date: str
    value: float
    prev_date: str | None
    prev_value: float | None

    @property
    def change(self) -> float | None:
        if self.prev_value is None:
            return None
        return self.value - self.prev_value


def _fetch_series(series_id: str) -> list[dict]:
    params = {
        "api_key": settings.EIA_API_KEY,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 2,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()["response"]["data"]


def get_oil_prices() -> list[OilPrice]:
    results = []
    for series_id, label in SERIES.items():
        rows = _fetch_series(series_id)
        latest = rows[0]
        prev = rows[1] if len(rows) > 1 else None
        results.append(
            OilPrice(
                series_id=series_id,
                label=label,
                date=latest["period"],
                value=float(latest["value"]),
                prev_date=prev["period"] if prev else None,
                prev_value=float(prev["value"]) if prev else None,
            )
        )
    return results
