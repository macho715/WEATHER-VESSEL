"""OpenAI 연동 FastAPI 백엔드. | FastAPI backend wired with OpenAI."""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import (Any, Callable, Dict, Iterable, List, Literal, Sequence,
                    TypeVar, cast)

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field
from PyPDF2 import PdfReader

LOGGER = logging.getLogger(__name__)


class LogiBaseModel(PydanticBaseModel):  # type: ignore[misc]
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
    schedule: List[Dict[str, Any]] = Field(default_factory=list)
    weather_windows: List[Dict[str, Any]] = Field(default_factory=list)
    model: str = Field(default="gpt-4.1-mini", max_length=64)


class BriefingResponse(LogiBaseModel):
    """일일 브리핑 응답. | Daily briefing response."""

    briefing: str


class AssistantResponse(LogiBaseModel):
    """AI 어시스턴트 응답. | AI assistant response."""

    answer: str


class ScheduleDraft(LogiBaseModel):
    """정규화 전 스케줄 초안. | Pre-normalized schedule draft."""

    id: str
    cargo: str
    etd: str | None = None
    eta: str | None = None
    status: str | None = None


class ScheduleRow(LogiBaseModel):
    """스케줄 행 구조. | Schedule row payload."""

    id: str
    cargo: str
    etd: str
    eta: str
    status: str = Field(default="Scheduled")


class ScheduleNormalizeResponse(LogiBaseModel):
    """스케줄 정규화 응답. | Schedule normalization result."""

    schedule: List[ScheduleRow]
    notes: str | None = None


MessagePayload = List[Dict[str, Any]]


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


def _image_to_base64(file: UploadFile, payload: bytes) -> Dict[str, Any]:
    """이미지를 base64로 인코딩. | Encode image to base64."""

    data_url = "data:{media};base64,{payload}".format(
        media=file.content_type,
        payload=base64.b64encode(payload).decode("utf-8"),
    )
    return {"type": "input_image", "image_url": {"url": data_url}}


def _build_user_content(
    prompt: str, files: Iterable[UploadFile], raw_payloads: List[bytes]
) -> MessagePayload:
    """사용자 메시지 콘텐츠 구성. | Compose user content payload."""

    content: MessagePayload = [{"type": "input_text", "text": prompt}]
    for idx, file in enumerate(files):
        data = raw_payloads[idx]
        filename = file.filename or f"attachment-{idx+1}"
        if file.content_type and file.content_type.startswith("image/"):
            content.append(
                {
                    "type": "input_text",
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
                    "type": "input_text",
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
                "type": "input_text",
                "text": f"[파일 첨부: {filename}]\n{decoded[:8000]}",
            }
        )

    return content


def _extract_output_text(response: Any) -> str:
    """Chat Completion 결과에서 텍스트 추출. | Extract text from Chat Completion."""

    outputs = getattr(response, "output", None)
    if outputs:
        texts: List[str] = []
        for item in cast(Iterable[Any], outputs):
            if getattr(item, "type", None) != "message":
                continue
            message = getattr(item, "message", None)
            if not message:
                continue
            for block in getattr(message, "content", []) or []:
                if getattr(block, "type", None) in {"text", "output_text"}:
                    text_value = getattr(block, "text", "")
                    if text_value:
                        texts.append(text_value)
        if texts:
            return "\n".join(texts)

    choices = cast(Sequence[Any], getattr(response, "choices", []))
    if not choices:
        return "Error: Could not extract response text"
    message_obj = getattr(choices[0], "message", None)
    if message_obj is None:
        return "Error: Could not extract response text"
    message_content = getattr(message_obj, "content", None)
    if isinstance(message_content, str):
        return message_content
    if message_content is None:
        return "Error: Could not extract response text"
    return str(message_content)


