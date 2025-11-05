variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "snowflake_account" {
  description = "Snowflake account identifier (e.g., abc12345.us-east-1)"
  type        = string
  sensitive   = true
}

variable "snowflake_user" {
  description = "Snowflake admin user"
  type        = string
  sensitive   = true
}

variable "snowflake_password" {
  description = "Snowflake admin password"
  type        = string
  sensitive   = true
}

variable "etl_service_account_password" {
  description = "Password for ETL service account"
  type        = string
  sensitive   = true
}
