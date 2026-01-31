from mbwind.score import (
    score_wind_speed,
    score_direction,
    score_thermal,
    score_gust_factor,
    score_time_of_day,
    compute_confidence,
    direction_name,
    laser_tip,
)


def test_direction_name():
    assert direction_name(0) == "N"
    assert direction_name(270) == "W"
    assert direction_name(290) == "WNW"
    assert direction_name(90) == "E"


def test_score_wind_speed():
    assert score_wind_speed(0) == 0
    assert score_wind_speed(2) == 0
    assert score_wind_speed(5) == 10
    assert score_wind_speed(10) == 30  # ideal
    assert score_wind_speed(18) == 18
    assert score_wind_speed(30) == 5


def test_score_direction():
    assert score_direction(270) == 20  # W — ideal
    assert score_direction(290) == 20  # WNW — ideal
    assert score_direction(90) == 2  # E — offshore, bad


def test_score_thermal():
    assert score_thermal(0) == 0
    assert score_thermal(5) == 4
    assert score_thermal(15) == 13
    assert score_thermal(20) == 17
    assert score_thermal(30) == 20


def test_score_gust_factor():
    assert score_gust_factor(10, 11) == 15  # steady
    assert score_gust_factor(10, 20) == 4  # very gusty
    assert score_gust_factor(0, 0) == 0


def test_score_time_of_day():
    assert score_time_of_day(13) == 15  # peak thermal
    assert score_time_of_day(7) == 3  # early morning


def test_compute_confidence_go():
    result = compute_confidence(
        wind_kts=10,
        wind_dir=270,
        gust_kts=13,
        thermal_delta_f=20,
        marine_layer_suppression=0.0,
        hour=13,
    )
    assert result["score"] >= 65
    assert result["recommendation"] == "GO"


def test_compute_confidence_nogo():
    result = compute_confidence(
        wind_kts=2,
        wind_dir=90,
        gust_kts=3,
        thermal_delta_f=2,
        marine_layer_suppression=0.7,
        hour=7,
    )
    assert result["score"] < 40
    assert result["recommendation"] == "NO-GO"


def test_laser_tip():
    assert "Light air" in laser_tip(3, 4)
    assert "hiking" in laser_tip(12, 15).lower()
