terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 0.94"
    }
  }
}

provider "snowflake" {
  # Key pair authentication (industry best practice)
  # Uses environment variables for security:
  # - SNOWFLAKE_ACCOUNT: Your Snowflake account identifier
  # - SNOWFLAKE_USER: Your Snowflake username
  # - SNOWFLAKE_PRIVATE_KEY_PATH: Path to your private key file

  role                = "ACCOUNTADMIN"
  authenticator       = "JWT"
  private_key_path    = pathexpand("~/.ssh/snowflake_key.p8")
  warehouse           = "COMPUTE_WH"
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
# Role hierarchy will be set up via SQL after initial creation
# This avoids deprecated resource types in the new provider version

# --- Service Account for ETL Pipeline ---

resource "snowflake_user" "etl_service_account" {
  name         = "ETL_SERVICE_ACCOUNT"
  login_name   = "etl_service_account"
  comment      = "Service account for automated ETL pipelines"
  password     = var.etl_service_account_password
  default_role = snowflake_role.data_engineer.name

  default_warehouse    = snowflake_warehouse.etl_warehouse.name
  must_change_password = false
  disabled             = false
}

# Role assignment will be done via SQL after creation

# --- Database ---

resource "snowflake_database" "apexml" {
  name    = "APEXML_${upper(var.environment)}"
  comment = "ApexML F1 Analytics Database - ${var.environment} environment"

  data_retention_time_in_days = var.environment == "prod" ? 7 : 1
}

# --- Schemas ---

resource "snowflake_schema" "dev" {
  database = snowflake_database.apexml.name
  name     = "DEV"
  comment  = "Raw data ingested from OpenF1 API"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.apexml.name
  name     = "STAGING"
  comment  = "Cleaned and transformed data"
}

resource "snowflake_schema" "prod" {
  database = snowflake_database.apexml.name
  name     = "PROD"
  comment  = "Production-ready analytics data for ML and visualizations"
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