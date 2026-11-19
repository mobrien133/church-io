"""Step 6. The filters (Section 5; Sections 2.3 and 7 for the carve-out): Table 5 (cascade) and Table 6 (loan exposure).

Carve-out: no Direct Loans disbursed in award years 2021-22 to 2025-26 (34 CFR 668.14(h)(3)(i)).
Yeshivas and rabbinical colleges in the federal files are identified by name (pattern below), excluding Yeshiva University.
Loan exposure: allocation = institution Direct Loans x program share of bachelor's completions; ceiling =
min(institution Direct Loans, min(estimated enrollment, undergraduate borrowers) x $12,500), with estimated enrollment =
four years of four-digit first-major bachelor's completions / completion rate (1/2 or 1/3). Completions: IPEDS 2021-22 + 2022-23.
"""
import numpy as np
import pandas as pd
import config as C
from common import save

fi = pd.read_csv(C.DER / "fsa_institutions.csv", dtype={"opeid6": str})
fi["nd"] = fi.no_dl_5y.astype(str).eq("True")
PAT = (r"YESHIVA|TALMUD|RABBINIC|RABBI\b|MESIVTA|MESIVTHA|MEDRASH|MIDRASH|MEDROSH|KOLLEL|KOLEL|TORAH|\bBETH\b|\bBAIS\b|\bBEIS\b"
       r"|\bBET\b|\bOHR\b|MECHON|MOSDOS|HADAS|HADATH|BINYOMIN|EISEK|MERCAZ")
fi["yeshiva_fsa"] = fi.school.str.contains(PAT, case=False, na=False, regex=True) & ~fi.school.eq("YESHIVA UNIVERSITY")
M = lambda x: round(x / 1e6, 1)

print("== Carve-out reach ==")
nd = fi[fi.nd]
print(f"all institutions with no Direct Loans in five years: {len(nd)}; Pell 2025-26 ${nd.pell_usd_2526.sum()/1e9:.2f}B")
y = fi[fi.yeshiva_fsa]
print(f"yeshivas and rabbinical colleges in the federal files: {len(y)}; outside the loan program: {int(y.nd.sum())}; "
      f"Pell 2025-26 ${M(y.pell_usd_2526.sum())}M")
sc = pd.read_csv(C.SCORECARD, dtype=str, low_memory=False); sc["opeid6"] = sc.OPEID6.str.zfill(6)
rb = sc[sc.CIPCODE.str[:2].isin(["38", "39"]) & (sc.CREDLEV == "3")][["opeid6"]].drop_duplicates().merge(fi, on="opeid6", how="left")
rb = rb[rb.state != "PR"]
rnd = rb[rb.nd == True]
print(f"institutions offering a religion bachelor's: {len(rb)}; no Direct Loans: {len(rnd)} with Pell ${M(rnd.pell_usd_2526.sum())}M; "
      f"of them yeshivas: {int(rnd.yeshiva_fsa.sum())} with ${M(rnd[rnd.yeshiva_fsa == True].pell_usd_2526.sum())}M")
print("  others:", "; ".join(rnd[rnd.yeshiva_fsa != True].school))
rb.to_csv(C.DER / "religion_ba_institutions.csv", index=False)

# ---------- Table 5: cascade ----------
ba = pd.read_csv(C.DER / "ba_robustness.csv", dtype={"CIPCODE": str, "opeid6": str})
ba["no_dl_5y"] = ba.no_dl_5y.astype(str).eq("True")
E = ba.earners4.sum()
f = ba[ba.fail_rule]
s1 = f[~f.no_dl_5y]
print(f"\n== Cascade == fail {len(f)} ({int(f.earners4.sum()):,} earners, {100*f.earners4.sum()/E:.1f}%); "
      f"carve-out removes {int(f.no_dl_5y.sum())} ({int(f[f.no_dl_5y].earners4.sum()):,} earners; "
      f"{100*f[f.no_dl_5y].earners4.sum()/f.earners4.sum():.0f}% of failing earners); Pell at those institutions "
      f"${M(f[f.no_dl_5y].drop_duplicates('opeid6').pell_usd_2526.sum())}M")
print(f"inside the loan program: {len(s1)} ({int(s1.earners4.sum())} earners, {100*s1.earners4.sum()/E:.1f}%)")
tested = s1[~((s1.INSTNM == "Mid-Atlantic Christian University") & (s1.CIPCODE == "3902"))]   # cohort floor (Section 5.3)
t5 = pd.DataFrame([
    ("Fail the earnings test", "-", len(f), int(f.earners4.sum()), round(100 * f.earners4.sum() / E, 1)),
    ("2. Inside the loan program", "Removed by the rule", len(s1), int(s1.earners4.sum()), round(100 * s1.earners4.sum() / E, 1)),
    ("3. Large enough to be tested", "Removed by the rule", len(tested), int(tested.earners4.sum()), round(100 * tested.earners4.sum() / E, 1)),
    ("4. Loan exposure", "Bounded, not removed", len(tested), int(tested.earners4.sum()), round(100 * tested.earners4.sum() / E, 1)),
    ("5. Folding into a passing program", "Possible response, lagged", len(tested), int(tested.earners4.sum()), round(100 * tested.earners4.sum() / E, 1))],
    columns=["filter", "kind", "programs", "earners", "pct_earners"])
