---
name: SKILL_CODE_IPYNB_AUTOGEN
description: "Cell-based document generation combining Python, markdown, and output metadata. Use when producing .ipynb files for data analysis, research notebooks, reproducible reports, or interactive documentation. Triggers: 'Jupyter notebook', '.ipynb', 'notebook', 'data analysis notebook', 'reproducible report', 'interactive Python'."
---

# SKILL_CODE_IPYNB_AUTOGEN — Jupyter Notebook Skill

## Quick Reference

| Task | Section |
|------|---------|
| Generate .ipynb from Python | [Programmatic Generation](#programmatic-generation) |
| Notebook structure conventions | [Structure Conventions](#structure-conventions) |
| Cell types and metadata | [Cell Types](#cell-types) |
| Parameterisation (Papermill) | [Parameterisation](#parameterisation) |
| Execute & export | [Execution & Export](#execution--export) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Programmatic Generation

### Core: Build .ipynb from Scratch

```python
import json
from pathlib import Path

def new_notebook(python_version: str = "3.10") -> dict:
    """Create an empty notebook structure."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": f"Python {python_version}",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": python_version
            }
        },
        "cells": []
    }

def markdown_cell(source: str) -> dict:
    """Create a markdown cell."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source
    }

def code_cell(source: str, outputs: list = None) -> dict:
    """Create a code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "source": source,
        "outputs": outputs or []
    }

def raw_cell(source: str) -> dict:
    """Create a raw (non-executed) cell."""
    return {
        "cell_type": "raw",
        "metadata": {},
        "source": source
    }

def save_notebook(nb: dict, path: str) -> None:
    Path(path).write_text(
        json.dumps(nb, indent=1, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Saved: {path}")
```

### Full Example: Data Analysis Notebook

```python
from pathlib import Path
import json

nb = new_notebook()

# Title cell
nb["cells"].append(markdown_cell(
    "# Analysis: [Dataset Name]\n\n"
    "**Author:** Name  \n"
    "**Date:** 2024-03-15  \n"
    "**Purpose:** Brief description of what this notebook does.\n\n"
    "---"
))

# Setup cell
nb["cells"].append(code_cell(
    "# Standard imports\n"
    "import pandas as pd\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "from pathlib import Path\n\n"
    "# Display settings\n"
    "pd.set_option('display.max_columns', 50)\n"
    "pd.set_option('display.float_format', '{:.3f}'.format)\n"
    "plt.style.use('seaborn-v0_8')\n"
    "%matplotlib inline\n"
    "\n"
    "print('Libraries loaded.')"
))

# Parameters cell (papermill-compatible)
nb["cells"].append(code_cell(
    "# Parameters (override via Papermill)\n"
    "INPUT_PATH = './data/raw/dataset.csv'\n"
    "OUTPUT_PATH = './data/processed/'\n"
    "DATE_FILTER = '2024-01-01'"
))
# Tag as parameters cell for Papermill
nb["cells"][-1]["metadata"]["tags"] = ["parameters"]

# Data loading
nb["cells"].append(markdown_cell("## 1. Data Loading"))
nb["cells"].append(code_cell(
    "df = pd.read_csv(INPUT_PATH)\n"
    "print(f'Shape: {df.shape}')\n"
    "print(f'Columns: {df.columns.tolist()}')\n"
    "df.head()"
))

# EDA
nb["cells"].append(markdown_cell("## 2. Exploratory Analysis"))
nb["cells"].append(code_cell(
    "df.describe()"
))
nb["cells"].append(code_cell(
    "# Missing values\n"
    "missing = df.isnull().sum()\n"
    "missing[missing > 0].sort_values(ascending=False)"
))

# Visualisation
nb["cells"].append(markdown_cell("## 3. Visualisation"))
nb["cells"].append(code_cell(
    "fig, axes = plt.subplots(1, 2, figsize=(12, 4))\n\n"
    "# Distribution\n"
    "df['value_column'].hist(bins=30, ax=axes[0])\n"
    "axes[0].set_title('Distribution')\n\n"
    "# Time series\n"
    "df.groupby('date')['value_column'].mean().plot(ax=axes[1])\n"
    "axes[1].set_title('Trend')\n\n"
    "plt.tight_layout()\n"
    "plt.savefig('./figures/eda_overview.png', dpi=150, bbox_inches='tight')\n"
    "plt.show()"
))

# Export
nb["cells"].append(markdown_cell("## 4. Export Results"))
nb["cells"].append(code_cell(
    "from pathlib import Path\n\n"
    "out = Path(OUTPUT_PATH)\n"
    "out.mkdir(parents=True, exist_ok=True)\n\n"
    "df_clean.to_csv(out / 'processed_dataset.csv', index=False)\n"
    "print(f'Exported {len(df_clean)} rows to {out}')"
))

save_notebook(nb, "analysis.ipynb")
```

---

## Structure Conventions

### Standard Notebook Layout

```
Notebook structure (top to bottom):
1. Title cell (markdown) — title, author, date, purpose
2. Table of contents (markdown) — for notebooks > 5 sections
3. Imports cell (code) — all imports together, clearly commented
4. Parameters cell (code) — all configurable values, tagged 'parameters'
5. Section H2 headings (markdown) — one per logical step
6. Code cells — one logical unit per cell
7. Inline commentary (markdown between code cells) — explain what/why
8. Results/conclusions cell (markdown) — summary findings
9. Export/save cell (code) — always last code cell
```

### Cell Size Rules

```
- Each code cell: single logical operation (load data, clean, plot, etc.)
- Max ~30 lines per code cell — split if longer
- No long pipelines in one cell — break into labelled steps
- Every output-producing cell should be immediately followed by
  a markdown cell explaining what the output means (for reports)
```

### Naming Convention

```
descriptive_snake_case_topic_YYYYMMDD.ipynb
Examples:
  customer_churn_analysis_20240315.ipynb
  monthly_revenue_report_202403.ipynb
  model_training_baseline_v1.ipynb
```

---

## Cell Types

### Markdown Cell — Heading Hierarchy

```markdown
# Notebook Title (H1 — once, at top)
## Major Section (H2)
### Subsection (H3)
#### Detail (H4 — sparingly)
```

### Code Cell — Output Types

```python
# Text output (stdout)
print("result")

# Rich display — DataFrame
df.head()                    # renders as HTML table in Jupyter

# Rich display — plot
plt.show()                   # renders inline with %matplotlib inline

# Rich display — explicit
from IPython.display import display, Markdown, HTML
display(Markdown("**Bold markdown** inline"))
display(HTML("<b>HTML output</b>"))

# Suppress output for intermediate cells
_ = some_function()          # assign to _ to suppress repr
```

### Injecting Pre-computed Outputs

```python
# Add text output to a cell
text_output = {
    "output_type": "stream",
    "name": "stdout",
    "text": "Shape: (1000, 15)\n"
}

# Add display output (e.g. matplotlib figure as base64)
import base64
with open("figure.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

image_output = {
    "output_type": "display_data",
    "data": {
        "image/png": img_b64,
        "text/plain": "<Figure>"
    },
    "metadata": {}
}

# Attach to code cell
cell = code_cell("plt.show()", outputs=[image_output])
```

---

## Parameterisation

### Papermill Integration

```bash
pip install papermill
```

```python
# In notebook: tag a cell as 'parameters'
# Cell metadata must include: {"tags": ["parameters"]}

# Default parameters (overridden by Papermill at runtime)
INPUT_FILE = "data.csv"
START_DATE = "2024-01-01"
END_DATE   = "2024-12-31"
REPORT_TITLE = "Monthly Report"
```

```bash
# Execute notebook with parameter overrides
papermill template.ipynb output_march.ipynb \
  -p INPUT_FILE "march_data.csv" \
  -p START_DATE "2024-03-01" \
  -p END_DATE "2024-03-31" \
  -p REPORT_TITLE "March 2024 Report"

# Batch execution
for month in 01 02 03 04 05 06; do
  papermill template.ipynb "reports/report_2024${month}.ipynb" \
    -p INPUT_FILE "data_2024${month}.csv" \
    -p REPORT_TITLE "Report 2024-${month}"
done
```

```python
# Python batch execution
import papermill as pm
from pathlib import Path

months = ["202401", "202402", "202403"]

for month in months:
    pm.execute_notebook(
        "template.ipynb",
        f"output/report_{month}.ipynb",
        parameters={
            "INPUT_FILE": f"data_{month}.csv",
            "REPORT_TITLE": f"Report {month}"
        }
    )
    print(f"Completed: {month}")
```

---

## Execution & Export

### Execute Notebook (nbconvert)

```bash
# Execute in place
jupyter nbconvert --to notebook --execute analysis.ipynb \
  --output analysis_executed.ipynb

# With timeout (seconds per cell)
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=120 analysis.ipynb \
  --output analysis_executed.ipynb

# Execute and clear outputs first
jupyter nbconvert --to notebook --execute \
  --ClearOutputPreprocessor.enabled=True \
  analysis.ipynb --output analysis_executed.ipynb
```

### Export to Other Formats

```bash
# HTML report (with embedded outputs)
jupyter nbconvert --to html analysis.ipynb
jupyter nbconvert --to html --no-input analysis.ipynb   # hide code cells

# PDF (requires LaTeX)
jupyter nbconvert --to pdf analysis.ipynb

# Python script (strips markdown, keeps code)
jupyter nbconvert --to script analysis.ipynb

# Markdown (for documentation sites)
jupyter nbconvert --to markdown analysis.ipynb

# Slides (Reveal.js)
jupyter nbconvert --to slides analysis.ipynb --post serve
```

### Strip Outputs Before Committing

```bash
pip install nbstripout

# Strip outputs from a single notebook
nbstripout analysis.ipynb

# Install as git filter (auto-strips on commit)
nbstripout --install

# Check what would be stripped
nbstripout --dry-run analysis.ipynb
```

---

## Validation & QA

```bash
pip install nbqa nbconvert nbstripout

# Check syntax (try to import cells as Python)
jupyter nbconvert --to script analysis.ipynb --stdout | python3 -c "import sys; compile(sys.stdin.read(), '<notebook>', 'exec')"

# Lint cells with ruff via nbqa
nbqa ruff analysis.ipynb
nbqa ruff --fix analysis.ipynb

# Check all cells execute without error
jupyter nbconvert --to notebook --execute analysis.ipynb \
  --ExecutePreprocessor.timeout=300 \
  --output /tmp/test_output.ipynb
echo "Exit code: $?"
```

```python
import json
from pathlib import Path

def validate_notebook(nb_path: str) -> bool:
    errors = []

    with open(nb_path, encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb.get("cells", [])
    code_cells = [c for c in cells if c["cell_type"] == "code"]
    md_cells   = [c for c in cells if c["cell_type"] == "markdown"]

    # Check nbformat
    if nb.get("nbformat") != 4:
        errors.append(f"WARNING: nbformat is {nb.get('nbformat')}, expected 4")

    # Check first cell is markdown (title)
    if cells and cells[0]["cell_type"] != "markdown":
        errors.append("WARNING: First cell should be a markdown title cell")

    # Check for parameters cell
    param_cells = [c for c in code_cells
                   if "parameters" in c.get("metadata", {}).get("tags", [])]
    if not param_cells:
        errors.append("INFO: No parameters cell found (add if using Papermill)")

    # Check for empty code cells
    empty = [i for i, c in enumerate(code_cells)
             if not "".join(c.get("source", "")).strip()]
    if empty:
        errors.append(f"WARNING: {len(empty)} empty code cells found")

    print(f"Total cells: {len(cells)}  "
          f"Code: {len(code_cells)}  "
          f"Markdown: {len(md_cells)}")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Notebook structure is valid")
    return True


validate_notebook("analysis.ipynb")
```

### QA Checklist

- [ ] First cell is a markdown title with author and date
- [ ] Imports are in a single, clearly-labelled cell
- [ ] Parameters cell is tagged `parameters`
- [ ] No cell is longer than ~30 lines
- [ ] All sections have markdown headings (H2+)
- [ ] Notebook executes top-to-bottom without error
- [ ] No hardcoded absolute paths
- [ ] Outputs stripped before committing to version control (`nbstripout`)
- [ ] `nbqa ruff` passes with zero errors
- [ ] Figures saved to file (not only displayed inline)

### QA Loop

1. Write notebook
2. Restart kernel and run all cells top-to-bottom
3. Verify all outputs are correct
4. Run `nbqa ruff --fix` — lint code cells
5. Run `nbstripout` — strip outputs before committing
6. Run `validate_notebook()` — structural check
7. **Do not commit with stale outputs or execution errors**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Wrong kernel/venv | Select correct kernel in Jupyter |
| Outputs out of date | Not re-run after code changes | Restart kernel & run all |
| Notebook too large for git | Embedded image outputs | Use `nbstripout --install` git filter |
| `KeyError` in cell | Variable from earlier cell not run | Always run top-to-bottom; use Restart & Run All |
| Papermill parameter not applied | Cell not tagged `parameters` | Add `{"tags": ["parameters"]}` to cell metadata |
| PDF export fails | LaTeX not installed | `sudo apt install texlive-xetex` |

---

## Dependencies

```bash
pip install jupyter nbconvert nbstripout papermill nbqa ruff

# Kernel registration
python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

# Common analysis packages
pip install pandas numpy matplotlib seaborn plotly scipy
```
