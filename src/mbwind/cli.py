import click
from datetime import datetime, timedelta

from .sources.open_meteo import fetch_coastal_forecast, fetch_inland_forecast, get_hourly_at, find_best_window
from .sources.noaa import fetch_tide_data, fetch_tide_predictions, fetch_wind_observation, fetch_marine_forecast, classify_tide
from .sources.thermal import compute_thermal_gradient, marine_layer_suppression
from .score import compute_confidence, sport_tip, SPORTS
from .display import render_report


@click.command()
@click.option("--hour", type=int, default=None, help="Hour (0-23) to check. Defaults to current hour, or 13 for tomorrow.")
@click.option("--tomorrow", is_flag=True, help="Check tomorrow's forecast instead of today.")
@click.option("--sport", type=click.Choice(SPORTS), default="laser", help="Sport to score for.")
def main(hour: int | None, tomorrow: bool, sport: str):
    """Mission Bay wind confidence for laser sailing."""
    target_date = datetime.now().astimezone()
    if tomorrow:
        target_date = target_date + timedelta(days=1)
    if hour is None:
        hour = 13 if tomorrow else datetime.now().hour

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

    coastal_now = get_hourly_at(coastal, hour, target_date)
    inland_now = get_hourly_at(inland, hour, target_date)

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
        sport=sport,
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

    best = find_best_window(coastal, target_date)
    tip = sport_tip(coastal_now["wind_kts"], coastal_now["gusts_kts"], sport)

    render_report(
        score=result["score"],
        recommendation=result["recommendation"],
        wind_kts=coastal_now["wind_kts"],
        wind_dir=coastal_now["wind_dir"],
        gust_kts=coastal_now["gusts_kts"],
        thermal=thermal,
        tide_str=tide_str,
        best_window_hour=best["hour"],
        tip=tip,
        breakdown=result["breakdown"],
        sport=sport,
        observed_wind=observed_wind,
        marine_forecast=marine_text,
    )
