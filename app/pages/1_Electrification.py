"""Track 1: Electrification. Grid mix and renewables share."""

import plotly.express as px
import streamlit as st
from common import banner, country_picker, egg_helps, load_owid

from climate.process import ELEC_MIX, country_series, latest, to_long

st.set_page_config(page_title="Electrification", layout="wide")
st.title("Electrification")
banner(
    "electrification.png",
    "Power County wind farm, Idaho – US Dept. of Energy, public domain",
    "Power County Wind Farm 002.jpg",
    [
        ("Our World in Data – Electricity mix", "https://ourworldindata.org/electricity-mix"),
        ("IEA – Electricity", "https://www.iea.org/energy-system/electricity"),
    ],
)
egg_helps(
    [
        "**Turns food scraps into local electricity:** about 0.25 kWh per kg. A Community Egg "
        "shared by 50 homes makes about 10 kWh a day, enough to charge around 20 e-bike "
        "batteries.",
        "**Stored gas is a battery:** the gas bag holds energy until it's needed, so the Egg "
        "can make power in the evening peak, after solar panels stop.",
        "**Local and renewable:** power is made on the street where the waste is, from scraps "
        "that would otherwise rot in landfill.",
    ]
)

country = country_picker()
energy = load_owid("energy")

year, renew = latest(energy, country, "renewables_share_elec")
_, per_cap = latest(energy, country, "per_capita_electricity")
c1, c2 = st.columns(2)
c1.metric("Renewables share of electricity", f"{renew:.1f}%" if renew else "n/a", help=str(year))
c2.metric("Electricity per person (kWh)", f"{per_cap:,.0f}" if per_cap else "n/a")

mix = to_long(country_series(energy, country, ELEC_MIX), ELEC_MIX)
st.plotly_chart(
    px.area(mix, x="year", y="value", color="source", title="Electricity mix (% of generation)"),
    use_container_width=True,
)

# TODO: your idea here, e.g. EV/heat-pump uptake, grid emissions intensity, demand forecasting
