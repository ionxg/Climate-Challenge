"""Feed the Egg: companion app for the egg-shaped home food-waste digester."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from common import banner  # also puts src/ on the path

from climate.digester import (
    CO2E_AVOIDED_PER_KG,
    DigesterSpec,
    demo_feed,
    egg_options,
    health,
    simulate,
    soil_timeline,
)
from climate.ingest import LEAK_ALARM_PPM, feed_log, load_readings

MODEL_3D = Path(__file__).resolve().parents[2] / "figures" / "eggcycle-3d.html"
APP_SITE = "https://thing-blend-46702836.figma.site/"

st.set_page_config(page_title="Feed the Egg", layout="centered")
st.title("Feed the Egg")
st.caption("Food scraps in → biomethane → power at the plug → soil for your plants.")
banner(
    "eggcycle.png",
    "A household biogas digester in South Africa – SuSanA Secretariat, CC BY 2.0",
    "Household biogas plant (2937019579).jpg",
    [
        ("Methane from food waste (UCC thesis)", "https://cora.ucc.ie/handle/10468/1362"),
        (
            "Biogas safety (Biogas Digest Vol. 2)",
            "https://samplecontents.library.ph/en-practical_action/Energy/Biogas/Biogas%20Digest%20Vol%202/page68.html",
        ),
        (
            "Digester heat loss study",
            "https://www.jeeng.net/Analysis-of-Heat-Loss-of-a-Biogas-Anaerobic-Digester-in-Weather-Conditions-in-Poland,89660,0,1.html",
        ),
    ],
)

st.subheader("The Egg in 3D")
st.caption("Drag to rotate, scroll to zoom. Press X-ray to see the slurry and gas dome inside.")
st.iframe(MODEL_3D, height=560)

st.subheader("The mobile app")
st.markdown(
    "Scan the Egg with your phone to see how much food waste is inside, the methane it has "
    "made and the electricity ready to use, then change its settings and learn what to feed it."
)
_, phone, _ = st.columns([1, 3, 1])
with phone:
    st.iframe(APP_SITE, height=760)
    st.link_button("Open the app full screen", APP_SITE, type="primary", width="stretch")

# --- Settings -------------------------------------------------------------------------------
readings = load_readings()
live = not readings.empty and st.sidebar.toggle("Live data from the egg", value=True)
today = st.sidebar.date_input("Today", date.today())
if live:
    last = readings.ffill().iloc[-1]  # an offline sensor keeps its last good value
    temp_c = float(last["temp_c"]) if pd.notna(last["temp_c"]) else 30.0
    ph = float(last["ph"]) if "ph" in last and pd.notna(last["ph"]) else None
else:
    temp_c = st.sidebar.slider("Digester temperature (°C)", 15, 38, 30)
    ph = st.sidebar.slider("Slurry pH (demo)", 5.5, 8.5, 7.2, 0.1)
usage = st.sidebar.slider("Power drawn from the plug (kWh/day)", 0.0, 1.0, 0.2, 0.05)
tank = st.sidebar.slider("Gas bag size (m³ biogas)", 0.05, 1.0, 0.15, 0.05)
spec = DigesterSpec(tank_biogas_m3=tank)

if live:
    seen = (pd.Timestamp.now() - last["time"]).total_seconds() / 60
    st.caption(f"{last['device']} · last reading {seen:,.0f} min ago · {temp_c:.1f} °C inside")
    if last["ch4_ppm"] >= LEAK_ALARM_PPM:
        st.error(
            f"Methane leak: {last['ch4_ppm']:.0f} ppm near the egg. The gas valve has been "
            "closed. Open windows, keep flames away, and check the fittings."
        )
    elif not last["valve_open"]:
        st.warning("The gas valve is closed, so the plug can't make power right now.")
    feed = feed_log(readings)
    with st.expander("Feeding log (weighed by the egg's hopper)"):
        st.dataframe(feed, hide_index=True, width="stretch")
else:
    if "feed" not in st.session_state:
        st.session_state.feed = demo_feed(today)
    with st.expander("Feeding log (demo data, edit it here)"):
        feed = st.data_editor(
            st.session_state.feed,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "kg": st.column_config.NumberColumn("Food waste (kg)", min_value=0.0, step=0.1),
            },
            hide_index=True,
            width="stretch",
        ).dropna()

if feed.empty or feed["kg"].sum() == 0:
    st.info("Add some food waste to the feeding log to get started.")
    st.stop()

# --- Model ----------------------------------------------------------------------------------
timeline = soil_timeline(feed, today, spec)
horizon = max(timeline["soil_ready"], today) + timedelta(days=3)
sim = simulate(feed, horizon, usage, temp_c, spec)
sim["period"] = (sim["date"].dt.date <= today).map({True: "So far", False: "Forecast"})
now = sim[sim["date"].dt.date <= today].iloc[-1].copy()
if live:  # measured values beat modelled ones
    now["cum_elec_kwh"] = last["gen_kwh"]
    now["tank_pct"] = last["bag_pct"]
    now["tank_ch4_m3"] = last["bag_pct"] / 100 * spec.tank_ch4_m3

# --- Egg status ----------------------------------------------------------------------------
fill = float(now["tank_pct"])
egg_svg = f"""
<svg viewBox="0 0 120 150" width="120" style="display:block;margin:auto">
  <defs><clipPath id="egg"><path d="M60 5 C25 5 8 65 8 95 C8 128 32 145 60 145
        C88 145 112 128 112 95 C112 65 95 5 60 5Z"/></clipPath></defs>
  <g clip-path="url(#egg)">
    <rect width="120" height="150" fill="#f3efe6"/>
    <rect y="{150 - 1.4 * fill:.0f}" width="120" height="150" fill="#7bc47f"/>
  </g>
  <path d="M60 5 C25 5 8 65 8 95 C8 128 32 145 60 145 C88 145 112 128 112 95
        C112 65 95 5 60 5Z" fill="none" stroke="#5a4a3a" stroke-width="3"/>
  <text x="60" y="88" text-anchor="middle" font-size="20" font-weight="bold"
        fill="#2d2d2d">{fill:.0f}%</text>
  <text x="60" y="106" text-anchor="middle" font-size="9" fill="#2d2d2d">gas bag</text>
