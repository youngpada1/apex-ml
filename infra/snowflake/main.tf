terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.94"
    }
  }
}

provider "snowflake" {
  account  = var.snowflake_account
  user     = var.snowflake_user
  password = var.snowflake_password
  role     = "ACCOUNTADMIN"
}

# --- RBAC: Custom Roles ---

resource "snowflake_role" "data_engineer" {
  name    = "DATA_ENGINEER"
  comment = "Role for data engineers with full access to ETL operations"
}

resource "snowflake_role" "analytics_user" {
  name    = "ANALYTICS_USER"
  comment = "Role for analytics users with read-only access"
}

resource "snowflake_role" "ml_engineer" {
  name    = "ML_ENGINEER"
  comment = "Role for ML engineers with access to analytics schema"
}

# --- Role Grants (Hierarchy) ---
# ACCOUNTADMIN → SYSADMIN → DATA_ENGINEER → ANALYTICS_USER
# SECURITYADMIN manages security-related operations

resource "snowflake_role_grants" "data_engineer_to_sysadmin" {
  role_name = snowflake_role.data_engineer.name
  roles     = ["SYSADMIN"]
}

resource "snowflake_role_grants" "analytics_user_to_data_engineer" {
  role_name = snowflake_role.analytics_user.name
  roles     = [snowflake_role.data_engineer.name]
}

resource "snowflake_role_grants" "ml_engineer_to_data_engineer" {
  role_name = snowflake_role.ml_engineer.name
  roles     = [snowflake_role.data_engineer.name]
}

# --- Service Account for ETL Pipeline ---

resource "snowflake_user" "etl_service_account" {
  name         = "ETL_SERVICE_ACCOUNT"
  login_name   = "etl_service_account"
  comment      = "Service account for automated ETL pipelines"
  password     = var.etl_service_account_password
  default_role = snowflake_role.data_engineer.name

  default_warehouse          = snowflake_warehouse.etl_warehouse.name
  default_secondary_roles    = ["ALL"]
  must_change_password       = false
  disabled                   = false
}

resource "snowflake_role_grants" "etl_service_account_data_engineer" {
  role_name = snowflake_role.data_engineer.name
  users     = [snowflake_user.etl_service_account.name]
}

# --- Database ---

resource "snowflake_database" "apexml" {
  name    = "APEXML_${upper(var.environment)}"
  comment = "ApexML F1 Analytics Database - ${var.environment} environment"

  data_retention_time_in_days = var.environment == "prod" ? 7 : 1
}

# --- Schemas ---

resource "snowflake_schema" "raw" {
  database = snowflake_database.apexml.name
  name     = "RAW"
  comment  = "Raw data ingested from OpenF1 API"

  is_managed = false
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.apexml.name
  name     = "STAGING"
  comment  = "Cleaned and transformed data"

  is_managed = false
}

resource "snowflake_schema" "analytics" {
  database = snowflake_database.apexml.name
  name     = "ANALYTICS"
  comment  = "Analytics-ready data for ML and visualizations"

  is_managed = false
}

# --- Warehouse ---

resource "snowflake_warehouse" "etl_warehouse" {
  name           = "ETL_WH_${upper(var.environment)}"
  comment        = "Warehouse for ETL operations - ${var.environment}"
  warehouse_size = var.environment == "prod" ? "SMALL" : "XSMALL"

  auto_suspend          = 60  # Suspend after 60 seconds of inactivity
  auto_resume           = true
  initially_suspended   = true
  max_cluster_count     = 1
  min_cluster_count     = 1
  scaling_policy        = "STANDARD"
}

resource "snowflake_warehouse" "analytics_warehouse" {
  name           = "ANALYTICS_WH_${upper(var.environment)}"
  comment        = "Warehouse for analytics queries - ${var.environment}"
  warehouse_size = "XSMALL"

  auto_suspend          = 300  # Suspend after 5 minutes
  auto_resume           = true
  initially_suspended   = true
  max_cluster_count     = 1
  min_cluster_count     = 1
  scaling_policy        = "STANDARD"
}

# --- Schema Grants for DATA_ENGINEER Role ---

resource "snowflake_schema_grant" "data_engineer_raw" {
  database_name = snowflake_database.apexml.name
  schema_name   = snowflake_schema.raw.name

  privilege = "ALL PRIVILEGES"
  roles     = [snowflake_role.data_engineer.name]

  with_grant_option = false
}

resource "snowflake_schema_grant" "data_engineer_staging" {
  database_name = snowflake_database.apexml.name
  schema_name   = snowflake_schema.staging.name

  privilege = "ALL PRIVILEGES"
  roles     = [snowflake_role.data_engineer.name]

  with_grant_option = false
}

resource "snowflake_schema_grant" "data_engineer_analytics" {
  database_name = snowflake_database.apexml.name
  schema_name   = snowflake_schema.analytics.name

  privilege = "ALL PRIVILEGES"
  roles     = [snowflake_role.data_engineer.name]

  with_grant_option = false
}

# --- Schema Grants for ANALYTICS_USER Role ---

resource "snowflake_schema_grant" "analytics_user_analytics_usage" {
  database_name = snowflake_database.apexml.name
  schema_name   = snowflake_schema.analytics.name

  privilege = "USAGE"
  roles     = [snowflake_role.analytics_user.name]
}

# --- Database Grants ---

resource "snowflake_database_grant" "data_engineer_usage" {
  database_name = snowflake_database.apexml.name

  privilege = "USAGE"
  roles     = [snowflake_role.data_engineer.name]
}

resource "snowflake_database_grant" "analytics_user_usage" {
  database_name = snowflake_database.apexml.name

  privilege = "USAGE"
  roles     = [snowflake_role.analytics_user.name]
}

# --- Warehouse Grants ---

resource "snowflake_warehouse_grant" "data_engineer_etl_warehouse" {
  warehouse_name = snowflake_warehouse.etl_warehouse.name
  privilege      = "USAGE"
  roles          = [snowflake_role.data_engineer.name]

  with_grant_option = false
}

resource "snowflake_warehouse_grant" "analytics_user_analytics_warehouse" {
  warehouse_name = snowflake_warehouse.analytics_warehouse.name
  privilege      = "USAGE"
  roles          = [snowflake_role.analytics_user.name]

  with_grant_option = false
}
