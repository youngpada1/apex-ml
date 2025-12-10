# ============================================================================
# Snowflake Python Stored Procedures for dbt Transformations
# ============================================================================
# These procedures execute dbt transformations when called by Snowflake tasks
# They run dbt Core with subprocess commands in a Python environment
# ============================================================================

# Python stored procedure to run dbt transformations
resource "snowflake_procedure_python" "dbt_transformations" {
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = var.environment == "dev" ? "STORED_PROCEDURE_DBT_TRANSFORMATIONS_DEV" : (var.environment == "staging" ? "STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING" : "STORED_PROCEDURE_DBT_TRANSFORMATIONS_PROD")
  comment  = "Python stored procedure to execute dbt transformations (${upper(var.environment)})"

  return_type = "VARCHAR"

  runtime_version = "3.11"

  packages = ["dbt-core", "dbt-snowflake"]

  snowpark_package = "1.11.1"

  handler = "run_dbt"

  procedure_definition = <<-EOT
import subprocess
import json
from datetime import datetime

def run_dbt():
    """
    Execute dbt transformations and return status.

    Returns:
        str: JSON string with execution status, timestamp, and any errors
    """
    result = {
        'status': 'unknown',
        'timestamp': datetime.utcnow().isoformat(),
        'models_run': 0,
        'errors': []
    }

    try:
        # Run dbt transformations for ${var.environment} environment
        # dbt run will execute all models in the dbt project
        process = subprocess.run(
            ['dbt', 'run', '--profiles-dir', '/dbt', '--project-dir', '/dbt', '--target', '${var.environment}'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if process.returncode == 0:
            result['status'] = 'success'
            # Parse output to count models (basic parsing)
            output_lines = process.stdout.split('\n')
            for line in output_lines:
                if 'Completed successfully' in line:
                    result['models_run'] += 1
            result['message'] = f"dbt transformations completed successfully. {result['models_run']} models processed."
        else:
            result['status'] = 'failed'
            result['errors'].append(process.stderr)
            result['message'] = f"dbt transformations failed: {process.stderr}"

    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
        result['errors'].append('dbt execution timed out after 10 minutes')
        result['message'] = 'dbt transformations timed out'

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        result['message'] = f"Error executing dbt: {str(e)}"

    return json.dumps(result)
EOT

  depends_on = [
    snowflake_schema.raw
  ]
}

# Grant execute permissions to ADMIN role
resource "snowflake_grant_privileges_to_account_role" "dbt_procedure_admin" {
  account_role_name = snowflake_account_role.admin.name
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.${snowflake_procedure_python.dbt_transformations.name}()"
  }
}

# Grant execute permissions to WRITE role
resource "snowflake_grant_privileges_to_account_role" "dbt_procedure_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}.${snowflake_procedure_python.dbt_transformations.name}()"
  }
}

# Output procedure information
output "dbt_stored_procedure_name" {
  value       = snowflake_procedure_python.dbt_transformations.name
  description = "Name of the stored procedure that runs dbt transformations"
}
