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

## 📁 Python Modules

### `main.py`

No module docstring found.

## 📦 Dependencies

Managed with **uv** package manager

**Production:**
- dbt-core>=1.10.13
- dbt-snowflake>=1.10.2
- httpx>=0.28.1
- snowflake-connector-python>=3.18.0


---

## 👨‍💻 Author

**Flavia Ferreira**
- GitHub: [@youngpada1](https://github.com/youngpada1)
- Email: flavsferr@gmail.com

---

**Built with ❤️ using Python, Terraform, Snowflake, and AWS**

_README auto-generated via GitHub Actions_