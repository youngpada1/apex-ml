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

driver_stats AS (
    SELECT
        rr.driver_number,
        rr.driver_name,
        rr.team_name,
        rr.season,

        -- Race performance
        COUNT(DISTINCT rr.session_key) AS races_entered,
        COUNT(DISTINCT CASE WHEN rr.final_position <= 10 THEN rr.session_key END) AS points_finishes,
        COUNT(DISTINCT CASE WHEN rr.final_position = 1 THEN rr.session_key END) AS wins,
        COUNT(DISTINCT CASE WHEN rr.final_position <= 3 THEN rr.session_key END) AS podiums,

        -- Lap performance
        AVG(lt.lap_duration) AS avg_lap_time,
        MIN(lt.lap_duration) AS fastest_lap_time,
        COUNT(DISTINCT CASE WHEN lt.is_session_fastest_lap THEN lt.session_key END) AS fastest_laps,

        -- Pit stop performance
        COUNT(ps.pit_stop_number) AS total_pit_stops,
        AVG(ps.pit_stop_duration) AS avg_pit_stop_duration,
        MIN(ps.pit_stop_duration) AS fastest_pit_stop

    FROM race_results rr
    LEFT JOIN lap_times lt
        ON rr.session_key = lt.session_key
        AND rr.driver_number = lt.driver_number
    LEFT JOIN pit_stops ps
        ON rr.session_key = ps.session_key
        AND rr.driver_number = ps.driver_number
    GROUP BY
        rr.driver_number,
        rr.driver_name,
        rr.team_name,
        rr.season
)

SELECT
    driver_number,
    driver_name,
    team_name,
    season,
    races_entered,
    points_finishes,
    wins,
    podiums,
    avg_lap_time,
    fastest_lap_time,
    fastest_laps,
    total_pit_stops,
    avg_pit_stop_duration,
    fastest_pit_stop,
    CURRENT_TIMESTAMP() AS updated_at
FROM driver_stats
ORDER BY season DESC, wins DESC, podiums DESC
