---
name: structured-csv-export
description: "Use this skill when producing .csv files. Covers clean tabular exports, multi-encoding support, dialect handling, large file generation, and validation. Trigger on any request for a .csv output, data table export, or spreadsheet-compatible flat file."
---

# Structured CSV Export SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Simple export | Python `csv` stdlib |
| DataFrame export | `pandas` |
| Large file (streaming) | `csv.writer` with chunking |
| Validate structure | `csvkit` CLI |
| Profile data | `pandas` describe |

---

## Standard CSV Export (Python stdlib)

```python
import csv

headers = ['ID', 'Name', 'Date', 'Value']
rows = [
    [1, 'Alpha Project', '2024-01-15', 125000],
    [2, 'Beta Phase', '2024-03-01', 87500],
]

with open('output.csv', 'w', newline='', encoding='utf-8-sig') as f:
    # utf-8-sig adds BOM — required for correct Excel opening
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)
```

---

## Pandas Export

```python
import pandas as pd

df = pd.DataFrame(data)

# Standard
df.to_csv('output.csv', index=False, encoding='utf-8-sig')

# Custom delimiter (TSV)
df.to_csv('output.tsv', sep='\t', index=False)

# Specific columns only
df[['col_a', 'col_b', 'col_c']].to_csv('subset.csv', index=False)

# Format floats
df.to_csv('output.csv', index=False, float_format='%.2f')

# Date format
df.to_csv('output.csv', index=False, date_format='%Y-%m-%d')
```

---

## Encoding Guide

| Encoding | Use When |
|----------|----------|
| `utf-8-sig` | Default — Excel-safe UTF-8 with BOM |
| `utf-8` | Linux/Mac pipelines, no Excel |
| `cp1252` | Legacy Windows systems |
| `latin-1` | Legacy European systems |

---

## Dialect Handling

```python
# Excel dialect (default comma, CRLF)
writer = csv.writer(f, dialect='excel')

# Unix dialect (LF line endings)
writer = csv.writer(f, dialect='unix')

# Custom dialect
csv.register_dialect('pipe_delimited',
    delimiter='|',
    quoting=csv.QUOTE_ALL,
    lineterminator='\n'
)
writer = csv.writer(f, dialect='pipe_delimited')
```

---

## Large File Streaming

```python
# Stream large datasets without loading all into memory
def stream_csv(output_path, data_generator, headers):
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for chunk in data_generator:
            writer.writerows(chunk)
```

---

## CLI Validation

```bash
# Install csvkit
pip install csvkit --break-system-packages

# Validate and show stats
csvstat output.csv

# Check structure
csvlook output.csv | head -20

# Count rows and columns
csvstat --count output.csv
python -c "
import csv
with open('output.csv') as f:
    reader = csv.reader(f)
    rows = list(reader)
print(f'Rows: {len(rows)-1}, Cols: {len(rows[0])}')
"

# Check for encoding issues
file output.csv
python -c "
with open('output.csv', encoding='utf-8-sig') as f:
    f.read()
print('Encoding OK')
"
```

---

## QA Checklist

- [ ] Header row present and correctly named
- [ ] All rows have same column count
- [ ] No unescaped commas within fields (or fields properly quoted)
- [ ] Encoding is `utf-8-sig` for Excel compatibility
- [ ] Dates in consistent format (ISO 8601: `YYYY-MM-DD`)
- [ ] Numeric fields contain no currency symbols or commas (unless intentional text)
- [ ] No blank rows mid-file
- [ ] File ends with newline
- [ ] No leading/trailing whitespace in header names

---

## Common Mistakes to Avoid

- Using plain `utf-8` (Excel shows garbled characters without BOM)
- Forgetting `newline=''` in `open()` (causes double line breaks on Windows)
- Including row index from pandas (`index=False` required)
- Mixing date formats within a column
- Embedding newlines in field values without proper quoting
- Leaving `None` values instead of empty strings or `0`

---

## Dependencies

```bash
pip install pandas --break-system-packages
pip install csvkit --break-system-packages
# csv module: Python stdlib (no install needed)
```
