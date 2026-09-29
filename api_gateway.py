from fastapi import FastAPI
from state_manager import StateManager
import uvicorn

app = FastAPI(
    title="AI Microgrid API Gateway",
    description="REST API for the SIH Polar Microgrid Dashboard",
    version="1.0.0"
)

# Initialize connection to the local time-series SQLite database
db = StateManager()

@app.get("/api/health")
async def health_check():
    """Simple health check for the edge deployment."""
    return {"status": "online", "message": "API Gateway is running."}

@app.get("/api/current-state")
async def get_current_state():
    """
    Fetches the instantaneous state of the microgrid from the SQLite database.
    Used by the frontend dashboard to update live gauges (SOC, Temp, Load).
    """
    state = db.get_latest_state()
    
    env = state.get("environment")
    sys = state.get("system")
    
    if not env or not sys:
        return {"error": "No telemetry data found in database. Run simulate_dataset.py or state_manager.py first."}

    # Map the SQLite tuple rows to clean JSON dictionaries
    return {
        "telemetry": {
            "timestamp": env[1],
            "temperature_c": env[2],
            "pressure_hpa": env[3],
            "wind_speed_ms": env[4],
            "solar_irradiance_w_m2": env[5]
        },
        "system_status": {
            "timestamp": sys[1],
            "battery_temp_c": sys[2],
            "dynamic_soc_pct": sys[3],
            "actual_capacity_kwh": sys[4],
            "station_load_kw": sys[5],
            "diesel_generator_active": bool(sys[6]),
            "load_shed_active": bool(sys[7])
        }
    }

@app.post("/api/trigger-diesel")
async def manual_diesel_override():
    """
    Allows a manual override from headquarters (or failsafe) to start the diesel generator,
    bypassing the AI logic entirely.
    """
    # In a full deployment, this would publish a strict override command to the MQTT broker
    return {"status": "success", "message": "Command sent to Edge Nodes: Diesel Generator START"}

if __name__ == "__main__":
    print("Starting API Gateway on port 8000...")
    # uvicorn is the ASGI web server that runs FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
