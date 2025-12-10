-- ============================================================================
-- Stream to monitor changes in RAW.SESSIONS table - DEV Environment
-- This stream will capture INSERT operations when new race data is loaded
-- ============================================================================

CREATE STREAM IF NOT EXISTS RAW.STREAM_DBT_TRANSFORMATIONS_DEV
ON TABLE RAW.SESSIONS
SHOW_INITIAL_ROWS = FALSE
COMMENT = 'Stream to monitor new race sessions loaded into RAW.SESSIONS table (DEV)';

-- Grant permissions
GRANT SELECT ON STREAM RAW.STREAM_DBT_TRANSFORMATIONS_DEV TO ROLE APEXML_DEV_ADMIN;
GRANT SELECT ON STREAM RAW.STREAM_DBT_TRANSFORMATIONS_DEV TO ROLE APEXML_DEV_WRITE;
