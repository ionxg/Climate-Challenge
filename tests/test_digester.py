from datetime import date

import pandas as pd
import pytest

from climate.digester import DigesterSpec, demo_feed, health, simulate, soil_timeline


def test_one_kg_releases_its_full_methane_potential():
    spec = DigesterSpec(tank_biogas_m3=100)
    feed = pd.DataFrame({"date": [date(2026, 1, 1)], "kg": [1.0]})
    sim = simulate(feed, date(2026, 6, 1), usage_kwh_per_day=0, spec=spec)
    assert sim["ch4_made_m3"].sum() == pytest.approx(spec.ch4_per_kg, rel=1e-6)
    assert sim["pending_ch4_m3"].iloc[-1] == pytest.approx(0, abs=1e-6)
    assert sim["tank_ch4_m3"].iloc[-1] == pytest.approx(spec.ch4_per_kg, rel=1e-6)


def test_gas_balance_and_flaring():
    spec = DigesterSpec(tank_biogas_m3=0.05)
    feed = demo_feed(date(2026, 3, 1), days=20, mean_kg=2.0)
    sim = simulate(feed, date(2026, 4, 1), usage_kwh_per_day=0.1, spec=spec)
    out = sim["ch4_burned_m3"] + sim["ch4_flared_m3"] + sim["tank_ch4_m3"].iloc[-1]
    assert out.sum() == pytest.approx(sim["ch4_made_m3"].sum())
    assert sim["ch4_flared_m3"].sum() > 0
    assert (sim["tank_pct"] <= 100 + 1e-9).all()
    assert sim["elec_kwh"].max() <= 0.1 + 1e-9


def test_soil_timeline():
    feed = pd.DataFrame({"date": [date(2026, 1, 1), date(2026, 1, 10)], "kg": [1.0, 1.0]})
    t = soil_timeline(feed, today=date(2026, 1, 10))
    assert t["days_to_digested"] == 21
    assert t["days_to_soil"] == 35
    assert soil_timeline(feed, today=date(2026, 6, 1))["days_to_soil"] == 0


def test_health_flags_overfeeding_sour_and_cold():
    today = date(2026, 1, 10)
    spec = DigesterSpec()
    assert spec.max_feed_kg == pytest.approx(1.53, abs=0.01)

    normal = pd.DataFrame({"date": [today], "kg": [1.0]})
    assert [i["level"] for i in health(normal, today, 30, 7.2)] == ["ok"]

    big_day = pd.DataFrame({"date": [today], "kg": [2.5]})
    assert health(big_day, today, 30)[0]["level"] == "warn"

    three_days = pd.DataFrame({"date": [date(2026, 1, d) for d in (8, 9, 10)], "kg": [2.0] * 3})
    assert health(three_days, today, 30)[0]["level"] == "bad"

    levels = {i["title"].split(" (")[0]: i["level"] for i in health(normal, today, 15, 6.2)}
    assert levels == {"Turning sour": "bad", "Too cold": "warn"}
