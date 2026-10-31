import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg

from db_config import get_database_url

DB_URL = get_database_url()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "03_Processed_Data"
RAW_CSV_CANDIDATES = (
    PROJECT_ROOT / "data" / "india_coal_imports_data.csv",
    SCRIPT_DIR / "india_coal_imports_data.csv",
)
CLEAN_CSV = PROCESSED_DIR / "india_australia_coal_imports_2021_2025_clean.csv"
TOP10_RAW_CSV = PROJECT_ROOT / "data" / "Top-10-Countries-wise-Coal-Import.csv"
TOP10_CLEAN_CSV = PROCESSED_DIR / "Top-10-Countries-wise-Coal-Import_cleaned.csv"
WORLD_2026_RAW_CSV = PROJECT_ROOT / "data" / "TradeData_10_23_2026_16_1_45.csv"
WORLD_2026_CLEAN_CSV = PROCESSED_DIR / "TradeData_10_23_2026_16_1_45_cleaned.csv"
SELECTED_CODES = ("27011100", "27011200", "27011910", "27011920", "27011990")
SOURCE_NAME = "India monthly import dataset (Australia origin)"
SOURCE_URL = "https://comtradeplus.un.org/"
CLEAN_FIELDS = (
    "month_start", "origin_country", "destination_country", "hs_code",
    "commodity_group", "quantity_value", "unit", "source_name", "source_url",
    "source_record_ref", "value_status", "notes",
)
TOP10_FIELDS = (
    "country", "reporting_year", "reporting_period", "coking_coal_mt",
    "non_coking_coal_mt", "total_coal_mt", "source_name", "source_url",
    "period_status", "classification", "notes",
)
WORLD_FIELDS = (
    "month", "period", "reporter_country", "partner_country", "commodity_code",
    "commodity_desc", "quantity_kg", "quantity_unit", "value_usd",
    "source_name", "source_url", "period_status", "classification", "notes",
)


# Convert valid finite numeric input while rejecting source placeholders.
def as_decimal(value):
    if value is None:
        return None
    value = str(value).strip()
    if value in {"", "-", "N/A", "NA", "NULL"}:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


# Parse YYYYMM values within the model's 2021-2025 coverage period.
def parse_yyyy_mm(raw_value):
    value = (raw_value or "").strip()
    if len(value) != 6 or not value.isdigit():
        return None
    year, month = int(value[:4]), int(value[4:])
    return (year, month) if 2021 <= year <= 2025 and 1 <= month <= 12 else None


# Locate the raw coal matrix, preferring the repository data directory.
def find_raw_csv():
    for path in RAW_CSV_CANDIDATES:
        if path.is_file():
            return path
    raise SystemExit(f"Missing coal import CSV; checked: {', '.join(map(str, RAW_CSV_CANDIDATES))}")


# Upsert source metadata and return its database identifier.
def safe_insert_source(
    cur, source_name, source_url, dataset_type, provenance_notes,
    units=None, frequency=None, coverage_start=None, coverage_end=None,
):
    cur.execute(
        """INSERT INTO data_sources (
            source_name, source_url, dataset_type, units, frequency,
            coverage_start, coverage_end, provenance_notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_name, dataset_type) DO UPDATE SET
            source_url = EXCLUDED.source_url, units = EXCLUDED.units,
            frequency = EXCLUDED.frequency, coverage_start = EXCLUDED.coverage_start,
            coverage_end = EXCLUDED.coverage_end,
            provenance_notes = EXCLUDED.provenance_notes
        RETURNING source_id""",
        (
            source_name, source_url, dataset_type, units, frequency,
            coverage_start, coverage_end, provenance_notes,
        ),
    )
    return cur.fetchone()[0]


# Create the coal-volume table when this importer is run on a new database.
def ensure_coal_trade_table(cur):
    cur.execute(
        """CREATE TABLE IF NOT EXISTS coal_trade_volumes (
            month_start DATE NOT NULL, origin_country TEXT NOT NULL,
            destination_country TEXT NOT NULL, hs_code TEXT NOT NULL,
            commodity_group TEXT NOT NULL, quantity_value NUMERIC(18,6) NOT NULL,
            unit TEXT NOT NULL DEFAULT 'million_tonnes',
            source_id BIGINT NOT NULL REFERENCES data_sources(source_id),
            source_record_ref TEXT,
            value_status TEXT NOT NULL DEFAULT 'reported'
                CHECK (value_status IN ('reported','suspected_missing','zero_reported')),
            notes TEXT,
            PRIMARY KEY (month_start, origin_country, destination_country, hs_code, source_id)
        )"""
    )


