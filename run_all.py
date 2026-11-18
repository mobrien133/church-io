"""Run the full pipeline. Usage: python run_all.py   (from the repository root; about one minute)."""
import subprocess
import sys
import time
from pathlib import Path

STEPS = ["01_fsa_panel", "02_acs", "03_score_programs", "04_earnings_constructions", "05_robustness", "06_filters",
         "07_relabel", "08_breadth", "09_polity", "10_universe", "11_bootstrap", "12_figures"]
code = Path(__file__).resolve().parent / "code"
log = Path(__file__).resolve().parent / "output" / "run_all.log"
log.parent.mkdir(parents=True, exist_ok=True)
with open(log, "w") as fh:
    for s in STEPS:
        t = time.time()
        print(f"== {s}", flush=True); fh.write(f"\n===== {s}\n"); fh.flush()
        r = subprocess.run([sys.executable, f"{s}.py"], cwd=code, stdout=fh, stderr=subprocess.STDOUT)
        if r.returncode:
            sys.exit(f"{s} failed; see output/run_all.log")
        print(f"   done in {time.time()-t:.1f}s", flush=True)
print(f"All steps complete. Tables in output/tables, figures in output/figures, console output in output/run_all.log.")
