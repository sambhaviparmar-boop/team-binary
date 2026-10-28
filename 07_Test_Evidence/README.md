# Test evidence index and acceptance checklist

No screenshot, log, or command result has been fabricated. The terminal-style
database snapshot below is actual output from a successful read-only query
against the existing healthy container; it includes its UTC capture timestamp.

## Evidence index

| Evidence | Status | What it supports |
|---|---|---|
| [`read_only_database_snapshot.txt`](read_only_database_snapshot.txt) | Captured for this submission | Actual table counts, dates, source/index counts, validation rows, ingestion run, port coordinate status, berth status, lane and distance values. The transaction was explicitly read-only. |
| [`berth_export_output.txt`](berth_export_output.txt) and [`berths_read_only_export.csv`](../05_Port_and_TradeLane/berths_read_only_export.csv) | Captured for this submission | Output and data rows from a read-only export of all 13 current berth records, with source references and verification status. |
| [`../06_Validation/index_source_validation_report_latest.txt`](../06_Validation/index_source_validation_report_latest.txt) | Latest `scripts/validate_indices.py` execution output | BDI, BCI, and BPI source-file date/value quality checks. This is structural validation only; the indices are not thereby independently verified or officially approved. |
| [`../06_Validation/index_source_validation_report.txt`](../06_Validation/index_source_validation_report.txt) | Existing file copied unchanged | Output of prior local index CSV structure/coverage validation. |
| [`SPRINT1_COMPLETION_REPORT.md`](SPRINT1_COMPLETION_REPORT.md) | Existing project documentation, copied unchanged | Historical claims about repeat imports, prior SQL checks, and compilation; original logs were not found to independently corroborate them. |
| [`../06_Validation/scripts/validate_db.py`](../06_Validation/scripts/validate_db.py) | Existing script copied unchanged; not executed here | Validation logic. It persists result rows, so executing it changes the database. |
| [`../06_Validation/sql/validation_queries.sql`](../06_Validation/sql/validation_queries.sql) | Existing SQL copied unchanged | Read-only query definitions; no report output from running the whole file is claimed. |

## Acceptance checklist

- [x] Package structure created with source artifacts copied from the repository.
- [x] Live database counts and status verified by read-only query.
- [x] Freight and coal date coverage, market series counts, berth statuses, and
      distance statuses captured.
- [x] Historical validation outcome remains 8 passed / 1 blocked.
- [x] Synthetic, derived, assumed, and unverified sources explicitly labeled.
- [x] Latest BDI/BCI/BPI date/value quality-check output is linked; it does not
      satisfy independent verification or approval.
- [ ] Obtain independent source validation for official observed BDI/BCI/BPI.
- [ ] Verify coal quantity units and exact source export/query provenance.
- [ ] Obtain independent navigational validation of lane distances and current
      operational berth constraints.
- [ ] Capture original terminal outputs for repeat-ingestion runs if required
      for formal audit; existing completion report is not a substitute for raw
      execution logs.
- [ ] Capture reviewer/approver sign-off, if required by the Sprint process.

## Still to capture

There were no existing screenshots or standalone terminal logs for prior
repeat-ingestion commands. None are represented as attached evidence. The
read-only snapshot is a new, directly captured output, not a screenshot.
Capture any further output only from a real, authorized execution and record
the command, time, environment, and whether it mutates state.
