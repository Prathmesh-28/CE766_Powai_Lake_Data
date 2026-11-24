# Powai Lake – Lake Problem reformulation (CE 766, Autumn 2026)

**Project:** Reformulating the Lake Problem for Powai Lake, Mumbai
**Student:** Prathmesh Walimbe (23B0747) · CE 766 Watershed Management, IIT Bombay
**Stage:** Final submission (November 2026)

As of October 2026, BMC has stopped untreated sewage (about 18 MLD) from entering Powai Lake, and a new 8 MLD STP is due to return treated effluent to the lake from mid-2027. In this project I ask two questions:
- Does this plan bring the lake out of hypereutrophy (total phosphorus, TP, below 0.1 mg/L)?
- If not, which mix of effluent treatment, sewer-leakage control and hyacinth harvesting does so robustly and at least cost?

I answer them with a monthly version of the course Lake Problem, many-objective optimisation (NSGA-II), 1,000 deep-uncertainty futures and PRIM scenario discovery.

## Submission files

| File | What it is |
|---|---|
| [`CE766_Final_Submission_PowaiLake.pdf`](CE766_Final_Submission_PowaiLake.pdf) | **Final report** (5 pages): cover page, then problem, data, methodology, results, discussion and references |
| [`CE766_Final_Submission_PowaiLake.docx`](CE766_Final_Submission_PowaiLake.docx) | The same report as an editable Word file |
| [`CE766_Final_Submission_Text.md`](CE766_Final_Submission_Text.md) | The same text as plain Markdown, used to build the PDF and the Word file |
| [`figures/Figure1_pareto_robustness.png`](figures/Figure1_pareto_robustness.png) | **Figure 1:** cost vs lake-TP trade-off (NSGA-II) and robustness of each policy |
| [`figures/Figure2_trajectories_prim.png`](figures/Figure2_trajectories_prim.png) | **Figure 2:** monthly lake TP under three policies, and where the compromise policy fails (PRIM) |
| [`CE766_Prelim_Results_PowaiLake.pdf`](CE766_Prelim_Results_PowaiLake.pdf) | Preliminary report (October 2026) that the final analysis builds on |

## Key results

| Policy | Cost (Rs crore/yr) | Mean TP 2028–37 (mg/L) | Months with TP < 0.1 | Robustness (1,000 futures) |
|---|---|---|---|---|
| Status quo (secondary STP, 5 mg/L) | 0 | 0.78 | 0% | 0% |
| Tertiary STP only (0.75 mg/L) | 0.76 | 0.39 | 1% | 4% |
| Effluent standard only (0.1 mg/L) | 1.57 | 0.31 | 12% | 15% |
| Leakage interception only (95%) | 1.50 | 0.65 | 0% | 0% |
| **Compromise P88** (0.14 mg/L, 89% interception, 28 t/day harvest) | **3.51** | **0.058** | **90%** | **86%** |
| Most robust P100 | 4.89 | 0.044 | 93% | 95% |

- **No single lever is enough.** Both point sources (effluent and leaking sewage) must be cut, and harvesting adds the last margin.
- **P88 fails mainly when sediment recycling is strong and settling is weak:** r/m > 6.6 yr⁻¹ and σ < 2.5 yr⁻¹. This PRIM box covers 73% of failures, with 81% density. It lies close to the hysteresis threshold (r/m ≈ 6 yr⁻¹) found in my preliminary report.
- **Costs are indicative assumptions.** I define the cost function and all parameter ranges at the top of `code/final_analysis.py`.

## Method (final stage)

1. **Monthly box model** (Δt = 1/12 yr), a Vollenweider mass balance plus Carpenter et al. (1999) sediment recycling:
   `X(t+1) = [X(t) + L(t)/V + Δt·r·X(t)^q/(m^q + X(t)^q) − H(t)] / [1 + Q(t)/V + σ·Δt]`
   - Q(t) is the monthly outflow from IMD rainfall.
   - L(t) is the phosphorus load from STP effluent, residual sewage leakage, urban runoff and deposition.
   - σ = v_s/z̄ is settling.
   - H(t) is phosphorus removed by hyacinth harvest.
