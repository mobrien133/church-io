"""Step 8. Table 8 and Section 5.5: breadth of the catalog at every credential level and the failing share of completions.

Programs: six-digit CIP by award level with at least one first-major completion, IPEDS 2021-22 and 2022-23. The completions
share of failing programs (CIP 38-39 bachelor's programs below the rule's threshold, completions at the four-digit level)
proxies the share of aid recipients in the administrative-capability test (34 CFR 668.16(t))."""
import pandas as pd
from scipy.stats import spearmanr
import config as C
from common import save

cs = []
for f in ["c2022_a_extract.csv", "c2023_a_extract.csv"]:
    c = pd.read_csv(C.IPEDS_DIR / f, dtype={"CIPCODE": str})
    cs.append(c[(c.MAJORNUM == 1) & ~c.CIPCODE.str.startswith("99")])
c = pd.concat(cs); c["CIPCODE"] = c.CIPCODE.str.strip()
g = c.groupby(["UNITID", "CIPCODE", "AWLEVEL"], as_index=False).CTOTALT.sum()
g = g[g.CTOTALT > 0]
inst = g.groupby("UNITID").agg(n_prog_all=("CIPCODE", "size"), compl_all=("CTOTALT", "sum"))
bach = g[g.AWLEVEL == 5].groupby("UNITID").agg(n_prog_ba=("CIPCODE", "size"), compl_ba=("CTOTALT", "sum"))
lev = g.groupby("UNITID").AWLEVEL.apply(lambda s: ",".join(str(x) for x in sorted(s.unique())))
r = pd.read_csv(C.DER / "ba_robustness.csv", dtype={"CIPCODE": str})
r = r.dropna(subset=["UNITID"]); r["UNITID"] = r.UNITID.astype(int)
r["cip4"] = r.CIPCODE.str[:2] + "." + r.CIPCODE.str[2:]
b4 = g[g.AWLEVEL == 5].copy(); b4["cip4"] = b4.CIPCODE.str[:5]
b4 = b4.groupby(["UNITID", "cip4"], as_index=False).CTOTALT.sum().rename(columns={"CTOTALT": "prog_compl"})
r = r.merge(b4, on=["UNITID", "cip4"], how="left")
fail = r[r.fail_rule].groupby("UNITID").agg(fail_compl=("prog_compl", "sum"), name=("INSTNM", "first"))
I = pd.DataFrame({"UNITID": r.UNITID.unique()}).set_index("UNITID").join(inst).join(bach).join(fail).join(lev.rename("levels"))
I["fail_compl"] = I.fail_compl.fillna(0)
I["fail_share_all"] = I.fail_compl / I.compl_all
I = I.join(r.groupby("UNITID").margin_rule.min().rename("worst")).join(r.groupby("UNITID").yeshiva.first())
I["failing"] = I.index.isin(r[r.fail_rule].UNITID)
I["name"] = I.name.fillna(r.groupby("UNITID").INSTNM.first())
bucket = lambda n: "1" if n == 1 else "2-3" if n <= 3 else "4-10" if n <= 10 else "11-30" if n <= 30 else "31 or more"
I["bucket"] = I.n_prog_all.apply(bucket)
I.to_csv(C.DER / "breadth_all_levels.csv")
t = I.groupby("bucket").agg(institutions=("failing", "size"), with_failing=("failing", "sum"),
                            failing_over_half=("fail_share_all", lambda s: int((s > 0.5).sum())),
                            nonyeshiva=("yeshiva", lambda s: int((~s.astype(bool)).sum())),
                            nonyeshiva_failing=("failing", lambda s: int((s & ~I.loc[s.index, "yeshiva"].astype(bool)).sum())))
t = t.reindex(["1", "2-3", "4-10", "11-30", "31 or more"])
save(t, "table8_breadth.csv", index=True)
print(t.to_string())
print("institutions:", len(I))
print(I[I.failing].sort_values("fail_share_all", ascending=False)[["name", "n_prog_all", "levels", "compl_all", "fail_compl", "fail_share_all"]].round(3).to_string())
ny = I[~I.yeshiva.astype(bool)]
print("Spearman, worst margin vs programs at all levels (non-yeshiva):", spearmanr(ny.worst, ny.n_prog_all))
print("Spearman, worst margin vs bachelor's programs (non-yeshiva):", spearmanr(ny.worst, ny.n_prog_ba))
