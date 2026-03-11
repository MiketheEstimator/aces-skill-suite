---
name: structured-txt-export
description: "Use this skill when exporting structured plain text files (.txt). Covers delimited text, fixed-width, log formats, config files, and human-readable reports. Trigger when the user wants a .txt output that must be consistently formatted, parseable, or machine-readable."
---

# Structured .txt Export SKILL

## Quick Reference

| Task | Approach |
|------|----------|
| Delimited text | Define delimiter, header row, escape rules |
| Fixed-width | Define column widths, pad with spaces |
| Log format | Timestamp prefix, severity levels, consistent line structure |
| Config/INI style | `[section]` headers, `key=value` pairs |
| Human report | Heading blocks, separator lines, aligned columns |

---

## Format Patterns

### Delimited Text
```
FIELD1|FIELD2|FIELD3
value1|value2|value3
```
- Prefer `|` over `,` when values may contain commas
- Always include a header row
- Escape delimiter characters within values using quotes or backslash

### Fixed-Width
```
NAME           ROLE            DATE
John Smith     Architect       2024-01-15
Jane Doe       Engineer        2024-03-22
```
- Define column widths explicitly before writing
- Left-align text fields; right-align numeric fields
- Use consistent padding character (space)

### Log Format
```
[2024-01-15 09:32:11] INFO  | Process started
[2024-01-15 09:32:14] WARN  | File not found: config.ini
[2024-01-15 09:32:15] ERROR | Connection timeout
```
- ISO 8601 timestamps always
- Fixed-width severity label (pad to 5 chars)
- Pipe separator between metadata and message

### INI / Config
```ini
[database]
host=localhost
port=5432
name=mydb

[logging]
level=INFO
output=stdout
```

---

## Writing to File (Python)

```python
# Write UTF-8 text file
with open("output.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

# Append to existing
with open("output.txt", "a", encoding="utf-8") as f:
    f.write(new_line + "\n")
```

---

## CLI Verification

```bash
# Check line count
wc -l output.txt

# Check encoding
file output.txt

# Preview first 20 lines
head -n 20 output.txt

# Check for inconsistent line endings
cat -A output.txt | grep -c $'\r'

# Verify delimiter consistency (pipe-delimited example)
awk -F'|' '{print NF}' output.txt | sort | uniq -c
```

---

## QA Checklist

- [ ] Encoding is UTF-8
- [ ] Line endings consistent (LF, not CRLF unless Windows target)
- [ ] Header row present (if tabular)
- [ ] All rows have same column count (if delimited/fixed-width)
- [ ] No unescaped delimiter characters within values
- [ ] No trailing whitespace on lines (unless fixed-width intentional)
- [ ] File ends with a single newline

---

## Common Mistakes to Avoid

- Mixing delimiter types within a file
- Inconsistent column widths in fixed-width output
- Forgetting to escape special characters
- Windows CRLF line endings when Unix target is expected
- Missing trailing newline (breaks some parsers)
- Using tabs without declaring tab as delimiter

---

## Dependencies

- Python 3 (stdlib only — no additional packages required)
- `wc`, `head`, `file`, `awk` (standard Unix tools)
