# generate_readme.py

project_name = "ApexML"
description = "🏎️ ApexML is a machine learning pipeline to analyze and predict Formula 1 race outcomes using OpenF1 API data."

readme = f"""# {project_name}

{description}

## 📊 Features

- Fetches real-time F1 data using OpenF1 API
- Stores and processes data using Snowflake
- Predicts race outcomes with LLMs and statistical models
- Visualizes data using Streamlit
- Deployed via Docker and optionally hosted on AWS

## 🚀 Setup

```bash
uv venv
uv pip install -r requirements.txt
streamlit run app.py
