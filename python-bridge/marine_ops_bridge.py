#!/usr/bin/env python3
"""
Python bridge for marine_ops package integration with Next.js
"""

import sys
import json
import os
from pathlib import Path

# Add the marine_ops package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "marine_ops"))

try:
    from marine_ops.core.settings import MarineOpsSettings
    from marine_ops.connectors import fetch_forecast_with_fallback
    from marine_ops.eri import compute_eri_timeseries, load_rule_set
    import datetime as dt
except ImportError as e:
    print(json.dumps({"error": f"Failed to import marine_ops: {e}"}))
    sys.exit(1)

def get_marine_forecast(lat: float, lon: float, hours: int = 72):
    """Get marine forecast using marine_ops package"""
    try:
        settings = MarineOpsSettings.from_env()
        stormglass = settings.build_stormglass_connector()
        fallback = settings.build_open_meteo_fallback()
        
        start = dt.datetime.now(tz=dt.timezone.utc)
        end = start + dt.timedelta(hours=hours)
        
        series = fetch_forecast_with_fallback(
            lat, lon, start, end, stormglass, fallback
        )
        
        # Convert to JSON-serializable format
        result = {
            "success": True,
            "data": {
                "points": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "latitude": point.position.latitude,
                        "longitude": point.position.longitude,
                        "measurements": [
                            {
                                "variable": measurement.variable.value,
                                "value": measurement.value,
                                "unit": measurement.unit.value
                            }
                            for measurement in point.measurements
                        ]
                    }
                    for point in series.points
                ]
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

def compute_eri_score(timeseries_data: dict, rules_path: str):
    """Compute ERI score using marine_ops package"""
    try:
        # Load rules
        rules = load_rule_set(rules_path)
        
        # Convert timeseries data back to marine_ops format
        # This is a simplified conversion - in practice you'd need more robust conversion
        from marine_ops.core.schema import MarineTimeseries, MarineDataPoint, Position, MarineMeasurement, MarineVariable, UnitEnum
        
        points = []
        for point_data in timeseries_data.get("points", []):
            measurements = []
            for measurement_data in point_data.get("measurements", []):
                measurements.append(MarineMeasurement(
                    variable=MarineVariable(measurement_data["variable"]),
                    value=measurement_data["value"],
                    unit=UnitEnum(measurement_data["unit"])
                ))
            
            points.append(MarineDataPoint(
                timestamp=dt.datetime.fromisoformat(point_data["timestamp"].replace('Z', '+00:00')),
                position=Position(
                    latitude=point_data["latitude"],
                    longitude=point_data["longitude"]
                ),
                measurements=measurements,
                metadata=series.metadata if 'series' in locals() else None
            ))
        
        series = MarineTimeseries(points=points)
        eri_points = compute_eri_timeseries(series, rules)
        
        result = {
            "success": True,
            "data": {
                "eri_points": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "score": point.score,
                        "badges": [badge.value for badge in point.badges]
                    }
                    for point in eri_points
                ]
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command"}))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "forecast":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Missing lat/lon parameters"}))
            sys.exit(1)
        
        lat = float(sys.argv[2])
        lon = float(sys.argv[3])
        hours = int(sys.argv[4]) if len(sys.argv) > 4 else 72
        
        print(get_marine_forecast(lat, lon, hours))
        
    elif command == "eri":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Missing timeseries_data and rules_path parameters"}))
            sys.exit(1)
        
        timeseries_data = json.loads(sys.argv[2])
        rules_path = sys.argv[3]
        
        print(compute_eri_score(timeseries_data, rules_path))
        
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)