save(t5, "table5_cascade.csv")

# Completions for the cohort floor and Table 6
cs = []
for fn in ["c2022_a_extract.csv", "c2023_a_extract.csv"]:
    c = pd.read_csv(C.IPEDS_DIR / fn, dtype={"CIPCODE": str}); c["year"] = fn[:5]; cs.append(c)
c = pd.concat(cs)
bach = c[(c.AWLEVEL == 5)]
first = bach[(bach.MAJORNUM == 1) & ~bach.CIPCODE.str.startswith("99")]
T6 = [("Appalachian Bible College", "39.02"), ("Mid-Atlantic Christian University", "39.02"), ("Crown College", "39.07"),
      ("Southeastern University", "39.07"), ("Bethany Global University", "39.03"), ("Crown College", "39.04"),
      ("Northpoint Bible College", "39.02"), ("Maranatha Baptist University", "39.07"), ("Boston Baptist College", "39.02")]
STUDENT_MAX, PARENT_MAX = 12500, 20000   # independent-undergraduate annual maximum; Parent PLUS annual cap from July 1, 2026
z = lambda v: float(np.nan_to_num(float(v)))
rows = []
for name, cip4 in T6:
    p = ba[(ba.INSTNM == name) & (ba.CIPCODE == cip4.replace(".", ""))].iloc[0]
    u = int(p.UNITID); i = fi[fi.opeid6 == p.opeid6].iloc[0]
    fu = first[first.UNITID == u]
    two = int(fu[fu.CIPCODE.str[:5] == cip4].CTOTALT.sum()); tot = int(fu.CTOTALT.sum())
    ug, pp, gr = z(i.ug_student_usd_2526), z(i.pplus_usd_2526), z(i.grad_usd_2526)
    dl, pell = z(i.dl_usd_2526), z(i.pell_usd_2526)
    aid = dl + pell
    alloc = (ug + pp) * two / tot
    r = dict(program=f"{name}, {cip4}", margin=round(p.margin_rule), ug_student_dl=ug, parent_plus=pp, graduate_dl=gr, aid=aid,
             two_yr_completions=two, bach_total_2yr=tot, alloc=alloc, alloc_pct=round(100 * alloc / aid, 1))
    for lab, rate in [("half", 1 / 2), ("third", 1 / 3)]:
        enroll = 2 * two / rate
        stu = min(ug, min(enroll, z(i.dl_ug_recip_2526)) * STUDENT_MAX)     # recipients summed across loan types: >= distinct borrowers
        par = min(pp, min(enroll, z(i.pplus_recip_2526)) * PARENT_MAX)
        r[f"ceiling_{lab}_student"] = stu; r[f"ceiling_{lab}_parent"] = par
        r[f"ceiling_{lab}"] = stu + par; r[f"ceiling_{lab}_pct"] = round(100 * (stu + par) / aid, 1)
    rows.append(r)
t6 = pd.DataFrame(rows)
save(t6, "table6_loan_exposure.csv")
k = lambda c: (t6[c] / 1e3).round(0)
print(t6[["program", "margin"]].assign(ug=k("ug_student_dl"), pplus=k("parent_plus"), grad=k("graduate_dl"), aid=k("aid"), alloc=k("alloc"),
      alloc_pct=t6.alloc_pct, c2=k("ceiling_half"), c2s=k("ceiling_half_student"), c2p=k("ceiling_half_parent"), c2pct=t6.ceiling_half_pct,
      c3=k("ceiling_third"), c3pct=t6.ceiling_third_pct).to_string(index=False))

# The ten failing institutions outside the loan program: evidence and what is at stake (Section 5.2)
br = None
ten = f[f.no_dl_5y].copy()
ten = ten.merge(fi[["opeid6", "years_in_dl_report", "pell_recip_2526"]], on="opeid6", how="left")
t5b = ten[["INSTNM", "CIPCODE", "earners4", "years_in_dl_report", "pell_recip_2526", "pell_usd_2526"]].rename(columns={"pell_usd_2526": "pell_usd_2526"})
save(t5b, "tableA2_carveout_institutions.csv")
print(t5b.to_string(index=False))
print(f"Pell 2025-26 at the ten: ${t5b.pell_usd_2526.sum()/1e6:.1f}M")

# Cohort floor, Mid-Atlantic Christian 39.02 (Section 5.3)
u = int(ba[(ba.INSTNM == "Mid-Atlantic Christian University") & (ba.CIPCODE == "3902")].UNITID.iloc[0])
m = bach[(bach.UNITID == u) & (bach.CIPCODE.str[:5] == "39.02")].groupby(["year", "MAJORNUM"]).CTOTALT.sum()
print("\nMid-Atlantic 39.02 bachelor's completions by year and major:", m.to_dict())

# New York Theological Seminary: Direct Loan years (Section 5.2)
panel = pd.read_csv(C.DER / "fsa_panel.csv", dtype={"opeid6": str, "year": str})
g = pd.read_csv(C.DER / "grad_programs_scored.csv", dtype={"opeid6": str})
o = g[g.INSTNM == "New York Theological Seminary"].opeid6.iloc[0]
print("NYTS Direct Loans by year:", panel[panel.opeid6 == o].set_index("year").dl_usd.to_dict())
