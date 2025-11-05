{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'sessions') }}
),

cleaned AS (
    SELECT
        session_key,
        session_name,
        session_type,
        date_start,
        date_end,
        gmt_offset,
        location,
        country_name,
        circuit_short_name,
        year,
        ingested_at,
        CASE
            WHEN date_start IS NULL OR date_end IS NULL THEN FALSE
            WHEN date_end < date_start THEN FALSE
            ELSE TRUE
        END AS is_valid_session
    FROM source
)

SELECT * FROM cleaned
WHERE is_valid_session = TRUE
