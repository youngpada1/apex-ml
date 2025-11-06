terraform {
  required_version = ">= 1.6.0"

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 0.94"
    }
  }

  backend "local" {
    # This will use workspace-specific state files
    # Path will be: terraform.tfstate.d/<workspace>/terraform.tfstate
  }
}

# Snowflake Provider Configuration
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

# Snowflake Infrastructure Module
module "snowflake" {
  source = "./snowflake"

  environment = var.environment
}