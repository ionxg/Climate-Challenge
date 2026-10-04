"""Shared data loading and sidebar controls for all dashboard pages."""

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from climate.config import DATA_RAW  # noqa: E402
from climate.fetch import CITIES, fetch_daily_weather  # noqa: E402

DEFAULT_COUNTRY = "New Zealand"
BANNERS = Path(__file__).resolve().parent / "images" / "banners"
COMMONS = "https://commons.wikimedia.org/wiki/File:"


def banner(image: str, credit: str, commons_file: str, links: list[tuple[str, str]]) -> None:
    """Wide photo under the page title, with its Wikimedia Commons credit and reference links."""
    st.image(str(BANNERS / image), width="stretch")
    st.caption(f"Photo: [{credit}]({COMMONS}{quote(commons_file.replace(' ', '_'))})")
    st.markdown("**Learn more:** " + " · ".join(f"[{text}]({url})" for text, url in links))


def egg_helps(points: list[str]) -> None:
    """Box tying this track to EggCycle, for judges reading the page."""
    with st.container(border=True):
        st.subheader("How EggCycle helps")
        st.markdown("\n".join(f"- {p}" for p in points))
        st.page_link("pages/6_Egg_Digester.py", label="Open the EggCycle app")


def _require(path: Path) -> None:
    if not path.exists():
        st.warning("No data yet. Run the **Fetch data** task (or F5 → Fetch data) first.")
        st.stop()


@st.cache_data
def load_owid(name: str) -> pd.DataFrame:
    path = DATA_RAW / f"owid_{name}.csv"
    _require(path)
    return pd.read_csv(path)


@st.cache_data(show_spinner="Downloading weather…")
def load_weather(city: str) -> pd.DataFrame:
    path = DATA_RAW / f"weather_{city.lower()}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["time"])
    df = fetch_daily_weather(*CITIES[city])
    df.to_csv(path, index=False)
    return df


def country_picker() -> str:
    """Sidebar country selector shared across pages (only real countries, not regions)."""
    co2 = load_owid("co2")
    countries = sorted(co2.loc[co2["iso_code"].notna(), "country"].unique())
    current = st.session_state.get("country", DEFAULT_COUNTRY)
    country = st.sidebar.selectbox("Country", countries, index=countries.index(current))
    st.session_state["country"] = country
    return country


def city_picker() -> str:
    return st.sidebar.selectbox("City", list(CITIES))
