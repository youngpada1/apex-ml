variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "etl_service_account_password" {
  description = "Password for ETL service account (used only for initial setup)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "snowflake_account" {
  description = "Snowflake account locator or full name"
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake username used for JTV authentication"
  type.       = string
}