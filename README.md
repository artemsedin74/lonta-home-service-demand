# Lonta Home-Service Demand Study — v1.0

Canonical report: https://lonta.io/research/home-service-demand/
Prepared October 12, 2026. Original secondary analysis of the 2023 American Housing Survey,
using the actual DataLumos 217661/V2 archival edition: https://doi.org/10.3886/E217661V2.
This is company-authored analysis prepared with Codex, not an independent journal
article, an original client study, a 2026 demand forecast or a causal advertising effect.

## Obtain the input
Download the National PUF folder from DataLumos V2 through its normal UI. Any required
login/data-use terms remain your responsibility. The raw records are not redistributed.
Both household.csv and project.csv must match the pinned hashes in
analysis/source_identity.py. ZIP compression/timestamps can vary; changed CSV contents
are rejected. Exact original Census-origin binary equality has not been established.

## Repeat the calculations
Use Python 3.12+ and the versions in requirements.txt. Install in your own virtual env.

```
python -m pip install -r requirements.txt
python -m unittest discover -s analysis -q
OPENBLAS_NUM_THREADS=1 python reproduce.py --archive /path/to/download.zip --out results
python -c "import json; from render_figures import render; render(json.load(open('results/data.json')), 'figures')"
```

The driver first reproduces 183 Census 2023 workbook figures at displayed precision,
then recomputes all eight categories, 24 vintage cells and the prespecified descriptive
income/division models. One small vintage cell and its model contrast are suppressed
in every public output. No raw IDs or household rows are saved. Test rows are invented
arithmetic fixtures, not Census records or Lonta observations.

The primary workbook was obtained as parsed text from its official URL by a document
reader. The binary XLSX was not downloaded. Selected source sections and the comparison
receipt are included. PUF estimates and Table Creator IUF estimates are distinct.
Source controls use positive costs for medians/means; Lonta's category medians retain
known nonnegative costs, including zero. Normal 90% intervals are pointwise, with no
multiplicity adjustment. The four-significant-digit/whole-dollar display and source
1.645 critical factor are used only for published-control replication; they do not
alter the research's exact NormalDist 90% intervals.

## Interpretation and limits
All owner homes, including those with no project, form the household denominator.
The window is preceding 24 months at the 2023 interview, not calendar-year 2023.
JOBDIY 2 means most work was done outside the household, not verified paid invoices.
Costs include different scopes/materials; insurance payments may be included and
household labour is excluded. Not all emergency/routine calls are measured.
Home vintage is not equipment age. Equipment stock, housing type, exposure time,
metro and other factors are not controlled; group associations do not identify causes.
Do not infer local leads, current prices, revenue, profit or an advertising budget.

## Citation and rights
Lonta AI (2026). Home-Service Demand Study: home age, professional work and spending.
Version 1.0. Analysis of the 2023 AHS using DataLumos 217661/V2.
Cite Census/HUD for the original survey, ICPSR/DataLumos DOI for the copy used, and
Lonta for these particular cross-tabulations, comparisons and figures.
The frozen private-analysis plan is a historical pre-output specification; its original
private-only scope label is not the current release status. Current source validation
is recorded in analysis/publication-readiness.json and the reproduced control receipt.
Lonta's original code: MIT. Original figures/aggregate exports/commentary/worksheet:
CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
Original survey data/source documentation retain their own rights and access terms;
the Lonta license does not replace the accepted ICPSR agreement.

## Repository companion
This repository makes the already-published study source easier to inspect and rerun.
The canonical public report and company definition remain on [Lonta AI](https://lonta.io/research/home-service-demand/).
See [CITATION.md](CITATION.md) for attribution and [REUSER-NOTES.md](REUSER-NOTES.md)
for denominators, uncertainty and editorial limits. This is company-authored source
material, not independent press coverage or peer review. No raw survey records, IDs,
credentials, private contacts or customer observations are included.

The 46 offline tests were rerun from this source package before repository publication.
The published report's 183 selected workbook-control comparisons are retained as
receipts; rerun the full driver yourself after obtaining the exact cited archive.
The inputs require their own access and terms. MIT applies to Lonta code; original
aggregates/figures/commentary/worksheet are CC BY 4.0; original source rights remain
separate. No raw data download or website submission occurs in the offline tests.
