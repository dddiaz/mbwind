from datetime import datetime


def direction_name(degrees: float) -> str:
    """Convert wind direction degrees to compass name."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return dirs[idx]


def score_wind_speed(kts: float) -> float:
    """Score wind speed for laser sailing (0-30 points)."""
    if kts is None or kts < 3:
        return 0
    elif kts < 6:
        return 10
    elif kts < 8:
        return 18
    elif kts < 12:
        return 30  # ideal laser range
    elif kts < 16:
        return 25
    elif kts < 20:
        return 18
    elif kts < 25:
        return 10
    else:
        return 5  # overpowered


def score_direction(degrees: float) -> float:
    """Score wind direction for Mission Bay (0-20 points).
    W/WNW (250-300) is ideal thermal direction.
    E/ENE (60-110) is offshore Santa Ana — bad."""
    if degrees is None:
        return 5
    # Ideal: 250-300 (W to WNW)
    if 240 <= degrees <= 310:
        return 20
    elif 220 <= degrees <= 330:
        return 15
    elif 180 <= degrees <= 220:
        return 10  # SW, ok
    elif 330 <= degrees or degrees <= 30:
        return 5  # N, light/variable
    else:
        return 2  # E/offshore


def score_thermal(delta_f: float) -> float:
    """Score thermal gradient (0-20 points)."""
    if delta_f >= 25:
        return 20
    elif delta_f >= 18:
        return 17
    elif delta_f >= 12:
        return 13
    elif delta_f >= 6:
        return 8
    elif delta_f >= 3:
        return 4
    else:
        return 0


def score_gust_factor(wind_kts: float, gust_kts: float) -> float:
    """Score gust reliability (0-15 points). Low gust factor = steady wind = good."""
    if wind_kts is None or wind_kts < 1:
        return 0
    if gust_kts is None:
        gust_kts = wind_kts
    ratio = gust_kts / wind_kts
    if ratio < 1.3:
        return 15  # very steady
    elif ratio < 1.5:
        return 12
    elif ratio < 1.8:
        return 8
    elif ratio < 2.2:
        return 4
    else:
        return 1  # very gusty/unreliable


def score_time_of_day(hour: int) -> float:
    """Score time of day for thermal wind (0-15 points).
    Peak thermal fill is typically 11am-3pm."""
    if 11 <= hour <= 15:
        return 15
    elif 10 <= hour <= 16:
        return 12
    elif 9 <= hour <= 17:
        return 8
    else:
        return 3


def compute_confidence(
    wind_kts: float,
    wind_dir: float,
    gust_kts: float,
    thermal_delta_f: float,
    marine_layer_suppression: float,
    hour: int,
) -> dict:
    """Compute overall wind confidence score (0-100)."""
    s_wind = score_wind_speed(wind_kts)
    s_dir = score_direction(wind_dir)
    s_thermal = score_thermal(thermal_delta_f)
    s_gust = score_gust_factor(wind_kts, gust_kts)
    s_time = score_time_of_day(hour)

    raw = s_wind + s_dir + s_thermal + s_gust + s_time  # max 100

    # Apply marine layer suppression penalty
    penalty = marine_layer_suppression * 15
    score = max(0, min(100, round(raw - penalty)))

    if score >= 65:
        recommendation = "GO"
    elif score >= 40:
        recommendation = "MAYBE"
    else:
        recommendation = "NO-GO"

    return {
        "score": score,
        "recommendation": recommendation,
        "breakdown": {
            "wind_speed": s_wind,
            "direction": s_dir,
            "thermal": s_thermal,
            "gust_factor": s_gust,
            "time_of_day": s_time,
            "marine_layer_penalty": round(penalty, 1),
        },
    }


def laser_tip(wind_kts: float, gust_kts: float) -> str:
    """Generate a laser sailing tip based on conditions."""
    if wind_kts is None or wind_kts < 5:
        return "Light air — focus on kinetics and sail trim"
    elif wind_kts < 10:
        gust_kts = gust_kts or wind_kts
        if gust_kts > 14:
            return "Shifty/gusty — stay ready to hike, keep weight forward in lulls"
        return "Pleasant conditions, good for technique work"
    elif wind_kts < 15:
        return "Good hiking conditions, reef if overpowered in gusts"
    elif wind_kts < 20:
        return "Full hike, consider reefing. Watch for gusts on the bay"
    else:
        return "Heavy air — reef recommended, watch for capsizes"
