import { NextResponse } from "next/server";

import { GuardedFetchError, guardedFetch } from "@/lib/server/guarded-fetch";
import { computeIoiFromMarine } from "@/lib/server/ioi";
import { VESSEL_DATASET } from "@/lib/server/vessel-data";

interface CachedMarine {
  snapshot: {
    hs: number | null;
    windKt: number | null;
    swellPeriod: number | null;
    ioi: number | null;
    fetchedAt: string;
  };
  expiresAt: number;
}

const cache = new Map<string, CachedMarine>();
const CACHE_TTL_MS = 10 * 60 * 1000;
const FETCH_TIMEOUT_MS = 7 * 1000;
const MAX_RETRIES = 2;
const CIRCUIT_THRESHOLD = 3;
const CIRCUIT_COOLDOWN_MS = 5 * 60 * 1000;

function safeNumber(value: unknown): number | null {
  const num = typeof value === "string" ? Number(value) : (value as number);
  return Number.isFinite(num) ? num : null;
}

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const port = searchParams.get("port") ?? VESSEL_DATASET.vessel.port;
  const coords =
    VESSEL_DATASET.ports[port as keyof typeof VESSEL_DATASET.ports];

  if (!coords) {
    return NextResponse.json({ error: "Unknown port" }, { status: 400 });
  }

  const cached = cache.get(port);
  const now = Date.now();
  if (cached && cached.expiresAt > now) {
    return NextResponse.json({
      port,
      coords,
      ...cached.snapshot,
      cached: true,
    });
  }

  try {
    const params = new URLSearchParams({
      latitude: String(coords.lat),
      longitude: String(coords.lon),
      hourly: ["wave_height", "wind_speed_10m", "swell_wave_period"].join(","),
      timezone: "auto",
    });
    const url = `https://marine-api.open-meteo.com/v1/marine?${params.toString()}`;
    const response = await guardedFetch(url, {
      key: `marine:${port}`,
      timeoutMs: FETCH_TIMEOUT_MS,
      retries: MAX_RETRIES,
      backoffMs: 500,
      backoffFactor: 2,
      circuitBreakerThreshold: CIRCUIT_THRESHOLD,
      circuitBreakerCooldownMs: CIRCUIT_COOLDOWN_MS,
    });

    const payload = await response.json();
    const hs = safeNumber(payload?.hourly?.wave_height?.[0]);
    const windMs = safeNumber(payload?.hourly?.wind_speed_10m?.[0]);
    const swellPeriod = safeNumber(payload?.hourly?.swell_wave_period?.[0]);
    const windKt = windMs != null ? windMs * 1.94384 : null;

    const ioi = computeIoiFromMarine({ hs, windKt, swellPeriod });

    const snapshot = {
      hs,
      windKt: windKt != null ? Number(windKt.toFixed(2)) : null,
      swellPeriod,
      ioi,
      fetchedAt: new Date().toISOString(),
    };

    cache.set(port, {
      snapshot,
      expiresAt: now + CACHE_TTL_MS,
    });

    return NextResponse.json({ port, coords, ...snapshot, cached: false });
  } catch (error: unknown) {
    if (cached) {
      return NextResponse.json(
        { port, coords, ...cached.snapshot, stale: true, cached: true },
        { status: 200 },
      );
    }
    const message =
      error instanceof GuardedFetchError
        ? error.message
        : error instanceof Error
          ? error.message
          : "Unknown marine error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

export function __resetMarineCacheForTests() {
  cache.clear();
}
