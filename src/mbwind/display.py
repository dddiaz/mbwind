from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .score import direction_name

console = Console()


def render_report(
    score: int,
    recommendation: str,
    wind_kts: float,
    wind_dir: float,
    gust_kts: float,
    thermal: dict,
    tide_str: str,
    best_window_hour: int,
    tip: str,
    breakdown: dict,
    sport: str = "laser",
    observed_wind: dict | None = None,
    marine_forecast: str | None = None,
) -> None:
    rec_colors = {"GO": "green", "MAYBE": "yellow", "NO-GO": "red"}
    color = rec_colors.get(recommendation, "white")

    header = Text()
    header.append("Mission Bay Wind Confidence: ", style="bold")
    header.append(f"{score}/100", style=f"bold {color}")
    header.append(f" — {recommendation}", style=f"bold {color}")

    dir_name = direction_name(wind_dir) if wind_dir is not None else "?"
    gust_str = f" (gusts {gust_kts:.0f})" if gust_kts else ""

    lines = []
    lines.append(f"[bold]Wind:[/bold]     {wind_kts:.0f} kts {dir_name}{gust_str}")

    if observed_wind:
        obs = observed_wind
        lines.append(
            f"[dim]Observed: {obs['speed_kts'] or '?'} kts {obs['direction']} "
            f"(NOAA {obs['time']})[/dim]"
        )

    lines.append(
        f"[bold]Thermal:[/bold]  {thermal['strength']} "
        f"(coastal {thermal['coastal_temp_f']:.0f}°F, "
        f"inland {thermal['inland_temp_f']:.0f}°F, "
        f"Δ{thermal['delta_f']:.0f}°F)"
    )
    lines.append(f"[bold]Tide:[/bold]     {tide_str}")

    end_hour = min(best_window_hour + 3, 18)
    lines.append(
        f"[bold]Best window:[/bold] {best_window_hour % 12 or 12}{'pm' if best_window_hour >= 12 else 'am'}"
        f" - {end_hour % 12 or 12}{'pm' if end_hour >= 12 else 'am'}"
    )

    lines.append("")
    sport_label = sport.capitalize()
    lines.append(f"[italic]{sport_label} tip: {tip}[/italic]")

    if marine_forecast:
        short = marine_forecast[:200] + "..." if len(marine_forecast) > 200 else marine_forecast
        lines.append("")
        lines.append(f"[dim]Marine forecast: {short}[/dim]")

    body = "\n".join(lines)
    console.print()
    console.print(Panel(body, title=header, border_style=color, padding=(1, 2)))
    console.print()
