---
name: SKILL_BIM_BCF_COORDINATE_CLASH
description: "XML/ZIP payload generation specifically for tracking spatial clashes and camera views in BIM workflows. Use when producing .bcf or .bcfzip files for coordination meetings, clash reports, or issue tracking in Revit, Navisworks, or BIM 360. Triggers: 'BCF', '.bcf', 'BIM clash', 'coordination issue', 'clash detection', 'BIM issue tracker', 'camera view export', 'Navisworks clash'."
---

# SKILL_BIM_BCF_COORDINATE_CLASH — BCF BIM Coordination Skill

## Quick Reference

| Task | Section |
|------|---------|
| BCF format overview | [BCF Format](#bcf-format) |
| Create BCF file (Python) | [Create BCF](#create-bcf-in-python) |
| Parse BCF file | [Parse BCF](#parse-bcf-in-python) |
| Clash report → BCF | [Clash to BCF](#clash-report-to-bcf) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## BCF Format

BCF (BIM Collaboration Format) is a ZIP archive containing:

```
issue.bcfzip
├── bcf.version         — BCF version declaration
├── project.bcfp        — project info
└── {topic-guid}/
    ├── markup.bcf      — issue metadata (title, status, author, comments)
    ├── viewpoint.bcfv  — camera position + component visibility
    ├── snapshot.png    — screenshot of the issue view (optional)
    └── viewpoint2.bcfv — additional viewpoints (optional)
```

BCF versions: 2.1 (most widely supported), 3.0 (latest).

---

## Create BCF in Python

```python
import zipfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def bcf_version_xml() -> str:
    return '<?xml version="1.0" encoding="utf-8"?>\n<Version VersionId="2.1" />'

def project_xml(project_name: str, project_guid: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ProjectExtension>
  <Project ProjectId="{project_guid}">
    <Name>{project_name}</Name>
  </Project>
</ProjectExtension>"""

def markup_xml(topic: dict) -> str:
    """
    topic keys:
        guid, title, type, status, priority, description,
        author, creation_date, assigned_to, labels (list),
        comments (list of {author, date, comment})
    """
    labels_xml = "\n    ".join(f"<Label>{l}</Label>"
                               for l in topic.get("labels", []))
    comments_xml = "\n  ".join(
        f'<Comment Guid="{str(uuid.uuid4())}">'
        f'<Date>{c["date"]}</Date>'
        f'<Author>{c["author"]}</Author>'
        f'<Comment>{c["comment"]}</Comment>'
        f'</Comment>'
        for c in topic.get("comments", [])
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<Markup>
  <Topic Guid="{topic['guid']}" TopicType="{topic.get('type','Clash')}" TopicStatus="{topic.get('status','Open')}">
    <Title>{topic['title']}</Title>
    <Priority>{topic.get('priority','Normal')}</Priority>
    <CreationDate>{topic.get('creation_date', iso_now())}</CreationDate>
    <CreationAuthor>{topic.get('author','BIM Coordinator')}</CreationAuthor>
    <AssignedTo>{topic.get('assigned_to','')}</AssignedTo>
    <Description>{topic.get('description','')}</Description>
    {labels_xml}
    <Viewpoints>
      <ViewPoint Guid="{topic['guid']}-vp">
        <Viewpoint>viewpoint.bcfv</Viewpoint>
        <Snapshot>snapshot.png</Snapshot>
      </ViewPoint>
    </Viewpoints>
  </Topic>
  {comments_xml}
</Markup>"""

def viewpoint_xml(camera: dict, components: list = None) -> str:
    """
    camera: {x, y, z, dir_x, dir_y, dir_z, up_x, up_y, up_z, fov}
    components: list of {ifc_guid, selected (bool), visible (bool)}
    """
    comp_xml = ""
    if components:
        selected = [c for c in components if c.get("selected")]
        hidden   = [c for c in components if not c.get("visible", True)]
        if selected:
            sel_xml = "\n      ".join(
                f'<Component IfcGuid="{c["ifc_guid"]}" />' for c in selected
            )
            comp_xml += f"\n  <Components>\n    <Selection>\n      {sel_xml}\n    </Selection>"
        if hidden:
            hid_xml = "\n      ".join(
                f'<Component IfcGuid="{c["ifc_guid"]}" />' for c in hidden
            )
            comp_xml += f"\n    <Visibility DefaultVisibility=\"true\">\n      <Exceptions>\n        {hid_xml}\n      </Exceptions>\n    </Visibility>\n  </Components>"

    return f"""<?xml version="1.0" encoding="utf-8"?>
<VisualizationInfo Guid="{str(uuid.uuid4())}">
  <PerspectiveCamera>
    <CameraViewPoint>
      <X>{camera.get('x', 0.0)}</X>
      <Y>{camera.get('y', 0.0)}</Y>
      <Z>{camera.get('z', 5.0)}</Z>
    </CameraViewPoint>
    <CameraDirection>
      <X>{camera.get('dir_x', 0.0)}</X>
      <Y>{camera.get('dir_y', 1.0)}</Y>
      <Z>{camera.get('dir_z', 0.0)}</Z>
    </CameraDirection>
    <CameraUpVector>
      <X>{camera.get('up_x', 0.0)}</X>
      <Y>{camera.get('up_y', 0.0)}</Y>
      <Z>{camera.get('up_z', 1.0)}</Z>
    </CameraUpVector>
    <FieldOfView>{camera.get('fov', 60.0)}</FieldOfView>
  </PerspectiveCamera>{comp_xml}
</VisualizationInfo>"""


def create_bcf(output_path: str, project_name: str, topics: list) -> None:
    """
    Create a BCF 2.1 zip file.

    topics: list of topic dicts (see markup_xml for keys)
    """
    project_guid = str(uuid.uuid4())

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", bcf_version_xml())
        zf.writestr("project.bcfp", project_xml(project_name, project_guid))

        for topic in topics:
            tguid = topic.get("guid") or str(uuid.uuid4())
            topic["guid"] = tguid
            folder = f"{tguid}/"

            zf.writestr(folder + "markup.bcf",
                        markup_xml(topic))
            zf.writestr(folder + "viewpoint.bcfv",
                        viewpoint_xml(topic.get("camera", {}),
                                      topic.get("components")))

    print(f"BCF created: {output_path} ({len(topics)} issues)")
```

### Usage Example

```python
topics = [
    {
        "title":       "Structural beam clashes with MEP duct — Level 3",
        "type":        "Clash",
        "status":      "Open",
        "priority":    "Critical",
        "author":      "j.smith@aec.com",
        "assigned_to": "m.jones@mep.com",
        "description": "200mm deep steel beam (Grid D/Level 3) intersects "
                       "500x300mm supply air duct. Requires beam notching "
                       "or duct rerouting. SE approval required.",
        "labels":      ["Structural", "MEP", "Level 3"],
        "camera": {
            "x": 12.5, "y": -8.3, "z": 9.7,
            "dir_x": -0.6, "dir_y": 0.7, "dir_z": -0.4,
            "up_x": 0.0, "up_y": 0.0, "up_z": 1.0,
            "fov": 60.0
        },
        "components": [
            {"ifc_guid": "3D8ZkKnZH9fBzRi_l8kIaA", "selected": True, "visible": True},
            {"ifc_guid": "1Qz8tNkPJADBcL5Rm7jXeB", "selected": True, "visible": True},
        ],
        "comments": [
            {
                "author":  "j.smith@aec.com",
                "date":    iso_now(),
                "comment": "Flagged from Navisworks clash test run 2024-03-15."
            }
        ]
    }
]

create_bcf("coordination_issues_R1.bcfzip", "Project Alpha", topics)
```

---

## Parse BCF in Python

```python
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_bcf(bcf_path: str) -> list[dict]:
    """Parse BCF zip and return list of topic dicts."""
    topics = []

    with zipfile.ZipFile(bcf_path, "r") as zf:
        names = zf.namelist()

        # Find all markup.bcf files
        markups = [n for n in names if n.endswith("markup.bcf")]

        for markup_path in markups:
            topic_guid = markup_path.split("/")[0]
            xml_content = zf.read(markup_path).decode("utf-8")
            root = ET.fromstring(xml_content)

            topic_el = root.find("Topic")
            if topic_el is None:
                continue

            topic = {
                "guid":          topic_el.get("Guid"),
                "type":          topic_el.get("TopicType"),
                "status":        topic_el.get("TopicStatus"),
                "title":         _text(topic_el, "Title"),
                "priority":      _text(topic_el, "Priority"),
                "description":   _text(topic_el, "Description"),
                "author":        _text(topic_el, "CreationAuthor"),
                "creation_date": _text(topic_el, "CreationDate"),
                "assigned_to":   _text(topic_el, "AssignedTo"),
                "labels":        [l.text for l in topic_el.findall("Label")],
                "comments":      []
            }

            for c in root.findall("Comment"):
                topic["comments"].append({
                    "author":  _text(c, "Author"),
                    "date":    _text(c, "Date"),
                    "comment": _text(c, "Comment")
                })

            topics.append(topic)

    return topics

def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""
```

---

## Clash Report to BCF

```python
import csv

def navisworks_csv_to_bcf(csv_path: str, output_bcf: str,
                           project_name: str) -> None:
    """
    Convert Navisworks clash report CSV to BCF.
    Expected CSV columns: Name, Status, Description, Point X, Point Y, Point Z
    """
    topics = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            x = float(row.get("Point X", 0))
            y = float(row.get("Point Y", 0))
            z = float(row.get("Point Z", 0))

            # Simple camera: pull back 5m from clash point
            topics.append({
                "title":       row.get("Name", "Unnamed Clash"),
                "type":        "Clash",
                "status":      _map_status(row.get("Status", "New")),
                "description": row.get("Description", ""),
                "camera": {
                    "x": x + 5, "y": y + 5, "z": z + 3,
                    "dir_x": -0.57, "dir_y": -0.57, "dir_z": -0.57,
                    "up_x": 0, "up_y": 0, "up_z": 1,
                    "fov": 60
                }
            })

    create_bcf(output_bcf, project_name, topics)

def _map_status(nw_status: str) -> str:
    return {"New": "Open", "Active": "Open",
            "Reviewed": "In Progress", "Approved": "Resolved",
            "Resolved": "Closed"}.get(nw_status, "Open")
```

---

## Validation & QA

```python
import zipfile, xml.etree.ElementTree as ET

def validate_bcf(bcf_path: str) -> bool:
    errors = []

    try:
        with zipfile.ZipFile(bcf_path, "r") as zf:
            names = zf.namelist()

            # Required files
            if "bcf.version" not in names:
                errors.append("MISSING: bcf.version")
            if "project.bcfp" not in names:
                errors.append("MISSING: project.bcfp")

            markups = [n for n in names if n.endswith("markup.bcf")]
            print(f"Topics found: {len(markups)}")

            for mp in markups:
                try:
                    ET.fromstring(zf.read(mp).decode("utf-8"))
                except ET.ParseError as e:
                    errors.append(f"XML ERROR in {mp}: {e}")

    except zipfile.BadZipFile:
        errors.append("ERROR: Not a valid ZIP/BCF file")

    if errors:
        for e in errors: print(e)
        return False
    print("PASS: BCF is valid")
    return True
```

### QA Checklist

- [ ] Archive opens as valid ZIP
- [ ] `bcf.version` present with correct version ID
- [ ] `project.bcfp` present with project name
- [ ] All `markup.bcf` files parse as valid XML
- [ ] All topic GUIDs are unique
- [ ] Camera coordinates are in project coordinate system
- [ ] Status values match BCF spec: `Open`, `In Progress`, `Resolved`, `Closed`
- [ ] Opens correctly in Navisworks / Revit / BIM 360

---

## Dependencies

```bash
import zipfile      # stdlib
import uuid         # stdlib
import xml.etree.ElementTree as ET   # stdlib

# Advanced BCF parsing
pip install bcf-client    # community BCF library
```
