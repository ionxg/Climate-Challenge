"""Home egg-shaped anaerobic digester: food waste -> biomethane -> electricity + digestate.

Every kilo of food waste fed in releases methane over the following days (first-order decay).
Gas collects in a storage bag; a small generator burns it to supply the plug. Once feeding stops,
the contents finish digesting and then cure into a soil amendment.

Defaults are typical literature values for household food waste; tune them to measured data.
"""

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

METHANE_KWH_PER_M3 = 9.97  # lower heating value of methane
CO2E_AVOIDED_PER_KG = 0.5  # rough landfill emissions avoided per kg food waste (kg CO2e)
CH4_KG_PER_M3 = 0.717
CH4_GWP100 = 28  # warming of 1 kg methane vs 1 kg CO2 over 100 years
ELEC_USD_PER_KWH = 0.12  # Thai household tariff (~4.2 THB)


@dataclass(frozen=True)
class DigesterSpec:
    solids_frac: float = 0.25  # total solids, share of wet food waste
    volatile_frac: float = 0.90  # volatile (digestible) solids, share of total solids
    methane_yield: float = 0.45  # m³ CH4 per kg volatile solids (B0)
    decay_rate_35c: float = 0.15  # 1/day at 35 °C
    gen_efficiency: float = 0.25  # share of gas energy turned into electricity
    tank_biogas_m3: float = 0.5  # gas bag size
    methane_share: float = 0.60  # CH4 share of biogas
    digest_days: int = 21  # retention time after the last feed
    cure_days: int = 14  # composting the digestate before it goes on plants
    slurry_m3: float = 0.115  # working (liquid) volume of the egg
    max_load: float = 3.0  # kg volatile solids per m³ slurry per day before it turns sour

    @property
    def ch4_per_kg(self) -> float:
        """Total m³ of methane one kg of food waste can eventually release."""
        return self.solids_frac * self.volatile_frac * self.methane_yield

    @property
    def max_feed_kg(self) -> float:
        """Most food waste per day the microbes can keep up with."""
        return self.max_load * self.slurry_m3 / (self.solids_frac * self.volatile_frac)

    @property
    def tank_ch4_m3(self) -> float:
        return self.tank_biogas_m3 * self.methane_share

    @property
    def kwh_per_m3_ch4(self) -> float:
        return METHANE_KWH_PER_M3 * self.gen_efficiency

    def decay_rate(self, temp_c: float) -> float:
        """Microbes slow down outside 35 °C (simple temperature-correction factor)."""
        return self.decay_rate_35c * 1.06 ** (min(temp_c, 38.0) - 35.0)


DEFAULT_SPEC = DigesterSpec()


def simulate(
    feed: pd.DataFrame,
    end: date,
    usage_kwh_per_day: float,
    temp_c: float = 30.0,
    spec: DigesterSpec = DEFAULT_SPEC,
) -> pd.DataFrame:
    """Day-by-day gas and power balance from the first feed to `end`.

    `feed` has columns `date` and `kg`. Returns one row per day.
    """
    feed = feed.assign(date=pd.to_datetime(feed["date"]).dt.normalize())
    days = pd.date_range(feed["date"].min(), pd.Timestamp(end), freq="D")
    fed = feed.groupby("date")["kg"].sum().reindex(days, fill_value=0.0).to_numpy()

    # Methane released on each day of age by 1 kg fed on day 0.
    k = spec.decay_rate(temp_c)
    age = np.arange(len(days) + 1)
    kernel = spec.ch4_per_kg * (np.exp(-k * age[:-1]) - np.exp(-k * age[1:]))
    made = np.convolve(fed, kernel)[: len(days)]
    # Methane still locked in the waste inside the egg at the end of each day.
    pending = np.cumsum(fed) * spec.ch4_per_kg - np.cumsum(made)

    need = usage_kwh_per_day / spec.kwh_per_m3_ch4
    tank, burned, flared = (np.zeros(len(days)) for _ in range(3))
    level = 0.0
    for i, gas in enumerate(made):
        level += gas
        flared[i] = max(level - spec.tank_ch4_m3, 0.0)  # pressure relief -> flare
        level -= flared[i]
        burned[i] = min(level, need)
        level -= burned[i]
        tank[i] = level

    elec = burned * spec.kwh_per_m3_ch4
    return pd.DataFrame(
        {
            "date": days,
            "fed_kg": fed,
            "ch4_made_m3": made,
            "ch4_burned_m3": burned,
            "ch4_flared_m3": flared,
            "tank_ch4_m3": tank,
            "tank_pct": 100 * tank / spec.tank_ch4_m3,
            "pending_ch4_m3": pending,
            "elec_kwh": elec,
            "cum_elec_kwh": np.cumsum(elec),
        }
    )


def soil_timeline(feed: pd.DataFrame, today: date, spec: DigesterSpec = DEFAULT_SPEC) -> dict:
    """When the egg's contents finish digesting and become usable soil, assuming feeding stops."""
    last_feed = pd.to_datetime(feed["date"]).max().date()
    digested = last_feed + timedelta(days=spec.digest_days)
    soil = digested + timedelta(days=spec.cure_days)
    return {
        "last_feed": last_feed,
        "digested": digested,
        "soil_ready": soil,
        "days_to_digested": max((digested - today).days, 0),
        "days_to_soil": max((soil - today).days, 0),
        # Digestate is roughly the solids that were not turned into gas.
        "soil_kg": float(feed["kg"].sum() * spec.solids_frac * (1 - 0.6 * spec.volatile_frac)),
    }


