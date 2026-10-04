"""Feed the Egg mobile app: the published phone prototype."""

import streamlit as st

APP_SITE = "https://thing-blend-46702836.figma.site/"

st.set_page_config(page_title="Mobile App", layout="centered")
st.title("Mobile App")
st.caption("Feed the Egg in your pocket. Try the prototype below: it works like the real app.")

st.markdown(
    """
- **Scan the Egg** with your phone to see its status
- **Dashboard:** kg of food waste inside, methane made and electricity ready to use
- **Settings:** temperature, alerts and where the power goes
- **Knowledge:** what to feed the Egg, how biogas works and how to stay safe
"""
)
st.iframe(APP_SITE, height=900)
st.link_button("Open the app full screen", APP_SITE, type="primary")
