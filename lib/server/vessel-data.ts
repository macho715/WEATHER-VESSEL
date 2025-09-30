export const VESSEL_DATASET = {
  timezone: "Asia/Dubai",
  vessel: {
    name: "DUNE_SAND",
    port: "Jebel Ali",
    speed: 12,
    cargo: "General Cargo",
    hsLimit: 2.5,
  },
  ports: {
    "Jebel Ali": { lat: 25.0267, lon: 55.0556 },
    "Fujairah": { lat: 25.1167, lon: 56.3333 },
    "Abu Dhabi": { lat: 24.4667, lon: 54.3667 },
    "Dubai": { lat: 25.2048, lon: 55.2708 },
  },
  schedule: [
    {
      id: "voyage-001",
      from: "Jebel Ali",
      to: "Fujairah",
      etd: "2025-01-01T06:00:00+04:00",
      eta: "2025-01-01T12:00:00+04:00",
      status: "scheduled",
      distance: 120,
    },
    {
      id: "voyage-002", 
      from: "Fujairah",
      to: "Abu Dhabi",
      etd: "2025-01-02T06:00:00+04:00",
      eta: "2025-01-02T18:00:00+04:00",
      status: "scheduled",
      distance: 180,
    },
  ],
  weatherWindows: [
    {
      start: "2025-01-01T06:00:00+04:00",
      end: "2025-01-01T12:00:00+04:00",
      wave_m: 1.2,
      wind_kt: 15.5,
      summary: "GO - Favorable conditions",
    },
    {
      start: "2025-01-02T06:00:00+04:00", 
      end: "2025-01-02T18:00:00+04:00",
      wave_m: 2.1,
      wind_kt: 22.3,
      summary: "WATCH - Moderate conditions",
    },
  ],
};
