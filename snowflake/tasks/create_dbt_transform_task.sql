-- ============================================================================
-- Task to run dbt transformations when new data arrives
-- This task checks the SESSIONS_STREAM and runs dbt when new data is detected
-- ============================================================================

-- Create task to run dbt transformations
CREATE OR REPLACE TASK ANALYTICS.DBT_TRANSFORM_TASK
WAREHOUSE = APEXML_DEV_WH  -- Change per environment (DEV/STAGING/PROD)
SCHEDULE = '5 MINUTE'  -- Check every 5 minutes
WHEN SYSTEM$STREAM_HAS_DATA('RAW.SESSIONS_STREAM')  -- Only run when stream has data
AS
CALL SYSTEM$RUN_DBT_CLOUD_JOB(
    <DBT_CLOUD_ACCOUNT_ID>,  -- Replace with your dbt Cloud account ID
    <DBT_CLOUD_JOB_ID>       -- Replace with your dbt Cloud job ID
);

-- Alternative: If using dbt Core instead of dbt Cloud, use external function
-- This requires setting up an external function to trigger dbt
-- CREATE OR REPLACE TASK ANALYTICS.DBT_TRANSFORM_TASK
-- WAREHOUSE = APEXML_DEV_WH
-- SCHEDULE = '5 MINUTE'
-- WHEN SYSTEM$STREAM_HAS_DATA('RAW.SESSIONS_STREAM')
-- AS
-- CALL ANALYTICS.RUN_DBT_CORE();  -- External function to run dbt Core

-- Grant permissions
GRANT OPERATE ON TASK ANALYTICS.DBT_TRANSFORM_TASK TO ROLE APEXML_DEV_CRUD;
GRANT MONITOR ON TASK ANALYTICS.DBT_TRANSFORM_TASK TO ROLE APEXML_DEV_READ;

-- Start the task (must be done explicitly)
-- ALTER TASK ANALYTICS.DBT_TRANSFORM_TASK RESUME;

-- To check task status:
-- SHOW TASKS LIKE 'DBT_TRANSFORM_TASK';
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) WHERE NAME = 'DBT_TRANSFORM_TASK' ORDER BY SCHEDULED_TIME DESC LIMIT 10;
