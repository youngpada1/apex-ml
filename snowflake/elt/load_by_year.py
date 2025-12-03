"""
Load F1 race data for specific years.
Usage: python load_by_year.py 2024
       python load_by_year.py 2024 2025 2023
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from extract import extract_session_data
from load import load_all
import httpx

# Add parent directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from library.connection import connection_manager

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')


async def get_race_sessions_by_year(year):
    """Fetch all Race sessions for a specific year."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.openf1.org/v1/sessions",
            params={"session_type": "Race", "year": year}
        )
        response.raise_for_status()
        sessions = response.json()
        sessions.sort(key=lambda s: s.get('session_key', 0))
        return sessions


def get_loaded_session_keys():
    """Get list of session_keys already loaded in Snowflake."""
    with connection_manager.get_connection(schema="RAW") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT session_key FROM APEXML_DEV.RAW.SESSIONS")
        loaded_keys = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return loaded_keys


async def load_year_data(year, force_reload=False):
    """Load all race data for a specific year."""
    print(f"\n{'='*80}")
    print(f"LOADING F1 DATA FOR YEAR {year}")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"{'='*80}")

    # Get all race sessions for this year
    print(f"\n[1/3] Fetching {year} race sessions from OpenF1 API...")
    year_sessions = await get_race_sessions_by_year(year)
    print(f"Found {len(year_sessions)} race sessions for {year}")

    if not year_sessions:
        print(f"No sessions found for year {year}")
        return

    # Get already loaded sessions
    print(f"\n[2/3] Checking what's already loaded...")
    loaded_keys = get_loaded_session_keys()

    # Filter sessions
    if force_reload:
        sessions_to_load = year_sessions
        print(f"Force reload: Loading all {len(sessions_to_load)} sessions")
    else:
        sessions_to_load = [s for s in year_sessions if s['session_key'] not in loaded_keys]
        print(f"Already loaded: {len(year_sessions) - len(sessions_to_load)} sessions")
        print(f"New sessions to load: {len(sessions_to_load)}")

    if not sessions_to_load:
        print(f"\nAll {year} sessions already loaded.")
        return

    # Load each session
    print(f"\n[3/3] Loading {year} sessions...")
    success_count = 0
    error_count = 0

    for i, session in enumerate(sessions_to_load, 1):
        session_key = session['session_key']
        session_name = session.get('session_name', 'Unknown')
        location = session.get('location', 'Unknown')

        print(f"\n[{i}/{len(sessions_to_load)}] Loading {session_key}: {session_name} - {location}")

        try:
            # Extract data
            data = await extract_session_data(session_key)

            # Load to Snowflake
            load_all(data)

            print(f"  ✓ Loaded: {len(data['sessions'])} sessions, {len(data['drivers'])} drivers, "
                  f"{len(data['laps'])} laps, {len(data['positions'])} positions")
            success_count += 1

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            error_count += 1
            continue

    print(f"\n{'='*80}")
    print(f"YEAR {year} LOAD COMPLETED")
    print(f"Success: {success_count}, Errors: {error_count}")
    print(f"Finished at: {datetime.now().isoformat()}")
    print(f"{'='*80}")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python load_by_year.py YEAR [YEAR2 YEAR3 ...]")
        print("Example: python load_by_year.py 2024")
        print("Example: python load_by_year.py 2024 2025 2023")
        sys.exit(1)

    years = [int(year) for year in sys.argv[1:]]

    print(f"{'='*80}")
    print(f"F1 DATA LOAD BY YEAR")
    print(f"Loading years: {', '.join(map(str, years))}")
    print(f"{'='*80}")

    for year in years:
        await load_year_data(year)

    print(f"\n{'='*80}")
    print("ALL YEARS LOADED SUCCESSFULLY")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
