"""Step 3. Score programs against the rule's comparators (Sections 4.1-4.2; Tables 2 and 3; Figure 1 inputs).

Bachelor's: 2024 state high-school-only threshold, or the national $31,269 where fewer than half of the institution's
first-time students are from its state (IPEDS EF2022C).
Graduate (CIP 39.06, master's and first-professional): lowest of three bachelor's-only ACS medians -- state all fields,
state same field (one dollar if the ACS cell has fewer than 16 observations), national same field ($45,000). Graduate
residence is not observed, so each program is also scored against the national comparators alone ($45,000).
"""
import numpy as np
import pandas as pd
import config as C
from common import programs, religion_ba, save

sc = programs()
sc.to_pickle(C.DER / "programs.pkl")

# ---------------- Bachelor's ----------------
ba = religion_ba(sc)
ba.to_csv(C.DER / "religion_ba_scored.csv", index=False,
          columns=["INSTNM", "opeid6", "UNITID", "CIPCODE", "state", "instate", "earn4", "earners4", "earn1", "th", "th_rule",
                   "margin_rule", "fail_state", "fail_rule", "fail10_state", "fail10_rule", "yeshiva", "polity", "sponsoring_body",
                   "no_dl_5y", "dl_usd_2526", "pell_usd_2526", "dl_ug_recip_2526"])
f = ba.fail_rule
print(f"religion BA programs scored: {len(ba)}; fail {int(f.sum())} ({100*ba.earners4[f].sum()/ba.earners4.sum():.1f}% of earners); "
      f"fail or within 10%: {int(ba.fail10_rule.sum())}; earners {int(ba.earners4.sum()):,}")
print(f"in-state share between 0.40 and 0.60: {int(ba.instate.between(0.4, 0.6).sum())}")
c39 = ba[ba.CIPCODE.str.startswith("39")]; m39 = c39.earn4 - c39.th_rule
print(f"CIP 39: {len(c39)} programs; median margin {m39.median():,.0f}; margin < $10,000: {int((m39 < 10000).sum())}; "
      f"failing share of earners {100*c39.earners4[c39.fail_rule].sum()/c39.earners4.sum():.1f}%")
c3802 = ba[ba.CIPCODE == "3802"]
print(f"CIP 38.02: failing share of earners {100*c3802.earners4[c3802.fail_rule].sum()/c3802.earners4.sum():.1f}%")

# Table 3: by field, religion fields at the rule threshold, comparison fields at state thresholds
FIELDS = [("3801", "Philosophy"), ("3802", "Religion/Religious Studies"), ("3902", "Bible/Biblical Studies"), ("3903", "Missions"),
          ("3904", "Religious Education"), ("3906", "Theological/Ministerial Studies"), ("3907", "Pastoral Counseling"),
          ("4201", "Psychology, General"), ("4407", "Social Work"), ("4511", "Sociology")]
rows = []
for cip, name in FIELDS:
    x = sc[(sc.CIPCODE == cip) & (sc.CREDLEV == "3")]
    r = x[x.earn4.notna() & x.th.notna()]
    th = r.th_rule if cip[:2] in ("38", "39") else r.th
    fl = r.earn4 < th
    rows.append(dict(cip=f"{cip[:2]}.{cip[2:]}", field=name, programs_offered=len(x), reported=len(r), median=r.earn4.median(),
                     fail=int(fl.sum()), fail_pct_earners=round(100 * r.earners4[fl].sum() / r.earners4.sum(), 1)))
save(pd.DataFrame(rows), "table3_ba_by_field.csv")

