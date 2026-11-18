"""Step 7. Table 7: pooled medians when a failing program is folded into a passing neighbor (Section 5.5).

Each program's earnings are lognormal around its Scorecard median, with dispersion sigma drawn independently from the
grid {0.3, 0.5, 0.7, 0.9, 1.2}; the pooled median is solved numerically for every combination (Cartesian product).
The grid brackets the IQR-implied dispersion of young bachelor's holders' log earnings in the ACS (data/acs/acs_dispersion.csv)."""
import itertools
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
import config as C
from common import save

GRID = [0.3, 0.5, 0.7, 0.9, 1.2]


def pooled_median(comps, sigs):
    N = sum(n for _, n in comps)
    f = lambda x: sum(n * norm.cdf((np.log(x) - np.log(m)) / s) for (m, n), s in zip(comps, sigs)) / N - 0.5
    return brentq(f, 1e3, 1e6)


# (median, earners) from the Scorecard; thresholds from 89 FR 107130 or the national figure
cases = {
    "Crown 39.07 -> Bible 39.02 (MN 34,795)": ([(32718, 26), (46800, 64)], 34795),
    "Crown 39.07 -> Psych 42.01+42.28 (MN 34,795)": ([(32718, 26), (48095, 20), (60077, 25)], 34795),
    "Crown 39.07 -> Psych 42.01 only (MN 34,795)": ([(32718, 26), (48095, 20)], 34795),
    "Crown 39.07 + 39.04 -> Bible 39.02 (MN 34,795)": ([(32718, 26), (36826, 38), (46800, 64)], 34795),
    "Maranatha 39.07 -> Bible 39.02 (WI 33,397)": ([(36728, 16), (53966, 16)], 33397),
    "Maranatha 39.07 -> Bible 39.02 (national 31,269)": ([(36728, 16), (53966, 16)], 31269),
    "Southeastern 39.07 -> 39.06 (national 31,269)": ([(30430, 17), (44106, 29)], 31269),
    "Southeastern 39.07 -> Psych 42.01 (national 31,269)": ([(30430, 17), (48011, 39)], 31269),
}
rows = []
for k, (c, t) in cases.items():
    vals = [pooled_median(c, s) for s in itertools.product(GRID, repeat=len(c))]
    rows.append(dict(case=k, threshold=t, n_sigma_combinations=len(vals), min_pooled=round(min(vals)), max_pooled=round(max(vals)),
                     worst_margin=round(min(vals) - t), passes_all=min(vals) >= t))
out = pd.DataFrame(rows)
save(out, "table7_relabel.csv")
print(out.to_string(index=False))
print(pd.read_csv(C.ACS / "acs_dispersion.csv").to_string(index=False))
