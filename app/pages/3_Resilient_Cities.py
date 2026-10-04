"""Track 3: Resilient cities & buildings. Climate extremes per city."""

import plotly.express as px
import streamlit as st
from common import banner, city_picker, egg_helps, load_weather

from climate.process import yearly_extremes

st.set_page_config(page_title="Resilient Cities", layout="wide")
st.title("Resilient Cities & Buildings")
banner(
    "resilient_cities.png",
    "Flash flooding in Mid-City New Orleans, July 2019 – Bart Everson, CC BY 2.0",
    "Banks Street Kayakers - Mid-City New Orleans flooding July 2019.jpg",
    [
        ("IPCC AR6 – Cities, settlements and infrastructure", "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-6/"),
        ("Open-Meteo (weather data used here)", "https://open-meteo.com/"),
    ],
)
egg_helps(
    [
        "**Backup energy when storms cut the power:** the gas bag and battery keep lights, "
        "phone charging and a stove running during an outage.",
        "**Less waste on the streets:** food waste is treated where it's made, so fewer garbage"
        " trucks are needed and less rubbish ends up blocking drains.",
        "**Greener, cooler neighbourhoods:** the digestate feeds community gardens and street "
        "trees, which shade streets and soak up rain.",
    ]
)

city = city_picker()
hot_c = st.sidebar.slider("Hot day threshold (°C max)", 20, 40, 25)
rain_mm = st.sidebar.slider("Heavy rain threshold (mm/day)", 20, 150, 50)

yearly = yearly_extremes(load_weather(city), hot_c, rain_mm)

c1, c2 = st.columns(2)
c1.plotly_chart(
    px.bar(yearly, x="year", y="hot_days", title=f"{city}: days ≥ {hot_c}°C"),
    use_container_width=True,
)
c2.plotly_chart(
    px.bar(yearly, x="year", y="heavy_rain_days", title=f"{city}: days ≥ {rain_mm} mm rain"),
    use_container_width=True,
)
st.plotly_chart(
    px.line(yearly, x="year", y="temp_mean", title="Mean temperature (°C)"),
    use_container_width=True,
)

# TODO: your idea here, e.g. flood-risk map, building cooling demand, heat-vulnerable suburbs
