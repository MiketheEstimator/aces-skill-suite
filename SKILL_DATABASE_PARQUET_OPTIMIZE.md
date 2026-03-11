---
name: SKILL_DATABASE_PARQUET_OPTIMIZE
description: "Columnar data compression and serialization for analytical pipelines. Use when producing .parquet files for data lakes, analytical queries, large dataset storage, or pipeline interchange. Triggers: 'Parquet', '.parquet file', 'columnar storage', 'data lake', 'analytical pipeline', 'PyArrow', 'DuckDB', 'Spark data'."
---

# SKILL_DATABASE_PARQUET_OPTIMIZE — Parquet Columnar Storage Skill

## Quick Reference

| Task | Section |
|------|---------|
| Write Parquet files | [Writing Parquet](#writing-parquet) |
| Read & query Parquet | [Reading Parquet](#reading-parquet) |
| Schema & types | [Schema & Types](#schema--types) |
| Partitioning | [Partitioning](#partitioning) |
| Compression options | [Compression](#compression) |
| DuckDB integration | [DuckDB Integration](#duckdb-integration) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Format Overview

| Feature | Parquet |
|---------|---------|
| Storage | Columnar (not row-based) |
| Compression | Snappy (default), Gzip, Brotli, Zstd, LZ4, None |
| Schema | Embedded (self-describing) |
| Nested data | Supported (lists, maps, structs) |
| Predicate pushdown | Yes — skip row groups during read |
| Column pruning | Yes — read only selected columns |
| Max row group size | Configurable (default 128MB) |
| Best for | Analytics, aggregations, large datasets, pipelines |
| Not ideal for | Frequent updates, single-row lookups, streaming appends |

---

## Writing Parquet

### pandas → Parquet

```python
import pandas as pd
from pathlib import Path

# Basic write
df = pd.DataFrame({
    "id":       [1, 2, 3],
    "name":     ["Alpha", "Beta", "Gamma"],
    "value":    [10.5, 20.3, 30.1],
    "date":     pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
    "active":   [True, True, False]
})

# Write with snappy compression (default, fast)
df.to_parquet("output.parquet", engine="pyarrow", compression="snappy", index=False)

# Write with zstd (better compression, slightly slower)
df.to_parquet("output.parquet", engine="pyarrow", compression="zstd", index=False)

# Write without compression (fastest read/write, largest file)
df.to_parquet("output.parquet", engine="pyarrow", compression=None, index=False)
```

### PyArrow → Parquet (full control)

```python
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

# Define explicit schema
schema = pa.schema([
    pa.field("id",          pa.int64(),      nullable=False),
    pa.field("project_id",  pa.int32(),      nullable=False),
    pa.field("code",        pa.string(),     nullable=False),
    pa.field("description", pa.string(),     nullable=True),
    pa.field("quantity",    pa.float64(),    nullable=False),
    pa.field("date",        pa.date32(),     nullable=True),
    pa.field("timestamp",   pa.timestamp("ms", tz="UTC"), nullable=True),
    pa.field("tags",        pa.list_(pa.string()), nullable=True),
])

# Create table from dict
table = pa.table({
    "id":          [1, 2, 3],
    "project_id":  [100, 100, 101],
    "code":        ["A001", "A002", "B001"],
    "description": ["Item A", "Item B", None],
    "quantity":    [10.0, 20.0, 30.0],
    "date":        [None, None, None],
    "timestamp":   [None, None, None],
    "tags":        [["concrete", "structural"], ["rebar"], []],
}, schema=schema)

# Write with all options
pq.write_table(
    table,
    "output.parquet",
    compression="snappy",
    row_group_size=100_000,     # rows per row group
    use_dictionary=True,        # dictionary encoding for repeated strings
    write_statistics=True,      # enables predicate pushdown
    coerce_timestamps="ms",     # normalise timestamp precision
)

print(f"Written: {table.num_rows} rows, {table.num_columns} columns")
```

### Append / Merge Multiple Files

```python
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path

# Append by writing multiple files and reading as dataset
def append_to_parquet_dir(new_df, output_dir: str, filename_prefix: str = "part"):
    """Write new partition file to a directory of Parquet files."""
    import pandas as pd
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    existing = sorted(path.glob(f"{filename_prefix}_*.parquet"))
    n = len(existing)
    out_file = path / f"{filename_prefix}_{n:04d}.parquet"
    new_df.to_parquet(out_file, engine="pyarrow", index=False)
    print(f"Written: {out_file}")

# Merge multiple Parquet files into one
def merge_parquet_files(input_dir: str, output_file: str) -> int:
    import pyarrow.dataset as ds
    dataset = ds.dataset(input_dir, format="parquet")
    table = dataset.to_table()
    pq.write_table(table, output_file, compression="snappy")
    print(f"Merged {len(list(Path(input_dir).glob('*.parquet')))} files "
          f"→ {output_file} ({table.num_rows} rows)")
    return table.num_rows
```

---

## Reading Parquet

### pandas

```python
import pandas as pd

# Read full file
df = pd.read_parquet("output.parquet", engine="pyarrow")

# Read specific columns only (column pruning — faster for wide tables)
df = pd.read_parquet("output.parquet", columns=["id", "code", "quantity"])

# Read from directory of partitioned Parquet files
df = pd.read_parquet("data/partitioned/", engine="pyarrow")
```

### PyArrow Dataset (lazy, scalable)

```python
import pyarrow.dataset as ds
import pyarrow.compute as pc

# Open dataset (lazy — doesn't read into memory yet)
dataset = ds.dataset("data/parquet/", format="parquet")

print(f"Schema:\n{dataset.schema}")
print(f"Files: {dataset.files}")

# Filter at scan time (predicate pushdown — skips row groups)
table = dataset.to_table(
    filter=pc.field("quantity") > 100,
    columns=["id", "code", "quantity"]
)

df = table.to_pandas()
print(f"Filtered rows: {len(df)}")
```

### Inspect Without Loading

```python
import pyarrow.parquet as pq

# Read metadata only (instant, no data loaded)
meta = pq.read_metadata("output.parquet")
print(f"Row groups:  {meta.num_row_groups}")
print(f"Total rows:  {meta.num_rows}")
print(f"Columns:     {meta.num_columns}")
print(f"Serialized:  {meta.serialized_size:,} bytes")

# Schema
schema = pq.read_schema("output.parquet")
print(schema)

# Row group stats
for i in range(meta.num_row_groups):
    rg = meta.row_group(i)
    print(f"Row group {i}: {rg.num_rows} rows, {rg.total_byte_size:,} bytes")
```

---

## Schema & Types

### Type Mapping Reference

| Python/Pandas | PyArrow type | Notes |
|---------------|-------------|-------|
| `int64` | `pa.int64()` | |
| `int32` | `pa.int32()` | Smaller = less space |
| `float64` | `pa.float64()` | |
| `float32` | `pa.float32()` | Half the size; ~7 sig. digits |
| `str` / `object` | `pa.string()` | UTF-8 |
| `bool` | `pa.bool_()` | |
| `datetime64[ns]` | `pa.timestamp("ns")` | |
| `datetime64[ms]` | `pa.timestamp("ms", tz="UTC")` | Prefer ms precision |
| `date` | `pa.date32()` | Days since epoch |
| `list` | `pa.list_(pa.string())` | |
| `dict` | `pa.map_(pa.string(), pa.string())` | |

### Schema Enforcement on Read

```python
import pyarrow.parquet as pq
import pyarrow as pa

expected_schema = pa.schema([
    pa.field("id",       pa.int64()),
    pa.field("code",     pa.string()),
    pa.field("quantity", pa.float64()),
])

table = pq.read_table("output.parquet")

# Cast to expected schema
try:
    table = table.cast(expected_schema)
except pa.ArrowInvalid as e:
    print(f"Schema mismatch: {e}")
```

---

## Partitioning

```python
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pandas as pd

# Create partitioned dataset (Hive-style: col=value/ directories)
df = pd.DataFrame({
    "year":     [2024, 2024, 2023, 2023],
    "month":    [1,    2,    12,   11],
    "region":   ["UK", "UK", "DE", "FR"],
    "value":    [100,  200,  150,  175]
})

table = pa.Table.from_pandas(df)

# Write partitioned by year and month
pq.write_to_dataset(
    table,
    root_path="data/partitioned",
    partition_cols=["year", "month"],
    compression="snappy",
    existing_data_behavior="overwrite_or_ignore"
)
# Creates: data/partitioned/year=2024/month=1/part-0.parquet
#          data/partitioned/year=2024/month=2/part-0.parquet  etc.

# Read with partition filter (only reads matching partitions)
dataset = ds.dataset("data/partitioned", format="parquet",
                     partitioning="hive")
table = dataset.to_table(
    filter=(ds.field("year") == 2024) & (ds.field("month") == 1)
)
```

---

## Compression

| Codec | Speed | Ratio | Best For |
|-------|-------|-------|----------|
| `snappy` | Very fast | Good | Default — balanced |
| `lz4` | Fastest | Fair | Highest throughput needed |
| `zstd` | Fast | Best | Storage cost matters |
| `gzip` | Slow | Very good | Archival, broad compat |
| `brotli` | Slowest | Excellent | Maximum compression |
| `None` | Instant | None | Fastest read, temp files |

```python
# Benchmark compression on your data
import time
from pathlib import Path

codecs = ["snappy", "lz4", "zstd", "gzip", None]
results = []

for codec in codecs:
    fname = f"test_{codec or 'none'}.parquet"
    t0 = time.time()
    df.to_parquet(fname, engine="pyarrow", compression=codec, index=False)
    write_time = time.time() - t0
    size = Path(fname).stat().st_size

    t0 = time.time()
    pd.read_parquet(fname)
    read_time = time.time() - t0

    results.append({
        "codec": codec or "none",
        "size_mb": round(size / 1024**2, 2),
        "write_s": round(write_time, 3),
        "read_s":  round(read_time, 3)
    })

for r in results:
    print(f"{r['codec']:8s}  {r['size_mb']:6.2f} MB  "
          f"write: {r['write_s']:.3f}s  read: {r['read_s']:.3f}s")
```

---

## DuckDB Integration

```python
import duckdb

# Query Parquet directly (no loading into memory required)
conn = duckdb.connect()

# Single file
result = conn.execute("""
    SELECT code, SUM(quantity) AS total_qty
    FROM 'output.parquet'
    WHERE quantity > 10
    GROUP BY code
    ORDER BY total_qty DESC
""").df()

# Directory of Parquet files
result = conn.execute("""
    SELECT year, COUNT(*) AS row_count, SUM(value) AS total
    FROM 'data/partitioned/**/*.parquet'
    GROUP BY year
""").df()

# Write query result back to Parquet
conn.execute("""
    COPY (SELECT * FROM 'input.parquet' WHERE active = true)
    TO 'active_only.parquet' (FORMAT PARQUET, COMPRESSION SNAPPY)
""")

print(result)
```

---

## Validation & QA

```python
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path

def validate_parquet(path: str, expected_schema: pa.Schema = None,
                     min_rows: int = 1) -> bool:
    errors = []
    p = Path(path)

    # 1. File exists and is non-empty
    if not p.exists():
        print(f"ERROR: File not found: {path}")
        return False
    if p.stat().st_size == 0:
        print("ERROR: File is empty")
        return False

    try:
        meta = pq.read_metadata(path)
        print(f"Row groups:  {meta.num_row_groups}")
        print(f"Total rows:  {meta.num_rows}")
        print(f"Columns:     {meta.num_columns}")
        print(f"Size:        {p.stat().st_size / 1024**2:.2f} MB")

        # 2. Minimum row count
        if meta.num_rows < min_rows:
            errors.append(f"WARNING: Only {meta.num_rows} rows (expected >= {min_rows})")

        # 3. Schema check
        actual_schema = pq.read_schema(path)
        if expected_schema:
            if actual_schema != expected_schema:
                errors.append(f"SCHEMA MISMATCH:\n"
                               f"  Expected: {expected_schema}\n"
                               f"  Actual:   {actual_schema}")

        # 4. Read first row group to confirm data integrity
        table = pq.read_table(path, row_groups=[0])
        if table.num_rows == 0:
            errors.append("WARNING: First row group is empty")

        # 5. Null checks on non-nullable columns
        for i, field in enumerate(actual_schema):
            if not field.nullable:
                col = table.column(field.name)
                if col.null_count > 0:
                    errors.append(f"NULL VIOLATION: {field.name} has {col.null_count} nulls")

    except Exception as e:
        errors.append(f"READ ERROR: {e}")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Parquet file is valid")
    return True


validate_parquet("output.parquet", min_rows=1)
```

### QA Checklist

- [ ] Schema is explicit — no inferred `object` columns
- [ ] Timestamps use UTC timezone (`tz="UTC"`)
- [ ] Appropriate compression chosen for use case
- [ ] `write_statistics=True` set (enables predicate pushdown)
- [ ] Row group size appropriate (128MB default; smaller for high-filter workloads)
- [ ] Metadata readable without loading data
- [ ] Column names are lowercase snake_case (pipeline convention)
- [ ] No all-null columns (validate after write)
- [ ] DuckDB or pandas can read file without error
- [ ] Row count matches source data

### QA Loop

1. Write Parquet file
2. Run `validate_parquet()` — structural + schema check
3. Read back and compare row count to source
4. Spot-check 5 random rows against source data
5. Run benchmark if compression choice was not obvious
6. **Do not pass to pipeline until row count and schema validated**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `object` dtype columns | Mixed types or strings not cast | Cast explicitly before writing: `df['col'].astype(str)` |
| Timestamp timezone errors | Naive datetime (no tz) | Convert: `df['ts'] = df['ts'].dt.tz_localize('UTC')` |
| File too large | No compression | Use `compression='snappy'` or `'zstd'` |
| Slow filtered reads | No statistics written | Set `write_statistics=True` |
| Can't append to file | Parquet is immutable | Write new file; use partitioned dataset |
| Schema mismatch on read | Evolved schema across files | Use `pyarrow.dataset` which handles schema evolution |

---

## Dependencies

```bash
pip install pyarrow pandas duckdb

# Optional but recommended
pip install fastparquet    # alternative Parquet engine
pip install polars         # fast DataFrame library with native Parquet support
```
