import { NextResponse } from "next/server";

import { VESSEL_DATASET } from "@/lib/server/vessel-data";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    timezone: VESSEL_DATASET.timezone,
    vessel: VESSEL_DATASET.vessel,
    schedule: VESSEL_DATASET.schedule,
    weatherWindows: VESSEL_DATASET.weatherWindows,
  });
}