# Save the Top-10 file as a separate, explicitly unverified reference dataset.
def write_reference_top10_csv(path):
    if not TOP10_RAW_CSV.exists():
        return
    with TOP10_RAW_CSV.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=TOP10_FIELDS)
        writer.writeheader()
        writer.writerows({
            "country": (row.get("Country") or "").strip(),
            "reporting_year": "",
            "reporting_period": "unknown",
            "coking_coal_mt": row.get("Coking_Coal_MT", ""),
            "non_coking_coal_mt": row.get("Non_Coking_Coal_MT", ""),
            "total_coal_mt": row.get("Total_Coal_MT", ""),
            "source_name": "Top-10 Countries-wise Coal Import dataset",
            "source_url": "unknown",
            "period_status": "unverified_reference",
            "classification": "annual_country_reference",
            "notes": (
                "Reporting year and source URL were not embedded in the file, so the period is "
                "preserved as an unverified annual country reference rather than a validated "
                "2021-2025 time series."
            ),
        } for row in rows)
    print(f"Saved cleaned reference CSV to {path} ({len(rows)} rows).")


# Save world-total 2026 records separately from Australia-origin model data.
def write_reference_world_2026_csv(path):
    if not WORLD_2026_RAW_CSV.exists():
        return
    with WORLD_2026_RAW_CSV.open(encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source)
        filtered = [
            {
                "month": row.get("refMonth", "").strip(),
                "period": row.get("period", "").strip(),
                "reporter_country": row.get("reporterDesc", "").strip(),
                "partner_country": row.get("partnerDesc", "").strip(),
                "commodity_code": row.get("cmdCode", "").strip(),
                "commodity_desc": row.get("cmdDesc", "").strip(),
                "quantity_kg": row.get("qty", "").strip(),
                "quantity_unit": row.get("qtyUnitAbbr", "").strip(),
                "value_usd": row.get("primaryValue", "").strip(),
                "source_name": "UN Comtrade India coal import world totals (2026 monthly reference)",
                "source_url": "unknown",
                "period_status": "out_of_model_period_reference",
                "classification": "world_total_reference",
                "notes": (
                    "World aggregate imports are not Australia-specific and must not be treated as "
                    "Australian origin volumes. These observations are retained only as a separate "
                    "2026 reference dataset."
                ),
            }
            for row in rows
            if row.get("partnerDesc") == "World"
            and row.get("flowDesc") == "Import"
            and row.get("cmdCode") == "2701"
        ]
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=WORLD_FIELDS)
            writer.writeheader()
            writer.writerows(filtered)
    print(f"Saved cleaned 2026 reference CSV to {path} ({len(filtered)} rows).")


# Normalize the cleaned export or raw YYYYMM matrix into import-ready records.
def prepare_rows(rows):
    columns = set(rows[0])
    cleaned_columns = {
        "month_start", "origin_country", "destination_country", "hs_code",
        "commodity_group", "quantity_value", "unit",
    }
    if cleaned_columns.issubset(columns):
        prepared = []
        for row in rows:
            quantity = as_decimal(row.get("quantity_value"))
            if quantity is None:
                continue
            prepared.append({
                "month_start": row["month_start"],
                "origin_country": row["origin_country"],
                "destination_country": row["destination_country"],
                "hs_code": row["hs_code"],
                "hs_group": row["commodity_group"],
                "quantity_value": quantity,
                "unit": row["unit"],
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "source_record_ref": row.get("source_record_ref") or f"AUS.{row['hs_code']}",
                "value_status": row.get("value_status") or (
                    "zero_reported" if quantity == 0 else "reported"
                ),
                "notes": row.get("notes") or (
                    "Loaded from the supplied cleaned Australia-origin coal dataset; "
                    "unit/source lineage requires confirmation."
                ),
            })
        return prepared

    if "YYYYMM" in columns:
        notes = (
            "Australia-origin monthly import values from the source matrix were retained in their "
            "native scale, which appears to be million tonnes. Only non-overlapping direct coal "
            "HS categories were retained; 27011210 and 27011290 were excluded to avoid "
            "double-counting with aggregate 27011200."
        )
        prepared = []
        for row in rows:
            parsed = parse_yyyy_mm(row.get("YYYYMM"))
            if parsed is None:
                continue
            year, month = parsed
            for code in SELECTED_CODES:
                quantity = as_decimal(row.get(f"AUS.{code}"))
                if quantity is None:
                    continue
                prepared.append({
                    "month_start": f"{year:04d}-{month:02d}-01",
                    "origin_country": "Australia",
                    "destination_country": "India",
                    "hs_code": code,
                    "hs_group": "coal",
                    "quantity_value": quantity,
                    "unit": "million_tonnes",
                    "source_name": SOURCE_NAME,
                    "source_url": SOURCE_URL,
                    "source_record_ref": f"AUS.{code}",
                    "notes": notes,
                })
        return prepared

    raise SystemExit(
        "Coal CSV must contain cleaned month_start/quantity_value columns "
        "or a raw YYYYMM matrix."
    )


