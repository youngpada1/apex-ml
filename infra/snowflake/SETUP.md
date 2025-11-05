# Snowflake Infrastructure Setup Guide

This guide walks you through setting up Snowflake infrastructure using Terraform with **key pair authentication** (industry best practice).

## Prerequisites

- Terraform >= 1.6.0
- Snowflake account with ACCOUNTADMIN privileges
- OpenSSL (for key generation)

## Step-by-Step Setup

### 1. Generate RSA Key Pair

From the project root, run:

```bash
./scripts/setup_snowflake_keypair.sh
```

This script will:
- Generate RSA private key at `~/.ssh/snowflake_key.p8`
- Generate public key at `~/.ssh/snowflake_key.pub`
- Set proper file permissions (600 for private, 644 for public)
- Display the formatted public key for Snowflake

**Output example:**
```
🔐 Snowflake Key Pair Authentication Setup
==========================================

Generating RSA private key...
Generating public key...

✅ Keys generated successfully!

Private key: ~/.ssh/snowflake_key.p8
Public key: ~/.ssh/snowflake_key.pub

📋 Next Steps:
==============

1. Copy the public key below and add it to your Snowflake user:

MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
```

### 2. Configure Snowflake User with Public Key

**Option A: Using Snowflake Web UI**
1. Log into Snowflake web interface
2. Click on your username (top right) → "My Profile"
3. Find your account identifier (format: `ORGNAME-ACCOUNTNAME` or `ACCOUNT.REGION`)
4. Go to Worksheets and run:

```sql
USE ROLE ACCOUNTADMIN;
ALTER USER YOUR_USERNAME SET RSA_PUBLIC_KEY='<paste_key_from_script>';
```

**Option B: Using SnowSQL CLI**
```bash
snowsql -a <account> -u <username>
ALTER USER YOUR_USERNAME SET RSA_PUBLIC_KEY='<paste_key_from_script>';
```

### 3. Set Environment Variables

Add these to your shell configuration file (`~/.zshrc` or `~/.bashrc`):

```bash
# Snowflake Authentication
export SNOWFLAKE_ACCOUNT='your-account-identifier'    # e.g., abc12345.us-east-1
export SNOWFLAKE_USER='your-username'                 # Your Snowflake username
export SNOWFLAKE_PRIVATE_KEY_PATH="$HOME/.ssh/snowflake_key.p8"
```

**Finding your account identifier:**
- From Snowflake URL: `https://<ACCOUNT>.snowflakecomputing.com`
- Or run: `SELECT CURRENT_ACCOUNT();` in Snowflake

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Verify environment variables:**
```bash
echo $SNOWFLAKE_ACCOUNT
echo $SNOWFLAKE_USER
echo $SNOWFLAKE_PRIVATE_KEY_PATH
```

### 4. Initialize Terraform

```bash
cd infra/snowflake
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding snowflake-labs/snowflake versions matching "~> 0.94"...
Terraform has been successfully initialized!
```

### 5. Plan Infrastructure Changes

```bash
terraform plan \
  -var="environment=dev" \
  -var="etl_service_account_password=YOUR_STRONG_PASSWORD"
```

Review the plan output to see what will be created:
- 3 custom roles
- 1 database (APEXML_DEV)
- 3 schemas (RAW, STAGING, ANALYTICS)
- 2 warehouses (ETL_WH_DEV, ANALYTICS_WH_DEV)
- 4 tables (SESSIONS, DRIVERS, POSITIONS, LAPS)
- 1 service account user
- Multiple grants for RBAC

### 6. Apply Configuration

```bash
terraform apply \
  -var="environment=dev" \
  -var="etl_service_account_password=YOUR_STRONG_PASSWORD"
```

Type `yes` when prompted to confirm.

### 7. Set Up Role Hierarchy and Grants

After Terraform creates the resources, run the SQL script to set up RBAC:

```bash
# Option 1: Run via Snowflake Web UI
# - Copy contents of infra/snowflake/setup_roles.sql
# - Open Snowflake Worksheets
# - Paste and execute the script

# Option 2: Run via SnowSQL CLI
snowsql -a <account> -u <username> -f infra/snowflake/setup_roles.sql
```

