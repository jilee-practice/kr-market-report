"""Gmail SMTP(앱 비밀번호)로 인포그래픽 리포트를 발송한다."""
from __future__ import annotations

import smtplib
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from .config import settings

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_infographic_email(image_path: Path, report_date: date | None = None) -> None:
    report_date = report_date or date.today()

    msg = MIMEMultipart("related")
    msg["Subject"] = f"[KR Market Report] {report_date.isoformat()}"
    msg["From"] = settings.GMAIL_ADDRESS
    msg["To"] = settings.REPORT_TO_EMAIL

    body = MIMEText(
        f'<html><body style="margin:0;padding:0;"><img src="cid:report_image" style="width:100%;max-width:1080px;"></body></html>',
        "html",
    )
    msg.attach(body)

    image_bytes = Path(image_path).read_bytes()
    image = MIMEImage(image_bytes)
    image.add_header("Content-ID", "<report_image>")
    image.add_header("Content-Disposition", "inline", filename=Path(image_path).name)
    msg.attach(image)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
        server.sendmail(settings.GMAIL_ADDRESS, [settings.REPORT_TO_EMAIL], msg.as_string())
