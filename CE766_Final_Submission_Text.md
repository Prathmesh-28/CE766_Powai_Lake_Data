# CE 766 Final Project Submission: Robust phosphorus management for Powai Lake, Mumbai

Prathmesh Walimbe (23B0747)

Upload `figures/Figure1_pareto_robustness.png` as Visual 1 and `figures/Figure2_trajectories_prim.png` as Visual 2.

---

## 1. Brief statement of the problem

Powai Lake (water-spread 2.2 km², catchment 6.61 km², 19.13° N, 72.91° E) is an urban reservoir in north-east Mumbai, built in 1891. For decades it received about 18 MLD of untreated sewage, which left it hypereutrophic (total phosphorus, TP, 0.93 ± 0.61 mg/L in 2018–20) and prone to water-hyacinth infestation. By October 2026 the Brihanmumbai Municipal Corporation (BMC) had intercepted 20 sewage outfalls. A new 8 MLD sewage treatment plant (STP) will return treated effluent to the lake from mid-2027.

The project asks two questions. Will this plan bring the lake below the hypereutrophic limit (TP < 0.1 mg/L)? If not, which mix of effluent treatment, sewer-leakage control and hyacinth harvesting does so robustly and at least cost, given that key lake processes are deeply uncertain? It is a real-lake version of the course Lake Problem (Carpenter et al., 1999), in which phosphorus recycled from the sediments can keep a lake eutrophic after external loads are cut. Rainfall is analysed for 2001–2025, and policies are simulated monthly for January 2028 – December 2037. Stakeholders: BMC (lake owner and STP operator), the Maharashtra Pollution Control Board (discharge standards), IIT Bombay, Powai residents and the lake ecosystem.

Changes since the preliminary submission:
- The annual time step became monthly, as water stays in the lake for only about half a year.
- The abstract load decision was replaced by three explicit levers.
- Residual leakage, rainfall non-stationarity and sediment recycling were added as deep uncertainties.

## 2. Data

- **Rainfall:** IMD 0.25° daily gridded rainfall (Pai et al., 2014), 2001–2025, bilinearly interpolated to the lake and summed to monthly totals (300 months). The mean is 2,872 mm/yr, 95% of it falls in June–September, and the trend is +40 mm/yr (p = 0.006).
- **Lake and catchment (static):** area 2.2 km², catchment 6.61 km², depth 3–10 m (Lekshmi et al., 2021).
- **Water quality (model check):** TP summary statistics for April 2018 – March 2020, from the lake centre (0.93 ± 0.61 mg/L) and eight periphery stations (0.05–2.78 mg/L) (Lekshmi et al., 2021). Phosphate for November 2016 – October 2017 (Usman et al., 2018).
- **Sewage:** 18 MLD inflow, interception in October 2026 and the 8 MLD STP due in May 2027, from BMC statements in the Free Press Journal (2025–26).
- **Unmeasured parameters and lever costs:** literature or assumed ranges, sampled synthetically (Section 3).

## 3. Methodology

Framework: Many-Objective Robust Decision Making (Hadka et al., 2015).

**R – Relationships.** A monthly box model (Δt = 1/12 yr):

Q(t) = max[P(t)·(C·(A_C − A_L) + A_L) − E·e(t)·A_L, 0] + Q_STP + f·Q_raw

L(t) = Q_STP·TP_eff + f·Q_raw·TP_raw + e_u·(A_C − A_L)·P(t)/P_yr + d·A_L·Δt

Main equation (Vollenweider balance plus Carpenter et al., 1999 recycling; semi-implicit):

X(t+1) = [X(t) + L(t)/V + Δt·r·X(t)^q/(m^q + X(t)^q) − H(t)] / [1 + Q(t)/V + σ·Δt]

