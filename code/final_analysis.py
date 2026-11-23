"""
CE 766 final project - Powai Lake: robust phosphorus management after sewage diversion.

Builds on the preliminary analysis (code/analysis.py) as proposed there:
  1. Monthly Carpenter-Vollenweider phosphorus model (annual step replaced by monthly step).
  2. Explicit levers: STP effluent TP standard, interception of residual sewage leakage, hyacinth harvesting.
  3. NSGA-II (pymoo) over the levers, three objectives: annual cost, mean lake TP, reliability (TP < 0.1 mg/L).
  4. Re-evaluation of the Pareto policies over 1,000 Latin Hypercube deep-uncertainty futures.
  5. PRIM scenario discovery: which futures make a chosen policy fail.

Run from the repository root:   python code/final_analysis.py
Inputs : data/imd_rainfall_powai_monthly_2001_2025.csv
Outputs: results/ (policies_pareto_and_robustness.csv, du_futures_outcomes.csv, monthly_TP_trajectories_baseline.csv,
         prim_trajectory.csv, failure_factor_shift_compromise.csv, model_checks.csv, final_summary.json)
"""
import os, json
import numpy as np, pandas as pd
from scipy.stats import qmc
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
SEED = 766
rng = np.random.default_rng(SEED)

# ---------------- fixed site data ----------------
rain = pd.read_csv(os.path.join(ROOT, "data", "imd_rainfall_powai_monthly_2001_2025.csv"))
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
P_YEARS = rain[[f"{m}_mm" for m in MONTHS]].values / 1000.0          # (25, 12) monthly rain, m
A_L, A_C = 2.2e6, 6.61e6                                              # m2 (Lekshmi et al. 2021)
A_LAND = A_C - A_L
Q_STP = 8e3                                                           # m3/d treated effluent returned (BMC)
DAYS = 365.0 / 12                                                     # days per month
DT = 1.0 / 12                                                         # yr per month
EVAP_SHAPE = np.array([130, 140, 180, 200, 210, 140, 100, 95, 105, 130, 120, 115], float)
EVAP_SHAPE /= EVAP_SHAPE.sum()                                        # monthly share of annual lake evaporation
T_YEARS = 10                                                          # simulate Jan 2028 - Dec 2037 (10 calendar yr, 120 months; STP online May 2027)
TARGET = 0.1                                                          # mg/L, hypereutrophic limit (OECD 1982)

# ---------------- uncertain factors ----------------
# name: (low, high).  Baseline ensemble samples the first block within these ranges with recycling fixed;
# the deep-uncertainty LHS samples all of them.
FACTORS = {
    "rain_mult":   (0.8, 1.3),    # rainfall multiplier (non-stationarity, +40 mm/yr trend)
    "C":           (0.4, 0.8),    # runoff coefficient
    "E":           (1.2, 1.8),    # annual lake evaporation, m/yr
    "z":           (2.5, 5.0),    # mean depth, m
    "Q_raw":       (15.0, 21.0),  # raw sewage generated in catchment, MLD
    "f0":          (0.0, 0.20),   # fraction of raw sewage still leaking in after diversion
    "TP_raw":      (4.0, 12.0),   # raw sewage TP, mg/L
    "e_u":         (0.5, 2.5),    # urban TP export coefficient, kg/ha/yr
    "v_s":         (5.0, 15.0),   # apparent P settling velocity, m/yr
    "p_h":         (150., 300.),  # P content of harvested hyacinth, g P per tonne wet weight
    "X0":          (0.5, 1.5),    # lake TP when the STP starts, mg/L (observed 0.93 +/- 0.61)
    "r_over_m":    (1.0, 10.0),   # max sediment recycling rate / half-saturation, 1/yr
    "m":           (0.1, 0.4),    # recycling half-saturation concentration, mg/L
    "q":           (2.0, 4.0),    # steepness of recycling curve
}
NOMINAL_RECYCLING = dict(rain_mult=1.0, r_over_m=4.0, m=0.2, q=2.0)   # baseline (well-characterised) case
DEP = 0.3                                                             # atmospheric deposition, kg/ha/yr

# ---------------- levers and indicative costs (Rs crore per year) ----------------
LEVERS = {"TP_eff": (0.1, 5.0),   # STP effluent TP standard, mg/L (5 = secondary treatment only)
          "u":      (0.0, 0.95),  # fraction of residual leakage intercepted
          "H":      (0.0, 50.0)}  # hyacinth harvest, tonnes wet weight per day
A_TRT, A_INT, A_HARV = 0.40, 0.50, 1000e-7 * 365   # Rs crore/yr coefficients (see README)


