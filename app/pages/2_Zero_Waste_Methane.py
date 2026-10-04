"""Track 2: Zero waste & methane reduction."""

import plotly.express as px
import streamlit as st
from common import banner, country_picker, egg_helps, load_owid

from climate.process import country_series

st.set_page_config(page_title="Zero Waste & Methane", layout="wide")
st.title("Zero Waste & Methane Reduction")
banner(
    "zero_waste.png",
    "Ling Hall landfill site from the air, 2021 – Simon Tomson, CC BY-SA 2.0",
    "Ling Hall Landfill Site, aerial 2021 - geograph.org.uk - 6952595.jpg",
    [
        ("US EPA – Landfill gas basics", "https://www.epa.gov/lmop/basic-information-about-landfill-gas"),
        ("World Bank – What a Waste", "https://datatopics.worldbank.org/what-a-waste/"),
        ("Global Methane Pledge", "https://www.globalmethanepledge.org/"),
    ],
)
egg_helps(
    [
        "**Captures methane instead of releasing it:** food in landfill rots without air and "
        "releases methane. The Egg collects that gas and burns it for energy.",
        "**Measurable impact:** one home keeps about 290 kg of food out of landfill a year. A "
        "Community Egg for 50 homes saves about 6 t CO₂e a year, after allowing for leaks.",
        "**Nothing wasted:** the leftover digestate becomes fertiliser, and the Egg's methane "
        "sensor shuts the gas valve if it detects a leak.",
    ]
)

country = country_picker()
co2 = load_owid("co2")

compare = st.sidebar.multiselect("Compare with", ["World", "Australia", "United States"])
rows = co2[co2["country"].isin([country, *compare])]
per_cap = rows.loc[rows["year"] >= 1990, ["country", "year", "methane_per_capita"]]
st.plotly_chart(
    px.line(
        per_cap,
        x="year",
        y="methane_per_capita",
        color="country",
        title="Methane per person (t CO₂e)",
    ),
    use_container_width=True,
)

total = country_series(co2, country, ["methane", "flaring_co2"])
st.plotly_chart(
    px.bar(total, x="year", y="methane", title=f"{country}: total methane (Mt CO₂e)"),
    use_container_width=True,
)

st.info(
    "Landfill, agriculture and gas leaks are the main methane sources. Add waste data here, "
    "e.g. the World Bank *What a Waste* dataset or local council waste stats (see docs/themes.md)."
)
# TODO: data/raw/waste_*.csv -> landfill vs recycling vs compost breakdown