where X = lake TP (mg/L); P(t), P_yr = monthly, annual rainfall; C = runoff coefficient; A_C, A_L = catchment, lake area; E·e(t) = monthly evaporation; Q_STP = 8 MLD returned effluent; Q_raw = raw sewage flow; f = f0·(1 − u) = fraction still leaking in; TP_eff, TP_raw = effluent, raw-sewage TP; e_u = urban export coefficient; d = atmospheric deposition; V = A_L·z̄ (z̄ = mean depth); σ = v_s/z̄ = settling rate (v_s = settling velocity); r, m, q = maximum recycling rate, half-saturation TP, steepness; H(t) = min(H·30.4·p_h/V, 0.5·X) = TP removed by harvest (p_h = g P per tonne).

**L – Levers:** effluent standard TP_eff 0.1–5 mg/L (5 = secondary treatment); leakage intercepted u 0–95%; hyacinth harvest H 0–50 t/day. Indicative cost (Rs crore/yr) = 0.4·ln(5/TP_eff) + 0.5·[−ln(1 − u)] + 0.0365·H.

**X – Uncertainties:**
- Baseline: 200 futures (IMD years resampled, preliminary ranges, recycling fixed at r/m = 4 yr⁻¹, m = 0.2 mg/L, q = 2).
- Deep uncertainty: 1,000 Latin Hypercube futures over 14 factors, adding a rainfall multiplier (0.8–1.3), r/m (1–10 yr⁻¹), m (0.1–0.4 mg/L), q (2–4), leakage f0 (0–20%), v_s (5–15 m/yr) and initial TP (0.5–1.5 mg/L).

**M – Measures:** minimise cost; minimise mean TP over 2028–37; maximise reliability (share of months with TP < 0.1 mg/L, OECD hypereutrophic limit). Robustness = share of the 1,000 futures with mean TP < 0.1 mg/L in 2033–37.

**Steps:** NSGA-II (pymoo; population 100, 120 generations) → re-evaluation → compromise = cheapest policy with ≥ 90% of the best robustness → PRIM (Friedman & Fisher, 1999) on its failures.

**Deviations from the preliminary plan:**
- Larsen–Mercier retention (annual means only) was replaced by σ; without recycling the model still reproduces preliminary S2 (0.17 vs 0.20 mg/L).
- NPV utility became cost and TP measures (no damage valuation exists for Powai).
- Recycling stays a deep uncertainty: only TP summary statistics are public, so it could not be calibrated.

## 4. Results

**Figure 1.** Panel (a) shows the 100 Pareto-optimal policies from NSGA-II as a trade-off between annual cost and mean lake TP (2028–37), coloured by reliability. The status quo returns 8 MLD of secondary effluent to the lake. It keeps mean TP at 0.78 mg/L, with no month below 0.1 mg/L. Upgrading the STP to tertiary treatment (0.75 mg/L) halves this to 0.39 mg/L, but the lake stays hypereutrophic. Moving along the front, the optimiser first tightens the effluent standard (to about 0.25 mg/L by Rs 1.2 crore/yr). It then intercepts the residual leakage (about 80% by Rs 2 crore/yr), and adds hyacinth harvesting last. Mean TP falls below 0.1 mg/L only above about Rs 2.6 crore/yr. Panel (b) re-tests the same policies over 1,000 deeply uncertain futures. Robustness is near zero for cheap policies (tertiary only: 4%), passes 50% at about Rs 2 crore/yr and levels off at 95%. The compromise P88 costs Rs 3.5 crore/yr: an effluent TP of 0.14 mg/L, 89% of the leakage intercepted and 28 t/day of hyacinth harvested. It achieves 86% robustness, a mean TP of 0.058 mg/L and 90% monthly reliability. The most robust policy costs about 40% more for 95%.

**Figure 2.** Panel (a) shows monthly TP (median and 5–95% band, baseline futures). Under the status quo and tertiary-only policies, TP peaks before the monsoon (May), when there is little flushing, and drops after it: from 0.95 to 0.52 mg/L and from 0.43 to 0.25 mg/L. Neither policy ever reaches 0.1 mg/L. Under P88 the median falls below 0.1 mg/L within 11 months and settles near 0.02 mg/L. The seasonal pattern then reverses, peaking in July–August, when urban stormwater becomes the main source. Panel (b) shows the 143 futures in which P88 fails. Failures cluster where sediment recycling is strong (r/m > 6.6 yr⁻¹) and settling is weak (σ < 2.5 yr⁻¹). This PRIM box contains 73% of all failures, and 81% of the futures inside it fail. 97% of failures lie above the hysteresis threshold of about 6 yr⁻¹ found in the preliminary report; below it, P88 fails in only 0.7% of futures. Leakage and sewage TP barely matter once P88 is in place.