def cost(TP_eff, u, H):
    """Annual cost (Rs crore/yr): chemical P removal + sewer interception + harvesting."""
    return A_TRT * np.log(5.0 / TP_eff) + A_INT * (-np.log(1.0 - u)) + A_HARV * H


def sample_rain(n_fut, mult):
    """Monthly rainfall series (n_fut, 120): IMD years resampled with replacement, scaled by multiplier."""
    idx = rng.integers(0, P_YEARS.shape[0], size=(n_fut, T_YEARS))
    return P_YEARS[idx].reshape(n_fut, T_YEARS * 12) * mult[:, None]


def simulate(lev, fut, P):
    """
    Monthly Carpenter-Vollenweider model, semi-implicit in the loss terms.
      X_{t+1} = [X_t + L_t/V + dt * r X_t^q / (m^q + X_t^q) - H_t] / [1 + Q_t/V + (v_s/z) dt]
    lev : dict of arrays broadcastable to (n_pol, n_fut); fut : dict of (n_fut,) arrays; P : (n_fut, 120)
    returns X : (n_pol, n_fut, 120) lake TP (mg/L)
    """
    TP_eff, u, H = (np.asarray(lev[k], float)[:, None] for k in ("TP_eff", "u", "H"))
    V = A_L * fut["z"]                                                 # m3
    f = fut["f0"] * (1 - u)                                            # residual leakage after interception
    Q_ww = (Q_STP + f * fut["Q_raw"] * 1e3) * DAYS                     # m3/month
    L_ww = (Q_STP * TP_eff + f * fut["Q_raw"] * 1e3 * fut["TP_raw"]) * DAYS   # g/month
    sigma = fut["v_s"] / fut["z"]                                      # settling loss, 1/yr
    m, q = fut["m"], fut["q"]
    r = fut["r_over_m"] * m                                            # mg/L/yr
    P_yr = P.reshape(len(V), T_YEARS, 12).sum(-1).repeat(12, axis=1)   # annual rain for each month
    X = np.broadcast_to(fut["X0"], TP_eff.shape[:1] + V.shape).copy()
    out = np.empty(X.shape + (P.shape[1],))
    for t in range(P.shape[1]):
        Pt = P[:, t]
        inflow = Pt * (fut["C"] * A_LAND + A_L) - fut["E"] * EVAP_SHAPE[t % 12] * A_L
        Q = np.maximum(inflow, 0.0) + Q_ww                             # outflow, m3/month
        L_nps = (fut["e_u"] * A_LAND / 1e4 * 1e3) * (Pt / P_yr[:, t]) + DEP * A_L / 1e4 * 1e3 * DT  # g/month
        harvest = np.minimum(H * DAYS * fut["p_h"] / V, 0.5 * X)       # mg/L removed in hyacinth
        recyc = DT * r * X ** q / (m ** q + X ** q)
        X = (X + (L_ww + L_nps) / V + recyc - harvest) / (1 + Q / V + sigma * DT)
        out[..., t] = X
    return out


def metrics(X):
    """Mean TP over 10 yr, monthly reliability (TP < target), and mean TP in years 6-10 (end state)."""
    return X.mean(-1), (X < TARGET).mean(-1), X[..., 60:].mean(-1)


def sample_baseline(n):
    fut = {k: rng.uniform(lo, hi, n) for k, (lo, hi) in FACTORS.items()}
    for k, v in NOMINAL_RECYCLING.items():
        fut[k] = np.full(n, v)
    return fut


# =============== 1. baseline ensemble and NSGA-II ===============
N_BASE = 200
base = sample_baseline(N_BASE)
P_base = sample_rain(N_BASE, base["rain_mult"])


class LakeProblem(Problem):
    def __init__(self):
        lo, hi = zip(*LEVERS.values())
        super().__init__(n_var=3, n_obj=3, xl=np.array(lo), xu=np.array(hi))

    def _evaluate(self, x, out, *args, **kwargs):
        lev = dict(TP_eff=x[:, 0], u=x[:, 1], H=x[:, 2])
        mean_tp, rel, _ = metrics(simulate(lev, base, P_base))
        out["F"] = np.column_stack([cost(*x.T), mean_tp.mean(1), -rel.mean(1)])


res = minimize(LakeProblem(), NSGA2(pop_size=100), ("n_gen", 120), seed=SEED, verbose=False)
X_par = res.X[np.argsort(res.F[:, 0])]
pareto = pd.DataFrame(X_par, columns=list(LEVERS))
pareto["cost_cr_per_yr"] = cost(*X_par.T)
mb, rb, eb = metrics(simulate(pareto, base, P_base))
pareto["mean_TP_mgL"], pareto["reliability"], pareto["end_TP_mgL"] = mb.mean(1), rb.mean(1), eb.mean(1)

