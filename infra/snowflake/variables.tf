variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "snowflake_account" {
  description = "Snowflake account identifier in format ORGNAME-ACCOUNTNAME"
  type        = string
  default     = ""
}

variable "snowflake_user" {
  description = "Snowflake username for authentication"
  type        = string
  default     = ""
}

variable "etl_service_account_password" {
  description = "Password for ETL service account (used only for initial setup)"
  type        = string
  sensitive   = true
  default     = ""
}