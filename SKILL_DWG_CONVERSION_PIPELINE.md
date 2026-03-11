---
name: dwg-conversion-pipeline
description: "Use this skill when converting between DWG and DXF formats, or processing .dwg files. Covers the ODA File Converter CLI pipeline, AutoCAD Script (.scr) generation, and batch conversion workflows. Trigger when .dwg output or DWG↔DXF conversion is required."
---

# DWG Conversion Pipeline + ODA File Converter CLI / AutoCAD Script SKILL

## Quick Reference

| Task | Tool |
|------|------|
| DXF → DWG | ODA File Converter CLI |
| DWG → DXF | ODA File Converter CLI |
| Batch conversion | ODA File Converter CLI (folder mode) |
| DWG processing scripted | AutoCAD Script (.scr) |
| DWG inspection | `ezdxf` (reads DWG in limited capacity) |
| DWG → PDF | ODA File Converter + print pipeline |

---

## ODA File Converter

ODA File Converter (formerly Teigha File Converter) is the primary open-source tool for DWG↔DXF conversion. It is a free CLI tool from the Open Design Alliance.

### Installation

```bash
# Ubuntu / Debian
# Download from: https://www.opendesign.com/guestfiles/oda_file_converter
# Install .deb package
sudo dpkg -i oda-file-converter_*.deb

# Verify
ODAFileConverter --version
# or
/usr/bin/ODAFileConverter --help
```

### Basic Syntax

```
ODAFileConverter <InputFolder> <OutputFolder> <OutputVersion> <OutputType> <RecurseSubfolders> <AuditFiles> [InputFilter]
```

| Parameter | Values | Notes |
|-----------|--------|-------|
| OutputVersion | `ACAD9` `ACAD10` `ACAD12` `ACAD14` `ACAD2000` `ACAD2004` `ACAD2007` `ACAD2010` `ACAD2013` `ACAD2018` | DWG version |
| OutputType | `DWG` `DXF` `DXB` | Output format |
| RecurseSubfolders | `0` `1` | Recurse into subfolders |
| AuditFiles | `0` `1` | Audit/repair files during conversion |

---

## DXF → DWG Conversion

```bash
# Single file conversion
# ODA works on folders — create temp dirs
mkdir -p /tmp/oda_input /tmp/oda_output
cp output.dxf /tmp/oda_input/

ODAFileConverter \
  /tmp/oda_input \
  /tmp/oda_output \
  ACAD2018 \
  DWG \
  0 \
  1

cp /tmp/oda_output/output.dwg ./output.dwg
echo "DWG saved: output.dwg"
```

---

## DWG → DXF Conversion

```bash
mkdir -p /tmp/oda_input /tmp/oda_output
cp input.dwg /tmp/oda_input/

ODAFileConverter \
  /tmp/oda_input \
  /tmp/oda_output \
  ACAD2018 \
  DXF \
  0 \
  1

cp /tmp/oda_output/input.dxf ./input_converted.dxf
```

---

## Batch Conversion (Python Wrapper)

```python
import subprocess
import shutil
from pathlib import Path

def oda_convert(input_files, output_dir, output_format="DWG", 
                dwg_version="ACAD2018", audit=True):
    """
    Convert DXF/DWG files using ODA File Converter.
    input_files: list of file paths
    output_format: "DWG" or "DXF"
    dwg_version: "ACAD2018", "ACAD2013", "ACAD2010", etc.
    """
    tmp_in = Path("/tmp/oda_batch_input")
    tmp_out = Path("/tmp/oda_batch_output")
    tmp_in.mkdir(parents=True, exist_ok=True)
    tmp_out.mkdir(parents=True, exist_ok=True)

    # Copy input files to temp dir
    for f in input_files:
        shutil.copy(f, tmp_in / Path(f).name)

    # Run ODA File Converter
    result = subprocess.run([
        "ODAFileConverter",
        str(tmp_in),
        str(tmp_out),
        dwg_version,
        output_format,
        "0",  # Don't recurse
        "1" if audit else "0"
    ], capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"ODA stderr: {result.stderr}")
        raise RuntimeError(f"ODA conversion failed: {result.returncode}")

    # Copy outputs
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_files = []
    ext = ".dwg" if output_format == "DWG" else ".dxf"
    for f in tmp_out.glob(f"*{ext}"):
        dest = Path(output_dir) / f.name
        shutil.copy(f, dest)
        output_files.append(dest)
        print(f"Converted: {f.name} → {dest}")

    # Cleanup
    shutil.rmtree(tmp_in)
    shutil.rmtree(tmp_out)
    return output_files
```

