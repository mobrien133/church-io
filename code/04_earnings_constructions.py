"""Step 4. Table 4: failing programs under alternative earnings constructions (Section 4.3).

Each row moves every program median by a field-level percentage shift computed in step 2 from the ACS microdata:
  - allowance added or stripped (h7_bounds_acs_shifts.csv, one-third of clergy opted out of Social Security), scaling the
    ACS earnings of clergy who pay self-employment tax up or down;
  - allowance stripped on a W-2-only ACS base (acs_naive_sum_shifts.csv, netted_to_W2), the assumption of the naive-sum rows;
  - naive sum of W-2 and Schedule SE to netted or W-2-only (acs_naive_sum_shifts.csv; CIP 39 bachelor's programs take the
    theology shift, CIP 38 programs none);
  - clergy-majority shifts of 16 and 20 percent for graduate programs.
Graduate programs are scored against the national ($45,000) and in-state lowest-of-three comparators.
"""
import numpy as np
import pandas as pd
import config as C
from common import save

ba = pd.read_csv(C.DER / "religion_ba_scored.csv", dtype={"CIPCODE": str, "opeid6": str})
g = pd.read_csv(C.DER / "grad_programs_scored.csv")
h = pd.read_csv(C.ACS / "h7_bounds_acs_shifts.csv"); h = h[h.opt > 0.3]
n = pd.read_csv(C.ACS / "acs_naive_sum_shifts.csv")
T, P, G = "BA field 49 (theology)", "BA field 48 (phil/relig)", "Grad, BA field 49"


def hs(group, s, col):
    return float(h[(h.group == group) & (h.s == s)][col].iloc[0])


def ns(group, s, col):
    return float(n[(n.group == group) & (n.s == s)][col].iloc[0])


is39 = ba.CIPCODE.str.startswith("39")
rows = [("Same construction", 0.0, 0.0, 0.0)]
for s in [0.15, 0.50]:
    rows.append((f"W-2-only -> netted, s = {int(s*100)}%", hs(T, s, "up_pct"), hs(P, s, "up_pct"), hs(G, s, "up_pct")))
for s in [0.15, 0.50]:
    rows.append((f"Netted -> W-2-only, s = {int(s*100)}%", hs(T, s, "dn_pct"), hs(P, s, "dn_pct"), hs(G, s, "dn_pct")))
for s in [0.15, 0.50]:
    rows.append((f"Netted -> W-2-only, s = {int(s*100)}%, W-2-only ACS base", ns(T, s, "netted_to_W2"), ns(P, s, "netted_to_W2"),
                 ns(G, s, "netted_to_W2")))
for s in [0.15, 0.50]:
    rows.append((f"Naive sum -> netted, s = {int(s*100)}%", ns(T, s, "sum_to_netted"), 0.0, ns(G, s, "sum_to_netted")))
for s in [0.15, 0.50]:
    rows.append((f"Naive sum -> W-2-only, s = {int(s*100)}%", ns(T, s, "sum_to_W2"), 0.0, ns(G, s, "sum_to_W2")))
rows += [("Netted -> W-2-only, clergy majority (-16%)", None, None, -0.16),
         ("Netted -> W-2-only, clergy majority (-20%)", None, None, -0.20)]

md = g.type.eq("mostly MDiv (39.0602)")
out = []
for lab, d39, d38, dg in rows:
    r = dict(scenario=lab)
    if d39 is not None:
        e = ba.earn4 * (1 + np.where(is39, d39, d38))
        r.update(shift_ba=f"{100*d39:+.1f}%", ba_fail=int((e < ba.th_rule).sum()))
    else:
        r.update(shift_ba="-", ba_fail=None)
    e = g.earn4 * (1 + dg)
    fn, fi = e < g.comp_national, e < g.comp_instate
    r.update(shift_grad=f"{100*dg:+.1f}%", grad_fail_national=int(fn.sum()), grad_fail_instate=int(fi.sum()),
             pct_earners_national=round(100 * g.earners4[fn].sum() / g.earners4.sum(), 1),
             pct_earners_instate=round(100 * g.earners4[fi].sum() / g.earners4.sum(), 1),
             mdiv_national=int((fn & md).sum()), mdiv_instate=int((fi & md).sum()),
             instate_subset_of_national=bool((fi & ~fn).sum() == 0))
    out.append(r)
t = pd.DataFrame(out)
t["ba_fail"] = t.ba_fail.astype("Int64")
save(t, "table4_earnings_constructions.csv")
print(t.to_string(index=False))

# Programs that fail on the national comparator but pass in-state, at an 11 percent downward shift
e = g.earn4 * (1 + hs(G, 0.5, "dn_pct"))
print(g[(e < g.comp_national) & (e >= g.comp_instate)][["INSTNM", "state", "comp_instate"]].to_string(index=False))

# Program-level earnings under each shift, for step 5
for s in [0.15, 0.50]:
    ba[f"earn_up_{s}"] = ba.earn4 * (1 + np.where(is39, hs(T, s, "up_pct"), hs(P, s, "up_pct")))
    ba[f"earn_dn_{s}"] = ba.earn4 * (1 + np.where(is39, hs(T, s, "dn_pct"), hs(P, s, "dn_pct")))
ba.to_csv(C.DER / "religion_ba_shifts.csv", index=False)
