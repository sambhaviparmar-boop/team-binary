# Processed data and data dictionary

The CSVs in this folder are copies of existing repository artifacts. No source
data was regenerated for this submission. Raw inputs remain in the project
`data/` folder and are referenced in
[the source inventory](../02_Data_Sources/README.md).

## Included processed datasets

| File | Rows / coverage | Classification | Unit / caveats |
|---|---|---|---|
| [`india_australia_coal_imports_2021_2025_clean.csv`](india_australia_coal_imports_2021_2025_clean.csv) | 300 month/HS-code rows, 2021-01 through 2025-12 | Source-extracted / transformed subset | `million_tonnes` is inferred from native scale and consistency checks; source metadata has not confirmed it. |
| [`weekly_indices_2021_2025.csv`](weekly_indices_2021_2025.csv) | 771 rows; 257 each BDI, BCI, BPI; 2021-01-08 through 2025-12-26 | Derived from community-maintained daily files | `index_points`; last available daily value in each Friday-ending week. Unverified as official observations. |
| [`Top-10-Countries-wise-Coal-Import_cleaned.csv`](Top-10-Countries-wise-Coal-Import_cleaned.csv) | 10 country rows | Cleaned reference / unknown period | MT stated by source columns; publisher and reporting year unknown. |
| [`TradeData_10_23_2026_16_1_45_cleaned.csv`](TradeData_10_23_2026_16_1_45_cleaned.csv) | 7 rows, 2026 months 1–7 | Cleaned World-total reference | `kg`; partner is World, not Australia. Out of the main 2021–2025 model period. |

The large synthetic freight input, Brent CSV mirror, original coal source matrix,
and raw index files are not recopied here; see the linked source register.

## Field dictionary

### Australia-origin coal monthly subset

| Field | Meaning | Status |
|---|---|---|
| `month_start` | Month represented, normalized to the first day of month | Derived date key |
| `origin_country`, `destination_country` | Trade flow countries | Source-reported; cleaned subset is Australia to India |
| `hs_code` | Selected direct coal HS code | Source-reported; overlapping subcodes excluded |
| `commodity_group` | Broad commodity grouping | Cleaned classification (`coal`) |
| `quantity_value` | Import quantity as present in source scale | Source value; scale/unit unresolved |
| `unit` | Stored unit label | Inferred `million_tonnes`; not source-confirmed |
| `source_name`, `source_url`, `source_record_ref` | Provenance reference | URL is associated with dataset; exact export query not retained |
| `value_status` | Reported value state | Includes explicit `zero_reported`; zeroes not imputed |
| `notes` | Transformation and caveat notes | Derived documentation |

### Weekly BDI / BCI / BPI file

| Field | Meaning | Status |
|---|---|---|
| `date` | Friday week-ending date | Derived via `W-FRI` resampling |
| `index_code` | `BDI`, `BCI`, or `BPI` | Source mapping |
| `value` | Last available source value for that week | Derived; community data, not official verification |
| `unit` | `index_points` | Declared transformation unit |
| `source`, `source_url` | Community source reference | Upstream lineage not independently confirmed |
| `source_type` | `community_maintained` | Classification |
| `verification_status` | `unverified` | Must not be presented as approved observed data |
| `aggregation_method` | `last_available_observation_W-FRI` | Transformation rule |

### Cleaned country and World references

- Country ranking fields are country, reporting period/year, coking/non-coking/
  total coal in MT, source identifiers, period status, classification, notes.
  The reporting period remains unknown.
- The cleaned World trade reference has month/period, reporter/partner,
  commodity code/description, quantity in kg, optional value, source
  identifiers, period status, classification, and notes. Partner `World` must
  not be represented as Australia.

## Transformation notes and labels

- **Synthetic:** freight scenario rates, BDI/BPI proxies in the freight
  scenario dataset, and candidate route configurations. These are not observed
  fixture or historical market data.
- **Derived:** weekly index resampling; route distance proxies; cleaned data
  subsets/references. Derived values retain source and method caveats.
- **Inferred:** coal quantity scale/unit (`million_tonnes`) and approximate
  port coordinates. These are assumptions pending source confirmation.
- **Unverified:** community index lineage, Top-10 country period/publisher, and
  several trade export source URLs.
- **Reported/reference:** source-reported coal values and Brent mirror values
  have local files, but provenance limits stated in the source register still
  apply.

For table-level field definitions see
[the schema](../04_Database/sql/001_schema.sql) and the
[coal table creation in the importer](../08_Code_and_Handover/scripts/ingest_coal_trade_volumes.py).
