import argparse
import csv
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from db_config import get_database_url


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_raw_payload(row, record_id):
    raw_payload = clean_text(row.get("raw_payload"))
    if not raw_payload:
        raise ValueError(
            f"Missing raw_payload JSON in record {record_id}; "
            "country fields are unavailable."
        )

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid raw_payload JSON in record {record_id}: {error.msg}"
        ) from error

    if not isinstance(payload, dict):
        raise ValueError(
            f"Invalid raw_payload in record {record_id}: expected a JSON object."
        )
    return payload


def extract_country(row, field, record_id, payload=None):
    country = clean_text(row.get(field))
    if country:
        return country

    if payload is None:
        payload = parse_raw_payload(row, record_id)

    country = clean_text(payload.get(field))
    if not country:
        raise ValueError(
            f"Missing {field} in record {record_id}; "
            "the CSV field and raw_payload value are both empty."
        )
    return country


def parse_decimal(value, field, record_id):
    if value is None or not str(value).strip():
        return None

    try:
        number = Decimal(str(value).strip())
    except InvalidOperation as error:
        raise ValueError(
            f"Invalid numeric value for {field} in record {record_id}: "
            f"{value!r}"
        ) from error

    if not number.is_finite():
        raise ValueError(
            f"Invalid numeric value for {field} in record {record_id}: "
            f"{value!r}"
        )
    return number


def optional_decimal(row, column, payload, payload_field, record_id):
    value = clean_text(row.get(column))
    if not value and payload is not None:
        value = payload.get(payload_field)
    return parse_decimal(value, column, record_id)


def row_payload_if_needed(row, record_id):
    country_missing = any(
        not clean_text(row.get(field))
        for field in ("origin_country", "destination_country")
    )
    index_values_missing = any(
        not clean_text(row.get(column))
        for column in ("bdi_proxy_value", "bpi_proxy_value")
    )

    if country_missing or (
        index_values_missing and clean_text(row.get("raw_payload"))
    ):
        return parse_raw_payload(row, record_id)
    return None


def validate_csv(path):
    required = {
        "record_id", "assessment_date",
        "origin_port", "destination_port",
        "route_id", "commodity", "vessel_class",
        "freight_rate_usd_per_tonne",
    }

    row_count = 0
    coverage_start = None
    coverage_end = None

    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")

        for row in reader:
            row_count += 1
            record_id = clean_text(row.get("record_id")) or f"row {row_count + 1}"

            for column in required:
                if not clean_text(row.get(column)):
                    raise ValueError(f"Missing {column} in record {record_id}")

            try:
                assessment_date = date.fromisoformat(
                    clean_text(row["assessment_date"])
                )
            except ValueError as error:
                raise ValueError(
                    f"Invalid assessment_date in record {record_id}: "
                    f"{row['assessment_date']!r}"
                ) from error

            rate = parse_decimal(
                row["freight_rate_usd_per_tonne"],
                "freight_rate_usd_per_tonne",
                record_id,
            )
            if rate is None or rate <= 0:
                raise ValueError(
                    f"Freight rate must be greater than zero in record {record_id}."
                )

            payload = row_payload_if_needed(row, record_id)
            extract_country(row, "origin_country", record_id, payload)
            extract_country(row, "destination_country", record_id, payload)

            distance = optional_decimal(
                row, "route_distance_nm", payload, "route_distance_nm", record_id
            )
            if distance is not None and distance <= 0:
                raise ValueError(
                    f"route_distance_nm must be positive in record {record_id}."
                )
            optional_decimal(
                row, "bdi_proxy_value", payload, "bdi_value", record_id
            )
            optional_decimal(
                row, "bpi_proxy_value", payload, "bpi_value", record_id
            )

            if coverage_start is None or assessment_date < coverage_start:
                coverage_start = assessment_date
            if coverage_end is None or assessment_date > coverage_end:
                coverage_end = assessment_date

    if row_count == 0:
        raise ValueError("CSV file contains no data rows.")
    return row_count, coverage_start, coverage_end


