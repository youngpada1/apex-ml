output "environment" {
  value       = var.environment
  description = "Current Terraform workspace environment"
}

output "snowflake_database" {
  value       = module.snowflake.database_name
  description = "Snowflake database name"
}

output "snowflake_schemas" {
  value       = module.snowflake.schemas
  description = "Snowflake schema names (raw, staging, analytics)"
}

output "data_engineer_role" {
  value       = module.snowflake.data_engineer_role
  description = "Snowflake data engineer role"
}

output "warehouse" {
  value       = module.snowflake.warehouse
  description = "Snowflake warehouse for operations"
}
