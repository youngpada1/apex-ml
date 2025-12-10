{{ config(materialized='table') }}

WITH pit_stops AS (
    SELECT * FROM {{ ref('stg_pit_stops') }}
),

sessions AS (
    SELECT * FROM {{ ref('stg_sessions') }}
    WHERE session_type = 'Race'
),

drivers AS (
    SELECT * FROM {{ ref('stg_drivers') }}
)

SELECT
    ps.session_key,
    ps.driver_number,
    d.full_name AS driver_name,
    d.team_name,
    ps.pit_stop_number,
    ps.lap_number,
    ps.pit_stop_time,
    ps.pit_stop_duration,
    s.session_name,
    s.circuit_short_name,
    s.location,
    s.country_name,
    s.season,
    s.race_number,
    s.date_start AS race_date,
    CURRENT_TIMESTAMP() AS updated_at
FROM pit_stops ps
INNER JOIN sessions s ON ps.session_key = s.session_key
LEFT JOIN drivers d ON ps.session_key = d.session_key
                   AND ps.driver_number = d.driver_number
ORDER BY s.season, s.race_number, ps.driver_number, ps.pit_stop_number