def _parse_datetime(value: str | None) -> datetime | None:
    """문자열을 UTC datetime 으로 파싱. | Parse string into UTC datetime."""

    if not value:
        return None
    text = value.strip().replace(" ", "T")
    if not text:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", text):
        text = f"{text}:00"
    try:
        if text.endswith("Z"):
            iso_text = text.replace("Z", "+00:00")
            return datetime.fromisoformat(iso_text).astimezone(timezone.utc)
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        for fmt in (
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y/%m/%dT%H:%M:%S",
        ):
            try:
                naive = datetime.strptime(text, fmt)
                return naive.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _format_iso(dt: datetime) -> str:
    """datetime 을 ISO8601 UTC 문자열로 변환. | Format datetime as ISO8601 UTC."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _autofill_schedule(
    rows: List[ScheduleDraft], anchor: datetime | None
) -> List[ScheduleRow]:
    """스케줄 초안을 자동 완성. | Autofill schedule draft rows."""

    voyage_anchor = anchor or datetime.now(timezone.utc)
    completed: List[ScheduleRow] = []
    cursor = voyage_anchor
    for idx, draft in enumerate(rows):
        etd_dt = _parse_datetime(draft.etd) or (cursor if idx == 0 else cursor)
        eta_dt = _parse_datetime(draft.eta)
        if eta_dt is None or eta_dt <= etd_dt:
            eta_dt = etd_dt + timedelta(hours=12)
        status = (draft.status or "Scheduled").strip() or "Scheduled"
        completed.append(
            ScheduleRow(
                id=draft.id.strip(),
                cargo=draft.cargo.strip(),
                etd=_format_iso(etd_dt),
                eta=_format_iso(eta_dt),
                status=status,
            )
        )
        cursor = eta_dt + timedelta(hours=4)
    return completed


def _extract_json_block(text: str) -> Any:
    """LLM 응답에서 JSON 블록 추출. | Extract JSON block from model output."""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidate = text[start_obj:end_obj + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    raise ValueError("JSON block not found in model output")


def _drafts_from_rows(rows: Iterable[Dict[str, Any]]) -> List[ScheduleDraft]:
    """원시 dict 리스트를 Draft로 변환. | Convert raw dict rows into drafts."""

    drafts: List[ScheduleDraft] = []
    for idx, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"Row {idx+1} is not an object")
        candidates = {
            "id": (
                raw.get("id")
                or raw.get("voyage")
                or raw.get("Voyage")
                or raw.get("trip")
            ),
            "cargo": (
                raw.get("cargo")
                or raw.get("Cargo")
                or raw.get("commodity")
            ),
            "etd": (
                raw.get("etd")
                or raw.get("ETD")
                or raw.get("departure")
            ),
            "eta": (
                raw.get("eta")
                or raw.get("ETA")
                or raw.get("arrival")
            ),
            "status": (
                raw.get("status")
                or raw.get("Status")
                or raw.get("state")
            ),
        }
        if not candidates["id"] or not candidates["cargo"]:
            raise ValueError(f"Row {idx+1} missing voyage or cargo")
        drafts.append(ScheduleDraft.model_validate(candidates))
    return drafts


def _try_local_schedule(text: str) -> List[ScheduleDraft]:
    """로컬 파서로 텍스트 스케줄 추출. | Parse schedule text without LLM."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header_cells = [cell.strip().lower() for cell in lines[0].split(",")]
    canonical = {"id", "voyage", "cargo", "etd", "eta", "status"}
    has_header = any(cell in canonical for cell in header_cells)
    records: List[Dict[str, Any]] = []
    if has_header:
        headers = [cell.strip() for cell in lines[0].split(",")]
        for line in lines[1:]:
            cells = [cell.strip() for cell in line.split(",")]
            record = {
                header: cells[idx] if idx < len(cells) else ""
                for idx, header in enumerate(headers)
            }
            records.append(record)
    else:
        for line in lines:
            cells = [cell.strip() for cell in line.split(",")]
            if len(cells) < 2:
                continue
            records.append(
                {
                    "id": cells[0],
                    "cargo": cells[1],
                    "etd": cells[2] if len(cells) > 2 else None,
                    "eta": cells[3] if len(cells) > 3 else None,
                    "status": cells[4] if len(cells) > 4 else None,
                }
            )
    if not records:
        return []
    return _drafts_from_rows(records)


async def _call_openai(messages: MessagePayload, *, model: str) -> Any:
    """OpenAI Responses API 호출. | Invoke OpenAI Responses API."""

    client = _require_client()
    return await client.responses.create(
        model=model,
        input=cast(Any, messages),
    )


