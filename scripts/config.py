"""환경 변수 로딩 (config/secrets.env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
SECRETS_PATH = ROOT_DIR / "config" / "secrets.env"

load_dotenv(SECRETS_PATH)


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. See config/secrets.env.example")
    return value


class Settings:
    FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
    EIA_API_KEY = os.environ.get("EIA_API_KEY", "")
    EXIM_API_KEY = os.environ.get("EXIM_API_KEY", "")

    KIS_APP_KEY = os.environ.get("KIS_APP_KEY", "")
    KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET", "")

    TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
    FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "")
    REPORT_TO_EMAIL = os.environ.get("REPORT_TO_EMAIL", "")


settings = Settings()
