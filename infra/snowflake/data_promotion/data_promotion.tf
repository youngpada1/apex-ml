# Data promotion configuration for moving data between environments
# DEV (raw data) → STAGING (transformations) → PROD (analytics)

# --- Promote data from DEV to STAGING ---
# Creates dynamic tables that automatically sync data from DEV.DEV to STAGING.DEV

resource "snowflake_dynamic_table" "staging_sessions" {
  count = var.environment == "staging" ? 1 : 0

  name     = "SESSIONS"
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.RAW.SESSIONS
  SQL

  comment = "Dynamic table syncing sessions data from DEV"
}

resource "snowflake_dynamic_table" "staging_drivers" {
  count = var.environment == "staging" ? 1 : 0

  name     = "DRIVERS"
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.RAW.DRIVERS
  SQL

  comment = "Dynamic table syncing drivers data from DEV"
}

resource "snowflake_dynamic_table" "staging_laps" {
  count = var.environment == "staging" ? 1 : 0

  name     = "LAPS"
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.RAW.LAPS
  SQL

  comment = "Dynamic table syncing laps data from DEV"
}

resource "snowflake_dynamic_table" "staging_positions" {
  count = var.environment == "staging" ? 1 : 0

  name     = "POSITIONS"
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name

  target_lag {
    maximum_duration = "1 hour"
  }

  warehouse = snowflake_warehouse.etl_warehouse.name

  query = <<-SQL
    SELECT * FROM APEXML_DEV.RAW.POSITIONS
  SQL

  comment = "Dynamic table syncing positions data from DEV"
}

# --- Alternative: Use Snowflake Streams and Tasks ---
# If you prefer explicit control over data promotion timing,
# you can use streams to capture changes and tasks to process them.
# Uncomment and customize the following if needed:

# resource "snowflake_stream" "dev_sessions_stream" {
#   count = var.environment == "staging" ? 1 : 0
#
#   name     = "DEV_SESSIONS_STREAM"
#   database = "APEXML_DEV"
#   schema   = "RAW"
#   on_table = "APEXML_DEV.RAW.SESSIONS"
#   comment  = "Stream to track changes in DEV sessions"
# }

# resource "snowflake_task" "promote_sessions_task" {
#   count = var.environment == "staging" ? 1 : 0
#
#   name      = "PROMOTE_SESSIONS"
#   database  = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
#   schema    = snowflake_schema.raw.name
#   warehouse = snowflake_warehouse.etl_warehouse.name
#
#   schedule = "USING CRON 0 * * * * UTC"  # Every hour
#
#   sql_statement = <<-SQL
#     MERGE INTO ${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.RAW.SESSIONS dst
#     USING (SELECT * FROM DEV_SESSIONS_STREAM) src
#     ON dst.session_key = src.session_key
#     WHEN MATCHED THEN UPDATE SET *
#     WHEN NOT MATCHED THEN INSERT *;
#   SQL
#
#   enabled = true
#   comment = "Task to promote sessions data from DEV to STAGING"
# }
