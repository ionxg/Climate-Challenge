"""Feed the Egg 3D model: the digester, its sensors and the power unit."""

from pathlib import Path

import streamlit as st

MODEL_3D = Path(__file__).resolve().parents[2] / "figures" / "eggcycle-3d.html"

st.set_page_config(page_title="3D Model", layout="wide")
st.title("3D Model")
st.caption("Drag to rotate, scroll to zoom. Press X-ray to see the slurry and gas dome inside.")

st.iframe(MODEL_3D, height=700)

st.markdown(
    """
- **Egg:** 90 cm tall × 60 cm wide, about 170 L (115 L of slurry plus the gas dome)
- **Overall:** about 1.55 m tall on an 80 cm base, with the gas bag, generator, battery and plug
- **Feeds:** about 1 kg of scraps a day, which makes about 0.25 kWh of electricity
"""
)