2. **Levers:**
   - STP effluent TP standard (0.1–5 mg/L)
   - share of residual leakage intercepted (0–95%)
   - hyacinth harvest (0–50 t/day)
3. **NSGA-II** (pymoo; population 100, 120 generations) over 200 baseline futures, with three objectives:
   - minimise cost
   - minimise mean TP
   - maximise reliability (share of months with TP < 0.1 mg/L)
4. **Robustness:** I re-evaluate the Pareto policies over 1,000 Latin Hypercube futures (14 uncertain factors, including the recycling parameters r/m, m and q, leakage, and a rainfall multiplier). Robustness is the share of futures with mean TP < 0.1 mg/L in 2033–37.
5. **PRIM** (Friedman & Fisher, 1999) on the futures in which the compromise policy fails.

**Model checks** (`results/model_checks.csv`):
- Before diversion, my model gives 1.40 mg/L (0.68–2.29), against an observed 0.93 ± 0.61 mg/L.
- Without recycling, it reproduces preliminary scenario S2: 0.17 vs 0.20 mg/L.

## Repository structure

| Path | Stage | Contents |
|---|---|---|
| `data/imd_rainfall_powai_monthly_2001_2025.csv` | both | Monthly and annual rainfall at Powai (mm), 2001–2025, from IMD 0.25° daily gridded rainfall bilinearly interpolated to 19.13° N, 72.91° E; also the largest daily total each year |
| `data/lake_catchment_parameters.csv` | both | Lake area, catchment area and depths, with sources |
| `data/water_quality_observations.csv` | both | Observed total phosphorus (2018–20) and phosphate (2016–17), with sources |
| `data/sewage_and_interventions.csv` | both | Sewage inflow and the BMC diversion / STP plan, with sources |
| `data/montecarlo_input_ranges.csv` | preliminary | Ranges and distributions of the uncertain inputs used in the preliminary Monte Carlo |
| `code/final_analysis.py` | final | Monthly model, NSGA-II, deep-uncertainty re-evaluation, PRIM, model checks |
| `code/final_figures.py` | final | Figures 1–2 of the final report |
| `code/make_pdf.py` | final | Builds the final PDF from `CE766_Final_Submission_Text.md` and the figures |
| `code/make_docx.js` | final | Builds the Word version (`.docx`) from the same text and figures |
| `code/analysis.py`, `code/figures.py` | preliminary | Annual mass balance, Monte Carlo scenarios, preliminary figures |
| `code/extract_imd_powai.py` | both | Downloads the IMD binary files and extracts the Powai rainfall series |
| `results/policies_pareto_and_robustness.csv` | final | The 100 Pareto policies and 4 reference policies, with levers, cost, mean TP, reliability and robustness |
| `results/du_futures_outcomes.csv` | final | The 1,000 deep-uncertainty futures, end-state TP for three policies, and the failure flag for the compromise |
| `results/monthly_TP_trajectories_baseline.csv` | final | Monthly TP percentiles (5/50/95) for the compromise, tertiary-only and status-quo policies |
| `results/prim_trajectory.csv`, `results/failure_factor_shift_compromise.csv` | final | PRIM peeling trajectory, and the shift in each factor between failed and successful futures |
| `results/model_checks.csv`, `results/final_summary.json` | final | Model checks against observations; headline numbers |
| `results/scenario_results.csv`, `results/montecarlo_lake_TP_samples.csv` | preliminary | Steady-state scenario results (S0–S3) and all 20,000 Monte Carlo samples |
| `results/sensitivity_spearman_S2.csv`, `results/leakage_effect_S2.csv`, `results/lake_regime_thresholds.csv`, `results/summary.json` | preliminary | Sensitivity, leakage effect, Carpenter-model thresholds, rainfall statistics |
| `figures/Figure1_pareto_robustness.png`, `figures/Figure2_trajectories_prim.png` | final | Figures 1–2 of the final report |
| `figures/iitb_logo.png`, `figures/iitb_logo_watermark.png` | final | IIT Bombay logo for the page header, and the faded copy behind the cover page |
| `figures/fig1_rainfall.png`, `fig2_scenarios.png`, `fig3_leakage.png`, `methodology_and_results.png` | preliminary | Figures of the preliminary report |

