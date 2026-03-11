---
name: ms-project-schedule-file
description: "Use this skill when producing Microsoft Project .mpp or .xml files for construction scheduling. Since .mpp is proprietary, this skill covers the XML export pathway and python-pptx-adjacent tools. Trigger on any MS Project schedule output request, Gantt chart generation, or project schedule data export."
---

# MS Project Schedule File SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create MS Project XML | Python (manual XML) or `mpxj` |
| Create .mpp | MS Project (Windows) or `mpxj` Java |
| Read .mpp / .xml | `mpxj` (Java/Python via subprocess) |
| Gantt chart (visual) | `matplotlib` or `plotly` |
| Export to CSV/XLSX | Python direct |
| P6 XER → MS Project XML | `mpxj` |

---

## MS Project XML Format

MS Project can import/export `.xml` files (Microsoft Project XML format). This is the primary open pathway.

```python
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_ms_project_xml(project_name, tasks, output_path):
    """
    Create Microsoft Project XML file.
    tasks: list of dicts with keys:
        id, name, duration_days, start, predecessors (list of ids),
        resource, percent_complete, notes
    """
    root = ET.Element("Project")
    root.set("xmlns", "http://schemas.microsoft.com/project")

    # Project metadata
    ET.SubElement(root, "Name").text = project_name
    ET.SubElement(root, "Title").text = project_name
    ET.SubElement(root, "CreationDate").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(root, "LastSaved").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(root, "ScheduleFromStart").text = "1"
    ET.SubElement(root, "DefaultStartTime").text = "08:00:00"
    ET.SubElement(root, "DefaultFinishTime").text = "17:00:00"
    ET.SubElement(root, "MinutesPerDay").text = "480"
    ET.SubElement(root, "DaysPerMonth").text = "20"
    ET.SubElement(root, "CalendarUID").text = "1"

    # Calendar
    cals = ET.SubElement(root, "Calendars")
    cal = ET.SubElement(cals, "Calendar")
    ET.SubElement(cal, "UID").text = "1"
    ET.SubElement(cal, "Name").text = "Standard"
    ET.SubElement(cal, "IsBaseCalendar").text = "1"

    # Tasks
    tasks_elem = ET.SubElement(root, "Tasks")
    
    # Summary task (ID 0)
    summary = ET.SubElement(tasks_elem, "Task")
    ET.SubElement(summary, "UID").text = "0"
    ET.SubElement(summary, "ID").text = "0"
    ET.SubElement(summary, "Name").text = project_name
    ET.SubElement(summary, "Summary").text = "1"
    ET.SubElement(summary, "OutlineLevel").text = "0"

    for task in tasks:
        t = ET.SubElement(tasks_elem, "Task")
        ET.SubElement(t, "UID").text = str(task["id"])
        ET.SubElement(t, "ID").text = str(task["id"])
        ET.SubElement(t, "Name").text = task["name"]
        ET.SubElement(t, "Duration").text = f"PT{task['duration_days'] * 8}H0M0S"
        ET.SubElement(t, "DurationFormat").text = "7"  # 7 = days
        ET.SubElement(t, "Start").text = task["start"].strftime("%Y-%m-%dT08:00:00")
        finish = task["start"] + timedelta(days=task["duration_days"])
        ET.SubElement(t, "Finish").text = finish.strftime("%Y-%m-%dT17:00:00")
        ET.SubElement(t, "PercentComplete").text = str(task.get("percent_complete", 0))
        ET.SubElement(t, "OutlineLevel").text = str(task.get("outline_level", 1))
        ET.SubElement(t, "Summary").text = "0"
        ET.SubElement(t, "Milestone").text = "1" if task.get("milestone") else "0"
        
        if task.get("notes"):
            ET.SubElement(t, "Notes").text = task["notes"]
        
        # Predecessors
        for pred_id in task.get("predecessors", []):
            preds = ET.SubElement(t, "PredecessorLink")
            ET.SubElement(preds, "PredecessorUID").text = str(pred_id)
            ET.SubElement(preds, "Type").text = "1"  # 1 = Finish-to-Start
            ET.SubElement(preds, "LinkLag").text = "0"

    # Resources
    resources_elem = ET.SubElement(root, "Resources")
    resource_names = list(set(t.get("resource", "") for t in tasks if t.get("resource")))
    for i, res_name in enumerate(resource_names, start=1):
        res = ET.SubElement(resources_elem, "Resource")
        ET.SubElement(res, "UID").text = str(i)
        ET.SubElement(res, "ID").text = str(i)
        ET.SubElement(res, "Name").text = res_name
        ET.SubElement(res, "Type").text = "1"  # 1 = Work resource

    # Assignments
    assignments_elem = ET.SubElement(root, "Assignments")
    assign_id = 1
    resource_map = {name: i+1 for i, name in enumerate(resource_names)}
    for task in tasks:
        if task.get("resource") and task["resource"] in resource_map:
            assign = ET.SubElement(assignments_elem, "Assignment")
            ET.SubElement(assign, "UID").text = str(assign_id)
            ET.SubElement(assign, "TaskUID").text = str(task["id"])
            ET.SubElement(assign, "ResourceUID").text = str(resource_map[task["resource"]])
            ET.SubElement(assign, "Units").text = "1"
            assign_id += 1

    # Pretty print
    raw = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="  ")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty)
    print(f"Saved: {output_path}")
```

