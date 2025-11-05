#!/bin/bash
# Helper script to run dbt commands with uv

PROJECT_DIR="snowflake/dbt_project"
PROFILES_DIR="$HOME/.dbt"

case "$1" in
  debug)
    uv run dbt debug --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    ;;
  run)
    uv run dbt run --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    ;;
  test)
    uv run dbt test --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    ;;
  docs)
    uv run dbt docs generate --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    uv run dbt docs serve --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    ;;
  compile)
    uv run dbt compile --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR"
    ;;
  *)
    echo "Usage: ./snowflake/run_dbt.sh {debug|run|test|docs|compile}"
    exit 1
    ;;
esac
