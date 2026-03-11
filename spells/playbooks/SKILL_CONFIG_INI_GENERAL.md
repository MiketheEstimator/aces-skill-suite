---
name: SKILL_CONFIG_INI_GENERAL
description: "Legacy section-based configuration file read/write operations. Use when producing .ini, .cfg, or .conf files for application configuration, Python setup files, or any INI-format config. Triggers: 'INI file', '.ini', '.cfg', 'config file', 'setup.cfg', 'configparser', 'section-based config'."
---

# SKILL_CONFIG_INI_GENERAL — INI Configuration Skill

## Quick Reference

| Task | Section |
|------|---------|
| INI syntax rules | [INI Syntax](#ini-syntax) |
| Common templates | [Config Templates](#config-templates) |
| Python read/write | [Python Integration](#python-integration) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## INI Syntax

```ini
; Comments use semicolons
# Hash comments also work in most parsers

; Global keys (before any section) — not supported by all parsers
global_key = value

[section_name]
key = value
another_key = another value
integer_key = 42
float_key = 3.14
boolean_key = true           ; true/false, yes/no, on/off, 1/0 all valid
empty_key =                  ; empty string value

[database]
host = localhost
port = 5432
name = mydb
; Multiline values (indent continuation lines)
connection_string = postgresql://user:pass@localhost:5432/mydb
    ?sslmode=require
    &connect_timeout=10

[section.nested]             ; use dots to imply hierarchy (convention only)
key = value

; Interpolation (configparser default: BasicInterpolation)
[paths]
base_dir = /opt/myapp
log_dir  = %(base_dir)s/logs      ; %(key)s syntax for variable reference
data_dir = %(base_dir)s/data
```

### Key Formatting Conventions

```ini
; Both = and : are valid delimiters
key = value
key: value

; Keys are case-insensitive in configparser (lowercased on read)
MyKey = value       ; read back as 'mykey'

; No spaces in section names (use underscores or hyphens)
[my_section]        ; good
[my section]        ; valid but avoid
```

---

## Config Templates

### Application Config

```ini
; app.ini — Application Configuration

[app]
name        = My Application
version     = 1.0.0
environment = production
debug       = false
secret_key  = %(SECRET_KEY)s     ; reference env var via interpolation

[server]
host    = 0.0.0.0
port    = 8000
workers = 4
timeout = 30

[database]
host         = localhost
port         = 5432
name         = mydb
user         = appuser
password     = %(DB_PASSWORD)s
pool_size    = 10
max_overflow = 5

[logging]
level   = INFO
format  = %(asctime)s [%(levelname)s] %(message)s
file    = /var/log/myapp/app.log

[cache]
backend = redis
host    = localhost
port    = 6379
ttl     = 3600
```

### Python setup.cfg

```ini
[metadata]
name             = my-package
version          = 0.1.0
description      = Package description
long_description = file: README.md
long_description_content_type = text/markdown
author           = Author Name
author_email     = author@example.com
license          = MIT
classifiers      =
    Development Status :: 3 - Alpha
    Programming Language :: Python :: 3
    License :: OSI Approved :: MIT License
python_requires  = >=3.10

[options]
packages         = find:
package_dir      = =src
install_requires =
    requests>=2.31.0
    click>=8.1.0

[options.packages.find]
where = src

[options.entry_points]
console_scripts =
    my-tool = my_package.cli:main

[tool:pytest]
testpaths = tests
addopts   = -v --tb=short

[flake8]
max-line-length = 100
extend-ignore   = E203, W503
exclude         =
    .git,
    __pycache__,
    build,
    dist
```

### Git Config Format (.gitconfig style)

```ini
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    autocrlf = input

[remote "origin"]
    url = https://github.com/org/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*

[branch "main"]
    remote = origin
    merge = refs/heads/main
```

---

## Python Integration

```python
import configparser
from pathlib import Path

# ── Read ──────────────────────────────────────────────────────────────────────

def load_config(path: str) -> configparser.ConfigParser:
    """Load INI config with sensible defaults."""
    config = configparser.ConfigParser(
        interpolation=configparser.BasicInterpolation(),
        default_section="DEFAULT",       # keys shared across all sections
        inline_comment_prefixes=(";", "#"),
        strict=True                       # raise on duplicate keys
    )
    config.read(path, encoding="utf-8")
    return config

config = load_config("app.ini")

# Access values
host = config["database"]["host"]               # string
port = config.getint("database", "port")        # int
debug = config.getboolean("app", "debug")       # bool
timeout = config.getfloat("server", "timeout")  # float

# Default fallback
level = config.get("logging", "level", fallback="INFO")

# List all sections
print(config.sections())    # excludes DEFAULT

# Check key existence
if config.has_option("cache", "backend"):
    backend = config["cache"]["backend"]

# Iterate section
for key, value in config["server"].items():
    print(f"{key} = {value}")
```

### Write INI

```python
import configparser

config = configparser.ConfigParser()

config["DEFAULT"] = {
    "log_level": "INFO",
    "timeout":   "30"
}

config["app"] = {
    "name":        "My Application",
    "environment": "production",
    "debug":       "false"
}

config["database"] = {
    "host":      "localhost",
    "port":      "5432",
    "name":      "mydb"
}

config["server"] = {
    "host":    "0.0.0.0",
    "port":    "8000",
    "timeout": "%(timeout)s"    # reference DEFAULT key
}

with open("app.ini", "w", encoding="utf-8") as f:
    config.write(f)
```

### Environment Variable Overrides

```python
import configparser
import os

class EnvConfigParser(configparser.ConfigParser):
    """ConfigParser that falls back to environment variables."""

    def get(self, section, option, *, fallback=configparser._UNSET, **kwargs):
        # Check env var first: SECTION__OPTION (uppercase, double underscore)
        env_key = f"{section}__{option}".upper()
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val
        return super().get(section, option, fallback=fallback, **kwargs)

config = EnvConfigParser()
config.read("app.ini")

# DB_HOST env var will override [database] host key
host = config.get("database", "host")
```

---

## Validation & QA

```python
import configparser
from pathlib import Path

def validate_ini(path: str, required_sections: list = None,
                 required_keys: dict = None) -> bool:
    """
    Validate an INI file.

    required_sections: ["database", "server"]
    required_keys: {"database": ["host", "port"], "server": ["port"]}
    """
    errors = []

    # 1. Parse check
    try:
        config = configparser.ConfigParser(strict=True)
        config.read(path, encoding="utf-8")
    except configparser.Error as e:
        print(f"PARSE ERROR: {e}")
        return False

    sections = config.sections()
    print(f"Sections: {sections}")

    # 2. Required sections
    if required_sections:
        for section in required_sections:
            if not config.has_section(section):
                errors.append(f"MISSING SECTION: [{section}]")

    # 3. Required keys
    if required_keys:
        for section, keys in required_keys.items():
            for key in keys:
                if not config.has_option(section, key):
                    errors.append(f"MISSING KEY: [{section}] {key}")

    # 4. Check for empty required values
    for section in sections:
        for key, value in config[section].items():
            if value.strip() == "" and not key.startswith(";"):
                errors.append(f"EMPTY VALUE: [{section}] {key}")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Config is valid")
    return True


validate_ini(
    "app.ini",
    required_sections=["app", "database", "server"],
    required_keys={"database": ["host", "port", "name"]}
)
```

### QA Checklist

- [ ] File parses without `configparser.Error`
- [ ] All required sections present
- [ ] All required keys present and non-empty
- [ ] No duplicate sections or keys (`strict=True`)
- [ ] Interpolation references (`%(key)s`) resolve correctly
- [ ] Sensitive values (passwords, keys) use environment variable references
- [ ] File ends with newline
- [ ] Consistent delimiter style (`=` throughout)

### QA Loop

1. Write INI file
2. Parse with `configparser.ConfigParser(strict=True)` — catches duplicates
3. Run `validate_ini()` — required sections and keys
4. Test interpolation: `config.get(section, key)` on all `%(...)s` references
5. **Do not ship until all required keys resolve without error**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `MissingSectionHeaderError` | Keys before any `[section]` | Move to `[DEFAULT]` or add section header |
| `InterpolationSyntaxError` | Bare `%` in value | Escape as `%%` |
| `DuplicateSectionError` | Same section name twice | Merge or rename sections; use `strict=True` to detect |
| Key lowercased unexpectedly | configparser lowercases keys by default | Use `optionxform = str` to preserve case |
| Multiline value not parsed | Continuation line not indented | Indent continuation with at least one space |
| Boolean `"true"` not parsed | Using `config[s][k]` not `getboolean()` | Use `config.getboolean(section, key)` |

```python
# Preserve key case (override default lowercasing)
config = configparser.ConfigParser()
config.optionxform = str    # prevents key lowercasing
```

---

## Dependencies

```bash
# Python stdlib — no install needed
import configparser

# Enhanced INI parsing
pip install configobj     # more powerful INI parser with validation
```