---

## AutoCAD Script (.scr) Generation

AutoCAD scripts automate operations when ODA isn't available or AutoCAD is accessible.

```python
def generate_autocad_script(operations):
    """
    Generate a .scr script for AutoCAD batch execution.
    operations: list of (command, args) tuples
    """
    lines = []
    for cmd, args in operations:
        lines.append(f"{cmd} {args}")
    lines.append("QUIT Y")  # Close without save prompt
    return "\n".join(lines)

# Example: open DXF, set layer, save as DWG
script = generate_autocad_script([
    ("OPEN", "input.dxf"),
    ("LAYER", "S A-WALL "),       # Set current layer
    ("ZOOM", "E"),                 # Zoom extents
    ("SAVEAS", "DWG2018 output.dwg"),
])

with open("process.scr", "w") as f:
    f.write(script)

# Run with AutoCAD (if installed)
# acad.exe /b process.scr
```

### Common AutoCAD Script Commands

```
OPEN <filepath>          ; Open file
SAVEAS DWG2018 <path>    ; Save as DWG
QSAVE                    ; Quick save
LAYER S <name>           ; Set current layer
ZOOM E                   ; Zoom extents
PURGE A                  ; Purge all unused
AUDIT Y                  ; Audit and fix
PLOT                     ; Plot to printer/PDF
QUIT Y                   ; Quit, discard changes
```

---

## Verify Converted DWG/DXF

```bash
# Check converted DXF is valid
python -c "
import ezdxf
doc = ezdxf.readfile('output.dxf')
auditor = doc.audit()
print(f'DXF Version: {doc.dxfversion}')
print(f'Entities: {len(list(doc.modelspace()))}')
print(f'Audit errors: {len(auditor.errors)}')
for e in auditor.errors[:5]:
    print(f'  {e}')
"

# File size sanity check
ls -lh output.dwg output.dxf 2>/dev/null

# Check ODA output log
# ODA writes *.err files for failed conversions
ls /tmp/oda_batch_output/*.err 2>/dev/null && echo "Errors found" || echo "No errors"
```

---

## DWG Version Compatibility Matrix

| DWG Version | AutoCAD Version | Notes |
|-------------|-----------------|-------|
| ACAD2018 | 2018–2026 | Current default |
| ACAD2013 | 2013–2017 | Good compatibility |
| ACAD2010 | 2010–2012 | Older projects |
| ACAD2007 | 2007–2009 | Legacy |
| ACAD2000 | 2000–2006 | Maximum compatibility |

---

## QA Checklist

- [ ] ODA conversion completed without `.err` files
- [ ] Output file size comparable to input (within 50% — extreme differences indicate corruption)
- [ ] DXF round-trip readable by ezdxf
- [ ] Layer count preserved after conversion
- [ ] Entity count preserved after conversion
- [ ] Text and dimensions not corrupted
- [ ] External references (XREFs) resolved or noted as missing
- [ ] DWG version matches target software requirement

---

## Common Mistakes to Avoid

- Running ODA on files rather than folders (it only accepts folder paths)
- Forgetting to clear temp input/output folders between runs (causes mixed results)
- Targeting too-old DWG versions (ACAD9/10/12 may lose data)
- Not auditing during conversion (corrupted inputs silently produce bad outputs)
- Ignoring `.err` files in output folder (they signal conversion failures)

---

## Dependencies

```bash
# ODA File Converter: https://www.opendesign.com/guestfiles/oda_file_converter
# Free download (requires registration)
# Install .deb on Ubuntu: sudo dpkg -i oda-file-converter_*.deb

pip install ezdxf --break-system-packages  # for DXF verification
```