# reference policies (no optimisation)
refs = pd.DataFrame([
    dict(policy="Status quo: secondary STP, no extra action", TP_eff=5.0, u=0.0, H=0.0),
    dict(policy="Tertiary STP only (prelim S2)", TP_eff=0.75, u=0.0, H=0.0),
    dict(policy="Effluent standard only (0.1 mg/L)", TP_eff=0.1, u=0.0, H=0.0),
    dict(policy="Leakage interception only (95%)", TP_eff=5.0, u=0.95, H=0.0),
])
mr, rr, er = metrics(simulate(refs, base, P_base))
refs["mean_TP_mgL"], refs["reliability"], refs["end_TP_mgL"] = mr.mean(1), rr.mean(1), er.mean(1)

# =============== 2. deep-uncertainty re-evaluation (LHS) ===============
N_DU = 1000
names = list(FACTORS)
lhs = qmc.LatinHypercube(d=len(names), seed=SEED).random(N_DU)
lo, hi = np.array([FACTORS[k] for k in names]).T
du = {k: lo[i] + lhs[:, i] * (hi[i] - lo[i]) for i, k in enumerate(names)}
P_du = sample_rain(N_DU, du["rain_mult"])

all_pol = pd.concat([pareto.assign(policy=[f"P{i+1}" for i in range(len(pareto))]),
                     refs.assign(cost_cr_per_yr=cost(refs.TP_eff, refs.u, refs.H))], ignore_index=True)
md, rd, ed = metrics(simulate(all_pol, du, P_du))
success = ed < TARGET                                                  # satisficing: end-state mean TP < 0.1 mg/L
all_pol["robustness"] = success.mean(1)
all_pol["DU_median_end_TP_mgL"] = np.median(ed, 1)
all_pol["DU_reliability_mean"] = rd.mean(1)
all_pol.round(4).to_csv(os.path.join(RES, "policies_pareto_and_robustness.csv"), index=False)

# chosen compromise: cheapest Pareto policy whose robustness is >= 90% of the best Pareto robustness
par = all_pol[all_pol.policy.str.startswith("P")]
best_rob = par.robustness.max()
comp = par[par.robustness >= 0.9 * best_rob].sort_values("cost_cr_per_yr").iloc[0]
ci = int(comp.name)

# =============== 3. PRIM scenario discovery for the compromise policy ===============
def prim(Xf, y, alpha=0.05, min_mass=0.05):
    """Patient Rule Induction Method (Friedman & Fisher 1999), peeling only. Returns peeling trajectory."""
    box = {k: [Xf[k].min(), Xf[k].max()] for k in Xf}
    inside = np.ones(len(y), bool)
    traj = [dict(coverage=1.0, density=y.mean(), mass=1.0, box={k: list(v) for k, v in box.items()})]
    while inside.mean() > min_mass:
        best = None
        for k in Xf:
            xs = Xf[k][inside]
            for side, thr in (("lo", np.quantile(xs, alpha)), ("hi", np.quantile(xs, 1 - alpha))):
                keep = inside & ((Xf[k] >= thr) if side == "lo" else (Xf[k] <= thr))
                if keep.sum() == 0 or keep.sum() == inside.sum():
                    continue
                d = y[keep].mean()
                if best is None or d > best[0]:
                    best = (d, k, side, thr, keep)
        if best is None:
            break
        d, k, side, thr, inside = best
        box[k][0 if side == "lo" else 1] = float(thr)
        traj.append(dict(coverage=y[inside].sum() / y.sum(), density=d, mass=inside.mean(),
                         box={kk: list(v) for kk, v in box.items()}))
    return traj


fail = ~success[ci]
prim_in = dict(du, sigma=du["v_s"] / du["z"])                         # derived: settling loss rate, 1/yr
traj = prim(prim_in, fail.astype(float))
# pick the box with density >= 0.8 and the highest coverage (fallback: highest coverage*density)
cand = [b for b in traj if b["density"] >= 0.8] or traj
pick = max(cand, key=lambda b: b["coverage"] * (1 if b["density"] >= 0.8 else b["density"]))
full = {k: (v.min(), v.max()) for k, v in prim_in.items()}
restricted = {k: v for k, v in pick["box"].items()                     # keep dims cut by > 10% of their range
              if (v[1] - v[0]) < 0.9 * (full[k][1] - full[k][0])}
pd.DataFrame(traj)[["coverage", "density", "mass"]].round(4).to_csv(os.path.join(RES, "prim_trajectory.csv"), index=False)

# Spearman-like importance for failures: difference in medians (normalised) of each factor, fail vs success
imp = pd.DataFrame([dict(factor=k, median_fail=np.median(du[k][fail]) if fail.any() else np.nan,
                         median_success=np.median(du[k][~fail]),
                         normalised_shift=(np.median(du[k][fail]) - np.median(du[k][~fail])) / (FACTORS[k][1] - FACTORS[k][0])
                         if fail.any() else np.nan) for k in names])
