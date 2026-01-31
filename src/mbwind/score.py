from datetime import datetime


SPORTS = ("laser", "wingfoil")


def direction_name(degrees: float) -> str:
    """Convert wind direction degrees to compass name."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return dirs[idx]


def score_wind_speed(kts: float, sport: str = "laser") -> float:
    """Score wind speed (0-30 points)."""
    if kts is None or kts < 3:
        return 0

    if sport == "wingfoil":
        # Wingfoil needs more wind; ideal 15-22 kts
        if kts < 8:
            return 5
        elif kts < 12:
            return 12
        elif kts < 15:
            return 22
        elif kts < 22:
            return 30  # ideal wingfoil range
        elif kts < 28:
            return 22
        elif kts < 35:
            return 12
        else:
            return 3  # dangerous
    else:
        # Laser: ideal 8-12 kts
        if kts < 6:
            return 10
        elif kts < 8:
            return 18
        elif kts < 12:
            return 30
        elif kts < 16:
            return 25
        elif kts < 20:
            return 18
        elif kts < 25:
            return 10
        else:
            return 5


def score_direction(degrees: float) -> float:
    """Score wind direction for Mission Bay (0-20 points).
    W/WNW (250-300) is ideal thermal direction.
    E/ENE (60-110) is offshore Santa Ana — bad."""
    if degrees is None:
        return 5
    if 240 <= degrees <= 310:
        return 20
    elif 220 <= degrees <= 330:
        return 15
    elif 180 <= degrees <= 220:
        return 10
    elif 330 <= degrees or degrees <= 30:
        return 5
    else:
        return 2


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


def score_gust_factor(wind_kts: float, gust_kts: float, sport: str = "laser") -> float:
    """Score gust reliability (0-15 points)."""
    if wind_kts is None or wind_kts < 1:
        return 0
    if gust_kts is None:
        gust_kts = wind_kts
    ratio = gust_kts / wind_kts

    if sport == "wingfoil":
        # Wingfoilers are more tolerant of gusts
        if ratio < 1.4:
            return 15
        elif ratio < 1.7:
            return 12
        elif ratio < 2.0:
            return 8
        elif ratio < 2.5:
            return 4
        else:
            return 1
    else:
        if ratio < 1.3:
            return 15
        elif ratio < 1.5:
            return 12
        elif ratio < 1.8:
            return 8
        elif ratio < 2.2:
            return 4
        else:
            return 1


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
    sport: str = "laser",
) -> dict:
    """Compute overall wind confidence score (0-100)."""
    s_wind = score_wind_speed(wind_kts, sport)
    s_dir = score_direction(wind_dir)
    s_thermal = score_thermal(thermal_delta_f)
    s_gust = score_gust_factor(wind_kts, gust_kts, sport)
    s_time = score_time_of_day(hour)

    raw = s_wind + s_dir + s_thermal + s_gust + s_time

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


def sport_tip(wind_kts: float, gust_kts: float, sport: str = "laser") -> str:
    """Generate a tip based on conditions and sport."""
    if sport == "wingfoil":
        if wind_kts is None or wind_kts < 8:
            return "Too light for foiling — try prone or SUP instead"
        elif wind_kts < 12:
            return "Marginal — big wing (6m+) and pumping required"
        elif wind_kts < 15:
            return "Rideable with a mid-size wing (5-6m)"
        elif wind_kts < 22:
            return "Sweet spot — great foiling conditions"
        elif wind_kts < 28:
            return "Powered up — small wing (3-4m), watch for chop"
        else:
            return "Nuking — experienced riders only, small wing"
    else:
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
