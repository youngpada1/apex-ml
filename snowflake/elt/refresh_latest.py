"""
Automated script to refresh F1 data pipeline.
Fetches the latest completed race session and runs the full ELT pipeline.
"""
import asyncio
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from extract import extract_session_data
from load import load_all
import httpx


async def get_latest_race_session():
    """Fetch the most recent completed race session."""
    async with httpx.AsyncClient() as client:
        # Get all race sessions
        response = await client.get(
            "https://api.openf1.org/v1/sessions",
            params={"session_type": "Race"}
        )
        response.raise_for_status()
        sessions = response.json()

        # Filter for completed sessions (ended in the past)
        now = datetime.now(timezone.utc)
        completed_sessions = [
            s for s in sessions
            if s.get('date_end') and datetime.fromisoformat(s['date_end'].replace('Z', '+00:00')) < now
        ]

        # Sort by date_end descending to get most recent
        completed_sessions.sort(
            key=lambda s: s.get('date_end', ''),
            reverse=True
        )

        if not completed_sessions:
            print("No completed race sessions found")
            return None

        return completed_sessions[0]


async def refresh_pipeline():
    """
    Run the full data refresh pipeline:
    1. Extract latest race data from OpenF1 API
    2. Load into Snowflake RAW schema (raw tables)
    3. Run dbt transformations to update STAGING and ANALYTICS schemas
    """
    print("="*80)
    print("F1 DATA REFRESH PIPELINE")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print("="*80)

    # Step 1: Get latest race session
    print("\n[1/3] Fetching latest race session from OpenF1 API...")
    latest_session = await get_latest_race_session()

    if not latest_session:
        print("No new sessions to load. Exiting.")
        return

    session_key = latest_session.get('session_key')
    session_name = latest_session.get('session_name')
    date_end = latest_session.get('date_end')

    print(f"Latest race: {session_name} (Session Key: {session_key})")
    print(f"Completed at: {date_end}")

    # Step 2: Extract and load to RAW
    print("\n[2/3] Extracting race data and loading to RAW tables...")
    try:
        data = await extract_session_data(session_key)
        load_all(data)
        print(f"Successfully loaded session {session_key} to RAW tables")
    except Exception as e:
        print(f"ERROR loading data to RAW: {e}")
        sys.exit(1)

    # Step 3: Run dbt transformations
    print("\n[3/3] Running dbt transformations (STAGING → PROD)...")
    try:
        # Get project root
        project_root = Path(__file__).parent.parent.parent
        dbt_project_dir = project_root / "snowflake" / "dbt_project"

        # Run dbt
        result = subprocess.run(
            ["uv", "run", "dbt", "run", "--target", "dev"],
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"ERROR running dbt:\n{result.stderr}")
            sys.exit(1)

        print("dbt transformations completed successfully")
        print(result.stdout)

    except Exception as e:
        print(f"ERROR running dbt: {e}")
        sys.exit(1)

    print("\n" + "="*80)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Finished at: {datetime.now(timezone.utc).isoformat()}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(refresh_pipeline())
