"""
Load new/recent F1 race data from OpenF1 API (incremental loads for daily automation).
This script fetches recent Race sessions (last 30 days or current/last year) and loads only new data.
Designed to be run daily via GitHub Actions.
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from extract import extract_session_data
from load import load_all
import httpx

# Add parent directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from library.connection import connection_manager
from library.config import get_settings

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')


async def get_recent_race_sessions():
    """Fetch recent Race sessions from the API (current + last year)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        current_year = datetime.now().year
        last_year = current_year - 1

        # Get race sessions for current and last year
        response = await client.get(
            "https://api.openf1.org/v1/sessions",
            params={"session_name": "Race", "year": f">={last_year}"}
        )
        response.raise_for_status()
        sessions = response.json()

        # Sort by session_key to load chronologically
        sessions.sort(key=lambda s: s.get('session_key', 0))
        return sessions


def get_loaded_session_keys():
    """Get list of session_keys already loaded in Snowflake."""
    settings = get_settings()
    with connection_manager.get_connection(schema="RAW") as conn:
        cursor = conn.cursor()
        # Query uses environment-specific database from settings
        query = f"SELECT DISTINCT session_key FROM {settings.snowflake_database}.RAW.SESSIONS"
        cursor.execute(query)
        loaded_keys = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return loaded_keys


async def load_new_data():
    """Load new race data that hasn't been loaded yet."""
    settings = get_settings()

    print("="*80, flush=True)
    print("F1 INCREMENTAL DATA LOAD", flush=True)
    print(f"Environment: {settings.environment.upper()}", flush=True)
    print(f"Database: {settings.snowflake_database}", flush=True)
    print(f"Started at: {datetime.now().isoformat()}", flush=True)
    print("="*80, flush=True)

    # Get recent race sessions from API
    print("\n[1/3] Fetching recent race sessions from OpenF1 API...", flush=True)
    recent_sessions = await get_recent_race_sessions()
    print(f"Found {len(recent_sessions)} recent race sessions", flush=True)

    # Get already loaded sessions
    print("\n[2/3] Checking what's already loaded in Snowflake...", flush=True)
    loaded_keys = get_loaded_session_keys()
    print(f"Already loaded: {len(loaded_keys)} sessions", flush=True)

    # Filter to only new sessions
    new_sessions = [s for s in recent_sessions if s['session_key'] not in loaded_keys]
    print(f"New sessions to load: {len(new_sessions)}", flush=True)

    if not new_sessions:
        print("\nAll recent sessions already loaded. Nothing to do.", flush=True)
        return

    # Load each new session
    print("\n[3/3] Loading new sessions...", flush=True)
    loaded_count = 0

    for i, session in enumerate(new_sessions, 1):
        session_key = session['session_key']
        session_name = session.get('session_name', 'Unknown')
        year = session.get('year', 'Unknown')
        location = session.get('location', 'Unknown')

        print(f"\n[{i}/{len(new_sessions)}] Loading session {session_key}: {session_name} - {location} ({year})", flush=True)

        try:
            # Extract data for this session
            data = await extract_session_data(session_key)

            # Load to Snowflake (will use environment-specific database from settings)
            load_all(data)

            loaded_count += 1
            print(f"  ✓ Loaded: {len(data['sessions'])} sessions, {len(data['drivers'])} drivers, "
                  f"{len(data['laps'])} laps, {len(data['positions'])} positions", flush=True)

        except Exception as e:
            print(f"  ✗ ERROR loading session {session_key}: {e}", flush=True)
            continue

    print("\n" + "="*80, flush=True)
    print(f"INCREMENTAL DATA LOAD COMPLETED", flush=True)
    print(f"Successfully loaded: {loaded_count}/{len(new_sessions)} sessions", flush=True)
    print(f"Finished at: {datetime.now().isoformat()}", flush=True)
    print("="*80, flush=True)


if __name__ == "__main__":
    asyncio.run(load_new_data())
