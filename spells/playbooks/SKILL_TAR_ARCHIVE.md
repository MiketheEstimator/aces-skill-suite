---
name: tar-archive
description: "Use this skill any time a TAR archive is involved — creating, extracting, compressing, or automating .tar, .tar.gz, .tar.bz2, .tar.xz, or .tgz files. Triggers include: 'tar', 'tarball', '.tar.gz', '.tgz', 'tar archive', 'compress for Linux', 'Unix archive'. Covers CLI (tar), Python (tarfile), and automation/pipeline workflows."
---

# TAR Archive Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Create TAR (CLI) | [CLI Workflow](#cli-workflow) |
| Choose compression format | [Compression Format Reference](#compression-format-reference) |
| Extract / inspect | [Extraction & Inspection](#extraction--inspection) |
| Python automation | [Python Workflow](#python-workflow) |
| Streaming / piped archive | [Streaming & Pipes](#streaming--pipes) |
| Validate archive | [Validation & QA](#validation--qa) |

---

## Format Overview

TAR (Tape Archive) bundles files without compression. Compression is applied as a second layer:

| Extension | Compression | Speed | Ratio | Use Case |
|-----------|-------------|-------|-------|----------|
| `.tar` | None | Fastest | None | Bundling only; pipe to compressor separately |
| `.tar.gz` / `.tgz` | gzip | Fast | Good | General purpose — most common on Linux/macOS |
| `.tar.bz2` | bzip2 | Slow | Better | Smaller archives, slower to create |
| `.tar.xz` | xz (LZMA) | Slowest | Best | Maximum compression, distributions |
| `.tar.zst` | zstd | Fast | Best | Modern replacement — fast AND small |

> **Default recommendation:** Use `.tar.gz` for general work. Use `.tar.xz` when archive size is critical. Use `.tar.zst` when both speed and size matter (modern systems only).

---

## CLI Workflow

### Core Flags Reference

```
c  — create archive
x  — extract archive
t  — list contents
v  — verbose (show filenames)
f  — file (always required; specifies archive filename)
z  — gzip compression (.tar.gz)
j  — bzip2 compression (.tar.bz2)
J  — xz compression (.tar.xz)
--zstd — zstd compression (.tar.zst)
p  — preserve permissions
C  — change to directory before operation
```

### Create Archives

```bash
# .tar.gz — general purpose
tar -czf archive.tar.gz ./folder/

# .tar.gz from multiple sources
tar -czf deliverable.tar.gz ./reports/ ./drawings/ ./schedules/

# .tar.xz — maximum compression
tar -cJf archive.tar.xz ./folder/

# .tar.bz2
tar -cjf archive.tar.bz2 ./folder/

# .tar.zst — fast + small (requires zstd installed)
tar --zstd -cf archive.tar.zst ./folder/

# Uncompressed .tar (bundle only)
tar -cf archive.tar ./folder/

# Verbose — show files being added
tar -czvf archive.tar.gz ./folder/

# Exclude patterns
tar -czf archive.tar.gz ./folder/ \
  --exclude="*.tmp" \
  --exclude="*.log" \
  --exclude=".DS_Store" \
  --exclude="__pycache__" \
  --exclude=".git"

# Create from a file list
find ./folder/ -name "*.pdf" > filelist.txt
tar -czf pdfs_only.tar.gz --files-from=filelist.txt

# Preserve permissions and ownership (for system backups)
tar -czpf backup.tar.gz ./folder/

# Append files to existing .tar (uncompressed only)
tar -rf archive.tar newfile.txt
```

### Compression Format Reference

```bash
# Benchmark compression on your data (pick the right tool)
time tar -czf  test.tar.gz  ./folder/ && ls -lh test.tar.gz
time tar -cJf  test.tar.xz  ./folder/ && ls -lh test.tar.xz
time tar --zstd -cf test.tar.zst ./folder/ && ls -lh test.tar.zst
```

---

## Extraction & Inspection

```bash
# List contents (no extraction)
tar -tzf archive.tar.gz       # gzip
tar -tjf archive.tar.bz2      # bzip2
tar -tJf archive.tar.xz       # xz
tar -tf  archive.tar          # uncompressed

# Verbose listing with details
tar -tzvf archive.tar.gz

# Extract to current directory
tar -xzf archive.tar.gz

# Extract to specific directory
tar -xzf archive.tar.gz -C ./output/

# Extract and create output directory if needed
mkdir -p ./output/ && tar -xzf archive.tar.gz -C ./output/

# Extract single file
tar -xzf archive.tar.gz folder/specific_file.pdf

# Extract single file to specific directory
tar -xzf archive.tar.gz -C ./output/ folder/specific_file.pdf

# Extract preserving permissions
tar -xzpf archive.tar.gz -C ./output/

# Auto-detect compression (modern tar)
tar -xf archive.tar.gz -C ./output/   # -x without compression flag = auto-detect
```

---

## Streaming & Pipes

TAR's native streaming makes it ideal for pipelines:

```bash
# Create and pipe directly to remote server (no local temp file)
tar -czf - ./folder/ | ssh user@server "cat > /remote/path/archive.tar.gz"

# Extract directly from remote
ssh user@server "cat /remote/archive.tar.gz" | tar -xzf - -C ./output/

# Pipe through encryption (GPG)
tar -czf - ./folder/ | gpg --symmetric --cipher-algo AES256 -o archive.tar.gz.gpg

# Pipe through 7-Zip encryption
tar -cf - ./folder/ | 7z a -si -mhe=on -p"password" archive.tar.7z

# Pipe to progress monitor
tar -czf - ./folder/ | pv > archive.tar.gz

# Transfer between directories preserving attributes
tar -cf - -C /source/dir . | tar -xf - -C /dest/dir/

# Estimate uncompressed size before creating archive
tar -cf /dev/null --totals ./folder/ 2>&1 | grep "Total bytes"
```

---

## Python Workflow

### Create TAR Archive

```python
import tarfile
from pathlib import Path

def create_tar(output_path: str, source_dirs: list = None,
               source_files: list = None, compression: str = 'gz'):
    """
    Create a TAR archive.

    Args:
        output_path:  Path for output file (e.g. 'archive.tar.gz')
        source_dirs:  List of directories to include
        source_files: Individual files to include at archive root
        compression:  'gz' | 'bz2' | 'xz' | '' (none)
    """
    mode = f'w:{compression}' if compression else 'w'

    with tarfile.open(output_path, mode) as tf:

        if source_dirs:
            for source_dir in source_dirs:
                base = Path(source_dir)
                tf.add(base, arcname=base.name)
                print(f"  Added dir:  {base.name}/")

        if source_files:
            for f in source_files:
                tf.add(f, arcname=Path(f).name)
                print(f"  Added file: {Path(f).name}")

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"\nCreated: {output_path} ({size_mb:.2f} MB)")


# Examples
create_tar('deliverable.tar.gz',  source_dirs=['./reports', './drawings'])
create_tar('deliverable.tar.xz',  source_dirs=['./reports'], compression='xz')
create_tar('bundle.tar',          source_dirs=['./folder'],  compression='')
```

### Create TAR with Exclusion Filter

```python
import tarfile
from pathlib import Path

EXCLUDE_PATTERNS = {'.DS_Store', '__pycache__', '.git', '.env', '*.tmp', '*.log'}

def should_exclude(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    name = Path(tarinfo.name).name
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return None
        elif name == pattern:
            return None
    return tarinfo

with tarfile.open('clean_archive.tar.gz', 'w:gz') as tf:
    tf.add('./project/', arcname='project', filter=should_exclude)

print("Archive created with exclusions applied")
```

### Extract TAR Archive

```python
import tarfile

def extract_tar(archive_path: str, output_dir: str,
                safe: bool = True):
    """
    Extract TAR archive.

    Args:
        archive_path: Path to .tar.gz / .tar.xz / .tar etc.
        output_dir:   Destination directory
        safe:         If True, block path traversal attacks (recommended)
    """
    with tarfile.open(archive_path, 'r:*') as tf:  # r:* = auto-detect compression

        if safe:
            # Block path traversal (e.g. ../../etc/passwd)
            members = []
            for member in tf.getmembers():
                if '..' in member.name or member.name.startswith('/'):
                    print(f"  SKIPPED (unsafe path): {member.name}")
                    continue
                members.append(member)
            tf.extractall(path=output_dir, members=members)
        else:
            tf.extractall(path=output_dir)

    print(f"Extracted to: {output_dir}")


extract_tar('archive.tar.gz', './output/')
```

### Inspect TAR Archive

```python
import tarfile

with tarfile.open('archive.tar.gz', 'r:*') as tf:
    print(f"{'Name':60s} {'Size':>12s} {'Type':>10s}")
    print("-" * 86)
    for member in tf.getmembers():
        ftype = 'DIR' if member.isdir() else 'FILE' if member.isfile() else 'OTHER'
        size = f"{member.size:,}" if member.isfile() else '-'
        print(f"{member.name:60s} {size:>12s} {ftype:>10s}")
```

---

## Validation & QA

```bash
# List contents — confirms archive is readable
tar -tzf archive.tar.gz

# Verbose list — check file paths and sizes
tar -tzvf archive.tar.gz

# Dry-run extract test (extract to /dev/null — no disk write)
tar -xzf archive.tar.gz -C /dev/null && echo "PASS: Archive readable"
```

```python
import tarfile
from pathlib import Path

def validate_tar(archive_path: str, expected_files: list = None) -> bool:
    errors = []

    try:
        with tarfile.open(archive_path, 'r:*') as tf:
            members = tf.getmembers()
            files = [m for m in members if m.isfile()]
            dirs  = [m for m in members if m.isdir()]

            print(f"Files:       {len(files)}")
            print(f"Directories: {len(dirs)}")

            # Zero-byte check
            for m in files:
                if m.size == 0:
                    errors.append(f"WARNING: Zero-byte file: {m.name}")

            # Path traversal safety check
            for m in members:
                if '..' in m.name or m.name.startswith('/'):
                    errors.append(f"SECURITY: Unsafe path in archive: {m.name}")

            # Expected files check
            if expected_files:
                archive_names = {m.name for m in members}
                for expected in expected_files:
                    if expected not in archive_names:
                        errors.append(f"MISSING: {expected}")

            # Size report
            total = sum(m.size for m in files)
            compressed = Path(archive_path).stat().st_size
            if total > 0:
                ratio = (1 - compressed / total) * 100
                print(f"Uncompressed: {total/1024/1024:.1f} MB")
                print(f"Compressed:   {compressed/1024/1024:.1f} MB")
                print(f"Ratio:        {ratio:.1f}%")

    except Exception as e:
        errors.append(f"ERROR opening archive: {e}")

    if errors:
        for e in errors:
            print(e)
        return False

    print("PASS: Archive is valid")
    return True


validate_tar('deliverable.tar.gz', expected_files=[
    'reports/schedule.pdf',
    'drawings/site_plan.pdf'
])
```

### QA Loop

1. Create archive
2. Run `tar -tzf` to confirm it lists without error
3. Run Python validation with expected file list
4. Spot-check: extract one file, confirm it opens correctly
5. Check for path traversal warnings (security check)
6. Verify uncompressed size matches source directory size
7. **Do not distribute until PASS on all checks**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `gzip: stdin: not in gzip format` | Wrong flag for compression type | Use `tar -xf` (auto-detect) or match flag to format |
| Files extracted with wrong paths | Archive created from wrong base directory | Use `-C` to set base: `tar -czf archive.tar.gz -C /base/dir .` |
| `Cannot open: No such file` on append | Tried to append to compressed archive | Append only works on uncompressed `.tar`; decompress first |
| Path traversal warning | Archive contains `../` paths | Always use `safe=True` in Python extraction |
| Large archive is slow to create | Using `xz` compression | Switch to `gz` or `zstd` for speed |
| `.tar.gz` won't open on Windows | No native support | Recipient needs 7-Zip or WinRAR; or send `.zip` instead |
| Permissions wrong after extract | `-p` flag not used | Extract with `tar -xzpf` to preserve permissions |

---

## Dependencies

```bash
# CLI — pre-installed on Linux/macOS
tar --version

# Install zstd support (if needed)
sudo apt install zstd        # Linux
brew install zstd            # macOS

# Python — stdlib, no install needed
import tarfile               # built-in

# Optional: progress bar for large archives
pip install tqdm
```
