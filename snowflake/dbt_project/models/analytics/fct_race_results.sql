{{ config(materialized='table') }}

WITH sessions AS (
    SELECT * FROM {{ ref('stg_sessions') }}
    WHERE session_type = 'Race'
),

positions AS (
    SELECT * FROM {{ ref('stg_positions') }}
),

drivers AS (
    SELECT * FROM {{ ref('stg_drivers') }}
),

final_positions AS (
    SELECT
        p.session_key,
        p.driver_number,
        p.position AS final_position,
        s.session_name,
        s.circuit_short_name,
        s.location,
        s.year,
        s.date_start,
        d.full_name AS driver_name,
        d.team_name
    FROM positions p
    INNER JOIN sessions s ON p.session_key = s.session_key
    LEFT JOIN drivers d ON p.session_key = d.session_key
                       AND p.driver_number = d.driver_number
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY p.session_key, p.driver_number
        ORDER BY p.position_timestamp DESC
    ) = 1
)

SELECT
    session_key,
    driver_number,
    driver_name,
    team_name,
    final_position,
    session_name,
    circuit_short_name,
    location,
    year,
    date_start,
    CURRENT_TIMESTAMP() AS updated_at
FROM final_positions
ORDER BY session_key, final_position
