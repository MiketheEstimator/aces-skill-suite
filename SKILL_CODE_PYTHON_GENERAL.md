---
name: SKILL_CODE_PYTHON_GENERAL
description: "Standard executable logic and automation script generation. Use when producing .py files for scripts, utilities, automation, data processing, or any Python-first deliverable. Triggers: 'Python script', '.py file', 'write a script', 'automate', 'CLI tool', 'utility script', 'batch process'."
---

# SKILL_CODE_PYTHON_GENERAL — Python Script Skill

## Quick Reference

| Task | Section |
|------|---------|
| Script templates | [Script Templates](#script-templates) |
| CLI argument parsing | [CLI with argparse](#cli-with-argparse) |
| Error handling patterns | [Error Handling](#error-handling) |
| Logging | [Logging](#logging) |
| File I/O patterns | [File I/O](#file-io) |
| Packaging & dependencies | [Packaging](#packaging) |
| Linting & formatting | [Linting & Formatting](#linting--formatting) |
| QA loop | [Validation & QA](#validation--qa) |

---

## Script Templates

### Minimal Executable Script

```python
#!/usr/bin/env python3
"""
Module docstring: one-line summary.

Extended description if needed.
"""

import sys


def main() -> int:
    """Entry point. Returns exit code."""
    print("Hello, world.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Standard Automation Script

```python
#!/usr/bin/env python3
"""
script_name.py — Brief description of what this script does.

Usage:
    python script_name.py --input ./data/ --output ./results/ --verbose
"""

import argparse
import logging
import sys
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input",   type=Path, required=True,  help="Input path")
    parser.add_argument("--output",  type=Path, required=True,  help="Output path")
    parser.add_argument("--verbose", action="store_true",        help="Enable debug logging")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.input.exists():
        raise FileNotFoundError(f"Input path not found: {args.input}")
    args.output.mkdir(parents=True, exist_ok=True)


def process(input_path: Path, output_path: Path) -> int:
    """Core logic. Returns count of items processed."""
    log = logging.getLogger(__name__)
    count = 0

    for file in sorted(input_path.rglob("*.txt")):
        log.debug(f"Processing: {file}")
        # TODO: implement processing
        count += 1

    log.info(f"Processed {count} files → {output_path}")
    return count


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    log = logging.getLogger(__name__)

    try:
        validate_args(args)
        count = process(args.input, args.output)
        log.info(f"Done. {count} items processed.")
        return 0
    except FileNotFoundError as e:
        log.error(str(e))
        return 1
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        return 130
    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## CLI with argparse

```python
import argparse
from pathlib import Path

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="my_tool",
        description="Tool description.",
        epilog="Example: my_tool --input data.csv --format json"
    )

    # Positional
    parser.add_argument("source", type=Path, help="Source file or directory")

    # Optional with default
    parser.add_argument("--output", "-o", type=Path, default=Path("./output"),
                        help="Output directory (default: ./output)")

    # Flag
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview actions without writing files")

    # Choice
    parser.add_argument("--format", choices=["json", "csv", "xlsx"],
                        default="json", help="Output format")

    # Count (e.g. -v, -vv, -vvv)
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Verbosity level (repeat for more: -vvv)")

    # Multiple values
    parser.add_argument("--exclude", nargs="+", default=[],
                        metavar="PATTERN", help="Patterns to exclude")

    # Integer with range validation
    parser.add_argument("--workers", type=int, default=4,
                        choices=range(1, 17),
                        help="Parallel worker count (1-16, default: 4)")

    return parser
```

---

## Error Handling

### Exception Hierarchy Pattern

```python
# Define project-specific exceptions
class AppError(Exception):
    """Base exception for this application."""

class ConfigError(AppError):
    """Invalid or missing configuration."""

class DataError(AppError):
    """Data validation or parsing failure."""

class NetworkError(AppError):
    """Network or API failure."""
```

### Standard Error Handling Block

```python
import sys
import logging

log = logging.getLogger(__name__)

def run():
    try:
        result = risky_operation()
        return result

    except FileNotFoundError as e:
        log.error(f"File not found: {e}")
        sys.exit(1)

    except PermissionError as e:
        log.error(f"Permission denied: {e}")
        sys.exit(1)

    except ValueError as e:
        log.error(f"Invalid value: {e}")
        sys.exit(2)

    except KeyboardInterrupt:
        log.warning("Interrupted.")
        sys.exit(130)   # standard Unix interrupt exit code

    except Exception as e:
        log.exception(f"Unexpected error: {e}")  # includes traceback
        sys.exit(1)
```

### Context Manager for Safe File Ops

```python
from contextlib import contextmanager
from pathlib import Path
import tempfile, shutil

@contextmanager
def atomic_write(target_path: Path):
    """Write to temp file then rename — prevents partial writes."""
    tmp = target_path.with_suffix('.tmp')
    try:
        yield tmp
        tmp.replace(target_path)   # atomic on same filesystem
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

# Usage
with atomic_write(Path('output.json')) as tmp:
    tmp.write_text('{"status": "ok"}')
```

---

## Logging

```python
import logging
import sys
from pathlib import Path

def setup_logging(
    verbose: bool = False,
    log_file: Path = None,
    name: str = None
) -> logging.Logger:
    """
    Configure root logger with console + optional file handler.
    Returns named logger if name provided, else root logger.
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
        handlers=handlers,
        force=True   # override any existing config
    )

    return logging.getLogger(name) if name else logging.getLogger()


# Usage
log = setup_logging(verbose=True, log_file=Path('./logs/run.log'))
log.debug("Debug message")
log.info("Info message")
log.warning("Warning message")
log.error("Error message")
log.exception("Error with traceback")  # use inside except blocks
```

---

## File I/O

### Path Operations (pathlib — always prefer over os.path)

```python
from pathlib import Path

p = Path("./data/input.csv")

p.exists()              # bool
p.is_file()             # bool
p.is_dir()              # bool
p.suffix                # '.csv'
p.stem                  # 'input'
p.name                  # 'input.csv'
p.parent                # Path('./data')
p.resolve()             # absolute path

# Build paths
output = p.parent / "output" / p.stem + "_processed.csv"

# Create directories
Path("./output/subdir").mkdir(parents=True, exist_ok=True)

# Glob
list(Path("./data").glob("*.csv"))         # direct children
list(Path("./data").rglob("*.csv"))        # recursive

# Read / write text
text = p.read_text(encoding='utf-8')
p.write_text("content", encoding='utf-8')

# Read / write bytes
data = p.read_bytes()
p.write_bytes(b'\x89PNG...')
```

### CSV

```python
import csv
from pathlib import Path

# Read
with open('data.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Write
fieldnames = ['id', 'name', 'value']
with open('output.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
```

### JSON

```python
import json
from pathlib import Path

# Read
data = json.loads(Path('data.json').read_text(encoding='utf-8'))

# Write (pretty-printed)
Path('output.json').write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding='utf-8'
)
```

---

## Packaging

### pyproject.toml (modern standard)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-tool"
version = "0.1.0"
description = "Tool description"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "requests>=2.31.0",
    "click>=8.1.0",
]

[project.scripts]
my-tool = "my_tool.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.4.0",
    "mypy>=1.0",
]
```

### requirements.txt (pinned for reproducibility)

```bash
# Generate
pip freeze > requirements.txt

# Install
pip install -r requirements.txt

# Best practice: separate dev requirements
pip freeze > requirements-dev.txt
```

---

## Linting & Formatting

```bash
# Install ruff (fast, replaces flake8 + isort + pyupgrade)
pip install ruff mypy

# Format (replaces black)
ruff format script.py
ruff format .           # whole project

# Lint
ruff check script.py
ruff check --fix .      # auto-fix safe issues

# Type checking
mypy script.py
mypy --strict script.py

# ruff.toml or pyproject.toml config
```

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true
```

---

## Validation & QA

```bash
# Full QA pipeline
ruff format .           # format
ruff check --fix .      # lint + auto-fix
mypy .                  # type check
python -m pytest        # tests
python script.py --help # smoke test — does it run?
```

### QA Checklist

- [ ] Script has shebang: `#!/usr/bin/env python3`
- [ ] Module docstring present
- [ ] `if __name__ == "__main__":` guard present
- [ ] `sys.exit(main())` pattern used
- [ ] All functions have docstrings
- [ ] No bare `except:` clauses
- [ ] No hardcoded paths — use `argparse` or config
- [ ] No hardcoded credentials — use env vars
- [ ] Logging used instead of bare `print()` (for production scripts)
- [ ] File ops use `pathlib.Path`, not `os.path`
- [ ] `ruff check` passes with zero errors
- [ ] `mypy` passes (or suppressions are documented)
- [ ] Script tested with `--help` and at least one real invocation

### QA Loop

1. Write script
2. Run `ruff format` + `ruff check --fix`
3. Run `mypy` — fix type errors
4. Smoke test: `python script.py --help`
5. Functional test: run with real or sample inputs
6. Check output files/results are correct
7. **Do not ship until linting passes and smoke test succeeds**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Package not installed in active env | `pip install package` in correct venv |
| Script works locally, fails in CI | Hardcoded path or missing env var | Use `argparse` / `os.environ` |
| `UnicodeDecodeError` on file read | File not UTF-8 | Open with `encoding='utf-8', errors='replace'` |
| `PermissionError` on write | No write access to directory | Check permissions; write to temp dir first |
| `RecursionError` | Unintended deep recursion | Add depth limit; convert to iterative |
| Slow on large files | Loading entire file into memory | Use streaming / chunked reads |

---

## Dependencies

```bash
# Core tools
pip install ruff mypy pytest

# Common utility packages
pip install requests          # HTTP
pip install click             # CLI framework (alternative to argparse)
pip install pydantic          # data validation
pip install rich              # terminal formatting
pip install tqdm              # progress bars
pip install pandas            # data processing
```
