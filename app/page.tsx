"use client";

import { useState, useEffect } from "react";

interface MarineData {
  port: string;
  coords: { lat: number; lon: number };
  hs: number | null;
  windKt: number | null;
  swellPeriod: number | null;
  ioi: number | null;
  fetchedAt: string;
  cached: boolean;
  stale?: boolean;
}

interface VesselData {
  timezone: string;
  vessel: {
    name: string;
    port: string;
    speed: number;
    cargo: string;
    hsLimit: number;
  };
  schedule: Array<{
    id: string;
    from: string;
    to: string;
    etd: string;
    eta: string;
    status: string;
    distance: number;
  }>;
  weatherWindows: Array<{
    start: string;
    end: string;
    wave_m: number;
    wind_kt: number;
    summary: string;
  }>;
}

export default function Home() {
  const [marineData, setMarineData] = useState<MarineData | null>(null);
  const [vesselData, setVesselData] = useState<VesselData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [marineResponse, vesselResponse] = await Promise.all([
          fetch("/api/marine"),
          fetch("/api/vessel"),
        ]);

        if (!marineResponse.ok || !vesselResponse.ok) {
          throw new Error("Failed to fetch data");
        }

        const marine = await marineResponse.json();
        const vessel = await vesselResponse.json();

        setMarineData(marine);
        setVesselData(vessel);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Weather Vessel Data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Weather Vessel Logistics
              </h1>
              <p className="text-gray-600">Marine Weather Intelligence Control Tower</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">
                {vesselData?.timezone} • {new Date().toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Marine Conditions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🌊 Marine Conditions
            </h2>
            {marineData ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Port:</span>
                  <span className="font-medium">{marineData.port}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Wave Height (Hs):</span>
                  <span className="font-medium">
                    {marineData.hs ? `${marineData.hs.toFixed(2)} m` : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Wind Speed:</span>
                  <span className="font-medium">
                    {marineData.windKt ? `${marineData.windKt.toFixed(2)} kt` : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Swell Period:</span>
                  <span className="font-medium">
                    {marineData.swellPeriod ? `${marineData.swellPeriod.toFixed(2)} s` : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">IOI Score:</span>
                  <span className={`font-medium px-2 py-1 rounded ${
                    marineData.ioi && marineData.ioi >= 75 ? "bg-green-100 text-green-800" :
                    marineData.ioi && marineData.ioi >= 55 ? "bg-yellow-100 text-yellow-800" :
                    "bg-red-100 text-red-800"
                  }`}>
                    {marineData.ioi ? `${marineData.ioi.toFixed(0)}` : "N/A"}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-4">
                  Last updated: {new Date(marineData.fetchedAt).toLocaleString()}
                  {marineData.cached && " (cached)"}
                  {marineData.stale && " (stale)"}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No marine data available</p>
            )}
          </div>

          {/* Vessel Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🚢 Vessel Information
            </h2>
            {vesselData ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Name:</span>
                  <span className="font-medium">{vesselData.vessel.name}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Current Port:</span>
                  <span className="font-medium">{vesselData.vessel.port}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Speed:</span>
                  <span className="font-medium">{vesselData.vessel.speed} kt</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cargo:</span>
                  <span className="font-medium">{vesselData.vessel.cargo}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Hs Limit:</span>
                  <span className="font-medium">{vesselData.vessel.hsLimit} m</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No vessel data available</p>
            )}
          </div>

          {/* Schedule */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              📋 Schedule
            </h2>
            {vesselData?.schedule && vesselData.schedule.length > 0 ? (
              <div className="space-y-3">
                {vesselData.schedule.map((voyage) => (
                  <div key={voyage.id} className="border-l-4 border-blue-500 pl-4">
                    <div className="font-medium">{voyage.from} → {voyage.to}</div>
                    <div className="text-sm text-gray-600">
                      ETD: {new Date(voyage.etd).toLocaleString()} | 
                      ETA: {new Date(voyage.eta).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      Distance: {voyage.distance} nm | Status: {voyage.status}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No schedule available</p>
            )}
          </div>

          {/* Weather Windows */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🌤️ Weather Windows
            </h2>
            {vesselData?.weatherWindows && vesselData.weatherWindows.length > 0 ? (
              <div className="space-y-3">
                {vesselData.weatherWindows.map((window, index) => (
                  <div key={index} className="border-l-4 border-green-500 pl-4">
                    <div className="font-medium">{window.summary}</div>
                    <div className="text-sm text-gray-600">
                      {new Date(window.start).toLocaleString()} - {new Date(window.end).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      Hs: {window.wave_m.toFixed(2)} m | Wind: {window.wind_kt.toFixed(2)} kt
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No weather windows available</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
