"""2단계: narrative(서술) JSON + 수집된 market_data JSON을 인포그래픽 PNG로 렌더링해 이메일로 보낸다.

사용 예:
    python3 -m scripts.send_infographic --narrative data/narrative_2026-07-16.json

narrative JSON은 data/market_data_<date>.json 을 읽고 판단한 해석 결과를 담아
클라우드 예약 에이전트(또는 사용자)가 직접 작성한다. 스키마는 scripts/narrative_schema.py 참고.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .config import ROOT_DIR
from .emailer import send_infographic_email
from .infographic import build_html, render_png

DATA_DIR = ROOT_DIR / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--narrative", required=True, help="narrative JSON 파일 경로")
    parser.add_argument("--market-data", help="market_data JSON 경로 (기본값: narrative의 date로 data/market_data_<date>.json 추정)")
    parser.add_argument("--out", help="PNG 출력 경로 (기본값: data/report_<date>.png)")
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 없이 PNG만 생성")
    args = parser.parse_args()

    narrative = json.loads(Path(args.narrative).read_text())
    report_date = date.fromisoformat(narrative["date"]) if narrative.get("date") else date.today()

    market_data_path = Path(args.market_data) if args.market_data else DATA_DIR / f"market_data_{report_date.isoformat()}.json"
    market_data = json.loads(market_data_path.read_text())

    out_path = Path(args.out) if args.out else DATA_DIR / f"report_{report_date.isoformat()}.png"

    html = build_html(market_data, narrative)
    render_png(html, out_path)
    print(f"Rendered: {out_path}")

    if args.dry_run:
        print("Dry run — skipping email send.")
        return

    send_infographic_email(out_path, report_date)
    print("Email sent.")


if __name__ == "__main__":
    main()
