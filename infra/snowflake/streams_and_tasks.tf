# ============================================================================
# Snowflake Streams and Tasks for Automated Data Pipeline
# ============================================================================
# Streams monitor RAW tables for changes (new data loads)
# Tasks automatically trigger dbt transformations when stream detects new data

# Stream on SESSIONS table to detect new data
resource "snowflake_stream_on_table" "sessions_stream" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = var.environment == "dev" ? "STREAM_DBT_TRANSFORMATIONS_DEV" : (var.environment == "staging" ? "STREAM_DBT_TRANSFORMATIONS_STAGING" : "STREAM_DBT_TRANSFORMATIONS_PROD")
  comment  = "Stream to monitor new race sessions loaded into RAW.SESSIONS table (${upper(var.environment)})"

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
resource "snowflake_task" "dbt_transform_task" {
  database  = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema    = snowflake_schema.analytics.name
  name      = var.environment == "dev" ? "TASK_DBT_TRANSFORMATIONS_DEV" : (var.environment == "staging" ? "TASK_DBT_TRANSFORMATIONS_STAGING" : "TASK_DBT_TRANSFORMATIONS_PROD")
  comment   = "Task to run dbt transformations when new data arrives in RAW.SESSIONS (${upper(var.environment)})"
  warehouse = snowflake_warehouse.etl_warehouse.name
  started   = false # Start disabled - enable after stored procedure is deployed

  # Run weekly on Saturday at 9 AM UTC, but only when stream has data
  schedule {
    using_cron = "0 9 * * SAT UTC"
  }

  when = "SYSTEM$STREAM_HAS_DATA('${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.${snowflake_stream_on_table.sessions_stream.name}')"

  # Call Python stored procedure to run dbt transformations
  sql_statement = var.environment == "dev" ? "CALL ${snowflake_schema.analytics.name}.STORED_PROCEDURE_DBT_TRANSFORMATIONS_DEV()" : (var.environment == "staging" ? "CALL ${snowflake_schema.analytics.name}.STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING()" : "CALL ${snowflake_schema.analytics.name}.STORED_PROCEDURE_DBT_TRANSFORMATIONS_PROD()")

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
