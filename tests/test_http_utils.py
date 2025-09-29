import httpx
import pytest

from wv.providers.base import ProviderError
from wv.utils import http as http_utils


def test_request_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx, "request", fake_request)
    data = http_utils.request_json("GET", "https://example.com")
    assert data["ok"] is True


def test_request_json_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        calls["count"] += 1
        if calls["count"] < 2:
            return httpx.Response(429, text="rate limited")
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx, "request", fake_request)
    monkeypatch.setattr(http_utils.time, "sleep", lambda s: None)
    data = http_utils.request_json("GET", "https://example.com", retries=1)
    assert data["ok"] is True


def test_request_json_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "request", fake_request)
    with pytest.raises(ProviderError):
        http_utils.request_json("GET", "https://example.com", retries=0)
