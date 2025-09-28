"""OpenAI 연동 FastAPI 백엔드. | FastAPI backend wired with OpenAI."""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Iterable, List, Literal, Sequence

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field
from PyPDF2 import PdfReader


LOGGER = logging.getLogger(__name__)


class LogiBaseModel(BaseModel):
    """로지스틱 도메인 공통 베이스 모델. | Common logistics base model."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ChatMessage(LogiBaseModel):
    """사용자/AI 메시지 구조. | Chat message schema."""

    role: Literal["user", "assistant", "system"]
    content: str = Field(..., max_length=6000)


class BriefingRequest(LogiBaseModel):
    """일일 브리핑 요청 본문. | Daily briefing payload."""

    current_time: str
    vessel_name: str
    vessel_status: str
    current_voyage: str | None = None
    schedule: List[dict] = Field(default_factory=list)
    weather_windows: List[dict] = Field(default_factory=list)


class BriefingResponse(LogiBaseModel):
    """일일 브리핑 응답. | Daily briefing response."""

    briefing: str


class AssistantResponse(LogiBaseModel):
    """AI 어시스턴트 응답. | AI assistant response."""

    answer: str


_async_client: AsyncOpenAI | None = None
_dotenv_loaded = False


def _load_dotenv() -> None:
    """로컬 .env 파일에서 환경변수를 로드. | Load environment variables from .env."""

    global _dotenv_loaded
    if _dotenv_loaded:
        return

    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
    ]
    for env_path in candidates:
        if not env_path.exists():
            continue
        try:
            with env_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", maxsplit=1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError as exc:  # pragma: no cover - filesystem edge
            LOGGER.warning("Failed to load .env file %s: %s", env_path, exc)
    _dotenv_loaded = True


def _require_client() -> AsyncOpenAI:
    """OpenAI 클라이언트를 생성. | Build an OpenAI client."""

    _load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_message = "OPENAI_API_KEY is not configured"
        raise HTTPException(status_code=500, detail=error_message)
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=api_key)
    return _async_client


def _pdf_to_text(payload: bytes) -> str:
    """PDF를 텍스트로 추출. | Extract text from PDF."""

    reader = PdfReader(io.BytesIO(payload))
    text_chunks: List[str] = []
    for page in reader.pages:
        snippet = page.extract_text() or ""
        text_chunks.append(snippet)
    return "\n".join(text_chunks)


def _image_to_base64(file: UploadFile, payload: bytes) -> dict:
    """이미지를 base64로 인코딩. | Encode image to base64."""

    data_url = "data:{media};base64,{payload}".format(
        media=file.content_type,
        payload=base64.b64encode(payload).decode("utf-8"),
    )
    return {"type": "input_image", "image_url": {"url": data_url}}


def _build_user_content(
    prompt: str, files: Iterable[UploadFile], raw_payloads: List[bytes]
) -> List[dict[str, Any]]:
    """사용자 메시지 콘텐츠 구성. | Compose user content payload."""

    content: List[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for idx, file in enumerate(files):
        data = raw_payloads[idx]
        filename = file.filename or f"attachment-{idx+1}"
        if file.content_type and file.content_type.startswith("image/"):
            content.append(
                {
                    "type": "text",
                    "text": f"[이미지 첨부: {filename}]",
                }
            )
            content.append(_image_to_base64(file, data))
            continue

        is_pdf_content = file.content_type == "application/pdf"
        if is_pdf_content or filename.lower().endswith(".pdf"):
            pdf_text = _pdf_to_text(data)[:8000]
            descriptor = f"[PDF 첨부: {filename}]\n{pdf_text}"
            content.append(
                {
                    "type": "text",
                    "text": descriptor,
                }
            )
            continue

        try:
            decoded = data.decode("utf-8")
        except UnicodeDecodeError:
            decoded = base64.b64encode(data).decode("utf-8")
            decoded = f"[base64-encoded attachment]\n{decoded[:6000]}"
        content.append(
            {
                "type": "text",
                "text": f"[파일 첨부: {filename}]\n{decoded[:8000]}",
            }
        )

    return content


def _extract_output_text(response: Any) -> str:
    """Chat Completion 결과에서 텍스트 추출. | Extract text from Chat Completion."""

    outputs = getattr(response, "output", None)
    if outputs:
        texts: List[str] = []
        for item in outputs:
            if getattr(item, "type", None) != "message":
                continue
            message = getattr(item, "message", None)
            if not message:
                continue
            for block in getattr(message, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    text_value = getattr(block, "text", "")
                    if text_value:
                        texts.append(text_value)
        if texts:
            return "\n".join(texts)

    try:
        return response.choices[0].message.content
    except (AttributeError, IndexError, KeyError):
        return "Error: Could not extract response text"


async def _call_openai(messages: List[dict[str, Any]], *, model: str) -> Any:
    """OpenAI Responses API 호출. | Invoke OpenAI Responses API."""

    client = _require_client()
    return await client.responses.create(model=model, input=messages)


def _build_history(messages: Sequence[ChatMessage]) -> List[dict[str, Any]]:
    """Chat Completion용 메시지 배열 구성. | Build chat completion messages."""

    history: List[dict[str, Any]] = []
    for item in messages:
        history.append(
            {
                "role": item.role,
                "content": [
                    {"type": "text", "text": item.content},
                ],
            }
        )
    return history


app = FastAPI(title="HVDC Logistics AI Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def healthcheck() -> dict:
    """헬스체크. | Service health check."""

    return {"status": "ok"}


@app.post("/api/assistant", response_model=AssistantResponse)
async def run_assistant(
    prompt: str = Form(..., max_length=4000),
    history: str = Form("[]"),
    files: List[UploadFile] | None = File(default=None),
    model: str = Form("gpt-4.1-mini"),
) -> AssistantResponse:
    """어시스턴트 호출. | Execute assistant call."""

    try:
        raw_history = json.loads(history)
        history_messages: List[ChatMessage] = []
        for item in raw_history:
            history_messages.append(ChatMessage.model_validate(item))
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:  # pragma: no cover - validation
        raise HTTPException(
            status_code=400, detail=f"Invalid history payload: {exc}"
        ) from exc

    attachments = list(files or [])
    payloads: List[bytes] = []
    for file in attachments:
        payloads.append(await file.read())

    messages = _build_history(history_messages)
    messages.append(
        {
            "role": "user",
            "content": _build_user_content(prompt, attachments, payloads),
        }
    )

    try:
        response = await _call_openai(messages, model=model)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network failure
        LOGGER.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AssistantResponse(answer=_extract_output_text(response))


@app.post("/api/briefing", response_model=BriefingResponse)
async def generate_briefing(payload: BriefingRequest) -> BriefingResponse:
    """일일 브리핑 생성. | Create a daily briefing."""

    schedule_summary = json.dumps(
        payload.schedule,
        ensure_ascii=False,
        indent=2,
    )
    weather_summary = json.dumps(
        payload.weather_windows,
        ensure_ascii=False,
        indent=2,
    )
    prompt_template = (
        "당신은 해상 물류 관제 전문가입니다. "
        "아래 데이터를 참고하여 200자 내외의 한국어 일일 브리핑을 작성하세요."
        "\n- 현재 시각: {time}"
        "\n- 선박명: {vessel}"
        "\n- 현재 항차: {voyage}"
        "\n- 선박 상태: {status}"
        "\n- 전체 일정: {schedule}"
        "\n- 기상 윈도우: {weather}"
        "\n브리핑은 핵심 일정, 위험, 권고사항을 bullet로 정리하세요."
    )
    prompt = prompt_template.format(
        time=payload.current_time,
        vessel=payload.vessel_name,
        voyage=payload.current_voyage or "N/A",
        status=payload.vessel_status,
        schedule=schedule_summary,
        weather=weather_summary,
    )

    try:
        response = await _call_openai(
            [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "당신은 HVDC 프로젝트 물류 전문가입니다. "
                                "일일 브리핑을 한국어로 작성하세요."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                },
            ],
            model=payload.model,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network failure
        LOGGER.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return BriefingResponse(briefing=_extract_output_text(response))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)