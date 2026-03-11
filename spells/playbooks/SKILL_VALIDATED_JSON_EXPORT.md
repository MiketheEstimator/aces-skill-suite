---
name: validated-json-export
description: "Use this skill when producing .json output files. Covers schema definition, validation, pretty-printing, minification, nested structures, and JSON Lines format. Trigger on any JSON export, API response format, config file, or structured data interchange task."
---

# Validated JSON Export SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Produce JSON | Python `json` stdlib |
| Validate against schema | `jsonschema` |
| Pretty-print | `json.dumps(indent=2)` |
| Minify | `json.dumps(separators=(',',':'))` |
| JSON Lines (JSONL) | One object per line, no wrapping array |
| Large file streaming | `ijson` |

---

## Standard JSON Export

```python
import json
from datetime import date, datetime
from decimal import Decimal

# Custom encoder for non-serializable types
class ExtendedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

data = {
    "project": "Main Tower",
    "date": date(2024, 3, 15),
    "cost": Decimal("1250000.00"),
    "phases": [
        {"id": 1, "name": "Foundation", "complete": True},
        {"id": 2, "name": "Structure", "complete": False}
    ]
}

# Pretty (human-readable)
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False, cls=ExtendedEncoder)

# Minified (production/transfer)
with open("output.min.json", "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(',', ':'), cls=ExtendedEncoder)
```

---

## JSON Schema Definition

```python
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Project Export",
    "type": "object",
    "required": ["project", "date", "phases"],
    "properties": {
        "project": {"type": "string", "minLength": 1},
        "date": {"type": "string", "format": "date"},
        "cost": {"type": "number", "minimum": 0},
        "phases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "complete": {"type": "boolean"}
                }
            }
        }
    }
}
```

---

## Validation

```python
# pip install jsonschema --break-system-packages
import jsonschema

def validate_json(data, schema):
    try:
        jsonschema.validate(instance=data, schema=schema)
        print("✓ Valid")
        return True
    except jsonschema.ValidationError as e:
        print(f"✗ Validation error: {e.message}")
        print(f"  Path: {' → '.join(str(p) for p in e.path)}")
        return False
    except jsonschema.SchemaError as e:
        print(f"✗ Schema error: {e.message}")
        return False
```

---

## JSON Lines Format (JSONL)

```python
# One JSON object per line — ideal for streaming, logs, large datasets
records = [
    {"id": 1, "event": "login", "user": "alice"},
    {"id": 2, "event": "upload", "user": "bob"},
]

with open("output.jsonl", "w", encoding="utf-8") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# Reading JSONL
with open("output.jsonl", "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]
```

---

## CLI Verification

```bash
# Validate JSON syntax
python -m json.tool output.json > /dev/null && echo "Valid JSON" || echo "INVALID"

# Pretty-print and inspect
python -m json.tool output.json | head -40

# Check structure with jq (if available)
jq 'keys' output.json
jq '.phases | length' output.json
jq '.phases[] | select(.complete == false)' output.json

# Count top-level keys
python -c "
import json
with open('output.json') as f:
    d = json.load(f)
print('Keys:', list(d.keys()))
print('Type:', type(d).__name__)
"

# File size check
wc -c output.json
```

---

## QA Checklist

- [ ] File parses without error (`python -m json.tool`)
- [ ] Required fields all present
- [ ] Data types correct (numbers not strings, booleans not 0/1)
- [ ] Dates in ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`)
- [ ] No `NaN`, `Infinity`, or `-Infinity` (not valid JSON)
- [ ] `null` used (not Python `None` string)
- [ ] `ensure_ascii=False` set (preserves Unicode characters)
- [ ] No trailing commas (not valid JSON)
- [ ] Encoding is UTF-8

---

## Common Mistakes to Avoid

- Forgetting `ensure_ascii=False` (escapes all non-ASCII to `\uXXXX`)
- Using Python `None`/`True`/`False` as strings instead of `null`/`true`/`false`
- Serializing `datetime` objects without a custom encoder
- Producing `NaN` from division or missing values (use `None` instead)
- Nested single quotes instead of double quotes (invalid JSON)
- Trailing commas after last array/object element

---

## Dependencies

```bash
pip install jsonschema --break-system-packages
pip install ijson --break-system-packages   # for large file streaming
# json, decimal, datetime: Python stdlib
```
