import os
import subprocess
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

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
        "│              MODERN DATA ENGINEERING ARCHITECTURE (ELT)              │",
        "└─────────────────────────────────────────────────────────────────────┘",
        "",
        "1️⃣ DATA INGESTION (Extract & Load)",
        "   ┌──────────────┐",
        "   │  OpenF1 API  │  ← Real-time F1 data (REST API)",
        "   └──────┬───────┘",
        "          │",
        "          ↓ httpx",
        "   ┌──────────────┐",
        "   │ extract.py   │  ← Python ETL script",
        "   │ load.py      │  ← Loads to Snowflake RAW schema",
        "   │ (httpx)      │  ← Async HTTP client",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "2️⃣ DATA WAREHOUSE (Snowflake)",
        "   ┌────────────────────────────────────────┐",
        "   │         APEXML_DEV Database            │",
        "   ├────────────────────────────────────────┤",
        "   │  📁 RAW Schema                         │",
        "   │    • sessions   (raw API data)         │",
        "   │    • drivers    (raw API data)         │",
        "   │    • positions  (raw API data)         │",
        "   │    • laps       (raw API data)         │",
        "   ├────────────────────────────────────────┤",
        "   │           ↓ dbt transformations        │",
        "   ├────────────────────────────────────────┤",
        "   │  📁 STAGING Schema (views)             │",
        "   │    • stg_sessions   (cleaned)          │",
        "   │    • stg_drivers    (deduplicated)     │",
        "   │    • stg_laps       (validated)        │",
        "   │    • stg_positions  (filtered)         │",
        "   ├────────────────────────────────────────┤",
        "   │           ↓ dbt transformations        │",
        "   ├────────────────────────────────────────┤",
        "   │  📁 ANALYTICS Schema (tables)          │",
        "   │    • dim_drivers        (dimension)    │",
        "   │    • fct_lap_times      (fact)         │",
        "   │    • fct_race_results   (fact)         │",
        "   └────────┬───────────────────────────────┘",
        "            │",
        "            ↓",
        "3️⃣ TRANSFORMATION (dbt)",
        "   ┌──────────────┐",
        "   │  dbt Core    │  ← SQL-based transformations",
        "   │              │  ← Data quality tests",
        "   │  • Models    │  ← RAW → STAGING → ANALYTICS",
        "   │  • Tests     │  ← not_null, unique, custom",
        "   │  • Docs      │  ← Auto-generated lineage",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "4️⃣ ANALYTICS & ML",
        "   ┌──────────────┐",
        "   │  ML Model    │  ← Trained on ANALYTICS schema",
        "   │  (sklearn)   │  ← Predicts race winners",
        "   └──────┬───────┘",
        "          │",
        "          ↓",
        "5️⃣ VISUALIZATION",
        "   ┌──────────────┐",
        "   │  Streamlit   │  ← Interactive dashboard",
        "   │  Dashboard   │  ← Queries ANALYTICS schema",
        "   │              │",
        "   │  Features:   │",
        "   │  • Real-time │  ← Live race data",
        "   │  • Historical│  ← Trends & analytics",
        "   │  • Predictions│ ← ML-powered insights",
        "   └──────────────┘",
        "          │",
        "          ↓",
        "6️⃣ INFRASTRUCTURE",
        "   ┌──────────────┐",
        "   │  AWS EC2     │  ← Docker container",
        "   │  (t3.micro)  │  ← Hosts Streamlit app",
        "   └──────────────┘",
        "",
        "7️⃣ CI/CD & IaC",
        "   ┌──────────────┐",
        "   │  Terraform   │  ← Infrastructure as Code (IaC)",
        "   │              │  ← Snowflake + AWS resources",
        "   │              │  ← Multi-environment (dev/staging/prod)",
        "   └──────────────┘",
        "   ┌──────────────┐",
        "   │  GitHub      │  ← CI/CD pipelines",
        "   │  Actions     │  ← Automated ETL + dbt runs",
        "   └──────────────┘",
        "```",
        "",
        "---",
        "",
        "## 🛠️ Tech Stack",
        "",
        "**Data Ingestion:** OpenF1 API, Python 3.11+, httpx, snowflake-connector-python",
        "**Transformation:** dbt Core, dbt-snowflake (SQL-based ELT)",
        "**Data Warehouse:** Snowflake (RAW → STAGING → ANALYTICS schemas)",
        "**Machine Learning:** scikit-learn (Random Forest Classifier)",
        "**Visualization:** Streamlit, Altair, Plotly",
        "**Infrastructure:** Terraform (IaC), AWS EC2, Docker",
        "**Package Manager:** uv (fast Python package manager)",
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

    # Add dependencies section - show ALL installed packages
    readme.append("## 📦 Dependencies")
    readme.append("")
    readme.append("Managed with **uv** package manager")
    readme.append("")

    try:
        # Get all installed packages from uv pip list
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

            if package_lines:
                readme.append(f"**Total packages installed: {len(package_lines)}**")
                readme.append("")
                readme.append("<details>")
                readme.append("<summary>View all packages</summary>")
                readme.append("")
                readme.append("```")
                for line in package_lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        readme.append(f"{parts[0]:<30} {parts[1]}")
                readme.append("```")
                readme.append("")
                readme.append("</details>")
            else:
                readme.append("_No packages found._")
        else:
            readme.append("_Could not retrieve package list._")
    except Exception as e:
        readme.append(f"_Error retrieving packages: {e}_")
        readme.append("")
        readme.append("**Note:** Using pyproject.toml as fallback")

        # Fallback to pyproject.toml
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    pyproject = tomllib.load(f)
                deps = pyproject.get("project", {}).get("dependencies", [])
                if deps:
                    for dep in deps:
                        readme.append(f"- {dep}")
            except Exception:
                pass

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
