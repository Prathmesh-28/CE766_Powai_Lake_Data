"""
CE 766 project - Powai Lake: preliminary analysis.

Annual water balance + Vollenweider-type phosphorus mass balance (Larsen-Mercier retention),
run as a Monte Carlo over uncertain inputs, for four sewage-diversion scenarios.
Also computes rainfall statistics, Spearman sensitivity and Carpenter lake-model regime thresholds.

Run from the repository root:   python code/analysis.py
Inputs : data/*.csv
Outputs: results/*.csv, results/summary.json
"""
import os, json
import numpy as np, pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RES = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
rng = np.random.default_rng(766)
N = 20000

# ---------------- data ----------------
rain = pd.read_csv(os.path.join(DATA, "imd_rainfall_powai_monthly_2001_2025.csv"))
P_obs = rain["annual_mm"].values / 1000.0          # m/yr
A_lake, A_catch = 2.2e6, 6.61e6                    # m2 (Lekshmi et al. 2021)
A_land = A_catch - A_lake

# ---------------- uncertain inputs (see data/montecarlo_input_ranges.csv) ----------------
P     = rng.choice(P_obs, N)                       # annual rainfall (m), resampled from IMD 2001-2025
z     = rng.uniform(2.5, 5.0, N)                   # mean depth (m)
C     = rng.uniform(0.4, 0.8, N)                   # runoff coefficient
E     = rng.uniform(1.2, 1.8, N)                   # lake evaporation (m/yr)
Qs    = rng.uniform(15, 21, N) * 1e3               # raw sewage inflow before diversion (m3/d)
TPs   = rng.triangular(4, 7, 12, N)                # raw sewage TP (mg/L = g/m3)
ecu   = rng.uniform(0.5, 2.5, N)                   # urban TP export coefficient (kg/ha/yr)
dep   = rng.uniform(0.1, 0.5, N)                   # atmospheric TP deposition on lake (kg/ha/yr)
leak  = rng.uniform(0.0, 0.15, N)                  # fraction of raw sewage still reaching lake after diversion
TPsec = rng.uniform(3.0, 6.0, N)                   # secondary STP effluent TP (mg/L)
TPter = rng.uniform(0.5, 1.0, N)                   # tertiary STP effluent TP (mg/L)
Qstp  = 8e3                                        # treated effluent returned (m3/d)

V = A_lake * z
L_nps = (ecu * A_land / 1e4 + dep * A_lake / 1e4) * 1e3   # non-point + atmospheric load (g/yr)

def balance(Q_ww, L_ww):
    """Q = P C (A_C - A_L) + P A_L - E A_L + Q_ww ; tau = V/Q ; R = 1/(1+sqrt(tau)) ; TP = (L/Q)(1-R)."""
    Q = np.maximum(P * A_land * C + P * A_lake - E * A_lake + Q_ww, 1e5)
    tau = V / Q
    R = 1.0 / (1.0 + np.sqrt(tau))
    L = L_ww + L_nps
    TP = L / Q * (1 - R)
    k = (Q / V) / (1 - R)                          # first-order P loss rate (1/yr)
    return dict(Q=Q, tau=tau, R=R, L=L, TP=TP, k=k)

day = 365.0
scen = {
    "S0 Before diversion":               balance(Qs * day, Qs * day * TPs),
    "S1 Diversion + secondary effluent": balance((Qstp + leak * Qs) * day, (Qstp * TPsec + leak * Qs * TPs) * day),
    "S2 Diversion + tertiary effluent":  balance((Qstp + leak * Qs) * day, (Qstp * TPter + leak * Qs * TPs) * day),
    "S3 Diversion, no effluent return":  balance(leak * Qs * day, leak * Qs * TPs * day),
}
pct = lambda x, p: float(np.percentile(x, p))

# ---------------- scenario results ----------------
rows = []
for name, s in scen.items():
    rows.append(dict(scenario=name,
        load_t_per_yr_median=pct(s["L"], 50) / 1e6, load_t_per_yr_p5=pct(s["L"], 5) / 1e6, load_t_per_yr_p95=pct(s["L"], 95) / 1e6,
        outflow_Mm3_per_yr_median=pct(s["Q"], 50) / 1e6,
        residence_time_yr_median=pct(s["tau"], 50), residence_time_yr_p5=pct(s["tau"], 5), residence_time_yr_p95=pct(s["tau"], 95),
        retention_R_median=pct(s["R"], 50),
        loss_rate_k_per_yr_median=pct(s["k"], 50), loss_rate_k_per_yr_p5=pct(s["k"], 5), loss_rate_k_per_yr_p95=pct(s["k"], 95),
        lake_TP_mgL_median=pct(s["TP"], 50), lake_TP_mgL_p5=pct(s["TP"], 5), lake_TP_mgL_p95=pct(s["TP"], 95),
        prob_TP_above_0_1=float(np.mean(s["TP"] > 0.1)), prob_TP_above_0_035=float(np.mean(s["TP"] > 0.035))))
