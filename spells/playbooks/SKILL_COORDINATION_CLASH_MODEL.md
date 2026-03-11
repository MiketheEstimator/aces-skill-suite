---
name: coordination-clash-model
description: "Use this skill when working with coordination models and clash detection in architecture/construction BIM workflows. Covers NWC/NWD format context, IFC-based clash detection with ifcopenshell, BCF issue reporting, and Navisworks automation. Trigger on any clash detection, model coordination, or federated model task."
---

# Coordination / Clash Model SKILL

## Quick Reference

| Task | Tool |
|------|------|
| IFC clash detection (open source) | `ifcopenshell` + geometry engine |
| Federated model assembly | `ifcopenshell` (merge IFC files) |
| BCF issue export | `bcf-client` or manual XML |
| NWC/NWD context | Navisworks (proprietary — see notes) |
| Clash report output | JSON, BCF, or formatted PDF |

---

## IFC-Based Clash Detection

```python
# pip install ifcopenshell --break-system-packages
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import numpy as np
from itertools import combinations

def get_bounding_boxes(model, entity_types=None):
    """Extract bounding boxes for all or specific entity types."""
    if entity_types is None:
        entity_types = ["IfcWall", "IfcBeam", "IfcColumn", "IfcSlab",
                        "IfcMechanicalFastener", "IfcPipeSegment", "IfcDuctSegment"]
    
    settings = ifcopenshell.geom.settings()
    elements = []
    
    for entity_type in entity_types:
        for element in model.by_type(entity_type):
            try:
                shape = ifcopenshell.geom.create_shape(settings, element)
                verts = shape.geometry.verts
                if not verts:
                    continue
                verts_array = np.array(verts).reshape(-1, 3)
                bbox = {
                    "element": element,
                    "guid": element.GlobalId,
                    "type": element.is_a(),
                    "name": getattr(element, "Name", ""),
                    "min": verts_array.min(axis=0),
                    "max": verts_array.max(axis=0),
                }
                elements.append(bbox)
            except Exception as e:
                continue
    return elements

def check_bbox_overlap(bbox1, bbox2, tolerance=0.0):
    """Check if two bounding boxes overlap."""
    for i in range(3):
        if bbox1["max"][i] <= bbox2["min"][i] - tolerance:
            return False
        if bbox2["max"][i] <= bbox1["min"][i] - tolerance:
            return False
    return True

def detect_clashes(model, tolerance=0.05):
    """
    Detect clashes between all elements.
    tolerance: meters — positive allows small gaps to be flagged, 
               negative allows small overlaps to be ignored.
    """
    elements = get_bounding_boxes(model)
    clashes = []
    
    for e1, e2 in combinations(elements, 2):
        # Skip same-type pairs if desired (e.g., wall-to-wall)
        if e1["type"] == e2["type"] == "IfcWall":
            continue
            
        if check_bbox_overlap(e1, e2, tolerance=-tolerance):
            clashes.append({
                "element_1_guid": e1["guid"],
                "element_1_type": e1["type"],
                "element_1_name": e1["name"],
                "element_2_guid": e2["guid"],
                "element_2_type": e2["type"],
                "element_2_name": e2["name"],
                "severity": "Hard Clash",
            })
    
    return clashes
```

---

## Federated Model Assembly

```python
def merge_ifc_models(model_paths, output_path):
    """
    Merge multiple IFC files into a single federated model.
    Note: maintains separate spatial hierarchies per discipline.
    """
    # Create new federated model
    merged = ifcopenshell.file(schema="IFC4")
    
    for path in model_paths:
        src = ifcopenshell.open(path)
        # Copy all entities
        for entity in src:
            merged.add(entity)
        print(f"Merged: {path} ({len(list(src))} entities)")
    
    merged.write(output_path)
    print(f"Federated model saved: {output_path}")
    return merged

# Example
merge_ifc_models([
    "architecture.ifc",
    "structure.ifc",
    "mep.ifc",
], "federated_model.ifc")
```

---

## BCF (BIM Collaboration Format) Issue Export