# Insert source metadata and upsert the prepared Australia-origin observations.
def import_rows(prepared):
    source_note = (
        "Cleaned Australia-origin monthly coal import subset for 2021-2025 extracted from the "
        "broader India import matrix. Only direct coal HS codes in the 2701 family were retained, "
        "excluding overlapping subcodes and coal products to avoid double counting. The source "
        "values appear to be in million tonnes and were preserved in their native unit rather than "
        "converted without a documented conversion factor."
    )
    with psycopg.connect(DB_URL) as connection, connection.cursor() as cursor:
        ensure_coal_trade_table(cursor)
        source_id = safe_insert_source(
            cursor, "India monthly import dataset (Australia origin, cleaned 2021-2025)",
            SOURCE_URL, "mixed",
            source_note, units="million tonnes", frequency="monthly",
            coverage_start="2021-01-01", coverage_end="2025-12-01",
        )
        cursor.executemany(
            """INSERT INTO coal_trade_volumes (
                month_start, origin_country, destination_country, hs_code, commodity_group,
                quantity_value, unit, source_id, source_record_ref, value_status, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (month_start, origin_country, destination_country, hs_code, source_id)
            DO UPDATE SET
                commodity_group = EXCLUDED.commodity_group,
                quantity_value = EXCLUDED.quantity_value, unit = EXCLUDED.unit,
                source_record_ref = EXCLUDED.source_record_ref,
                value_status = EXCLUDED.value_status, notes = EXCLUDED.notes""",
            (
                (
                    item["month_start"], item["origin_country"], item["destination_country"],
                    item["hs_code"], item["hs_group"], item["quantity_value"], item["unit"],
                    source_id, item["source_record_ref"],
                    item.get("value_status") or (
                        "zero_reported" if item["quantity_value"] == 0 else "reported"
                    ),
                    item["notes"],
                )
                for item in prepared
            )
        )
        safe_insert_source(
            cursor, "Top-10 Countries-wise Coal Import dataset", "unknown", "unknown",
            "Source URL and reporting year were not embedded in the file; the data is retained "
            "as an unverified annual country-reference dataset only.",
            units="million tonnes", frequency="annual",
        )
        safe_insert_source(
            cursor, "UN Comtrade India coal import world totals (2026 monthly reference)",
            "unknown", "mixed",
            "World aggregate records do not identify Australia as the origin and are retained "
            "only as a separate out-of-period reference dataset.",
            units="kg", frequency="monthly",
            coverage_start="2026-01-01", coverage_end="2026-07-01",
        )
        connection.commit()


# Write the normalized records used to reproduce and review the database import.
def write_clean_csv(prepared):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CLEAN_CSV.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=CLEAN_FIELDS)
        writer.writeheader()
        writer.writerows({
            "month_start": item["month_start"],
            "origin_country": item["origin_country"],
            "destination_country": item["destination_country"],
            "hs_code": item["hs_code"],
            "commodity_group": item["hs_group"],
            "quantity_value": str(item["quantity_value"]),
            "unit": item["unit"],
            "source_name": item["source_name"],
            "source_url": item["source_url"],
            "source_record_ref": item["source_record_ref"],
            "value_status": item.get("value_status") or (
                "zero_reported" if item["quantity_value"] == 0 else "reported"
            ),
            "notes": item["notes"],
        } for item in prepared)


# Run the source parsing, database upsert, and provenance CSV exports.
def main():
    raw_csv = find_raw_csv()
    with raw_csv.open("rb") as source:
        encoding = "utf-16" if source.read(2) in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    with raw_csv.open(encoding=encoding, newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise SystemExit("Coal import CSV contains no data rows.")

    prepared = prepare_rows(rows)
    if not prepared:
        raise SystemExit("No usable Australia-origin coal import rows were found for 2021-2025.")

    import_rows(prepared)
    write_clean_csv(prepared)
    write_reference_top10_csv(TOP10_CLEAN_CSV)
    write_reference_world_2026_csv(WORLD_2026_CLEAN_CSV)
    print(f"Prepared {len(prepared)} Australia-origin coal import rows from {raw_csv}.")
    print(f"Saved cleaned CSV to {CLEAN_CSV}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
