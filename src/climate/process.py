"""Clean raw data and build analysis-ready tables, grouped by hackathon track."""

import pandas as pd

# Electricity mix columns in the OWID energy dataset (% of generation).
ELEC_MIX = [
    "coal_share_elec",
    "gas_share_elec",
    "oil_share_elec",
    "nuclear_share_elec",
    "hydro_share_elec",
    "wind_share_elec",
    "solar_share_elec",
    "biofuel_share_elec",
]

# Fossil/industrial CO2 sources in the OWID CO2 dataset (million tonnes).
INDUSTRY_CO2 = ["coal_co2", "oil_co2", "gas_co2", "cement_co2", "flaring_co2"]


def country_series(df: pd.DataFrame, country: str, cols: list[str], since: int = 1990):
    """Rows for one country from `since` onward, with year + selected columns."""
    out = df.loc[(df["country"] == country) & (df["year"] >= since), ["year", *cols]]
    return out.dropna(how="all", subset=cols)


def latest(df: pd.DataFrame, country: str, col: str) -> tuple[int | None, float | None]:
    """Most recent non-null (year, value) for a country and column."""
    rows = df.loc[(df["country"] == country) & df[col].notna(), ["year", col]]
    if rows.empty:
        return None, None
    row = rows.iloc[-1]
    return int(row["year"]), float(row[col])


def to_long(df: pd.DataFrame, cols: list[str], label: str = "source") -> pd.DataFrame:
    """Wide year x columns -> long format for stacked Plotly charts."""
    long = df.melt(id_vars="year", value_vars=cols, var_name=label, value_name="value")
    long[label] = long[label].str.replace(r"_share_elec|_co2", "", regex=True)
    return long


def yearly_extremes(
    weather: pd.DataFrame, hot_c: float = 25.0, heavy_rain_mm: float = 50.0
) -> pd.DataFrame:
    """Per-year mean temp, count of hot days and heavy-rain days (resilience indicators)."""
    return (
        weather.assign(
            year=weather["time"].dt.year,
            hot=weather["temperature_2m_max"] >= hot_c,
            heavy_rain=weather["precipitation_sum"] >= heavy_rain_mm,
        )
        .groupby("year")
        .agg(
            temp_mean=("temperature_2m_mean", "mean"),
            hot_days=("hot", "sum"),
            heavy_rain_days=("heavy_rain", "sum"),
            precip_total=("precipitation_sum", "sum"),
        )
        .reset_index()
    )
