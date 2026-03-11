---
name: SKILL_SPREADSHEET_TSV_EXPORT
description: "Tab-delimited data export, explicitly bypassing CSV comma-escaping issues. Use when producing .tsv files for data interchange where commas in data cause CSV parsing problems, bioinformatics pipelines, or systems expecting tab-delimited input. Triggers: 'TSV', '.tsv', 'tab-delimited', 'tab separated', 'avoid CSV escaping'."
---

# SKILL_SPREADSHEET_TSV_EXPORT — TSV Export Skill

## Quick Reference

| Task | Section |
|------|---------|
| Write TSV | [Writing TSV](#writing-tsv) |
| Read TSV | [Reading TSV](#reading-tsv) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Why TSV Over CSV

| Issue | CSV | TSV |
|-------|-----|-----|
| Commas in data | Requires quoting: `"value, with, commas"` | No issue |
| Newlines in data | Complex escaping required | Still requires care |
| Numbers formatted as `1,000` | Breaks parsing | No issue |
| Address fields | `"123 Main St, Apt 4"` | `123 Main St, Apt 4` |
| Financial data | `"$1,234.56"` | `$1,234.56` |

**Use TSV when:** Data fields contain commas, currency, addresses, or prose text.
**Use CSV when:** Recipient system only accepts CSV and data is clean.

---

## Writing TSV

### Python (csv module)

```python
import csv
from pathlib import Path

def write_tsv(rows: list[dict], output_path: str,
              fieldnames: list = None) -> None:
    """
    Write list of dicts to TSV file.
    
    Tabs within field values are replaced with spaces automatically.
    """
    if not rows:
        return

    fields = fieldnames or list(rows[0].keys())

    # Sanitise: replace tabs in values to prevent broken rows
    clean_rows = []
    for row in rows:
        clean = {k: str(v).replace("\t", " ").replace("\n", " ")
                 if v is not None else ""
                 for k, v in row.items()}
        clean_rows.append(clean)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(clean_rows)

    print(f"Written: {len(clean_rows)} rows → {output_path}")


# Example
data = [
    {"id": 1, "description": "Steel beam, 6m", "cost": "$1,250.00", "qty": 10},
    {"id": 2, "description": "Concrete mix (30MPa)", "cost": "$85.50",  "qty": 500},
]
write_tsv(data, "materials.tsv")
```

### Pandas

```python
import pandas as pd

df = pd.DataFrame(data)

# Write TSV
df.to_csv("output.tsv", sep="\t", index=False, encoding="utf-8")

# With quoting disabled (pure tab-delimited, no quotes)
df.to_csv("output.tsv", sep="\t", index=False,
          quoting=csv.QUOTE_NONE, escapechar="\\")
```

---

## Reading TSV

```python
import csv

# Read to list of dicts
with open("data.tsv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    rows = list(reader)

# Pandas
import pandas as pd
df = pd.read_csv("data.tsv", sep="\t", encoding="utf-8")
```

---

## Validation & QA

```python
def validate_tsv(path: str, expected_columns: list = None) -> bool:
    errors = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        headers = next(reader)
        rows = list(reader)

    print(f"Columns: {len(headers)}  Rows: {len(rows)}")

    if expected_columns:
        missing = set(expected_columns) - set(headers)
        if missing:
            errors.append(f"MISSING COLUMNS: {missing}")

    # Check consistent column count
    bad_rows = [i+2 for i, r in enumerate(rows) if len(r) != len(headers)]
    if bad_rows:
        errors.append(f"COLUMN COUNT MISMATCH on rows: {bad_rows[:10]}")

    if errors:
        for e in errors: print(e)
        return False
    print("PASS: TSV is valid")
    return True
```

### QA Checklist

- [ ] No literal tab characters within field values (sanitised)
- [ ] Header row present
- [ ] Consistent column count across all rows
- [ ] UTF-8 encoding
- [ ] No trailing tab on each line
- [ ] File ends with newline

---

## Dependencies

```bash
import csv        # Python stdlib
pip install pandas   # optional
```
