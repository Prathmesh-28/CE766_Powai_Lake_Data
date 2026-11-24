# CE 766 Final Project Submission: Robust phosphorus management for Powai Lake, Mumbai

Prathmesh Walimbe (23B0747)

Upload `figures/Figure1_pareto_robustness.png` as Visual 1 and `figures/Figure2_trajectories_prim.png` as Visual 2.

---

## 1. Brief statement of the problem

Powai Lake (water-spread 2.2 km², catchment 6.61 km², 19.13° N, 72.91° E) is an urban reservoir in north-east Mumbai. Decades of untreated sewage (about 18 MLD) have left it hypereutrophic (total phosphorus, TP, 0.93 ± 0.61 mg/L in 2018–20) and prone to water-hyacinth infestation. As of October 2026, the Brihanmumbai Municipal Corporation (BMC) has intercepted 20 sewage outfalls, and a new 8 MLD sewage treatment plant (STP) starts returning treated effluent to the lake in mid-2027.

I ask whether this plan brings the lake below the hypereutrophic limit (TP < 0.1 mg/L) and, if not, which mix of effluent treatment, sewer-leakage control and hyacinth harvesting does so robustly and at least cost, given deeply uncertain lake processes. This is a live watershed-management decision: BMC's choices of STP standard and sewer works control the catchment's phosphorus load to the lake. I adapt the course Lake Problem (Carpenter et al., 1999), where sediment phosphorus recycling can keep a lake eutrophic after loads are cut. I analyse rainfall for 2001–2025 and simulate policies monthly for January 2028 – December 2037. Stakeholders: BMC (lake owner, STP operator), the Maharashtra Pollution Control Board (discharge standards), IIT Bombay, Powai residents and the lake ecosystem.

Changes since my preliminary submission:
- I switch from annual to monthly steps, as water stays in the lake only about half a year.
- I replace the abstract load decision with three explicit levers.
- I add residual leakage, rainfall non-stationarity and sediment recycling as deep uncertainties.

## 2. Data

- **Rainfall:** IMD 0.25° daily gridded rainfall (Pai et al., 2014), 2001–2025, bilinearly interpolated to the lake and summed monthly; mean 2,872 mm/yr, 95% in June–September, trend +40 mm/yr.
- **Lake and catchment:** static, lake-scale values: area 2.2 km², catchment 6.61 km², depth 3–10 m (Lekshmi et al., 2021).
- **Water quality:** TP at one centre and eight periphery stations, April 2018 – March 2020, as period statistics (centre 0.93 ± 0.61 mg/L; periphery 0.05–2.78 mg/L) (Lekshmi et al., 2021); phosphate, November 2016 – October 2017 (Usman et al., 2018).
- **Sewage:** catchment totals: 18 MLD inflow, outfall interception in October 2026, 8 MLD STP due May 2027 (BMC statements, Free Press Journal, 2025–26).
- **Synthetic inputs:** unmeasured parameters and lever costs come from literature or assumptions (Section 3); I sample parameters randomly or by Latin Hypercube and resample whole IMD years for rainfall.

## 3. Methodology

**R – Relationships** (monthly, Δt = 1/12 yr):

Q(t) = max[P(t)·(C·(A_C − A_L) + A_L) − E·e(t)·A_L, 0] + Q_STP + f·Q_raw

L(t) = Q_STP·TP_eff + f·Q_raw·TP_raw + e_u·(A_C − A_L)·P(t)/P_yr + d·A_L·Δt

Main equation (Vollenweider, 1976; Carpenter et al., 1999):

X(t+1) = [X(t) + L(t)/V + Δt·r·X(t)^q/(m^q + X(t)^q) − H(t)] / [1 + Q(t)/V + σ·Δt]

where Q(t), L(t): monthly outflow, P load; X: lake TP (mg/L); P(t), P_yr: monthly, annual rainfall; A_C, A_L: catchment, lake area; e(t): monthly share of E; Q_STP: 8 MLD returned effluent; f = f0·(1 − u): leaking sewage fraction; d: atmospheric deposition (0.3 kg/ha/yr); V = A_L·z̄: lake volume; σ = v_s/z̄: settling rate; r, m, q: maximum recycling rate, half-saturation TP, steepness; H(t) = min(H·30.4·p_h/V, 0.5·X): TP removed by harvest (30.4 days/month). Others: see L and X.

