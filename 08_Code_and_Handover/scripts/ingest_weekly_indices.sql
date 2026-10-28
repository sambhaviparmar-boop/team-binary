BEGIN;

CREATE TEMP TABLE stage_indices (
    date date,
    index_code text,
    value numeric,
    unit text,
    source text,
    source_url text,
    source_type text,
    verification_status text,
    aggregation_method text
);

\copy stage_indices (date,index_code,value,unit,source,source_url,source_type,verification_status,aggregation_method) FROM '/tmp/weekly_indices_2021_2025.csv' WITH (FORMAT csv, HEADER true)

DO $$
BEGIN
    IF (SELECT COUNT(*) FROM stage_indices) <> 771 THEN
        RAISE EXCEPTION 'Expected 771 rows in staging table';
    END IF;

    IF (SELECT COUNT(DISTINCT index_code) FROM stage_indices) <> 3 THEN
        RAISE EXCEPTION 'Expected exactly 3 index codes';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM stage_indices
        GROUP BY date, index_code
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate date/index combinations found';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM stage_indices
        WHERE index_code NOT IN ('BDI','BCI','BPI')
           OR value <= 0
           OR unit <> 'index_points'
           OR verification_status <> 'unverified'
    ) THEN
        RAISE EXCEPTION 'Unexpected or invalid index records found';
    END IF;

    IF EXISTS (
        SELECT index_code
        FROM stage_indices
        GROUP BY index_code
        HAVING COUNT(*) <> 257
    ) THEN
        RAISE EXCEPTION 'Expected 257 rows per index';
    END IF;
END $$;

INSERT INTO market_observations (
    observed_at,
    source_id,
    indicator_code,
    value,
    unit,
    frequency,
    data_type,
    source_record_ref,
    notes
)
SELECT
    s.date::timestamp AT TIME ZONE 'UTC',
    ds.source_id,
    s.index_code,
    s.value,
    s.unit,
    'weekly',
    'derived',
    s.source_url || '#' || s.index_code || '/' || s.date::text,
    'Community-maintained dataset; unverified; Friday-ending weekly value using last available observation. Not independently verified as official Baltic Exchange data.'
FROM stage_indices s
CROSS JOIN (
    SELECT source_id
    FROM data_sources
    WHERE source_name = 'BDI BCI BPI weekly historical indices - community dataset'
) ds
ON CONFLICT (observed_at, source_id, indicator_code) DO NOTHING;

COMMIT;
