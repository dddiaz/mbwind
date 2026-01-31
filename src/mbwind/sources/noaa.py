import httpx

# NOAA station IDs near Mission Bay
# San Diego Bay - 9410170
TIDE_STATION = "9410170"

NWS_MARINE_ZONE = "PZZ775"  # Coastal waters San Diego
NWS_OFFICE = "SGX"  # San Diego NWS office


def fetch_tide_data() -> dict:
    """Fetch current tide data from NOAA CO-OPS."""
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "date": "latest",
        "station": TIDE_STATION,
        "product": "water_level",
        "datum": "MLLW",
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
        "application": "mbwind",
    }
    resp = httpx.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if "data" in data and data["data"]:
        entry = data["data"][0]
        return {
            "water_level_ft": float(entry["v"]),
            "time": entry["t"],
        }
    return {"water_level_ft": None, "time": None}


def fetch_tide_predictions() -> list[dict]:
    """Fetch today's tide predictions (hi/lo) from NOAA."""
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "date": "today",
        "station": TIDE_STATION,
        "product": "predictions",
        "datum": "MLLW",
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
        "interval": "hilo",
        "application": "mbwind",
    }
    resp = httpx.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    predictions = []
    for entry in data.get("predictions", []):
        predictions.append({
            "time": entry["t"],
            "height_ft": float(entry["v"]),
            "type": "High" if entry["type"] == "H" else "Low",
        })
    return predictions


def fetch_wind_observation() -> dict | None:
    """Fetch latest wind observation from NOAA station."""
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "date": "latest",
        "station": TIDE_STATION,
        "product": "wind",
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
        "application": "mbwind",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "data" in data and data["data"]:
            entry = data["data"][0]
            speed = float(entry["s"]) if entry["s"] else None
            gust = float(entry["g"]) if entry.get("g") else None
            direction = entry.get("dr", "")
            return {
                "speed_kts": speed,
                "gust_kts": gust,
                "direction": direction,
                "time": entry["t"],
            }
    except Exception:
        pass
    return None


def fetch_marine_forecast() -> str | None:
    """Fetch marine forecast discussion from NWS."""
    url = f"https://api.weather.gov/offices/{NWS_OFFICE}"
    headers = {"User-Agent": "mbwind/0.1 (sailwind confidence tool)"}
    try:
        resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        resp.raise_for_status()
    except Exception:
        pass

    # Try fetching the zone forecast directly
    url = f"https://api.weather.gov/zones/forecast/{NWS_MARINE_ZONE}/forecast"
    try:
        resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        periods = data.get("properties", {}).get("periods", [])
        if periods:
            return periods[0].get("detailedForecast", "")
    except Exception:
        pass
    return None


def classify_tide(water_level_ft: float | None, predictions: list[dict]) -> str:
    """Classify current tide state."""
    if water_level_ft is None:
        return "Unknown"

    if water_level_ft < 1.0:
        base = "Low"
    elif water_level_ft > 4.0:
        base = "High"
    else:
        base = "Mid"

    # Try to determine if incoming or outgoing from predictions
    from datetime import datetime
    now = datetime.now()
    next_tides = []
    for p in predictions:
        try:
            t = datetime.strptime(p["time"], "%Y-%m-%d %H:%M")
            if t > now:
                next_tides.append(p)
        except ValueError:
            continue

    if next_tides:
        if next_tides[0]["type"] == "High":
            return f"{base}, incoming"
        else:
            return f"{base}, outgoing"
    return base
