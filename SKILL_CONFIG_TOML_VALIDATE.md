---
name: SKILL_CONFIG_TOML_VALIDATE
description: "Minimalist config generation for modern package managers and build tools. Use when producing .toml files for pyproject.toml, Cargo.toml, application config, or any TOML-first configuration. Triggers: 'TOML', '.toml', 'pyproject.toml', 'Cargo.toml', 'package config', 'build tool config'."
---

# SKILL_CONFIG_TOML_VALIDATE — TOML Configuration Skill

## Quick Reference

| Task | Section |
|------|---------|
| Syntax rules | [TOML Syntax](#toml-syntax) |
| pyproject.toml templates | [pyproject.toml Templates](#pyprojecttoml-templates) |
| Python read/write | [Python Integration](#python-integration) |
| Validation | [Validation & QA](#validation--qa) |

---

## TOML Syntax

```toml
# Comments use hash

# Strings
name = "My App"
multiline = """
  Line one.
  Line two.
"""
literal = 'C:\Users\no\escaping\needed'    # literal string — no escapes

# Numbers
integer = 42
float   = 3.14
hex     = 0xDEADBEEF
bin     = 0b11010110

# Booleans (lowercase only)
active = true
debug  = false

# Dates & times
date      = 2024-03-15
time      = 14:30:00
datetime  = 2024-03-15T14:30:00Z

# Arrays
tags     = ["alpha", "beta", "production"]
ports    = [8080, 8443]
mixed    = []            # empty array

# Inline tables (one line only)
point = {x = 1, y = 2}

# Standard table (section header)
[server]
host = "0.0.0.0"
port = 8000

[database]
host = "localhost"
port = 5432
name = "mydb"

# Nested tables
[server.tls]
enabled = true
cert    = "/etc/certs/server.crt"

# Array of tables
[[workers]]
name = "worker-1"
queue = "default"

[[workers]]
name = "worker-2"
queue = "priority"
```

---

## pyproject.toml Templates

### Python Package (hatchling)

```toml
[build-system]
requires      = ["hatchling"]
build-backend = "hatchling.build"

[project]
name            = "my-package"
version         = "0.1.0"
description     = "Package description"
readme          = "README.md"
license         = { text = "MIT" }
requires-python = ">=3.10"
keywords        = ["keyword1", "keyword2"]
classifiers     = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]
dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev  = ["pytest>=7.0", "ruff>=0.4", "mypy>=1.0"]
docs = ["mkdocs", "mkdocs-material"]

[project.scripts]
my-tool = "my_package.cli:main"

[project.urls]
Homepage   = "https://github.com/org/my-package"
Repository = "https://github.com/org/my-package"

# ── Tool configs ──────────────────────────────────────────────────────────────

[tool.ruff]
line-length    = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version       = "3.10"
strict               = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths    = ["tests"]
addopts      = "-v --tb=short"
filterwarnings = ["error"]

[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
exclude_lines = ["if TYPE_CHECKING:", "def __repr__"]
```

### Rust Cargo.toml

```toml
[package]
name        = "my-crate"
version     = "0.1.0"
edition     = "2021"
authors     = ["Name <email@example.com>"]
description = "Crate description"
license     = "MIT"
repository  = "https://github.com/org/my-crate"

[dependencies]
serde       = { version = "1.0", features = ["derive"] }
tokio       = { version = "1.0", features = ["full"] }
anyhow      = "1.0"

[dev-dependencies]
assert_cmd = "2.0"

[profile.release]
opt-level = 3
lto       = true
```

---

## Python Integration

```python
import tomllib      # Python 3.11+ stdlib
# or: import tomli as tomllib   (backport for Python 3.10-)

from pathlib import Path

# Read TOML (Python 3.11+)
with open("pyproject.toml", "rb") as f:    # must open as binary
    config = tomllib.load(f)

print(config["project"]["name"])
print(config["project"]["version"])

# Write TOML
pip install tomli-w   # no stdlib writer exists

import tomli_w

config = {
    "app": {
        "name": "My App",
        "port": 8000,
        "debug": False,
        "tags": ["web", "api"]
    }
}

with open("config.toml", "wb") as f:    # binary mode
    tomli_w.dump(config, f)
```

---

## Validation & QA

```bash
# Syntax check (Python)
python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))" && echo "VALID"

# Install taplo (TOML formatter + linter)
brew install taplo              # macOS
cargo install taplo-cli         # from source
# or download binary: https://github.com/tamasfe/taplo

taplo check pyproject.toml      # validate
taplo fmt   pyproject.toml      # format in place
taplo fmt --check pyproject.toml  # format check (CI mode)
```

```python
import tomllib
from pathlib import Path

def validate_toml(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        print(f"PASS: {path} parsed successfully")
        print(f"  Top-level keys: {list(data.keys())}")
        return True
    except tomllib.TOMLDecodeError as e:
        print(f"FAIL: {e}")
        return False

validate_toml("pyproject.toml")
```

### QA Checklist

- [ ] File parses without error (`tomllib.load`)
- [ ] `taplo fmt --check` passes (no formatting diff)
- [ ] All string values use double quotes
- [ ] Booleans use `true`/`false` (lowercase)
- [ ] Dates use ISO 8601 format
- [ ] No duplicate keys in same table
- [ ] `[[array.of.tables]]` used correctly (not `[array.of.tables]`)

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Invalid key` | Duplicate key in same section | Remove duplicate |
| `Expected newline or EOF` | Inline table has trailing comma | Remove trailing comma |
| `tomllib.load` requires binary | Opening file in text mode | Open with `"rb"` not `"r"` |
| Float parse error | `1.` or `.5` not valid | Use `1.0` or `0.5` |
| Multi-line basic string indent | Leading whitespace included | Trim with `\` at start |

---

## Dependencies

```bash
# Python 3.11+ — tomllib is stdlib
import tomllib

# Python 3.10 backport
pip install tomli

# Write TOML
pip install tomli-w

# Lint / format
brew install taplo    # or: cargo install taplo-cli
```
