import os
from datetime import datetime
from typing import Any

import snowflake.connector
from snowflake.connector import DictCursor


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key_path=os.path.expanduser("~/.ssh/snowflake_key.p8"),
        database=os.getenv("SNOWFLAKE_DATABASE", "APEXML_DEV"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ETL_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE", "DATA_ENGINEER"),
    )


def load_sessions(conn, sessions: list[dict[str, Any]]) -> int:
    cursor = conn.cursor()
    count = 0

    for session in sessions:
        cursor.execute(
            """
            INSERT INTO sessions (
                session_key, session_name, date_start, date_end, gmt_offset,
                session_type, meeting_key, location, country_key, country_code,
                country_name, circuit_key, circuit_short_name, year, ingested_at
            ) VALUES (
                %(session_key)s, %(session_name)s, %(date_start)s, %(date_end)s,
                %(gmt_offset)s, %(session_type)s, %(meeting_key)s, %(location)s,
                %(country_key)s, %(country_code)s, %(country_name)s, %(circuit_key)s,
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
                session_key, driver_number, broadcast_name, full_name, name_acronym,
                team_name, team_colour, first_name, last_name, headshot_url,
                country_code, ingested_at
            ) VALUES (
                %(session_key)s, %(driver_number)s, %(broadcast_name)s, %(full_name)s,
                %(name_acronym)s, %(team_name)s, %(team_colour)s, %(first_name)s,
                %(last_name)s, %(headshot_url)s, %(country_code)s, %(ingested_at)s
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
                %(segments_sector_1)s, %(segments_sector_2)s, %(segments_sector_3)s,
                %(is_pit_out_lap)s, %(date_start)s, %(ingested_at)s
            )
            """,
            {
                "session_key": lap.get("session_key"),
                "driver_number": lap.get("driver_number"),
                "lap_number": lap.get("lap_number"),
                "lap_duration": lap.get("lap_duration"),
                "segments_sector_1": lap.get("segments_sector_1"),
                "segments_sector_2": lap.get("segments_sector_2"),
                "segments_sector_3": lap.get("segments_sector_3"),
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
                session_key, driver_number, position, position_timestamp, ingested_at
            ) VALUES (
                %(session_key)s, %(driver_number)s, %(position)s, %(date)s, %(ingested_at)s
            )
            """,
            {
                "session_key": position.get("session_key"),
                "driver_number": position.get("driver_number"),
                "position": position.get("position"),
                "date": position.get("date"),
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