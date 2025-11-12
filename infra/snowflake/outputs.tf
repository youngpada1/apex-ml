output "database_name" {
  value       = snowflake_database.apexml.name
  description = "Snowflake database name"
}

output "schemas" {
  value = {
    raw       = snowflake_schema.dev.name
    staging   = snowflake_schema.staging.name
    analytics = snowflake_schema.prod.name
  }
  description = "Snowflake schema names"
}

output "data_engineer_role" {
  value       = snowflake_role.data_engineer.name
  description = "Data engineer role name"
}

output "warehouse" {
  value       = "COMPUTE_WH"
  description = "Snowflake warehouse used for operations"
}
