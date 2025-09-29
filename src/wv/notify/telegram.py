"""텔레그램 알림. Telegram notifications."""

from __future__ import annotations

import logging
import os

import httpx

from wv.core.models import NotificationMessage

LOGGER = logging.getLogger(__name__)


def send_telegram(message: NotificationMessage, *, dry_run: bool = False) -> None:
    """텔레그램 봇 메시지. Send Telegram message."""

    token = os.getenv("WV_TELEGRAM_TOKEN")
    chat_id = os.getenv("WV_TELEGRAM_CHAT_ID")
    if dry_run or not token or not chat_id:
        LOGGER.info("Dry-run Telegram notification: %s", message.subject)
        LOGGER.debug("Body:\n%s", message.body)
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"{message.subject}\n{message.body}"}
    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        LOGGER.info("Telegram notification delivered")
    except httpx.HTTPError as exc:
        LOGGER.error("Telegram delivery failed: %s", exc)
        raise


__all__ = ["send_telegram"]
