# 🥚 EggCycle: egg-shaped home food-waste digester

**Pitch:** Put your food scraps in the egg. Microbes turn them into biomethane, which powers a plug.
After a few weeks, what's left becomes soil for your plants. The app shows how much power the egg
has made, how much biomethane is left, and how many days until the soil is ready.

## Why an egg?
Large wastewater plants already use egg-shaped digesters. The shape has no dead corners where
sludge settles, it mixes well, gas collects at the top, and the curved shell handles pressure well.

## How it works
```
 food scraps ─► [ inlet + grinder ] ─► ( EGG: anaerobic digestion, ~30–35 °C, 21 days )
                                          │ biogas (≈60% CH₄)          │ digestate
                                          ▼                            ▼
                              [ H₂S filter ] ─► gas bag      [ outlet tap ] ─► cure 14 days ─► soil
                                                   │
                                     [ mini generator / fuel cell ] ─► battery ─► 🔌 plug (USB + AC)
```

## Sensors behind the app (ESP32 → Wi-Fi → dashboard)
| Sensor | What the app shows |
|---|---|
| Load cell under the inlet | Feeding log (kg per day) |
| Distance sensor above the gas bag | Biomethane in the bag |
| Temperature probe | Digestion speed, "days left" |
| Energy meter on the generator output | Power produced |
| Methane sensor next to the egg | Leak alarm + automatic gas shut-off |

Firmware, wiring and parts list: [hardware/README.md](../hardware/README.md).
3D model: [figures/eggcycle-3d.html](../figures/eggcycle-3d.html) (interactive) and
[hardware/eggcycle.scad](../hardware/eggcycle.scad) (printable).
With no hardware, `python -m climate.ingest --fake` generates sensor data for the demo.

## Realistic numbers (state these honestly in the pitch)
- 1 kg of food waste releases about **100 L of methane**, which is roughly **0.25 kWh** at the plug
  with a small generator (~25% efficient).
- A household making ~1 kg of scraps a day gets **~0.25 kWh/day**. That's enough for phone
  charging, LED lights and a Wi-Fi router, but not a fridge or air conditioner.
- The bigger win is climate: food waste in landfill releases methane, and the egg captures and
  uses it instead. It also replaces store-bought fertiliser.
- An alternative pitch: use the gas directly for a cooking burner, which is about 2–3× more useful
  energy than turning it into electricity.

## Safety
Methane is flammable and H₂S is toxic. The design needs a pressure-relief valve and flare,
a flame arrestor, an H₂S scrubber (iron sponge), a gas leak alarm, and an outdoor or ventilated location.
