# FreightIQ Sprint 1 handover

## Package contents

- `scripts/` contains copies of the existing project configuration helper,
  ingestion scripts, and weekly index SQL/export assets.
- The database schema, seed scripts, Compose configuration, validation scripts,
  SQL checks, and existing index validation output are in their numbered
  package folders.
- Processed CSV copies are in `03_Processed_Data/`; raw datasets remain at the
  repository `data/` paths listed in the source inventory.
- [`.env.example`](.env.example) is a placeholder-only template. The actual
  local `.env`, passwords, and database connection string are intentionally
  excluded.

Package code files are archival copies of repository files. For routine work,
run the originals from the project root and review changes against the
repository version before using a packaged copy.

## Prerequisites and setup

1. Windows PowerShell, Docker Desktop with Compose v2, and Python 3.10+.
2. From the project root, configure the local environment:

   ```powershell
   Copy-Item .env.example .env
   # Edit .env locally; use a unique local password and matching URL.
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Start/check the local service:

   ```powershell
   docker compose up -d
   docker compose ps
   ```

4. On an empty database volume, Compose initializes the base schema. An
   existing volume is not recreated or migrated. Never use `docker compose
   down -v` or drop tables to prepare this submission.

The root project [`README.md`](../../README.md) is the authoritative original
project guide. Database setup details and the safe new-database recreation
procedure are in [`04_Database/README.md`](../04_Database/README.md).

## Execution order for a fresh local development database

Run from the original project root, not from inside this submission folder:

1. Confirm a fresh/empty local development volume and bring up Compose.
2. `python scripts/ingest_route_config.py --input data/route_configuration.csv`
3. `python scripts/ingest_freight_csv.py --input data/FreightIQ_Freight_Forecasting_2021_2025_Reviewed.csv`
4. `python scripts/ingest_brent_market.py`
5. `python scripts/ingest_coal_trade_volumes.py`
6. Review optional research seed/migration scripts before use. They are not
   necessary to recreate the recorded ingestion run and do not verify source
   values.
7. Run validation only when intentional: `python scripts/validate_db.py`
   appends check results to `validation_results`. It is not a read-only
   diagnostic.

Input paths are resolved relative to the project root rather than the current
working directory. Brent and coal importers check `data/` first and then the
bundled CSVs alongside the scripts. The bundled Brent/coal CSVs are exported or
cleaned formats, which the importers recognize separately from the original
raw inputs.

The weekly index transformation can be generated with
`python scripts/export_weekly_indices.py` when the three daily index source
files exist under `data/indices/`. If they are absent, the script validates and
reuses the packaged weekly file in `03_Processed_Data/`. Its SQL loader
requires staging the CSV at the path expected by `\copy`, and inserts
**derived, unverified** community data. Do not use this dataset to satisfy the
approved-observed index check.

Do not replay setup or ingestion against the existing project database just
to reproduce evidence. Idempotent import behavior does not make all other
commands read-only.

## Environment template

See [`.env.example`](.env.example). Replace placeholders locally; do not
commit or submit the populated `.env`.

## Troubleshooting

- **`DATABASE_URL is not set`:** configure local `.env` from the placeholder
  template or set the variable in the current PowerShell session.
- **Compose reports schema/table issues:** confirm whether the volume already
  existed. Compose init scripts are run for an empty database directory only;
  review migrations rather than deleting the volume.
- **Coal importer reports missing input:** it searches for
  `data/india_coal_imports_data.csv` and then the bundled
  `scripts/india_coal_imports_data.csv`.
- **Index validator/exporter reports missing daily inputs:** place the
  original BDI/BCI/BPI source files under `data/indices/`. Without those daily
  files, validation uses the packaged weekly CSV and export reuses that
  existing weekly output.
- **Index source validation does not make rows observed:** community source
  rows remain derived/unverified; use independently verified and approved
  sources only for the blocked check.
- **Distances or berth records appear operational:** they are proxy/research
  references. Confirm independently with current port and navigational sources.

## Handover notes

- Project-level disposition and blockers are summarized in
  [`SPRINT1_ACCEPTANCE_REPORT.md`](../../SPRINT1_ACCEPTANCE_REPORT.md).
- Existing recorded database counts: see the timestamped read-only snapshot
  and acceptance report.
- Known blockers: official verified BDI/BCI/BPI observations, coal-unit and
  export-provenance confirmation, independent route/berth verification, and
  original repeat-ingestion logs.
- No production credentials, `.env`, database dump, or large raw freight file
  is included.
- Software license: project code has an MIT license. Dataset redistribution
  terms must be reviewed separately.
