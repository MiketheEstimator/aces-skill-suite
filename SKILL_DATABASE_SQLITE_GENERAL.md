---
name: SKILL_DATABASE_SQLITE_GENERAL
description: "Creation and manipulation of self-contained, offline relational databases. Use when producing .sqlite or .db files, SQL schema scripts, or database automation. Triggers: 'SQLite', '.sqlite', '.db file', 'offline database', 'embedded database', 'relational data', 'create database schema'."
---

# SKILL_DATABASE_SQLITE_GENERAL — SQLite Database Skill

## Quick Reference

| Task | Section |
|------|---------|
| Schema design & creation | [Schema Design](#schema-design) |
| CRUD operations | [CRUD Operations](#crud-operations) |
| Indexes & performance | [Indexes & Performance](#indexes--performance) |
| Python integration | [Python Integration](#python-integration) |
| Import / export data | [Import & Export](#import--export) |
| CLI operations | [CLI Operations](#cli-operations) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Schema Design

### Full Schema Template

```sql
-- =============================================================================
-- schema.sql — Database schema for [Project Name]
-- SQLite version: 3.x
-- =============================================================================

PRAGMA journal_mode = WAL;         -- Write-Ahead Logging for concurrency
PRAGMA foreign_keys = ON;          -- Enforce FK constraints (off by default)
PRAGMA encoding = 'UTF-8';

-- =============================================================================
-- TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','complete','archived')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    code        TEXT    NOT NULL,
    description TEXT,
    quantity    REAL    NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit        TEXT    NOT NULL DEFAULT 'EA',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (project_id, code)
);

CREATE TABLE IF NOT EXISTS tags (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS item_tags (
    item_id  INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag_id   INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_items_project ON items (project_id);
CREATE INDEX IF NOT EXISTS idx_items_code    ON items (code);
CREATE INDEX IF NOT EXISTS idx_projects_code ON projects (code);

-- =============================================================================
-- TRIGGERS — auto-update updated_at
-- =============================================================================

CREATE TRIGGER IF NOT EXISTS trg_projects_updated
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- =============================================================================
-- VIEWS
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_item_summary AS
SELECT
    p.code                  AS project_code,
    p.name                  AS project_name,
    i.code                  AS item_code,
    i.description,
    i.quantity,
    i.unit,
    COUNT(it.tag_id)        AS tag_count,
    i.created_at
FROM items i
JOIN projects p ON i.project_id = p.id
LEFT JOIN item_tags it ON i.id = it.item_id
GROUP BY i.id;
```

### SQLite Data Types

```sql
-- SQLite uses type affinity, not strict types
-- 5 storage classes:
NULL     -- null value
INTEGER  -- signed integer (1,2,3,4,6,8 bytes)
REAL     -- 8-byte IEEE float
TEXT     -- UTF-8/UTF-16 string
BLOB     -- binary data, stored as-is

-- Common column type patterns:
id          INTEGER PRIMARY KEY AUTOINCREMENT
code        TEXT NOT NULL UNIQUE
amount      REAL NOT NULL DEFAULT 0
count       INTEGER NOT NULL DEFAULT 0
flag        INTEGER NOT NULL DEFAULT 0 CHECK (flag IN (0, 1))   -- boolean
created_at  TEXT NOT NULL DEFAULT (datetime('now'))             -- ISO 8601
date_val    TEXT NOT NULL                                       -- 'YYYY-MM-DD'
json_data   TEXT                                                -- JSON as text
file_data   BLOB                                                -- binary
```

---

## CRUD Operations

### INSERT

```sql
-- Single row
INSERT INTO projects (code, name) VALUES ('PRJ001', 'Project Alpha');

-- Multiple rows
INSERT INTO items (project_id, code, description, quantity, unit) VALUES
    (1, 'ITEM-001', 'Steel beam', 10.0, 'EA'),
    (1, 'ITEM-002', 'Concrete mix', 500.0, 'KG'),
    (1, 'ITEM-003', 'Rebar', 200.0, 'M');

-- Insert or ignore (skip on conflict)
INSERT OR IGNORE INTO projects (code, name) VALUES ('PRJ001', 'Duplicate');

-- Insert or replace (upsert — replaces entire row)
INSERT OR REPLACE INTO projects (code, name) VALUES ('PRJ001', 'Updated Name');

-- Upsert (update specific columns on conflict)
INSERT INTO projects (code, name)
VALUES ('PRJ001', 'Project Alpha')
ON CONFLICT(code) DO UPDATE SET
    name = excluded.name,
    updated_at = datetime('now');
```

### SELECT

```sql
-- Basic
SELECT * FROM projects WHERE status = 'active';

-- With JOIN
SELECT p.code, i.code AS item_code, i.description
FROM projects p
JOIN items i ON i.project_id = p.id
WHERE p.status = 'active'
ORDER BY p.code, i.code;

-- Aggregation
SELECT
    p.code,
    COUNT(i.id)     AS item_count,
    SUM(i.quantity) AS total_qty
FROM projects p
LEFT JOIN items i ON i.project_id = p.id
GROUP BY p.id
HAVING item_count > 0;

-- JSON extraction (SQLite 3.38+)
SELECT json_extract(json_data, '$.name') AS name
FROM items
WHERE json_extract(json_data, '$.active') = 1;

-- Full-text search (FTS5)
SELECT * FROM items_fts WHERE items_fts MATCH 'concrete beam';
```

### UPDATE / DELETE

```sql
-- Update
UPDATE items
SET quantity = quantity + 50
WHERE project_id = 1 AND code = 'ITEM-002';

-- Conditional update
UPDATE projects
SET status = 'complete', updated_at = datetime('now')
WHERE id = 1 AND status = 'active';

-- Delete with FK cascade
DELETE FROM projects WHERE code = 'PRJ001';
-- (cascades to items, item_tags via ON DELETE CASCADE)

-- Soft delete pattern
ALTER TABLE projects ADD COLUMN deleted_at TEXT;
UPDATE projects SET deleted_at = datetime('now') WHERE id = 1;
-- Then filter: WHERE deleted_at IS NULL
```

---

## Indexes & Performance

```sql
-- Single column index
CREATE INDEX idx_items_code ON items (code);

-- Composite index (order matters — most selective first)
CREATE INDEX idx_items_project_code ON items (project_id, code);

-- Partial index (only index rows meeting condition)
CREATE INDEX idx_active_projects ON projects (code)
WHERE status = 'active';

-- Unique index
CREATE UNIQUE INDEX idx_projects_code ON projects (code);

-- Check if index is being used
EXPLAIN QUERY PLAN
SELECT * FROM items WHERE project_id = 1 AND code = 'ITEM-001';
-- Look for: SEARCH items USING INDEX (not SCAN)

-- Analyse statistics for query planner
ANALYZE;

-- Vacuum to reclaim space and defragment
VACUUM;

-- Performance PRAGMAs
PRAGMA cache_size = -64000;        -- 64MB cache
PRAGMA mmap_size = 268435456;      -- 256MB memory-map
PRAGMA synchronous = NORMAL;       -- balance durability vs speed
PRAGMA temp_store = MEMORY;        -- temp tables in RAM
```

---

## Python Integration

### Core Pattern

```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("./data/project.db")

@contextmanager
def get_db(db_path: Path = DB_PATH):
    """Thread-safe database connection context manager."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row     # rows as dict-like objects
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Initialise Database

```python
def init_db(db_path: Path = DB_PATH) -> None:
    """Create schema from SQL file."""
    schema = Path("schema.sql").read_text(encoding="utf-8")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_db(db_path) as conn:
        conn.executescript(schema)
    print(f"Database initialised: {db_path}")
```

### CRUD with Parameterised Queries

```python
# Always use ? placeholders — never f-strings or string concatenation (SQL injection)

def insert_project(code: str, name: str) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO projects (code, name) VALUES (?, ?)",
            (code, name)
        )
        return cursor.lastrowid

def get_project(code: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE code = ?",
            (code,)
        ).fetchone()
    return dict(row) if row else None

def list_items(project_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE project_id = ? ORDER BY code",
            (project_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def upsert_item(project_id: int, code: str, description: str, qty: float) -> None:
    with get_db() as conn:
        conn.execute("""
            INSERT INTO items (project_id, code, description, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, code) DO UPDATE SET
                description = excluded.description,
                quantity    = excluded.quantity
        """, (project_id, code, description, qty))

def bulk_insert(rows: list[dict]) -> None:
    """Batch insert for performance."""
    with get_db() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO items (project_id, code, description, quantity) "
            "VALUES (:project_id, :code, :description, :quantity)",
            rows
        )
```

### Pandas Integration

```python
import pandas as pd
import sqlite3
from pathlib import Path

# Read into DataFrame
with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM v_item_summary WHERE project_code = ?",
        conn,
        params=("PRJ001",)
    )

# Write DataFrame to table
with sqlite3.connect(DB_PATH) as conn:
    df.to_sql("items_import", conn, if_exists="replace", index=False)
    # if_exists: 'fail' | 'replace' | 'append'
```

---

## Import & Export

### CSV Import

```python
import csv, sqlite3
from pathlib import Path

def import_csv(csv_path: str, table: str, db_path: str = DB_PATH) -> int:
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return 0

    cols = rows[0].keys()
    placeholders = ", ".join(f":{c}" for c in cols)
    sql = f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    with sqlite3.connect(db_path) as conn:
        conn.executemany(sql, rows)
        conn.commit()

    return len(rows)
```

```bash
# SQLite CLI CSV import
sqlite3 project.db <<EOF
.mode csv
.import data.csv items
EOF
```

### Export to CSV / JSON

```bash
# CSV export via CLI
sqlite3 -header -csv project.db "SELECT * FROM v_item_summary;" > export.csv

# JSON export
sqlite3 -json project.db "SELECT * FROM items;" > export.json
```

```python
import sqlite3, csv, json
from pathlib import Path

def export_to_csv(query: str, output_path: str, db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()

    if not rows:
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
    print(f"Exported {len(rows)} rows → {output_path}")
```

---

## CLI Operations

```bash
# Open interactive shell
sqlite3 project.db

# Common dot commands
.tables                        # list tables
.schema                        # show all CREATE statements
.schema items                  # show specific table
.indexes                       # list all indexes
.mode column                   # columnar output
.headers on                    # show column names
.width 20 40 10               # set column widths

# Quick queries
sqlite3 project.db "SELECT COUNT(*) FROM items;"
sqlite3 -header -column project.db "SELECT * FROM projects LIMIT 5;"

# Run SQL file
sqlite3 project.db < schema.sql
sqlite3 project.db ".read schema.sql"

# Backup
sqlite3 project.db ".backup backup.db"

# Integrity check
sqlite3 project.db "PRAGMA integrity_check;"
sqlite3 project.db "PRAGMA foreign_key_check;"
```

---

## Validation & QA

```python
import sqlite3
from pathlib import Path

def validate_database(db_path: str) -> bool:
    errors = []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # 1. Integrity check
        result = conn.execute("PRAGMA integrity_check").fetchall()
        if result[0][0] != "ok":
            errors.append(f"INTEGRITY FAIL: {[r[0] for r in result]}")

        # 2. Foreign key check
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_violations:
            errors.append(f"FK VIOLATIONS: {len(fk_violations)} found")

        # 3. Table list
        tables = [r["name"] for r in
                  conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Tables: {tables}")

        # 4. Row counts
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
            print(f"  {table}: {count} rows")

        # 5. Schema version (if using user_version)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        print(f"Schema version: {version}")

    finally:
        conn.close()

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Database is valid")
    return True


validate_database("project.db")
```

### QA Checklist

- [ ] `PRAGMA foreign_keys = ON` set on every connection
- [ ] `PRAGMA journal_mode = WAL` set for concurrent access
- [ ] All parameterised queries use `?` / `:name` — never string formatting
- [ ] `PRAGMA integrity_check` passes
- [ ] `PRAGMA foreign_key_check` returns no violations
- [ ] All tables have appropriate indexes for expected queries
- [ ] `EXPLAIN QUERY PLAN` confirms indexes are used (not full scans)
- [ ] No data inserted without validation (use `CHECK` constraints)
- [ ] Backup strategy defined (`.backup` command or file copy when db closed)

### QA Loop

1. Create schema with `CREATE TABLE IF NOT EXISTS` everywhere
2. Run `PRAGMA integrity_check` — expect `ok`
3. Run `PRAGMA foreign_key_check` — expect no rows
4. Insert sample data — verify constraints fire correctly
5. Run `EXPLAIN QUERY PLAN` on critical queries — fix missing indexes
6. **Do not ship until integrity check passes and all queries use indexes**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| FK constraint ignored | `PRAGMA foreign_keys` not set | Add `PRAGMA foreign_keys = ON` on every connection |
| `database is locked` | Multiple writers without WAL | Set `PRAGMA journal_mode = WAL` |
| Slow queries | Missing indexes | Run `EXPLAIN QUERY PLAN`; add indexes |
| `UNIQUE constraint failed` | Duplicate insert | Use `INSERT OR IGNORE` or `ON CONFLICT DO UPDATE` |
| Database corruption | Crash during write without WAL | Use WAL mode; run `PRAGMA integrity_check` to detect |
| `no such table` | Schema not initialised | Run `init_db()` or `.read schema.sql` |
| Boolean values wrong | Python True/False stored as 1/0 | Use `CHECK (col IN (0,1))`; read as `bool(row['col'])` |

---

## Dependencies

```bash
# Python — stdlib only (no install needed)
import sqlite3

# Pandas integration
pip install pandas

# Schema migration tool
pip install alembic     # for versioned migrations
pip install sqlite-utils  # CLI and Python tool for SQLite manipulation

# CLI
# SQLite3 CLI is pre-installed on Linux/macOS
# Windows: download from https://sqlite.org/download.html
```