def _build_history(messages: Sequence[ChatMessage]) -> MessagePayload:
    """Chat Completion용 메시지 배열 구성. | Build chat completion messages."""

    history: MessagePayload = []
    for item in messages:
        history.append(
            {
                "role": item.role,
                "content": [
                    {"type": "input_text", "text": item.content},
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


FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def typed_get(path: str, **kwargs: Any) -> Callable[[FuncT], FuncT]:
    """FastAPI GET 데코레이터에 타입 힌트를 부여. | Typed FastAPI GET decorator."""

    return cast("Callable[[FuncT], FuncT]", app.get(path, **kwargs))


def typed_post(path: str, **kwargs: Any) -> Callable[[FuncT], FuncT]:
    """FastAPI POST 데코레이터에 타입 힌트를 부여. | Typed FastAPI POST decorator."""

    return cast("Callable[[FuncT], FuncT]", app.post(path, **kwargs))


@typed_get("/health")
async def healthcheck() -> Dict[str, str]:
    """헬스체크. | Service health check."""

    return {"status": "ok"}


@typed_post("/api/assistant", response_model=AssistantResponse)
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


@typed_post(
    "/api/schedule/normalize",
    response_model=ScheduleNormalizeResponse,
)
async def normalize_schedule(
    text: str | None = Form(None),
    anchor_etd: str | None = Form(None),
    context_schedule: str = Form("[]"),
    model: str = Form("gpt-4.1-mini"),
    files: List[UploadFile] | None = File(default=None),
) -> ScheduleNormalizeResponse:
    """스케줄 텍스트/이미지를 정규화. | Normalize schedule text or images."""

    anchor_dt = _parse_datetime(anchor_etd)
    try:
        context_data = (
            json.loads(context_schedule) if context_schedule else []
        )
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=400,
            detail=f"Invalid context_schedule: {exc}",
        ) from exc

    if anchor_dt is None and isinstance(context_data, list) and context_data:
        last_row = context_data[-1]
        anchor_dt = (
            _parse_datetime(last_row.get("eta"))
            if isinstance(last_row, dict)
            else None
        )

    # Local parsing for plain text (no attachments)
    drafts: List[ScheduleDraft] = []
    if text and not files:
        drafts = _try_local_schedule(text)
        if drafts:
            schedule = _autofill_schedule(drafts, anchor_dt)
            return ScheduleNormalizeResponse(
                schedule=schedule,
                notes="로컬 파서로 스케줄을 정규화했습니다.",
            )

    attachments = list(files or [])
    payloads: List[bytes] = []
    for file in attachments:
        payloads.append(await file.read())

    if not text and not attachments:
        raise HTTPException(status_code=400, detail="정규화할 데이터가 없습니다.")

    context_summary = (
        json.dumps(context_data[-5:], ensure_ascii=False, indent=2)
        if isinstance(context_data, list)
        else "[]"
    )
    user_sections: List[str] = [
        "아래 자료를 id, cargo, etd, eta, status 필드가 있는 JSON 배열로 정규화하세요.",
        "etd/eta 값이 없으면 12시간 항해 + 4시간 하역/적재 패턴을 기준으로 추정하세요.",
    ]
    if anchor_dt:
        user_sections.append(
            f"이전 항차 기준 anchor ETD: {_format_iso(anchor_dt)}"
        )
    if context_summary:
        user_sections.append(
            f"최근 스케줄 컨텍스트: {context_summary}"
        )
    if text:
        snippet = text.strip()
        if len(snippet) > 6000:
            snippet = snippet[:6000]
        user_sections.append(f"원본 텍스트:\n{snippet}")

    user_prompt = "\n\n".join(user_sections)
    content = _build_user_content(user_prompt, attachments, payloads)

    try:
        response = await _call_openai(
            [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "당신은 HVDC 물류 스케줄 정규화 전문가입니다. "
                                "반드시 JSON 형식만 반환하고, 한국어 status 값을 그대로 유지하세요."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            model=model,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network failure
        LOGGER.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    raw_text = _extract_output_text(response)
    try:
        parsed = _extract_json_block(raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    records: List[Dict[str, Any]]
    if isinstance(parsed, dict):
        payload_rows = parsed.get("schedule")
        if not isinstance(payload_rows, list):
            raise HTTPException(
                status_code=502, detail="AI 응답에 schedule 리스트가 없습니다."
            )
        records = cast(List[Dict[str, Any]], payload_rows)
    elif isinstance(parsed, list):
        records = cast(List[Dict[str, Any]], parsed)
    else:
        raise HTTPException(status_code=502, detail="AI 응답이 리스트 형식이 아닙니다.")

    try:
        drafts = _drafts_from_rows(records)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    schedule = _autofill_schedule(drafts, anchor_dt)
    return ScheduleNormalizeResponse(
        schedule=schedule,
        notes="AI 추론으로 스케줄을 보정했습니다.",
    )


@typed_post("/api/briefing", response_model=BriefingResponse)
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
                            "type": "input_text",
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
                            "type": "input_text",
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
