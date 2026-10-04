"""Track 5: Awareness across all areas. Plain-language facts and actions."""

from pathlib import Path
from urllib.parse import quote

import streamlit as st
from common import country_picker, egg_helps, load_owid

from climate.process import latest

IMAGES = Path(__file__).resolve().parents[1] / "images" / "awareness"
COMMONS = "https://commons.wikimedia.org/wiki/File:"

st.set_page_config(page_title="Awareness", layout="wide")
st.title("Awareness")
st.caption("Plain-language climate facts, and what you can do about them.")
egg_helps(
    [
        "**Makes impact visible:** every kg logged shows the kWh made, methane captured and "
        "CO₂e avoided, so people can see the difference their scraps make.",
        "**Brings neighbours together:** a Community Egg shows each household's share, which "
        "encourages friendly competition between homes, schools and streets.",
        "**Teaches better habits:** the app explains what to feed the Egg, how to sort waste "
        "and how to stay safe around biogas.",
    ]
)

country = country_picker()
co2, energy = load_owid("co2"), load_owid("energy")


def fmt(df, col, digits=1):
    year, value = latest(df, country, col)
    return ("n/a", "") if value is None else (f"{value:,.{digits}f}", f" ({year})")


def card(image, heading, body, link_text, link_url):
    with st.container(border=True):
        st.image(str(IMAGES / image), width="stretch")
        st.markdown(f"#### {heading}")
        st.markdown(body)
        st.markdown(f"[{link_text}]({link_url})")


renew, renew_y = fmt(energy, "renewables_share_elec")
ghg, ghg_y = fmt(co2, "ghg_per_capita")

st.header(f"Did you know? ({country})")
cols = st.columns(3)
with cols[0]:
    card(
        "renewables.png",
        f"{renew}% renewable electricity",
        f"Share of {country}'s electricity that comes from renewables{renew_y}.",
        "Source: Our World in Data – renewable share of electricity",
        "https://ourworldindata.org/grapher/share-electricity-renewables",
    )
with cols[1]:
    card(
        "ghg_map.png",
        f"{ghg} t CO₂e per person",
        f"Greenhouse gases the average person in {country} is responsible for each year{ghg_y}.",
        "Source: Our World in Data – greenhouse gas emissions per capita",
        "https://ourworldindata.org/grapher/per-capita-ghg-emissions",
    )
with cols[2]:
    card(
        "food_waste.png",
        "Food waste makes methane",
        "Food scraps rotting in landfill release methane, which warms the planet about "
        "80× more than CO₂ over 20 years (about 28× over 100 years).",
        "Source: IPCC AR6, Chapter 7 (warming potentials)",
        "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/",
    )
st.markdown(
    "Also see: [US EPA – Importance of methane](https://www.epa.gov/gmi/importance-methane) · "
    "[US EPA – Food recovery hierarchy]"
    "(https://www.epa.gov/sustainable-management-food/food-recovery-hierarchy)"
)

st.header("What you can do")
actions = [
    (
        "heat_pump.png",
        "Electrification",
        "Switch gas appliances to heat pumps and induction; choose EVs and e-bikes.",
        "Read more: IEA – Heat pumps",
        "https://www.iea.org/energy-system/buildings/heat-pumps",
    ),
    (
        "compost.png",
        "Zero waste",
        "Compost food scraps; refuse single-use items; repair before replacing.",
        "Read more: US EPA – Composting at home",
        "https://www.epa.gov/recycle/composting-home",
    ),
    (
        "green_roof.png",
        "Resilient homes",
        "Insulate, add shading and green roofs, and know your flood and heat risk.",
        "Read more: US EPA – Green roofs and heat islands",
        "https://www.epa.gov/heatislands/using-green-roofs-reduce-heat-islands",
    ),
    (
        "recycling.png",
        "Green industry",
        "Support low-carbon products and local recycling.",
        "Read more: US EPA – Recycling basics and benefits",
        "https://www.epa.gov/recycle/recycling-basics-and-benefits",
    ),
]
for row in (actions[:2], actions[2:]):
    for col, action in zip(st.columns(2), row, strict=True):
        with col:
            card(*action)

credits = [
    ("Wind-solar hybrid system", "Wind-solar hybrid system.png", "Adityadav, public domain"),
    (
        "Per capita greenhouse gas emissions, 2022",
        "Per capita greenhouse gas emissions, 2022.png",
        "Our World in Data, CC BY 4.0",
    ),
    (
        "In landfills, food waste contributes to climate change",
        "In Landfills, Food Waste Contribute To Climate Change (3679111263).jpg",
        "US EPA, public domain",
    ),
    (
        "Ecodan outdoor unit in the snow",
        "Ecodan outdoor unit in the snow.jpg",
        "PeterEastern, CC BY-SA 4.0",
    ),
    ("Compost bin with compost", "Compost bin with compost.jpg", "Niwrat, CC BY-SA 4.0"),
    ("EVA Lanxmeer green roof", "EVA- Lanxmeer Green roof 2009.jpg", "Lamiot, CC BY-SA 4.0"),
    (
        "Sorted waste containers close-up",
        "Sorted waste containers close-up.jpg",
        "E961, CC BY 4.0",
    ),
]
with st.expander("Image credits (Wikimedia Commons)"):
    st.markdown(
        "\n".join(
            f"- [{title}]({COMMONS}{quote(file.replace(' ', '_'))}) – {who}"
            for title, file, who in credits
        )
        + "\n\nPhotos were cropped and resized for this page."
    )

# TODO: your idea here, e.g. carbon-footprint quiz, shareable infographic, school/community campaign
