---
name: 7zip-secure-archive
description: "Use this skill any time a 7-Zip archive (.7z) is involved — creating, extracting, validating, or automating. Also use when strong AES-256 encryption is required on any archive format. Triggers include: '7z', '7-zip', 'encrypted archive', 'AES-256 archive', 'secure zip', 'password protected archive', '.7z output'. Covers CLI (7z), Python (py7zr), and batch workflows."
---

# Secure 7-Zip Archive Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Create .7z (CLI) | [CLI Workflow](#cli-workflow) |
| Create encrypted .7z | [Encryption Workflow](#encryption-workflow) |
| Create AES-256 encrypted ZIP | [Encrypted ZIP via 7-Zip](#encrypted-zip-via-7-zip) |
| Extract / inspect | [Extraction & Inspection](#extraction--inspection) |
| Python automation | [Python Workflow](#python-workflow) |
| Validate archive | [Validation & QA](#validation--qa) |

---

## Format Overview

| Feature | 7z Support |
|---------|------------|
| Compression | LZMA2 (default), LZMA, BZIP2, PPMd, Deflate |
| Encryption | AES-256 |
| Filename encryption | Yes (header encryption) |
| Max file/archive size | 16 EiB (no practical limit) |
| OS compatibility | Windows, macOS, Linux (p7zip) |
| Self-extracting | Supported |
| Solid archive | Supported (better compression ratios) |

> **7z with AES-256 is the correct choice whenever security matters.** Native ZIP encryption (ZipCrypto) is cryptographically broken — never rely on it for sensitive data.

---

## Installation

```bash
# Linux
sudo apt install p7zip-full           # Ubuntu/Debian
sudo yum install p7zip p7zip-plugins  # RHEL/CentOS

# macOS
brew install p7zip

# Windows (winget)
winget install 7zip.7zip

# Verify install
7z i
```

---

## CLI Workflow

### Basic Archive Creation

```bash
# Create .7z from a folder
7z a archive.7z ./folder/

# Create .7z from specific files
7z a archive.7z file1.pdf file2.xlsx file3.docx

# Create from multiple directories
7z a deliverable.7z ./reports/ ./drawings/ ./schedules/

# Maximum compression
7z a -mx=9 archive.7z ./folder/

# Exclude junk files
7z a archive.7z ./folder/ -x!*.tmp -x!*.log -x!*.DS_Store -x!*/__pycache__

# Verbose output (show files being added)
7z a -bb1 archive.7z ./folder/

# Split into volumes (e.g. 100MB parts for email/upload)
7z a -v100m archive.7z ./folder/
# Produces: archive.7z.001, archive.7z.002, ...
```

### Compression Level Reference

| Flag | Level | Use Case |
|------|-------|----------|
| `-mx=0` | Store (none) | Already-compressed files (PDFs, images) |
| `-mx=1` | Fastest | Quick packaging, large files |
| `-mx=5` | Normal (default) | General purpose |
| `-mx=7` | Maximum | Distribution archives |
| `-mx=9` | Ultra | Smallest size, slowest |

---

## Encryption Workflow

### AES-256 Encrypted .7z

```bash
# Encrypt — interactive password prompt (recommended)
7z a -mhe=on -p archive_secure.7z ./folder/
# -mhe=on  → encrypt headers (filenames hidden from directory listing)
# -p       → prompt for password interactively

# Encrypt with inline password (scripts only — see security note below)
7z a -mhe=on -p"StrongPassword123!" archive_secure.7z ./folder/
```

> ⚠️ **Security Note:** Inline passwords appear in shell history (`~/.bash_history`). In scripts, always use an environment variable or secrets manager:

```bash
# Safe approach — read password from environment variable
7z a -mhe=on -p"${ARCHIVE_PASSWORD}" archive_secure.7z ./folder/

# Generate a strong random password
python3 -c "import secrets; print(secrets.token_urlsafe(20))"
```

### Header Encryption Explained

```bash
# Without header encryption — filenames VISIBLE, contents encrypted
7z a -p"password" archive.7z ./folder/

# With header encryption — filenames AND contents encrypted
7z a -mhe=on -p"password" archive.7z ./folder/
```

Use `-mhe=on` whenever filename exposure is a risk (e.g. sensitive project names, personnel files).

---

## Encrypted ZIP via 7-Zip

When recipients can't open .7z files, create an AES-256 encrypted ZIP instead:

```bash
# AES-256 encrypted ZIP — real security, universal compatibility
7z a -tzip -mem=AES256 -p"StrongPassword!" secure_archive.zip ./folder/
```

| Format | Encryption | Filenames Hidden | Compatibility |
|--------|-----------|-----------------|---------------|
| `.7z` + `-mhe=on` | AES-256 | Yes | Requires 7-Zip |
| `.7z` | AES-256 | No | Requires 7-Zip |
| `.zip` via 7-Zip | AES-256 | No | Universal |
| `.zip` native | ZipCrypto ⚠️ | No | Universal (insecure) |

---

## Extraction & Inspection

```bash
# List contents
7z l archive.7z

# List with full technical detail
7z l -slt archive.7z

# Test archive integrity (no extraction)
7z t archive.7z

# Test encrypted archive
7z t -p"password" archive_secure.7z

# Extract — preserving folder structure
7z x archive.7z -o./output/

# Extract encrypted archive
7z x -p"password" archive_secure.7z -o./output/

# Extract flat (no subfolders, all files to one directory)
7z e archive.7z -o./output/

# Extract single file
7z x archive.7z "subfolder/specific_file.pdf" -o./output/
```

---

## Python Workflow

```bash
pip install py7zr
```

### Create .7z Archive

```python
import py7zr
import os
from pathlib import Path

def create_7z(output_path: str, source_dirs: list = None,
              source_files: list = None, password: str = None,
              compression_level: int = 5):
    """
    Create a .7z archive with optional AES-256 encryption.

    Args:
        output_path:       Path for output .7z file
        source_dirs:       Directories to archive (structure preserved)
        source_files:      Individual files added at archive root
        password:          AES-256 encryption password (None = no encryption)
        compression_level: 1 (fast) to 9 (ultra), default 5
    """
    filters = [{"id": py7zr.FILTER_LZMA2, "preset": compression_level}]

    with py7zr.SevenZipFile(output_path, 'w', password=password, filters=filters) as zf:

        if source_dirs:
            for source_dir in source_dirs:
                base = Path(source_dir)
                zf.writeall(base, arcname=base.name)
                print(f"  Added dir:  {base.name}/")

        if source_files:
            for f in source_files:
                zf.write(f, Path(f).name)
                print(f"  Added file: {Path(f).name}")

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    enc = " [AES-256 encrypted]" if password else ""
    print(f"\nCreated: {output_path} ({size_mb:.2f} MB){enc}")


# Unencrypted
create_7z('deliverable.7z', source_dirs=['./reports', './drawings'])

# AES-256 encrypted — password from environment variable
create_7z(
    'deliverable_secure.7z',
    source_dirs=['./reports', './drawings', './schedules'],
    source_files=['./transmittal.pdf'],
    password=os.environ.get('ARCHIVE_PASSWORD')
)
```

### Extract .7z Archive

```python
import py7zr, os

def extract_7z(archive_path: str, output_dir: str, password: str = None):
    with py7zr.SevenZipFile(archive_path, 'r', password=password) as zf:
        zf.extractall(path=output_dir)
    print(f"Extracted to: {output_dir}")

# Unencrypted
extract_7z('archive.7z', './output/')

# Encrypted
extract_7z('archive_secure.7z', './output/', password=os.environ.get('ARCHIVE_PASSWORD'))
```

### Inspect Archive

```python
import py7zr

with py7zr.SevenZipFile('archive.7z', 'r') as zf:
    for f in zf.list():
        size = f.uncompressed if not f.is_directory else 0
        print(f"{f.filename:60s} {size:>12,} bytes")

    info = zf.archiveinfo()
    print(f"\nMethod:           {info.method_names}")
    print(f"Encrypted:        {info.encrypted}")
    print(f"Header encrypted: {info.header_encrypted}")
    print(f"Solid:            {info.solid}")
```

---

## Validation & QA

```bash
# CLI integrity test
7z t archive.7z
# Pass output: Everything is Ok

# Test encrypted archive
7z t -p"password" archive_secure.7z
```

```python
import py7zr
from pathlib import Path

def validate_7z(archive_path: str, password: str = None,
                expected_files: list = None) -> bool:
    errors = []

    try:
        with py7zr.SevenZipFile(archive_path, 'r', password=password) as zf:

            info = zf.archiveinfo()
            file_list = zf.list()

            print(f"Files:            {len(file_list)}")
            print(f"Encrypted:        {info.encrypted}")
            print(f"Header encrypted: {info.header_encrypted}")

            # Zero-byte file check
            for f in file_list:
                if not f.is_directory and f.uncompressed == 0:
                    errors.append(f"WARNING: Zero-byte file: {f.filename}")

            # Expected files check
            if expected_files:
                archive_names = {f.filename for f in file_list}
                for expected in expected_files:
                    if expected not in archive_names:
                        errors.append(f"MISSING: {expected}")

            # Compression ratio
            total = sum(f.uncompressed for f in file_list if not f.is_directory)
            compressed = Path(archive_path).stat().st_size
            if total > 0:
                ratio = (1 - compressed / total) * 100
                print(f"Uncompressed:     {total/1024/1024:.1f} MB")
                print(f"Compressed:       {compressed/1024/1024:.1f} MB")
                print(f"Ratio:            {ratio:.1f}%")

    except Exception as e:
        errors.append(f"ERROR: {e}")

    if errors:
        for e in errors:
            print(e)
        return False

    print("PASS: Archive is valid")
    return True


validate_7z(
    'deliverable_secure.7z',
    password='your_password',
    expected_files=['reports/schedule.pdf', 'transmittal.pdf']
)
```

### QA Loop

1. Create archive
2. Run `7z t` integrity test
3. Run Python validation with expected file list
4. Spot-check: extract one file, confirm it opens correctly
5. If encrypted — verify a wrong password is correctly rejected
6. Confirm `-mhe=on` if filename privacy is required
7. **Do not distribute until PASS on all checks**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Wrong password` on extract | Typo or wrong key | Confirm password; check caps lock |
| Filenames visible despite encryption | `-mhe=on` not used | Re-create with `-mhe=on` flag |
| Recipient can't open .7z | 7-Zip not installed | Send as AES-256 ZIP instead (`-tzip -mem=AES256`) |
| Split volumes won't extract | Missing a volume part | All `.001`, `.002` etc. must be present |
| Very low compression ratio | Source files already compressed | Use `-mx=0` (store) for PDFs/images |
| py7zr password error on read | Wrong encoding | Ensure password is passed as `str`, not `bytes` |

---

## Dependencies

```bash
# CLI
sudo apt install p7zip-full   # Linux
brew install p7zip            # macOS
winget install 7zip.7zip      # Windows

# Python
pip install py7zr
```
