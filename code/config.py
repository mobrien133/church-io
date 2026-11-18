"""Paths and constants shared by every script. All paths are relative to the repository root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ACS = ROOT / "data" / "acs"          # ACS-derived inputs (committed; regenerated if the IPUMS extract is present)
DER = ROOT / "data" / "derived"      # intermediate files written by the pipeline
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"

SCORECARD = RAW / "scorecard" / "fos_extract.csv"
FSA_DIR = RAW / "fsa"
IPEDS_DIR = RAW / "ipeds"
POLITY_SHEET = RAW / "author" / "polity_coding_sheet.csv"
THRESHOLDS = RAW / "author" / "thresholds_89FR107130.csv"
IPUMS_EXTRACT = RAW / "ipums" / "usa_00003.csv.gz"   # not redistributed; see README

FSA_YEARS = ["2122", "2223", "2324", "2425", "2526"]
NATIONAL_HS = 31269.0      # 2024 national high-school-only threshold (89 FR 107130)
THEOLOGY_BA_NATIONAL = 45000.0   # ACS 2019-23 national median, bachelor's-only, DEGFIELD 49 (data/acs)
ALL_BA_NATIONAL = 59539.0        # ACS 2019-23 national median, bachelor's-only, all fields (data/acs)
SEED = 20261106

for d in (DER, TAB, FIG, ACS):
    d.mkdir(parents=True, exist_ok=True)
