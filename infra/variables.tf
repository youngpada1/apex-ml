variable "github_token" {
  description = "GitHub Personal Access Token (with repo and workflow scopes)"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or org name"
  type        = string
  default     = "youngpada1"
}

variable "repository" {
  description = "Target GitHub repository name"
  type        = string
  default     = "apex-ml"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# Environment-specific configurations
locals {
  env_config = {
    dev = {
      branch              = "main"
      ec2_instance_type   = "t3.micro"
      enable_monitoring   = false
      log_retention_days  = 7
    }
    staging = {
      branch              = "main"
      ec2_instance_type   = "t3.small"
      enable_monitoring   = true
      log_retention_days  = 14
    }
    prod = {
      branch              = "main"
      ec2_instance_type   = "t3.medium"
      enable_monitoring   = true
      log_retention_days  = 30
    }
  }
  
  current_env = local.env_config[var.environment]
}

variable "alert_email" {
  description = "Email address for billing alerts"
  type        = string
  sensitive   = true
  default     = "flavsferr@gmail.com"  
}