"""SQL Query Builder for F1 Analytics.

This module provides a clean interface for building SQL queries for the F1 analytics
application. It separates query construction logic from the UI layer.
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryFilters:
    """Filters for F1 analytics queries."""
    seasons: List[int]
    drivers: Optional[List[str]] = None
    teams: Optional[List[str]] = None
    circuits: Optional[List[str]] = None


class F1QueryBuilder:
    """Builds SQL queries for F1 analytics with proper separation of concerns."""

    # Metric definitions
    METRIC_SQL = {
        "Average Lap Time": "AVG(l.lap_duration) as avg_lap_time",
        "Best Lap Time": "MIN(l.lap_duration) as best_lap_time",
        "Total Laps": "COUNT(*) as total_laps",
        "Average Position": "AVG(r.final_position) as avg_position",
        "Best Position": "MIN(r.final_position) as best_position",
        "Worst Position": "MAX(r.final_position) as worst_position",
        "Total Sessions": "COUNT(DISTINCT l.session_key) as total_sessions",
        "Pit Stop Laps": "SUM(CASE WHEN rl.is_pit_out_lap THEN 1 ELSE 0 END) as pit_stop_laps",
        "Average Sector 1": "AVG(l.segment_1_duration) as avg_sector_1",
        "Average Sector 2": "AVG(l.segment_2_duration) as avg_sector_2",
        "Average Sector 3": "AVG(l.segment_3_duration) as avg_sector_3",
        "Fastest Laps Count": "SUM(CASE WHEN l.is_driver_fastest_lap THEN 1 ELSE 0 END) as fastest_laps_count"
    }

    # Dimension definitions
    DIMENSION_SQL = {
        "Driver": ("d.full_name as driver", ["d.full_name"]),
        "Team": ("d.team_name as team", ["d.team_name"]),
        "Season": ("l.year as season", ["l.year"]),
        "Circuit": ("l.circuit_short_name as circuit", ["l.circuit_short_name"]),
        "Laps": (
            ["l.lap_number as lap",
             "l.lap_position as position_during_lap",
             "CASE WHEN rl.is_pit_out_lap THEN 'Yes' ELSE 'No' END as is_pit_lap"],
            ["l.lap_number", "l.lap_position", "rl.is_pit_out_lap"]
        )
    }

    def __init__(self, database: Optional[str] = None):
        """Initialize query builder.

        Args:
            database: Database name (defaults to env var SNOWFLAKE_DATABASE)
        """
        self.database = database or os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV')

    def build_analytics_query(
        self,
        metrics: List[str],
        dimensions: List[str],
        filters: QueryFilters,
        limit: int = 100
    ) -> str:
        """Build a complete analytics query.

        Args:
            metrics: List of metric names to include
            dimensions: List of dimension names to group by
            filters: Query filters (seasons, drivers, teams, circuits)
            limit: Maximum number of rows to return

        Returns:
            Complete SQL query string

        Raises:
            ValueError: If metrics or dimensions are empty, or if invalid metric/dimension names
        """
        if not metrics:
            raise ValueError("At least one metric is required")
        if not dimensions:
            raise ValueError("At least one dimension is required")
        if not filters.seasons:
            raise ValueError("At least one season is required")

        # Build metric SQL
        metric_sql = []
        for metric in metrics:
            if metric not in self.METRIC_SQL:
                raise ValueError(f"Unknown metric: {metric}")
            metric_sql.append(self.METRIC_SQL[metric])

        # Build dimension SQL and group by
        dim_sql = []
        group_by = []
        needs_raw_laps = "Pit Stop Laps" in metrics or "Laps" in dimensions

        for dimension in dimensions:
            if dimension not in self.DIMENSION_SQL:
                raise ValueError(f"Unknown dimension: {dimension}")

            dim_def, group_def = self.DIMENSION_SQL[dimension]

            if isinstance(dim_def, list):
                dim_sql.extend(dim_def)
            else:
                dim_sql.append(dim_def)

            group_by.extend(group_def)

            if dimension == "Laps":
                needs_raw_laps = True

        # Build WHERE conditions
        where_conditions = self._build_where_conditions(filters)

        # Build JOIN clauses
        join_clauses = self._build_join_clauses(metrics, needs_raw_laps)

        # Construct final query
        query = f"""
        SELECT
            {', '.join(dim_sql)},
            {', '.join(metric_sql)}
        FROM fct_lap_times l
        {chr(10).join(join_clauses)}
        WHERE {' AND '.join(where_conditions)}
        GROUP BY {', '.join(group_by)}
        ORDER BY {metric_sql[0].split(' as ')[1]}
        LIMIT {limit}
        """

        return query

    def _build_where_conditions(self, filters: QueryFilters) -> List[str]:
        """Build WHERE clause conditions from filters."""
        conditions = ["l.lap_duration > 0"]

        # Season filter (required)
        if len(filters.seasons) == 1:
            conditions.append(f"l.year = {filters.seasons[0]}")
        else:
            season_list = ', '.join(map(str, filters.seasons))
            conditions.append(f"l.year IN ({season_list})")

        # Driver filter
        if filters.drivers:
            if len(filters.drivers) == 1:
                conditions.append(f"d.full_name = '{filters.drivers[0]}'")
            else:
                driver_list = "', '".join(filters.drivers)
                conditions.append(f"d.full_name IN ('{driver_list}')")

        # Team filter
        if filters.teams:
            if len(filters.teams) == 1:
                conditions.append(f"d.team_name = '{filters.teams[0]}'")
            else:
                team_list = "', '".join(filters.teams)
                conditions.append(f"d.team_name IN ('{team_list}')")

        # Circuit filter
        if filters.circuits:
            if len(filters.circuits) == 1:
                conditions.append(f"l.circuit_short_name = '{filters.circuits[0]}'")
            else:
                circuit_list = "', '".join(filters.circuits)
                conditions.append(f"l.circuit_short_name IN ('{circuit_list}')'")

        return conditions

    def _build_join_clauses(self, metrics: List[str], needs_raw_laps: bool) -> List[str]:
        """Build JOIN clauses based on required tables."""
        joins = ["JOIN dim_drivers d ON l.driver_number = d.driver_number"]

        # Add raw laps join for pit stop data
        if needs_raw_laps:
            raw_laps_table = f"{self.database}.RAW.LAPS"
            joins.append(
                f"LEFT JOIN {raw_laps_table} rl ON l.session_key = rl.session_key "
                f"AND l.driver_number = rl.driver_number AND l.lap_number = rl.lap_number"
            )

        # Add race results join if needed
        if any(m in metrics for m in ["Average Position", "Best Position", "Worst Position"]):
            joins.append(
                "LEFT JOIN fct_race_results r ON l.driver_number = r.driver_number "
                "AND l.session_key = r.session_key"
            )

        return joins
