"""Track 4: Green industrialization. Industrial emissions and GDP decoupling."""

import plotly.express as px
import streamlit as st
from common import banner, country_picker, egg_helps, load_owid

from climate.process import INDUSTRY_CO2, country_series, to_long

st.set_page_config(page_title="Green Industrialization", layout="wide")
st.title("Green Industrialization")
banner(
    "green_industry.png",
    "Solar panels on a factory roof in Bangladesh – Ayman Nakib Badhan, CC BY-SA 4.0",
    "Powering Progress.jpg",
    [
        ("IEA – Industry", "https://www.iea.org/energy-system/industry"),
        ("Our World in Data – CO₂ emissions", "https://ourworldindata.org/co2-emissions"),
    ],
)
egg_helps(
    [
        "**Scales up to food businesses:** restaurants, food courts and fresh markets make tens"
        " of kg of food waste a day. Their gas can replace LPG in their kitchens.",
        "**Replaces chemical fertiliser:** making chemical fertiliser uses fossil gas. "
        "Digestate from the Egg returns nutrients to the soil instead.",
        "**Green jobs:** the egg shells, sensors and app can be built, installed and maintained"
        " locally.",
    ]
)

country = country_picker()
co2 = load_owid("co2")

sources = to_long(country_series(co2, country, INDUSTRY_CO2), INDUSTRY_CO2)
st.plotly_chart(
    px.area(sources, x="year", y="value", color="source", title="CO₂ by source (Mt)"),
    use_container_width=True,
)

# Decoupling: is the economy growing while emissions per $ fall?
intensity = country_series(co2, country, ["co2_per_gdp"])
st.plotly_chart(
    px.line(intensity, x="year", y="co2_per_gdp", title="CO₂ per $ of GDP (kg/$)"),
    use_container_width=True,
)

# TODO: your idea here, e.g. green steel/cement, industrial heat electrification,
# circular supply chains
