variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

locals {
  env_config = {
    dev = {
      ec2_instance_type   = "t3.micro"
      enable_monitoring   = false
      log_retention_days  = 7
    }
    staging = {
      ec2_instance_type   = "t3.small"
      enable_monitoring   = true
      log_retention_days  = 14
    }
    prod = {
      ec2_instance_type   = "t3.medium"
      enable_monitoring   = true
      log_retention_days  = 30
    }
  }

  current_env = local.env_config[var.environment]
}