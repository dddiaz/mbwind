# mbwind — Mission Bay Wind Confidence Tool

A CLI tool that answers: **"Will there actually be sailworthy wind at Mission Bay right now/today?"**

Produces a wind confidence score (0-100) and go/no-go recommendation tailored to laser sailing out of Mission Bay Aquatic Center.

## Usage

```
uv run mbwind           # check current conditions
uv run mbwind --hour 14 # check conditions at 2pm
```

## Data Sources

- **Open-Meteo** — hourly wind/temp forecast (coastal + inland)
- **NOAA Tides & Currents** — real-time observations, tide data
- **NOAA NWS** — marine forecast for San Diego
- **Thermal gradient** — coastal vs. inland temp delta to predict thermal fill

## Scoring

The confidence score (0-100) weights:
- Wind speed (0-30 pts) — 8-12 kts ideal for laser
- Wind direction (0-20 pts) — W/WNW thermal is best
- Thermal gradient (0-20 pts) — bigger delta = stronger thermal
- Gust factor (0-15 pts) — steady wind scores higher
- Time of day (0-15 pts) — 11am-3pm peak thermal window
- Marine layer penalty — thick layer suppresses thermal

Thresholds: **GO** ≥ 65 | **MAYBE** ≥ 40 | **NO-GO** < 40
