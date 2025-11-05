{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'laps') }}
),

cleaned AS (
    SELECT
        session_key,
        driver_number,
        lap_number,
        lap_duration,
        segment_1_duration,
        segment_2_duration,
        segment_3_duration,
        is_pit_out_lap,
        date_start,
        ingested_at,
        COALESCE(segment_1_duration, 0) +
        COALESCE(segment_2_duration, 0) +
        COALESCE(segment_3_duration, 0) AS total_segment_time,
        CASE
            WHEN lap_duration IS NULL THEN FALSE
            WHEN lap_duration <= 0 THEN FALSE
            WHEN lap_duration > 300 THEN FALSE
            ELSE TRUE
        END AS is_valid_lap
    FROM source
)

SELECT * FROM cleaned
WHERE is_valid_lap = TRUE
