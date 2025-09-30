import { NextResponse } from "next/server";

import { getLastReport } from "@/lib/server/report-state";
import { VESSEL_DATASET } from "@/lib/server/vessel-data";

export const dynamic = "force-dynamic";

export async function GET() {
  const lastReport = getLastReport();
  
  return NextResponse.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
    timezone: VESSEL_DATASET.timezone,
    vessel: VESSEL_DATASET.vessel,
    lastReport: lastReport ? {
      slot: lastReport.slot,
      generatedAt: lastReport.generatedAt,
      sent: lastReport.sent,
    } : null,
  });
}