imp = imp.reindex(imp.normalised_shift.abs().sort_values(ascending=False).index)
imp.round(4).to_csv(os.path.join(RES, "failure_factor_shift_compromise.csv"), index=False)

# save DU samples + outcomes for the compromise and status-quo/tertiary references (for figures)
sq_i = int(all_pol.index[all_pol.policy.str.startswith("Status")][0])
s2_i = int(all_pol.index[all_pol.policy.str.startswith("Tertiary")][0])
du_df = pd.DataFrame(prim_in)
du_df["end_TP_compromise"], du_df["end_TP_tertiary_only"], du_df["end_TP_status_quo"] = ed[ci], ed[s2_i], ed[sq_i]
du_df["fail_compromise"] = fail
du_df.round(5).to_csv(os.path.join(RES, "du_futures_outcomes.csv"), index=False)

# monthly trajectories (baseline ensemble) for compromise, tertiary-only and status quo
sel = all_pol.loc[[ci, s2_i, sq_i]]
Xb = simulate(sel, base, P_base)
traj_df = pd.DataFrame({"month": np.arange(1, 121)})
for lab, xb in zip(["compromise", "tertiary_only", "status_quo"], Xb):
    for p in (5, 50, 95):
        traj_df[f"{lab}_p{p}"] = np.percentile(xb, p, axis=0)
traj_df.round(5).to_csv(os.path.join(RES, "monthly_TP_trajectories_baseline.csv"), index=False)

summary = dict(
    nsga2=dict(pop_size=100, generations=120, n_baseline_futures=N_BASE, n_pareto=len(pareto)),
    deep_uncertainty=dict(n_futures=N_DU, satisficing="mean TP in 2033-2037 (years 6-10) < 0.1 mg/L"),
    compromise=dict(policy=comp.policy, TP_eff=float(comp.TP_eff), u=float(comp.u), H=float(comp.H),
                    cost_cr_per_yr=float(comp.cost_cr_per_yr), mean_TP=float(comp.mean_TP_mgL),
                    reliability=float(comp.reliability), robustness=float(comp.robustness)),
    best_pareto_robustness=float(best_rob),
    status_quo=all_pol.loc[sq_i, ["cost_cr_per_yr", "mean_TP_mgL", "reliability", "robustness"]].astype(float).to_dict(),
    tertiary_only=all_pol.loc[s2_i, ["cost_cr_per_yr", "mean_TP_mgL", "reliability", "robustness"]].astype(float).to_dict(),
    prim_box=dict(coverage=pick["coverage"], density=pick["density"], mass=pick["mass"], limits=restricted),
)
json.dump(summary, open(os.path.join(RES, "final_summary.json"), "w"), indent=1, default=float)
print(json.dumps(summary, indent=1, default=float))
print(all_pol[["policy", "TP_eff", "u", "H", "cost_cr_per_yr", "mean_TP_mgL", "reliability", "robustness"]].round(3).to_string())

# =============== 4. consistency checks against observations and the preliminary model ===============
def check(lev, fut, P, q_stp):
    global Q_STP
    keep, Q_STP = Q_STP, q_stp
    X = simulate(lev, fut, P)[0]
    Q_STP = keep
    end = X[:, 60:].mean(-1)
    return dict(median=float(np.median(end)), p5=float(np.percentile(end, 5)), p95=float(np.percentile(end, 95)))

no_rec = dict(base, r_over_m=np.zeros(N_BASE))
pre = dict(base, f0=np.ones(N_BASE))                                  # all raw sewage enters, no STP
pre_norec = dict(no_rec, f0=np.ones(N_BASE))
one = lambda **k: {kk: np.array([v]) for kk, v in k.items()}
s2_norec = dict(no_rec, f0=rng.uniform(0, 0.15, N_BASE))              # preliminary S2 leakage range
checks = {
    "pre-diversion, no recycling (prelim S0 = 1.21)": check(one(TP_eff=0.0, u=0.0, H=0.0), pre_norec, P_base, 0.0),
    "pre-diversion, nominal recycling r/m = 4": check(one(TP_eff=0.0, u=0.0, H=0.0), pre, P_base, 0.0),
    "tertiary STP, no recycling (prelim S2 = 0.20)": check(one(TP_eff=0.75, u=0.0, H=0.0), s2_norec, P_base, Q_STP),
}
pd.DataFrame(checks).T.round(3).rename_axis("case").to_csv(os.path.join(RES, "model_checks.csv"))
print(pd.DataFrame(checks).T.round(3).to_string())
