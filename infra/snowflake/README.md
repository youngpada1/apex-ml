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
- `dev` branch � dev environment
- `staging` branch � staging environment
- `main` branch � prod environment

## Resources Created

Each environment includes:
- Database (APEXML_DEV/STAGING/PROD)
- Schemas: RAW, STAGING, ANALYTICS
- Roles: APEX_ML_{ENV}_ADMIN, APEX_ML_{ENV}_WRITE, APEX_ML_{ENV}_READ
- Warehouses: ETL_WH_{ENV}, ANALYTICS_WH_{ENV}
- Service account: APEX_ML_ETL_{ENV}

## Role Structure

```
ACCOUNTADMIN
  └── SYSADMIN
      └── APEX_ML_{ENV}_ADMIN    (Full access)
          └── APEX_ML_{ENV}_WRITE (ETL pipelines, dbt)
              └── APEX_ML_{ENV}_READ (App users, read-only)
```

**Role Permissions:**
- `APEX_ML_{ENV}_ADMIN`: Full database access, create/modify schemas
- `APEX_ML_{ENV}_WRITE`: Write to RAW/STAGING/ANALYTICS, run ETL/dbt
- `APEX_ML_{ENV}_READ`: Read-only access to ANALYTICS schema (for public app)