</svg>
"""
left, right = st.columns([1, 2])
left.markdown(egg_svg, unsafe_allow_html=True)
with right:
    st.metric("Power produced so far", f"{now['cum_elec_kwh']:.2f} kWh")
    st.metric(
        "Biomethane in the bag",
        f"{now['tank_ch4_m3'] * 1000:.0f} L",
        help=f"≈ {now['tank_ch4_m3'] * spec.kwh_per_m3_ch4:.2f} kWh still available at the plug",
    )

c1, c2, c3 = st.columns(3)
c1.metric(
    "Days until soil",
    timeline["days_to_soil"],
    help=f"Digesting until {timeline['digested']:%d %b}, then curing until "
    f"{timeline['soil_ready']:%d %b} (if you stop feeding today).",
)
c2.metric(
    "Gas still to come",
    f"{now['pending_ch4_m3'] * 1000:.0f} L",
    help="Biomethane the food already inside will still release.",
)
c3.metric("CO₂e kept out of landfill", f"{feed['kg'].sum() * CO2E_AVOIDED_PER_KG:.1f} kg")

if timeline["days_to_soil"] == 0:
    st.success(f"Digestate ready: about {timeline['soil_kg']:.1f} kg of dry soil amendment.")
elif timeline["days_to_digested"] == 0:
    st.info("Digestion is finished. Move the digestate to a compost bin to cure.")

charges = now["cum_elec_kwh"] / 0.015
st.caption(f"That's enough to charge a phone about **{charges:.0f} times**.")

# --- Health --------------------------------------------------------------------------------
st.subheader("Digester health")
today_kg = float(feed.loc[pd.to_datetime(feed["date"]).dt.date == today, "kg"].sum())
st.progress(
    min(today_kg / spec.max_feed_kg, 1.0),
    text=f"Fed today: {today_kg:.1f} of ~{spec.max_feed_kg:.1f} kg",
)
show = {"ok": st.success, "warn": st.warning, "bad": st.error}
for issue in health(feed, today, temp_c, ph, spec):
    show[issue["level"]](f"**{issue['title']}**  \n{issue['tip']}")

# --- Charts --------------------------------------------------------------------------------
st.subheader("Power produced")
# Repeat today's point in the forecast so the two areas join up.
joined = pd.concat([sim, sim[sim["date"].dt.date == today].assign(period="Forecast")])
joined = joined.sort_values("date", kind="stable")
power = px.line(joined, x="date", y="cum_elec_kwh", color="period", labels={"cum_elec_kwh": "kWh"})
power.update_traces(fill="tozeroy")
st.plotly_chart(power, width="stretch")

st.subheader("Biomethane")
if live:  # plot the measured bag level (daily average), not the model's end-of-day level
    measured = readings.set_index("time")["bag_pct"].resample("D").mean() / 100 * spec.tank_ch4_m3
    sim["tank_ch4_m3"] = sim["date"].map(measured).fillna(sim["tank_ch4_m3"])
gas = sim.melt(
    id_vars="date",
    value_vars=["tank_ch4_m3", "pending_ch4_m3"],
    var_name="where",
    value_name="m³",
).replace({"tank_ch4_m3": "In gas bag", "pending_ch4_m3": "Still in the food waste"})
fig = px.line(gas, x="date", y="m³", color="where")
fig.add_vline(x=pd.Timestamp(today).timestamp() * 1000, line_dash="dot", annotation_text="today")
st.plotly_chart(fig, width="stretch")

if sim["ch4_flared_m3"].sum() > 0:
    st.warning(
        f"The gas bag was full and {sim['ch4_flared_m3'].sum() * 1000:.0f} L was flared. "
        "Use more power at the plug or fit a bigger bag."
    )

# --- Which egg ----------------------------------------------------------------------------
st.subheader("Home Egg or Community Egg?")
c1, c2 = st.columns(2)
kg_day = c1.slider(
    "Food waste per home (kg/day)",
    0.2,
    2.0,
    0.8,
    0.1,
    help="A 3-person Thai home wastes about 0.8 kg of food a day.",
)
homes = c2.slider("Homes sharing a Community Egg", 10, 200, 50, 10)
options = egg_options(kg_day, homes, spec)
st.dataframe(
    options,
    hide_index=True,
    width="stretch",
    column_config={
        "Cost per home ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Saves per year ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Payback (years)": st.column_config.NumberColumn(format="%.0f"),
        "Net CO₂e saved (kg/yr)": st.column_config.NumberColumn(format="%.0f"),
    },
)
best = options.loc[options["Payback (years)"].idxmin(), "Egg"]
st.success(
    f"**Fastest payback: {best}.** Share one Community Egg per apartment block or street. "
    "A Home Egg with its own generator costs too much for the power one home makes."
)
st.caption(
    "Thai prices. Home digesters leak about 10% of their gas, which cancels part of the "
    "climate benefit; a monitored Community Egg leaks less. Sources: "
    "[household food waste in Thailand]"
    "(https://ph01.tci-thaijo.org/index.php/aer/article/view/259655) · "
    "[biogas leaks from home digesters](https://researchportal.hw.ac.uk/en/publications/"
    "measuring-biogas-venting-from-over-pressurisation-of-household-sc/)"
)

with st.expander("How the numbers work"):
    st.markdown(
        f"""
- 1 kg of food waste releases about **{spec.ch4_per_kg * 1000:.0f} L of methane**
  over roughly {spec.digest_days} days. Microbes work faster near 35 °C.
- 1 m³ of methane holds {spec.kwh_per_m3_ch4 / spec.gen_efficiency:.1f} kWh. A small generator
  turns about {spec.gen_efficiency:.0%} of that into electricity at the plug,
  so **1 kg of scraps ≈ {spec.ch4_per_kg * spec.kwh_per_m3_ch4:.2f} kWh**.
- After the last feed, the contents digest for {spec.digest_days} days, then cure for
  {spec.cure_days} days before going on plants.
"""
    )
