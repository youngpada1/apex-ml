import os
from pathlib import Path

def extract_docstring(file_path: str) -> str:
    """Extract the first module-level docstring from a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for quote in ('"""', "'''"):
        if quote in content:
            start = content.find(quote) + 3
            end = content.find(quote, start)
            if end > start:
                return content[start:end].strip()
    return "No module docstring found."

def generate_readme():
    project_name = "ApexML - F1 Race Analytics & Prediction Platform"

    readme = [
        f"# {project_name}",
        "",
        "> An end-to-end data engineering and ML platform for Formula 1 race analytics, predictions, and visualizations.",
        "",
        "[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)",
        "[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple.svg)](https://www.terraform.io/)",
        "[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)](https://streamlit.io/)",
        "[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8.svg)](https://www.snowflake.com/)",
        "[![AWS](https://img.shields.io/badge/AWS-EC2-orange.svg)](https://aws.amazon.com/)",
        "",
        "---",
        "",
        "## 🎯 Project Overview",
        "",
        "ApexML is a comprehensive data engineering and machine learning platform that:",
        "",
        "- **Extracts** real-time Formula 1 data from the OpenF1 API",
        "- **Transforms** and loads data into Snowflake data warehouse",
        "- **Analyzes** historical race performance and driver statistics",
        "- **Predicts** race outcomes using machine learning models",
        "- **Visualizes** insights through an interactive Streamlit dashboard",
        "- **Deploys** on AWS infrastructure with full CI/CD automation",
        "",
        "---",
        "",
        "## 🏗️ Architecture",
        "",
        "```",
        "┌─────────────────────────────────────────────────────────────────────┐",
        "│                    DATA ENGINEERING ARCHITECTURE                     │",
        "└─────────────────────────────────────────────────────────────────────┘",
        "",
        "1️⃣ DATA INGESTION",
        "   ┌──────────────┐",
        "   │  OpenF1 API  │  ← Real-time F1 data (sessions, drivers, positions)",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "   ┌──────────────┐",
        "   │  ETL Script  │  ← Python (Extract, Transform, Load)",
        "   │  (Scheduled) │  ← Runs daily via GitHub Actions / Cron",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "2️⃣ DATA WAREHOUSE",
        "   ┌──────────────┐",
        "   │  Snowflake   │  ← Centralized data storage",
        "   │              │",
        "   │  Tables:     │",
        "   │  • sessions  │  ← Race sessions metadata",
        "   │  • drivers   │  ← Driver information",
        "   │  • positions │  ← Lap-by-lap positions",
        "   │  • laps      │  ← Lap times & telemetry",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "3️⃣ ANALYTICS & ML",
        "   ┌──────────────┐",
        "   │  ML Model    │  ← Trained on historical data",
        "   │  (sklearn)   │  ← Predicts race winners",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "4️⃣ VISUALIZATION",
        "   ┌──────────────┐",
        "   │  Streamlit   │  ← Interactive dashboard",
        "   │  Dashboard   │  ← Connected to Snowflake",
        "   │              │",
        "   │  Features:   │",
        "   │  • Real-time │  ← Live race data",
        "   │  • Historical│  ← Trends & analytics",
        "   │  • Predictions│ ← ML-powered insights",
        "   └──────────────┘",
        "          │",
        "          ↓",
        "5️⃣ INFRASTRUCTURE",
        "   ┌──────────────┐",
        "   │  AWS EC2     │  ← Docker container",
        "   │  (t3.micro)  │  ← Hosts Streamlit app",
        "   └──────────────┘",
        "",
        "6️⃣ CI/CD & IaC",
        "   ┌──────────────┐",
        "   │  Terraform   │  ← Infrastructure as Code",
        "   │              │  ← Multi-environment (dev/staging/prod)",
        "   └──────────────┘",
        "   ┌──────────────┐",
        "   │  GitHub      │  ← CI/CD pipelines",
        "   │  Actions     │  ← Automated testing & deployment",
        "   └──────────────┘",
        "```",
        "",
        "---",
        "",
        "## 🛠️ Tech Stack",
        "",
        "**Data Engineering:** OpenF1 API, Python 3.11+, Snowflake, GitHub Actions",
        "**Machine Learning:** scikit-learn (Random Forest Classifier)",
        "**Visualization:** Streamlit, Altair, Plotly",
        "**Infrastructure:** Terraform, AWS EC2, Docker",
        "**CI/CD:** GitHub Actions, CodeQL",
        "",
        "---",
        "",
    ]

    # Add Python modules section
    py_files = sorted(
        [f for f in os.listdir() if f.endswith(".py") and f != "scripts/generate_readme.py"]
    )

    if py_files:
        readme.append("## 📁 Python Modules")
        readme.append("")
        for file in py_files:
            doc = extract_docstring(file)
            readme.append(f"### `{file}`")
            readme.append("")
            readme.append(doc)
            readme.append("")

    # Add dependencies section
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    readme.append("## 📦 Dependencies")
    readme.append("")

    if req_path.exists():
        with open(req_path, "r", encoding="utf-8") as f:
            deps = [line.strip() for line in f if line.strip()]
        if deps:
            for dep in deps:
                readme.append(f"- {dep}")
        else:
            readme.append("_No dependencies listed._")
    else:
        readme.append("_No requirements.txt file found._")

    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 👨‍💻 Author")
    readme.append("")
    readme.append("**Flavia Ferreira**")
    readme.append("- GitHub: [@youngpada1](https://github.com/youngpada1)")
    readme.append("- Email: flavsferr@gmail.com")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("**Built with ❤️ using Python, Terraform, Snowflake, and AWS**")
    readme.append("")
    readme.append("_README auto-generated via GitHub Actions_")

    Path("README.md").write_text("\n".join(readme), encoding="utf-8")
    print("README.md generated successfully.")

if __name__ == "__main__":
    generate_readme()
