# Feed the Egg hardware

| File | What it is |
|---|---|
| `esp32/eggcycle/eggcycle.ino` | ESP32 firmware: reads sensors, closes the gas valve on a leak, sends readings to the app |
| `esp32/eggcycle/secrets.example.h` | Wi-Fi and server settings template (copy to `secrets.h`) |
| `eggcycle.scad` | Parametric 3D model (OpenSCAD) for a 1:10 printed desk model |
| `../figures/eggcycle-3d.html` | Interactive 3D view for the pitch (open in a browser; try **X-ray**) |

## System
```
 Sensors ──► ESP32 ──Wi-Fi──► laptop: python -m climate.ingest ──► data/raw/egg_readings.csv
                │                                                         │
                └─► relay ─► gas solenoid valve (closes on leak)          ▼
                                                             Feed the Egg app (Streamlit, phone browser)
```

## Sensors and wiring (ESP32 DevKit v1)
| Part | Measures | ESP32 pins | Notes |
|---|---|---|---|
| Load cell 5 kg + HX711 | Food added (under the inlet hopper) | DOUT → GPIO25, SCK → GPIO26, VCC 3.3V | A feed is logged when the hopper is tipped empty |
| DS18B20 waterproof probe | Slurry temperature | DATA → GPIO4, 4.7 kΩ pull-up to 3.3V | Probe goes into the egg through a sealed gland |
| Analog pH probe + board (e.g. DFRobot Gravity pH V2) | Slurry pH: sour = smelly | Signal → GPIO35, VCC 3.3V | Calibrate in pH 4 and pH 7 buffer; clean the probe monthly |
| VL53L0X distance sensor | Gas bag level | SDA → GPIO21, SCL → GPIO22, VCC 3.3V | Mount above the bag; the bag rises as it fills |
| PZEM-004T v3 + CT clamp | Power produced (W, lifetime kWh) | PZEM TX → GPIO16, PZEM RX ← GPIO17, VCC 5V | Clamp on the generator output. Add a level shifter (or 1k/2k divider) on PZEM TX → GPIO16 |
| MQ-4 module | Methane leak | AO → 10 kΩ/20 kΩ divider → GPIO34, VCC 5V | Must be on ADC1 (GPIO32–39) because ADC2 stops working when Wi-Fi is on |
| 5V relay module | Gas valve | IN → GPIO32 | Drives a **normally-closed** 12V biogas solenoid valve |
| Buzzer | Leak alarm | GPIO27 | |
| Push button | Re-open valve after a leak is fixed | GPIO33 → GND | Only works once methane is back below half the alarm level |

Power: 12V battery → buck converter → 5V for the ESP32 (VIN), MQ-4 heater, PZEM and relay.

**Fail-safe design:** the gas valve is normally closed, so it shuts if the ESP32 crashes or loses
power. The firmware latches the leak alarm until a person presses the reset button.

## Parts list (approximate prices, USD)
| Electronics | ~$ | Digester and power | ~$ |
|---|---|---|---|
| ESP32 DevKit v1 | 6 | 200 L HDPE or fibreglass egg shell (insulated) | 80–200 |
| HX711 + 5 kg load cell | 4 | 150 L PVC biogas bag | 30 |
| DS18B20 waterproof probe | 3 | Small biogas generator (500 W–1 kW) | 300–500 |
| pH probe + board | 15–40 | Charcoal filter vent + lid gasket | 15 |
| VL53L0X | 5 | 12V LiFePO4 battery, 50 Ah (~0.6 kWh) | 200 |
| PZEM-004T v3 + CT clamp | 12 | 300 W pure-sine inverter + USB panel | 60 |
| MQ-4 module | 3 | H₂S filter (steel-wool canister) | 10 |
| Relay + 12V NC gas solenoid valve | 22 | Pressure relief valve, flame arrestor | 30 |
| Buzzer, button, buck converter, resistors | 6 | Pipes, ball valves, digestate tap | 40 |

For the hackathon demo you only need the electronics (about $60). Run
`python -m climate.ingest --fake` to show the app without building the digester.

## Getting it running
1. **Arduino IDE:** install the ESP32 board package, then these libraries: HX711 (Bogdan Necula),
   OneWire, DallasTemperature, Adafruit_VL53L0X, PZEM004Tv30, ArduinoJson.
2. Copy `secrets.example.h` to `secrets.h`. Set your Wi-Fi, your laptop's IP (`ipconfig`), and a key.
3. On the laptop, put the same key in `.env` as `EGG_API_KEY=...`, then run:
   ```powershell
   $env:PYTHONPATH = "src"; python -m climate.ingest
   ```
   Allow Python through Windows Firewall on private networks when asked.
4. Flash the ESP32 and open Serial Monitor at 115200 baud. You should see `POST 200 {...}` every minute.
5. Open the app (`streamlit run app/main.py` → **Feed the Egg**). It switches to **Live data** automatically.

## Calibration (constants at the top of the `.ino`)
- `SCALE_FACTOR`: put a known weight (e.g. 1 kg of water) in the hopper and adjust until it reads 1.00.
- `BAG_EMPTY_MM` / `BAG_FULL_MM`: note the distance shown with the bag flat and with it full.
- `PH7_MV` / `PH4_MV`: dip the pH probe in pH 7 and pH 4 buffer solution and note the millivolts.
- `MQ4_R0`: run the MQ-4 for 48 hours in clean air, then compute R0. MQ sensors are only indicative,
  so also fit a certified methane alarm.

## Status
The firmware has not been compiled yet and the OpenSCAD model has not been rendered yet. Test each sensor on its own before wiring everything together.
