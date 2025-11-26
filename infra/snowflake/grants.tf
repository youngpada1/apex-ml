# Role hierarchy grants
# ACCOUNTADMIN → SYSADMIN → ADMIN → WRITE → READ
resource "snowflake_grant_account_role" "admin_to_sysadmin" {
  role_name        = snowflake_account_role.admin.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "write_to_admin" {
  role_name        = snowflake_account_role.write.name
  parent_role_name = snowflake_account_role.admin.name
}

resource "snowflake_grant_account_role" "read_to_write" {
  role_name        = snowflake_account_role.read.name
  parent_role_name = snowflake_account_role.write.name
}

# Database grants
# Each workspace grants permissions to its own database (dev, staging, or prod)
resource "snowflake_grant_privileges_to_account_role" "database_usage_admin" {
  account_role_name = snowflake_account_role.admin.name
  privileges        = ["USAGE", "CREATE SCHEMA", "MODIFY", "MONITOR"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE", "CREATE SCHEMA"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

# RAW schema grants - WRITE role can load data
resource "snowflake_grant_privileges_to_account_role" "raw_schema_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "raw_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "raw_future_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
    }
  }
}

# STAGING schema grants - WRITE role can transform data
resource "snowflake_grant_privileges_to_account_role" "staging_schema_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_views_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

# READ role can read from STAGING schema
resource "snowflake_grant_privileges_to_account_role" "staging_schema_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["USAGE"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_tables_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

# ANALYTICS schema grants - WRITE role can create analytics tables
resource "snowflake_grant_privileges_to_account_role" "analytics_schema_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE", "CREATE TABLE", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_future_tables_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

# READ role can read from ANALYTICS schema (main app access)
resource "snowflake_grant_privileges_to_account_role" "analytics_schema_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["USAGE"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_future_tables_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

# Warehouse grants
resource "snowflake_grant_privileges_to_account_role" "etl_warehouse_write" {
  account_role_name = snowflake_account_role.write.name
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.etl_warehouse.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_warehouse_read" {
  account_role_name = snowflake_account_role.read.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.analytics_warehouse.name
  }
}

# User role assignment
resource "snowflake_grant_account_role" "etl_service_account_write" {
  role_name = snowflake_account_role.write.name
  user_name = snowflake_user.etl_service_account.name
}
