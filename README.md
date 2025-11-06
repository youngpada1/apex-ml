# ApexML - F1 Race Analytics & Prediction Platform

> An end-to-end data engineering and ML platform for Formula 1 race analytics, predictions, and visualizations.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)](https://streamlit.io/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8.svg)](https://www.snowflake.com/)
[![AWS](https://img.shields.io/badge/AWS-EC2-orange.svg)](https://aws.amazon.com/)

---

## 🎯 Project Overview

ApexML is a comprehensive data engineering and machine learning platform that:

- **Extracts** real-time Formula 1 data from the OpenF1 API
- **Transforms** and loads data into Snowflake data warehouse
- **Analyzes** historical race performance and driver statistics
- **Predicts** race outcomes using machine learning models
- **Visualizes** insights through an interactive Streamlit dashboard
- **Deploys** on AWS infrastructure with full CI/CD automation

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
   │ extract.py   │  ← Python ETL script
   │ load.py      │  ← Loads to Snowflake RAW schema
   │ (httpx)      │  ← Async HTTP client
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
   │              │  ← Data quality tests
   │  • Models    │  ← RAW → STAGING → ANALYTICS
   │  • Tests     │  ← not_null, unique, custom
   │  • Docs      │  ← Auto-generated lineage
   └──────┬───────┘
          │
          ↓
4️⃣ ANALYTICS & ML
   ┌──────────────┐
   │  ML Model    │  ← Trained on ANALYTICS schema
   │  (sklearn)   │  ← Predicts race winners
   └──────┬───────┘
          │
          ↓
5️⃣ VISUALIZATION
   ┌──────────────┐
   │  Streamlit   │  ← Interactive dashboard
   │  Dashboard   │  ← Queries ANALYTICS schema
   │              │
   │  Features:   │
   │  • Real-time │  ← Live race data
   │  • Historical│  ← Trends & analytics
   │  • Predictions│ ← ML-powered insights
   └──────────────┘
          │
          ↓
6️⃣ INFRASTRUCTURE
   ┌──────────────┐
   │  AWS EC2     │  ← Docker container
   │  (t3.micro)  │  ← Hosts Streamlit app
   └──────────────┘

7️⃣ CI/CD & IaC
   ┌──────────────┐
   │  Terraform   │  ← Infrastructure as Code (IaC)
   │              │  ← Snowflake + AWS resources
   │              │  ← Multi-environment (dev/staging/prod)
   └──────────────┘
   ┌──────────────┐
   │  GitHub      │  ← CI/CD pipelines
   │  Actions     │  ← Automated ETL + dbt runs
   └──────────────┘
```

---

## 🛠️ Tech Stack

**Data Ingestion:** OpenF1 API, Python 3.11+, httpx, snowflake-connector-python
**Transformation:** dbt Core, dbt-snowflake (SQL-based ELT)
**Data Warehouse:** Snowflake (RAW → STAGING → ANALYTICS schemas)
**Machine Learning:** scikit-learn (Random Forest Classifier)
**Visualization:** Streamlit, Altair, Plotly
**Infrastructure:** Terraform (IaC), AWS EC2, Docker
**Package Manager:** uv (fast Python package manager)
**CI/CD:** GitHub Actions, CodeQL

---

## 📦 Dependencies

Managed with **uv** package manager

**Total packages installed: 77**

<details>
<summary>View all packages</summary>

```
agate                          1.9.1
annotated-types                0.7.0
anyio                          4.11.0
asn1crypto                     1.5.1
attrs                          25.4.0
babel                          2.17.0
boto3                          1.40.66
botocore                       1.40.66
certifi                        2025.1.31
cffi                           1.17.1
charset-normalizer             3.4.4
click                          8.3.0
colorama                       0.4.6
cryptography                   45.0.7
daff                           1.4.2
dbt-adapters                   1.18.0
dbt-common                     1.35.0
dbt-core                       1.10.13
dbt-extractor                  0.6.0
dbt-protos                     1.0.382
dbt-semantic-interfaces        0.9.0
dbt-snowflake                  1.10.2
deepdiff                       8.6.1
filelock                       3.20.0
h11                            0.16.0
httpcore                       1.0.9
httpx                          0.28.1
idna                           3.11
importlib-metadata             8.7.0
isodate                        0.6.1
jaraco-classes                 3.4.0
jaraco-context                 6.0.1
jaraco-functools               4.3.0
jinja2                         3.1.6
jmespath                       1.0.1
jsonschema                     4.25.1
jsonschema-specifications      2025.9.1
keyring                        25.6.0
leather                        0.4.0
markupsafe                     3.0.3
mashumaro                      3.14
more-itertools                 10.8.0
msgpack                        1.1.2
networkx                       3.5
orderly-set                    5.5.0
packaging                      25.0
parsedatetime                  2.6
pathspec                       0.12.1
platformdirs                   4.5.0
protobuf                       6.33.0
pycparser                      2.23
pydantic                       2.12.4
pydantic-core                  2.41.5
pyjwt                          2.10.1
pyopenssl                      25.3.0
python-dateutil                2.9.0.post0
python-slugify                 8.0.4
pytimeparse                    1.1.8
pytz                           2025.2
pyyaml                         6.0.3
referencing                    0.37.0
requests                       2.32.5
rpds-py                        0.28.0
s3transfer                     0.14.0
six                            1.17.0
sniffio                        1.3.1
snowflake-connector-python     3.18.0
snowplow-tracker               1.1.0
sortedcontainers               2.4.0
sqlparse                       0.5.3
text-unidecode                 1.3
tomli                          2.3.0
tomlkit                        0.13.3
typing-extensions              4.15.0
typing-inspection              0.4.2
urllib3                        2.5.0
zipp                           3.23.0
```

</details>

---

## 👨‍💻 Author

**Flavia Ferreira**
- GitHub: [@youngpada1](https://github.com/youngpada1)
- Email: flavsferr@gmail.com

---

**Built with ❤️ using Python, Terraform, Snowflake, and AWS**

_README auto-generated via GitHub Actions_