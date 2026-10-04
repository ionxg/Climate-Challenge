"""Hackathon demo dashboard home page. Run: streamlit run app/main.py"""

import streamlit as st
from common import BANNERS, country_picker, load_owid

from climate.process import latest

st.set_page_config(page_title="Climate Hackathon", layout="wide")
st.title("Climate Hackathon")
st.caption(
    "Food waste in landfill makes methane. Feed the Egg captures it and turns it into power, "
    "cooking gas and soil, with one shared Egg per street."
)

country = country_picker()
co2, energy = load_owid("co2"), load_owid("energy")

st.subheader(f"{country} at a glance")
kpis = [
    ("Renewables share of electricity", energy, "renewables_share_elec", "%"),
    ("Methane (Mt CO₂e)", co2, "methane", ""),
    ("CO₂ per $ GDP (kg)", co2, "co2_per_gdp", ""),
    ("Warming caused by country's GHG (°C)", co2, "temperature_change_from_ghg", ""),
]
for col, (label, df, field, unit) in zip(st.columns(len(kpis)), kpis, strict=True):
    year, value = latest(df, country, field)
    col.metric(label, "n/a" if value is None else f"{value:,.2f}{unit}", help=f"Latest: {year}")

st.subheader("How Feed the Egg fits each track")
tracks = [
    (
        "pages/1_Electrification.py",
        "electrification.png",
        "Electrification",
        "Makes local power from food scraps, and stores it as gas for the evening peak.",
    ),
    (
        "pages/2_Zero_Waste_Methane.py",
        "zero_waste.png",
        "Zero Waste & Methane",
        "Keeps food out of landfill and captures its methane for energy.",
    ),
    (
        "pages/3_Resilient_Cities.py",
        "resilient_cities.png",
        "Resilient Cities & Buildings",
        "Backup power and cooking gas when storms cut the grid; less waste on the streets.",
    ),
    (
        "pages/4_Green_Industrialization.py",
        "green_industry.png",
        "Green Industrialization",
        "Scales up to markets and restaurants, and replaces chemical fertiliser with digestate.",
    ),
    (
        "pages/5_Awareness.py",
        "awareness.png",
        "Awareness",
        "Shows every household the kWh made and CO₂e saved by their scraps.",
    ),
    (
        "pages/6_Feed_the_Egg.py",
        "eggcycle.png",
        "Feed the Egg",
        "Our app: power made, biomethane left, digester health and days until soil.",
    ),
    (
        "pages/7_3D_Model.py",
        "model_3d.png",
        "3D Model",
        "The Egg, its sensors and power unit. Press X-ray to see inside.",
    ),
    (
        "pages/8_Mobile_App.py",
        "mobile_app.png",
        "Mobile App",
        "Scan the Egg and see food waste, methane and electricity on your phone.",
    ),
]
for start in range(0, len(tracks), 3):
    row = tracks[start : start + 3]
    for col, (page, image, label, blurb) in zip(st.columns(3), row, strict=False):
        with col.container(border=True):
            st.image(str(BANNERS / image), width="stretch")
            st.page_link(page, label=f"**{label}**")
            st.caption(blurb)
