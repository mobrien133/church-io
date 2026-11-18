"""Step 12. Figures 1 and 2."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#1a1a19", "#5f5e58", "#e6e5e1"
money = lambda v, p: f"{'−' if v < 0 else ''}${abs(v)/1000:.0f}k"
g = pd.read_csv(C.DER / "grad_programs_scored.csv")
ba = pd.read_csv(C.DER / "ba_robustness.csv", dtype={"CIPCODE": str})
ba["yeshiva"] = ba.yeshiva.astype(bool)

# ---------- Figure 1 ----------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200)
for ax in axes:
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8); ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax = axes[0]
ax.hist(g.earn4, bins=np.arange(30000, 125000, 5000), color=BLUE, edgecolor="white", linewidth=0.8)
ax.axvline(C.THEOLOGY_BA_NATIONAL, color=INK, lw=1.2, ls="--")
ax.text(C.THEOLOGY_BA_NATIONAL - 1200, ax.get_ylim()[1] * 0.92, "National theology-BA\ncomparator\n$45,000 (ACS)",
        fontsize=7.5, color=INK, va="top", ha="right")
ax.set_title("A. Graduate theology programs (CIP 39.06, master's & first-professional)", fontsize=9, color=INK, loc="left")
ax.set_xlabel("Program median earnings, 4 years after completion", fontsize=8, color=INK2); ax.set_ylabel("Programs", fontsize=8, color=INK2)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v/1000:.0f}k"))
ax.text(0.98, 0.97, f"n = {len(g)} reported programs\n{int(g.fail_national.sum())} below comparator", transform=ax.transAxes,
        ha="right", va="top", fontsize=7.5, color=INK2)
ax = axes[1]
groups = [("Yeshivas (CIP 38.02)", ba[ba.yeshiva], ORANGE), ("Ministry/Bible BAs (CIP 39)", ba[~ba.yeshiva & ba.CIPCODE.str.startswith("39")], BLUE),
          ("Religion/philosophy BAs (CIP 38, other)", ba[~ba.yeshiva & ba.CIPCODE.str.startswith("38")], AQUA)]
ax.hist([x[1].margin_rule for x in groups], bins=np.arange(-15000, 80000, 2500), stacked=True, color=[x[2] for x in groups],
        edgecolor="white", linewidth=0.6, label=[x[0] for x in groups])
ax.axvline(0, color=INK, lw=1.2, ls="--")
ax.text(1000, ax.get_ylim()[1] * 0.92, "Rule threshold\n(state or national\nHS-only median)", fontsize=7.5, color=INK, va="top")
ax.set_title("B. Religion bachelor's programs (CIP 38 & 39) vs. rule threshold", fontsize=9, color=INK, loc="left")
ax.set_xlabel("Program median earnings minus the rule's 2024 threshold", fontsize=8, color=INK2)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(money))
ax.legend(fontsize=7.5, frameon=False, loc="upper right", labelcolor=INK2)
ax.text(0.98, 0.72, f"n = {len(ba)} reported programs\n{int(ba.fail_rule.sum())} below threshold", transform=ax.transAxes,
        ha="right", va="top", fontsize=7.5, color=INK2)
fig.text(0.01, 0.005, "Source: College Scorecard field-of-study data (4th year after completion); 2024 thresholds (89 FR 107130), national where the "
         "IPEDS in-state share is below 50%;\nACS 2019–23 same-field comparator; FSA Title IV volumes for state. Puerto Rico excluded.", fontsize=6.5, color=INK2)
plt.tight_layout(rect=(0, 0.05, 1, 1)); plt.savefig(C.FIG / "figure1.png"); plt.close()

# ---------- Figure 2 ----------
br = pd.read_csv(C.DER / "breadth_all_levels.csv").set_index("UNITID")
ba["n_programs"] = pd.to_numeric(ba.UNITID, errors="coerce").map(br.n_prog_all)
ba["group"] = np.where(ba.yeshiva, "Yeshivas", np.where(ba.n_programs <= 10, "Ten or fewer programs", "More than ten programs"))
order = ["Yeshivas", "Ten or fewer programs", "More than ten programs"]
col = dict(zip(order, [ORANGE, BLUE, AQUA]))
rng = np.random.default_rng(2)
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=200)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID); ax.tick_params(colors=INK2, labelsize=8); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
for i, k in enumerate(order):
    d = ba[ba.group == k]; y = i + rng.uniform(-0.28, 0.28, len(d)); ba.loc[d.index, "yj"] = y
    ax.scatter(d.margin_rule / 1000, y, s=np.clip(d.earners4, 16, 500) / 4, color=col[k], alpha=0.75, edgecolor="white", linewidth=0.6)
    ax.text(51.5, i + 0.36, f"{k} (n = {len(d)}; {int((d.margin_rule < 0).sum())} below the line)", fontsize=8.5, color=INK, ha="right", va="bottom")
ax.axvline(0, color=INK, lw=1.1, ls="--"); ax.text(0.3, 3.05, "Rule threshold", fontsize=7.5, color=INK, va="top")
lab = {"United Talmudical Seminary": "United Talmudical", "Appalachian Bible College": "Appalachian Bible",
       "Mid-Atlantic Christian University": "Mid-Atlantic Christian", "Bethany Global University": "Bethany Global",
       "Crown College": "Crown (pastoral couns.)", "Southeastern University": "Southeastern (pastoral couns.)"}
for _, r in ba[ba.INSTNM.isin(lab) & (ba.margin_rule < 600)].iterrows():
    if r.INSTNM == "United Talmudical Seminary":
        xy = (-15.5, -0.45)
    elif r.INSTNM == "Bethany Global University":
        xy = (3.0, 0.62)
    else:
        xy = (-15.5, r.yj)
    ax.annotate(lab[r.INSTNM], (r.margin_rule / 1000, r.yj), xytext=xy, fontsize=6.5, color=INK2, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5, shrinkB=2))
ax.set_yticks([]); ax.set_xlim(-17, 52); ax.set_ylim(-0.6, 3.1)
ax.set_xlabel("Program median earnings four years after completion, minus the rule's threshold (thousands of dollars)", fontsize=8, color=INK2)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{'−' if v < 0 else ''}${abs(v):.0f}k"))
fig.text(0.01, 0.01, "Reported religion bachelor's programs (CIP 38 and 39), n = 237. Dot area ∝ earners in the cohort. Threshold: 2024 state "
         "high-school-only median, or the national median where the institution's first-time students are majority out-of-state. "
         "Programs: six-digit CIP codes by award level with a first-major completion, IPEDS 2021–22 and 2022–23, all credential levels (as in Table 8).",
         fontsize=6.3, color=INK2, wrap=True)
plt.tight_layout(rect=(0, 0.06, 1, 1)); plt.savefig(C.FIG / "figure2.png"); plt.close()
print("figures written:", [p.name for p in C.FIG.glob("*.png")])
