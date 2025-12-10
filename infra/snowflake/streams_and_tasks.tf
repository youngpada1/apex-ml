# ============================================================================
# Snowflake Streams and Tasks for Automated Data Pipeline
# ============================================================================
# Streams monitor RAW tables for changes (new data loads)
# Tasks automatically trigger dbt transformations when stream detects new data

# Stream on SESSIONS table to detect new data
resource "snowflake_stream_on_table" "sessions_stream" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = "SESSIONS_STREAM"
  comment  = "Stream to monitor new race sessions loaded into RAW.SESSIONS table"

  table              = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.SESSIONS"
  show_initial_rows  = false # Only capture changes after stream creation

  depends_on = [
    snowflake_table.sessions
  ]
}

# Grant stream permissions to WRITE role
resource "snowflake_grant_privileges_to_account_role" "sessions_stream_select" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT"]

  on_schema_object {
    object_type = "STREAM"
    object_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.${snowflake_stream_on_table.sessions_stream.name}"
  }
}

# Task to run dbt transformations when stream has data
# Note: This task definition is a placeholder - actual dbt execution requires either:
# 1. dbt Cloud (use SYSTEM$RUN_DBT_CLOUD_JOB)
# 2. External function integration to trigger dbt Core
# 3. Stored procedure that runs dbt commands via Python
resource "snowflake_task" "dbt_transform_task" {
  database  = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema    = snowflake_schema.analytics.name
  name      = "DBT_TRANSFORM_TASK"
  comment   = "Task to run dbt transformations when new data arrives in RAW.SESSIONS"
  warehouse = snowflake_warehouse.etl_warehouse.name

  # Run every 5 minutes, but only when stream has data
  schedule = "5 MINUTE"
  when     = "SYSTEM$STREAM_HAS_DATA('${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.${snowflake_stream_on_table.sessions_stream.name}')"

  # Placeholder SQL - replace with actual dbt execution method
  # Option 1: dbt Cloud
  # sql_statement = "CALL SYSTEM$RUN_DBT_CLOUD_JOB(<account_id>, <job_id>)"

  # Option 2: External function (requires setup)
  # sql_statement = "CALL ${snowflake_schema.analytics.name}.RUN_DBT_CORE()"

  # Option 3: Simple placeholder for manual configuration
  sql_statement = "SELECT 'DBT transformation placeholder - configure with dbt Cloud or external function' AS MESSAGE"

  enabled = false # Start disabled - enable after configuring dbt execution method

  depends_on = [
    snowflake_stream_on_table.sessions_stream,
    snowflake_schema.analytics
  ]
}

# Grant task permissions to ADMIN role
resource "snowflake_grant_privileges_to_account_role" "dbt_task_operate" {
  account_role_name = snowflake_account_role.admin.name
  privileges        = ["OPERATE", "MONITOR"]

  on_schema_object {
    object_type = "TASK"
    object_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}.${snowflake_task.dbt_transform_task.name}"
  }
}

# Grant task permissions to READ role for monitoring
resource "snowflake_grant_privileges_to_account_role" "dbt_task_monitor" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["MONITOR"]

  on_schema_object {
    object_type = "TASK"
    object_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}.${snowflake_task.dbt_transform_task.name}"
  }
}

# Output task and stream information
output "sessions_stream_name" {
  value       = snowflake_stream_on_table.sessions_stream.name
  description = "Name of the stream monitoring SESSIONS table"
}

output "dbt_transform_task_name" {
  value       = snowflake_task.dbt_transform_task.name
  description = "Name of the task that runs dbt transformations"
}
