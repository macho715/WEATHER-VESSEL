from wv.core.models import NotificationChannel, NotificationMessage
from wv.core.scheduler import contextual_channel
from wv.notify.email import send_email
from wv.notify.slack import send_slack
from wv.notify.telegram import send_telegram


def _notification() -> NotificationMessage:
    return NotificationMessage(subject="Test", body="Body", channel=NotificationChannel.EMAIL)


def test_email_dry_run(caplog) -> None:
    message = _notification()
    caplog.set_level("INFO")
    send_email(message, ["ops@example.com"], dry_run=True)
    assert "Dry-run email" in caplog.text


def test_slack_dry_run(caplog) -> None:
    message = _notification()
    caplog.set_level("INFO")
    send_slack(message, dry_run=True)
    assert "Dry-run Slack" in caplog.text


def test_telegram_dry_run(caplog) -> None:
    message = _notification()
    caplog.set_level("INFO")
    send_telegram(message, dry_run=True)
    assert "Dry-run Telegram" in caplog.text


def test_contextual_channel_default() -> None:
    assert contextual_channel() is NotificationChannel.EMAIL
