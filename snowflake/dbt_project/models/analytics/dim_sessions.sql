{{ config(materialized='table') }}

WITH sessions AS (
    SELECT * FROM {{ ref('stg_sessions') }}
)

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
    season,
    race_number,
    CURRENT_TIMESTAMP() AS updated_at
FROM sessions
ORDER BY season, race_number
