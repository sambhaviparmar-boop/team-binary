# Sprint 1 plan and outcome

## Objective

Establish a local PostgreSQL/TimescaleDB foundation for provenance-aware
FreightIQ coal bulk-freight scenarios: retain source datasets, load the core
reference and observation tables, and provide initial validation without
representing synthetic scenarios or unverified market data as observations.

## Scope

- Database schema for ports, berths, trade lanes, distances, source metadata,
  observations, ingestion runs, and validation results.
- Import of candidate Hay Point-to-India routes, a synthetic freight dataset,
  Brent CSV-mirror observations, Australian-origin monthly coal import records,
  and weekly community-derived BDI/BCI/BPI indices.
- Research-stage berth references and derived distance proxies.
- Dataset inventories, provenance notes, validation scripts, and handover
  material.

Out of scope for acceptance: operational navigation advice, verified sailing
distances or berth restrictions, official BDI/BCI/BPI observations, and
source-backed Australian coal price series.

## Completed work (evidence-backed)

- Existing database queried in read-only mode on 2026-10-27 UTC; counts and
  coverages are recorded in
  [the database snapshot](../07_Test_Evidence/read_only_database_snapshot.txt).
- 10 candidate lanes and 10 derived distance records; 13 berths are all marked
  `partially_verified`; 4 port coordinates are marked approximate assumptions.
- 14,608 freight observations cover 2021-01-01 to 2025-12-31. The source and
  benchmark records are synthetic, not historical fixture rates.
- 300 monthly Australia-to-India coal trade records cover 2021-01 to 2025-12.
  Their apparent `million_tonnes` unit remains inferred pending source metadata.
- Market table has 2,034 rows: 1,263 Brent rows and 771 weekly community-derived
  BDI/BCI/BPI rows (257 per index) from 2021-01-08 to 2025-12-26.
- Latest stored database validation results: 8 passed and 1 blocked. The
  blocked check is `approved_observed_index_rows`; no independently verified
  observed index records are present.
- Submission files were assembled from repository artifacts. Original data,
  database schema, and ingestion logic were not modified for this package.

Historical repeat-ingestion and command claims are distinguished from the
current database snapshot in the
[evidence index](../07_Test_Evidence/README.md).

## Acceptance criteria

| Criterion | Result | Evidence / qualification |
|---|---|---|
| Core schema, source assets, and safe setup/recreation guidance documented | Met | `04_Database/` and `08_Code_and_Handover/` |
| Current table counts and core data coverage reconciled | Met | Read-only database snapshot |
| Validation status preserved without altering historical results | Met | 8 passed, 1 blocked in current database |
| Derived and synthetic data clearly distinguished from observed data | Met | Data-source register and processed-data dictionary |
| Coordinates, berths, distances, coal units, and community index provenance qualified | Met with open limitations | Source and reference registers |
| Official observed BDI/BCI/BPI records available | Not met | Validation is blocked until approved source data is supplied |
| Independent verification for operational berth limits and distances | Not met | Requires current port / navigational evidence |
| Original terminal logs for each reported repeat ingestion available | Not met | Historical details are documented, but no original logs were present |

## Remaining blockers and next actions

1. Obtain and approve independently verifiable observed BDI, BCI, and BPI
   observations; retain the current blocked result until this is done.
2. Verify Australian coal quantity units and exact dataset export provenance
   against source metadata.
3. Independently validate the route distances and current berth constraints
   before operational use.
4. Capture original command output for repeat-ingestion claims and source
   verification in the project evidence store.

## Recommendation

**Not fully accepted.** Recommend conditional acceptance of the Sprint 1
foundation and documentation package only. The observed-index requirement,
source metadata, operational reference verification, and missing original
repeat-ingestion logs remain open.

See the project-root
[`SPRINT1_ACCEPTANCE_REPORT.md`](../../SPRINT1_ACCEPTANCE_REPORT.md) for the
submission summary.
