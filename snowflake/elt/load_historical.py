"""
Script to load historical F1 data from OpenF1 API.
This will fetch all available sessions and load them into Snowflake.
"""
import asyncio
import sys
from extract import extract_session_data
from load import load_all
import httpx


async def get_all_sessions():
    """Fetch all available sessions from OpenF1 API."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.openf1.org/v1/sessions")
        response.raise_for_status()
        return response.json()


async def load_historical_data(year: int = None, session_type: str = None):
    """
    Load historical F1 data.

    Args:
        year: Filter by specific year (e.g., 2023, 2024). If None, loads all years.
        session_type: Filter by session type (e.g., 'Race', 'Qualifying'). If None, loads all types.
    """
    print("Fetching available sessions from OpenF1 API...")
    all_sessions = await get_all_sessions()

    # Filter sessions
    filtered_sessions = all_sessions

    if year:
        filtered_sessions = [s for s in filtered_sessions if s.get('year') == year]
        print(f"Filtering for year {year}")

    if session_type:
        filtered_sessions = [s for s in filtered_sessions if s.get('session_type') == session_type]
        print(f"Filtering for session type {session_type}")

    # Sort by year and date
    filtered_sessions = sorted(
        filtered_sessions,
        key=lambda s: (s.get('year', 0), s.get('date_start', ''))
    )

    print(f"\nFound {len(filtered_sessions)} sessions to load")

    # Show summary by year and type
    from collections import defaultdict
    summary = defaultdict(lambda: defaultdict(int))
    for session in filtered_sessions:
        summary[session.get('year')][session.get('session_type')] += 1

    print("\nSessions by year and type:")
    for year in sorted(summary.keys()):
        print(f"\n{year}:")
        for session_type, count in sorted(summary[year].items()):
            print(f"  {session_type}: {count}")

    # Ask for confirmation
    print(f"\nThis will load {len(filtered_sessions)} sessions into Snowflake.")
    response = input("Continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Load each session
    successful = 0
    failed = 0
    failed_sessions = []

    for i, session in enumerate(filtered_sessions, 1):
        session_key = session.get('session_key')
        session_name = session.get('session_name')
        session_type_val = session.get('session_type')
        year_val = session.get('year')

        print(f"\n[{i}/{len(filtered_sessions)}] Loading {year_val} {session_name} ({session_type_val}) - Session Key: {session_key}")

        try:
            # Extract data for this session
            data = await extract_session_data(session_key)

            # Load into Snowflake
            load_all(data)
            successful += 1

        except Exception as e:
            print(f"ERROR loading session {session_key}: {e}")
            failed += 1
            failed_sessions.append((session_key, session_name, year_val, str(e)))
            # Continue with next session

    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Total sessions: {len(filtered_sessions)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")

    if failed_sessions:
        print(f"\nFailed sessions:")
        for session_key, session_name, year_val, error in failed_sessions:
            print(f"  {year_val} {session_name} (Key: {session_key}) - {error}")

    print(f"{'='*80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load historical F1 data from OpenF1 API")
    parser.add_argument("--year", type=int, help="Filter by year (e.g., 2023, 2024)")
    parser.add_argument("--type", type=str, help="Filter by session type (e.g., Race, Qualifying)")
    parser.add_argument("--list", action="store_true", help="List available sessions without loading")

    args = parser.parse_args()

    if args.list:
        # Just list available sessions
        async def list_sessions():
            sessions = await get_all_sessions()
            from collections import defaultdict
            summary = defaultdict(lambda: defaultdict(int))
            for session in sessions:
                summary[session.get('year')][session.get('session_type')] += 1

            print("\nAvailable sessions by year and type:")
            for year in sorted(summary.keys()):
                print(f"\n{year}:")
                for session_type, count in sorted(summary[year].items()):
                    print(f"  {session_type}: {count}")

            print(f"\nTotal sessions: {len(sessions)}")

        asyncio.run(list_sessions())
    else:
        asyncio.run(load_historical_data(year=args.year, session_type=args.type))
