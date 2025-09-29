"""슬랙 알림. Slack notifications."""

from __future__ import annotations

import logging
import os

import httpx

from wv.core.models import NotificationMessage

LOGGER = logging.getLogger(__name__)


def send_slack(message: NotificationMessage, *, dry_run: bool = False) -> None:
    """슬랙 웹훅 전송. Send Slack webhook."""

    webhook = os.getenv("WV_SLACK_WEBHOOK")
    if dry_run or not webhook:
        LOGGER.info("Dry-run Slack notification: %s", message.subject)
        LOGGER.debug("Body:\n%s", message.body)
        return
    payload = {"text": f"*{message.subject}*\n{message.body}"}
    try:
        response = httpx.post(webhook, json=payload, timeout=10)
        response.raise_for_status()
        LOGGER.info("Slack notification delivered")
    except httpx.HTTPError as exc:
        LOGGER.error("Slack delivery failed: %s", exc)
        raise


__all__ = ["send_slack"]
