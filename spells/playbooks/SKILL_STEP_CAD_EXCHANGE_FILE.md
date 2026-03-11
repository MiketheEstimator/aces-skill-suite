---
name: step-cad-exchange-file
description: "Use this skill when producing or processing .step / .stp files — the ISO 10303 STEP format for 3D CAD geometry exchange. Covers pythonocc, FreeCAD CLI, and Open CASCADE. Trigger on any .step or .stp file output request, 3D geometry export, or CAD data interchange task."
---

# STEP CAD Exchange File SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create STEP geometry | `pythonocc-core` or `cadquery` |
| Read/inspect STEP | `pythonocc-core` or `cadquery` |
| Convert STEP ↔ other formats | FreeCAD CLI |
| Validate STEP | `steptools` or manual inspection |
| STEP → STL (mesh) | `pythonocc-core` or FreeCAD |
| STEP → IGES | FreeCAD CLI |

---

## STEP with CadQuery (Recommended — Pythonic)

```python
# pip install cadquery --break-system-packages
# Note: cadquery has complex dependencies — conda preferred:
# conda install -c cadquery -c conda-forge cadquery

import cadquery as cq

# Create a simple solid
box = cq.Workplane("XY").box(100, 60, 30)

# Chamfer edges
box_chamfered = box.edges("|Z").chamfer(5)

# Export to STEP
box_chamfered.val().exportStep("output.step")
print("Saved: output.step")

# More complex example: structural profile
profile = (
    cq.Workplane("XY")
    .rect(200, 10)               # Bottom flange
    .extrude(200)                # Length of member
)

profile.val().exportStep("beam_profile.step")
```

---

## STEP with pythonocc-core

```python
# pip install pythonocc-core --break-system-packages
# Alternative: conda install -c conda-forge pythonocc-core

from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf

def create_box(x, y, z, dx, dy, dz):
    """Create a box shape at given position and dimensions."""
    box = BRepPrimAPI_MakeBox(gp_Pnt(x, y, z),
                               gp_Pnt(x+dx, y+dy, z+dz)).Shape()
    return box

def create_cylinder(x, y, z, radius, height):
    """Create a vertical cylinder."""
    ax = gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0, 0, 1))
    cyl = BRepPrimAPI_MakeCylinder(ax, radius, height).Shape()
    return cyl

def export_to_step(shapes, output_path, schema="AP214"):
    """Export one or more shapes to STEP file."""
    writer = STEPControl_Writer()
    
    # Set schema (AP203 or AP214)
    if schema == "AP203":
        writer.Model().SetAttribute("STEP-AP203", "1")
    
    for shape in shapes if isinstance(shapes, list) else [shapes]:
        writer.Transfer(shape, STEPControl_AsIs)
    
    status = writer.Write(output_path)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"STEP export failed with status: {status}")
    print(f"Saved: {output_path}")

# Example
slab = create_box(0, 0, 0, 5000, 8000, 200)     # Floor slab (mm)
column = create_cylinder(1000, 1000, 200, 300, 3200)  # Column

export_to_step([slab, column], "structure.step")
```

---

## Reading STEP Files

```python
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE

def read_step(filepath):
    """Read a STEP file and return the compound shape."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"Failed to read STEP: {filepath}")
    reader.TransferRoots()
    shape = reader.OneShape()
    return shape

def count_topology(shape):
    """Count topological entities in a shape."""
    counts = {}
    for topo_type, name in [
        (TopAbs_SOLID, "Solids"),
        (TopAbs_FACE, "Faces"),
        (TopAbs_EDGE, "Edges"),
    ]:
        explorer = TopExp_Explorer(shape, topo_type)
        count = 0
        while explorer.More():
            count += 1
            explorer.Next()
        counts[name] = count
    return counts

shape = read_step("input.step")
print(count_topology(shape))
```

---

## FreeCAD CLI Conversions

```bash
# FreeCAD headless: convert STEP → STL
freecad --console << 'EOF'
import FreeCAD, Part, Mesh
shape = Part.read("input.step")
mesh = Mesh.Mesh()
mesh.addFacets(shape.tessellate(0.1)[1])
mesh.write("output.stl")
print("Done")
EOF

# STEP → IGES
freecad --console << 'EOF'
import FreeCAD, Part
shape = Part.read("input.step")
Part.export([shape], "output.iges")
print("Done")
EOF
```

---

## STEP → STL (Mesh)

```python
from OCC.Core.BRep import BRep_Builder
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

def step_to_stl(step_path, stl_path, resolution=0.1):
    """Convert STEP to STL mesh."""
    shape = read_step(step_path)
    
    # Mesh the shape
    mesh = BRepMesh_IncrementalMesh(shape, resolution)
    mesh.Perform()
    
    # Write STL
    writer = StlAPI_Writer()
    writer.Write(shape, stl_path)
    print(f"Saved STL: {stl_path}")
```

---

## STEP Schema Reference

| Schema | Use Case |
|--------|----------|
| AP203 | Configuration-controlled design (aerospace/defense) |
| AP214 | Automotive industry (surfaces + assemblies) |
| AP242 | Modern replacement for AP203/214, BIM bridge |

For architecture/construction, **AP214** or **AP242** is standard.

---

## CLI Verification

```bash
# Check STEP file header
head -10 output.step

# Count entities in STEP file
grep -c "^#" output.step

# Validate with pythonocc
python -c "
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
r = STEPControl_Reader()
status = r.ReadFile('output.step')
print('Read status:', 'OK' if status == IFSelect_RetDone else 'FAILED')
r.TransferRoots()
shape = r.OneShape()
print('Shape type:', shape.ShapeType())
print('Is null:', shape.IsNull())
"

# File size
ls -lh output.step
```

---

## QA Checklist

- [ ] STEP file header present (`ISO-10303-21;`)
- [ ] Schema declared (`AP203`, `AP214`, or `AP242`)
- [ ] File reads without error in pythonocc or FreeCAD
- [ ] Shape is not null after read
- [ ] Solid count matches expected geometry
- [ ] Units consistent (mm for architecture — verify in header)
- [ ] No degenerate faces or edges (check topology counts)
- [ ] File opens in target CAD software (AutoCAD, SolidWorks, Rhino)

---

## STEP File Header Example

```
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Open CASCADE STEP translator'),'2;1');
FILE_NAME('output.step','2024-03-15T09:00:00',('Author'),('Org'),'OCC','OCC','');
FILE_SCHEMA(('AP214IS'));
ENDSEC;
DATA;
#1=PRODUCT('Part','Part','',(#2));
...
ENDSEC;
END-ISO-10303-21;
```

---

## Common Mistakes to Avoid

- Exporting without performing `BRepMesh_IncrementalMesh` before STL (empty mesh)
- Using AP203 when importing into software expecting AP214 (may lose color/material)
- Setting mesh resolution too coarse (blocky output) or too fine (enormous file)
- Not checking `IFSelect_RetDone` return status (silent read failures)
- Exporting null shapes (check `shape.IsNull()` before writing)

---

## Dependencies

```bash
# CadQuery (easier API)
conda install -c cadquery -c conda-forge cadquery
# or: pip install cadquery --break-system-packages (may fail on some systems)

# pythonocc-core (lower-level, full OCC access)
conda install -c conda-forge pythonocc-core
# or: pip install pythonocc-core --break-system-packages

# FreeCAD (CLI conversion)
sudo apt-get install freecad
```