def get_or_create_port(cur, name, country, cache):
    key = (name, country)

    if key in cache:
        return cache[key]

    cur.execute(
        """
        INSERT INTO ports (port_name, country, coordinate_status, notes)
        VALUES (%s, %s, 'unknown', %s)
        ON CONFLICT (port_name, country) DO NOTHING
        RETURNING port_id
        """,
        (
            name,
            country,
            "Imported from synthetic data; coordinates and "
            "physical limits require source verification."
        )
    )

    result = cur.fetchone()

    if result is None:
        cur.execute(
            """
            SELECT port_id FROM ports
            WHERE port_name = %s AND country = %s
            """,
            (name, country)
        )
        result = cur.fetchone()

    if result is None:
        raise RuntimeError(f"Unable to resolve port {name!r} in {country!r}.")

    port_id = result[0]
    cache[key] = port_id

    return port_id


def get_or_create_lane(cur, row, origin_id, dest_id, source_id, cache):
    route_id = clean_text(row["route_id"])

    if route_id in cache:
        return cache[route_id]

    cur.execute(
        """
        INSERT INTO trade_lanes (
            route_id, origin_port_id, destination_port_id,
            commodity, vessel_class, feasibility_status,
            direct_fixture_evidence, source_id, notes
        )
        VALUES (%s, %s, %s, %s, %s,
                'candidate_synthetic_scenario', FALSE, %s, %s)
        ON CONFLICT (route_id) DO NOTHING
        RETURNING lane_id
        """,
        (
            route_id,
            origin_id,
            dest_id,
            clean_text(row["commodity"]),
            clean_text(row["vessel_class"]),
            source_id,
            "Candidate synthetic scenario; not proof of an executed fixture."
        )
    )

    result = cur.fetchone()

    if result is None:
        cur.execute(
            "SELECT lane_id FROM trade_lanes WHERE route_id = %s",
            (route_id,)
        )
        result = cur.fetchone()

    if result is None:
        raise RuntimeError(f"Unable to resolve trade lane {route_id!r}.")

    lane_id = result[0]
    cache[route_id] = lane_id

    return lane_id


