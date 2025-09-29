"""애플리케이션 설정 로딩. | Application configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from .core.risk import RiskRules

load_dotenv()


@dataclass(frozen=True)
class ProviderConfig:
    """프로바이더 설정 값. | Provider configuration values."""

    stormglass_key: Optional[str]
    stormglass_endpoint: Optional[str]
    copernicus_key: Optional[str]
    copernicus_endpoint: Optional[str]


@dataclass(frozen=True)
class NotificationConfig:
    """알림 설정 값. | Notification configuration values."""

    email_from: Optional[str]
    email_to: List[str]
    smtp_host: Optional[str]
    smtp_port: int
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    slack_webhook: Optional[str]
    telegram_token: Optional[str]
    telegram_chat_id: Optional[str]


@dataclass(frozen=True)
class AppConfig:
    """전역 설정 컨테이너. | Global configuration container."""

    cache_dir: Path
    output_dir: Path
    provider: ProviderConfig
    notification: NotificationConfig
    risk_rules: RiskRules


def load_config() -> AppConfig:
    """환경 변수에서 설정 로드. | Load configuration from environment."""

    cache_dir = Path(os.getenv("WV_CACHE_DIR", "~/.wv/cache")).expanduser()
    output_dir = Path(os.getenv("WV_OUTPUT_DIR", "outputs")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    provider = ProviderConfig(
        stormglass_key=os.getenv("STORMGLASS_API_KEY"),
        stormglass_endpoint=os.getenv("STORMGLASS_ENDPOINT"),
        copernicus_key=os.getenv("COPERNICUS_API_KEY"),
        copernicus_endpoint=os.getenv("COPERNICUS_ENDPOINT"),
    )

    notification = NotificationConfig(
        email_from=os.getenv("WV_EMAIL_FROM"),
        email_to=[addr.strip() for addr in os.getenv("WV_EMAIL_TO", "").split(",") if addr.strip()],
        smtp_host=os.getenv("WV_SMTP_HOST"),
        smtp_port=int(os.getenv("WV_SMTP_PORT", "587")),
        smtp_username=os.getenv("WV_SMTP_USERNAME"),
        smtp_password=os.getenv("WV_SMTP_PASSWORD"),
        slack_webhook=os.getenv("WV_SLACK_WEBHOOK"),
        telegram_token=os.getenv("WV_TELEGRAM_TOKEN"),
        telegram_chat_id=os.getenv("WV_TELEGRAM_CHAT_ID"),
    )

    risk_rules = RiskRules(
        medium_hs=float(os.getenv("WV_MEDIUM_HS", "2.0")),
        high_hs=float(os.getenv("WV_HIGH_HS", "3.0")),
        medium_wind=float(os.getenv("WV_MEDIUM_WIND", "22.0")),
        high_wind=float(os.getenv("WV_HIGH_WIND", "28.0")),
    )

    return AppConfig(
        cache_dir=cache_dir,
        output_dir=output_dir,
        provider=provider,
        notification=notification,
        risk_rules=risk_rules,
    )
