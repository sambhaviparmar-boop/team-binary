import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg

from db_config import get_database_url


REQUIRED_COLUMNS = {
    "route_id",
    "origin_country",
    "origin_port",
    "destination_country",
    "destination_port",
    "commodity",
    "vessel_class",
    "route_distance_nm",
    "distance_method",
}


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_decimal(value, field, route_id):
    text = clean_text(value)
    if not text:
        return None

    try:
        number = Decimal(text)
    except InvalidOperation as error:
        raise ValueError(
            f"Invalid numeric value for {field} in route {route_id}: {text!r}"
        ) from error

    if not number.is_finite():
        raise ValueError(
            f"Invalid numeric value for {field} in route {route_id}: {text!r}"
        )
    return number


def read_routes(path):
    if not path.is_file():
        raise FileNotFoundError(f"Route configuration file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {sorted(missing_columns)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("Route configuration CSV contains no data rows.")

    required_values = REQUIRED_COLUMNS - {"route_distance_nm", "distance_method"}
    for row_number, row in enumerate(rows, start=2):
        route_id = clean_text(row.get("route_id")) or f"CSV row {row_number}"
        for column in required_values:
            if not clean_text(row.get(column)):
                raise ValueError(f"Missing {column} in route {route_id}.")
    return rows


def get_or_create_port(cur, name, country, latitude, longitude, source_id):
    cur.execute(
        """
        INSERT INTO ports (
            port_name, country, latitude, longitude,
            coordinate_status, source_id, notes
        )
        VALUES (
            %s, %s, %s, %s,
            'approximate_assumed', %s,
            'Coordinates from route configuration; not for navigation.'
        )
        ON CONFLICT (port_name, country)
        DO UPDATE SET
            latitude = COALESCE(ports.latitude, EXCLUDED.latitude),
            longitude = COALESCE(ports.longitude, EXCLUDED.longitude)
        RETURNING port_id
        """,
        (name, country, latitude, longitude, source_id),
    )
    result = cur.fetchone()
    if result is None:
        raise RuntimeError(f"Unable to resolve port {name!r} in {country!r}.")
    return result[0]


def upsert_trade_lane(cur, row, origin_id, destination_id, source_id, notes):
    route_id = clean_text(row["route_id"])
    cur.execute(
        """
        INSERT INTO trade_lanes (
            route_id, origin_port_id, destination_port_id, commodity,
            vessel_class, feasibility_status, direct_fixture_evidence,
            source_id, notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s, %s)
        ON CONFLICT (route_id)
        DO UPDATE SET
            origin_port_id = EXCLUDED.origin_port_id,
            destination_port_id = EXCLUDED.destination_port_id,
            commodity = EXCLUDED.commodity,
            vessel_class = EXCLUDED.vessel_class,
            feasibility_status = EXCLUDED.feasibility_status,
            source_id = EXCLUDED.source_id,
            notes = EXCLUDED.notes
        RETURNING lane_id
        """,
        (
            route_id,
            origin_id,
            destination_id,
            clean_text(row["commodity"]),
            clean_text(row["vessel_class"]),
            clean_text(row.get("feasibility_status")) or "candidate_scenario",
            source_id,
            notes,
        ),
    )
    result = cur.fetchone()
    if result is None:
        raise RuntimeError(f"Unable to resolve trade lane {route_id!r}.")
    return result[0]


def build_lane_notes(row):
    details = (
        row.get("route_evidence_and_limitations"),
        row.get("destination_port_constraint"),
        row.get("absolute_freight_scale_status"),
    )
    return "; ".join(filter(None, (clean_text(item) for item in details)))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Load candidate routes and derived distance proxies "
            "from route_configuration.csv"
        )
    )
    parser.add_argument("--input", required=True, help="Route configuration CSV")
    args = parser.parse_args()

    path = Path(args.input)
    rows = read_routes(path)
    database_url = get_database_url()

    processed = 0
    proxy_inserted = 0
    proxy_skipped_invalid = 0
    proxy_skipped_conflict = 0

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_sources (
                    source_name, publisher, dataset_type, units,
                    frequency, provenance_notes
                )
                VALUES (
                    %s, 'FreightIQ team', 'mixed', 'nautical miles',
                    'route-level', %s
                )
                ON CONFLICT (source_name, dataset_type)
                DO UPDATE SET
                    provenance_notes = EXCLUDED.provenance_notes
                RETURNING source_id
                """,
                (
                    path.name,
                    (
                        "Candidate route scenarios and approximate derived "
                        "distances. Coordinates and distance allowances require "
                        "review; direct fixture evidence was not established."
                    ),
                ),
            )
            source_id = cur.fetchone()[0]

            for row in rows:
                route_id = clean_text(row["route_id"])
                origin = clean_text(row["origin_port"])
                destination = clean_text(row["destination_port"])
                origin_country = clean_text(row["origin_country"])
                destination_country = clean_text(row["destination_country"])

                origin_latitude = parse_decimal(
                    row.get("origin_latitude_assumed"),
                    "origin_latitude_assumed",
                    route_id,
                )
                origin_longitude = parse_decimal(
                    row.get("origin_longitude_assumed"),
                    "origin_longitude_assumed",
                    route_id,
                )
                destination_latitude = parse_decimal(
                    row.get("destination_latitude_assumed"),
                    "destination_latitude_assumed",
                    route_id,
                )
                destination_longitude = parse_decimal(
                    row.get("destination_longitude_assumed"),
                    "destination_longitude_assumed",
                    route_id,
                )

                origin_id = get_or_create_port(
                    cur,
                    origin,
                    origin_country,
                    origin_latitude,
                    origin_longitude,
                    source_id,
                )
                destination_id = get_or_create_port(
                    cur,
                    destination,
                    destination_country,
                    destination_latitude,
                    destination_longitude,
                    source_id,
                )
                lane_id = upsert_trade_lane(
                    cur,
                    row,
                    origin_id,
                    destination_id,
                    source_id,
                    build_lane_notes(row),
                )

                distance = parse_decimal(
                    row.get("route_distance_nm"), "route_distance_nm", route_id
                )
                if distance is None or distance <= 0:
                    proxy_skipped_invalid += 1
                    processed += 1
                    continue

                distance_method = (
                    clean_text(row.get("distance_method"))
                    or "CSV-derived proxy; method unspecified"
                )
                coordinate_status = clean_text(
                    row.get("coordinate_source_status")
                )
                cur.execute(
                    """
                    INSERT INTO lane_distances (
                        lane_id, distance_nm, method, distance_status,
                        source_id, notes
                    )
                    VALUES (%s, %s, %s, 'derived', %s, %s)
                    ON CONFLICT (lane_id, distance_nm, method) DO NOTHING
                    """,
                    (
                        lane_id,
                        distance,
                        distance_method,
                        source_id,
                        (
                            "CSV proxy only; not a navigational or "
                            "AIS-verified sailing distance. "
                            + coordinate_status
                        ),
                    ),
                )

                if cur.rowcount == 1:
                    proxy_inserted += 1
                else:
                    proxy_skipped_conflict += 1

                processed += 1

            cur.execute("SELECT COUNT(*) FROM trade_lanes")
            lane_count = cur.fetchone()[0]

    print(f"Route config processed: {processed} rows")
    print(f"Candidate lanes currently in DB: {lane_count}")
    print(f"CSV proxy distances inserted: {proxy_inserted}")
    print(f"Proxies skipped (duplicate key): {proxy_skipped_conflict}")
    print(f"Invalid/missing distances skipped: {proxy_skipped_invalid}")
    print("Done. Existing distance records were not deleted or overwritten.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
