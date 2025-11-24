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
            INSERT INTO sessions (
                session_key, session_name, session_type, date_start, date_end,
                gmt_offset, location, country_name, circuit_short_name, year, ingested_at
            ) VALUES (
                %(session_key)s, %(session_name)s, %(session_type)s, %(date_start)s,
                %(date_end)s, %(gmt_offset)s, %(location)s, %(country_name)s,
                %(circuit_short_name)s, %(year)s, %(ingested_at)s
            )
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
            INSERT INTO drivers (
                driver_number, session_key, broadcast_name, full_name, name_acronym,
                team_name, team_colour, headshot_url, country_code, ingested_at
            ) VALUES (
                %(driver_number)s, %(session_key)s, %(broadcast_name)s, %(full_name)s,
                %(name_acronym)s, %(team_name)s, %(team_colour)s, %(headshot_url)s,
                %(country_code)s, %(ingested_at)s
            )
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
        cursor.execute(
            """
            INSERT INTO laps (
                session_key, driver_number, lap_number, lap_duration,
                segment_1_duration, segment_2_duration, segment_3_duration,
                is_pit_out_lap, date_start, ingested_at
            ) VALUES (
                %(session_key)s, %(driver_number)s, %(lap_number)s, %(lap_duration)s,
                %(duration_sector_1)s, %(duration_sector_2)s, %(duration_sector_3)s,
                %(is_pit_out_lap)s, %(date_start)s, %(ingested_at)s
            )
            """,
            {
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
            },
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def load_positions(conn, positions: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for position in positions:
        cursor.execute(
            """
            INSERT INTO positions (
                session_key, driver_number, date, position, ingested_at
            ) VALUES (
                %(session_key)s, %(driver_number)s, %(date)s, %(position)s, %(ingested_at)s
            )
            """,
            {
                "session_key": position.get("session_key"),
                "driver_number": position.get("driver_number"),
                "date": position.get("date"),
                "position": position.get("position"),
                "ingested_at": position.get("ingested_at"),
            },
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