# Source tables for raw F1 data from OpenF1 API
# These tables are created in the RAW schema and serve as sources for:
# - dbt transformations in the STAGING schema
# - Dynamic tables for data promotion to STAGING/PROD environments
# Only create regular tables in DEV environment - staging/prod use dynamic tables

# Sessions table - F1 session metadata
resource "snowflake_table" "sessions" {
  count    = var.environment == "dev" ? 1 : 0
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = "SESSIONS"
  comment  = "F1 session metadata from OpenF1 API"

  column {
    name     = "SESSION_KEY"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Unique session identifier"
  }

  column {
    name     = "SESSION_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Session name (e.g., 'Race', 'Qualifying')"
  }

  column {
    name     = "SESSION_TYPE"
    type     = "VARCHAR(100)"
    nullable = true
    comment  = "Type of session"
  }

  column {
    name     = "DATE_START"
    type     = "TIMESTAMP_NTZ"
    nullable = true
    comment  = "Session start timestamp"
  }

  column {
    name     = "DATE_END"
    type     = "TIMESTAMP_NTZ"
    nullable = true
    comment  = "Session end timestamp"
  }

  column {
    name     = "GMT_OFFSET"
    type     = "VARCHAR(10)"
    nullable = true
    comment  = "GMT offset for session location"
  }

  column {
    name     = "LOCATION"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Circuit location"
  }

  column {
    name     = "COUNTRY_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Country name"
  }

  column {
    name     = "CIRCUIT_SHORT_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Circuit short name"
  }

  column {
    name     = "YEAR"
    type     = "NUMBER(4,0)"
    nullable = false
    comment  = "Season year"
  }

  column {
    name     = "INGESTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
    comment  = "ETL ingestion timestamp"
  }

  primary_key {
    name = "PK_SESSIONS"
    keys = ["SESSION_KEY"]
  }
}

# Drivers table - F1 driver information
resource "snowflake_table" "drivers" {
  count    = var.environment == "dev" ? 1 : 0
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = "DRIVERS"
  comment  = "F1 driver information from OpenF1 API"

  column {
    name     = "DRIVER_NUMBER"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Driver racing number"
  }

  column {
    name     = "SESSION_KEY"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Session identifier"
  }

  column {
    name     = "BROADCAST_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Driver broadcast name"
  }

  column {
    name     = "FULL_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Driver full name"
  }

  column {
    name     = "NAME_ACRONYM"
    type     = "VARCHAR(10)"
    nullable = true
    comment  = "Driver name acronym (e.g., VER, HAM)"
  }

  column {
    name     = "TEAM_NAME"
    type     = "VARCHAR(255)"
    nullable = true
    comment  = "Team name"
  }

  column {
    name     = "TEAM_COLOUR"
    type     = "VARCHAR(10)"
    nullable = true
    comment  = "Team color hex code"
  }

  column {
    name     = "HEADSHOT_URL"
    type     = "VARCHAR(500)"
    nullable = true
    comment  = "Driver headshot image URL"
  }

  column {
    name     = "COUNTRY_CODE"
    type     = "VARCHAR(10)"
    nullable = true
    comment  = "Driver country code"
  }

  column {
    name     = "INGESTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
    comment  = "ETL ingestion timestamp"
  }

  primary_key {
    name = "PK_DRIVERS"
    keys = ["DRIVER_NUMBER", "SESSION_KEY"]
  }
}

# Laps table - Lap times and sector data
resource "snowflake_table" "laps" {
  count    = var.environment == "dev" ? 1 : 0
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = "LAPS"
  comment  = "Lap times and sector data from OpenF1 API"

  column {
    name     = "SESSION_KEY"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Session identifier"
  }

  column {
    name     = "DRIVER_NUMBER"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Driver number"
  }

  column {
    name     = "LAP_NUMBER"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Lap number"
  }

  column {
    name     = "LAP_DURATION"
    type     = "FLOAT"
    nullable = true
    comment  = "Total lap time in seconds"
  }

  column {
    name     = "SEGMENT_1_DURATION"
    type     = "FLOAT"
    nullable = true
    comment  = "Sector 1 duration in seconds"
  }

  column {
    name     = "SEGMENT_2_DURATION"
    type     = "FLOAT"
    nullable = true
    comment  = "Sector 2 duration in seconds"
  }

  column {
    name     = "SEGMENT_3_DURATION"
    type     = "FLOAT"
    nullable = true
    comment  = "Sector 3 duration in seconds"
  }

  column {
    name     = "IS_PIT_OUT_LAP"
    type     = "BOOLEAN"
    nullable = true
    comment  = "Whether this is a pit out lap"
  }

  column {
    name     = "DATE_START"
    type     = "TIMESTAMP_NTZ"
    nullable = true
    comment  = "Lap start timestamp"
  }

  column {
    name     = "INGESTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
    comment  = "ETL ingestion timestamp"
  }

  primary_key {
    name = "PK_LAPS"
    keys = ["SESSION_KEY", "DRIVER_NUMBER", "LAP_NUMBER"]
  }
}

# Positions table - Driver positions throughout the race
resource "snowflake_table" "positions" {
  count    = var.environment == "dev" ? 1 : 0
  database = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  schema   = snowflake_schema.raw.name
  name     = "POSITIONS"
  comment  = "Driver positions throughout the race from OpenF1 API"

  column {
    name     = "SESSION_KEY"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Session identifier"
  }

  column {
    name     = "DRIVER_NUMBER"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Driver number"
  }

  column {
    name     = "DATE"
    type     = "TIMESTAMP_NTZ"
    nullable = true
    comment  = "Timestamp of position"
  }

  column {
    name     = "POSITION"
    type     = "NUMBER(38,0)"
    nullable = false
    comment  = "Track position"
  }

  column {
    name     = "INGESTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
    comment  = "ETL ingestion timestamp"
  }

  primary_key {
    name = "PK_POSITIONS"
    keys = ["SESSION_KEY", "DRIVER_NUMBER", "DATE"]
  }
}