**L – Levers:** effluent TP standard TP_eff 0.1–5 mg/L (5 = secondary); leakage interception u 0–95%; hyacinth harvest H 0–50 t/day. Indicative cost (Rs crore/yr) = 0.4·ln(5/TP_eff) + 0.5·[−ln(1 − u)] + 0.0365·H.

**X – Uncertainties** (uniform ranges): runoff coefficient C 0.4–0.8; evaporation E 1.2–1.8 m/yr; mean depth z̄ 2.5–5 m; raw sewage Q_raw 15–21 MLD, TP_raw 4–12 mg/L (preliminary triangular); leakage f0 0–20% (preliminary 0–15%); export coefficient e_u 0.5–2.5 kg/ha/yr; settling velocity v_s 5–15 m/yr; hyacinth P p_h 150–300 g/t; initial TP 0.5–1.5 mg/L; rainfall multiplier 0.8–1.3; recycling r/m 1–10 yr⁻¹, m 0.1–0.4 mg/L, q 2–4. Baseline: 200 random futures (IMD years resampled; multiplier 1; r/m = 4 yr⁻¹, m = 0.2 mg/L, q = 2). Deep uncertainty: 1,000 Latin Hypercube futures over all 14 factors.

**M – Measures:** minimise cost; minimise mean TP (2028–37); maximise reliability (months with TP < 0.1 mg/L, OECD hypereutrophic limit). Robustness = share of futures with 2033–37 mean TP < 0.1 mg/L.

**Steps** (MORDM; Hadka et al., 2015): NSGA-II (pymoo; population 100, 120 generations) → re-evaluation → compromise = cheapest policy with ≥ 90% of best robustness → PRIM (Friedman & Fisher, 1999) on its failures.

**Deviations from my preliminary plan:**
- I replace Larsen–Mercier retention (annual-only) with σ; without recycling, my model matches preliminary S2 (0.17 vs 0.20 mg/L).
- I replace NPV utility with cost and TP measures (Powai has no damage valuation).
- I cannot calibrate recycling (only TP summary statistics are available).

## 4. Results

**Figure 1.** Panel (a) shows the 100 Pareto-optimal policies from NSGA-II as a trade-off between annual cost and mean lake TP (2028–37), coloured by reliability. The status quo returns 8 MLD of secondary effluent to the lake. It keeps mean TP at 0.78 mg/L, with no month below 0.1 mg/L. Upgrading the STP to tertiary treatment (0.75 mg/L) halves this to 0.39 mg/L, but the lake stays hypereutrophic. Moving along the front, the optimiser first tightens the effluent standard (to about 0.25 mg/L by Rs 1.2 crore/yr). It then intercepts the residual leakage (about 80% by Rs 2 crore/yr), and adds hyacinth harvesting last. Mean TP falls below 0.1 mg/L only above about Rs 2.6 crore/yr. In panel (b) I re-test the same policies over 1,000 deeply uncertain futures. Robustness is near zero for cheap policies (tertiary only: 4%), passes 50% at about Rs 2 crore/yr and levels off at 95%. My compromise, P88, costs Rs 3.5 crore/yr: an effluent TP of 0.14 mg/L, 89% of the leakage intercepted and 28 t/day of hyacinth harvested. It achieves 86% robustness, a mean TP of 0.058 mg/L and 90% monthly reliability. The most robust policy costs about 40% more for 95%.

**Figure 2.** Panel (a) shows monthly TP (median and 5–95% band, baseline futures). Under the status quo and tertiary-only policies, TP peaks before the monsoon (May), when there is little flushing, and drops after it: from 0.95 to 0.52 mg/L and from 0.43 to 0.25 mg/L. Neither policy ever reaches 0.1 mg/L. Under P88 the median falls below 0.1 mg/L within 11 months and settles near 0.02 mg/L. The seasonal pattern then reverses, peaking in July–August, when urban stormwater becomes the main source. Panel (b) shows the 143 futures in which P88 fails. Failures cluster where sediment recycling is strong (r/m > 6.6 yr⁻¹) and settling is weak (σ < 2.5 yr⁻¹). This PRIM box contains 73% of all failures, and 81% of the futures inside it fail. 97% of failures lie above the hysteresis threshold of about 6 yr⁻¹ found in my preliminary report; below it, P88 fails in only 0.7% of futures. Leakage and sewage TP barely matter once P88 is in place.

