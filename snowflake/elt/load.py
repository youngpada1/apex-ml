import os
from datetime import datetime
from typing import Any

import snowflake.connector
from snowflake.connector import DictCursor


def get_snowflake_connection():
    from pathlib import Path

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator='SNOWFLAKE_JWT',
        private_key_file=str(Path.home() / '.ssh' / 'snowflake_key.p8'),
        database=os.getenv("SNOWFLAKE_DATABASE", "APEXML_DEV"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ETL_WH_DEV"),
        role=os.getenv("SNOWFLAKE_ROLE", "DATA_ENGINEER_DEV"),
    )


def load_sessions(conn, sessions: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for session in sessions:
        cursor.execute(
            """
            MERGE INTO APEXML_DEV.RAW.SESSIONS AS target
            USING (SELECT
                %(session_key)s AS session_key,
                %(session_name)s AS session_name,
                %(session_type)s AS session_type,
                %(date_start)s AS date_start,
                %(date_end)s AS date_end,
                %(gmt_offset)s AS gmt_offset,
                %(location)s AS location,
                %(country_name)s AS country_name,
                %(circuit_short_name)s AS circuit_short_name,
                %(year)s AS year,
                %(ingested_at)s AS ingested_at
            ) AS source
            ON target.session_key = source.session_key
            WHEN MATCHED THEN
                UPDATE SET
                    session_name = source.session_name,
                    session_type = source.session_type,
                    date_start = source.date_start,
                    date_end = source.date_end,
                    gmt_offset = source.gmt_offset,
                    location = source.location,
                    country_name = source.country_name,
                    circuit_short_name = source.circuit_short_name,
                    year = source.year,
                    ingested_at = source.ingested_at
            WHEN NOT MATCHED THEN
                INSERT (session_key, session_name, session_type, date_start, date_end,
                        gmt_offset, location, country_name, circuit_short_name, year, ingested_at)
                VALUES (source.session_key, source.session_name, source.session_type,
                        source.date_start, source.date_end, source.gmt_offset, source.location,
                        source.country_name, source.circuit_short_name, source.year, source.ingested_at)
            """,
            session,
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def load_drivers(conn, drivers: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for driver in drivers:
        cursor.execute(
            """
            MERGE INTO APEXML_DEV.RAW.DRIVERS AS target
            USING (SELECT
                %(driver_number)s AS driver_number,
                %(session_key)s AS session_key,
                %(broadcast_name)s AS broadcast_name,
                %(full_name)s AS full_name,
                %(name_acronym)s AS name_acronym,
                %(team_name)s AS team_name,
                %(team_colour)s AS team_colour,
                %(headshot_url)s AS headshot_url,
                %(country_code)s AS country_code,
                %(ingested_at)s AS ingested_at
            ) AS source
            ON target.driver_number = source.driver_number AND target.session_key = source.session_key
            WHEN MATCHED THEN
                UPDATE SET
                    broadcast_name = source.broadcast_name,
                    full_name = source.full_name,
                    name_acronym = source.name_acronym,
                    team_name = source.team_name,
                    team_colour = source.team_colour,
                    headshot_url = source.headshot_url,
                    country_code = source.country_code,
                    ingested_at = source.ingested_at
            WHEN NOT MATCHED THEN
                INSERT (driver_number, session_key, broadcast_name, full_name, name_acronym,
                        team_name, team_colour, headshot_url, country_code, ingested_at)
                VALUES (source.driver_number, source.session_key, source.broadcast_name, source.full_name,
                        source.name_acronym, source.team_name, source.team_colour, source.headshot_url,
                        source.country_code, source.ingested_at)
            """,
            driver,
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def load_laps(conn, laps: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for lap in laps:
        lap_params = {
            "session_key": lap.get("session_key"),
            "driver_number": lap.get("driver_number"),
            "lap_number": lap.get("lap_number"),
            "lap_duration": lap.get("lap_duration"),
            "duration_sector_1": lap.get("duration_sector_1"),
            "duration_sector_2": lap.get("duration_sector_2"),
            "duration_sector_3": lap.get("duration_sector_3"),
            "is_pit_out_lap": lap.get("is_pit_out_lap"),
            "date_start": lap.get("date_start"),
            "ingested_at": lap.get("ingested_at"),
        }
        cursor.execute(
            """
            MERGE INTO APEXML_DEV.RAW.LAPS AS target
            USING (SELECT
                %(session_key)s AS session_key,
                %(driver_number)s AS driver_number,
                %(lap_number)s AS lap_number,
                %(lap_duration)s AS lap_duration,
                %(duration_sector_1)s AS segment_1_duration,
                %(duration_sector_2)s AS segment_2_duration,
                %(duration_sector_3)s AS segment_3_duration,
                %(is_pit_out_lap)s AS is_pit_out_lap,
                %(date_start)s AS date_start,
                %(ingested_at)s AS ingested_at
            ) AS source
            ON target.session_key = source.session_key
                AND target.driver_number = source.driver_number
                AND target.lap_number = source.lap_number
            WHEN MATCHED THEN
                UPDATE SET
                    lap_duration = source.lap_duration,
                    segment_1_duration = source.segment_1_duration,
                    segment_2_duration = source.segment_2_duration,
                    segment_3_duration = source.segment_3_duration,
                    is_pit_out_lap = source.is_pit_out_lap,
                    date_start = source.date_start,
                    ingested_at = source.ingested_at
            WHEN NOT MATCHED THEN
                INSERT (session_key, driver_number, lap_number, lap_duration,
                        segment_1_duration, segment_2_duration, segment_3_duration,
                        is_pit_out_lap, date_start, ingested_at)
                VALUES (source.session_key, source.driver_number, source.lap_number, source.lap_duration,
                        source.segment_1_duration, source.segment_2_duration, source.segment_3_duration,
                        source.is_pit_out_lap, source.date_start, source.ingested_at)
            """,
            lap_params,
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def load_positions(conn, positions: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for position in positions:
        position_params = {
            "session_key": position.get("session_key"),
            "driver_number": position.get("driver_number"),
            "date": position.get("date"),
            "position": position.get("position"),
            "ingested_at": position.get("ingested_at"),
        }
        cursor.execute(
            """
            MERGE INTO APEXML_DEV.RAW.POSITIONS AS target
            USING (SELECT
                %(session_key)s AS session_key,
                %(driver_number)s AS driver_number,
                %(date)s AS date,
                %(position)s AS position,
                %(ingested_at)s AS ingested_at
            ) AS source
            ON target.session_key = source.session_key
                AND target.driver_number = source.driver_number
                AND target.date = source.date
            WHEN MATCHED THEN
                UPDATE SET
                    position = source.position,
                    ingested_at = source.ingested_at
            WHEN NOT MATCHED THEN
                INSERT (session_key, driver_number, date, position, ingested_at)
                VALUES (source.session_key, source.driver_number, source.date, source.position, source.ingested_at)
            """,
            position_params,
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def load_all(data: dict[str, list[dict[str, Any]]]):
    conn = get_snowflake_connection()

    try:
        # Ensure warehouse is active
        cursor = conn.cursor()
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "ETL_WH_DEV")
        cursor.execute(f"ALTER WAREHOUSE {warehouse} RESUME IF SUSPENDED")
        cursor.close()

        sessions_count = load_sessions(conn, data["sessions"])
        print(f"Loaded {sessions_count} sessions")

        drivers_count = load_drivers(conn, data["drivers"])
        print(f"Loaded {drivers_count} drivers")

        laps_count = load_laps(conn, data["laps"])
        print(f"Loaded {laps_count} laps")

        positions_count = load_positions(conn, data["positions"])
        print(f"Loaded {positions_count} positions")

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    from extract import extract_session_data
    import asyncio

    if len(sys.argv) < 2:
        print("Usage: python load.py <session_key>")
        sys.exit(1)

    session_key = int(sys.argv[1])
    data = asyncio.run(extract_session_data(session_key))
    load_all(data)