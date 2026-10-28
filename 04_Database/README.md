# Database schema, relationships, and safe recreation

## Included database assets

- [`sql/001_schema.sql`](sql/001_schema.sql): PostgreSQL/TimescaleDB base schema.
- [`sql/002_seed_berths_research.sql`](sql/002_seed_berths_research.sql):
  research-stage berth source/records; berth rows remain partially verified.
- [`sql/003_extend_derived_distance_proxies.sql`](sql/003_extend_derived_distance_proxies.sql):
  reuses existing same-port-pair proxies without upgrading their status.
- [`docker-compose.yml`](docker-compose.yml): local TimescaleDB service and
  first-volume schema initialization.

The `coal_trade_volumes` table is created by
[`ingest_coal_trade_volumes.py`](../08_Code_and_Handover/scripts/ingest_coal_trade_volumes.py)
using `CREATE TABLE IF NOT EXISTS`; it is not defined in `001_schema.sql`.

## ER diagram

The source is Mermaid and can be rendered by Markdown viewers that support
Mermaid. No screenshot or rendered diagram image is included.

```mermaid
erDiagram
    DATA_SOURCES ||--o{ PORTS : documents
    DATA_SOURCES ||--o{ BERTHS : documents
    DATA_SOURCES ||--o{ TRADE_LANES : documents
    DATA_SOURCES ||--o{ LANE_DISTANCES : documents 
    DATA_SOURCES ||--o{ FREIGHT_OBSERVATIONS : attributes
    DATA_SOURCES ||--o{ MARKET_OBSERVATIONS : attributes
    DATA_SOURCES ||--o{ COAL_TRADE_VOLUMES : attributes
    DATA_SOURCES ||--o{ INGESTION_RUNS : tracks
    PORTS ||--o{ BERTHS : has
    PORTS ||--o{ TRADE_LANES : origin
    PORTS ||--o{ TRADE_LANES : destination
    TRADE_LANES ||--o{ LANE_DISTANCES : has
    TRADE_LANES o|--o{ FREIGHT_OBSERVATIONS : associated
    VALIDATION_RESULTS {
        bigint validation_id PK
        timestamptz validation_run_at
        text check_name
        text status
    }
    DATA_SOURCES {
        bigint source_id PK
        text source_name
        text dataset_type
        text source_url
    }
    PORTS {
        bigint port_id PK
        text port_name
        text country
        numeric latitude
        numeric longitude
        text coordinate_status
        bigint source_id FK
    }
    BERTHS {
        bigint berth_id PK
        bigint port_id FK
        text berth_name
        text verification_status
        bigint source_id FK
    }
    TRADE_LANES {
        bigint lane_id PK
        text route_id
        bigint origin_port_id FK
        bigint destination_port_id FK
        text vessel_class
        bigint source_id FK
    }
    LANE_DISTANCES {
        bigint distance_id PK
        bigint lane_id FK
        numeric distance_nm
        text distance_status
        bigint source_id FK
    }
    FREIGHT_OBSERVATIONS {
        date assessment_date PK
        text record_id PK
        bigint source_id FK
        bigint lane_id FK
        numeric freight_rate_usd_per_tonne
        text target_data_type
    }
    MARKET_OBSERVATIONS {
        timestamptz observed_at PK
        bigint source_id PK
        text indicator_code PK
        numeric value
        text data_type
    }
    COAL_TRADE_VOLUMES {
        date month_start PK
        text origin_country PK
        text destination_country PK
        text hs_code PK
        bigint source_id PK
        numeric quantity_value
        text unit
        text value_status
    }
    INGESTION_RUNS {
        bigint ingestion_run_id PK
        bigint source_id FK
        text file_name
        text status
    }
```

`VALIDATION_RESULTS` is intentionally independent: each check execution is a
record with status, observed/expected values, and evidence. The diagram shows
the coal table's composite key as represented by the importer; see the actual
table definition in the included importer for all columns and constraints.

## Relationship notes

- `ports` has zero or more `berths`; each berth belongs to one port.
- `trade_lanes` references an origin and destination port, plus optional source
  metadata. Current lanes are candidate route scenarios.
- A lane may have one or more `lane_distances`; current rows are all derived
  proxies, not verified navigational sailing distances.
- `freight_observations` may reference a lane and must reference a source.
  Its primary key is `(assessment_date, record_id)`.
- `market_observations` references a source and is keyed by
  `(observed_at, source_id, indicator_code)`.
- Coal rows reference a source. The importer defines a composite primary key
  over month, origin, destination, HS code, and source.
- `data_sources` records provenance for multiple domain tables. `ingestion_runs`
  track files and outcomes; `validation_results` records check outcomes.

## Safe setup / recreation procedure

This documents how to initialize a **new local development database**. It does
not rebuild the current database, and no reset was performed for this
submission.

1. Use a disposable/new local checkout and confirm the target is an empty
   database volume. Do not run `docker compose down -v`, delete a volume, drop
   tables, or replay schema into an existing installation without a reviewed
   migration plan.
2. From the project root, copy `.env.example` to `.env` and set unique local
   placeholders/secrets privately. Never include `.env` in a submission.
3. Install Docker Compose v2 and the Python dependencies as described in
   [handover setup](../08_Code_and_Handover/README.md).
4. Run `docker compose up -d` and wait for the service health check. Compose
   mounts `001_schema.sql` into the initialization directory; the database
   image executes it only when initializing an empty data directory.
5. After confirming the initialized schema, use the ingestion order in the
   handover guide. The coal importer creates its own table when absent.
6. Review optional SQL seeds/migrations (`002` and `003`) before applying to a
   new database. They are transaction-wrapped and scoped to inserts/upserts,
   but their source values still require review.
7. Run validation only when prepared to persist validation records: the Python
   validation script inserts rows into `validation_results`.

On the existing project database, `docker compose up -d` merely starts the
service. It does not initialize/migrate an existing volume. Use a backup and
explicit migration procedure before any schema change.
