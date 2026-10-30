BEGIN;

CREATE TEMP TABLE stage_indices (
    observation_date date,
    index_code text,
    value numeric,
    unit text,
    source text,
    source_url text,
    source_type text,
    verification_status text,
    aggregation_method text
);

\copy stage_indices (observation_date, index_code, value, unit, source, source_url, source_type, verification_status, aggregation_method) FROM '/tmp/weekly_indices_2021_2025.csv' WITH (FORMAT csv, HEADER true)

DO $validate_indices$
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
        GROUP BY observation_date, index_code
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate date/index combinations found';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM stage_indices
        WHERE observation_date IS NULL
           OR EXTRACT(ISODOW FROM observation_date) <> 5
           OR index_code IS NULL
           OR index_code NOT IN ('BDI', 'BCI', 'BPI')
           OR value IS NULL
           OR value <= 0
           OR unit IS DISTINCT FROM 'index_points'
           OR source IS NULL
           OR btrim(source) = ''
           OR source_url IS NULL
           OR btrim(source_url) = ''
           OR source_type IS DISTINCT FROM 'community_maintained'
           OR verification_status IS DISTINCT FROM 'unverified'
           OR aggregation_method
                IS DISTINCT FROM 'last_available_observation_W-FRI'
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

    IF NOT EXISTS (
        SELECT 1
        FROM data_sources
        WHERE source_name =
            'BDI BCI BPI weekly historical indices - community dataset'
          AND dataset_type = 'derived'
    ) THEN
        RAISE EXCEPTION 'Weekly index data source has not been registered';
    END IF;
END;
$validate_indices$;

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
    stage.observation_date::timestamp AT TIME ZONE 'UTC',
    registered_source.source_id,
    stage.index_code,
    stage.value,
    stage.unit,
    'weekly',
    'derived',
    stage.source_url || '#' || stage.index_code || '/'
        || stage.observation_date::text,
    'Community-maintained dataset; unverified; Friday-ending weekly value using last available observation. Not independently verified as official Baltic Exchange data.'
FROM stage_indices AS stage
JOIN data_sources AS registered_source
    ON registered_source.source_name =
        'BDI BCI BPI weekly historical indices - community dataset'
    AND registered_source.dataset_type = 'derived'
ON CONFLICT (observed_at, source_id, indicator_code) DO NOTHING;

COMMIT;