def health(
    feed: pd.DataFrame,
    today: date,
    temp_c: float,
    ph: float | None = None,
    spec: DigesterSpec = DEFAULT_SPEC,
) -> list[dict]:
    """Checks that warn before the digester turns sour, smelly or slow.

    Returns a list of {"level": "ok" | "warn" | "bad", "title", "tip"}, worst first.
    """
    daily = feed.assign(date=pd.to_datetime(feed["date"]).dt.date).groupby("date")["kg"].sum()
    today_kg = float(daily.get(today, 0.0))
    last3 = sum(float(daily.get(today - timedelta(days=d), 0.0)) for d in range(3)) / 3
    limit = spec.max_feed_kg
    issues = []

    if last3 > limit:
        issues.append(
            {
                "level": "bad",
                "title": f"Overfed for 3 days (avg {last3:.1f} kg/day, limit ~{limit:.1f} kg)",
                "tip": "The microbes can't keep up, so the egg may turn sour and smell. "
                "Skip feeding for 2–3 days.",
            }
        )
    elif today_kg > limit:
        issues.append(
            {
                "level": "warn",
                "title": f"Fed {today_kg:.1f} kg today (limit ~{limit:.1f} kg/day)",
                "tip": "Keep the rest in the kitchen caddy and feed it tomorrow.",
            }
        )

    if ph is not None and not pd.isna(ph):
        if ph < 6.5:
            issues.append(
                {
                    "level": "bad",
                    "title": f"Turning sour (pH {ph:.1f})",
                    "tip": "Stop feeding for 3–5 days and stir in a spoon of baking soda. "
                    "Sour digesters smell and stop making gas.",
                }
            )
        elif ph < 6.8:
            issues.append(
                {
                    "level": "warn",
                    "title": f"Slightly acidic (pH {ph:.1f})",
                    "tip": "Feed less and cut back on fruit and bread for a few days.",
                }
            )
        elif ph > 8.0:
            issues.append(
                {
                    "level": "warn",
                    "title": f"Too alkaline (pH {ph:.1f})",
                    "tip": "Usually too much meat or dairy. Add more vegetable scraps.",
                }
            )

    if temp_c < 20:
        issues.append(
            {
                "level": "warn",
                "title": f"Too cold ({temp_c:.0f} °C)",
                "tip": "Gas production slows right down below 20 °C. "
                "Check the insulation jacket and heating pad.",
            }
        )
    elif temp_c > 40:
        issues.append(
            {
                "level": "warn",
                "title": f"Too hot ({temp_c:.0f} °C)",
                "tip": "Shade the egg. Microbes struggle above 40 °C.",
            }
        )

    if not issues:
        issues.append(
            {
                "level": "ok",
                "title": "Healthy",
                "tip": f"Feeding is within the ~{limit:.1f} kg/day limit"
                + (
                    f", pH {ph:.1f} is in the healthy range"
                    if ph is not None and not pd.isna(ph)
                    else ""
                )
                + f" and {temp_c:.0f} °C keeps the microbes active.",
            }
        )
    order = {"bad": 0, "warn": 1, "ok": 2}
    return sorted(issues, key=lambda i: order[i["level"]])


def demo_feed(today: date, days: int = 30, mean_kg: float = 1.0, seed: int = 7) -> pd.DataFrame:
    """Made-up feeding log for the demo: a household adding scraps most days."""
    rng = np.random.default_rng(seed)
    dates = [today - timedelta(days=d) for d in range(days, 0, -1)]
    kg = rng.normal(mean_kg, 0.3 * mean_kg, days).clip(0)
    kg[rng.random(days) < 0.15] = 0  # skipped days
    return pd.DataFrame({"date": dates, "kg": kg.round(2)})


def egg_options(
    kg_per_day: float, households: int, spec: DigesterSpec = DEFAULT_SPEC
) -> pd.DataFrame:
    """Yearly payoff per household of a Home Egg and a shared Community Egg.

    Leak shares: unattended home digesters lose about 10% of their gas (field studies measured
    8–16%); a maintained, monitored community unit is assumed to lose 3%.
    """
    kg = kg_per_day * 365
    ch4 = kg * spec.ch4_per_kg
    options = [
        # name, hardware cost per household (USD), leak share
        ("Home Egg", 1000.0, 0.10),
        ("Community Egg", 1500 / households + 70, 0.03),
    ]
    rows = []
    for name, cost, leak in options:
        saved = ch4 * (1 - leak) * spec.kwh_per_m3_ch4 * ELEC_USD_PER_KWH
        rows.append(
            {
                "Egg": name,
                "Cost per home ($)": cost,
                "Saves per year ($)": saved,
                "Payback (years)": cost / saved,
                "Net CO₂e saved (kg/yr)": kg * CO2E_AVOIDED_PER_KG
                - ch4 * leak * CH4_KG_PER_M3 * CH4_GWP100,
            }
        )
    return pd.DataFrame(rows)