## 5. Discussion

Three findings hold across the modelling choices.
- **No single lever is enough.** The strictest effluent standard alone (0.1 mg/L) gives only 15% robustness. Intercepting 95% of the leakage while returning secondary effluent gives 0%, because 8 MLD at 5 mg/L still carries about 15 t P/yr. Both point sources must be cut; harvesting then adds the last margin.
- **Once both are cut, the lake responds fast**, because its residence time is about 0.6 years. P88's unreliable months fall almost entirely in its first year.
- **Failure comes from internal loading.** The baseline optimisation (r/m = 4 yr⁻¹) never encountered this process.

How the results depend on the choices:
- The cost functions are indicative. Different unit costs would shift policies along the front, but would not remove the need to control both point sources.
- A stricter target (the eutrophic limit, 0.035 mg/L) lowers P88's robustness only from 86% to 83%.
- The monthly step matters. The annual model (b ≈ 0.98) averaged away the pre-monsoon peak. Under P88, the seasonal reversal points to stormwater as the next load to manage.
- The model over-predicts TP before diversion (median 1.40 vs observed 0.93 ± 0.61 mg/L, which lies inside the 5–95% band). The results are therefore, if anything, conservative.

Implications: returning secondary effluent will not restore Powai Lake. BMC should design the STP for tertiary phosphorus removal (about 0.15–0.3 mg/L) and audit the sewer network to close the remaining leaks. Because failure depends on sediment recycling, management should be adaptive. TP should be monitored monthly once the STP starts. If TP is still above 0.1 mg/L after two monsoons, strong internal loading is likely, and that should trigger in-lake measures such as dredging or phosphorus inactivation (not modelled).

The results cannot yet be used directly, for four reasons:
- The model is one fully mixed box, while TP at the periphery ranged from 0.05 to 2.78 mg/L.
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

**Main references**
1. Carpenter, S. R., Ludwig, D., & Brock, W. A. (1999). Management of eutrophication for lakes subject to potentially irreversible changes. *Ecological Applications*, 9(3), 751–771.
2. Hadka, D., Herman, J., Reed, P., & Keller, K. (2015). An open source framework for many-objective robust decision making. *Environmental Modelling & Software*, 74, 114–129.
3. Lekshmi, B., et al. (2021). Science & technology agenda for blue-green spaces inspired by citizen science: Case for rejuvenation of Powai Lake. *Sustainability*, 13(18), 10061. https://doi.org/10.3390/su131810061

**Datasets**
- IMD 0.25° daily gridded rainfall, 2001–2025 (Pai, D. S., et al. (2014), *Mausam*, 65(1), 1–18): https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html
- Lake TP, 2018–20 (Lekshmi et al., 2021); phosphate, 2016–17 (Usman, A., et al. (2018), *Int. J. Curr. Microbiol. App. Sci.*, 7(4), 520–533).
- BMC sewage diversion and 8 MLD STP: *Free Press Journal*, 26 Nov 2025 and 30 Sep 2026.

**Methods cited in the text:** NSGA-II (Deb et al., 2002, *IEEE Trans. Evol. Comput.*, 6(2), 182–197); pymoo (Blank & Deb, 2020, *IEEE Access*, 8, 89497–89509); PRIM (Friedman & Fisher, 1999, *Statistics and Computing*, 9, 123–143); trophic limits (OECD, 1982).

**Repository:** https://github.com/Prathmesh-28/CE766_Powai_Lake_Data. Inputs are in `data/`, scripts in `code/` and outputs in `results/` and `figures/`. The README explains how to rerun everything.
