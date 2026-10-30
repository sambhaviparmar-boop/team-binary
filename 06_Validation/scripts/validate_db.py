
import sys
from pathlib import Path

import psycopg

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "08_Code_and_Handover" / "scripts"),
)
from db_config import get_database_url  # type: ignore[reportMissingImports]

DB_URL = get_database_url()

SOURCE_NAME = "BDI BCI BPI weekly historical indices - community dataset"

checks = [
    ("freight_row_count", "SELECT count(*) FROM freight_observations"),
    ("duplicate_date_record_ids", """
        SELECT count(*) FROM (
            SELECT assessment_date, record_id FROM freight_observations
            GROUP BY assessment_date, record_id HAVING count(*) > 1
        ) x
    """),
    ("nonpositive_rates", """
        SELECT count(*) FROM freight_observations
        WHERE freight_rate_usd_per_tonne <= 0 OR freight_rate_usd_per_tonne IS NULL
    """),
    ("rows_missing_port_names", """
        SELECT count(*) FROM freight_observations
        WHERE origin_port IS NULL OR destination_port IS NULL
           OR btrim(origin_port) = '' OR btrim(destination_port) = ''
    """),
    ("required_destination_ports_present", """
        SELECT count(DISTINCT destination_port) FROM freight_observations
        WHERE destination_port IN ('Paradip', 'Visakhapatnam', 'Haldia')
    """),
    ("candidate_lanes_count", "SELECT count(*) FROM trade_lanes"),
    ("community_derived_index_rows", """
        SELECT count(*) FROM market_observations mo
        JOIN data_sources ds ON ds.source_id = mo.source_id
        WHERE ds.source_name = %s AND mo.indicator_code IN ('BDI', 'BCI', 'BPI')
          AND mo.data_type = 'derived'
    """),
    ("community_derived_index_nonpositive_values", """
        SELECT count(*) FROM market_observations mo
        JOIN data_sources ds ON ds.source_id = mo.source_id
        WHERE ds.source_name = %s AND mo.indicator_code IN ('BDI', 'BCI', 'BPI')
          AND mo.data_type = 'derived' AND mo.value <= 0
    """),
    ("approved_observed_index_rows", """
        SELECT count(*) FROM market_observations
        WHERE indicator_code IN ('BDI', 'BCI', 'BPI') AND data_type = 'observed'
    """),
]

expected_values = {
    "freight_row_count": "14608",
    "duplicate_date_record_ids": "0",
    "nonpositive_rates": "0",
    "rows_missing_port_names": "0",
    "required_destination_ports_present": "3",
    "candidate_lanes_count": "10",
    "community_derived_index_rows": "771",
    "community_derived_index_nonpositive_values": "0",
    "approved_observed_index_rows": (
        "Verified observed index data required"
    ),
}



# Classify each database check using its established expected values.
def get_status(name, value):
    zero_checks = {
        "duplicate_date_record_ids",
        "nonpositive_rates",
        "rows_missing_port_names",
        "community_derived_index_nonpositive_values",
    }
    if name in zero_checks:
        return "passed" if value == 0 else "failed"

    expected = {
        "freight_row_count": (14608, "warning"),
        "required_destination_ports_present": (3, "failed"),
        "candidate_lanes_count": (10, "warning"),
        "community_derived_index_rows": (771, "warning"),
    }
    if name == "approved_observed_index_rows":
        return "blocked" if value == 0 else "warning"
    if name in expected:
        target, mismatch = expected[name]
        return "passed" if value == target else mismatch
    return "warning"


# Explain provenance limitations for checks that need evidence context.
def get_evidence(name, value):
    if name.startswith("community_derived_index_"):
        return (
            "Community-derived historical indices; "
            "not independently verified as official observations."
        )

    if name == "approved_observed_index_rows":
        if value == 0:
            return "No approved observed BDI/BCI/BPI records found."
        return "Records exist; verify source provenance before approval."

    if name == "freight_row_count":
        return "Freight observations include synthetic benchmark records."

    if name == "candidate_lanes_count":
        return "Lane count does not establish direct fixture evidence."

    return None


# Run all database checks, save results, and print coverage summaries.
def main():
    validation_results = []

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # Run validation checks and prepare their results.
            for name, sql in checks:
                if name.startswith("community_derived_index_"):
                    cur.execute(sql, (SOURCE_NAME,))
                else:
                    cur.execute(sql)

                value = cur.fetchone()[0]
                status = get_status(name, value)
                expected = expected_values.get(name)
                evidence = get_evidence(name, value)

                print(f"{name}: {value} [{status.upper()}]")
                validation_results.append(
                    (
                        name,
                        status,
                        str(value),
                        expected,
                        evidence,
                    )
                )

            # Persist results from this validation run.
            cur.executemany(
                """
                INSERT INTO validation_results (
                    check_name,
                    status,
                    observed_value,
                    expected_value,
                    evidence
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                validation_results,
            )

            print(
                f"\nSaved {len(validation_results)} validation "
                "results to validation_results."
            )

            # Community-derived historical index coverage.
            cur.execute(
                """
                SELECT
                    mo.indicator_code,
                    count(*) AS rows,
                    count(DISTINCT mo.observed_at) AS unique_dates,
                    min(mo.observed_at) AS first_date,
                    max(mo.observed_at) AS last_date
                FROM market_observations mo
                JOIN data_sources ds
                    ON ds.source_id = mo.source_id
                WHERE ds.source_name = %s
                  AND mo.indicator_code IN ('BDI', 'BCI', 'BPI')
                  AND mo.data_type = 'derived'
                GROUP BY mo.indicator_code
                ORDER BY mo.indicator_code
                """,
                (SOURCE_NAME,),
            )

            print("\nCommunity-derived index coverage:")
            for row in cur.fetchall():
                print(
                    f"  {row[0]}: rows={row[1]}, "
                    f"unique_dates={row[2]}, "
                    f"first={row[3]}, last={row[4]}"
                )

            # Freight rows by destination port.
            cur.execute(
                """
                SELECT destination_port, count(*)
                FROM freight_observations
                GROUP BY destination_port
                ORDER BY destination_port
                """
            )

            print("\nRows by destination:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

            # Freight dataset date coverage.
            cur.execute(
                """
                SELECT
                    min(assessment_date),
                    max(assessment_date),
                    count(DISTINCT assessment_date)
                FROM freight_observations
                """
            )

            print("\nFreight date coverage:", cur.fetchone())

        # The context manager commits inserts on successful exit.


if __name__ == "__main__":
    main()
