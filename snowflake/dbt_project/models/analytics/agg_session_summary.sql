{{ config(materialized='table') }}

WITH race_results AS (
    SELECT * FROM {{ ref('fct_race_results') }}
    WHERE session_name = 'Race'
),

lap_times AS (
    SELECT * FROM {{ ref('fct_lap_times') }}
    WHERE session_type = 'Race'
),

pit_stops AS (
    SELECT * FROM {{ ref('fct_pit_stops') }}
),

session_stats AS (
    SELECT
        rr.session_key,
        rr.session_name,
        rr.circuit_short_name,
        rr.location,
        rr.country_name,
        rr.season,
        rr.race_number,
        rr.date_start AS race_date,

        -- Winner info
        MAX(CASE WHEN rr.final_position = 1 THEN rr.driver_name END) AS race_winner,
        MAX(CASE WHEN rr.final_position = 1 THEN rr.team_name END) AS winning_team,

        -- Session statistics
        COUNT(DISTINCT rr.driver_number) AS total_drivers,
        COUNT(DISTINCT CASE WHEN rr.final_position IS NOT NULL THEN rr.driver_number END) AS classified_drivers,

        -- Lap statistics
        MIN(lt.lap_duration) AS fastest_lap_time,
        MAX(CASE WHEN lt.is_session_fastest_lap THEN lt.driver_name END) AS fastest_lap_driver,
        AVG(lt.lap_duration) AS avg_lap_time,
        MAX(lt.lap_number) AS total_laps,

        -- Pit stop statistics
        COUNT(ps.pit_stop_number) AS total_pit_stops,
        AVG(ps.pit_stop_duration) AS avg_pit_stop_duration,
        MIN(ps.pit_stop_duration) AS fastest_pit_stop

    FROM race_results rr
    LEFT JOIN lap_times lt
        ON rr.session_key = lt.session_key
    LEFT JOIN pit_stops ps
        ON rr.session_key = ps.session_key
    GROUP BY
        rr.session_key,
        rr.session_name,
        rr.circuit_short_name,
        rr.location,
        rr.country_name,
        rr.season,
        rr.race_number,
        rr.date_start
)

SELECT
    session_key,
    session_name,
    circuit_short_name,
    location,
    country_name,
    season,
    race_number,
    race_date,
    race_winner,
    winning_team,
    total_drivers,
    classified_drivers,
    fastest_lap_time,
    fastest_lap_driver,
    avg_lap_time,
    total_laps,
    total_pit_stops,
    avg_pit_stop_duration,
    fastest_pit_stop,
    CURRENT_TIMESTAMP() AS updated_at
FROM session_stats
ORDER BY season DESC, race_number DESC
