-- ============================================================================
-- Python Stored Procedure to Execute dbt Transformations - STAGING Environment
-- ============================================================================
-- This procedure runs dbt transformations when called by Snowflake tasks
-- It executes dbt commands using the snowflake-connector-python library
-- ============================================================================

CREATE PROCEDURE IF NOT EXISTS ANALYTICS.STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python', 'dbt-core', 'dbt-snowflake')
HANDLER = 'run_dbt'
AS
$$
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
        # Run dbt transformations for STAGING environment
        # dbt run will execute all models in the dbt project
        process = subprocess.run(
            ['dbt', 'run', '--profiles-dir', '/dbt', '--project-dir', '/dbt', '--target', 'staging'],
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
$$;

-- Grant execute permissions
GRANT USAGE ON PROCEDURE ANALYTICS.STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING() TO ROLE APEXML_STAGING_ADMIN;
GRANT USAGE ON PROCEDURE ANALYTICS.STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING() TO ROLE APEXML_STAGING_WRITE;

-- Usage:
-- CALL ANALYTICS.STORED_PROCEDURE_DBT_TRANSFORMATIONS_STAGING();
