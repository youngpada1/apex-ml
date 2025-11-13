# ApexML - F1 Race Analytics Platform

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
dbt-core>=1.10.13
dbt-snowflake>=1.10.2
httpx>=0.28.1
snowflake-connector-python>=3.18.0
pytest>=8.3.4
streamlit>=1.40.2
```

### All Installed Packages (100 total)

<details>
<summary>View all packages</summary>

```
agate                                    1.9.1
altair                                   5.5.0
annotated-types                          0.7.0
anyio                                    4.11.0
asn1crypto                               1.5.1
attrs                                    25.4.0
babel                                    2.17.0
blinker                                  1.9.0
boto3                                    1.40.66
botocore                                 1.40.66
cachetools                               6.2.1
certifi                                  2025.1.31
cffi                                     1.17.1
charset-normalizer                       3.4.4
click                                    8.3.0
colorama                                 0.4.6
cryptography                             45.0.7
daff                                     1.4.2
dbt-adapters                             1.18.0
dbt-common                               1.35.0
dbt-core                                 1.10.13
dbt-extractor                            0.6.0
dbt-protos                               1.0.382
dbt-semantic-interfaces                  0.9.0
dbt-snowflake                            1.10.2
deepdiff                                 8.6.1
filelock                                 3.20.0
gitdb                                    4.0.12
gitpython                                3.1.45
h11                                      0.16.0
httpcore                                 1.0.9
httpx                                    0.28.1
idna                                     3.11
importlib-metadata                       8.7.0
iniconfig                                2.3.0
isodate                                  0.6.1
jaraco-classes                           3.4.0
jaraco-context                           6.0.1
jaraco-functools                         4.3.0
jeepney                                  0.9.0
jinja2                                   3.1.6
jmespath                                 1.0.1
jsonschema                               4.25.1
jsonschema-specifications                2025.9.1
keyring                                  25.6.0
leather                                  0.4.0
markupsafe                               3.0.3
mashumaro                                3.14
more-itertools                           10.8.0
msgpack                                  1.1.2
narwhals                                 2.10.2
networkx                                 3.5
numpy                                    2.3.4
orderly-set                              5.5.0
packaging                                25.0
pandas                                   2.3.3
parsedatetime                            2.6
pathspec                                 0.12.1
pillow                                   12.0.0
platformdirs                             4.5.0
pluggy                                   1.6.0
protobuf                                 6.33.0
pyarrow                                  21.0.0
pycparser                                2.23
pydantic                                 2.12.4
pydantic-core                            2.41.5
pydeck                                   0.9.1
pygments                                 2.19.2
pyjwt                                    2.10.1
pyopenssl                                25.3.0
pytest                                   8.4.2
python-dateutil                          2.9.0.post0
python-slugify                           8.0.4
pytimeparse                              1.1.8
pytz                                     2025.2
pyyaml                                   6.0.3
referencing                              0.37.0
requests                                 2.32.5
rpds-py                                  0.28.0
s3transfer                               0.14.0
secretstorage                            3.4.0
six                                      1.17.0
smmap                                    5.0.2
sniffio                                  1.3.1
snowflake-connector-python               3.18.0
snowplow-tracker                         1.1.0
sortedcontainers                         2.4.0
sqlparse                                 0.5.3
streamlit                                1.51.0
tenacity                                 9.1.2
text-unidecode                           1.3
toml                                     0.10.2
tomlkit                                  0.13.3
tornado                                  6.5.2
typing-extensions                        4.15.0
typing-inspection                        0.4.2
tzdata                                   2025.2
urllib3                                  2.5.0
watchdog                                 6.0.0
zipp                                     3.23.0
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
./library/tf.sh plan dev    # Preview changes
./library/tf.sh apply dev    # Apply changes

# 2. Run data extraction and loading
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

#### Terraform Helper Script

The `library/tf.sh` script automatically loads environment variables from `.env` and runs Terraform commands:

```bash
# Usage: ./library/tf.sh <command> <environment>

# Initialize Terraform
./library/tf.sh init dev

# Preview changes
./library/tf.sh plan dev
./library/tf.sh plan staging
./library/tf.sh plan prod

# Apply changes
./library/tf.sh apply dev

# Validate configuration
./library/tf.sh validate dev

# Destroy infrastructure (be careful!)
./library/tf.sh destroy dev
```

**Requirements:**
- `.env` file in project root with `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_USER`
- Private key at `~/.ssh/snowflake_key.p8`
- Terraform installed

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
├── library/                  # Helper scripts
│   └── tf.sh                 # Terraform wrapper script
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
