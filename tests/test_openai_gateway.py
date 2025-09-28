"""openai_gateway FastAPI endpoints tests."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import openai_gateway  # noqa: E402

Payload = openai_gateway.MessagePayload


@pytest.fixture(autouse=True)
def _reset_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure OpenAI client globals reset for isolation."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    openai_gateway._async_client = None
    openai_gateway._dotenv_loaded = False
    yield
    openai_gateway._async_client = None
    openai_gateway._dotenv_loaded = False


def _client() -> TestClient:
    return TestClient(openai_gateway.app)


def test_healthcheck() -> None:
    """GET /health returns ok."""

    with _client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_require_client_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing OPENAI_API_KEY raises an HTTPException."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    openai_gateway._async_client = None
    openai_gateway._dotenv_loaded = False
    with pytest.raises(openai_gateway.HTTPException) as exc:
        openai_gateway._require_client()
    assert exc.value.status_code == 500
    assert "OPENAI_API_KEY" in exc.value.detail


def test_assistant_with_image_and_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assistant endpoint handles image and text attachments."""

    captured: dict[str, Any] = {}

    class FakeResponse:
        output = [
            SimpleNamespace(
                type="message",
                message=SimpleNamespace(
                    content=[SimpleNamespace(type="output_text", text="완료")]
                ),
            )
        ]

    async def fake_call(messages: Payload, *, model: str) -> Any:
        captured["messages"] = messages
        return FakeResponse()

    monkeypatch.setattr(openai_gateway, "_call_openai", fake_call)

    png_bytes = base64.b64decode(
        (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4n"
            "GNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
        )
    )
    files = [
        ("files", ("snapshot.png", png_bytes, "image/png")),
        ("files", ("notes.txt", "hazard log", "text/plain")),
    ]
    data = {"prompt": "기상 분석", "history": "[]", "model": "gpt-4.1-mini"}

    with _client() as client:
        response = client.post("/api/assistant", data=data, files=files)

    assert response.status_code == 200
    assert response.json()["answer"] == "완료"
    payload = captured["messages"]
    assert isinstance(payload, list)
    user_block = payload[-1]["content"]
    types = [item["type"] for item in user_block]
    assert "input_image" in types
    assert any(
        item.get("text", "").startswith("[파일 첨부")
        for item in user_block
        if item["type"] == "input_text"
    )


def test_briefing_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Briefing endpoint returns text from Responses API choices."""

    class FakeResponse:
        def __init__(self, text: str) -> None:
            self.choices = [
                SimpleNamespace(
                    message=SimpleNamespace(content=text),
                )
            ]

    async def fake_call(messages: Payload, *, model: str) -> Any:
        assert model == "gpt-4.1-mini"
        # Ensure payload includes weather levels
        last = messages[-1]["content"][0]["text"]
        assert "sail level" in last.lower() or "기상" in last
        return FakeResponse("요약")

    monkeypatch.setattr(openai_gateway, "_call_openai", fake_call)

    payload = {
        "current_time": "2025-09-28T12:00:00Z",
        "vessel_name": "JOPETWIL 71",
        "vessel_status": "Weather Standby",
        "current_voyage": "69th",
        "schedule": [
            {
                "id": "69th",
                "cargo": "Sand",
                "etd": "2025-09-28T16:00:00Z",
                "eta": "2025-09-29T04:00:00Z",
                "status": "Scheduled",
            }
        ],
        "weather_windows": [
            {
                "start": "2025-09-29T00:00:00Z",
                "end": "2025-09-29T06:00:00Z",
                "sail_level": "Warn",
                "discharge_level": "NoGo",
                "waveM": 1.6,
                "windKt": 24,
                "visKm": 3.2,
            }
        ],
        "model": "gpt-4.1-mini",
    }

    with _client() as client:
        response = client.post("/api/briefing", json=payload)

    assert response.status_code == 200
    assert response.json()["briefing"] == "요약"


def test_require_client_reuses_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_require_client caches AsyncOpenAI instance."""

    created: list[str] = []

    class DummyClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.responses = SimpleNamespace(
                create=lambda **_: None,
            )

    def fake_async_openai(api_key: str) -> DummyClient:
        created.append(api_key)
        return DummyClient(api_key)

    monkeypatch.setattr(openai_gateway, "AsyncOpenAI", fake_async_openai)

    first = openai_gateway._require_client()
    second = openai_gateway._require_client()

    assert first is second
    assert created == ["sk-test"]


def test_schedule_normalize_local(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain text schedule is parsed locally without OpenAI."""

    def fail_call(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("OpenAI should not be called for local parse")

    monkeypatch.setattr(openai_gateway, "_call_openai", fail_call)

    form = {
        "text": "Voyage,Cargo\n80th,Dune Sand\n81st,20mm Agg.",
        "anchor_etd": "2025-10-01T00:00:00Z",
        "context_schedule": "[]",
    }

    with _client() as client:
        response = client.post("/api/schedule/normalize", data=form)

    assert response.status_code == 200
    payload = response.json()
    rows = payload["schedule"]
    assert len(rows) == 2
    assert rows[0]["id"] == "80th"
    assert rows[0]["cargo"] == "Dune Sand"
    assert rows[0]["etd"] == "2025-10-01T00:00:00Z"
    assert rows[0]["eta"] == "2025-10-01T12:00:00Z"
    assert rows[1]["etd"] == "2025-10-01T16:00:00Z"


def test_schedule_normalize_with_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image uploads trigger OpenAI normalization."""

    class FakeResponse:
        def __init__(self, text: str) -> None:
            self.choices = [
                SimpleNamespace(
                    message=SimpleNamespace(content=text),
                )
            ]

    async def fake_call(messages: Payload, *, model: str) -> Any:
        assert model == "gpt-4.1-mini"
        assert any(
            block["type"] == "input_image" for block in messages[-1]["content"]
        )
        text = json.dumps(
            {
                "schedule": [
                    {
                        "id": "90th",
                        "cargo": "Sand",
                        "etd": "2025-10-03T00:00:00Z",
                        "eta": "2025-10-03T12:00:00Z",
                        "status": "Scheduled",
                    }
                ]
            }
        )
        return FakeResponse(text)

    monkeypatch.setattr(openai_gateway, "_call_openai", fake_call)

    png_bytes = base64.b64decode(
        (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4n"
            "GNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
        )
    )
    files = [("files", ("capture.png", png_bytes, "image/png"))]

    with _client() as client:
        response = client.post(
            "/api/schedule/normalize",
            data={"text": "", "context_schedule": "[]"},
            files=files,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["notes"].startswith("AI")
    row = payload["schedule"][0]
    assert row["id"] == "90th"
    assert row["eta"] == "2025-10-03T12:00:00Z"
