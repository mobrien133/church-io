"""Step 9. Section 6.2: polity of the sponsoring body, earnings given the credential, and where exposed programs sit."""
import numpy as np
import pandas as pd
from scipy import stats
import config as C
from common import POLITY_LABELS as LAB

g = pd.read_csv(C.DER / "grad_programs_scored.csv")
print("graduate theology programs:", len(g), "uncoded:", int(g.polity.isna().sum()))
a = g[g.polity.isin(["E", "C"])]; b = g[g.polity.isin(["G", "M"])]
d_mean = a.earn4.mean() - b.earn4.mean()
se = np.sqrt(a.earn4.var() / len(a) + b.earn4.var() / len(b))
print(f"E+C n={len(a)} median {a.earn4.median():,.0f}; G+M n={len(b)} median {b.earn4.median():,.0f}")
print(f"difference in means {d_mean:,.0f} (95% CI {d_mean-1.96*se:,.0f} to {d_mean+1.96*se:,.0f}); "
      f"minimum detectable difference at 80% power {2.8*se:,.0f} ({100*2.8*se/g.earn4.median():.1f}% of the median)")
rng = np.random.default_rng(C.SEED); E = np.concatenate([a.earn4.values, b.earn4.values]); na = len(a); R = 20000
obs = abs(a.earn4.median() - b.earn4.median()); cnt = 0
for _ in range(R):
    i = rng.permutation(len(E)); cnt += abs(np.median(E[i[:na]]) - np.median(E[i[na:]])) >= obs
print(f"permutation p (difference in medians) = {cnt/R:.2f}; Mann-Whitney p = {stats.mannwhitneyu(a.earn4, b.earn4).pvalue:.2f}; "
      f"Kruskal-Wallis (five classes) p = {stats.kruskal(*[x.earn4 for _, x in g.groupby('polity')]).pvalue:.2f}")

ba = pd.read_csv(C.DER / "ba_robustness.csv", dtype={"CIPCODE": str})
c39 = ba[ba.CIPCODE.str.startswith("39")]
hb, lb = c39[c39.polity.isin(["E", "C"])].earn4.median(), c39[c39.polity.isin(["G", "M"])].earn4.median()
x, y = c39[c39.polity.isin(["E", "C"])].earn4.values, c39[c39.polity.isin(["G", "M"])].earn4.values
E2 = np.concatenate([x, y]); obs2 = abs(np.median(x) - np.median(y)); cnt2 = 0
for _ in range(R):
    i = rng.permutation(len(E2)); cnt2 += abs(np.median(E2[i[:len(x)]]) - np.median(E2[i[len(x):]])) >= obs2
print(f"bachelor's CIP 39, median difference (E+C minus G+M): {hb-lb:,.0f}; permutation p = {cnt2/R:.2f}; "
      f"Mann-Whitney p = {stats.mannwhitneyu(x, y).pvalue:.2f}")
sc = pd.read_pickle(C.DER / "programs.pkl")
allb = sc[sc.CIPCODE.str.startswith("39") & (sc.CREDLEV == "3")]
print("ministry bachelor's programs offered, by polity:", allb.polity.map(LAB).fillna("uncoded").value_counts().to_dict())
print("failing CIP 39 by polity:", c39[c39.fail_rule][["INSTNM", "polity"]].values.tolist())
print("at or within 10% of the line:", c39[c39.fail10_rule][["INSTNM", "polity"]].values.tolist())
e = g.earn4 * 0.84 < g.comp_national
print("graduate failures at a 16% shift by polity:", g[e].polity.value_counts().to_dict(), "of", g.polity.value_counts().to_dict())
