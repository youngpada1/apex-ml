# Data promotion configuration for moving data between environments
# DEV (raw data) → STAGING (transformations) → PROD (analytics)

# Only create data promotion resources for staging and prod environments
locals {
  should_promote_from_dev = var.environment == "staging"
  should_promote_from_staging = var.environment == "prod"
}

# --- Promote data from DEV to STAGING ---
# Creates dynamic tables that automatically sync data from DEV.DEV to STAGING.DEV

resource "snowflake_dynamic_table" "staging_sessions" {
  count = local.should_promote_from_dev ? 1 : 0

  name     = "SESSIONS"
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.DEV.SESSIONS
  SQL

  comment = "Dynamic table syncing sessions data from DEV"
}

resource "snowflake_dynamic_table" "staging_drivers" {
  count = local.should_promote_from_dev ? 1 : 0

  name     = "DRIVERS"
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.DEV.DRIVERS
  SQL

  comment = "Dynamic table syncing drivers data from DEV"
}

resource "snowflake_dynamic_table" "staging_laps" {
  count = local.should_promote_from_dev ? 1 : 0

  name     = "LAPS"
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.DEV.LAPS
  SQL

  comment = "Dynamic table syncing laps data from DEV"
}

resource "snowflake_dynamic_table" "staging_positions" {
  count = local.should_promote_from_dev ? 1 : 0

  name     = "POSITIONS"
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.DEV.POSITIONS
  SQL

  comment = "Dynamic table syncing positions data from DEV"
}

# --- Alternative: Use Snowflake Streams and Tasks ---
# If you prefer explicit control over data promotion timing,
# you can use streams to capture changes and tasks to process them.
# Uncomment and customize the following if needed:

# resource "snowflake_stream" "dev_sessions_stream" {
#   count = local.should_promote_from_dev ? 1 : 0
#
#   name     = "DEV_SESSIONS_STREAM"
#   database = "APEXML_DEV"
#   schema   = "RAW"
#   on_table = "APEXML_DEV.RAW.SESSIONS"
#   comment  = "Stream to track changes in DEV sessions"
# }

# resource "snowflake_task" "promote_sessions_task" {
#   count = local.should_promote_from_dev ? 1 : 0
#
#   name      = "PROMOTE_SESSIONS"
#   database  = snowflake_database.apexml.name
#   schema    = snowflake_schema.raw.name
#   warehouse = snowflake_warehouse.etl_warehouse.name
#
#   schedule = "USING CRON 0 * * * * UTC"  # Every hour
#
#   sql_statement = <<-SQL
#     MERGE INTO ${snowflake_database.apexml.name}.RAW.SESSIONS dst
#     USING (SELECT * FROM DEV_SESSIONS_STREAM) src
#     ON dst.session_key = src.session_key
#     WHEN MATCHED THEN UPDATE SET *
#     WHEN NOT MATCHED THEN INSERT *;
#   SQL
#
#   enabled = true
#   comment = "Task to promote sessions data from DEV to STAGING"
# }
