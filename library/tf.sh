#!/bin/bash
# Terraform wrapper script that loads environment variables from .env
# Usage: ./tf.sh plan dev
#        ./tf.sh apply dev
#        ./tf.sh init dev

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
ENV_FILE="$PROJECT_ROOT/.env"
TF_DIR="$PROJECT_ROOT/infra/snowflake"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Load environment variables from .env
set -a
source "$ENV_FILE"
set +a

# Get the command and environment
COMMAND="$1"
ENVIRONMENT="$2"

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <command> <environment>"
    echo "Commands: init, plan, apply, destroy, validate"
    echo "Environments: dev, staging, prod"
    exit 1
fi

if [ -z "$ENVIRONMENT" ]; then
    echo "Error: Environment required (dev, staging, or prod)"
    exit 1
fi

# Verify environment variables are set
if [ -z "$SNOWFLAKE_ACCOUNT" ] || [ -z "$SNOWFLAKE_USER" ]; then
    echo "Error: SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER must be set in .env"
    exit 1
fi

echo "Running terraform $COMMAND for environment: $ENVIRONMENT"
echo "Using SNOWFLAKE_ACCOUNT: $SNOWFLAKE_ACCOUNT"
echo "Using SNOWFLAKE_USER: $SNOWFLAKE_USER"
echo ""

# Export the variables so terraform can use them
export TF_VAR_snowflake_account="$SNOWFLAKE_ACCOUNT"
export TF_VAR_snowflake_user="$SNOWFLAKE_USER"
export TF_VAR_etl_service_account_password="${ETL_SERVICE_ACCOUNT_PASSWORD:-placeholder}"

# Find terraform binary
TERRAFORM_BIN=$(which terraform 2>/dev/null || echo "/opt/homebrew/bin/terraform")

if [ ! -x "$TERRAFORM_BIN" ]; then
    echo "Error: terraform not found. Please install terraform."
    exit 1
fi

# Change to the terraform directory
cd "$TF_DIR"

# Select the appropriate workspace
echo "Selecting workspace: $ENVIRONMENT"
"$TERRAFORM_BIN" workspace select "$ENVIRONMENT" || "$TERRAFORM_BIN" workspace new "$ENVIRONMENT"
echo ""

# Run the terraform command
case "$COMMAND" in
    init)
        "$TERRAFORM_BIN" init
        ;;
    plan)
        "$TERRAFORM_BIN" plan -var="environment=$ENVIRONMENT"
        ;;
    apply)
        "$TERRAFORM_BIN" apply -var="environment=$ENVIRONMENT" -auto-approve
        ;;
    destroy)
        "$TERRAFORM_BIN" destroy -var="environment=$ENVIRONMENT"
        ;;
    validate)
        "$TERRAFORM_BIN" validate
        ;;
    *)
        "$TERRAFORM_BIN" "$COMMAND" -var="environment=$ENVIRONMENT" "${@:3}"
        ;;
esac
