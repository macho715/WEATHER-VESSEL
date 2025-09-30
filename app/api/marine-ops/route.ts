import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const lat = parseFloat(searchParams.get("lat") || "0");
  const lon = parseFloat(searchParams.get("lon") || "0");
  const hours = parseInt(searchParams.get("hours") || "72");
  const action = searchParams.get("action") || "forecast";

  if (isNaN(lat) || isNaN(lon)) {
    return NextResponse.json({ error: "Invalid lat/lon parameters" }, { status: 400 });
  }

  try {
    const pythonScript = path.join(process.cwd(), "python-bridge", "marine_ops_bridge.py");
    
    let args: string[];
    if (action === "forecast") {
      args = ["forecast", lat.toString(), lon.toString(), hours.toString()];
    } else if (action === "eri") {
      const timeseriesData = searchParams.get("timeseries_data");
      const rulesPath = searchParams.get("rules_path");
      
      if (!timeseriesData || !rulesPath) {
        return NextResponse.json({ error: "Missing timeseries_data or rules_path for ERI calculation" }, { status: 400 });
      }
      
      args = ["eri", timeseriesData, rulesPath];
    } else {
      return NextResponse.json({ error: "Invalid action. Use 'forecast' or 'eri'" }, { status: 400 });
    }

    const result = await new Promise<string>((resolve, reject) => {
      const python = spawn("python", [pythonScript, ...args], {
        cwd: process.cwd(),
        env: { ...process.env, PYTHONPATH: path.join(process.cwd(), "marine_ops") }
      });

      let stdout = "";
      let stderr = "";

      python.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      python.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      python.on("close", (code) => {
        if (code === 0) {
          resolve(stdout);
        } else {
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
        }
      });

      python.on("error", (error) => {
        reject(new Error(`Failed to start Python script: ${error.message}`));
      });
    });

    const jsonResult = JSON.parse(result);
    
    if (jsonResult.success) {
      return NextResponse.json(jsonResult.data);
    } else {
      return NextResponse.json({ error: jsonResult.error }, { status: 500 });
    }

  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
