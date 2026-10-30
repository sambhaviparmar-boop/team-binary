# FreightIQ Sprint 1

This repository contains the foundation package for the FreightIQ initiative: a provenance-aware, local analytics dataset for coal bulk freight and trade-lane research. It is designed to capture the project’s initial schema, data inventories, validation evidence, and handover materials without claiming operationally verified voyage or berth outcomes.

## Project objective

FreightIQ Sprint 1 establishes a local PostgreSQL/TimescaleDB foundation for freight scenario analysis, including:

- source-aware reference data for ports, berths, and trade lanes
- freight and market observations covering multiple years of candidate route data
- ingestion and validation workflows to preserve provenance and evidence
- research-stage documentation for derived or partially verified values

This sprint does not present the data as fully operational or independently approved market/berth truth; the repository explicitly flags where verification is still pending.

## Repository structure

- [01_Sprint_Plan](./01_Sprint_Plan/README.md) — sprint goals, scope, completed work, acceptance criteria, and remaining blockers
- [02_Data_Sources](./02_Data_Sources) — source register and data inventory for raw inputs and reference datasets
- [03_Processed_Data](./03_Processed_Data) — processed/cleaned copies of project datasets and dictionaries
- [04_Database](./04_Database) — schema, setup guidance, and database recreation notes
- [05_Port_and_TradeLane](./05_Port_and_TradeLane) — port, berth, and trade-lane reference material
- [06_Validation](./06_Validation) — validation scripts, checks, and related assets
- [07_Test_Evidence](./07_Test_Evidence) — read-only database snapshot, evidence index, and acceptance materials
- [08_Code_and_Handover](./08_Code_and_Handover/README.md) — execution guidance, environment setup, and handover notes
- [SPRINT1_ACCEPTANCE_REPORT.md](./SPRINT1_ACCEPTANCE_REPORT.md) — summary of the sprint’s status and recommendation

## Current status

The project is in a research and documentation stage rather than a production-ready operational system. The current evidence shows a working local data foundation with captured counts and validation results, but the repository still flags key limitations, including:

- unverified official BDI/BCI/BPI observations
- projected or partially verified berth and distance references
- inferred coal quantity units pending source confirmation
- missing original repeat-ingestion logs for historical claims

These are documented in the sprint acceptance report and validation evidence, and they are treated as explicit blockers for operational use.

## Recommended reading order

1. Start with [01_Sprint_Plan](./01_Sprint_Plan/README.md) for scope and acceptance context.
2. Review [02_Data_Sources](./02_Data_Sources) and [03_Processed_Data](./03_Processed_Data) to understand dataset provenance.
3. Read [04_Database](./04_Database) and [08_Code_and_Handover](./08_Code_and_Handover/README.md) for setup and execution details.
4. Check [07_Test_Evidence](./07_Test_Evidence) and [SPRINT1_ACCEPTANCE_REPORT.md](./SPRINT1_ACCEPTANCE_REPORT.md) for validation results and known limitations.

## Prerequisites and local database startup

To run the SQL checks, you need:

- Docker Engine/Desktop with Docker Compose v2.
- A free local TCP port `5433` (the container continues to use port `5432`).
- A local `.env` file in the repository root with `POSTGRES_PASSWORD` set.

The repository-root `.env` is the single active configuration file for both
Compose and the Python scripts. Do not create a second `.env` in a subfolder.

Create or update the root `.env` with these local values (do not overwrite an
existing file or credentials):

```dotenv
POSTGRES_PASSWORD=your-unique-local-password
DATABASE_URL=postgresql://freightiq:URL-ENCODED-PASSWORD@localhost:5433/freightiq
```

Replace the example password in both values, URL-encoding special characters
in `DATABASE_URL`. The Compose file sets the database name and user to
`freightiq`. Keep credentials private; `.env*` files are ignored by Git.
Create the root `.env` locally if it does not exist.

From the repository root, start the database and wait until it is healthy:

```sh
docker compose --env-file .env -f 04_Database/docker-compose.yml up -d
docker compose --env-file .env -f 04_Database/docker-compose.yml ps
docker compose --env-file .env -f 04_Database/docker-compose.yml exec timescaledb pg_isready -U freightiq -d freightiq
```

