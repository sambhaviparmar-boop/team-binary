# Source register and raw-data inventory

This register separates source-backed content, local mirrors, derived
transformations, synthetic scenarios, and unresolved provenance. A public URL
is not proof that the local file was fetched from that endpoint. The repository
software license does not establish redistribution rights for third-party
datasets; check each publisher's terms before sharing data externally.

## Source register

| Dataset / source | Publisher / URL | Coverage and units | Provenance, license, and limitations |
|---|---|---|---|
| Freight forecast scenarios | FreightIQ team; no external source URL | Daily 2021-01-01–2025-12-31; USD/DMT | Synthetic benchmark data, including synthetic BDI/BPI proxies. Not market observations. Project-generated; no separate data license recorded. |
| Route configuration | FreightIQ team; no external source URL | 10 candidate route scenarios; nautical miles, assumed coordinates, vessel/cargo parameters | Synthetic/candidate scenarios with derived distance proxies; direct port-pair fixture evidence is not established. |
| Brent daily CSV mirror | Underlying series: [EIA Europe Brent spot price history](https://www.eia.gov/dnav/pet/hist/RBRTED.htm) | Daily 2021-01-04–2025-12-31; USD/barrel; 1,263 rows in database | Loaded from bundled `brent_daily.csv`; import did not fetch from EIA API or independently establish mirror lineage. EIA page is a series reference, not proof of local file provenance. |
| India coal import matrix / selected Australia subset | [UN Comtrade Plus](https://comtradeplus.un.org/) (URL associated with the export; exact query/export provenance not retained) | Cleaned Australia-to-India subset: 2021-01–2025-12, monthly; 300 database rows | Selected direct coal HS codes; overlapping subcodes excluded. Quantity is retained at apparent native scale and recorded as `million_tonnes`, but source metadata does not independently confirm the unit. Licensing/redistribution terms require review. |
| Weekly BDI/BCI/BPI historical files | [yieldchaser/Shipping indices directory](https://github.com/yieldchaser/Shipping/tree/main/data/indices) | Source daily files reduced to weekly Friday-ending values; 257/index, 771 total; 2021-01-08–2025-12-26; index points | Community-maintained and derived; not independently verified as official Baltic Exchange observations. Review repository license and upstream source terms before redistribution. |
| Top-10 countries coal reference | No URL or publisher embedded | 10-country reference; reporting year unknown; stated MT columns | Unverified period and publisher; Australia appears in the file. Reference only, not a time series. |
| 2026 World coal trade export | No verified URL; Comtrade-like field structure | 2026-01–2026-07; 7 rows; kg; partner is World | Out-of-period world totals, not Australia-specific. Do not use to infer Australia-origin imports. |
| 2026 World coal import export (second file) | No verified URL; Comtrade-like field structure | 12 rows; kg; partner is World | Raw reference only; not Australia-specific. |
| India annual coal/coke PDF | Local PDF only; no stable public source URL recorded | FY 2015-16–FY 2024-25; national totals, million tonnes | National India aggregate reference, not Australia- or port-specific. |
| Annual coal reference CSV | Derived local reference from the annual PDF | 10 fiscal-year rows; million tonnes | National aggregate; derived/reference, not monthly or Australia-specific. |
| Month-wise coal products reference | Source URL and unit metadata not recorded | 12 monthly rows | Quality-check reference. Suspicious zero values in October–December 2024-25 were retained as recorded, not corrected. |
| Official berth references | [Paradip Port Authority berth specifications](https://paradipport.gov.in/berth-specifications/); [Syama Prasad Mookerjee Port Authority FY 2024-25 administrative report](https://smportkolkata.shipping.gov.in/smpk/wp-content/uploads/2026/04/Administrative-Report-2024-2025-Soft-Copy_compressed.pdf); [Visakhapatnam Port Authority berth particulars](https://vpt.shipping.gov.in/Template/navigateTemplate/gnt/QmVydGhz) | Reference draft/LOA/DWT as published; not guaranteed current operational limits | Public authority webpages/reports; follow publisher terms. Each stored berth remains `partially_verified`; tidal and current operational constraints require confirmation. |

## Raw-data inventory

The raw files remain in the repository's `data/` directory; they are not
duplicated in this submission. Paths below are relative to the project root.
The large freight input is deliberately referenced rather than copied.

| Repository path | Role / coverage | Classification and caveat |
|---|---|---|
| [`data/FreightIQ_Freight_Forecasting_2021_2025_Reviewed.csv`](../../data/FreightIQ_Freight_Forecasting_2021_2025_Reviewed.csv) | Freight scenario source, 2021–2025 | Synthetic; includes BDI/BPI proxy columns. |
| [`data/route_configuration.csv`](../../data/route_configuration.csv) | Candidate route / vessel / cargo scenarios | Assumed coordinates; derived distances; no verified direct fixture evidence. A copy is included in `05_Port_and_TradeLane/`. |
| [`data/brent_daily.csv`](../../data/brent_daily.csv) | Brent local CSV mirror | 2021–2025; underlying EIA series URL does not establish mirror lineage. |
| [`data/india_coal_imports_data.csv`](../../data/india_coal_imports_data.csv) | Monthly India import matrix | Raw source for the cleaned 2021–2025 Australia subset; unit/export lineage unresolved. |
| [`data/india_australia_coal_imports_2021_2025_clean.csv`](../../data/india_australia_coal_imports_2021_2025_clean.csv) | Cleaned Australia-to-India subset | 300 rows; apparent unit inferred as million tonnes; copy included in `03_Processed_Data/`. |
| [`data/Import-of-Coal-and-Coke-last-ten-years-2.pdf`](../../data/Import-of-Coal-and-Coke-last-ten-years-2.pdf) | National India annual reference | FY 2015-16–2024-25; million tonnes; not origin- or port-specific. |
| [`data/india_coal_imports_reference_annual_fy_2015_2025.csv`](../../data/india_coal_imports_reference_annual_fy_2015_2025.csv) | Annual reference extracted/cleaned from PDF | 10 annual rows; national-only reference. |
| [`data/Month-wise-Coal-and-Coal-Products-Import.csv`](../../data/Month-wise-Coal-and-Coal-Products-Import.csv) | Monthly quality-check reference | Incomplete source/unit metadata; reported zeroes retained. |
| [`data/Top-10-Countries-wise-Coal-Import.csv`](../../data/Top-10-Countries-wise-Coal-Import.csv) | Country ranking reference | 10 rows; publisher and reporting year unknown. |
| [`data/Top-10-Countries-wise-Coal-Import_cleaned.csv`](../../data/Top-10-Countries-wise-Coal-Import_cleaned.csv) | Cleaned country ranking | Still an unverified reference; copy included in `03_Processed_Data/`. |
| [`data/TradeData_10_23_2026_16_1_45.csv`](../../data/TradeData_10_23_2026_16_1_45.csv) | 2026 monthly trade export | World partner; kg; 7 rows; not Australia-specific. |
| [`data/TradeData_10_23_2026_16_1_45_cleaned.csv`](../../data/TradeData_10_23_2026_16_1_45_cleaned.csv) | Cleaned 2026 World reference | Copy included in `03_Processed_Data/`; not model-period Australian imports. |
| [`data/TradeData_10_23_2026_16_2_5.csv`](../../data/TradeData_10_23_2026_16_2_5.csv) | Earlier World trade export | 12 rows; kg; partner World; source URL not verified. |
| [`data/indices/bdiy_historical.csv`](../../data/indices/bdiy_historical.csv) | Community BDI daily input | Source/provider lineage not independently verified. |
| [`data/indices/cape_historical.csv`](../../data/indices/cape_historical.csv) | Community BCI daily input | Source/provider lineage not independently verified. |
| [`data/indices/panama_historical.csv`](../../data/indices/panama_historical.csv) | Community BPI daily input | Source/provider lineage not independently verified. |
| [`data/indices/weekly_indices_2021_2025.csv`](../../data/indices/weekly_indices_2021_2025.csv) | Derived weekly index output | 771 rows; copy included in `03_Processed_Data/`; not official verified observations. |
| [`data/indices/validation_report.txt`](../../data/indices/validation_report.txt) | Existing index preprocessing output | Existing terminal-style output copied to `06_Validation/index_source_validation_report.txt`. |

## License and handling notes

- Repository code carries the project's [MIT license](../../LICENSE). This does
  not automatically license the datasets or grant rights to redistribute
  government, community, or third-party source files.
- The database source register contains publisher URLs, unit/frequency notes,
  and provenance statements for the ten registered sources where available.
- Files with unknown publisher, license, query/export provenance, or period
  should remain reference-only until reviewed. Do not silently fill missing
  metadata from inference.
