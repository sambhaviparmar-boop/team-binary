# Port, berth, trade-lane, and distance reference

The copied [route configuration](route_configuration.csv) and the current
database read-only snapshot are the reference for the 10 route scenarios.
Values are research/forecasting inputs, not operational navigation
recommendations.
The trade lanes are **synthetic candidate route scenarios**, not evidence of
historical fixtures or actual booked voyages.

The [berth reference export](berths_read_only_export.csv) contains the 13
current database rows, retrieved in a read-only transaction. Its actual command
output is retained as
[export evidence](../07_Test_Evidence/berth_export_output.txt).

## Port reference

Current database records: 4 ports. All coordinates have status
`approximate_assumed` and must not be used as navigational positions.

| Port | Country | Approximate latitude | Approximate longitude | Status |
|---|---|---:|---:|---|
| Hay Point | Australia | -21.270000 | 149.300000 | `approximate_assumed` |
| Haldia | India | 22.070000 | 88.070000 | `approximate_assumed` |
| Paradip | India | 20.320000 | 86.700000 | `approximate_assumed` |
| Visakhapatnam | India | 17.690000 | 83.220000 | `approximate_assumed` |

## Berth reference

The database contains 13 berth rows and **all 13 are `partially_verified`**.
The seeded records reference port authority material, but the values may be
conditional on tide, berth arrangement, and current port restrictions. Missing
draft values are intentionally not inferred from design draft or present depth.
Confirm current port notices and marine conditions before use.

The authority URLs and their use limitations are in
[the source register](../02_Data_Sources/README.md); the actual research-stage
seed is [002_seed_berths_research.sql](../04_Database/sql/002_seed_berths_research.sql).

## Lane and vessel scenarios

The table below is from the read-only database snapshot. Each value is a
**derived distance proxy**. The first three route IDs are candidate scenarios
created from the route-configuration naming; the other IDs identify commodity
and vessel variations. They are not verified sailing tracks or distances.

| Route ID | Origin → destination | Commodity | Vessel class | Distance (nautical miles) | Distance status |
|---|---|---|---|---:|---|
| AUS-HYD-HLD | Hay Point → Haldia | thermal_coal | Handymax | 4,873 | derived |
| AUS-HYD-PRD | Hay Point → Paradip | coking_coal | Panamax | 4,885 | derived |
| AUS-HYD-VIZ | Hay Point → Visakhapatnam | coking_coal | Panamax | 4,989 | derived |
| HAY-HAL-COKING-PMX | Hay Point → Haldia | Coking coal | Panamax | 4,873 | derived |
| HAY-HAL-THERMAL-PMX | Hay Point → Haldia | Thermal coal | Panamax | 4,873 | derived |
| HAY-PAR-COKING-CAPE | Hay Point → Paradip | Coking coal | Capesize | 4,885 | derived |
| HAY-PAR-COKING-PMX | Hay Point → Paradip | Coking coal | Panamax | 4,885 | derived |
| HAY-PAR-THERMAL-CAPE | Hay Point → Paradip | Thermal coal | Capesize | 4,885 | derived |
| HAY-PAR-THERMAL-PMX | Hay Point → Paradip | Thermal coal | Panamax | 4,885 | derived |
| HAY-VIZ-THERMAL-PMX | Hay Point → Visakhapatnam | Thermal coal | Panamax | 4,989 | derived |

## Distance and route limitations

- All 10 current distance rows are `derived`; none is an independently
  verified sailing distance.
- Scenario distance values are repeated between vessel/commodity variations
  with identical origin/destination pairs; this is proxy reuse, not route
  validation.
- `direct_fixture_evidence` is not established as positive evidence for these
  candidate lanes. Scenario existence does not prove a historical fixture.
- Coordinate precision in storage must not be mistaken for coordinate
  accuracy.
- Independent navigational/AIS route verification and current berth checks
  remain blockers for any operational use.