---

## Example Usage

```python
from datetime import date

tasks = [
    {"id": 1, "name": "Site Preparation",       "duration_days": 10, "start": date(2024, 4, 1),  "predecessors": [],  "resource": "Civil",    "percent_complete": 100},
    {"id": 2, "name": "Foundation Excavation",   "duration_days": 15, "start": date(2024, 4, 15), "predecessors": [1], "resource": "Civil",    "percent_complete": 60},
    {"id": 3, "name": "Foundation Concrete",     "duration_days": 10, "start": date(2024, 5, 6),  "predecessors": [2], "resource": "Concrete", "percent_complete": 0},
    {"id": 4, "name": "Ground Floor Structure",  "duration_days": 20, "start": date(2024, 5, 20), "predecessors": [3], "resource": "Structural","percent_complete": 0},
    {"id": 5, "name": "Handover",                "duration_days": 1,  "start": date(2024, 6, 15), "predecessors": [4], "resource": "",         "percent_complete": 0, "milestone": True},
]

create_ms_project_xml("Main Tower Construction", tasks, "schedule.xml")
```

---

## Gantt Chart (Python Visual)

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

def plot_gantt(tasks, title="Project Schedule"):
    fig, ax = plt.subplots(figsize=(14, len(tasks) * 0.6 + 2))
    
    colors = {"Civil": "#1E2761", "Concrete": "#F96167", "Structural": "#065A82",
              "": "#AAAAAA"}
    
    for i, task in enumerate(reversed(tasks)):
        start = task["start"]
        duration = task["duration_days"]
        color = colors.get(task.get("resource", ""), "#888888")
        
        ax.barh(i, duration, left=start.toordinal(),
                height=0.6, color=color, alpha=0.85, edgecolor="white")
        ax.text(start.toordinal() + duration/2, i,
                task["name"], ha="center", va="center",
                fontsize=8, color="white", fontweight="bold")
    
    task_names = [t["name"] for t in reversed(tasks)]
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels(task_names, fontsize=9)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.xaxis_date()
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig("gantt.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: gantt.png")
```

---

## mpxj (Java-based, Reads/Writes .mpp)

```bash
# mpxj can read .mpp, .xml, .mpp, .xer and convert between them
# Python wrapper available

pip install mpxj --break-system-packages

python -c "
from mpxj import ProjectReader
reader = ProjectReader()
project = reader.read('schedule.mpp')
for task in project.tasks:
    print(f'{task.name}: {task.start} → {task.finish}')
"
```

---

## CLI Verification

```bash
# Validate XML structure
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('schedule.xml')
ns = {'ms': 'http://schemas.microsoft.com/project'}
root = tree.getroot()
tasks = root.findall('ms:Tasks/ms:Task', ns)
print(f'Tasks: {len(tasks)}')
for t in tasks[:5]:
    name = t.findtext('ms:Name', namespaces=ns)
    dur = t.findtext('ms:Duration', namespaces=ns)
    print(f'  {name}: {dur}')
"

# Check file
wc -l schedule.xml
head -20 schedule.xml
```

---

## QA Checklist

- [ ] All tasks have UID, ID, Name, Duration, Start, Finish
- [ ] Predecessor links use correct UIDs
- [ ] Duration format correct (`PT8H0M0S` = 1 day)
- [ ] Start/Finish dates in ISO 8601 with time (`2024-04-01T08:00:00`)
- [ ] Calendar defined (UID 1)
- [ ] Project namespace declared correctly
- [ ] Resource assignments match resource UIDs
- [ ] Imports cleanly into MS Project without errors
- [ ] Critical path logical (no circular dependencies)

---

## Common Mistakes to Avoid

- Wrong duration format (must be `PTxH0M0S` not just days as integer)
- Missing namespace on root element (XML won't import)
- Circular predecessor dependencies (causes import failure)
- Milestones with non-zero duration (milestone must have 0 duration)
- Predecessor UIDs that don't exist in the task list
- Date format without time component (MS Project requires time)

---

## Dependencies

```bash
pip install mpxj --break-system-packages
pip install matplotlib --break-system-packages
# xml.etree.ElementTree: Python stdlib
```
