import click
from datetime import datetime

from .sources.open_meteo import fetch_coastal_forecast, fetch_inland_forecast, get_hourly_at, find_best_window
from .sources.noaa import fetch_tide_data, fetch_tide_predictions, fetch_wind_observation, fetch_marine_forecast, classify_tide
from .sources.thermal import compute_thermal_gradient, marine_layer_suppression
from .score import compute_confidence, laser_tip
from .display import render_report


@click.command()
@click.option("--hour", type=int, default=None, help="Hour (0-23) to check. Defaults to current hour.")
def main(hour: int | None):
    """Mission Bay wind confidence for laser sailing."""
    if hour is None:
        hour = datetime.now().hour

    # Fetch all data
    try:
        coastal = fetch_coastal_forecast()
    except Exception as e:
        click.echo(f"Error fetching coastal forecast: {e}", err=True)
        raise SystemExit(1)

    try:
        inland = fetch_inland_forecast()
    except Exception as e:
        click.echo(f"Error fetching inland forecast: {e}", err=True)
        raise SystemExit(1)

    coastal_now = get_hourly_at(coastal, hour)
    inland_now = get_hourly_at(inland, hour)

    # Thermal gradient
    thermal = compute_thermal_gradient(coastal_now["temp_f"], inland_now["temp_f"])
    ml_suppression = marine_layer_suppression(coastal_now["temp_f"], coastal_now["dewpoint_f"])

    # Confidence score
    result = compute_confidence(
        wind_kts=coastal_now["wind_kts"],
        wind_dir=coastal_now["wind_dir"],
        gust_kts=coastal_now["gusts_kts"],
        thermal_delta_f=thermal["delta_f"],
        marine_layer_suppression=ml_suppression,
        hour=hour,
    )

    # NOAA data (non-critical)
    tide_data = None
    tide_predictions = []
    observed_wind = None
    marine_text = None

    try:
        tide_data = fetch_tide_data()
    except Exception:
        pass

    try:
        tide_predictions = fetch_tide_predictions()
    except Exception:
        pass

    try:
        observed_wind = fetch_wind_observation()
    except Exception:
        pass

    try:
        marine_text = fetch_marine_forecast()
    except Exception:
        pass

    tide_str = classify_tide(
        tide_data["water_level_ft"] if tide_data else None,
        tide_predictions,
    )

    best = find_best_window(coastal)
    tip = laser_tip(coastal_now["wind_kts"], coastal_now["gusts_kts"])

    render_report(
        score=result["score"],
        recommendation=result["recommendation"],
        wind_kts=coastal_now["wind_kts"],
        wind_dir=coastal_now["wind_dir"],
        gust_kts=coastal_now["gusts_kts"],
        thermal=thermal,
        tide_str=tide_str,
        best_window_hour=best["hour"],
        laser_tip=tip,
        breakdown=result["breakdown"],
        observed_wind=observed_wind,
        marine_forecast=marine_text,
    )
