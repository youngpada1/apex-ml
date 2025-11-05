{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'positions') }}
),

cleaned AS (
    SELECT
        session_key,
        driver_number,
        date AS position_timestamp,
        position,
        ingested_at,
        CASE
            WHEN position IS NULL THEN FALSE
            WHEN position < 1 OR position > 20 THEN FALSE
            ELSE TRUE
        END AS is_valid_position
    FROM source
)

SELECT * FROM cleaned
WHERE is_valid_position = TRUE