```python
import json
import uuid
from datetime import datetime

def create_bcf_issue(title, description, guid_1, guid_2, clash_point=None):
    """Create a BCF-compatible issue record."""
    return {
        "Guid": str(uuid.uuid4()),
        "TopicType": "Clash",
        "TopicStatus": "Open",
        "Priority": "Major",
        "Title": title,
        "Description": description,
        "CreationDate": datetime.utcnow().isoformat() + "Z",
        "RelatedViewpoints": [],
        "RelatedIfcGuids": [guid_1, guid_2],
        "ClashPoint": clash_point or {},
    }

def export_clash_report_bcf(clashes, output_path):
    """Export clashes as BCF JSON report."""
    issues = []
    for clash in clashes:
        issue = create_bcf_issue(
            title=f"Clash: {clash['element_1_type']} / {clash['element_2_type']}",
            description=(f"{clash['element_1_name']} ({clash['element_1_guid']}) "
                        f"clashes with {clash['element_2_name']} ({clash['element_2_guid']})"),
            guid_1=clash["element_1_guid"],
            guid_2=clash["element_2_guid"],
        )
        issues.append(issue)
    
    report = {
        "version": "2.1",
        "generated": datetime.utcnow().isoformat() + "Z",
        "total_clashes": len(clashes),
        "issues": issues,
    }
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"BCF report: {output_path} ({len(clashes)} clashes)")

def export_clash_report_csv(clashes, output_path):
    """Export clashes as CSV for spreadsheet review."""
    import csv
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "severity", "element_1_type", "element_1_name", "element_1_guid",
            "element_2_type", "element_2_name", "element_2_guid"
        ])
        writer.writeheader()
        writer.writerows(clashes)
    print(f"CSV report: {output_path}")
```

---

## Navisworks NWC/NWD Notes

> NWC (Navisworks Cache) and NWD (Navisworks Document) are **proprietary Autodesk formats**. They cannot be written without Navisworks or the Navisworks API.

**Open-source pathway:**
- Export each discipline model as IFC
- Use ifcopenshell for clash detection (as above)
- Export BCF report for issue tracking

**If Navisworks is available:**
```
# Navisworks CLI (NWD batch processing)
"C:\Program Files\Autodesk\Navisworks Manage 2024\FiletoolsTaskpanePlugin.exe" ^
  -nwcout output.nwc ^
  -i input.rvt

# Or via COM automation (VBScript/PowerShell)
# See Navisworks API documentation
```

---

## CLI Verification

```bash
# Run clash detection on IFC file
python -c "
import ifcopenshell, json
# (paste detect_clashes function here)
model = ifcopenshell.open('federated_model.ifc')
clashes = detect_clashes(model, tolerance=0.05)
print(f'Total clashes: {len(clashes)}')
by_type = {}
for c in clashes:
    key = f'{c[\"element_1_type\"]} × {c[\"element_2_type\"]}'
    by_type[key] = by_type.get(key, 0) + 1
for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
"

# Validate federated model
python -c "
import ifcopenshell
m = ifcopenshell.open('federated_model.ifc')
print(f'Schema: {m.schema}')
print(f'Total entities: {len(list(m))}')
for t in ['IfcWall','IfcColumn','IfcBeam','IfcSlab','IfcSpace']:
    print(f'  {t}: {len(m.by_type(t))}')
"
```

---

## QA Checklist

- [ ] All discipline models validated as IFC before federation
- [ ] Shared coordinate system consistent across all models
- [ ] Clash tolerance set appropriately (typically 5–50mm depending on discipline)
- [ ] BCF/CSV report generated and reviewable
- [ ] Clash count reviewed for false positives (same-discipline same-type)
- [ ] Hard clashes distinguished from soft clashes (clearance violations)
- [ ] Output report references element GUIDs (traceable back to model)

---

## Common Mistakes to Avoid

- Merging IFC models with different coordinate origins (all clashes will be false positives)
- Using too-tight tolerance (hundreds of false positives from adjacent elements)
- Using too-loose tolerance (real clashes missed)
- Not filtering same-type structural clashes (e.g., wall-to-wall at junctions)
- Attempting to write NWC/NWD without Navisworks — use IFC-based detection instead

---

## Dependencies

```bash
pip install ifcopenshell --break-system-packages
pip install numpy --break-system-packages
# bcf-client (optional): pip install bcf-client --break-system-packages
# Navisworks: Autodesk commercial license required
```
