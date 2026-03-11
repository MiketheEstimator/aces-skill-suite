---
name: SKILL_CONFIG_YAML_VALIDATE
description: "Strict indentation and syntax validation for CI/CD and system configuration. Use when producing .yml or .yaml files for CI/CD pipelines, Kubernetes manifests, Docker Compose, Ansible playbooks, or application config. Triggers: 'YAML', '.yml', '.yaml', 'CI/CD config', 'Kubernetes manifest', 'Ansible playbook', 'GitHub Actions', 'config file'."
---

# SKILL_CONFIG_YAML_VALIDATE — YAML Configuration Skill

## Quick Reference

| Task | Section |
|------|---------|
| Syntax rules & gotchas | [YAML Syntax Rules](#yaml-syntax-rules) |
| Common config templates | [Config Templates](#config-templates) |
| Read / write in Python | [Python Integration](#python-integration) |
| Schema validation | [Schema Validation](#schema-validation) |
| Linting & validation | [Linting & Validation](#linting--validation) |
| QA loop | [Validation & QA](#validation--qa) |

---

## YAML Syntax Rules

### Indentation

```yaml
# YAML uses SPACES only — NEVER tabs
# Standard: 2 spaces per level

parent:
  child:
    grandchild: value    # 2-space indent at each level

# WRONG — tabs cause parse errors:
parent:
	child: value         # TAB — will fail
```

### Scalar Types

```yaml
# Strings
plain: hello world              # no quotes needed for simple strings
quoted: "hello: world"          # quote when string contains : or special chars
single: 'don''t use this'       # single quotes: escape ' with ''
multiline_fold: >               # folded: newlines become spaces
  This is a long
  single line.
multiline_literal: |            # literal: newlines preserved
  Line one.
  Line two.
  Line three.

# Numbers
integer: 42
float: 3.14
negative: -7
scientific: 1.5e10
octal: 0o755                   # file permissions
hex: 0xFF

# Booleans — ONLY these are boolean in YAML 1.2
bool_true:  true
bool_false: false
# WARNING: 'yes', 'no', 'on', 'off' are STRINGS in YAML 1.2
#          but were BOOLEANS in YAML 1.1 — always use true/false

# Null
null_value: null
also_null: ~
empty:                         # empty value = null

# Timestamps
date: 2024-03-15
datetime: 2024-03-15T14:30:00Z
datetime_tz: 2024-03-15T14:30:00+01:00
```

### Collections

```yaml
# Sequence (list) — block style
fruits:
  - apple
  - banana
  - cherry

# Sequence — flow style (inline)
fruits: [apple, banana, cherry]

# Mapping (dict) — block style
person:
  name: Alice
  age: 30
  active: true

# Mapping — flow style
person: {name: Alice, age: 30}

# Nested
servers:
  - name: web-01
    ip: 10.0.0.1
    tags:
      - web
      - prod
  - name: db-01
    ip: 10.0.0.2
    tags:
      - database
```

### Anchors & Aliases (DRY)

```yaml
# Define anchor
defaults: &defaults
  timeout: 30
  retries: 3
  log_level: INFO

# Reuse with alias (inherits all keys from anchor)
development:
  <<: *defaults          # merge key — imports all from defaults
  log_level: DEBUG       # override specific key

production:
  <<: *defaults
  timeout: 60
```

### Quoting Rules

```yaml
# MUST quote these:
colon_in_value: "host:port"         # contains :
starts_with_special: "@admin"       # starts with @, !, &, *, ?, |, -, <, >, =, %
looks_like_bool: "true"             # to force string, not boolean
looks_like_number: "42"             # to force string
empty_string: ""                    # explicit empty string (vs null)
multiline: "line1\nline2"           # escape sequences in double quotes only

# Safe without quotes (simple alphanumeric + hyphens)
safe: hello-world
also_safe: my_variable_name
```

---

## Config Templates

### GitHub Actions Workflow

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: ruff check .

      - name: Test
        run: pytest --tb=short -q

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
  labels:
    app: myapp
    version: "1.0.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myapp:1.0.0
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: myapp-secrets
                  key: database-url
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
```

### Application Config (generic)

```yaml
# config.yaml
app:
  name: "My Application"
  version: "1.0.0"
  environment: production    # development | staging | production
  debug: false

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  timeout: 30

database:
  host: localhost
  port: 5432
  name: mydb
  pool_size: 10
  max_overflow: 5

logging:
  level: INFO                # DEBUG | INFO | WARNING | ERROR
  format: json               # json | text
  output: stdout             # stdout | file
  file:
    path: "/var/log/myapp/app.log"
    max_bytes: 10485760      # 10MB
    backup_count: 5

features:
  feature_a: true
  feature_b: false
  rate_limit:
    enabled: true
    requests_per_minute: 100
```

---

## Python Integration

```python
import yaml
from pathlib import Path

# Read YAML
def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)    # ALWAYS use safe_load, not load()

config = load_config("config.yaml")
print(config["server"]["port"])

# Write YAML
def save_config(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,   # always block style
            allow_unicode=True,
            sort_keys=False,            # preserve insertion order
            indent=2
        )

# Read multiple documents (--- separator)
def load_all(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return list(yaml.safe_load_all(f))

# Render YAML template with variable substitution
def render_template(template_path: str, variables: dict) -> dict:
    template = Path(template_path).read_text(encoding="utf-8")
    for key, value in variables.items():
        template = template.replace(f"${{{key}}}", str(value))
    return yaml.safe_load(template)
```

> ⚠️ **Never use `yaml.load()` without `Loader=yaml.SafeLoader`** — it allows arbitrary code execution. Always use `yaml.safe_load()`.

---

## Schema Validation

### Using jsonschema

```python
import yaml
import jsonschema

# Define schema
schema = {
    "type": "object",
    "required": ["app", "server", "database"],
    "properties": {
        "app": {
            "type": "object",
            "required": ["name", "environment"],
            "properties": {
                "name":        {"type": "string"},
                "environment": {"type": "string",
                                "enum": ["development", "staging", "production"]},
                "debug":       {"type": "boolean"}
            }
        },
        "server": {
            "type": "object",
            "required": ["port"],
            "properties": {
                "port":    {"type": "integer", "minimum": 1, "maximum": 65535},
                "workers": {"type": "integer", "minimum": 1}
            }
        }
    }
}

def validate_config(yaml_path: str) -> bool:
    with open(yaml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    try:
        jsonschema.validate(instance=config, schema=schema)
        print("PASS: Config is valid")
        return True
    except jsonschema.ValidationError as e:
        print(f"FAIL: {e.message} (at {'.'.join(str(p) for p in e.path)})")
        return False
```

### Using Pydantic

```python
from pydantic import BaseModel, Field, validator
from typing import Literal
import yaml

class ServerConfig(BaseModel):
    host:    str     = "0.0.0.0"
    port:    int     = Field(default=8000, ge=1, le=65535)
    workers: int     = Field(default=4, ge=1)
    timeout: int     = 30

class AppConfig(BaseModel):
    name:        str
    environment: Literal["development", "staging", "production"]
    debug:       bool = False
    server:      ServerConfig = ServerConfig()

def load_validated_config(path: str) -> AppConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)

config = load_validated_config("config.yaml")
print(config.server.port)   # type-safe access
```

---

## Linting & Validation

```bash
# Install yamllint
pip install yamllint

# Lint a file
yamllint config.yaml

# Lint all YAML files
yamllint .

# Custom config (.yamllint.yaml)
```

```yaml
# .yamllint.yaml
extends: default

rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  truthy:
    allowed-values: ["true", "false"]   # disallow yes/no/on/off
    check-keys: false
  comments:
    min-spaces-from-content: 2
```

```bash
# Validate Kubernetes manifests
kubectl apply --dry-run=client -f manifest.yaml

# Validate with kubeval
pip install kubeval
kubeval manifest.yaml

# Online / Python-based YAML parse test
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "VALID"
```

---

## Validation & QA

```python
import yaml
from pathlib import Path

def validate_yaml(path: str) -> bool:
    errors = []

    # 1. Parse check
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"PARSE ERROR: {e}")
        return False

    # 2. Not empty
    if data is None:
        errors.append("ERROR: File is empty or null")

    # 3. Check for tab characters (common mistake)
    content = Path(path).read_text(encoding="utf-8")
    for i, line in enumerate(content.splitlines(), 1):
        if "\t" in line:
            errors.append(f"TAB CHARACTER on line {i}: {repr(line)}")

    # 4. Check for trailing whitespace
    trailing = [i for i, l in enumerate(content.splitlines(), 1) if l != l.rstrip()]
    if trailing:
        errors.append(f"TRAILING WHITESPACE on {len(trailing)} lines: {trailing[:5]}")

    if errors:
        for e in errors: print(e)
        return False

    print(f"PASS: {path} is valid YAML")
    return True


validate_yaml("config.yaml")
```

### QA Checklist

- [ ] Spaces only — no tab characters
- [ ] Consistent 2-space indentation throughout
- [ ] Booleans use `true`/`false` (not `yes`/`no`)
- [ ] Strings with `:` or special characters are quoted
- [ ] File parses with `yaml.safe_load()` without error
- [ ] `yamllint` passes with zero errors
- [ ] Schema validated (jsonschema or Pydantic)
- [ ] No hardcoded secrets — use environment variable references
- [ ] File ends with single newline

### QA Loop

1. Write YAML
2. `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"` — parse check
3. `yamllint file.yaml` — style check
4. Schema validate with jsonschema or Pydantic
5. Test in target system (`kubectl apply --dry-run`, etc.)
6. **Do not deploy until parse, lint, and schema validation all pass**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `mapping values are not allowed here` | Unquoted `:` in value | Quote the value: `"host:port"` |
| `found character '\\t'` | Tab used for indentation | Replace all tabs with spaces |
| `True`/`False` instead of `true`/`false` | Python dump default | Use `yaml.dump(..., default_flow_style=False)` |
| Unexpected null | Key with no value | Use `""` for empty string or `null` explicitly |
| List merged incorrectly | `<<:` merge key misused | Ensure anchor is a mapping, not a sequence |
| `yes`/`no` parsed as boolean | YAML 1.1 behaviour | Quote them: `"yes"`, `"no"` — or use yamllint `truthy` rule |

---

## Dependencies

```bash
pip install pyyaml           # Python YAML parser (safe_load)
pip install yamllint         # linting
pip install jsonschema       # schema validation
pip install pydantic         # typed config validation
pip install ruamel.yaml      # round-trip parser (preserves comments)
```
