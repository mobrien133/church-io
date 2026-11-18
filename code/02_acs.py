"""Step 2 (optional). ACS 2019-23 statistics from the IPUMS USA microdata extract.

IPUMS terms do not allow the microdata to be redistributed, so the outputs of this step are committed in data/acs/ and
every later step reads them from there. If the extract is present at data/raw/ipums/usa_00003.csv.gz, this script
recomputes them; otherwise it checks that the committed files exist and exits.

Population (34 CFR 668.2 and 91 FR 21138-42): ages 25-34, in the labor force (LABFORCE 2), not enrolled (SCHOOL 1),
person-weighted; earnings = INCEARN (wages plus self-employment). Clergy: OCC 2040 or OCCSOC 2120xx.

Outputs (data/acs/):
  acs_state_hs_thresholds.csv   high-school-only medians by state vs 89 FR 107130 (validation; Section 3.1)
  acs_field_comparators.csv     bachelor's-only medians by degree field, national; cells < 16 by state
  acs_field_<code>_by_state.csv bachelor's-only medians by state and field
  acs_all_ba_by_state.csv       bachelor's-only medians by state, all fields
  acs_theology_clergy.csv       clergy share and earnings, theology bachelor's holders
  h7_bounds_acs_shifts.csv      median shifts when the housing allowance is added or stripped (Table 4, rows 2-5)
  acs_naive_sum_shifts.csv      median shifts from a naive W-2 + Schedule SE sum (Table 4, rows 6-9)
  acs_dispersion.csv            dispersion of log earnings by field (Table 7 grid)
  acs_misc.csv                  clergy shares and the clergy median used in Section 4.3
"""
import sys
import numpy as np
import pandas as pd
import config as C

if not C.IPUMS_EXTRACT.exists():
    need = ["acs_field_49_by_state.csv", "acs_all_ba_by_state.csv", "h7_bounds_acs_shifts.csv", "acs_naive_sum_shifts.csv",
            "acs_dispersion.csv", "acs_misc.csv"]
    missing = [f for f in need if not (C.ACS / f).exists()]
    if missing:
        sys.exit(f"IPUMS extract not found and committed ACS outputs missing: {missing}")
    print("IPUMS extract not present; using the committed ACS outputs in data/acs/.")
    sys.exit(0)

