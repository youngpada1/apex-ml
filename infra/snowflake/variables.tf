variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake user for authentication"
  type        = string
  default     = "flavs"
}

variable "etl_service_account_password" {
  description = "Password for ETL service account (used only for initial setup)"
  type        = string
  sensitive   = true
  default     = ""
}