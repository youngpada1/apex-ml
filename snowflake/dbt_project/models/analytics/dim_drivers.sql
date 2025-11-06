{{ config(materialized='table') }}

WITH drivers AS (
    SELECT DISTINCT
        driver_number,
        full_name,
        name_acronym,
        team_name,
        team_colour,
        country_code,
        headshot_url
    FROM {{ ref('stg_drivers') }}
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY driver_number
        ORDER BY ingested_at DESC
    ) = 1
)

SELECT
    driver_number,
    full_name,
    name_acronym,
    team_name,
    team_colour,
    country_code,
    headshot_url,
    CURRENT_TIMESTAMP() AS updated_at
FROM drivers