This script sets up:
- Role hierarchy (SYSADMIN → DATA_ENGINEER → ANALYTICS_USER, ML_ENGINEER)
- Database, schema, and warehouse grants
- Future grants (auto-permissions for new tables/views)
- Service account role assignment

### 8. Verify in Snowflake

Log into Snowflake and verify:

```sql
-- Check roles
SHOW ROLES;

-- Check database
SHOW DATABASES LIKE 'APEXML_DEV';

-- Check schemas
USE DATABASE APEXML_DEV;
SHOW SCHEMAS;

-- Check tables
USE SCHEMA RAW;
SHOW TABLES;

-- Check warehouses
SHOW WAREHOUSES;

-- Check service account
SHOW USERS LIKE 'ETL_SERVICE_ACCOUNT';

-- Verify role grants (from setup_roles.sql)
SHOW GRANTS TO ROLE DATA_ENGINEER;
SHOW GRANTS TO USER ETL_SERVICE_ACCOUNT;
```

## What Gets Created

### Roles & Hierarchy
```
ACCOUNTADMIN (Snowflake built-in)
    ↓
SYSADMIN (Snowflake built-in)
    ↓
DATA_ENGINEER (custom)
    ↓
├── ANALYTICS_USER (custom)
└── ML_ENGINEER (custom)
```

### Database Structure
```
APEXML_DEV
├── RAW (schema)
│   ├── SESSIONS (table)
│   ├── DRIVERS (table)
│   ├── POSITIONS (table)
│   └── LAPS (table)
├── STAGING (schema)
└── ANALYTICS (schema)
```

### Warehouses
- **ETL_WH_DEV**: XSMALL, auto-suspend 60s (for ETL operations)
- **ANALYTICS_WH_DEV**: XSMALL, auto-suspend 300s (for queries)

### Service Account
- **Username**: `etl_service_account`
- **Role**: DATA_ENGINEER
- **Purpose**: Automated ETL pipelines

## Multi-Environment Management

For staging and production environments:

```bash
# Staging
terraform apply \
  -var="environment=staging" \
  -var="etl_service_account_password=DIFFERENT_PASSWORD"

# Production
terraform apply \
  -var="environment=prod" \
  -var="etl_service_account_password=DIFFERENT_PASSWORD"
```

Each environment creates isolated resources:
- `APEXML_STAGING` / `APEXML_PROD` databases
- `ETL_WH_STAGING` / `ETL_WH_PROD` warehouses
- Different warehouse sizes (dev: XSMALL, staging: SMALL, prod: SMALL)

## Security Best Practices

✅ **Do:**
- Store private keys in `~/.ssh/` with 600 permissions
- Use environment variables for credentials
- Rotate service account passwords regularly
- Use different passwords per environment
- Keep private keys out of git (already in `.gitignore`)

❌ **Don't:**
- Commit private keys or passwords to git
- Share private keys via email or messaging
- Use the same password across environments
- Store credentials in `.tfvars` files

## Troubleshooting

### Authentication Failed
```
Error: 390144: JWT token is invalid
```
**Solution:** Verify public key is correctly set in Snowflake user:
```sql
DESC USER YOUR_USERNAME;
-- Check RSA_PUBLIC_KEY_FP field
```

### Private Key Not Found
```
Error: private key file not found
```
**Solution:** Verify environment variable points to correct path:
```bash
ls -la $SNOWFLAKE_PRIVATE_KEY_PATH
```

### Permission Denied
```
Error: Insufficient privileges
```
**Solution:** Ensure you're using ACCOUNTADMIN role:
```sql
USE ROLE ACCOUNTADMIN;
```

### Terraform State Lock
```
Error: state lock
```
**Solution:** Check for stale processes:
```bash
ps aux | grep terraform
# Kill if needed
```

## Clean Up (Optional)

To destroy all resources:
```bash
terraform destroy \
  -var="environment=dev" \
  -var="etl_service_account_password=PASSWORD"
```

⚠️ **Warning:** This will delete all databases, tables, and data!

## Next Steps

After infrastructure is set up:
1. Build ETL scripts in `snowflake/etl/`
2. Create transformation queries in `snowflake/sql/`
3. Configure Snowflake connection in ETL scripts
4. Set up GitHub Actions for automated ETL runs
