# Library Scripts

Helper scripts for managing the apex-ml infrastructure.

## tf.sh - Terraform Wrapper

A wrapper script that loads environment variables from `.env` and runs Terraform commands.

### Usage

```bash
./library/tf.sh <command> <environment>
```

### Commands

- `init` - Initialize Terraform
- `plan` - Show what changes Terraform will make
- `apply` - Apply Terraform changes
- `destroy` - Destroy Terraform-managed infrastructure
- `validate` - Validate Terraform configuration

### Environments

- `dev` - Development environment (APEXML_DEV database)
- `staging` - Staging environment (APEXML_STAGING database)
- `prod` - Production environment (APEXML_PROD database)

### Examples

```bash
# Plan changes for dev environment
./library/tf.sh plan dev

# Apply changes to staging
./library/tf.sh apply staging

# Validate configuration
./library/tf.sh validate dev
```

### Requirements

- `.env` file in project root with `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_USER`
- Private key at `~/.ssh/snowflake_key.p8`
- Terraform installed (checked automatically)
