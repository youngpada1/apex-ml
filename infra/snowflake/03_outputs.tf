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

output "roles" {
  value = {
    admin = snowflake_account_role.admin.name
    write = snowflake_account_role.write.name
    read  = snowflake_account_role.read.name
  }
  description = "Snowflake role names for the environment"
}

output "warehouses" {
  value = {
    etl       = snowflake_warehouse.etl_warehouse.name
    analytics = snowflake_warehouse.analytics_warehouse.name
  }
  description = "Snowflake warehouse names"
}

output "service_account" {
  value       = snowflake_user.etl_service_account.name
  description = "ETL service account name"
}
