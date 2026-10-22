# Powai Lake – Lake Problem reformulation (CE 766, Fall 2026)

**Project:** Reformulating the Lake Problem for Powai Lake, Mumbai
**Student:** Prathmesh Walimbe (23B0747) · CE 766 Watershed Management, IIT Bombay
**Stage:** Data and preliminary results (October 2026)

This repository holds the data, code and results behind the preliminary submission.

## Folder structure

| Folder / file | Contents |
|---|---|
| `data/imd_rainfall_powai_monthly_2001_2025.csv` | Monthly and annual rainfall at Powai (mm), 2001–2025, from IMD 0.25° daily gridded rainfall, bilinearly interpolated to 19.13° N, 72.91° E; also the largest daily total each year |
| `data/lake_catchment_parameters.csv` | Lake area, catchment area and depths, with sources |
| `data/water_quality_observations.csv` | Observed total phosphorus (2018–20) and phosphate (2016–17), with sources |
| `data/sewage_and_interventions.csv` | Sewage inflow and BMC diversion / STP plan, with sources |
| `data/montecarlo_input_ranges.csv` | Ranges and distributions of the uncertain inputs used in the Monte Carlo |
| `results/scenario_results.csv` | Load, outflow, residence time, retention, loss rate and lake TP (median, 5–95%) for each scenario |
| `results/montecarlo_lake_TP_samples.csv` | All 20,000 Monte Carlo lake-TP values for each scenario, with the leakage fraction |
| `results/sensitivity_spearman_S2.csv` | Spearman rank correlation of each input with lake TP (scenario S2) |
| `results/leakage_effect_S2.csv` | Chance of TP < 0.1 mg/L by leakage band (scenario S2) |
| `results/lake_regime_thresholds.csv` | Carpenter-model thresholds *g*max, *f′*max and the recycling strength *r/m* needed for hysteresis / irreversibility |
| `results/summary.json` | Rainfall statistics and other summary values |
| `figures/` | Summary figure (`methodology_and_results.png`) and Figures 1–3 of the report |
| `code/` | Python scripts to reproduce everything |
| `CE766_Prelim_Results_PowaiLake.pdf` | Preliminary report with all formulas, tables and figures |

## Method (summary)

1. Water balance: Q = P·C·(A_C − A_L) + P·A_L − E·A_L + Q_ww
2. Phosphorus load: L = Q_ww·TP_ww + e_u·(A_C − A_L) + d·A_L
3. Residence time and retention: τ = V/Q, R = 1/(1 + √τ) (Larsen–Mercier)
4. Steady-state lake phosphorus: TP = (L/Q)·(1 − R)
5. Loss rate and Lake-Problem parameter: k = 1/[τ(1 − R)], b = 1 − e^(−k)
6. Monte Carlo with N = 20,000 samples over the inputs in `data/montecarlo_input_ranges.csv`, for four scenarios:
   S0 before diversion; S1 diversion + secondary effluent returned; S2 diversion + tertiary effluent returned; S3 diversion with no effluent return.

## Key results

| Scenario | Lake TP, median (5–95%) | Chance TP > 0.1 mg/L |
|---|---|---|
| S0 Before diversion | 1.21 mg/L (0.70–2.03) | 100% |
| S1 Diversion + secondary effluent | 0.55 mg/L (0.31–0.96) | 100% |
| S2 Diversion + tertiary effluent | 0.20 mg/L (0.09–0.41) | 92% |
| S3 Diversion, no effluent return | 0.18 mg/L (0.04–0.46) | 76% |

The observed TP (0.93 ± 0.61 mg/L, 2018–20) lies within the predicted pre-diversion range.

## How to reproduce

```bash
pip install numpy pandas scipy matplotlib requests
python code/analysis.py            # writes results/
python code/figures.py             # writes figures/methodology_and_results.png
python code/extract_imd_powai.py 2001 2025   # optional: re-download IMD data and rebuild the rainfall series
```

`extract_imd_powai.py` downloads the yearly IMD binary files from imdpune.gov.in (about 25 MB per year) and keeps only the Powai point.

## Data sources

- IMD 0.25° daily gridded rainfall: Pai, D. S., et al. (2014), *Mausam* 65(1), 1–18. https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html
- Lekshmi, B., et al. (2021). Case for rejuvenation of Powai Lake. *Sustainability* 13(18), 10061. https://doi.org/10.3390/su131810061
- Usman, A., et al. (2018). Water quality index … urban lake of Mumbai. *Int. J. Curr. Microbiol. App. Sci.* 7(4), 520–533.
- Free Press Journal (26 Nov 2025; 30 Sep 2026): reports on BMC's Powai Lake sewage diversion and 8 MLD STP.
- Metcalf & Eddy (2003); Reckhow et al. (1980); Larsen & Mercier (1976); Carpenter et al. (1999).

Unmeasured inputs (runoff coefficient, evaporation, leakage, effluent TP, mean depth) are assumed ranges, as listed in `data/montecarlo_input_ranges.csv`.
