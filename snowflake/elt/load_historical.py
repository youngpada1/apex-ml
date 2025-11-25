"""
Load all historical F1 race data from OpenF1 API.
This script fetches all Race sessions from 2023 onwards and loads them into Snowflake.
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from extract import extract_session_data, fetch_sessions
from load import load_all, get_snowflake_connection
import httpx

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')


async def get_all_race_sessions():
    """Fetch all Race sessions from the API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get all race sessions (API supports filtering by session_type)
        response = await client.get(
            "https://api.openf1.org/v1/sessions",
            params={"session_type": "Race"}
        )
        response.raise_for_status()
        sessions = response.json()

        # Sort by session_key to load chronologically
        sessions.sort(key=lambda s: s.get('session_key', 0))
        return sessions


def get_loaded_session_keys():
    """Get list of session_keys already loaded in Snowflake."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT session_key FROM APEXML_DEV.RAW.SESSIONS")
    loaded_keys = {row[0] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return loaded_keys


async def load_historical_data():
    """Load all historical race data that hasn't been loaded yet."""
    print("="*80)
    print("HISTORICAL F1 DATA LOAD")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print("="*80)

    # Get all race sessions from API
    print("\n[1/3] Fetching all race sessions from OpenF1 API...")
    all_sessions = await get_all_race_sessions()
    print(f"Found {len(all_sessions)} total race sessions")

    # Get already loaded sessions
    print("\n[2/3] Checking what's already loaded in Snowflake...")
    loaded_keys = get_loaded_session_keys()
    print(f"Already loaded: {len(loaded_keys)} sessions")

    # Filter to only new sessions
    new_sessions = [s for s in all_sessions if s['session_key'] not in loaded_keys]
    print(f"New sessions to load: {len(new_sessions)}")

    if not new_sessions:
        print("\nAll sessions already loaded. Nothing to do.")
        return

    # Load each new session
    print("\n[3/3] Loading new sessions...")
    for i, session in enumerate(new_sessions, 1):
        session_key = session['session_key']
        session_name = session.get('session_name', 'Unknown')
        year = session.get('year', 'Unknown')

        print(f"\n[{i}/{len(new_sessions)}] Loading session {session_key}: {session_name} ({year})")

        try:
            # Extract data for this session
            data = await extract_session_data(session_key)

            # Load to Snowflake
            load_all(data)

            print(f"  ✓ Loaded: {len(data['sessions'])} sessions, {len(data['drivers'])} drivers, "
                  f"{len(data['laps'])} laps, {len(data['positions'])} positions")

        except Exception as e:
            print(f"  ✗ ERROR loading session {session_key}: {e}")
            continue

    print("\n" + "="*80)
    print("HISTORICAL DATA LOAD COMPLETED")
    print(f"Finished at: {datetime.utcnow().isoformat()}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(load_historical_data())
