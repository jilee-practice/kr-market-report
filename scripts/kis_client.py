"""한국투자증권(KIS) Open API에서 국내 지수(KOSPI/KOSDAQ) 시세를 가져온다.

주의: KIS API는 tr_id/필드명이 문서 개정에 따라 바뀔 수 있으므로,
실제 사용 전 https://apiportal.koreainvestment.com 최신 문서와 대조 확인 필요.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import ROOT_DIR, settings

BASE_URL = "https://openapi.koreainvestment.com:9443"
TOKEN_CACHE_PATH = ROOT_DIR / "config" / ".kis_token.json"

# index_code: 표시 이름
INDICES = {
    "0001": "KOSPI",
    "1001": "KOSDAQ",
}


@dataclass
class IndexPrice:
    index_code: str
    label: str
    price: float
    change: float
    change_rate: float


def _load_cached_token() -> str | None:
    if not TOKEN_CACHE_PATH.exists():
        return None
    cached = json.loads(TOKEN_CACHE_PATH.read_text())
    if cached.get("expires_at", 0) > time.time() + 60:
        return cached["access_token"]
    return None


def _save_token_cache(access_token: str, expires_in: int) -> None:
    TOKEN_CACHE_PATH.write_text(
        json.dumps({"access_token": access_token, "expires_at": time.time() + expires_in})
    )


def get_access_token() -> str:
    cached = _load_cached_token()
    if cached:
        return cached

    resp = requests.post(
        f"{BASE_URL}/oauth2/tokenP",
        json={
            "grant_type": "client_credentials",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _save_token_cache(data["access_token"], data["expires_in"])
    return data["access_token"]


def _get_index_price(index_code: str, label: str) -> IndexPrice:
    token = get_access_token()
    resp = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price",
        headers={
            "authorization": f"Bearer {token}",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET,
            "tr_id": "FHPUP02100000",
        },
        params={
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
        },
        timeout=15,
    )
    resp.raise_for_status()
    output = resp.json()["output"]
    return IndexPrice(
        index_code=index_code,
        label=label,
        price=float(output["bstp_nmix_prpr"]),
        change=float(output["bstp_nmix_prdy_vrss"]),
        change_rate=float(output["bstp_nmix_prdy_ctrt"]),
    )


def get_indices() -> list[IndexPrice]:
    return [_get_index_price(code, label) for code, label in INDICES.items()]
