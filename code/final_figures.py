"""Figures for the final submission. Run after final_analysis.py:  python code/final_figures.py"""
import os, json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator, FixedFormatter, PercentFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
RES, FIG = (os.path.join(os.path.dirname(HERE), d) for d in ("results", "figures"))
os.makedirs(FIG, exist_ok=True)
BLUE, ORANGE, GREY, INK, INK2, GRID = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.labelcolor": INK, "axes.titlesize": 13.5})
BLUES = LinearSegmentedColormap.from_list("blues", ["#dbe8fa", "#7fb0ef", "#2a78d6", "#0d3f86"])

pol = pd.read_csv(os.path.join(RES, "policies_pareto_and_robustness.csv"))
summ = json.load(open(os.path.join(RES, "final_summary.json")))
par = pol[pol.policy.str.match(r"^P\d+$")].sort_values("cost_cr_per_yr")
sq = pol[pol.policy.str.startswith("Status")].iloc[0]
s2 = pol[pol.policy.str.startswith("Tertiary")].iloc[0]
cp = pol[pol.policy == summ["compromise"]["policy"]].iloc[0]


def grid(ax):
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)


# ======================= Figure 1: trade-offs and robustness =======================
fig, (a, b) = plt.subplots(1, 2, figsize=(14, 6.2), gridspec_kw=dict(wspace=0.42))

sc = a.scatter(par.cost_cr_per_yr, par.mean_TP_mgL, c=par.reliability * 100, cmap=BLUES, vmin=0, vmax=100,
               s=55, edgecolor="white", lw=0.8, zorder=3)
a.set_yscale("log"); a.set_ylim(0.035, 1.0)
a.yaxis.set_major_locator(FixedLocator([0.05, 0.1, 0.2, 0.5, 1.0]))
a.yaxis.set_major_formatter(FixedFormatter(["0.05", "0.1", "0.2", "0.5", "1.0"]))
a.yaxis.set_minor_locator(FixedLocator([]))
a.axhline(0.1, color=INK2, lw=0.9, ls=":")
a.text(5.05, 0.104, "Hypereutrophic limit 0.1 mg/L", ha="right", va="bottom", fontsize=10, color=INK2)
for p, lab, dx, dy, ha in [(sq, "Status quo\n(secondary STP only)", 0.12, 0.0, "left"),
                           (s2, "Tertiary STP only\n(prelim. S2)", 0.12, 0.03, "left")]:
    a.scatter(p.cost_cr_per_yr, p.mean_TP_mgL, marker="s", s=70, color=GREY, edgecolor="white", zorder=4)
    a.text(p.cost_cr_per_yr + dx, p.mean_TP_mgL + dy, lab, fontsize=10.5, color=INK2, va="center", ha=ha)
a.scatter(cp.cost_cr_per_yr, cp.mean_TP_mgL, s=210, facecolor="none", edgecolor=ORANGE, lw=2.2, zorder=5)
a.annotate(f"Compromise {cp.policy}\nTP$_{{eff}}$ = {cp.TP_eff:.2f} mg/L,\n{cp.u:.0%} leakage intercepted,\n"
           f"{cp.H:.0f} t/d harvest; Rs {cp.cost_cr_per_yr:.1f} cr/yr",
           xy=(cp.cost_cr_per_yr, cp.mean_TP_mgL), xytext=(2.55, 0.3), fontsize=10.5, color=INK,
           arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.2))
a.set_xlim(-0.15, 5.1)
a.set_xlabel("Annual cost of levers (Rs crore/yr, indicative)")
a.set_ylabel("Mean lake TP, 2028–37 (mg/L, log scale)")
a.set_title("(a) NSGA-II Pareto front (200 baseline futures)", loc="left", fontweight="bold")
grid(a)
cb = fig.colorbar(sc, ax=a, pad=0.015, fraction=0.045)
cb.set_label("Reliability (% of months TP < 0.1 mg/L)", fontsize=10.5)
cb.outline.set_visible(False)

b.plot(par.cost_cr_per_yr, par.robustness * 100, color=BLUE, lw=2, zorder=3)
b.scatter(par.cost_cr_per_yr, par.robustness * 100, s=22, color=BLUE, edgecolor="white", lw=0.6, zorder=4,
          label="Pareto policies")
for p, lab, ty in [(sq, "Status quo: 0%", 38), (s2, f"Tertiary STP only: {s2.robustness:.0%}", 28)]:
    b.scatter(p.cost_cr_per_yr, p.robustness * 100, marker="s", s=70, color=GREY, edgecolor="white", zorder=5)
    b.annotate(lab, xy=(p.cost_cr_per_yr, p.robustness * 100), xytext=(0.05, ty), fontsize=10.5, color=INK2,
               arrowprops=dict(arrowstyle="-", color=GREY, lw=0.9))
b.scatter(cp.cost_cr_per_yr, cp.robustness * 100, s=210, facecolor="none", edgecolor=ORANGE, lw=2.2, zorder=6)
b.text(cp.cost_cr_per_yr - 0.12, cp.robustness * 100 + 3, f"{cp.policy}: {cp.robustness:.0%}", ha="right",
       fontsize=10.5, color=INK, fontweight="bold")
