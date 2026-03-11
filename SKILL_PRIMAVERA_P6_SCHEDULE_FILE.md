---
name: p6-schedule-export
description: "Use this skill any time a Primavera P6 schedule file is involved — as input, output, or both. Covers XER export, XML (P6 PMXML), PDF schedule reports, Excel-based schedule exports, and batch CLI operations. Trigger when the user mentions 'P6', 'Primavera', 'XER file', 'schedule export', 'baseline export', 'resource export', or any construction/engineering schedule deliverable. Architecture/Construction context."
---

# Primavera P6 Schedule Export Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Export XER from P6 client | [XER Export Workflow](#xer-export-workflow) |
| Export P6 PMXML | [PMXML Export Workflow](#pmxml-export-workflow) |
| Batch / headless export | [CLI & Automation](#cli--automation) |
| Validate XER file | [Validation & QA](#validation--qa) |
| Convert / transform XER | [Conversion Tools](#conversion-tools) |
| Read / parse XER in Python | [Parsing XER in Python](#parsing-xer-in-python) |

---

## File Format Overview

| Format | Extension | Use Case |
|--------|-----------|----------|
| P6 Native Export | `.xer` | Standard inter-system exchange, contractor submittals |
| P6 XML | `.xml` (PMXML) | Oracle-standard, richer metadata, preferred for integrations |
| Excel Export | `.xlsx` | Owner reporting, non-P6 stakeholders |
| PDF Report | `.pdf` | Contractual schedule submittals, baseline records |
| MPX / MPP | `.mpx` | Legacy MS Project interchange |

---

## XER Export Workflow

### From P6 Professional Client (GUI)

```
File → Export → Primavera PM - (XER)
  └─ Select Projects to export
  └─ Export Type: Project
  └─ File Name: [ProjectCode]_[BaselineRev]_[YYYYMMDD].xer
  └─ Click Finish
```

**Naming convention (Architecture/Construction):**
```
[ProjectNo]_[Contractor]_[ScheduleType]_[Rev]_[YYYYMMDD].xer
Example: 2401_ACME_BL01_R3_20240315.xer
```

### Export Options Checklist

- [ ] Include all project data (WBS, Activities, Resources, Relationships)
- [ ] Include Baselines — select which baselines to embed
- [ ] Include Resource Assignments if resource-loaded
- [ ] Include Calendars
- [ ] Include User Defined Fields (UDFs) if used
- [ ] Currency: confirm project currency before export
- [ ] Admin categories: include if transferring to new database

---

## PMXML Export Workflow

### From P6 Professional Client

```
File → Export → Primavera PM - (XML)
  └─ Select Projects
  └─ Options: check "Export Baselines", "Export Resources"
  └─ File Name: [ProjectCode]_[YYYYMMDD].xml
```

### From P6 EPPM (Web)

```
Administration → Export Projects
  └─ Format: Primavera P6 (PMXML)
  └─ Select project(s)
  └─ Download
```

**PMXML is preferred over XER when:**
- Integrating with Oracle Primavera Cloud
- Using API-based ingestion pipelines
- Preserving all metadata fields

---

## CLI & Automation

### P6 Database Direct Export (Oracle)

```bash
# Export XER via P6 API wrapper (requires P6 SDK or web services)
# P6 Professional must be installed; use StorePass for credentials

# Using p6-xer-tools (community Python wrapper)
pip install p6xer

python - <<EOF
from p6xer import P6XerExporter
exporter = P6XerExporter(
    host='your-p6-server',
    port=8206,
    username='admin',
    password='password',
    database='PMDB'
)
exporter.export_project(project_id='PROJECT_CODE', output_path='./output.xer')
EOF
```

### Headless XER Generation from Existing Data

```bash
# Install xerparser for reading/writing XER programmatically
pip install xerparser

python - <<EOF
from xerparser import Xer

# Read existing XER
with open('source.xer', encoding='utf-8-sig', errors='ignore') as f:
    xer = Xer(f.read())

# Inspect projects
for project in xer.projects:
    print(project.proj_short_name, project.last_recalc_date)

# Inspect activities
for task in xer.tasks:
    print(task.task_code, task.task_name, task.target_drtn_hr_cnt)
EOF
```

### Batch Export via PowerShell (Windows P6 Client)

```powershell
# Automate P6 GUI export via COM (requires P6 Pro installed)
$p6 = New-Object -ComObject "PrimaveraP6.Application"
$p6.Login("admin", "password", "PMDB")
$project = $p6.Projects.Open("PROJECT_CODE")
$project.Export("C:\exports\output.xer", "XER")
$p6.Logout()
```

---

## Conversion Tools

### XER → Excel (Python)

```bash
pip install xerparser openpyxl pandas

python - <<EOF
import pandas as pd
from xerparser import Xer

with open('schedule.xer', encoding='utf-8-sig', errors='ignore') as f:
    xer = Xer(f.read())

tasks = [{
    'Activity ID': t.task_code,
    'Activity Name': t.task_name,
    'Original Duration': round(t.target_drtn_hr_cnt / 8, 1),
    'Start': t.target_start_date,
    'Finish': t.target_end_date,
    'WBS': t.wbs.wbs_name if t.wbs else '',
    'Status': t.status_code
} for t in xer.tasks]

df = pd.DataFrame(tasks)
df.to_excel('schedule_export.xlsx', index=False)
print(f"Exported {len(tasks)} activities")
EOF
```

### XER → CSV

```bash
python - <<EOF
import csv
from xerparser import Xer

with open('schedule.xer', encoding='utf-8-sig', errors='ignore') as f:
    xer = Xer(f.read())

with open('activities.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ID','Name','Duration_Days','Start','Finish','WBS','Type'])
    for t in xer.tasks:
        writer.writerow([
            t.task_code, t.task_name,
            round(t.target_drtn_hr_cnt / 8, 1),
            t.target_start_date, t.target_end_date,
            t.wbs.wbs_name if t.wbs else '',
            t.task_type
        ])
EOF
```

### XER → PMXML (Oracle Tool)

```bash
# Using Oracle's P6 Integration API (requires licensed install)
# XER to PMXML via P6 web services endpoint:
curl -X POST https://p6server:8206/p6ws/services/ProjectService \
  -H "Content-Type: text/xml" \
  -d @export_request.xml \
  -o output.xml
```

---

## Parsing XER in Python

```bash
pip install xerparser
```

```python
from xerparser import Xer
from pathlib import Path

def load_xer(filepath: str) -> Xer:
    """Load XER with encoding fallback."""
    path = Path(filepath)
    for encoding in ['utf-8-sig', 'latin-1', 'cp1252']:
        try:
            with open(path, encoding=encoding, errors='ignore') as f:
                return Xer(f.read())
        except Exception:
            continue
    raise ValueError(f"Could not parse XER: {filepath}")

xer = load_xer('schedule.xer')

# Key collections
print(f"Projects:    {len(xer.projects)}")
print(f"Activities:  {len(xer.tasks)}")
print(f"WBS nodes:   {len(xer.wbss)}")
print(f"Resources:   {len(xer.resources)}")
print(f"Calendars:   {len(xer.calendars)}")
print(f"Baselines:   {len(xer.projects)}")  # baselines are stored as projects
```

---

## Validation & QA

### Structural Checks

```bash
pip install xerparser

python - <<EOF
from xerparser import Xer

with open('schedule.xer', encoding='utf-8-sig', errors='ignore') as f:
    xer = Xer(f.read())

errors = []

# Check for activities with no duration
no_duration = [t for t in xer.tasks if t.target_drtn_hr_cnt == 0 and t.task_type != 'TT_Mile']
if no_duration:
    errors.append(f"WARNING: {len(no_duration)} activities with zero duration (excluding milestones)")

# Check for missing relationships (isolated activities)
task_ids = {t.task_id for t in xer.tasks}
linked = set()
for rel in xer.taskpreds:
    linked.add(rel.task_id)
    linked.add(rel.pred_task_id)
isolated = task_ids - linked
if isolated:
    errors.append(f"WARNING: {len(isolated)} activities have no relationships")

# Check for missing WBS
no_wbs = [t for t in xer.tasks if not t.wbs]
if no_wbs:
    errors.append(f"ERROR: {len(no_wbs)} activities missing WBS assignment")

if errors:
    for e in errors: print(e)
else:
    print("PASS: No structural issues found")
EOF
```

### Schedule Logic Checks

```bash
python - <<EOF
from xerparser import Xer

with open('schedule.xer', encoding='utf-8-sig', errors='ignore') as f:
    xer = Xer(f.read())

# Check for activities missing predecessors (except project start)
no_pred = []
pred_tasks = {r.task_id for r in xer.taskpreds}
for t in xer.tasks:
    if t.task_id not in pred_tasks and t.task_type not in ('TT_LOE', 'TT_WBS'):
        no_pred.append(t.task_code)

print(f"Activities with no predecessor: {len(no_pred)}")
if no_pred[:10]:
    print("  First 10:", no_pred[:10])

# Check for activities missing successors
no_succ = []
succ_tasks = {r.pred_task_id for r in xer.taskpreds}
for t in xer.tasks:
    if t.task_id not in succ_tasks and t.task_type not in ('TT_LOE', 'TT_WBS'):
        no_succ.append(t.task_code)

print(f"Activities with no successor: {len(no_succ)}")
EOF
```

### QA Verification Loop

1. Export XER from P6
2. Run structural checks → fix in P6 → re-export
3. Run logic checks → resolve open ends → re-export
4. Parse and verify activity count matches P6 GUI count
5. Spot-check 5 random activities: ID, name, duration, dates
6. Confirm baselines embedded if required by contract
7. **Do not submit until zero ERROR-level findings**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| XER opens blank in P6 | Wrong P6 version | Check XER header `ERMHDR` version line |
| Encoding errors on parse | Non-UTF-8 characters in activity names | Open with `latin-1` or `cp1252` |
| Missing resources on import | Resources not included in export | Re-export with "Include Resources" checked |
| Calendars lost | Admin calendars not exported | Export admin data with project |
| Baseline not visible | Baseline not selected during export | Re-export, explicitly select baselines |
| Activity count mismatch | WBS summary activities counted differently | Exclude `TT_WBS` type from count |

---

## Dependencies

```bash
pip install xerparser          # XER read/write/parse
pip install pandas openpyxl   # Excel conversion
pip install lxml               # PMXML/XML processing
```

**Licensed software required for full export:**
- Primavera P6 Professional (client GUI export)
- Primavera P6 EPPM (web export)
- Oracle P6 Integration API (headless/API export)

**Community tools (no license required for parsing):**
- `xerparser` — read/validate/transform XER files
- `p6xer` — lightweight XER utilities
