variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "etl_service_account_password" {
  description = "Password for ETL service account (used only for initial setup)"
  type        = string
  sensitive   = true
  default     = ""
}