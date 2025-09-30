import { NextResponse } from "next/server";

import { VESSEL_DATASET } from "@/lib/server/vessel-data";

interface AssistantContext {
  prompt: string;
  model: string;
  attachments: File[];
  dataset: typeof VESSEL_DATASET;
}

const LOWER_PROMPT_MATCH = [
  { key: "weather", handler: buildWeatherInsight },
  { key: "risk", handler: buildRiskInsight },
  { key: "schedule", handler: buildRiskInsight },
];

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const form = await request.formData();
  const prompt = String(form.get("prompt") ?? "").trim();
  const model = String(form.get("model") ?? "gpt-4.1-mini");
  const attachments = form
    .getAll("files")
    .map((item) => (item instanceof File ? item : null))
    .filter((file): file is File => Boolean(file));

  if (!prompt) {
    return NextResponse.json({ answer: "질문을 입력해주세요." });
  }

  const lower = prompt.toLowerCase();
  const handler = LOWER_PROMPT_MATCH.find((entry) =>
    lower.includes(entry.key),
  )?.handler;
  const dataset = VESSEL_DATASET ?? {
    schedule: [],
    weatherWindows: [],
    timezone: "Asia/Dubai",
  };
  const context = {
    attachments,
    prompt,
    model,
    dataset,
  };

  if (!handler) {
    return NextResponse.json({ answer: buildDefaultInsight(context) });
  }

  const body = handler(context);
  const attachmentLine = attachments.length
    ? `\n첨부 ${attachments.length}건: ${attachments.map((file) => file.name || "무제").join(", ")}`
    : "\n첨부 없음: 파일을 추가하면 더 정확한 답변을 제공할 수 있어요.";

  return NextResponse.json({
    answer: `${body}\n모델: ${model}${attachmentLine}`,
  });
}

function buildWeatherInsight(context: AssistantContext) {
  const tz = context.dataset.timezone;
  const windows = Array.isArray(context.dataset.weatherWindows)
    ? context.dataset.weatherWindows
    : [];
  if (!windows.length) {
    return "📡 등록된 기상 창 정보가 없습니다. Risk Scan으로 최신 데이터를 받아보세요.";
  }
  const lines = windows.map((window: { start: string; end: string; wave_m: number; wind_kt: number; summary: string }) => {
    const start = new Date(window.start);
    const end = new Date(window.end);
    const span =
      `${start.toLocaleString("ko-KR", { timeZone: tz, hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" })}` +
      ` – ${end.toLocaleString("ko-KR", { timeZone: tz, hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" })}`;
    return `• ${span} · Hs ${window.wave_m.toFixed(2)} m · Wind ${window.wind_kt.toFixed(2)} kt · ${window.summary}`;
  });

  return [
    "📡 최신 기상 창 요약",
    ...lines,
    "",
    "💡 추가 정보가 필요하시면 첨부 파일을 업로드해주세요.",
  ].join("\n");
}

function buildRiskInsight(context: AssistantContext) {
  const schedule = Array.isArray(context.dataset.schedule)
    ? context.dataset.schedule
    : [];
  if (!schedule.length) {
    return "📋 등록된 항해 일정이 없습니다. Schedule 탭에서 일정을 확인해보세요.";
  }
  
  const lines = schedule.map((voyage: { etd: string; eta: string; from: string; to: string; status: string }) => {
    const etd = new Date(voyage.etd);
    const eta = new Date(voyage.eta);
    const span = `${etd.toLocaleString("ko-KR", { 
      timeZone: context.dataset.timezone, 
      hour: "2-digit", 
      minute: "2-digit", 
      month: "short", 
      day: "numeric" 
    })} – ${eta.toLocaleString("ko-KR", { 
      timeZone: context.dataset.timezone, 
      hour: "2-digit", 
      minute: "2-digit", 
      month: "short", 
      day: "numeric" 
    })}`;
    return `• ${voyage.from} → ${voyage.to} (${span}) · ${voyage.status}`;
  });

  return [
    "📋 항해 일정 및 위험도 분석",
    ...lines,
    "",
    "⚠️ 위험도는 실시간 기상 데이터를 기반으로 계산됩니다.",
  ].join("\n");
}

function buildDefaultInsight(_context: AssistantContext) {
  return `안녕하세요! Weather Vessel 로지스틱스 어시스턴트입니다.

다음과 같은 정보를 제공할 수 있습니다:
• 🌤️ 기상 정보 및 예보
• 📋 항해 일정 및 위험도 분석  
• 🚢 선박 상태 및 위치 정보
• 📊 IOI (Index of Interest) 점수

구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다.`;
}