pd.DataFrame(rows).round(4).to_csv(os.path.join(RES, "scenario_results.csv"), index=False)

mc = pd.DataFrame({"leakage_fraction": leak, **{f"TP_mgL_{k.split()[0]}": v["TP"] for k, v in scen.items()}})
mc.round(5).to_csv(os.path.join(RES, "montecarlo_lake_TP_samples.csv"), index=False)

# ---------------- sensitivity (Spearman), scenario S2 ----------------
tp2 = scen["S2 Diversion + tertiary effluent"]["TP"]
inp = {"leakage f": leak, "rainfall P": P, "runoff coefficient C": C, "raw sewage TP": TPs,
       "tertiary effluent TP": TPter, "mean depth": z, "export coefficient": ecu, "evaporation E": E}
sens = pd.DataFrame([dict(input=k, spearman_rho=float(stats.spearmanr(v, tp2).statistic)) for k, v in inp.items()])
sens = sens.reindex(sens.spearman_rho.abs().sort_values(ascending=False).index)
sens.round(3).to_csv(os.path.join(RES, "sensitivity_spearman_S2.csv"), index=False)

leak_rows = []
for lo, hi in [(0, .03), (.03, .07), (.07, .11), (.11, .15)]:
    m = (leak >= lo) & (leak < hi)
    leak_rows.append(dict(leakage_range=f"{lo:.0%}-{hi:.0%}", prob_TP_below_0_1=float(np.mean(tp2[m] < 0.1)), median_TP_mgL=float(np.median(tp2[m]))))
pd.DataFrame(leak_rows).round(3).to_csv(os.path.join(RES, "leakage_effect_S2.csv"), index=False)

# ---------------- Carpenter lake-model regime thresholds ----------------
def gmax(q): return (q - 1) ** ((q - 1) / q) / q
def fpmax(q):
    X = np.linspace(1e-4, 10, 200001)
    return float(np.max(q * X ** (q - 1) / (1 + X ** q) ** 2))
k_med = pct(scen["S2 Diversion + tertiary effluent"]["k"], 50)
reg = pd.DataFrame([dict(q=q, g_max=gmax(q), f_prime_max=fpmax(q),
                         r_over_m_for_hysteresis=k_med / fpmax(q), r_over_m_for_irreversibility=k_med / gmax(q)) for q in (2.0, 3.0, 4.0)])
reg.round(3).to_csv(os.path.join(RES, "lake_regime_thresholds.csv"), index=False)

kpost = scen["S2 Diversion + tertiary effluent"]["k"]
b_ann, b_mon = 1 - np.exp(-kpost), 1 - np.exp(-kpost / 12)

# ---------------- rainfall statistics ----------------
ann = rain["annual_mm"]
sh, _, sc = stats.lognorm.fit(ann, floc=0)
lr = stats.linregress(rain["year"], ann)
summary = dict(
    rainfall=dict(mean_mm=float(ann.mean()), sd_mm=float(ann.std()), cv=float(ann.std() / ann.mean()),
                  jun_sep_share=float((rain["jun_sep_mm"] / ann).mean()),
                  driest=[int(rain.year[ann.idxmin()]), float(ann.min())], wettest=[int(rain.year[ann.idxmax()]), float(ann.max())],
                  lognormal_median_mm=float(sc), lognormal_sigma=float(sh),
                  shapiro_wilk_log_p=float(stats.shapiro(np.log(ann)).pvalue),
                  trend_mm_per_yr=float(lr.slope), trend_p=float(lr.pvalue)),
    lake_volume_Mm3=[pct(V, 5) / 1e6, pct(V, 50) / 1e6, pct(V, 95) / 1e6],
    sewage_share_of_load_before_diversion=pct((Qs * day * TPs) / scen["S0 Before diversion"]["L"], 50),
    b_annual_median_p5_p95=[pct(b_ann, 50), pct(b_ann, 5), pct(b_ann, 95)],
    b_monthly_median_p5_p95=[pct(b_mon, 50), pct(b_mon, 5), pct(b_mon, 95)],
    classroom_lake=dict(b=0.42, q=2, regime="irreversible" if 0.42 < gmax(2) else "not irreversible"),
)
json.dump(summary, open(os.path.join(RES, "summary.json"), "w"), indent=1)
print(pd.DataFrame(rows)[["scenario", "lake_TP_mgL_median", "prob_TP_above_0_1"]].round(3).to_string(index=False))
