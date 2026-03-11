---
name: revit-project-file
description: "Use this skill when working with Autodesk Revit .rvt files in an architecture/construction context. Since .rvt is a proprietary binary format not directly writable without the Revit API, this skill covers the primary pathways: IFC export/import, Dynamo scripting, Revit CLI via journal files, and pyRevit. Trigger when the user needs to produce or process Revit files."
---

# Revit Project File SKILL

## Important Constraint

> Revit `.rvt` files are a **proprietary binary format** — they cannot be written from scratch without the Revit API (C#/.NET) or an active Revit installation. This skill covers the realistic pathways available in non-Windows or non-Revit environments.

## Pathways Summary

| Goal | Best Approach |
|------|--------------|
| Create BIM model → open in Revit | Create IFC → import into Revit |
| Automate inside Revit (Windows) | Revit Journal file or pyRevit |
| Extract data from .rvt | Forge/APS API or Dynamo |
| Batch export from Revit | Revit Journal automation |
| Clash detection from .rvt | Export to NWC → Navisworks |

---

## Pathway 1: IFC → Revit (Recommended)

Build your model as IFC using the `ifc-file` skill, then import into Revit.

```python
# Step 1: Build IFC model (see ifc-file SKILL)
import ifcopenshell
import ifcopenshell.api

model = ifcopenshell.file(schema="IFC4")
# ... build complete IFC model ...
model.write("model.ifc")
```

**In Revit:**
1. File → Open → IFC
2. Select `model.ifc`
3. Map IFC categories to Revit categories in the dialog
4. Save as `.rvt`

### IFC Export Settings for Revit Compatibility

```python
# Use IFC2x3 for maximum Revit compatibility (IFC4 import is less stable)
model = ifcopenshell.file(schema="IFC2X3")

# Avoid these in IFC for Revit import:
# - IfcSpace with complex geometry (simplify)
# - Non-standard property set names (use Pset_ prefix)
# - Nested aggregations deeper than Project→Site→Building→Storey→Element
```

---

## Pathway 2: Revit Journal Files (Windows / Revit Installed)

Revit journal files (`.txt`) automate Revit UI actions.

```python
def generate_revit_journal(rvt_path, export_path, export_format="IFC"):
    """Generate a Revit journal file for automated export."""
    
    journal = f"""' Autodesk Revit Journal
' Generated: {__import__('datetime').datetime.now().isoformat()}

Dim Jrn
Set Jrn = CmdlnJrn

' Open project
Jrn.Command "StartupPage" , "Open a Revit file , ID_FILE_MRU_FIRST"
Jrn.Data "FileOpenSubDialog" , "FileName={rvt_path}"
Jrn.Data "FileOpenSubDialog" , "Click Open"
"""

    if export_format == "IFC":
        journal += f"""
' Export to IFC
Jrn.Command "Internal" , "ID_EXPORT_IFC"
Jrn.Data "ExportIFCDialog" , "FileName={export_path}"
Jrn.Data "ExportIFCDialog" , "Click Export"
"""
    elif export_format == "DWG":
        journal += f"""
' Export to DWG
Jrn.Command "Internal" , "ID_EXPORT_CAD"
Jrn.Data "ExportCADDialog" , "FileName={export_path}"
Jrn.Data "ExportCADDialog" , "Click OK"
"""

    journal += """
' Close
Jrn.Command "Internal" , "ID_REVIT_FILE_CLOSE"
"""
    return journal

# Save journal
with open("export_model.txt", "w") as f:
    f.write(generate_revit_journal(
        r"C:\Projects\MainTower.rvt",
        r"C:\Projects\Export\MainTower.ifc"
    ))

# Run (Windows, Revit installed)
# "C:\Program Files\Autodesk\Revit 2024\Revit.exe" /journal export_model.txt
```

---

## Pathway 3: pyRevit (Inside Revit)

pyRevit scripts run inside Revit as push-button tools.

```python
# pyRevit script: export_to_ifc.py
# Run via pyRevit panel inside Revit

from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

# Get all walls
walls = DB.FilteredElementCollector(doc)\
    .OfClass(DB.Wall)\
    .ToElements()

output.print_md("# Wall Export")
output.print_md(f"Found **{len(walls)}** walls")

for wall in walls:
    name = wall.Name
    level = doc.GetElement(wall.LevelId)
    level_name = level.Name if level else "Unknown"
    length = wall.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH)
    length_m = length.AsDouble() * 0.3048 if length else 0  # Feet → meters
    output.print_md(f"- **{name}** | Level: {level_name} | Length: {length_m:.2f}m")
```

---

## Pathway 4: Autodesk Platform Services (APS / Forge API)

For server-side RVT processing without a Revit installation:

```python
import requests

# APS authentication
def get_aps_token(client_id, client_secret):
    resp = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "grant_type": "client_credentials",
            "scope": "data:read data:write bucket:create"
        },
        auth=(client_id, client_secret)
    )
    return resp.json()["access_token"]

# Upload and translate RVT → SVF (viewable) or IFC
def translate_rvt(token, bucket_key, object_key, rvt_path):
    # 1. Create bucket
    # 2. Upload RVT
    # 3. Start translation job
    # 4. Poll for completion
    # 5. Download output
    # Full implementation: see APS documentation
    pass
```

---

## Extracting Data from RVT (Without Revit API)

```bash
# RVT files are OLE2 compound documents — can extract embedded data
python -c "
import olefile
if olefile.isOleFile('project.rvt'):
    ole = olefile.OleFileIO('project.rvt')
    print('OLE streams:', ole.listdir())
"

pip install olefile --break-system-packages
```

---

## Revit ↔ IFC Round-Trip Notes

| Direction | Fidelity | Common Issues |
|-----------|----------|---------------|
| IFC → Revit | Medium | Family mapping, parameter loss |
| Revit → IFC | High | Geometry simplification |
| Revit → DWG | High | 2D only per view |
| Revit → NWC | High | Full geometry, Navisworks only |

---

## QA Checklist

- [ ] IFC validated before Revit import (use `ifc-file` skill QA)
- [ ] IFC schema set to IFC2x3 for maximum Revit compatibility
- [ ] All elements on correct spatial hierarchy
- [ ] Shared coordinates established before import
- [ ] After Revit import: check warnings log for mapping errors
- [ ] Element count comparable between IFC and Revit model
- [ ] Materials mapped correctly in Revit

---

## Common Mistakes to Avoid

- Expecting to write `.rvt` directly — it requires the Revit API (C#/.NET) or active Revit installation
- Using IFC4 when Revit version is pre-2020 (IFC4 support is limited in older Revit)
- Importing IFC without establishing a project base point first
- Running journal files without a display session (Revit needs a display for some operations)

---

## Dependencies

```bash
pip install ifcopenshell --break-system-packages  # IFC creation
pip install olefile --break-system-packages        # RVT binary inspection
# pyRevit: installed inside Revit environment
# Revit API: requires licensed Autodesk Revit installation
# APS/Forge API: requires Autodesk developer account
```
