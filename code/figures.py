"""Make the summary figure (methodology flow + scenario results). Run after analysis.py:  python code/figures.py"""
import os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, FixedFormatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(ROOT, "results"), os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
BLUE, BLUE_L, ORANGE, INK, INK2, GRID, BOX = "#2a78d6", "#b7d3f6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#f3f7fc"
fams = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
plt.rcParams.update({"font.family": "Carlito" if "Carlito" in fams else "DejaVu Sans", "font.size": 12,
                     "mathtext.fontset": "cm", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2})

mc = pd.read_csv(os.path.join(RES, "montecarlo_lake_TP_samples.csv"))
sc = pd.read_csv(os.path.join(RES, "scenario_results.csv"))

fig = plt.figure(figsize=(13.5, 6.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.15], wspace=0.12)

# ---------------- (a) methodology flow ----------------
ax = fig.add_subplot(gs[0]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("(a) Methodology", loc="left", fontsize=14, fontweight="bold", color=INK)
steps = [
    ("Data", "IMD 0.25° rainfall 2001–2025 (bilinear at 19.13°N, 72.91°E)\nLake 2.2 km², catchment 6.61 km²; TP 2016–20; sewage 18 MLD"),
    ("Water balance", r"$Q = P\,C\,(A_C - A_L) + P\,A_L - E\,A_L + Q_{ww}$"),
    ("Phosphorus load", r"$L = Q_{ww}\,TP_{ww} + e_u\,(A_C - A_L) + d\,A_L$"),
    ("Lake phosphorus", r"$\tau = V/Q,\quad R = 1/(1+\sqrt{\tau}),\quad TP = (L/Q)\,(1-R)$"),
    ("Monte Carlo (N = 20,000)", "4 sewage-diversion scenarios + Spearman sensitivity"),
    ("Link to Lake Problem", r"$k = 1/[\tau\,(1-R)],\quad b = 1-e^{-k}\ \rightarrow$ lake type ($b$ vs $q$)"),
]
n = len(steps); top, h, gap = 0.965, 0.135, 0.026
for i, (title, body) in enumerate(steps):
    y = top - i * (h + gap) - h
    ax.add_patch(FancyBboxPatch((0.02, y), 0.96, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                fc=BOX, ec="#7fa3c8", lw=1.1))
    ax.text(0.05, y + h - 0.022, f"{i + 1}. {title}", fontsize=12.5, fontweight="bold", color="#1F4E79", va="top")
    ax.text(0.05, y + 0.042, body, fontsize=12 if "$" in body else 10.5, color=INK, va="center", linespacing=1.35)
    if i < n - 1:
        ax.annotate("", xy=(0.5, y - gap + 0.004), xytext=(0.5, y - 0.004),
                    arrowprops=dict(arrowstyle="-|>", color="#7fa3c8", lw=1.6))

# ---------------- (b) results ----------------
b = fig.add_subplot(gs[1])
cols = ["TP_mgL_S0", "TP_mgL_S1", "TP_mgL_S2", "TP_mgL_S3"]
labels = ["Before diversion\n(18 MLD raw sewage)", "Diversion +\nsecondary effluent", "Diversion +\ntertiary effluent", "Diversion,\nno effluent return"]
data = [mc[c].values for c in cols]
b.boxplot(data, positions=range(4), widths=0.45, whis=(5, 95), showfliers=False, patch_artist=True,
          medianprops=dict(color=INK, lw=1.6), boxprops=dict(facecolor=BLUE_L, edgecolor=BLUE, lw=1.2),
          whiskerprops=dict(color=BLUE, lw=1.2), capprops=dict(color=BLUE, lw=1.2))
for i, (d, p) in enumerate(zip(data, sc["prob_TP_above_0_1"])):
    b.text(i + 0.27, np.median(d), f"{np.median(d):.2f}", va="center", ha="left", fontsize=12, fontweight="bold", color=INK)
    b.text(i, 2.75, f"{p:.0%}", ha="center", fontsize=11.5, color=INK)
b.text(-0.85, 2.75, "P(TP > 0.1):", ha="left", fontsize=11, color=INK2)
b.errorbar([-0.45], [0.93], yerr=[[0.61], [0.61]], fmt="o", color=ORANGE, ms=7, capsize=3.5, lw=1.4, zorder=4)
b.text(-0.45, 0.24, "Observed\n2018–20", color=ORANGE, fontsize=10.5, ha="center", va="top")
b.set_yscale("log"); b.set_ylim(0.025, 3.6)
b.yaxis.set_major_locator(FixedLocator([0.03, 0.1, 0.3, 1, 3]))
b.yaxis.set_major_formatter(FixedFormatter(["0.03", "0.1", "0.3", "1", "3"]))
b.yaxis.set_minor_locator(FixedLocator([]))
for y, t in [(0.1, "Hypereutrophic limit 0.1 mg/L"), (0.035, "Eutrophic limit 0.035 mg/L")]:
    b.axhline(y, color=INK2, lw=0.9, ls=":")
    b.text(1.0, y * 1.08, t, fontsize=10, color=INK2, ha="center", va="bottom")
b.set_xticks(range(4)); b.set_xticklabels(labels, fontsize=10.5); b.set_xlim(-0.9, 3.6)
b.set_ylabel("Steady-state lake TP (mg/L, log scale)")
b.yaxis.grid(True, color=GRID, lw=0.6); b.set_axisbelow(True)
b.set_title("(b) Result: lake phosphorus before and after diversion", loc="left", fontsize=14, fontweight="bold", color=INK)

fig.text(0.5, 0.012, "Box: 25–75%, whiskers: 5–95% of 20,000 Monte Carlo runs; number = median. Model reproduces observed TP "
         "(1.21 vs 0.93 ± 0.61 mg/L). Rainfall: mean 2,872 mm/yr, +40 mm/yr trend (p = 0.006).",
         ha="center", fontsize=10.5, color=INK2)
fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.17)
fig.savefig(os.path.join(FIG, "methodology_and_results.png"), dpi=200)
print("saved")