# ---------------- Graduate: CIP 39.06 at the master's and first-professional levels ----------------
acs49 = pd.read_csv(C.ACS / "acs_field_49_by_state.csv").set_index("state")
allba = pd.read_csv(C.ACS / "acs_all_ba_by_state.csv").set_index("state")["median"]
g = sc[(sc.CIPCODE == "3906") & sc.CREDLEV.isin(["5", "7"]) & sc.earn4.notna()].copy()
g["sf"] = g.state.map(lambda s: (1.0 if acs49.loc[s, "n"] < 16 else acs49.loc[s, "median"]) if s in acs49.index else np.nan)
g["ab"] = g.state.map(allba)
g["comp_national"] = C.THEOLOGY_BA_NATIONAL                         # min(national all-BA $59,539, national field $45,000)
g["comp_instate"] = g[["sf", "ab", "comp_national"]].min(axis=1)     # lowest of three; national where state unknown
g["fail_national"] = g.earn4 < g.comp_national
g["fail_instate"] = g.earn4 < g.comp_instate

# Six-digit composition from IPEDS graduate completions (first major, award levels 7, 8, 17, 18, 19), 2021-22 and 2022-23
cs = []
for f in ["c2022_a_extract.csv", "c2023_a_extract.csv"]:
    c = pd.read_csv(C.IPEDS_DIR / f, dtype={"CIPCODE": str})
    cs.append(c[(c.MAJORNUM == 1) & c.AWLEVEL.isin([7, 8, 17, 18, 19]) & c.CIPCODE.str.startswith("39.06")])
c = pd.concat(cs).groupby(["UNITID", "CIPCODE"]).CTOTALT.sum().unstack(fill_value=0)
g["UNITID"] = pd.to_numeric(g.UNITID, errors="coerce")
g = g.merge(c, left_on="UNITID", right_index=True, how="left")
six = [k for k in c.columns]
g["tot"] = g[six].sum(axis=1)
g["sh0602"] = np.where(g.tot > 0, g.get("39.0602", 0) / g.tot.replace(0, np.nan), np.nan)
g["type"] = np.select([g.tot.fillna(0) == 0, g.sh0602 >= 0.5], ["no recent completions", "mostly MDiv (39.0602)"], "mostly other theology")
keep = ["INSTNM", "opeid6", "UNITID", "state", "CREDDESC", "earn4", "earners4", "sf", "ab", "comp_national", "comp_instate",
        "fail_national", "fail_instate", "polity", "sponsoring_body", "no_dl_5y", "tot", "sh0602", "type"]
g[keep].sort_values("earn4").to_csv(C.DER / "grad_programs_scored.csv", index=False)

q = g.earn4.quantile([.1, .25, .5, .75, .9])
t2 = pd.DataFrame([
    ("Programs reported", len(g)),
    ("Median of program medians", f"{q[.5]:,.0f}"),
    ("10th / 25th / 75th / 90th percentile", " / ".join(f"{q[p]:,.0f}" for p in [.1, .25, .75, .9])),
    ("Same-field comparator, national (ACS 2019-23)", f"{C.THEOLOGY_BA_NATIONAL:,.0f}"),
    ("Programs below national comparator (share of earners)",
     f"{int(g.fail_national.sum())} ({100*g.earners4[g.fail_national].sum()/g.earners4.sum():.1f}%)"),
    ("Mostly MDiv / mostly other theology / no recent completions",
     " / ".join(str(int((g.type == t).sum())) for t in ["mostly MDiv (39.0602)", "mostly other theology", "no recent completions"])),
    ("Programs below in-state lowest-of-three comparator (share of earners)",
     f"{int(g.fail_instate.sum())} ({100*g.earners4[g.fail_instate].sum()/g.earners4.sum():.1f}%)"),
], columns=["item", "value"])
save(t2, "table2_graduate_theology.csv")
print(f"graduate: {len(g)} programs; in-state comparator below $45,000 for {int(((g.comp_instate > 1) & (g.comp_instate < 45000)).sum())}, "
      f"one dollar for {int((g.comp_instate <= 1).sum())}")
print(g.groupby("type").earn4.median().round(0).to_string())
print(g[g.fail_national][["INSTNM", "state", "earn4", "earners4", "type", "sh0602"]].to_string(index=False))