## 5. Discussion

Three findings hold across my modelling choices.
- **No single lever is enough.** The strictest effluent standard alone (0.1 mg/L) gives only 15% robustness. Intercepting 95% of the leakage while returning secondary effluent gives 0%, because 8 MLD at 5 mg/L still carries about 15 t P/yr. Both point sources must be cut; harvesting then adds the last margin.
- **Once both are cut, the lake responds fast** (residence time about 0.6 years): P88's unreliable months fall almost entirely in its first year.
- **Failure comes from internal loading**, which my baseline optimisation (r/m = 4 yr⁻¹) never tests.

How the results depend on the choices:
- **Model:** the monthly step matters; my annual model (b ≈ 0.98) averages away the pre-monsoon peak, and under P88 the seasonal reversal points to stormwater as the next load. My model over-predicts pre-diversion TP (median 1.40 vs observed 0.93 ± 0.61 mg/L, inside the 5–95% band), so my results are conservative.
- **Input data:** outcomes depend far more on unmeasured recycling and settling than on rainfall or sewage inputs (PRIM, Figure 2b), so lake measurements matter most.
- **Objective functions:** the cost functions are indicative; other unit costs shift policies along the front but cannot remove the need to control both point sources. With the stricter eutrophic target (0.035 mg/L), P88's robustness falls only from 86% to 83%.

Implications: returning secondary effluent does not restore Powai Lake. I recommend that BMC design the STP for tertiary phosphorus removal (about 0.15–0.3 mg/L) and audit the sewer network to close the remaining leaks. Because failure depends on sediment recycling, management should be adaptive: monitor TP monthly once the STP starts and, if it is still above 0.1 mg/L after two monsoons, trigger in-lake measures such as dredging or phosphorus inactivation (not modelled).

My results cannot yet be used directly, for four reasons:
- My model is one fully mixed box, while periphery TP spans 0.05–2.78 mg/L.
- The volume rests on an assumed depth.
- The costs are indicative.
- Recycling has not been measured.

The additional data and analysis needed are:
- A bathymetric survey.
- Monthly TP, dissolved oxygen and chlorophyll after diversion.
- Sediment-core phosphorus-release tests to constrain r/m.
- Measured STP effluent quality and leakage flows.
- BMC cost data.
- CMIP6 rainfall scenarios.
- A 2-D water-quality model to resolve spatial hotspots.

## 6. References and Data/Code Repository

**Main references and datasets**
1. Carpenter, S. R., Ludwig, D., & Brock, W. A. (1999). Management of eutrophication for lakes subject to potentially irreversible changes. *Ecological Applications*, 9(3), 751–771. (Lake model and main equation.)
2. Pai, D. S., et al. (2014). Development of a new high spatial resolution (0.25° × 0.25°) long period (1901–2010) daily gridded rainfall data set over India and its comparison with existing data sets over the region. *Mausam*, 65(1), 1–18. Data: https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html
3. Lekshmi, B., et al. (2021). Science & technology agenda for blue-green spaces inspired by citizen science: Case for rejuvenation of Powai Lake. *Sustainability*, 13(18), 10061. https://doi.org/10.3390/su131810061 (Lake morphometry and TP data.)

**Other sources used:** Hadka et al. (2015), *Environ. Model. Softw.* 74, 114–129; Vollenweider (1976), *Mem. Ist. Ital. Idrobiol.* 33, 53–83; Deb et al. (2002), *IEEE Trans. Evol. Comput.* 6(2), 182–197; Blank & Deb (2020), *IEEE Access* 8, 89497–89509; Friedman & Fisher (1999), *Stat. Comput.* 9, 123–143; OECD (1982); Usman et al. (2018), *Int. J. Curr. Microbiol. App. Sci.* 7(4), 520–533; Free Press Journal (26 Nov 2025; 30 Sep 2026).

**Data and code repository:** https://github.com/Prathmesh-28/CE766_Powai_Lake_Data. Inputs are in `data/`, scripts in `code/` and outputs in `results/` and `figures/`; the README explains how to rerun everything.
