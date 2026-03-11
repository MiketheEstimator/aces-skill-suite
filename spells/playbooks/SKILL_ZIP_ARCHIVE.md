---
name: zip-archive
description: "Use this skill any time a ZIP archive is involved — creating, reading, extracting, validating, or automating ZIP files. Triggers include: 'zip', 'compress', 'archive', 'bundle files', 'package deliverable', '.zip output', 'extract zip', 'unzip'. Covers single-file zips, structured multi-folder archives, password-protected zips, and batch/CLI workflows."
---

# Structured ZIP Archive Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Create ZIP (CLI) | [CLI Workflow](#cli-workflow) |
| Create ZIP (Python) | [Python Workflow](#python-workflow) |
| Extract / inspect | [Extraction & Inspection](#extraction--inspection) |
| Password-protect | [Password Protection](#password-protection) |
| Validate archive | [Validation & QA](#validation--qa) |
| Structured deliverable packaging | [Deliverable Packaging](#deliverable-packaging) |

---

## Format Overview

| Feature | ZIP Support |
|---------|-------------|
| Compression | Deflate, Store, BZIP2, LZMA |
| Encryption | ZipCrypto (weak), AES-256 (7-Zip extension) |
| Max file size | 4 GB (standard) / unlimited (ZIP64) |
| Max archive size | 4 GB (standard) / unlimited (ZIP64) |
| OS compatibility | Universal — Windows, macOS, Linux, mobile |
| Streaming | Supported |

> **Note:** For strong encryption, use the 7-Zip skill instead. Native ZIP encryption (ZipCrypto) is not cryptographically secure.

---

## CLI Workflow

### Linux / macOS

```bash
# Create ZIP from folder
zip -r archive.zip ./folder/

# Create ZIP from specific files
zip archive.zip file1.pdf file2.xlsx file3.docx

# Create ZIP preserving folder structure
zip -r deliverable.zip ./reports/ ./drawings/ ./schedules/

# Add files to existing ZIP
zip -u archive.zip newfile.pdf

# Create ZIP excluding unwanted files
zip -r archive.zip ./project/ --exclude "*.tmp" --exclude "*/__pycache__/*" --exclude "*.DS_Store"

# Verbose output — see what's being added
zip -rv archive.zip ./folder/

# ZIP64 for large archives (>4GB)
zip -r --compression-method deflate archive.zip ./large_folder/
```

### Windows (PowerShell)

```powershell
# Compress folder to ZIP
Compress-Archive -Path "C:\project\folder" -DestinationPath "C:\output\archive.zip"

# Compress multiple items
Compress-Archive -Path "C:\reports\*", "C:\drawings\*" -DestinationPath "C:\output\deliverable.zip"

# Update existing ZIP
Compress-Archive -Path "C:\new_file.pdf" -DestinationPath "C:\output\archive.zip" -Update

# Force overwrite
Compress-Archive -Path "C:\folder\*" -DestinationPath "C:\output\archive.zip" -Force
```

### Windows (7-Zip CLI for ZIP format)

```bash
# Create ZIP using 7-Zip engine (better compression than built-in)
7z a -tzip archive.zip ./folder/

# Maximum compression
7z a -tzip -mx=9 archive.zip ./folder/

# Exclude files
7z a -tzip archive.zip ./folder/ -x!*.tmp -x!*.log
```

---

## Python Workflow

### Create ZIP

```python
import zipfile
import os
from pathlib import Path

def create_zip(output_path: str, source_dirs: list, source_files: list = None):
    """
    Create a structured ZIP archive.
    
    Args:
        output_path: Path for output .zip file
        source_dirs: List of directories to include (preserves structure)
        source_files: Optional list of individual files to include at root
    """
    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        
        # Add directories
        for source_dir in source_dirs:
            base = Path(source_dir)
            for file_path in base.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(base.parent)
                    zf.write(file_path, arcname)
                    print(f"  Added: {arcname}")
        
        # Add individual files at root
        if source_files:
            for f in source_files:
                zf.write(f, Path(f).name)
                print(f"  Added: {Path(f).name}")
    
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"\nArchive created: {output_path} ({size_mb:.2f} MB)")

# Example usage
create_zip(
    output_path='project_deliverable.zip',
    source_dirs=['./reports', './drawings', './schedules'],
    source_files=['./README.txt', './transmittal.pdf']
)
```

### Create ZIP with Internal Structure

```python
import zipfile
from pathlib import Path
import io

def create_structured_zip(output_path: str, file_map: dict):
    """
    Create ZIP with explicit internal folder structure.
    
    file_map: {
        'internal/path/filename.ext': '/local/path/filename.ext'
    }
    """
    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for archive_path, local_path in file_map.items():
            zf.write(local_path, archive_path)
            print(f"  {local_path} → {archive_path}")

# Example: structured construction deliverable
file_map = {
    '01_Reports/schedule_report.pdf':     './output/schedule_report.pdf',
    '01_Reports/cost_report.xlsx':        './output/cost_report.xlsx',
    '02_Drawings/site_plan_A101.pdf':     './drawings/site_plan.pdf',
    '03_Schedules/baseline_BL01.xer':     './schedules/baseline.xer',
    'Transmittal.pdf':                    './transmittal.pdf',
}

create_structured_zip('2401_ACME_Deliverable_R1.zip', file_map)
```

---

## Extraction & Inspection

### CLI

```bash
# List contents without extracting
unzip -l archive.zip

# Test archive integrity
unzip -t archive.zip

# Extract to specific directory
unzip archive.zip -d ./output/

# Extract single file
unzip archive.zip "folder/specific_file.pdf" -d ./output/

# Extract without overwriting existing files
unzip -n archive.zip -d ./output/
```

### Python

```python
import zipfile

# Inspect contents
with zipfile.ZipFile('archive.zip', 'r') as zf:
    for info in zf.infolist():
        print(f"{info.filename:60s} {info.file_size:>12,} bytes  {info.compress_size:>12,} compressed")

# Extract all
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zf.extractall('./output/')

# Extract specific file
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zf.extract('folder/file.pdf', './output/')
```

---

## Password Protection

> ⚠️ Native ZIP encryption (ZipCrypto) is weak. For secure password protection use the **Secure 7-Zip Archive** skill.

```python
# Python — basic ZIP password (ZipCrypto, NOT secure)
import zipfile

with zipfile.ZipFile('protected.zip', 'w') as zf:
    zf.setpassword(b'password123')
    zf.write('file.pdf', pwd=b'password123')

# CLI with password (also ZipCrypto)
zip -P password123 protected.zip file.pdf
```

---

## Deliverable Packaging

### Construction Project Transmittal Structure

```
[ProjectNo]_[Contractor]_[Deliverable]_[Rev]_[YYYYMMDD].zip
├── 00_Transmittal/
│   └── Transmittal_[Rev].pdf
├── 01_Schedules/
│   ├── [ProjectNo]_Schedule_BL01_[YYYYMMDD].xer
│   └── [ProjectNo]_Schedule_BL01_[YYYYMMDD].pdf
├── 02_Reports/
│   └── ScheduleNarrative_[Rev].pdf
├── 03_Drawings/               (if applicable)
└── README.txt
```

```python
# Auto-generate transmittal ZIP with datestamp
from datetime import datetime
import zipfile, os
from pathlib import Path

def package_transmittal(project_no, contractor, rev, source_map):
    date_str = datetime.now().strftime('%Y%m%d')
    zip_name = f"{project_no}_{contractor}_Deliverable_{rev}_{date_str}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for archive_path, local_path in source_map.items():
            if Path(local_path).exists():
                zf.write(local_path, archive_path)
            else:
                print(f"WARNING: Missing file: {local_path}")
    
    print(f"Packaged: {zip_name}")
    return zip_name
```

---

## Validation & QA

```bash
# CLI integrity test
unzip -t archive.zip
# Expected output: No errors detected in archive

# Check file count
unzip -l archive.zip | tail -1
```

```python
import zipfile
from pathlib import Path

def validate_zip(zip_path: str, expected_files: list = None) -> bool:
    """Full ZIP validation with optional expected file check."""
    errors = []
    
    # Test 1: Can open
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            
            # Test 2: Integrity check
            bad = zf.testzip()
            if bad:
                errors.append(f"CORRUPT: First bad file: {bad}")
            
            # Test 3: No zero-byte files (excluding directories)
            for info in zf.infolist():
                if not info.filename.endswith('/') and info.file_size == 0:
                    errors.append(f"WARNING: Zero-byte file: {info.filename}")
            
            # Test 4: Expected files present
            if expected_files:
                archive_files = {info.filename for info in zf.infolist()}
                for expected in expected_files:
                    if expected not in archive_files:
                        errors.append(f"MISSING: {expected}")
            
            # Test 5: Report size
            total = sum(i.file_size for i in zf.infolist())
            compressed = Path(zip_path).stat().st_size
            ratio = (1 - compressed/total) * 100 if total > 0 else 0
            print(f"Files: {len(zf.infolist())}  |  Uncompressed: {total/1024/1024:.1f} MB  |  Ratio: {ratio:.1f}%")
    
    except zipfile.BadZipFile as e:
        errors.append(f"BAD ZIP FILE: {e}")
    
    if errors:
        for e in errors: print(e)
        return False
    
    print("PASS: Archive is valid")
    return True

validate_zip('deliverable.zip', expected_files=[
    'Transmittal.pdf',
    '01_Schedules/baseline.xer'
])
```

### QA Loop

1. Create archive
2. Run `unzip -t` integrity test
3. Run Python validation with expected file list
4. Spot-check: extract one file, verify it opens correctly
5. Confirm archive size is reasonable (not suspiciously small)
6. **Do not distribute until PASS on all checks**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `BadZipFile` on open | Incomplete download / corruption | Re-create or re-download |
| Files missing after extract | Path separator issue on Windows | Use `zipfile` module; avoid `\` in paths |
| Archive too large | Incompressible files (PDFs, images already compressed) | Use `ZIP_STORED` for pre-compressed files |
| Unicode filename errors | Non-ASCII filenames | Ensure Python uses `UTF-8` encoding; add `allowZip64=True` |
| Nested ZIP inside ZIP | Accidental double-wrap | Check source paths before archiving |
| `.DS_Store` / `__pycache__` included | No exclusion filter | Add `--exclude` patterns or filter in Python |

---

## Dependencies

```bash
# Python stdlib — no install needed
import zipfile  # built-in

# CLI tools
# Linux: apt install zip unzip
# macOS: brew install zip (unzip built-in)
# Windows: built-in (PowerShell) or install 7-Zip for CLI

pip install tqdm   # optional: progress bar for large archives
```
