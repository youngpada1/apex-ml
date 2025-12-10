# ============================================================================
# Snowflake Streams for Automated Data Pipeline
# ============================================================================
# Streams monitor RAW tables for changes (new data loads)

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

# Output stream information
output "sessions_stream_name" {
  value       = snowflake_stream_on_table.sessions_stream.name
  description = "Name of the stream monitoring SESSIONS table"
}
