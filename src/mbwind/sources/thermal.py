def compute_thermal_gradient(coastal_temp_f: float, inland_temp_f: float) -> dict:
    """Compute thermal gradient and classify strength."""
    delta = inland_temp_f - coastal_temp_f

    if delta >= 25:
        strength = "Very Strong"
    elif delta >= 18:
        strength = "Strong"
    elif delta >= 12:
        strength = "Moderate"
    elif delta >= 6:
        strength = "Weak"
    else:
        strength = "None"

    return {
        "coastal_temp_f": coastal_temp_f,
        "inland_temp_f": inland_temp_f,
        "delta_f": round(delta, 1),
        "strength": strength,
    }


def marine_layer_suppression(temp_f: float, dewpoint_f: float) -> float:
    """Estimate marine layer suppression factor (0-1, where 1 = full suppression).
    A small temp-dewpoint spread means thick marine layer."""
    spread = temp_f - dewpoint_f
    if spread < 3:
        return 0.7  # thick marine layer, significant suppression
    elif spread < 6:
        return 0.3
    elif spread < 10:
        return 0.1
    return 0.0  # clear, no suppression
