"""Step 5. Table 9 and Section 6.1: robust and conditional classifications of the religion bachelor's programs.

Alternatives: state and national threshold for every program; the other threshold where the in-state share decides it;
earnings x1.04 and x1.08 (timing); the housing allowance added or stripped at s = 15% and 50% (Table 4).
A program is a robust fail if it fails under the base and every alternative, a robust pass if it passes under all of them."""
import numpy as np
import pandas as pd
import config as C
from common import save

r = pd.read_csv(C.DER / "religion_ba_shifts.csv", dtype={"CIPCODE": str, "opeid6": str})
NAT = C.NATIONAL_HS
S = pd.DataFrame({
    "base": r.earn4 < r.th_rule,
    "state_th": r.earn4 < r.th,
    "nat_th": r.earn4 < NAT,
    "res_alt": r.earn4 < np.where(r.th_rule == r.th, NAT, r.th),
    "t4": r.earn4 * 1.04 < r.th_rule,
    "t8": r.earn4 * 1.08 < r.th_rule,
    "h_up15": r["earn_up_0.15"] < r.th_rule, "h_dn15": r["earn_dn_0.15"] < r.th_rule,
    "h_up50": r["earn_up_0.5"] < r.th_rule, "h_dn50": r["earn_dn_0.5"] < r.th_rule})
r["class"] = np.where(S.all(axis=1), "robust fail", np.where(~S.any(axis=1), "robust pass", "conditional"))
r["flips"] = [",".join(c for c in S.columns[1:] if S.loc[i, c] != S.loc[i, "base"]) for i in r.index]
r.to_csv(C.DER / "ba_robustness.csv", index=False)
print(r["class"].value_counts().to_string())
cnt = pd.DataFrame([dict(alternative=c, fail=int(S[c].sum()), pct_earners=round(100 * r.earners4[S[c]].sum() / r.earners4.sum(), 1))
                    for c in S.columns])
print(cnt.to_string(index=False))
t9 = r[(r["class"] != "robust pass") | r.fail10_rule | r.fail10_state].sort_values("margin_rule")
save(t9[["INSTNM", "CIPCODE", "state", "instate", "earn4", "th_rule", "margin_rule", "earners4", "yeshiva", "class", "flips"]],
     "table9_robustness.csv")
save(cnt, "table9_counts_by_alternative.csv")

g = pd.read_csv(C.DER / "grad_programs_scored.csv")
for k in [1.04, 1.08]:
    f = g.earn4 * k < g.comp_national
    print(f"graduate x{k}: {int(f.sum())} below $45,000:", ", ".join(g.INSTNM[f]))

# Joint sensitivity (Cartesian product): threshold x earnings timing x compensation construction.
# Thresholds: rule, state, national, the alternative residence classification. Timing: x1, x1.04, x1.08.
# Construction: published as is; allowance added or stripped at s = 15%, 50% (scaled ACS base); stripped on a W-2-only ACS
# base; naive sum to netted or W-2-only (CIP 39 only), all from step 2.
import itertools
h = pd.read_csv(C.ACS / "h7_bounds_acs_shifts.csv"); h = h[h.opt > 0.3]
nv = pd.read_csv(C.ACS / "acs_naive_sum_shifts.csv")
T, P = "BA field 49 (theology)", "BA field 48 (phil/relig)"
is39 = r.CIPCODE.str.startswith("39")
def hs(g, s_, col): return float(h[(h.group == g) & (h.s == s_)][col].iloc[0])
def ns(g, s_, col): return float(nv[(nv.group == g) & (nv.s == s_)][col].iloc[0])
cons = {"published": (0.0, 0.0)}
for s_ in [0.15, 0.50]:
    cons[f"added {s_}"] = (hs(T, s_, "up_pct"), hs(P, s_, "up_pct"))
    cons[f"stripped {s_}"] = (hs(T, s_, "dn_pct"), hs(P, s_, "dn_pct"))
    cons[f"stripped W2 base {s_}"] = (ns(T, s_, "netted_to_W2"), ns(P, s_, "netted_to_W2"))
    cons[f"naive->netted {s_}"] = (ns(T, s_, "sum_to_netted"), 0.0)
    cons[f"naive->W2 {s_}"] = (ns(T, s_, "sum_to_W2"), 0.0)
ths = {"rule": r.th_rule, "state": r.th, "national": pd.Series(NAT, index=r.index), "res_alt": pd.Series(np.where(r.th_rule == r.th, NAT, r.th), index=r.index)}
J = {}
for (tn, th), k, (cn, (d39, d38)) in itertools.product(ths.items(), [1.0, 1.04, 1.08], cons.items()):
    J[(tn, k, cn)] = r.earn4 * k * (1 + np.where(is39, d39, d38)) < th
J = pd.DataFrame(J)
r["joint_fail_share"] = J.mean(axis=1)
r["joint_class"] = np.where(J.all(axis=1), "fails in every combination", np.where(~J.any(axis=1), "passes in every combination", "conditional"))
print(f"\njoint design: {J.shape[1]} combinations ({len(ths)} thresholds x 3 timings x {len(cons)} constructions)")
print(r.joint_class.value_counts().to_string())
moved = r[(r["class"] == "robust pass") & (r.joint_class != "passes in every combination")]
print(f"one-at-a-time robust passes that fail in some joint combination: {len(moved)}")
cond = r[r.joint_class == "conditional"].sort_values("joint_fail_share", ascending=False)
save(cond[["INSTNM", "CIPCODE", "state", "earn4", "th_rule", "margin_rule", "yeshiva", "class", "joint_fail_share"]].round(3), "table9_joint_conditional.csv")
print(cond[["INSTNM", "CIPCODE", "margin_rule", "class", "joint_fail_share"]].round(2).to_string(index=False))
r.to_csv(C.DER / "ba_robustness.csv", index=False)
