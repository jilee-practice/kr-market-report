"""Resend API(HTTPS)로 인포그래픽 리포트를 발송한다.

원래는 Gmail SMTP(587)를 썼지만, 클라우드 예약 에이전트 샌드박스의 아웃바운드
프록시가 HTTPS(443) 외의 프로토콜/포트를 지원하지 않아 SMTP 자체가 불가능했다.
Resend는 순수 HTTPS REST API라 동일한 프록시 제약에서도 정상 동작한다.
"""
from __future__ import annotations

import base64
from datetime import date
from pathlib import Path

import requests

from .config import settings

RESEND_API_URL = "https://api.resend.com/emails"


def send_infographic_email(image_path: Path, report_date: date | None = None) -> None:
    report_date = report_date or date.today()

    # Gmail은 <img src="data:..."> 형태의 base64 인라인 이미지를 렌더링하지 않으므로,
    # 진짜 첨부파일 + Content-ID 참조(cid:)로 보내야 본문에 이미지가 표시된다.
    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    html = '<html><body style="margin:0;padding:0;"><img src="cid:report_image" style="width:100%;max-width:1080px;"></body></html>'

    resp = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": settings.RESEND_FROM_EMAIL,
            "to": [settings.REPORT_TO_EMAIL],
            "subject": f"[KR Market Report] {report_date.isoformat()}",
            "html": html,
            "attachments": [
                {
                    "filename": Path(image_path).name,
                    "content": image_b64,
                    "content_id": "report_image",
                }
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
