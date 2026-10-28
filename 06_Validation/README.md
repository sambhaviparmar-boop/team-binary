# Validation assets and outcomes

## Included assets

- [`scripts/validate_db.py`](scripts/validate_db.py): existing database checks.
  **This script writes rows to `validation_results`; it was not run for this
  package.** Running it again appends another set of results.
- [`scripts/validate_indices.py`](scripts/validate_indices.py): local CSV
  checks for the three source index files and weekly resampling.
- [`index_source_validation_report_latest.txt`](index_source_validation_report_latest.txt):
  latest execution output from `scripts/validate_indices.py`, covering BDI,
  BCI, and BPI date/value quality checks on the local source files. These
  structural checks do not independently verify the indices or establish
  official approval.
- [`sql/validation_queries.sql`](sql/validation_queries.sql): existing SQL
  checks. The statements are SELECT/CTE queries; the complete file was not run
  as part of this package build.
- [`index_source_validation_report.txt`](index_source_validation_report.txt):
  existing output from local source-index validation, copied as-is.

## Current database counts and check results

Captured in a read-only transaction on 2026-10-27 UTC:

| Check | Result | Interpretation |
|---|---:|---|
| `freight_row_count` | 14,608 — passed | Matches expected synthetic scenario count. |
| `duplicate_date_record_ids` | 0 — passed | No duplicate freight primary key groups. |
| `nonpositive_rates` | 0 — passed | No nonpositive or null freight rates. |
| `rows_missing_port_names` | 0 — passed | Required names present. |
| `required_destination_ports_present` | 3 — passed | Paradip, Visakhapatnam, and Haldia. |
| `candidate_lanes_count` | 10 — passed | Candidate scenario count only; not fixture validation. |
| `community_derived_index_rows` | 771 — passed | 257 per index, but community-derived and unverified. |
| `community_derived_index_nonpositive_values` | 0 — passed | Does not establish official provenance. |
| `approved_observed_index_rows` | 0 — blocked | Approved independently verified observed BDI/BCI/BPI rows are absent. |

Database validation results remain **8 passed, 1 blocked**. In particular,
`approved_observed_index_rows = 0 [BLOCKED]`: no independently verified or
officially approved observed BDI/BCI/BPI rows are available. The latest local
date/value quality output does not change this database status. No validation
results have been modified to turn the blocked check into a pass.

Other read-only checks in the snapshot: 14,608 freight rows and 1,826 distinct
dates (2021-01-01 through 2025-12-31); 2,034 total market rows (1,263 BRENT
and 771 community-derived indices); 300 coal rows (2021-01 through
2025-12); 13/13 berths `partially_verified`; 10/10 lane distances `derived`;
and one recorded successful freight ingestion run of 14,608 rows.

## Index-source validation

The copied existing report shows, for each of BDI/BCI/BPI: 1,251 in-range
source daily rows; no invalid dates, missing/non-numeric values, duplicate
dates, or non-positive values; and 257 weekly Friday-ending values from
2021-01-08 through 2025-12-26. These checks are structural checks on the
community files only and do not verify official source provenance.

## Repeat-ingestion evidence

The existing project report is preserved as
[`SPRINT1_COMPLETION_REPORT.md`](../07_Test_Evidence/SPRINT1_COMPLETION_REPORT.md).
It records a Brent re-import with 0 new rows and 1,263 total observations, and
coal import output describing the 300-row cleaned series. These are historical
claims in the project report; no original terminal log for those repeat runs
was found in the repository. The current snapshot independently confirms
counts, but does not independently prove the prior command sequence.

No importer or mutating validation script was executed for this submission.
See the [evidence index](../07_Test_Evidence/README.md) for what still needs to
be captured.
