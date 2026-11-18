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
