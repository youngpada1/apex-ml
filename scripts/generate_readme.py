#!/usr/bin/env python3
"""Auto-generate README.md from pyproject.toml and installed packages."""

import subprocess
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_direct_dependencies():
    """Extract direct dependencies from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return data.get("project", {}).get("dependencies", [])


def get_all_installed_packages():
    """Get all installed packages from uv pip list"""
    try:
        result = subprocess.run(
            ["uv", "pip", "list", "--format=columns"],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout:
            lines = result.stdout.strip().split("\n")
            # Skip header lines
            package_lines = [line for line in lines[2:] if line.strip()]
            packages = []

            for line in package_lines:
                parts = line.split()
                if len(parts) >= 2:
                    packages.append((parts[0], parts[1]))

            return packages
    except Exception as e:
        print(f"Warning: Could not get package list: {e}")
        return []


def generate_readme():
    """Generate README.md content"""
    direct_deps = get_direct_dependencies()
    all_packages = get_all_installed_packages()

    readme_content = f"""# ApexML - F1 Race Analytics Platform

A comprehensive data engineering platform for Formula 1 race analytics using OpenF1 API, Snowflake, dbt, and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)](https://streamlit.io/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8.svg)](https://www.snowflake.com/)

---

## 🎯 Project Overview

ApexML is a comprehensive data engineering platform that:

- **Extracts** real-time Formula 1 data from the OpenF1 API
- **Loads** data into Snowflake data warehouse (RAW schema)
- **Transforms** data using dbt (STAGING → ANALYTICS schemas)
- **Tests** data quality with automated dbt tests
- **Visualizes** insights through an interactive Streamlit dashboard

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              MODERN DATA ENGINEERING ARCHITECTURE (ELT)              │
└─────────────────────────────────────────────────────────────────────┘

1️⃣ DATA INGESTION (Extract & Load)
   ┌──────────────┐
   │  OpenF1 API  │  ← Real-time F1 data (REST API)
   └──────┬───────┘
          │
          ↓ httpx
   ┌──────────────┐
   │ extract.py   │  ← Python ELT script
   │ load.py      │  ← Loads to Snowflake RAW schema
   └──────┬───────┘
          │
          ↓
2️⃣ DATA WAREHOUSE (Snowflake)
   ┌────────────────────────────────────────┐
   │         APEXML_DEV Database            │
   ├────────────────────────────────────────┤
   │  📁 RAW Schema                         │
   │    • sessions   (raw API data)         │
   │    • drivers    (raw API data)         │
   │    • positions  (raw API data)         │
   │    • laps       (raw API data)         │
   ├────────────────────────────────────────┤
   │           ↓ dbt transformations        │
   ├────────────────────────────────────────┤
   │  📁 STAGING Schema (views)             │
   │    • stg_sessions   (cleaned)          │
   │    • stg_drivers    (deduplicated)     │
   │    • stg_laps       (validated)        │
   │    • stg_positions  (filtered)         │
   ├────────────────────────────────────────┤
   │           ↓ dbt transformations        │
   ├────────────────────────────────────────┤
   │  📁 ANALYTICS Schema (tables)          │
   │    • dim_drivers        (dimension)    │
   │    • fct_lap_times      (fact)         │
   │    • fct_race_results   (fact)         │
   └────────┬───────────────────────────────┘
            │
            ↓
3️⃣ TRANSFORMATION (dbt)
   ┌──────────────┐
   │  dbt Core    │  ← SQL-based transformations
   │              │  ← Data quality tests (22 passing)
   │  • Models    │  ← RAW → STAGING → ANALYTICS
   │  • Tests     │  ← not_null, unique, custom
   └──────┬───────┘
          │
          ↓
4️⃣ VISUALIZATION
   ┌──────────────┐
   │  Streamlit   │  ← Interactive dashboard
   │  Dashboard   │  ← Queries ANALYTICS schema
   └──────────────┘
          │
          ↓
5️⃣ INFRASTRUCTURE
   ┌──────────────┐
   │  Terraform   │  ← Infrastructure as Code (IaC)
   │              │  ← Snowflake resources
   │              │  ← Multi-environment (dev/staging/prod)
   └──────────────┘
```

---

## 🛠️ Tech Stack

**Data Ingestion:** OpenF1 API, Python 3.11+, httpx, snowflake-connector-python
**Transformation:** dbt Core, dbt-snowflake (SQL-based ELT)
**Data Warehouse:** Snowflake (RAW → STAGING → ANALYTICS schemas)
**Visualization:** Streamlit
**Infrastructure:** Terraform (IaC)
**Package Manager:** uv (fast Python package manager)
**Testing:** pytest
**CI/CD:** GitHub Actions

---

## 📦 Dependencies

Managed with **uv** package manager (see [pyproject.toml](pyproject.toml))

### Direct Dependencies

```
{chr(10).join(direct_deps)}
```

### All Installed Packages ({len(all_packages)} total)

<details>
<summary>View all packages</summary>

```
{chr(10).join(f"{name:<40} {version}" for name, version in all_packages)}
```

</details>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11-3.13
- uv package manager
- Snowflake account
- Terraform

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <your-repo-url>
cd apex-ml

# Install dependencies
uv sync
```

### Running the Pipeline

```bash
# 1. Deploy Snowflake infrastructure
cd infra/snowflake
terraform init
terraform apply -var="environment=dev"

# 2. Run data extraction and loading
cd ../..
uv run python snowflake/elt/load.py <session_key>

# 3. Run dbt transformations
./scripts/run_dbt.sh

# 4. Run dbt tests
cd snowflake/dbt_project
uv run dbt test

# 5. Launch Streamlit dashboard
cd ../..
uv run streamlit run app/app.py
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run API tests
uv run pytest tests/test_api.py -v

# Run dbt tests
cd snowflake/dbt_project
uv run dbt test
```

---

## 📁 Project Structure

```
apex-ml/
├── app/                      # Streamlit dashboard
├── snowflake/
│   ├── dbt_project/          # dbt transformations
│   │   ├── models/
│   │   │   ├── sources/      # Source definitions
│   │   │   ├── staging/      # Staging views
│   │   │   └── analytics/    # Analytics tables
│   │   ├── dbt_project.yml
│   │   └── profiles.yml
│   ├── elt/                  # Data pipeline scripts
│   │   ├── extract.py
│   │   └── load.py
│   └── config/               # Snowflake configs
├── infra/
│   └── snowflake/            # Terraform infrastructure
│       ├── main.tf
│       ├── grants.tf
│       └── tables.tf
├── scripts/                  # Shell scripts
│   ├── run_dbt.sh
│   └── setup_snowflake_keypair.sh
├── tests/                    # Test files
│   └── test_api.py
├── ml/                       # ML models (future)
└── pyproject.toml            # Dependencies & config
```

---

## 🔐 Security

- Uses JWT authentication for Snowflake
- Private keys stored securely (not in repo)
- Environment variables for sensitive data
- Terraform state encryption

---

## 👨‍💻 Author

**Flavia Ferreira**
- GitHub: [@youngpada1](https://github.com/youngpada1)
- Email: flavsferr@gmail.com

---

**Built with ❤️ using Python, Terraform, Snowflake, and dbt**

_README auto-generated via GitHub Actions_
"""

    # Write to README.md
    readme_path = Path(__file__).parent.parent / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print("✓ README.md generated successfully")
    print(f"✓ Direct dependencies: {len(direct_deps)}")
    print(f"✓ Total packages: {len(all_packages)}")


if __name__ == "__main__":
    generate_readme()
