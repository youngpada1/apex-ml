# Snowflake Infrastructure

Multi-environment Terraform infrastructure for Snowflake data platform.

## Environments

- **dev**: Development environment (APEXML_DEV database)
- **staging**: Staging environment (APEXML_STAGING database)
- **prod**: Production environment (APEXML_PROD database)

## Authentication

Uses JWT authentication with RSA key pairs:
- Local development: `~/.ssh/snowflake_key.p8`
- CI/CD: GitHub Secret `SNOWFLAKE_PRIVATE_KEY`

## Deployment

Automatically deployed via GitHub Actions when changes are pushed to:
- `dev` branch ’ dev environment
- `staging` branch ’ staging environment
- `main` branch ’ prod environment

## Resources Created

Each environment includes:
- Database (APEXML_DEV/STAGING/PROD)
- Schemas: RAW, STAGING, ANALYTICS
- Roles: DATA_ENGINEER, ANALYTICS_USER, ML_ENGINEER
- Warehouses: ETL_WAREHOUSE, ANALYTICS_WAREHOUSE
- Service account: ETL_SERVICE_ACCOUNT
