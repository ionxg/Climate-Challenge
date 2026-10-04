import json
import threading
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer

import pytest

from climate import ingest


def test_append_load_and_feed_log(tmp_path):
    path = tmp_path / "egg.csv"
    ingest.append_reading({"time": "2026-01-01T08:00", "temp_c": 31, "fed_kg": 0.8}, path)
    ingest.append_reading({"time": "2026-01-01T19:00", "temp_c": "30.5", "fed_kg": 0.4}, path)
    ingest.append_reading({"time": "2026-01-02T19:00", "temp_c": 30, "fed_kg": 0}, path)
    readings = ingest.load_readings(path)
    assert len(readings) == 3
    log = ingest.feed_log(readings)
    assert log["date"].tolist() == [date(2026, 1, 1)]
    assert log["kg"].tolist() == pytest.approx([1.2])


def test_rejects_non_numeric(tmp_path):
    with pytest.raises(ValueError, match="temp_c"):
        ingest.append_reading({"temp_c": "hot"}, tmp_path / "egg.csv")


def test_fake_readings_match_demo():
    fake = ingest.fake_readings(date(2026, 3, 1), days=10)
    assert fake["gen_kwh"].is_monotonic_increasing
    assert fake["bag_pct"].max() <= 100
    assert ingest.feed_log(fake)["kg"].sum() > 0


def test_http_post(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "READINGS", tmp_path / "egg.csv")
    monkeypatch.setattr(ingest, "EGG_API_KEY", "secret")
    monkeypatch.setattr(ingest.append_reading, "__defaults__", (tmp_path / "egg.csv",))
    server = ThreadingHTTPServer(("127.0.0.1", 0), ingest.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/readings"

    def post(key):
        req = urllib.request.Request(
            url, json.dumps({"temp_c": 30}).encode(), headers={"X-Egg-Key": key}
        )
        try:
            return urllib.request.urlopen(req).status
        except urllib.error.HTTPError as err:
            return err.code

    assert post("wrong") == 401
    assert post("secret") == 200
    server.shutdown()
    assert len(ingest.load_readings(tmp_path / "egg.csv")) == 1


def test_offline_sensor_is_stored_as_missing(tmp_path):
    row = ingest.append_reading({"temp_c": None, "bag_pct": 40}, tmp_path / "egg.csv")
    assert row["temp_c"] != row["temp_c"]  # NaN
    assert row["bag_pct"] == 40
