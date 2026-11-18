"""Step 1. Build OPEID6-level Direct Loan and Pell panel (AY2021-22 .. AY2025-26) from FSA Title IV volume files."""
import pandas as pd
import numpy as np
import config as C

YEARS = C.FSA_YEARS


def num(s):
    return pd.to_numeric(s.replace({"-": np.nan, " - ": np.nan}), errors="coerce")


def load_dl(y):
    d = pd.read_excel(C.FSA_DIR / f"dl_{y}.xls", sheet_name="Award Year Summary", header=None, skiprows=7, dtype=str)
    d = d.iloc[:, :30]
    d.columns = (["opeid", "school", "state", "zip", "type"]
                 + [f"{p}_{m}" for p in ["sub", "unsub_ug", "unsub_gr", "pplus", "gplus"]
                    for m in ["recip", "n_orig", "usd_orig", "n_disb", "usd_disb"]])
    d = d[d.opeid.notna() & d.opeid.str.match(r"^\d{8}$")]
    for c in d.columns[5:]:
        d[c] = num(d[c])
    d["dl_recip"] = d[[f"{p}_recip" for p in ["sub", "unsub_ug", "unsub_gr", "pplus", "gplus"]]].sum(axis=1, min_count=1)
    d["dl_usd"] = d[[f"{p}_usd_disb" for p in ["sub", "unsub_ug", "unsub_gr", "pplus", "gplus"]]].sum(axis=1, min_count=1)
    d["dl_ug_recip"] = d[["sub_recip", "unsub_ug_recip"]].sum(axis=1, min_count=1)
    d["opeid6"] = d.opeid.str[:6]
    g = d.groupby("opeid6").agg(school=("school", "first"), state=("state", "first"), type=("type", "first"),
                                dl_recip=("dl_recip", "sum"), dl_usd=("dl_usd", "sum"), dl_ug_recip=("dl_ug_recip", "sum"))
    g["year"] = y
    return g.reset_index()


def load_gr(y):
    d = pd.read_excel(C.FSA_DIR / f"gr_{y}.xls", sheet_name="Award Year Summary", header=None, skiprows=7, dtype=str)
    d = d.iloc[:, :9]
    d.columns = ["opeid", "school", "state", "zip", "type", "pell_recip", "pell_usd", "teach_recip", "teach_usd"]
    d = d[d.opeid.notna() & d.opeid.str.match(r"^\d{8}$")]
    for c in ["pell_recip", "pell_usd"]:
        d[c] = num(d[c])
    d["opeid6"] = d.opeid.str[:6]
    g = d.groupby("opeid6").agg(school=("school", "first"), state=("state", "first"), type=("type", "first"),
                                pell_recip=("pell_recip", "sum"), pell_usd=("pell_usd", "sum"))
    g["year"] = y
    return g.reset_index()


dl = pd.concat([load_dl(y) for y in YEARS], ignore_index=True)
gr = pd.concat([load_gr(y) for y in YEARS], ignore_index=True)
panel = pd.merge(dl, gr, on=["opeid6", "year"], how="outer", suffixes=("", "_g"))
for c in ["school", "state", "type"]:
    panel[c] = panel[c].fillna(panel[c + "_g"])
panel = panel.drop(columns=[c for c in panel.columns if c.endswith("_g")])
panel.to_csv(C.DER / "fsa_panel.csv", index=False)
print("panel rows:", len(panel), " institutions:", panel.opeid6.nunique())
print(panel.groupby("year")[["dl_recip", "dl_usd", "pell_recip", "pell_usd"]].sum().to_string())

# institution-level summary: any DL in 5 years; latest-year Pell/DL
inst = panel.groupby("opeid6").agg(school=("school", "first"), state=("state", "first"), type=("type", "first"),
                                   dl_recip_5y=("dl_recip", "sum"), dl_usd_5y=("dl_usd", "sum"),
                                   years_with_dl=("dl_usd", lambda s: int((s.fillna(0) > 0).sum())),
                                   pell_recip_5y=("pell_recip", "sum"), pell_usd_5y=("pell_usd", "sum"))
latest = panel[panel.year == "2526"].set_index("opeid6")[["dl_recip", "dl_usd", "dl_ug_recip", "pell_recip", "pell_usd"]].add_suffix("_2526")
inst = inst.join(latest)
inst["no_dl_5y"] = inst.years_with_dl == 0
inst.to_csv(C.DER / "fsa_institutions.csv")
print("institutions with no DL in any of 5 years:", int(inst.no_dl_5y.sum()), "of", len(inst))

# Carve-out reach (Sections 2.3 and 5.2): all institutions with no Direct Loans in five years
nd = inst[inst.no_dl_5y]
print(f"no-DL institutions: {len(nd)}; their Pell 2025-26: ${nd.pell_usd_2526.sum()/1e9:.2f}B")
