# generate_readme.py

import os
import importlib.util
from pathlib import Path

def extract_docstring(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                return line.strip().strip('"""').strip("'''")
    return "No module docstring found."

def generate_readme():
    project_name = Path.cwd().name
    files = [f for f in os.listdir() if f.endswith('.py') and f != 'generate_readme.py']

    readme_lines = [
        f"# {project_name}\n",
        f"Auto-generated README for **{project_name}**.\n",
        "## 🧠 Project Overview\n",
        "This project was automatically documented by reading Python source files.\n",
        "## 📦 Python Modules\n"
    ]

    for file in files:
        doc = extract_docstring(file)
        readme_lines.append(f"### `{file}`\n")
        readme_lines.append(f"{doc}\n\n")

    if os.path.exists("requirements.txt"):
        readme_lines.append("## 📚 Dependencies\n")
        with open("requirements.txt", "r") as reqs:
            deps = reqs.readlines()
            for dep in deps:
                readme_lines.append(f"- {dep.strip()}\n")

    readme_lines.append("\n---\n*README auto-generated via GitHub Actions.*\n")

    with open("README.md", "w") as f:
        f.writelines(readme_lines)

if __name__ == "__main__":
    generate_readme()
