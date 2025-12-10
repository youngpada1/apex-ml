{{ config(materialized='view') }}

WITH laps_source AS (
    SELECT * FROM {{ source('raw', 'laps') }}
),

pit_stops AS (
    SELECT
        session_key,
        driver_number,
        lap_number,
        date_start AS pit_stop_time,
        lap_duration AS pit_stop_duration,
        ingested_at,
        -- Calculate pit stop number for each driver in the session
        ROW_NUMBER() OVER (
            PARTITION BY session_key, driver_number
            ORDER BY lap_number
        ) AS pit_stop_number
    FROM laps_source
    WHERE is_pit_out_lap = TRUE
        AND lap_duration IS NOT NULL
        AND lap_duration > 0
)

SELECT * FROM pit_stops
