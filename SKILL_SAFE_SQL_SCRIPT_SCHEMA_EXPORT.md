---
name: safe-sql-script-schema-export
description: "Use this skill when generating .sql files — DDL schema scripts, DML data exports, migration scripts, or stored procedures. Trigger on any request for SQL output, database schema creation, seed data scripts, or database migration files."
---

# Safe SQL Script / Schema Export SKILL

## Quick Reference

| Task | Approach |
|------|----------|
| DDL schema | CREATE TABLE with constraints |
| DML seed data | INSERT with safe value quoting |
| Migration script | Sequential ALTER TABLE statements |
| Data export | SELECT → INSERT or COPY format |
| Multi-dialect | Flag dialect at top of file |

---

## File Header Convention

Always begin SQL files with a dialect and intent header:

```sql
-- ============================================================
-- Script:   schema_v1.sql
-- Dialect:  PostgreSQL 15
-- Purpose:  Initial schema creation
-- Author:   Generated
-- Date:     2024-03-15
-- Run:      psql -U user -d dbname -f schema_v1.sql
-- ============================================================
```

---

## DDL: Schema Creation

```sql
-- Safe creation pattern: check before create
CREATE TABLE IF NOT EXISTS projects (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255)    NOT NULL,
    status        VARCHAR(50)     NOT NULL DEFAULT 'active',
    budget        NUMERIC(15,2),
    start_date    DATE,
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('active','on_hold','complete','cancelled')),
    CONSTRAINT chk_budget CHECK (budget >= 0)
);

-- Index creation
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_start_date ON projects(start_date);

-- Foreign key example
CREATE TABLE IF NOT EXISTS project_phases (
    id          SERIAL PRIMARY KEY,
    project_id  INTEGER NOT NULL,
    phase_name  VARCHAR(100) NOT NULL,
    sequence    INTEGER NOT NULL,

    CONSTRAINT fk_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
        ON DELETE CASCADE
);
```

---

## DML: Safe Data Insertion

```python
# Generate INSERT statements safely from Python
import re

def sql_escape(value):
    """Escape string values for SQL. Use parameterized queries in production."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes by doubling them
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"

def generate_inserts(table, rows, columns):
    lines = []
    col_list = ", ".join(columns)
    for row in rows:
        values = ", ".join(sql_escape(v) for v in row)
        lines.append(f"INSERT INTO {table} ({col_list}) VALUES ({values});")
    return "\n".join(lines)
```

---

## Transaction Wrapping

```sql
-- Always wrap migrations and bulk inserts in transactions
BEGIN;

-- Schema changes
ALTER TABLE projects ADD COLUMN IF NOT EXISTS region VARCHAR(100);

-- Data updates
UPDATE projects SET region = 'EMEA' WHERE id IN (1, 2, 3);

-- Verify before committing
-- SELECT COUNT(*) FROM projects WHERE region IS NULL;

COMMIT;
-- ROLLBACK;  -- Uncomment to undo
```

---

## Migration Script Pattern

```sql
-- Migration: 002_add_project_region.sql
-- Depends on: 001_initial_schema.sql

BEGIN;

-- Up migration
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS region VARCHAR(100),
    ADD COLUMN IF NOT EXISTS region_code CHAR(4);

CREATE INDEX IF NOT EXISTS idx_projects_region ON projects(region);

-- Down migration (comment block — uncomment to reverse)
/*
DROP INDEX IF EXISTS idx_projects_region;
ALTER TABLE projects
    DROP COLUMN IF EXISTS region,
    DROP COLUMN IF EXISTS region_code;
*/

COMMIT;
```

---

## Dialect Differences Reference

| Feature | PostgreSQL | MySQL | SQLite | SQL Server |
|---------|-----------|-------|--------|------------|
| Auto-increment | `SERIAL` / `GENERATED` | `AUTO_INCREMENT` | `AUTOINCREMENT` | `IDENTITY(1,1)` |
| String type | `VARCHAR(n)` | `VARCHAR(n)` | `TEXT` | `NVARCHAR(n)` |
| Boolean | `BOOLEAN` | `TINYINT(1)` | `INTEGER` | `BIT` |
| Current time | `CURRENT_TIMESTAMP` | `NOW()` | `datetime('now')` | `GETDATE()` |
| If not exists | Supported | Supported | Supported | Not for columns |

---

## CLI Verification

```bash
# Syntax check (PostgreSQL)
psql -U user -d dbname --dry-run -f output.sql

# Syntax check with pg_dump round-trip
psql -c "\i output.sql" -v ON_ERROR_STOP=1

# Lint SQL with sqlfluff
pip install sqlfluff --break-system-packages
sqlfluff lint output.sql --dialect postgres

# Format SQL
sqlfluff fix output.sql --dialect postgres

# Grep for unsafe patterns
grep -n "DROP TABLE " output.sql      # Flag any DROP TABLE
grep -n "DELETE FROM" output.sql      # Flag any DELETE without WHERE
grep -n "TRUNCATE" output.sql         # Flag TRUNCATE
```

---

## QA Checklist

- [ ] Dialect declared in header comment
- [ ] All `CREATE` statements use `IF NOT EXISTS`
- [ ] All `DROP` statements use `IF EXISTS`
- [ ] Foreign keys reference existing tables (in correct order)
- [ ] Transaction wrapping on all destructive operations
- [ ] No string values with unescaped single quotes
- [ ] No `DELETE` or `UPDATE` without `WHERE` clause
- [ ] Indexes named consistently (`idx_table_column`)
- [ ] Constraints named consistently (`fk_`, `chk_`, `uq_`)
- [ ] Script tested end-to-end (or at minimum syntax-checked)

---

## Safety Rules

> **Never generate:**
> - `DROP DATABASE` or `DROP SCHEMA` statements
> - `TRUNCATE` without explicit user confirmation
> - `DELETE FROM table` without a `WHERE` clause
> - Hardcoded passwords or connection strings in scripts

---

## Dependencies

```bash
pip install sqlfluff --break-system-packages   # linting and formatting
# psql, mysql, sqlite3: database CLI tools (system-installed)
```
