{{ config(materialized='table') }}

WITH laps AS (
    SELECT * FROM {{ ref('stg_laps') }}
),

sessions AS (
    SELECT * FROM {{ ref('stg_sessions') }}
),

drivers AS (
    SELECT * FROM {{ ref('stg_drivers') }}
),

lap_facts AS (
    SELECT
        l.session_key,
        l.driver_number,
        l.lap_number,
        l.lap_duration,
        l.segment_1_duration,
        l.segment_2_duration,
        l.segment_3_duration,
        l.is_pit_out_lap,
        s.session_type,
        s.circuit_short_name,
        s.location,
        s.country_name,
        s.season,
        s.race_number,
        d.team_name,
        d.full_name AS driver_name,
        ROW_NUMBER() OVER (
            PARTITION BY l.session_key, l.lap_number
            ORDER BY l.lap_duration
        ) AS lap_position,
        MIN(l.lap_duration) OVER (
            PARTITION BY l.session_key, l.driver_number
        ) AS driver_fastest_lap,
        MIN(l.lap_duration) OVER (
            PARTITION BY l.session_key
        ) AS session_fastest_lap
    FROM laps l
    INNER JOIN sessions s ON l.session_key = s.session_key
    LEFT JOIN drivers d ON l.session_key = d.session_key
                       AND l.driver_number = d.driver_number
    WHERE l.is_pit_out_lap = FALSE
)

SELECT
    session_key,
    driver_number,
    driver_name,
    team_name,
    lap_number,
    lap_duration,
    segment_1_duration,
    segment_2_duration,
    segment_3_duration,
    session_type,
    circuit_short_name,
    location,
    country_name,
    season,
    race_number,
    lap_position,
    CASE
        WHEN lap_duration = driver_fastest_lap THEN TRUE
        ELSE FALSE
    END AS is_driver_fastest_lap,
    CASE
        WHEN lap_duration = session_fastest_lap THEN TRUE
        ELSE FALSE
    END AS is_session_fastest_lap,
    CURRENT_TIMESTAMP() AS updated_at
FROM lap_facts
