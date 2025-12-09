-- ============================================================================
-- Stream to monitor changes in RAW.SESSIONS table
-- This stream will capture INSERT operations when new race data is loaded
-- ============================================================================

-- Create stream on SESSIONS table to detect new data
CREATE STREAM IF NOT EXISTS RAW.SESSIONS_STREAM
ON TABLE RAW.SESSIONS
SHOW_INITIAL_ROWS = FALSE  -- Only capture changes after stream creation
COMMENT = 'Stream to monitor new race sessions loaded into RAW.SESSIONS table';

-- Grant permissions to appropriate roles
GRANT SELECT ON STREAM RAW.SESSIONS_STREAM TO ROLE APEXML_DEV_CRUD;
GRANT SELECT ON STREAM RAW.SESSIONS_STREAM TO ROLE APEXML_STAGING_CRUD;
GRANT SELECT ON STREAM RAW.SESSIONS_STREAM TO ROLE APEXML_PROD_CRUD;
