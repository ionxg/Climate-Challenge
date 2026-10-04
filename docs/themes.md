# Hackathon tracks

Each track has a dashboard page in `app/pages/` and functions in `src/climate/process.py`.
Pick one track to go deep on and use the others as supporting context.

## ⚡ 1. Electrification
- **Questions:** How clean is the grid? Which homes or vehicles to electrify first? When does the grid peak?
- **Data in repo:** OWID energy (`*_share_elec`, `per_capita_electricity`)
- **More data:** [Ember](https://ember-energy.org/data/) (monthly grid data), [EECA](https://www.eeca.govt.nz/insights/) (NZ), [Electricity Authority EMI](https://www.emi.ea.govt.nz/) (NZ)
- **Ideas:** heat-pump savings calculator, EV charging-time optimiser, home electrification planner

## 🗑️ 2. Zero Waste & Methane Reduction
- **Questions:** Where does methane come from? How much waste goes to landfill vs recycling/compost?
- **Data in repo:** OWID CO₂ (`methane`, `methane_per_capita`, `flaring_co2`)
- **More data:** [World Bank What a Waste 2.0](https://datacatalog.worldbank.org/search/dataset/0039597), [Climate TRACE](https://climatetrace.org/) (landfill/methane sites), [Global Methane Tracker (IEA)](https://www.iea.org/data-and-statistics/data-tools/methane-tracker), local council waste stats
- **Ideas:** food-waste tracker, home or community biogas digester, landfill-methane hotspot map

## 🏙️ 3. Resilient Cities & Buildings
- **Questions:** Are heatwaves and heavy rain getting more frequent? Which areas or buildings are most exposed?
- **Data in repo:** Open-Meteo daily weather per city (`yearly_extremes`)
- **More data:** [Open-Meteo flood API](https://open-meteo.com/en/docs/flood-api), [NIWA](https://niwa.co.nz/climate-and-weather), council hazard maps, [OpenStreetMap buildings](https://www.openstreetmap.org/)
- **Ideas:** urban heat-island map, flood early-warning bot, building retrofit priority score

## 🏭 4. Green Industrialization
- **Questions:** Which industries emit most? Is GDP growing while emissions fall (decoupling)?
- **Data in repo:** OWID CO₂ (`coal_co2`, `oil_co2`, `gas_co2`, `cement_co2`, `co2_per_gdp`)
- **More data:** [Climate TRACE](https://climatetrace.org/) (facility level), [EDGAR](https://edgar.jrc.ec.europa.eu/), [NZ ETS](https://www.epa.govt.nz/industry-areas/emissions-trading-scheme/)
- **Ideas:** supply-chain carbon calculator, industrial heat electrification matcher, circular-material marketplace

## 📣 5. Awareness Across All Areas
- **Questions:** How do you turn the data from tracks 1–4 into something people act on?
- **Data in repo:** all of the above (latest-value facts on the Awareness page)
- **Ideas:** personal carbon-footprint quiz, shareable infographics, school campaign kit, local climate-risk guide

## Judging-friendly checklist
- [ ] One clear user and problem
- [ ] One number that shows the scale
- [ ] Working demo (dashboard page)
- [ ] Estimated impact (t CO₂e, $, or people)
