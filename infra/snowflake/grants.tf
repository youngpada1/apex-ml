# Ownership grants - ACCOUNTADMIN owns databases, then grant ALL to SYSADMIN
resource "snowflake_grant_ownership" "database_ownership_dev" {
  count               = var.environment == "dev" ? 1 : 0
  account_role_name   = "ACCOUNTADMIN"
  on {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_dev[0].name
  }
}

resource "snowflake_grant_ownership" "database_ownership_staging" {
  count               = var.environment == "staging" ? 1 : 0
  account_role_name   = "ACCOUNTADMIN"
  on {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_staging[0].name
  }
}

resource "snowflake_grant_ownership" "database_ownership_prod" {
  count               = var.environment == "prod" ? 1 : 0
  account_role_name   = "ACCOUNTADMIN"
  on {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_prod[0].name
  }
}

# Grant ALL privileges on databases to SYSADMIN (Snowflake best practice)
resource "snowflake_grant_privileges_to_account_role" "database_all_sysadmin_dev" {
  count             = var.environment == "dev" ? 1 : 0
  account_role_name = "SYSADMIN"
  privileges        = ["ALL"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_dev[0].name
  }
  depends_on = [snowflake_grant_ownership.database_ownership_dev]
}

resource "snowflake_grant_privileges_to_account_role" "database_all_sysadmin_staging" {
  count             = var.environment == "staging" ? 1 : 0
  account_role_name = "SYSADMIN"
  privileges        = ["ALL"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_staging[0].name
  }
  depends_on = [snowflake_grant_ownership.database_ownership_staging]
}

resource "snowflake_grant_privileges_to_account_role" "database_all_sysadmin_prod" {
  count             = var.environment == "prod" ? 1 : 0
  account_role_name = "SYSADMIN"
  privileges        = ["ALL"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.apexml_prod[0].name
  }
  depends_on = [snowflake_grant_ownership.database_ownership_prod]
}

# Role hierarchy grants
resource "snowflake_grant_account_role" "data_engineer_to_sysadmin" {
  role_name        = snowflake_account_role.data_engineer.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "analytics_user_to_data_engineer" {
  role_name        = snowflake_account_role.analytics_user.name
  parent_role_name = snowflake_account_role.data_engineer.name
}

resource "snowflake_grant_account_role" "ml_engineer_to_data_engineer" {
  role_name        = snowflake_account_role.ml_engineer.name
  parent_role_name = snowflake_account_role.data_engineer.name
}

# Database grants
# Each workspace grants permissions to its own database (dev, staging, or prod)
resource "snowflake_grant_privileges_to_account_role" "database_usage_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["USAGE", "CREATE SCHEMA"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage_ml_engineer" {
  account_role_name = snowflake_account_role.ml_engineer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)
  }
}

# RAW schema grants
resource "snowflake_grant_privileges_to_account_role" "raw_schema_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "raw_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "raw_future_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.raw.name}"
    }
  }
}

# STAGING schema grants
resource "snowflake_grant_privileges_to_account_role" "staging_schema_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_views_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_schema_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["USAGE"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "staging_future_tables_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.staging.name}"
    }
  }
}

# ANALYTICS schema grants
resource "snowflake_grant_privileges_to_account_role" "analytics_schema_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["USAGE", "CREATE TABLE", "MODIFY"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_future_tables_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_schema_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["USAGE"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_future_tables_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_schema_ml_engineer" {
  account_role_name = snowflake_account_role.ml_engineer.name
  privileges        = ["USAGE"]

  on_schema {
    schema_name = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_future_tables_ml_engineer" {
  account_role_name = snowflake_account_role.ml_engineer.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = "${var.environment == "dev" ? snowflake_database.apexml_dev[0].name : (var.environment == "staging" ? snowflake_database.apexml_staging[0].name : snowflake_database.apexml_prod[0].name)}.${snowflake_schema.analytics.name}"
    }
  }
}

# Warehouse grants
resource "snowflake_grant_privileges_to_account_role" "etl_warehouse_data_engineer" {
  account_role_name = snowflake_account_role.data_engineer.name
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.etl_warehouse.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_warehouse_analytics_user" {
  account_role_name = snowflake_account_role.analytics_user.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.analytics_warehouse.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "analytics_warehouse_ml_engineer" {
  account_role_name = snowflake_account_role.ml_engineer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.analytics_warehouse.name
  }
}

# User role assignment
resource "snowflake_grant_account_role" "etl_service_account_data_engineer" {
  role_name = snowflake_account_role.data_engineer.name
  user_name = snowflake_user.etl_service_account.name
}