For a **new, empty database volume**, Compose initializes the schema from
[04_Database/sql/001_schema.sql](./04_Database/sql/001_schema.sql). Initialization
scripts run only on the first start of an empty volume; starting Compose does
not migrate an existing database. Do not remove volumes, drop tables, or replay
schema scripts against a database containing data. See
[04_Database/README.md](./04_Database/README.md) before any recreation or
migration.

## Run the SQL validation queries

The complete set of seven read-only database checks is in
[06_Validation/sql/validation_queries.sql](./06_Validation/sql/validation_queries.sql).
With the database running and the shell at the repository root, execute the
whole file with `psql` inside the database container:

```sh
docker compose --env-file .env -f 04_Database/docker-compose.yml exec -T timescaledb \
  psql -v ON_ERROR_STOP=1 -U freightiq -d freightiq \
  < 06_Validation/sql/validation_queries.sql
```

The checks report freight row counts and date coverage, duplicate keys,
required destination ports, freight data classifications, BDI/BCI/BPI market
coverage, weekly gaps for observed indices, and berth verification status.
Some queries can return no rows when there are no duplicates or no missing
weeks. The approved-observed-index coverage query may show zero records: the
current project evidence marks this check **blocked**, not passed.

For an interactive SQL session instead:

```sh
docker compose --env-file .env -f 04_Database/docker-compose.yml exec timescaledb \
  psql -U freightiq -d freightiq
```

Then paste SQL statements at the `freightiq=#` prompt and exit with `\q`.

## Optional ingestion and Python checks

Python is not required for the SQL queries. To run the included scripts, use
Python 3.10 or later and install their dependencies in a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "psycopg[binary]" python-dotenv pandas
```

The repository does not include a dependency lockfile or a root-level
`requirements.txt`. Before running the scripts, make sure `DATABASE_URL` from
the root `.env` is exported in the current shell; the scripts read it through
`08_Code_and_Handover/scripts/db_config.py`. Run commands from the repository
root. The bundled script copies are under `08_Code_and_Handover/scripts/`:

```sh
python 08_Code_and_Handover/scripts/ingest_route_config.py \
  --input 05_Port_and_TradeLane/route_configuration.csv
python 08_Code_and_Handover/scripts/ingest_freight_csv.py \
  --input 08_Code_and_Handover/scripts/FreightIQ_Freight_Forecasting_2021_2025_Reviewed.csv
python 08_Code_and_Handover/scripts/ingest_brent_market.py
python 08_Code_and_Handover/scripts/ingest_coal_trade_volumes.py
```

Run ingestion only against a new/disposable development database after schema
initialization, and in the order shown: route configuration before freight.
The Brent and coal scripts use bundled CSV fallbacks. Some original raw inputs
described in the source inventory are not present in this checkout. These
importers write to the database; safe-to-rerun conflict behavior does not make
them read-only.

Additional script behavior:

- `python 06_Validation/scripts/validate_indices.py` checks local index CSV
  inputs. It uses daily files under `data/indices/` when available and
  otherwise checks the packaged weekly CSV.
- `python 08_Code_and_Handover/scripts/export_weekly_indices.py` rebuilds the
  packaged weekly CSV only when all three BDI/BCI/BPI daily files exist under
  `data/indices/`; otherwise it checks and reuses the packaged weekly data.
- `08_Code_and_Handover/scripts/ingest_weekly_indices.sql` is an optional,
  **mutating** loader for 771 community-derived, unverified weekly index rows.
  It requires the weekly CSV staged at `/tmp/weekly_indices_2021_2025.csv`
  inside the database container and a matching source row in `data_sources`.
  These records must not be presented as approved observed Baltic Exchange
  data.
- `python 06_Validation/scripts/validate_db.py` runs database checks and
  appends results to `validation_results`; running it again adds another set
  of rows. Use the read-only SQL file above when you only need to inspect the
  database.

The SQL seeds
[002_seed_berths_research.sql](./04_Database/sql/002_seed_berths_research.sql)
and
[003_extend_derived_distance_proxies.sql](./04_Database/sql/003_extend_derived_distance_proxies.sql)
are optional research data scripts, not required for the read-only checks.
Review their contents and provenance before applying them to a new database.
They do not independently verify berth details or route distances.

## Notes

This repository is best understood as an evidence-backed foundation package for FreightIQ: it preserves the project’s current state, documents assumptions, and makes the validation status visible without overstating certainty. It is intended for research, handover review, and follow-on verification work rather than live operational deployment.
