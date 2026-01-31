import httpx
from datetime import datetime, timezone

# Mission Bay, San Diego
COASTAL_LAT, COASTAL_LON = 32.77, -117.23
# El Cajon (inland reference)
INLAND_LAT, INLAND_LON = 32.79, -116.96

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def _fetch_forecast(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,dewpoint_2m",
        "wind_speed_unit": "kn",
        "temperature_unit": "fahrenheit",
        "timezone": "America/Los_Angeles",
        "forecast_days": 1,
    }
    resp = httpx.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_coastal_forecast() -> dict:
    return _fetch_forecast(COASTAL_LAT, COASTAL_LON)


def fetch_inland_forecast() -> dict:
    return _fetch_forecast(INLAND_LAT, INLAND_LON)


def get_hourly_at(forecast: dict, target_hour: int | None = None) -> dict:
    """Extract data for a specific hour (0-23) or the current hour."""
    hourly = forecast["hourly"]
    times = hourly["time"]

    if target_hour is None:
        now = datetime.now().astimezone()
        target_hour = now.hour

    # Find the index matching target_hour
    for i, t in enumerate(times):
        dt = datetime.fromisoformat(t)
        if dt.hour == target_hour:
            return {
                "time": t,
                "hour": dt.hour,
                "temp_f": hourly["temperature_2m"][i],
                "wind_kts": hourly["wind_speed_10m"][i],
                "wind_dir": hourly["wind_direction_10m"][i],
                "gusts_kts": hourly["wind_gusts_10m"][i],
                "dewpoint_f": hourly["dewpoint_2m"][i],
            }

    # Fallback to last available hour
    i = len(times) - 1
    dt = datetime.fromisoformat(times[i])
    return {
        "time": times[i],
        "hour": dt.hour,
        "temp_f": hourly["temperature_2m"][i],
        "wind_kts": hourly["wind_speed_10m"][i],
        "wind_dir": hourly["wind_direction_10m"][i],
        "gusts_kts": hourly["wind_gusts_10m"][i],
        "dewpoint_f": hourly["dewpoint_2m"][i],
    }


def find_best_window(forecast: dict) -> dict:
    """Find the best wind window in the forecast."""
    hourly = forecast["hourly"]
    best_i = 0
    best_speed = 0
    for i, speed in enumerate(hourly["wind_speed_10m"]):
        if speed is not None and speed > best_speed:
            dt = datetime.fromisoformat(hourly["time"][i])
            if 9 <= dt.hour <= 18:  # daytime only
                best_speed = speed
                best_i = i

    dt = datetime.fromisoformat(hourly["time"][best_i])
    return {
        "hour": dt.hour,
        "wind_kts": best_speed,
        "wind_dir": hourly["wind_direction_10m"][best_i],
    }