best = par.loc[par.robustness.idxmax()]
b.text(best.cost_cr_per_yr, best.robustness * 100 + 3, f"max {best.robustness:.0%}", ha="right", fontsize=10.5,
       color=INK2)
b.set_xlim(-0.15, 5.1); b.set_ylim(-3, 105)
b.yaxis.set_major_formatter(PercentFormatter())
b.set_xlabel("Annual cost of levers (Rs crore/yr, indicative)")
b.set_ylabel("Robustness: % of 1,000 deep-uncertainty futures\nwith mean TP < 0.1 mg/L in 2033–37")
b.set_title("(b) Robustness over 1,000 LHS futures", loc="left", fontweight="bold")
grid(b)
fig.suptitle("Figure 1.  Cost vs lake phosphorus trade-off (NSGA-II) and robustness of each policy, Powai Lake",
             x=0.01, ha="left", fontsize=15, fontweight="bold", color=INK)
fig.subplots_adjust(left=0.06, right=0.985, top=0.86, bottom=0.11)
fig.savefig(os.path.join(FIG, "Figure1_pareto_robustness.png"), dpi=220)
plt.close(fig)

# ======================= Figure 2: trajectories and scenario discovery =======================
tr = pd.read_csv(os.path.join(RES, "monthly_TP_trajectories_baseline.csv"))
du = pd.read_csv(os.path.join(RES, "du_futures_outcomes.csv"))
box = summ["prim_box"]
fig, (a, b) = plt.subplots(1, 2, figsize=(14, 6.2), gridspec_kw=dict(wspace=0.2, width_ratios=[1.1, 1]))

yrs = 2028 + (tr.month - 1) / 12
for key, col, lab in [("status_quo", GREY, "Status quo (secondary STP)"),
                      ("tertiary_only", BLUE, "Tertiary STP only"),
                      ("compromise", ORANGE, f"Compromise {cp.policy}")]:
    a.fill_between(yrs, tr[f"{key}_p5"], tr[f"{key}_p95"], color=col, alpha=0.16, lw=0)
    a.plot(yrs, tr[f"{key}_p50"], color=col, lw=2, label=lab)
a.axhline(0.1, color=INK2, lw=0.9, ls=":")
a.text(2037.85, 0.106, "0.1 mg/L", ha="right", va="bottom", fontsize=10, color=INK2)
a.set_yscale("log"); a.set_ylim(0.008, 7)
a.yaxis.set_major_locator(FixedLocator([0.01, 0.03, 0.1, 0.3, 1.0]))
a.yaxis.set_major_formatter(FixedFormatter(["0.01", "0.03", "0.1", "0.3", "1.0"]))
a.yaxis.set_minor_locator(FixedLocator([]))
a.set_xlim(2028, 2038)
a.set_xlabel("Year (monthly time step, Jan 2028 – Dec 2037)")
a.set_ylabel("Lake TP (mg/L, log scale)")
a.set_title("(a) Monthly lake TP: median and 5–95% band (baseline)", loc="left", fontweight="bold")
a.legend(loc="upper center", ncol=3, frameon=False, fontsize=10, handlelength=1.4, columnspacing=1.2)
grid(a)

ok, bad = du[~du.fail_compromise], du[du.fail_compromise]
b.scatter(ok.r_over_m, ok.sigma, s=14, color=BLUE, alpha=0.55, lw=0, label=f"Meets target ({len(ok)})")
b.scatter(bad.r_over_m, bad.sigma, s=20, color=ORANGE, alpha=0.9, lw=0, label=f"Fails ({len(bad)})")
rl, sl = box["limits"]["r_over_m"], box["limits"]["sigma"]
b.add_patch(Rectangle((rl[0], sl[0]), rl[1] - rl[0], sl[1] - sl[0], fill=False, ec=INK, lw=1.6, ls="--", zorder=5))
b.text(9.95, 6.0,
       f"PRIM box: r/m > {rl[0]:.1f} /yr and σ < {sl[1]:.1f} /yr\n"
       f"coverage {box['coverage']:.0%}, density {box['density']:.0%}", ha="right", va="top", fontsize=10.5,
       color=INK, bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
b.axvline(6.0, color=INK2, lw=0.9, ls=":")
b.text(5.9, 0.95, "Hysteresis threshold\nfor q = 2 (prelim.)", ha="right", va="bottom", fontsize=9.5,
       color=INK2, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
b.set_xlabel("Sediment recycling strength r/m (1/yr)")
b.set_ylabel("Settling loss rate σ = v$_s$ / z (1/yr)")
b.set_title(f"(b) Where compromise {cp.policy} fails (1,000 futures)", loc="left", fontweight="bold")
b.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=10.5, markerscale=1.6)
grid(b)
fig.suptitle("Figure 2.  Monthly lake TP under three policies, and the futures in which the compromise policy fails",
             x=0.01, ha="left", fontsize=15, fontweight="bold", color=INK)
fig.subplots_adjust(left=0.06, right=0.985, top=0.86, bottom=0.11)
fig.savefig(os.path.join(FIG, "Figure2_trajectories_prim.png"), dpi=220)
print("saved figures")
