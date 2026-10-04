# Feed the Egg

> Food waste in landfill makes methane. Feed the Egg captures it and turns it into power, cooking gas and soil, with one shared Egg per street.

**Mobile app:** [try the prototype](https://thing-blend-46702836.figma.site/)

## Quick start (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
$env:PYTHONPATH = "src"; python -m climate.fetch   # download data (skip if data/raw already has CSVs)
streamlit run app/main.py                          # launch dashboard
```

Or in VS Code: **Terminal → Run Task → Setup venv**, then **F5 → Fetch data**, then **F5 → Run dashboard**.

## Tracks

| # | Track | Dashboard page | Starter data |
|---|---|---|---|
| 1 | Electrification | `app/pages/1_Electrification.py` | OWID energy: electricity mix |
| 2 | Zero Waste & Methane | `app/pages/2_Zero_Waste_Methane.py` | OWID CO₂: methane |
| 3 | Resilient Cities & Buildings | `app/pages/3_Resilient_Cities.py` | Open-Meteo: heat and rain extremes |
| 4 | Green Industrialization | `app/pages/4_Green_Industrialization.py` | OWID CO₂: by source, CO₂/GDP |
| 5 | Awareness | `app/pages/5_Awareness.py` | Facts pulled from all of the above |
| 6 | Feed the Egg | `app/pages/6_Feed_the_Egg.py` | Egg sensor readings (`python -m climate.ingest --fake` for demo data) |
| 7 | 3D Model | `app/pages/7_3D_Model.py` | `figures/eggcycle-3d.html` |
| 8 | Mobile App | `app/pages/8_Mobile_App.py` | Published phone prototype |

See [docs/themes.md](docs/themes.md) for questions, extra datasets and project ideas per track.

## Layout

```
data/raw/            downloaded data (gitignored)
data/processed/      cleaned tables (gitignored)
notebooks/           exploration
src/climate/         config.py, fetch.py -> process.py -> (model.py)
app/main.py          Streamlit home page (country KPIs)
app/common.py        shared data loading + sidebar pickers
app/pages/           one page per track
tests/               pytest
docs/                tracks, pitch outline, data sources
figures/             exported charts for slides
```

## Team

-
