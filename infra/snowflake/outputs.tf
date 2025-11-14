output "database_name" {
  value       = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  description = "Snowflake database name"
}

output "schemas" {
  value = {
    raw       = snowflake_schema.raw.name
    staging   = snowflake_schema.staging.name
    analytics = snowflake_schema.analytics.name
  }
  description = "Snowflake schema names"
}

output "data_engineer_role" {
  value       = snowflake_account_role.data_engineer.name
  description = "Data engineer role name"
}

output "warehouse" {
  value       = "COMPUTE_WH"
  description = "Snowflake warehouse used for operations"
}
