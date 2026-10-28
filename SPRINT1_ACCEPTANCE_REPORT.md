# FreightIQ Sprint 1 acceptance report

**Recommendation: conditional acceptance of the foundation/documentation only;
Sprint 1 is not fully accepted.**

The complete submission is in
[`FreightIQ_Sprint_1/`](FreightIQ_Sprint_1/). Detailed scope and acceptance
criteria are in the [sprint plan](FreightIQ_Sprint_1/01_Sprint_Plan/README.md).

## Deliverables

The package contains the requested sprint plan, source register and raw-data
inventory, processed-data copies and dictionary, Mermaid ER diagram and
database recreation guidance, port/berth/trade-lane references, validation
assets and existing validation output, a read-only database snapshot and
evidence checklist, and setup/handover instructions with a placeholder-only
environment template.

## Current database evidence

The existing healthy database was queried in a read-only transaction. The
captured UTC output is
[here](FreightIQ_Sprint_1/07_Test_Evidence/read_only_database_snapshot.txt);
the current berth rows were also exported read-only to
[this CSV](FreightIQ_Sprint_1/05_Port_and_TradeLane/berths_read_only_export.csv).

| Table | Rows |
|---|---:|
| `ports` | 4 |
| `berths` | 13 |
| `trade_lanes` | 10 |
| `lane_distances` | 10 |
| `freight_observations` | 14,608 |
| `market_observations` | 2,034 |
| `coal_trade_volumes` | 300 |
| `data_sources` | 10 |
| `ingestion_runs` | 1 |
| `validation_results` | 9 |

Freight observations cover 2021-01-01 through 2025-12-31. The 300 coal rows
cover 2021-01 through 2025-12, with quantity units inferred as
`million_tonnes` but not confirmed by source metadata. Market observations
include 1,263 Brent rows and 771 weekly community-derived BDI/BCI/BPI records
(257 per index) from 2021-01-08 through 2025-12-26.

The existing validation results remain **8 passed, 1 blocked**. The blocked
`approved_observed_index_rows` check has zero independently verified approved
BDI/BCI/BPI observations. Freight benchmarks are synthetic, all 13 berth rows
are `partially_verified`, port coordinates are approximate assumptions, and
all 10 lane distances are derived proxies, not navigationally verified
distances.

## Limitations and remaining blockers

- Independent verification/approval of official observed BDI, BCI, and BPI
  data is outstanding.
- Coal quantity units and exact source export/query provenance require
  confirmation.
- Current berth constraints and navigational distances need independent
  verification before operational use.
- Source-backed Australian thermal/coking coal price series and VLSFO
  observations are absent.
- Original terminal logs for historical repeated-ingestion claims were not
  found. The existing project completion report documents these claims, but
  this submission does not represent that report as raw execution evidence.
- Some reference datasets have unknown publisher, license, URL, or reporting
  period.

No destructive reset, database rebuild, schema migration, mutating validation,
or ingestion rerun was performed for this package. The database snapshot and
berth export used read-only transactions; the original blocked validation
result was not changed. See the [evidence index](FreightIQ_Sprint_1/07_Test_Evidence/README.md)
for the acceptance checklist and evidence still to capture.