cols = ["AGE", "STATEFIP", "EDUCD", "DEGFIELD", "SCHOOL", "LABFORCE", "CLASSWKR", "OCC", "OCCSOC", "INCWAGE", "INCBUS00", "INCEARN", "PERWT"]
df = pd.read_csv(C.IPUMS_EXTRACT, usecols=lambda c: c in cols, low_memory=False)
df = df[df.AGE.between(25, 34)]
FIPS = {1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI", 16: "ID", 17: "IL",
        18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA", 23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS", 29: "MO", 30: "MT",
        31: "NE", 32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK", 41: "OR", 42: "PA", 44: "RI",
        45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY", 72: "PR"}
df["state"] = df.STATEFIP.map(FIPS)
inlf = (df.LABFORCE == 2) & (df.SCHOOL == 1)
L = df[inlf].copy()
L["clergy"] = (L.OCC == 2040) | (L.OCCSOC.astype(str).str.startswith("2120"))


def wmed(v, w):
    v = np.asarray(v, float); w = np.asarray(w, float)
    if len(v) == 0:
        return np.nan
    o = np.argsort(v); v, w = v[o], w[o]; c = np.cumsum(w)
    return float(v[np.searchsorted(c, c[-1] / 2)])


def wq(v, w, q):
    v = np.asarray(v, float); w = np.asarray(w, float); o = np.argsort(v); v, w = v[o], w[o]; c = np.cumsum(w)
    return float(v[np.searchsorted(c, q * c[-1])])


# 1. High-school-only medians vs the Department's 2024 thresholds
TH = pd.read_csv(C.THRESHOLDS).set_index("state").threshold_2024
hs = L[L.EDUCD.isin([63, 64])]
rows = [dict(state=st, n=len(g), median=wmed(g.INCEARN, g.PERWT)) for st, g in hs.groupby("state")]
rows.append(dict(state="US", n=len(hs), median=wmed(hs.INCEARN, hs.PERWT)))
t = pd.DataFrame(rows); t["fr2024"] = t.state.map(TH); t["ratio"] = t["median"] / t.fr2024
t.to_csv(C.ACS / "acs_state_hs_thresholds.csv", index=False)
print("HS-only median ratio to 89 FR 107130:", round(t.ratio.median(), 3))

# 2. Bachelor's-only comparators by field, state and national; n < 16 rule
ba = L[L.EDUCD == 101]
fields = {49: "Theology and Religious Vocations", 48: "Philosophy and Religious Studies", 52: "Psychology",
          54: "Public Affairs/Policy/Social Work", 55: "Social Sciences", 61: "Medical and Health Sciences"}
out = []
for code, name in fields.items():
    f = ba[ba.DEGFIELD == code]
    cells = pd.DataFrame([(st, len(g), wmed(g.INCEARN, g.PERWT)) for st, g in f.groupby("state")], columns=["state", "n", "median"])
    cells.assign(degfield=code).to_csv(C.ACS / f"acs_field_{code}_by_state.csv", index=False)
    out.append(dict(degfield=code, field=name, national_n=len(f), national_median=wmed(f.INCEARN, f.PERWT),
                    states_with_cell_lt16=int((cells.n < 16).sum()), states_total=len(cells)))
pd.DataFrame(out).to_csv(C.ACS / "acs_field_comparators.csv", index=False)
allba = pd.DataFrame([dict(state=st, n=len(g), median=wmed(g.INCEARN, g.PERWT)) for st, g in ba.groupby("state")])
allba.to_csv(C.ACS / "acs_all_ba_by_state.csv", index=False)
print("national theology bachelor's median:", out[0]["national_median"], "n =", out[0]["national_n"],
      "| national all-bachelor's:", wmed(ba.INCEARN, ba.PERWT))
th = ba[ba.DEGFIELD == 49]
pd.DataFrame([dict(n=len(th), clergy_share=(th.clergy * th.PERWT).sum() / th.PERWT.sum(),
                   med_clergy=wmed(th.INCEARN[th.clergy], th.PERWT[th.clergy]),
                   med_nonclergy=wmed(th.INCEARN[~th.clergy], th.PERWT[~th.clergy]))]).to_csv(C.ACS / "acs_theology_clergy.csv", index=False)

# 3. Housing-allowance shifts. Allowance s as a share of W-2 wages; one-third of clergy opted out of Social Security.
groups = {"BA field 49 (theology)": (L.EDUCD == 101) & (L.DEGFIELD == 49),
          "BA field 48 (phil/relig)": (L.EDUCD == 101) & (L.DEGFIELD == 48),
          "Grad, BA field 49": L.EDUCD.isin([114, 115, 116]) & (L.DEGFIELD == 49)}
rows, naive, misc = [], [], []
OPT = 1 / 3
for g, m in groups.items():
    t = L[m]; cl = t.clergy
    base = wmed(t.INCEARN, t.PERWT); share = float((cl * t.PERWT).sum() / t.PERWT.sum())
    misc.append(dict(item=f"clergy share, {g}", value=round(share, 3)))
    for s in [0.15, 0.50]:
        for opt in [0.0, OPT]:
            x = s * (1 - opt)
            up = wmed(t.INCEARN.where(~cl, t.INCEARN * (1 + x)), t.PERWT)
            dn = wmed(t.INCEARN.where(~cl, t.INCEARN / (1 + x)), t.PERWT)
            rows.append(dict(group=g, n=len(t), clergy_share=round(share, 3), base=base, s=s, opt=round(opt, 2), x=round(x, 3),
                             up_pct=round(up / base - 1, 4), dn_pct=round(dn / base - 1, 4)))
        # naive sum: SE-tax-paying clergy record (2+s)W, netted (1+s)W, W-2-only W; opted-out clergy W throughout
        a = t[~cl]; c = t[cl]

        def med_under(factor):
            v = np.concatenate([a.INCEARN, c.INCEARN * factor, c.INCEARN])
            w = np.concatenate([a.PERWT, c.PERWT * (1 - OPT), c.PERWT * OPT])
            return wmed(v, w)
        m_w, m_net, m_sum = med_under(1.0), med_under(1 + s), med_under(2 + s)
        naive.append(dict(group=g, s=s, W2_only=m_w, netted=m_net, naive_sum=m_sum, sum_to_netted=round(m_net / m_sum - 1, 3),
                          sum_to_W2=round(m_w / m_sum - 1, 3), netted_to_W2=round(m_w / m_net - 1, 3)))
pd.DataFrame(rows).to_csv(C.ACS / "h7_bounds_acs_shifts.csv", index=False)
pd.DataFrame(naive).to_csv(C.ACS / "acs_naive_sum_shifts.csv", index=False)

# 4. Clergy with graduate degrees, ages 27 and over in the extract (27-34), for the Section 4.3 comparison
g = L[L.EDUCD.isin([114, 115, 116]) & L.clergy & L.AGE.between(27, 34)]
misc.append(dict(item="median earnings, clergy with graduate degrees, ages 27-34", value=wmed(g.INCEARN, g.PERWT)))
pd.DataFrame(misc).to_csv(C.ACS / "acs_misc.csv", index=False)

# 5. Dispersion of log earnings, young bachelor's holders with positive earnings (Section 5.5)
pos = ba[ba.INCEARN > 0]
disp = []
for f, name in [(49, "theology"), (52, "psychology"), (54, "public affairs/social work"), (48, "phil/relig")]:
    s = pos[pos.DEGFIELD == f]
    iqr = np.log(wq(s.INCEARN, s.PERWT, .75)) - np.log(wq(s.INCEARN, s.PERWT, .25))
    disp.append(dict(field=name, n=len(s), iqr_sigma=round(iqr / 1.349, 2)))
pd.DataFrame(disp).to_csv(C.ACS / "acs_dispersion.csv", index=False)
print(pd.DataFrame(disp).to_string(index=False))
print(pd.DataFrame(misc).to_string(index=False))
