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
│                    DATA ENGINEERING ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────┘

1️⃣ DATA INGESTION
   ┌──────────────┐
   │  OpenF1 API  │  ← Real-time F1 data (sessions, drivers, positions)
   └──────┬───────┘
          │
          ↓
   ┌──────────────┐
   │  ETL Script  │  ← Python (Extract, Transform, Load)
   │  (Scheduled) │  ← Runs daily via GitHub Actions / Cron
   └──────┬───────┘
          │
          ↓
2️⃣ DATA WAREHOUSE
   ┌──────────────┐
   │  Snowflake   │  ← Centralized data storage
   │              │
   │  Tables:     │
   │  • sessions  │  ← Race sessions metadata
   │  • drivers   │  ← Driver information
   │  • positions │  ← Lap-by-lap positions
   │  • laps      │  ← Lap times & telemetry
   └──────┬───────┘
          │
          ↓
3️⃣ ANALYTICS & ML
   ┌──────────────┐
   │  ML Model    │  ← Trained on historical data
   │  (sklearn)   │  ← Predicts race winners
   └──────┬───────┘
          │
          ↓
4️⃣ VISUALIZATION
   ┌──────────────┐
   │  Streamlit   │  ← Interactive dashboard
   │  Dashboard   │  ← Connected to Snowflake
   │              │
   │  Features:   │
   │  • Real-time │  ← Live race data
   │  • Historical│  ← Trends & analytics
   │  • Predictions│ ← ML-powered insights
   └──────────────┘
          │
          ↓
5️⃣ INFRASTRUCTURE
   ┌──────────────┐
   │  AWS EC2     │  ← Docker container
   │  (t3.micro)  │  ← Hosts Streamlit app
   └──────────────┘

6️⃣ CI/CD & IaC
   ┌──────────────┐
   │  Terraform   │  ← Infrastructure as Code
   │              │  ← Multi-environment (dev/staging/prod)
   └──────────────┘
   ┌──────────────┐
   │  GitHub      │  ← CI/CD pipelines
   │  Actions     │  ← Automated testing & deployment
   └──────────────┘
```

---

## 🛠️ Tech Stack

**Data Engineering:** OpenF1 API, Python 3.11+, Snowflake, GitHub Actions
**Machine Learning:** scikit-learn (Random Forest Classifier)
**Visualization:** Streamlit, Altair, Plotly
**Infrastructure:** Terraform, AWS EC2, Docker
**CI/CD:** GitHub Actions, CodeQL

---

## 📁 Python Modules

### `main.py`

No module docstring found.

## 📦 Dependencies

- altair==5.5.0
- anyio==4.11.0
- attrs==25.4.0
- blinker==1.9.0
- cachetools==6.2.1
- certifi==2025.10.5
- charset-normalizer==3.4.4
- click==8.3.0
- gitdb==4.0.12
- gitpython==3.1.45
- h11==0.16.0
- httpcore==1.0.9
- httpx==0.28.1
- idna==3.11
- iniconfig==2.3.0
- jinja2==3.1.6
- jsonschema==4.25.1
- jsonschema-specifications==2025.9.1
- markupsafe==3.0.3
- narwhals==2.10.0
- numpy==2.3.4
- packaging==25.0
- pandas==2.3.3
- pillow==12.0.0
- pip==25.3
- pluggy==1.6.0
- protobuf==6.33.0
- pyarrow==21.0.0
- pydeck==0.9.1
- pygments==2.19.2
- pytest==8.4.2
- python-dateutil==2.9.0.post0
- pytz==2025.2
- referencing==0.37.0
- requests==2.32.5
- rpds-py==0.28.0
- setuptools==80.9.0
- six==1.17.0
- smmap==5.0.2
- sniffio==1.3.1
- streamlit==1.51.0
- tenacity==9.1.2
- toml==0.10.2
- tornado==6.5.2
- typing-extensions==4.15.0
- tzdata==2025.2
- urllib3==2.5.0
- wheel==0.45.1

---

## 👨‍💻 Author

**Flavia Ferreira**
- GitHub: [@youngpada1](https://github.com/youngpada1)
- Email: flavsferr@gmail.com

---

**Built with ❤️ using Python, Terraform, Snowflake, and AWS**

_README auto-generated via GitHub Actions_