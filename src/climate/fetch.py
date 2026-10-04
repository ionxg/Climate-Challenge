"""Download raw climate data into data/raw.

Sources (all free, no key):
- Our World in Data CO2/GHG dataset   -> methane, cement, industry, emissions intensity
- Our World in Data energy dataset    -> electricity mix, renewables share
- Open-Meteo historical weather       -> heat and heavy-rain extremes for cities

Run: python -m climate.fetch  (with PYTHONPATH=src)
"""

import pandas as pd
import requests

from climate.config import DATA_RAW

OWID_URLS = {
    "co2": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
    "energy": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
}
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Edit to match the cities your challenge cares about.
CITIES = {
    "Wellington": (-41.29, 174.78),
    "Auckland": (-36.85, 174.76),
    "Christchurch": (-43.53, 172.64),
    "Bangkok": (13.75, 100.50),
    "Sydney": (-33.87, 151.21),
}


def fetch_owid(name: str) -> pd.DataFrame:
    """Download one Our World in Data dataset ('co2' or 'energy')."""
    return pd.read_csv(OWID_URLS[name])


def fetch_daily_weather(
    lat: float, lon: float, start: str = "1990-01-01", end: str = "2025-12-31"
) -> pd.DataFrame:
    """Daily mean/max temperature and precipitation for a location."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_mean,temperature_2m_max,precipitation_sum",
        "timezone": "auto",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=120)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json()["daily"])
    df["time"] = pd.to_datetime(df["time"])
    return df


def main() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    for name in OWID_URLS:
        df = fetch_owid(name)
        out = DATA_RAW / f"owid_{name}.csv"
        df.to_csv(out, index=False)
        print(f"Saved {len(df):,} rows -> {out}")

    city = "Wellington"
    df = fetch_daily_weather(*CITIES[city])
    out = DATA_RAW / f"weather_{city.lower()}.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} rows -> {out}")


if __name__ == "__main__":
    main()