def main():
    parser = argparse.ArgumentParser(
        description="Import FreightIQ freight CSV into PostgreSQL."
    )
    parser.add_argument("--input", required=True, help="Input CSV path")
    args = parser.parse_args()

    path = Path(args.input)

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    row_count, coverage_start, coverage_end = validate_csv(path)

    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_sources (
                    source_name, publisher, source_url, dataset_type,
                    units, frequency, coverage_start, coverage_end,
                    provenance_notes
                )
                VALUES (%s, %s, %s, 'synthetic', 'USD/DMT',
                        'daily', %s, %s, %s)
                ON CONFLICT (source_name, dataset_type)
                DO UPDATE SET provenance_notes = EXCLUDED.provenance_notes
                RETURNING source_id
                """,
                (
                    path.name,
                    "FreightIQ team",
                    None,
                    coverage_start,
                    coverage_end,
                    "Synthetic freight data. BDI/BPI values are "
                    "synthetic proxies, not historical Baltic Exchange data."
                )
            )

            source_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO ingestion_runs (
                    source_id, file_name, status, rows_read, rows_attempted
                )
                VALUES (%s, %s, 'running', %s, 0)
                RETURNING ingestion_run_id
                """,
                (source_id, path.name, row_count)
            )

            run_id = cur.fetchone()[0]

        # Save the source and run before processing the data.
        conn.commit()

        attempted = 0
        try:
            port_cache = {}
            lane_cache = {}

            with conn.cursor() as cur:
                with path.open(encoding="utf-8-sig", newline="") as file:
                    for row in csv.DictReader(file):
                        attempted += 1
                        record_id = clean_text(row["record_id"])
                        payload = row_payload_if_needed(row, record_id)
                        origin = clean_text(row["origin_port"])
                        destination = clean_text(row["destination_port"])
                        origin_country = extract_country(
                            row, "origin_country", record_id, payload
                        )
                        destination_country = extract_country(
                            row, "destination_country", record_id, payload
                        )
                        origin_id = get_or_create_port(
                            cur, origin, origin_country, port_cache
                        )
                        destination_id = get_or_create_port(
                            cur, destination, destination_country, port_cache
                        )
                        lane_id = get_or_create_lane(
                            cur,
                            row,
                            origin_id,
                            destination_id,
                            source_id,
                            lane_cache,
                        )

                        route_distance = optional_decimal(
                            row,
                            "route_distance_nm",
                            payload,
                            "route_distance_nm",
                            record_id,
                        )
                        if route_distance is not None and route_distance <= 0:
                            raise ValueError(
                                f"route_distance_nm must be positive in "
                                f"record {record_id}."
                            )
                        bdi_value = optional_decimal(
                            row, "bdi_proxy_value", payload, "bdi_value", record_id
                        )
                        bpi_value = optional_decimal(
                            row, "bpi_proxy_value", payload, "bpi_value", record_id
                        )

                        cur.execute(
                            """
                            INSERT INTO freight_observations (
                                assessment_date, record_id, source_id, lane_id,
                                route_id, origin_port, destination_port,
                                commodity, vessel_class,
                                freight_rate_usd_per_tonne, rate_unit,
                                route_distance_nm, bdi_proxy_value,
                                bpi_proxy_value, target_data_type,
                                index_data_type, extreme_flag,
                                source_reference, assumptions_notes, raw_payload
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, 'synthetic',
                                %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (assessment_date, record_id)
                            DO UPDATE SET
                                source_id = EXCLUDED.source_id,
                                lane_id = EXCLUDED.lane_id,
                                route_id = EXCLUDED.route_id,
                                origin_port = EXCLUDED.origin_port,
                                destination_port = EXCLUDED.destination_port,
                                commodity = EXCLUDED.commodity,
                                vessel_class = EXCLUDED.vessel_class,
                                freight_rate_usd_per_tonne =
                                    EXCLUDED.freight_rate_usd_per_tonne,
                                rate_unit = EXCLUDED.rate_unit,
                                route_distance_nm = EXCLUDED.route_distance_nm,
                                bdi_proxy_value = EXCLUDED.bdi_proxy_value,
                                bpi_proxy_value = EXCLUDED.bpi_proxy_value,
                                target_data_type = EXCLUDED.target_data_type,
                                index_data_type = EXCLUDED.index_data_type,
                                extreme_flag = EXCLUDED.extreme_flag,
                                source_reference = EXCLUDED.source_reference,
                                assumptions_notes = EXCLUDED.assumptions_notes,
                                raw_payload = EXCLUDED.raw_payload,
                                imported_at = now()
                            """,
                            (
                                date.fromisoformat(
                                    clean_text(row["assessment_date"])
                                ),
                                record_id,
                                source_id,
                                lane_id,
                                clean_text(row["route_id"]),
                                origin,
                                destination,
                                clean_text(row["commodity"]),
                                clean_text(row["vessel_class"]),
                                parse_decimal(
                                    row["freight_rate_usd_per_tonne"],
                                    "freight_rate_usd_per_tonne",
                                    record_id,
                                ),
                                clean_text(row.get("rate_unit")) or None,
                                route_distance,
                                bdi_value,
                                bpi_value,
                                clean_text(row.get("index_data_type"))
                                or "synthetic_proxy_not_historical_observation",
                                clean_text(row.get("extreme_flag")).lower()
                                in ("true", "1", "yes"),
                                clean_text(row.get("source_reference")) or None,
                                clean_text(row.get("assumptions_notes")) or None,
                                Jsonb(row),
                            ),
                        )

                cur.execute(
                    """
                    UPDATE ingestion_runs
                    SET status = 'success', finished_at = now()
                    WHERE ingestion_run_id = %s
                    """,
                    (run_id,)
                )
                cur.execute(
                    """
                    UPDATE ingestion_runs
                    SET rows_attempted = %s
                    WHERE ingestion_run_id = %s
                    """,
                    (attempted, run_id),
                )

                cur.execute("SELECT count(*) FROM freight_observations")
                total = cur.fetchone()[0]

                cur.execute("SELECT count(*) FROM ports")
                ports = cur.fetchone()[0]

                cur.execute("SELECT count(*) FROM trade_lanes")
                lanes = cur.fetchone()[0]

            conn.commit()

        except Exception as error:
            conn.rollback()

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ingestion_runs
                    SET status = 'failed',
                        finished_at = now(),
                        rows_attempted = %s,
                        error_message = %s
                    WHERE ingestion_run_id = %s
                    """,
                    (attempted, str(error)[:2000], run_id)
                )

            conn.commit()
            raise

    print(f"Import completed: {row_count} rows processed.")
    print(f"Freight records: {total}, Ports: {ports}, Trade lanes: {lanes}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
