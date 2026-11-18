"""Step 10. Appendix Table A1 and Section 5: the religion bachelor's universe and the unreported programs."""
import numpy as np
import pandas as pd
import config as C
from common import raw_scorecard, thresholds, save

TH = thresholds()
b = raw_scorecard()
b = b[(b.CREDLEV == "3") & b.CIPCODE.str[:2].isin(["38", "39"])].copy()
fi = pd.read_csv(C.DER / "fsa_institutions.csv", dtype={"opeid6": str})
b = b.merge(fi[["opeid6", "state", "no_dl_5y", "dl_usd_2526"]], on="opeid6", how="left")
n0 = len(b); b = b[b.state != "PR"]; n1 = len(b)
for col in ["IPEDSCOUNT1", "IPEDSCOUNT2"]:
    b[col] = pd.to_numeric(b[col], errors="coerce")
b["two"] = b.IPEDSCOUNT1.fillna(0) + b.IPEDSCOUNT2.fillna(0)
g = b.groupby(["opeid6", "CIPCODE"]).agg(INSTNM=("INSTNM", "first"), state=("state", "first"),
                                         nodl=("no_dl_5y", lambda s: str(s.iloc[0]) == "True"), two=("two", "sum"),
                                         earn4=("earn4", "max"), earn1=("earn1", "max")).reset_index()
g["cat"] = np.where(g.earn4.notna(), "reported", np.where(g.two >= 15, "unreported, potentially testable", "unreported, unlikely testable"))
t = g.groupby("cat").agg(programs=("cat", "size"), awards=("two", "sum"), noDL_programs=("nodl", "sum"))
t["noDL_awards"] = [g[(g.cat == k) & g.nodl].two.sum() for k in t.index]
t["share_awards"] = (100 * t.awards / t.awards.sum()).round(1)
flow = pd.DataFrame([("Scorecard records, CIP 38-39 bachelor's", n0), ("Excluding Puerto Rico", n1),
                     ("Programs (OPEID6 x CIP)", len(g)), ("Earnings reported", int(g.earn4.notna().sum())),
                     ("Scored: reported, with a U.S. state threshold", int((g.earn4.notna() & g.state.notna()).sum()))],
                    columns=["step", "programs"])
save(flow, "tableA1_flow.csv"); save(t, "tableA1_categories.csv", index=True)
print(flow.to_string(index=False)); print(t.to_string())
u = g[(g.cat == "unreported, potentially testable") & ~g.nodl]
thmax = u.state.map(TH).fillna(C.NATIONAL_HS).clip(lower=C.NATIONAL_HS)
print(f"unreported, potentially testable, inside the loan program: {len(u)} ({100*u.two.sum()/g.two.sum():.1f}% of awards); "
      f"one-year earnings reported {int(u.earn1.notna().sum())}: pass {int((u.earn1 >= thmax).sum())}, below {int((u.earn1 < thmax).sum())}")
print(u[u.earn1 < thmax][["INSTNM", "CIPCODE", "earn1"]].sort_values("earn1").to_string(index=False))
c39 = g[g.CIPCODE.str[:2] == "39"]
print(f"CIP 39: {len(c39)} programs; testable after pooling {int((c39.two >= 15).sum())}; not {int((c39.two < 15).sum())}, "
      f"{100*c39[c39.two < 15].two.sum()/c39.two.sum():.0f}% of awards")
g.to_csv(C.DER / "universe_38_39_ba.csv", index=False)
