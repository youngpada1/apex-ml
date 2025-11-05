# --- Tables in RAW Schema ---

resource "snowflake_table" "raw_sessions" {
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name
  name     = "SESSIONS"
  comment  = "Raw F1 session data from OpenF1 API"

  column {
    name = "SESSION_KEY"
    type = "NUMBER(38,0)"
    comment = "Unique session identifier"
  }

  column {
    name = "SESSION_NAME"
    type = "VARCHAR(100)"
  }

  column {
    name = "SESSION_TYPE"
    type = "VARCHAR(50)"
    comment = "Practice, Qualifying, Sprint, Race"
  }

  column {
    name = "DATE_START"
    type = "TIMESTAMP_NTZ"
  }

  column {
    name = "DATE_END"
    type = "TIMESTAMP_NTZ"
  }

  column {
    name = "GMT_OFFSET"
    type = "VARCHAR(10)"
  }

  column {
    name = "LOCATION"
    type = "VARCHAR(100)"
  }

  column {
    name = "COUNTRY_NAME"
    type = "VARCHAR(100)"
  }

  column {
    name = "CIRCUIT_SHORT_NAME"
    type = "VARCHAR(50)"
  }

  column {
    name = "YEAR"
    type = "NUMBER(4,0)"
  }

  column {
    name = "INGESTED_AT"
    type = "TIMESTAMP_NTZ"
    comment = "ETL ingestion timestamp"
  }
}

resource "snowflake_table" "raw_drivers" {
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name
  name     = "DRIVERS"
  comment  = "Raw F1 driver data from OpenF1 API"

  column {
    name = "DRIVER_NUMBER"
    type = "NUMBER(3,0)"
  }

  column {
    name = "SESSION_KEY"
    type = "NUMBER(38,0)"
  }

  column {
    name = "BROADCAST_NAME"
    type = "VARCHAR(50)"
  }

  column {
    name = "FULL_NAME"
    type = "VARCHAR(100)"
  }

  column {
    name = "NAME_ACRONYM"
    type = "VARCHAR(3)"
  }

  column {
    name = "TEAM_NAME"
    type = "VARCHAR(100)"
  }

  column {
    name = "TEAM_COLOUR"
    type = "VARCHAR(6)"
  }

  column {
    name = "HEADSHOT_URL"
    type = "VARCHAR(500)"
  }

  column {
    name = "COUNTRY_CODE"
    type = "VARCHAR(3)"
  }

  column {
    name = "INGESTED_AT"
    type = "TIMESTAMP_NTZ"
  }
}

resource "snowflake_table" "raw_positions" {
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name
  name     = "POSITIONS"
  comment  = "Raw lap-by-lap position data from OpenF1 API"

  column {
    name = "SESSION_KEY"
    type = "NUMBER(38,0)"
  }

  column {
    name = "DRIVER_NUMBER"
    type = "NUMBER(3,0)"
  }

  column {
    name = "DATE"
    type = "TIMESTAMP_NTZ"
  }

  column {
    name = "POSITION"
    type = "NUMBER(2,0)"
  }

  column {
    name = "INGESTED_AT"
    type = "TIMESTAMP_NTZ"
  }
}

resource "snowflake_table" "raw_laps" {
  database = snowflake_database.apexml.name
  schema   = snowflake_schema.raw.name
  name     = "LAPS"
  comment  = "Raw lap times and telemetry from OpenF1 API"

  column {
    name = "SESSION_KEY"
    type = "NUMBER(38,0)"
  }

  column {
    name = "DRIVER_NUMBER"
    type = "NUMBER(3,0)"
  }

  column {
    name = "LAP_NUMBER"
    type = "NUMBER(3,0)"
  }

  column {
    name = "LAP_DURATION"
    type = "FLOAT"
    comment = "Lap time in seconds"
  }

  column {
    name = "SEGMENT_1_DURATION"
    type = "FLOAT"
  }

  column {
    name = "SEGMENT_2_DURATION"
    type = "FLOAT"
  }

  column {
    name = "SEGMENT_3_DURATION"
    type = "FLOAT"
  }

  column {
    name = "IS_PIT_OUT_LAP"
    type = "BOOLEAN"
  }

  column {
    name = "DATE_START"
    type = "TIMESTAMP_NTZ"
  }

  column {
    name = "INGESTED_AT"
    type = "TIMESTAMP_NTZ"
  }
}

# --- Grants ---
# Note: Table grants will be managed via SQL GRANT statements after Terraform creates the infrastructure
# The role hierarchy (SYSADMIN → DATA_ENGINEER) automatically inherits necessary permissions
