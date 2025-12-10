-- ============================================================================
-- Stream to monitor changes in RAW.SESSIONS table - PROD Environment
-- This stream will capture INSERT operations when new race data is loaded
-- ============================================================================

CREATE STREAM IF NOT EXISTS RAW.STREAM_DBT_TRANSFORMATIONS_PROD
ON TABLE RAW.SESSIONS
SHOW_INITIAL_ROWS = FALSE
COMMENT = 'Stream to monitor new race sessions loaded into RAW.SESSIONS table (PROD)';

-- Grant permissions
GRANT SELECT ON STREAM RAW.STREAM_DBT_TRANSFORMATIONS_PROD TO ROLE APEXML_PROD_ADMIN;
GRANT SELECT ON STREAM RAW.STREAM_DBT_TRANSFORMATIONS_PROD TO ROLE APEXML_PROD_WRITE;
