{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'drivers') }}
),

cleaned AS (
    SELECT
        driver_number,
        session_key,
        broadcast_name,
        full_name,
        name_acronym,
        team_name,
        team_colour,
        headshot_url,
        country_code,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY driver_number, session_key
            ORDER BY ingested_at DESC
        ) AS row_num
    FROM source
    WHERE driver_number IS NOT NULL
)

SELECT
    driver_number,
    session_key,
    broadcast_name,
    full_name,
    name_acronym,
    team_name,
    team_colour,
    headshot_url,
    country_code,
    ingested_at
FROM cleaned
WHERE row_num = 1
