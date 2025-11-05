import asyncio
from datetime import datetime
from typing import Any

import httpx

BASE_URL = "https://api.openf1.org/v1"


async def fetch_sessions(
    client: httpx.AsyncClient,
    year: int | None = None,
    session_key: int | None = None,
) -> list[dict[str, Any]]:
    params = {}
    if year:
        params["year"] = year
    if session_key:
        params["session_key"] = session_key

    response = await client.get(f"{BASE_URL}/sessions", params=params)
    response.raise_for_status()
    return response.json()


async def fetch_drivers(
    client: httpx.AsyncClient, session_key: int
) -> list[dict[str, Any]]:
    response = await client.get(
        f"{BASE_URL}/drivers", params={"session_key": session_key}
    )
    response.raise_for_status()
    return response.json()


async def fetch_laps(
    client: httpx.AsyncClient, session_key: int
) -> list[dict[str, Any]]:
    response = await client.get(f"{BASE_URL}/laps", params={"session_key": session_key})
    response.raise_for_status()
    return response.json()


async def fetch_positions(
    client: httpx.AsyncClient, session_key: int
) -> list[dict[str, Any]]:
    response = await client.get(
        f"{BASE_URL}/position", params={"session_key": session_key}
    )
    response.raise_for_status()
    return response.json()


async def extract_session_data(session_key: int) -> dict[str, list[dict[str, Any]]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        sessions_task = fetch_sessions(client, session_key=session_key)
        drivers_task = fetch_drivers(client, session_key)
        laps_task = fetch_laps(client, session_key)
        positions_task = fetch_positions(client, session_key)

        sessions, drivers, laps, positions = await asyncio.gather(
            sessions_task, drivers_task, laps_task, positions_task
        )

        for record in sessions:
            record["ingested_at"] = datetime.utcnow().isoformat()
        for record in drivers:
            record["ingested_at"] = datetime.utcnow().isoformat()
        for record in laps:
            record["ingested_at"] = datetime.utcnow().isoformat()
        for record in positions:
            record["ingested_at"] = datetime.utcnow().isoformat()

        return {
            "sessions": sessions,
            "drivers": drivers,
            "laps": laps,
            "positions": positions,
        }


async def extract_latest_sessions(year: int | None = None) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        if year is None:
            year = datetime.utcnow().year
        sessions = await fetch_sessions(client, year=year)
        return sessions


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract.py <session_key>")
        sys.exit(1)

    session_key = int(sys.argv[1])
    data = asyncio.run(extract_session_data(session_key))

    print(f"Extracted data for session {session_key}:")
    print(f"  Sessions: {len(data['sessions'])} records")
    print(f"  Drivers: {len(data['drivers'])} records")
    print(f"  Laps: {len(data['laps'])} records")
    print(f"  Positions: {len(data['positions'])} records")