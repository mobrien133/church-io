# Replication package

**From Nominal Failure to Effective Exposure: Program-Level Earnings Accountability in a Multiproduct, Mixed-Finance Industry**

Michael O'Brien ([ORCID 0009-0002-8028-843X](https://orcid.org/0009-0002-8028-843X))

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24341795.svg)](https://doi.org/10.5281/zenodo.24341795)

Archived at Zenodo: https://doi.org/10.5281/zenodo.24341795

This repository reproduces every table and figure in the paper from public data. `python run_all.py` runs the whole pipeline in about 20 seconds on a laptop.

## Overview

The code scores religion and theology degree programs against the earnings test in the U.S. Department of Education's July 2026 final rule (91 FR 40136). It then measures five filters between nominal failure and economic exposure:

1. the comparator;
2. the carve-out for institutions outside the Direct Loan program;
3. the cohort floor;
4. loan volumes;
5. product-line breadth.

The inputs are:

- program earnings from the College Scorecard;
- institution financing from Federal Student Aid (FSA) volume reports;
- completions and residence from IPEDS;
- comparators from the 2019–23 American Community Survey (ACS);
- the author's coding of sponsoring bodies.

Every file needed to run the pipeline is in the repository except the ACS microdata. IPUMS does not allow those to be redistributed. The ACS statistics the pipeline uses are committed in `data/acs/`, so the full pipeline runs without the microdata. With the IPUMS extract placed in `data/raw/ipums/`, step 2 recomputes those statistics; the committed files were produced that way.

## Data availability and provenance

| Data | Source | Files in this repository | Access and terms |
|---|---|---|---|
| College Scorecard, field of study (September 2025 release) | U.S. Department of Education, [collegescorecard.ed.gov/data](https://collegescorecard.ed.gov/data/) | `data/raw/scorecard/fos_extract.csv`: all rows with two-digit CIP 38, 39, 42, 44, 45 or 51, every credential level, all columns | Public domain (U.S. government work) |
| Title IV program volume reports: Direct Loan and Grant volume by school, award years 2021–22 to 2025–26, fourth quarter | Federal Student Aid, [studentaid.gov/data-center/student/title-iv](https://studentaid.gov/data-center/student/title-iv) | `data/raw/fsa/dl_YYZZ.xls`, `gr_YYZZ.xls`, unmodified | Public domain |
| IPEDS Completions, C2022_A and C2023_A | NCES, [nces.ed.gov/ipeds/datacenter](https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx) | `data/raw/ipeds/c2022_a_extract.csv`, `c2023_a_extract.csv`: the 1,576 institutions with a CIP 38–39 program in the Scorecard extract; columns UNITID, CIPCODE, MAJORNUM, AWLEVEL, CTOTALT | Public domain |
| IPEDS Fall Enrollment, residence of first-time students, EF2022C (revised) | NCES | `data/raw/ipeds/ef2022c_rv.csv`, unmodified | Public domain |
| 2024 earnings thresholds | 89 FR 107130 (December 2024) | `data/raw/author/thresholds_89FR107130.csv`, transcribed | Public domain |
| Sponsoring body and polity of each institution in the results | Author's coding from each institution's statement of affiliation, checked against the sponsoring body's published polity | `data/raw/author/polity_coding_sheet.csv`; corrections applied in `code/common.py` (`polity_map`) | CC BY 4.0 |
| ACS 2019–23 five-year public-use microdata | IPUMS USA (Ruggles et al.), [usa.ipums.org](https://usa.ipums.org/) | Not redistributed. Derived statistics in `data/acs/` | IPUMS terms of use; free registration |

### ACS extract

The extract is IPUMS USA `usa_00003`, created November 6, 2026:

- **Sample:** 2019–2023 ACS 5-year.
- **Case selection:** AGE 25–34.
- **Variables:** YEAR, MULTYEAR, SAMPLE, SERIAL, CBSERIAL, HHWT, CLUSTER, STATEFIP, PUMA, STRATA, GQ, PERNUM, PERWT, SEX, AGE, SCHOOL, EDUC, EDUCD, DEGFIELD, DEGFIELDD, DEGFIELD2, DEGFIELD2D, EMPSTAT, EMPSTATD, LABFORCE, CLASSWKR, CLASSWKRD, OCC, OCCSOC, UHRSWORK, INCTOT, INCWAGE, INCBUS00, INCEARN.
- **Format:** CSV, gzip-compressed.

To recompute `data/acs/`, save the extract as `data/raw/ipums/usa_00003.csv.gz` and run `python run_all.py`.

Users of IPUMS data must cite it. The extract was drawn from IPUMS USA Version 16.0: Ruggles, S., Flood, S., Sobek, M., Backman, D., Cooper, G., Rivera Drew, J. A., Richards, S., Rogers, R., Schroeder, J., & Williams, K. C. W. (2025). *IPUMS USA: Version 16.0* [dataset]. Minneapolis, MN: IPUMS. https://doi.org/10.18128/D010.V16.0

## Computational requirements

- Python 3.11 or later. Tested with Python 3.13 on Linux.
- Packages, pinned in `requirements.txt`: numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, matplotlib 3.11.2, xlrd 2.0.1. `xlrd` reads the FSA `.xls` files.
- Run time is about 20 seconds without the IPUMS extract and about 25 seconds with it. Memory use is under 2 GB.
- Randomness: the permutation tests (step 9) and the bootstrap (step 11) use seed 20261106 (`code/config.py`).

```
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs the scripts in `code/` in order. Intermediate files go to `data/derived/`, tables to `output/tables/` and figures to `output/figures/`. Console output from every step is written to `output/run_all.log`, including the figures quoted in the text.

## Programs

| Step | Script | Produces |
|---|---|---|
| 1 | `01_fsa_panel.py` | Institution-level Direct Loan and Pell panel; five-year no-Direct-Loan indicator (`data/derived/fsa_institutions.csv`) |
| 2 | `02_acs.py` | ACS comparators, clergy shares, housing-allowance shifts and dispersion (`data/acs/`). Runs only if the extract is present |
| 3 | `03_score_programs.py` | Bachelor's programs scored against the rule's threshold; graduate theology programs against both comparators; IPEDS composition of CIP 39.06 |
| 4 | `04_earnings_constructions.py` | Failing counts under alternative earnings constructions |
| 5 | `05_robustness.py` | Robust and conditional classifications |
| 6 | `06_filters.py` | Carve-out reach, the filter cascade, loan exposure, cohort-floor counts |
| 7 | `07_relabel.py` | Pooled medians of folded programs over the full grid of dispersion assumptions |
| 8 | `08_breadth.py` | Catalog breadth at every credential level; failing share of completions |
| 9 | `09_polity.py` | Polity tests |
| 10 | `10_universe.py` | Program universe and unreported programs |
| 11 | `11_bootstrap.py` | Bootstrap intervals |
| 12 | `12_figures.py` | Figures 1 and 2 |

`code/config.py` holds paths and constants. `code/common.py` holds the shared loaders: the program file, thresholds, in-state shares and polity coding.

## Tables and figures

| Exhibit | Output | Script |
|---|---|---|
| Table 1 (the preview against the rule's measure) | Descriptive; no computation | — |
| Table 2 | `output/tables/table2_graduate_theology.csv` | 03 |
| Table 3 | `output/tables/table3_ba_by_field.csv` | 03 |
| Table 4 | `output/tables/table4_earnings_constructions.csv` | 04 |
| Table 5 | `output/tables/table5_cascade.csv` | 06 |
| Table 6 | `output/tables/table6_loan_exposure.csv` | 06 |
| Table 7 | `output/tables/table7_relabel.csv` | 07 |
| Table 8 | `output/tables/table8_breadth.csv` | 08 |
| Table 9 | `output/tables/table9_robustness.csv`, `table9_counts_by_alternative.csv` | 05 |
| Table 10 (responses available) | Descriptive; no computation | — |
| Table A1 | `output/tables/tableA1_flow.csv`, `tableA1_categories.csv` | 10 |
| Figure 1 | `output/figures/figure1.png` | 12 |
| Figure 2 | `output/figures/figure2.png` | 12 |
| Bootstrap intervals (Sections 4.1–4.2) | `output/tables/bootstrap_failure_shares.csv` | 11 |
| In-text figures | `output/run_all.log` | 1–11 |

## Definitions worth knowing

- **Program unit.** OPEID6 × four-digit CIP × credential level, as the Scorecard reports it.
  - Puerto Rico is excluded.
  - Multi-campus records that repeat a program's earnings are dropped.
  - One reported program, at a seminary outside the United States, has no state threshold and is not scored.
- **Bachelor's threshold.** The state value from 89 FR 107130, or the national $31,269 where fewer than half of the institution's first-time students are from its state (IPEDS EF2022C).
- **Graduate comparators.** Every graduate program in CIP 39.06 is scored against two comparators, because graduate residence is not observed:
  - the national $45,000 (the lower of the national all-bachelor's and national theology medians);
  - the in-state lowest of three (state all-bachelor's; state theology, set to $1 if the ACS cell has fewer than 16 observations; national theology).
- **Mostly MDiv.** CIP 39.0602 is at least half of the institution's CIP 39.06 graduate completions (IPEDS, first major, award levels 7, 8, 17, 18 and 19, 2021–22 and 2022–23).
- **Yeshivas.**
  - In the Scorecard files, by institution name: Yeshiva, Talmud, Rabbinical, Mesivta or Medrash.
  - In the FSA files, by the broader name pattern in `code/06_filters.py`, excluding Yeshiva University.
- **Housing-allowance shifts (Table 4).**
  - The "added" and first "stripped" rows scale the ACS earnings of clergy who pay self-employment tax up or down by the allowance net of a one-third opt-out.
  - The stripped rows marked "W-2-only ACS base" and the naive-sum rows treat the ACS as recording W-2 wages only and compare the naive-sum, netted and W-2-only medians. The ACS cannot show which assumption is right, so the paper reports both.
- **Loan-exposure ceiling (Table 6).**
  - The ceiling is min(institution Direct Loans, min(estimated enrollment, undergraduate borrowers) × $12,500).
  - Estimated enrollment is four years of four-digit completions divided by a completion rate of 1/2 or 1/3.
  - The ceiling is an illustrative conditional bound, not a statutory maximum.
- **Institutions outside the federal files.** Records with no match in the FSA volume files are treated as inside the loan program. Sixty-three CIP 38–39 bachelor's records have no match, and one reported graduate program does: the Southern Baptist Theological Seminary, which passes either way.

## License

- Code (`code/`, `run_all.py`): MIT License (`LICENSE`).
- The author's coding and the derived data: CC BY 4.0 (`LICENSE-DATA`).
- The federal source files are U.S. government works in the public domain.

## Citation

See `CITATION.cff`. Please cite the paper and this package.
