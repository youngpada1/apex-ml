# ApexML - F1 Race Analytics & Prediction Platform

> An end-to-end data engineering and ML platform for Formula 1 race analytics, predictions, and visualizations.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)](https://streamlit.io/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8.svg)](https://www.snowflake.com/)
[![AWS](https://img.shields.io/badge/AWS-EC2-orange.svg)](https://aws.amazon.com/)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Infrastructure](#-infrastructure)
- [Data Pipeline](#-data-pipeline)
- [ML Model](#-ml-model)
- [Deployment](#-deployment)
- [CI/CD](#-cicd)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 Project Overview

ApexML is a comprehensive data engineering and machine learning platform that:

- **Extracts** real-time Formula 1 data from the OpenF1 API
- **Transforms** and loads data into Snowflake data warehouse
- **Analyzes** historical race performance and driver statistics
- **Predicts** race outcomes using machine learning models
- **Visualizes** insights through an interactive Streamlit dashboard
- **Deploys** on AWS infrastructure with full CI/CD automation

This project demonstrates proficiency in:
- Data Engineering (ETL pipelines, data warehousing)
- DevOps (IaC, containerization, CI/CD)
- Machine Learning (predictive modeling)
- Cloud Infrastructure (AWS EC2, Snowflake)
- Software Engineering best practices

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

### **Data Engineering**
- **Data Source**: [OpenF1 API](https://openf1.org/) - Real-time Formula 1 data
- **ETL**: Python 3.11+ with `httpx`, `pandas`
- **Data Warehouse**: Snowflake (cloud data platform)
- **Orchestration**: GitHub Actions (scheduled workflows)

### **Machine Learning**
- **Framework**: scikit-learn
- **Model**: Random Forest Classifier (race outcome prediction)
- **Features**: Driver stats, circuit history, qualifying positions

### **Visualization**
- **Frontend**: Streamlit 1.51+
- **Charts**: Altair, Plotly
- **Database Connector**: snowflake-connector-python

### **Infrastructure & DevOps**
- **IaC**: Terraform 1.6+ (workspace-based multi-env)
- **Cloud**: AWS EC2 (t3.micro, free tier)
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: AWS CloudWatch (billing alerts)

### **Development**
- **Version Control**: Git, GitHub
- **Code Quality**: pytest, CodeQL
- **Secrets Management**: GitHub Secrets, Terraform sensitive variables

---

## ✨ Features

### **Data Pipeline**
- ✅ Automated daily data ingestion from OpenF1 API
- ✅ ETL pipeline with data validation & transformation
- ✅ Incremental data loading to Snowflake
- ✅ Historical data retention for trend analysis

### **Analytics Dashboard**
- ✅ Real-time race session tracking
- ✅ Historical performance analysis
- ✅ Driver & team comparisons
- ✅ Lap time visualizations
- ✅ Circuit-specific statistics

### **ML Predictions**
- ✅ Race winner prediction based on historical data
- ✅ Driver performance forecasting
- ✅ Confidence scores & probability distributions
- ✅ Model retraining on new data

### **Infrastructure**
- ✅ Multi-environment setup (dev, staging, prod)
- ✅ Terraform workspace-based state management
- ✅ AWS free tier optimization (cost monitoring)
- ✅ Docker containerization for portability
- ✅ Automated deployments via CI/CD

---

## 📁 Project Structure

```
apex-ml/
├── .github/
│   └── workflows/
│       ├── codeql.yml              # Security scanning
│       ├── generate-readme.yml     # Auto-generate README
│       └── etl-pipeline.yml        # Scheduled ETL job
├── app/
│   ├── app.py                      # Streamlit dashboard
│   └── tests/
│       └── test_app.py             # Unit tests
├── etl/
│   ├── extract.py                  # Fetch data from OpenF1 API
│   ├── transform.py                # Data cleaning & validation
│   ├── load.py                     # Load to Snowflake
│   └── config.py                   # ETL configuration
├── ml/
│   ├── train.py                    # Model training
│   ├── predict.py                  # Inference
│   └── model.pkl                   # Trained model
├── infra/
│   ├── main.tf                     # Terraform main config
│   ├── variables.tf                # Terraform variables
│   ├── outputs.tf                  # Terraform outputs
│   ├── billing_alerts.tf.disabled  # AWS billing alerts (optional)
│   ├── dev.tfvars                  # Dev environment
│   ├── staging.tfvars              # Staging environment
│   └── prod.tfvars                 # Prod environment
├── sql/
│   └── schema.sql                  # Snowflake table definitions
├── scripts/
│   └── generate_readme.py          # Auto-generate README
├── Dockerfile                      # Container definition
├── docker-compose.yml              # Local development
├── requirements.txt                # Python dependencies
├── .dockerignore                   # Docker exclusions
├── .gitignore                      # Git exclusions
└── README.md                       # Project documentation
```

---

## 🚀 Setup & Installation

### **Prerequisites**

- Python 3.11+
- Docker & Docker Compose
- Terraform 1.6+
- AWS Account (free tier)
- Snowflake Account (free trial: $400 credits)
- GitHub Account

### **Local Development**

```bash
# Clone repository
git clone https://github.com/youngpada1/apex-ml.git
cd apex-ml

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit locally
streamlit run app/app.py
```

### **Docker Setup**

```bash
# Build image
docker build -t apex-ml:latest .

# Run container
docker run -p 8501:8501 apex-ml:latest

# Or use docker-compose
docker-compose up
```

---

## 🏗️ Infrastructure

### **Terraform Workspace Setup**

```bash
cd infra

# Initialize Terraform
terraform init

# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Deploy to dev
terraform workspace select dev
terraform apply -var-file="dev.tfvars" -var="github_token=$GITHUB_TOKEN"
```

### **Multi-Environment Configuration**

| Environment | Instance Type | Monitoring | Log Retention |
|-------------|--------------|------------|---------------|
| **dev**     | t3.micro     | Disabled   | 7 days        |
| **staging** | t3.micro     | Enabled    | 14 days       |
| **prod**    | t3.micro     | Enabled    | 30 days       |

---

## 🔄 Data Pipeline

### **ETL Process**

```python
# Extract
data = extract_from_openf1_api(
    endpoint="/v1/sessions",
    params={"year": 2025}
)

# Transform
cleaned_data = transform_data(data)
validated_data = validate_schema(cleaned_data)

# Load
load_to_snowflake(
    data=validated_data,
    table="sessions",
    mode="append"
)
```

### **Snowflake Schema**

```sql
-- Sessions
CREATE TABLE sessions (
    session_key INT PRIMARY KEY,
    session_name VARCHAR(100),
    date_start TIMESTAMP,
    circuit_key INT,
    year INT
);

-- Drivers
CREATE TABLE drivers (
    driver_number INT PRIMARY KEY,
    full_name VARCHAR(100),
    team_name VARCHAR(100),
    country_code VARCHAR(3)
);

-- Positions (for ML)
CREATE TABLE positions (
    position_id INT AUTOINCREMENT PRIMARY KEY,
    session_key INT,
    driver_number INT,
    position INT,
    timestamp TIMESTAMP
);
```

---

## 🤖 ML Model

### **Features**

- Driver historical performance
- Circuit-specific statistics
- Qualifying position
- Weather conditions
- Team performance metrics

### **Model Training**

```python
from sklearn.ensemble import RandomForestClassifier

# Load historical data from Snowflake
df = load_training_data()

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Model Accuracy: {accuracy:.2%}")
```

---

## 🚢 Deployment

### **AWS EC2 Deployment**

1. Provision EC2 instance via Terraform
2. Deploy Docker container
3. Configure security groups
4. Set up Elastic IP (optional)

### **Streamlit Cloud (Alternative)**

```bash
# Deploy to Streamlit Cloud
streamlit deploy app/app.py
```

---

## 🔄 CI/CD

### **GitHub Actions Workflows**

- **CodeQL**: Security scanning on every push
- **README Generation**: Auto-update on file changes
- **ETL Pipeline**: Scheduled daily data ingestion
- **Testing**: Run pytest on PRs
- **Deployment**: Auto-deploy on main branch merge

---

## 🔮 Future Enhancements

- [ ] Real-time WebSocket data streaming
- [ ] Advanced ML models (XGBoost, Neural Networks)
- [ ] Multi-model ensemble predictions
- [ ] Historical race replay visualization
- [ ] Driver comparison tool
- [ ] Mobile-responsive dashboard
- [ ] Email alerts for race predictions
- [ ] API endpoint for predictions

---

## 📊 Project Metrics

- **Data Sources**: 1 (OpenF1 API)
- **Data Tables**: 4+ (Snowflake)
- **ETL Jobs**: 1 (scheduled daily)
- **ML Models**: 1 (Random Forest)
- **Environments**: 3 (dev, staging, prod)
- **CI/CD Pipelines**: 4 (GitHub Actions)
- **Cloud Providers**: 2 (AWS, Snowflake)

---

## 👨‍💻 Author

**Flavia Ferreira**
- GitHub: [@youngpada1](https://github.com/youngpada1)
- Email: flavsferr@gmail.com

---

## 📝 License

This project is for portfolio demonstration purposes.

---

## 🙏 Acknowledgments

- [OpenF1](https://openf1.org/) for providing free F1 data API
- Snowflake for free trial credits
- AWS for free tier resources

---

**Built with ❤️ using Python, Terraform, Snowflake, and AWS**
