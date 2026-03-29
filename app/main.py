from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Weather Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

DEFAULT_PARAMS = {
    "latitude": 31.5497,
    "longitude": 74.3436,
    "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max,relative_humidity_2m_mean",
    "current_weather": True,
    "timezone": "Asia/Karachi",
    "forecast_days": 7,
}
AQI_PARAMS = {
    "latitude": 31.5497,
    "longitude": 74.3436,
    "current": "pm10,pm2_5,european_aqi",
    "timezone": "Asia/Karachi",
}


def aqi_label(value):
    if value is None:
        return "N/A"
    if value <= 20:
        return "Good"
    if value <= 40:
        return "Fair"
    if value <= 60:
        return "Poor"
    return "Very Poor"


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(OPEN_METEO_URL, params=DEFAULT_PARAMS)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "city": "Lahore, Pakistan",
                "error": f"Could not fetch weather data: {exc}",
                "current_temp": None,
                "current_windspeed": None,
                "current_humidity": None,
                "dates": [],
                "temp_max": [],
                "temp_min": [],
                "windspeed": [],
                "humidity": [],
                "european_aqi": None,
                "aqi_label": "N/A",
                "pm10": None,
                "pm2_5": None,
                "aqi_error": None,
            },
        )

    # Fetch air quality (independent — don't let it break weather display)
    aqi_data = {}
    aqi_error = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            aqi_resp = await client.get(AIR_QUALITY_URL, params=AQI_PARAMS)
            aqi_resp.raise_for_status()
            aqi_data = aqi_resp.json().get("current", {})
    except httpx.HTTPError as exc:
        aqi_error = f"Could not fetch air quality data: {exc}"

    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    european_aqi = aqi_data.get("european_aqi")

    context = {
        "request": request,
        "city": "Lahore, Pakistan",
        "current_temp": current.get("temperature"),
        "current_windspeed": current.get("windspeed"),
        "current_humidity": (
            daily.get("relative_humidity_2m_mean", [None])[0]
        ),
        "dates": daily.get("time", []),
        "temp_max": daily.get("temperature_2m_max", []),
        "temp_min": daily.get("temperature_2m_min", []),
        "windspeed": daily.get("windspeed_10m_max", []),
        "humidity": daily.get("relative_humidity_2m_mean", []),
        "european_aqi": european_aqi,
        "aqi_label": aqi_label(european_aqi),
        "pm10": aqi_data.get("pm10"),
        "pm2_5": aqi_data.get("pm2_5"),
        "aqi_error": aqi_error,
    }
    return templates.TemplateResponse("dashboard.html", context)
