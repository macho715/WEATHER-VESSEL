import { NextResponse } from "next/server";

import { VESSEL_DATASET } from "@/lib/server/vessel-data";

export const dynamic = "force-dynamic";

export async function GET() {
  const tz = VESSEL_DATASET.timezone;
  const windows = VESSEL_DATASET.weatherWindows;
  
  const briefing = windows.length > 0 
    ? windows.map((window: { start: string; end: string; wave_m: number; wind_kt: number; summary: string }) => {
        const start = new Date(window.start);
        const end = new Date(window.end);
        const span = `${start.toLocaleString("ko-KR", { 
          timeZone: tz, 
          hour: "2-digit", 
          minute: "2-digit", 
          month: "short", 
          day: "numeric" 
        })} – ${end.toLocaleString("ko-KR", { 
          timeZone: tz, 
          hour: "2-digit", 
          minute: "2-digit", 
          month: "short", 
          day: "numeric" 
        })}`;
        return `• ${span} · Hs ${window.wave_m.toFixed(2)} m · Wind ${window.wind_kt.toFixed(2)} kt · ${window.summary}`;
      }).join('\n')
    : "📡 등록된 기상 창 정보가 없습니다. Risk Scan으로 최신 데이터를 받아보세요.";

  return NextResponse.json({
    briefing: `📡 최신 기상 창 요약\n${briefing}`,
    generatedAt: new Date().toISOString(),
  });
}
