"""1단계: EXIM/FRED/EIA/Naver/TwelveData/Finnhub에서 지표를 수집해
data/market_data_<date>.json으로 저장한다.

클라우드 예약 에이전트가 이 스크립트을 먼저 실행해 수치 데이터를 읽고,
그 데이터를 근거로 서술형 해석(narrative)을 직접 작성한 뒤
scripts/send_infographic.py 로 넘겨 이미지를 만들고 이메일을 보낸다.

- KOSPI/KOSDAQ: 원래 KIS Open API(kis_client.py) → 비표준 포트(9443)가 클라우드
  프록시에 막혀 yfinance로, 이후 yfinance도 클라우드에서 curl_cffi/프록시 충돌 및
  레이트리밋으로 계속 실패해 지금은 네이버 금융 공개 API(naver_client.py)를 쓴다.
- 미국 지수: Twelve Data 무료 티어는 실지수 접근이 막혀있어 ETF 대리 지표를 쓴다
  (twelvedata_client.py).
- 관심 종목(반도체 관련주): Finnhub(finnhub_client.py).

kis_client.py/yfinance_client.py는 로컬 등 해당 소스 접속이 가능한 환경에서
대안으로 쓸 수 있도록 레포에 남겨뒀다.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
from datetime import date
from pathlib import Path

from . import eia_client, exim_client, finnhub_client, fred_client, naver_client, twelvedata_client
from .config import ROOT_DIR

DATA_DIR = ROOT_DIR / "data"


def _best_effort(label: str, fn):
    """외부 무료/비공식 데이터 소스는 가끔 통째로 실패할 수 있어, 이 소스가 죽어도
    FX/금리/유가 등 나머지는 정상 발송되도록 실패를 흡수한다."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        print(f"[collect_data] WARNING: {label} 수집 실패, 이 섹션은 비워둡니다: {exc}")
        return []


def collect(report_date: date | None = None) -> dict:
    report_date = report_date or date.today()

    indices = _best_effort("KOSPI/KOSDAQ (Naver)", naver_client.get_kr_indices)
    fx_rates = exim_client.get_fx_rates()
    rates = fred_client.get_rates()
    oil_prices = eia_client.get_oil_prices()
    us_indices = _best_effort("미국 지수 (Twelve Data)", twelvedata_client.get_us_indices)
    watchlist = _best_effort("관심 종목 (Finnhub)", finnhub_client.get_watchlist)

    return {
        "date": report_date.isoformat(),
        "indices": [dataclasses.asdict(i) for i in indices],
        "fx_rates": [dataclasses.asdict(f) for f in fx_rates],
        "rates": [dataclasses.asdict(r) for r in rates],
        "oil_prices": [dataclasses.asdict(o) for o in oil_prices],
        "us_indices": [dataclasses.asdict(q) for q in us_indices],
        "watchlist": [dataclasses.asdict(q) for q in watchlist],
    }


def save(data: dict) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / f"market_data_{data['date']}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD (기본값: 오늘)")
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else date.today()
    data = collect(report_date)
    out_path = save(data)
    print(f"Saved: {out_path}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