## How to reproduce

I run everything with Python 3.9, and Node.js for the Word file. From the repository root:

```bash
pip install -r requirements.txt

# final stage (about 15 s in total)
python code/final_analysis.py      # writes the final results/ files
python code/final_figures.py       # writes figures/Figure1_*.png and figures/Figure2_*.png
python code/make_pdf.py            # writes CE766_Final_Submission_PowaiLake.pdf
npm install docx                   # once, for the Word file
node code/make_docx.js             # writes CE766_Final_Submission_PowaiLake.docx

# preliminary stage
python code/analysis.py            # writes the preliminary results/ files
python code/figures.py             # writes figures/methodology_and_results.png
python code/extract_imd_powai.py 2001 2025   # optional: re-download IMD data and rebuild the rainfall series
```

All random draws use fixed seeds, so the results are reproducible. `extract_imd_powai.py` downloads the yearly IMD binary files from imdpune.gov.in (about 25 MB per year) and keeps only the Powai point.

## Preliminary stage (October 2026)

My preliminary stage uses an annual steady-state model:
- water balance
- Vollenweider load
- Larsen–Mercier retention R = 1/(1 + √τ)
- TP = (L/Q)(1 − R)

I run it as a 20,000-sample Monte Carlo for four diversion scenarios:

| Scenario | Lake TP, median (5–95%) | Chance TP > 0.1 mg/L |
|---|---|---|
| S0 Before diversion | 1.21 mg/L (0.70–2.03) | 100% |
| S1 Diversion + secondary effluent | 0.55 mg/L (0.31–0.96) | 100% |
| S2 Diversion + tertiary effluent | 0.20 mg/L (0.09–0.41) | 92% |
| S3 Diversion, no effluent return | 0.18 mg/L (0.04–0.46) | 76% |

In my preliminary report I proposed the following changes, and my final stage implements all of them:
- the monthly time step
- explicit levers
- NSGA-II
- 1,000 LHS futures
- PRIM

## Data sources

- IMD 0.25° daily gridded rainfall: Pai, D. S., et al. (2014), *Mausam* 65(1), 1–18. https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html
- Lekshmi, B., et al. (2021). Science & technology agenda for blue-green spaces inspired by citizen science: Case for rejuvenation of Powai Lake. *Sustainability* 13(18), 10061. https://doi.org/10.3390/su131810061
- Usman, A., et al. (2018). Water quality index as a tool for assessment of status of an urban lake of Mumbai. *Int. J. Curr. Microbiol. App. Sci.* 7(4), 520–533.
- Free Press Journal (26 Nov 2025; 30 Sep 2026): reports on BMC's Powai Lake sewage diversion and the 8 MLD STP.
- IIT Bombay logo (cover page and page header): https://en.wikipedia.org/wiki/File:Indian_Institute_of_Technology_Bombay_Logo.svg
- Methods: Carpenter et al. (1999); Hadka et al. (2015); Deb et al. (2002); Blank & Deb (2020); Friedman & Fisher (1999); Metcalf & Eddy (2003); Reckhow et al. (1980); Larsen & Mercier (1976); OECD (1982).

For unmeasured inputs (runoff coefficient, evaporation, leakage, effluent TP, settling velocity, recycling parameters) and the lever costs, I use assumed or literature-based ranges. I document them in `data/montecarlo_input_ranges.csv` (preliminary) and at the top of `code/final_analysis.py` (final).
