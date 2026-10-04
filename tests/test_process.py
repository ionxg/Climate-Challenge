import pandas as pd

from climate.process import country_series, latest, to_long, yearly_extremes


def test_yearly_extremes():
    weather = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01", "2020-06-01", "2021-01-01"]),
            "temperature_2m_mean": [10.0, 20.0, 12.0],
            "temperature_2m_max": [30.0, 22.0, 26.0],
            "precipitation_sum": [60.0, 2.0, 3.0],
        }
    )
    out = yearly_extremes(weather, hot_c=25, heavy_rain_mm=50)
    assert out["temp_mean"].tolist() == [15.0, 12.0]
    assert out["hot_days"].tolist() == [1, 1]
    assert out["heavy_rain_days"].tolist() == [1, 0]


def test_country_series_and_latest():
    df = pd.DataFrame(
        {
            "country": ["NZ", "NZ", "NZ", "AU"],
            "year": [1980, 2000, 2020, 2020],
            "methane": [1.0, 2.0, None, 9.0],
        }
    )
    assert country_series(df, "NZ", ["methane"])["year"].tolist() == [2000]
    assert latest(df, "NZ", "methane") == (2000, 2.0)
    assert latest(df, "XX", "methane") == (None, None)


def test_to_long_strips_suffixes():
    wide = pd.DataFrame({"year": [2020], "solar_share_elec": [5.0], "cement_co2": [1.0]})
    long = to_long(wide, ["solar_share_elec", "cement_co2"])
    assert set(long["source"]) == {"solar", "cement"}
