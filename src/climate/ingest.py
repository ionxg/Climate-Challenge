"""Receive EggCycle sensor readings from the ESP32 and save them for the dashboard.

On the laptop (same Wi-Fi as the egg):
    $env:PYTHONPATH = "src"; python -m climate.ingest           # listen on port 8000
    $env:PYTHONPATH = "src"; python -m climate.ingest --fake    # no hardware: 30 days of fake data

The ESP32 POSTs JSON to http://<laptop-ip>:8000/readings with header X-Egg-Key: <EGG_API_KEY>.
"""

import argparse
import csv
import json
import os
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pandas as pd

from climate.config import DATA_RAW
from climate.digester import DigesterSpec, demo_feed, simulate

READINGS = DATA_RAW / "egg_readings.csv"
EGG_API_KEY = os.getenv("EGG_API_KEY", "")
LEAK_ALARM_PPM = 5000  # 10% of methane's lower explosive limit (5% in air)
EGG_SPEC = DigesterSpec(tank_biogas_m3=0.15)  # 150 L gas bag in the base

NUMERIC = ["temp_c", "ph", "hopper_kg", "fed_kg", "bag_pct", "gen_w", "gen_kwh", "ch4_ppm"]
FIELDS = ["time", "device", *NUMERIC, "valve_open"]


def append_reading(payload: dict, path: Path = READINGS) -> dict:
    """Validate one ESP32 reading and append it to the CSV. Raises ValueError if malformed."""
    row = {
        "time": payload.get("time") or datetime.now().isoformat(timespec="seconds"),
        "device": str(payload.get("device", "egg-01")),
        "valve_open": int(bool(payload.get("valve_open", True))),
    }
    for field in NUMERIC:
        try:
            value = payload.get(field, None if field == "ph" else 0.0)  # no pH sensor = missing
            row[field] = float("nan") if value is None else float(value)  # None = sensor offline
        except (TypeError, ValueError) as err:
            raise ValueError(f"{field} must be a number") from err

    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(row)
    return row


def load_readings(path: Path = READINGS) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=FIELDS)
    return pd.read_csv(path, parse_dates=["time"]).sort_values("time")


def feed_log(readings: pd.DataFrame) -> pd.DataFrame:
    """Daily kg of food waste, from the hopper's 'emptied into the egg' events."""
    fed = readings[readings["fed_kg"] > 0]
    return (
        fed.groupby(fed["time"].dt.date)["fed_kg"].sum().rename_axis("date").reset_index(name="kg")
    )


def fake_readings(today: date, days: int = 30, spec: DigesterSpec = EGG_SPEC) -> pd.DataFrame:
    """Readings an egg would have sent every 3 hours, built from the digester model."""
    rng = np.random.default_rng(1)
    feed = demo_feed(today, days)
    sim = simulate(feed, today, usage_kwh_per_day=0.2, temp_c=30, spec=spec).set_index("date")
    rows, prev = [], {"tank_ch4_m3": 0.0, "cum_elec_kwh": 0.0}
    for day, s in sim.iterrows():
        for hour in range(0, 24, 3):
            # The bag fills through the day; the generator empties it into the battery at 21:00.
            ran = hour >= 21
            bag = s["tank_ch4_m3"] if ran else prev["tank_ch4_m3"] + s["ch4_made_m3"] * hour / 24
            rows.append(
                {
                    "time": day + timedelta(hours=hour),
                    "device": "egg-01",
                    "temp_c": round(30 + rng.normal(0, 0.8), 1),
                    "ph": round(7.2 + rng.normal(0, 0.06), 2),
                    "hopper_kg": 0.0,
                    "fed_kg": round(s["fed_kg"], 2) if hour == 18 else 0.0,
                    "bag_pct": round(min(100 * bag / spec.tank_ch4_m3, 100), 1),
                    "gen_w": 350.0 if hour == 21 and s["elec_kwh"] > 0 else 0.0,
                    "gen_kwh": round((s if ran else prev)["cum_elec_kwh"], 3),
                    "ch4_ppm": round(abs(rng.normal(40, 15))),
                    "valve_open": 1,
                }
            )
        prev = s
    out = pd.DataFrame(rows, columns=FIELDS)
    return out[out["time"] <= datetime.now()]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 (http.server naming)
        if self.path != "/readings":
            return self._reply(404, {"error": "not found"})
        if EGG_API_KEY and self.headers.get("X-Egg-Key") != EGG_API_KEY:
            return self._reply(401, {"error": "bad key"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            row = append_reading(json.loads(self.rfile.read(length)))
        except (ValueError, json.JSONDecodeError) as err:
            return self._reply(400, {"error": str(err)})
        if row["ch4_ppm"] >= LEAK_ALARM_PPM:
            print(f"WARNING: METHANE LEAK ALARM from {row['device']}: {row['ch4_ppm']:.0f} ppm")
        self._reply(200, {"ok": True})

    def _reply(self, status: int, body: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--fake", action="store_true", help="write fake readings and exit")
    args = parser.parse_args()

    if args.fake:
        READINGS.parent.mkdir(parents=True, exist_ok=True)
        fake_readings(date.today()).to_csv(READINGS, index=False)
        print(f"Wrote fake readings to {READINGS}")
        return
    print(f"Listening for the egg on port {args.port} → {READINGS}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
