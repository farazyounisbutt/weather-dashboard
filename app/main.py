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
DEFAULT_PARAMS = {
    "latitude": 31.5497,
    "longitude": 74.3436,
    "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max,relative_humidity_2m_mean",
    "current_weather": True,
    "timezone": "Asia/Karachi",
    "forecast_days": 7,
}


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
            },
        )

    current = data.get("current_weather", {})
    daily = data.get("daily", {})

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
    }
    return templates.TemplateResponse("dashboard.html", context)
