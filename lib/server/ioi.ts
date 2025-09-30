interface MarineData {
  hs: number | null;
  windKt: number | null;
  swellPeriod: number | null;
}

export function computeIoiFromMarine(data: MarineData): number | null {
  const { hs, windKt, swellPeriod } = data;
  
  if (hs === null || windKt === null || swellPeriod === null) {
    return null;
  }

  // IOI calculation based on marine conditions
  let score = 100;
  
  // Wave height penalty (Hs)
  if (hs > 3.0) score -= 40;
  else if (hs > 2.0) score -= 20;
  else if (hs > 1.5) score -= 10;
  
  // Wind speed penalty
  if (windKt > 30) score -= 30;
  else if (windKt > 20) score -= 15;
  else if (windKt > 15) score -= 5;
  
  // Swell period bonus/penalty
  if (swellPeriod < 6) score -= 10;
  else if (swellPeriod > 12) score += 5;
  
  return Math.max(0, Math.min(100, score));
}
