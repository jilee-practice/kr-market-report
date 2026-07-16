"""FRED(Federal Reserve Economic Data)에서 미국 금리 지표를 가져온다."""
from __future__ import annotations

from dataclasses import dataclass

import requests

from .config import settings

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# series_id: 표시 이름
SERIES = {
    "DGS10": "미국 10년 국채금리",
    "DGS2": "미국 2년 국채금리",
    "FEDFUNDS": "미국 기준금리(FF Rate)",
}


@dataclass
class RateObservation:
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
        "series_id": series_id,
        "api_key": settings.FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 2,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()["observations"]


def get_rates() -> list[RateObservation]:
    results = []
    for series_id, label in SERIES.items():
        obs = _fetch_series(series_id)
        latest = obs[0]
        prev = obs[1] if len(obs) > 1 else None
        results.append(
            RateObservation(
                series_id=series_id,
                label=label,
                date=latest["date"],
                value=float(latest["value"]),
                prev_date=prev["date"] if prev else None,
                prev_value=float(prev["value"]) if prev and prev["value"] != "." else None,
            )
        )
    return results
