"""Step 11. Bootstrap intervals for failing shares of earners and programs (Sections 4.1-4.2): 10,000 program resamples."""
import numpy as np
import pandas as pd
import config as C
from common import save

ba = pd.read_csv(C.DER / "ba_robustness.csv", dtype={"CIPCODE": str})
g = pd.read_csv(C.DER / "grad_programs_scored.csv")
sets = {"All religion BA (CIP 38+39)": (ba, "fail_rule"), "CIP 38.02": (ba[ba.CIPCODE == "3802"], "fail_rule"),
        "CIP 39 (ministry)": (ba[ba.CIPCODE.str.startswith("39")], "fail_rule"),
        "Religion BA excl. yeshivas": (ba[~ba.yeshiva], "fail_rule"), "Graduate theology (CIP 39.06)": (g, "fail_national")}
rng = np.random.default_rng(C.SEED); R = 10000; rows = []
for k, (d, col) in sets.items():
    f = d[col].values.astype(bool); w = d.earners4.values; n = len(d)
    es, ps = [], []
    for _ in range(R):
        i = rng.integers(0, n, n); es.append(100 * w[i][f[i]].sum() / w[i].sum()); ps.append(100 * f[i].mean())
    rows.append(dict(set=k, n=n, earner_share=round(100 * w[f].sum() / w.sum(), 1), earner_lo=round(np.percentile(es, 2.5), 1),
                     earner_hi=round(np.percentile(es, 97.5), 1), prog_share=round(100 * f.mean(), 1),
                     prog_lo=round(np.percentile(ps, 2.5), 1), prog_hi=round(np.percentile(ps, 97.5), 1)))
t = pd.DataFrame(rows); save(t, "bootstrap_failure_shares.csv"); print(t.to_string(index=False))
