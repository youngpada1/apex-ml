terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 0.94"
    }
  }

  backend "s3" {
    bucket         = "apex-ml-terraform-state"
    key            = "snowflake/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "apex-ml-terraform-locks"
    encrypt        = true
  }
}

provider "snowflake" {
  # Key pair authentication reads from environment variables:
  # - SNOWFLAKE_ACCOUNT (format: ORGNAME-ACCOUNTNAME)
  # - SNOWFLAKE_USER
  # - SNOWFLAKE_PRIVATE_KEY

  role                = "ACCOUNTADMIN"
  authenticator       = "SNOWFLAKE_JWT"
  warehouse           = "COMPUTE_WH"
}

# --- RBAC: Environment-Specific Custom Roles ---
# Simple CRUD-based naming: ADMIN (full), WRITE (ETL), READ (app users)

resource "snowflake_account_role" "admin" {
  name    = "APEX_ML_${upper(var.environment)}_ADMIN"
  comment = "Full admin access to ${var.environment} environment"
}

resource "snowflake_account_role" "write" {
  name    = "APEX_ML_${upper(var.environment)}_WRITE"
  comment = "Write access for ETL pipelines in ${var.environment}"
}

resource "snowflake_account_role" "read" {
  name    = "APEX_ML_${upper(var.environment)}_READ"
  comment = "Read-only access for app users and analysts in ${var.environment}"
}

# --- Role Grants (Hierarchy) ---
# ACCOUNTADMIN → SYSADMIN → APEX_ML_{ENV}_ADMIN → APEX_ML_{ENV}_WRITE → APEX_ML_{ENV}_READ

# --- Service Account for ETL Pipeline ---
# Each environment has its own service account

resource "snowflake_user" "etl_service_account" {
  name         = "APEX_ML_ETL_${upper(var.environment)}"
  login_name   = "apex_ml_etl_${lower(var.environment)}"
  comment      = "Service account for ETL pipelines in ${var.environment}"
  password     = var.etl_service_account_password
  default_role = snowflake_account_role.write.name

  default_warehouse    = snowflake_warehouse.etl_warehouse.name
  must_change_password = false
  disabled             = false
}

# Role assignment will be done via SQL after initial creation

# --- Databases ---
# Three separate databases: APEXML_DEV, APEXML_STAGING, APEXML_PROD
# Conditional creation based on var.environment to ensure workspace isolation

resource "snowflake_database" "apexml_dev" {
  count   = var.environment == "dev" ? 1 : 0
  name    = "APEXML_DEV"
  comment = "ApexML F1 Analytics Database - DEV environment"

  data_retention_time_in_days = 1
}

resource "snowflake_database" "apexml_staging" {
  count   = var.environment == "staging" ? 1 : 0
  name    = "APEXML_STAGING"
  comment = "ApexML F1 Analytics Database - STAGING environment"

  data_retention_time_in_days = 1
}

resource "snowflake_database" "apexml_prod" {
  count   = var.environment == "prod" ? 1 : 0
  name    = "APEXML_PROD"
  comment = "ApexML F1 Analytics Database - PROD environment"

  data_retention_time_in_days = 7
}

# --- Schemas ---
# Each environment gets its own RAW, STAGING, and ANALYTICS schemas

resource "snowflake_schema" "raw" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  name     = "RAW"
  comment  = "Raw data ingested from OpenF1 API"
}

resource "snowflake_schema" "staging" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  name     = "STAGING"
  comment  = "Cleaned and transformed data"
}

resource "snowflake_schema" "analytics" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  name     = "ANALYTICS"
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