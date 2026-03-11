---
name: ifc-file
description: "Use this skill when producing or processing IFC (Industry Foundation Classes) files for BIM workflows in architecture and construction. Covers IfcOpenShell, IFC schema, entity creation, geometry, and model validation. Trigger on any .ifc file output or BIM data exchange task."
---

# Industry Foundation Classes (IFC) File SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create IFC from scratch | `ifcopenshell` |
| Read/query IFC | `ifcopenshell` |
| Validate IFC | `ifcopenshell` + schema checks |
| IFC → geometry (mesh) | `ifcopenshell.geom` |
| Viewer | BIMvision (Windows) or xBIM (web) |
| Schema reference | IFC2x3, IFC4, IFC4x3 |

---

## Setup

```bash
pip install ifcopenshell --break-system-packages
# Note: may require specific version for your platform
# Alternative: conda install -c conda-forge ifcopenshell
```

---

## Create a Minimal IFC File

```python
import ifcopenshell
import ifcopenshell.api
from datetime import datetime

# Create new IFC file (IFC4 schema)
model = ifcopenshell.file(schema="IFC4")

# --- Project setup ---
project = ifcopenshell.api.run("root.create_entity", model,
    ifc_class="IfcProject", name="Main Tower")

# Units
ifcopenshell.api.run("unit.assign_unit", model,
    units=[{
        "type": "LENGTHUNIT",
        "prefix": "MILLI",
        "name": "METRE"
    }])

# Geometry context
context = ifcopenshell.api.run("context.add_context", model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=None)

# Site → Building → StoreyS hierarchy
site = ifcopenshell.api.run("root.create_entity", model,
    ifc_class="IfcSite", name="Site")
building = ifcopenshell.api.run("root.create_entity", model,
    ifc_class="IfcBuilding", name="Main Tower Building")
storey = ifcopenshell.api.run("root.create_entity", model,
    ifc_class="IfcBuildingStorey", name="Ground Floor")

# Assign spatial hierarchy
ifcopenshell.api.run("aggregate.assign_object", model,
    relating_object=project, products=[site])
ifcopenshell.api.run("aggregate.assign_object", model,
    relating_object=site, products=[building])
ifcopenshell.api.run("aggregate.assign_object", model,
    relating_object=building, products=[storey])
```

---

## Adding Walls

```python
import ifcopenshell.util.placement

def add_wall(model, storey, context, name, x, y, z, length, height, thickness):
    """Add an IfcWall with extruded area solid geometry."""
    
    # Create wall entity
    wall = ifcopenshell.api.run("root.create_entity", model,
        ifc_class="IfcWall", name=name)
    
    # Placement
    matrix = ifcopenshell.util.placement.get_axis2placement(model)
    placement = model.createIfcLocalPlacement(
        None,
        model.createIfcAxis2Placement3D(
            model.createIfcCartesianPoint((x, y, z)),
            model.createIfcDirection((0., 0., 1.)),
            model.createIfcDirection((1., 0., 0.))
        )
    )
    wall.ObjectPlacement = placement
    
    # Geometry — extruded rectangle
    profile = model.createIfcRectangleProfileDef(
        "AREA", None,
        model.createIfcAxis2Placement2D(
            model.createIfcCartesianPoint((0., 0.))
        ),
        length, thickness
    )
    solid = model.createIfcExtrudedAreaSolid(
        profile,
        model.createIfcAxis2Placement3D(
            model.createIfcCartesianPoint((0., 0., 0.))
        ),
        model.createIfcDirection((0., 0., 1.)),
        height
    )
    shape_rep = model.createIfcShapeRepresentation(
        context, "Body", "SweptSolid", [solid]
    )
    product_def_shape = model.createIfcProductDefinitionShape(
        None, None, [shape_rep]
    )
    wall.Representation = product_def_shape
    
    # Assign to storey
    ifcopenshell.api.run("spatial.assign_container", model,
        relating_structure=storey, products=[wall])
    
    return wall
```

---

## Adding Properties (Psets)

```python
def add_pset(model, element, pset_name, properties):
    """Add a property set to an IFC element."""
    pset = ifcopenshell.api.run("pset.add_pset", model,
        product=element, name=pset_name)
    ifcopenshell.api.run("pset.edit_pset", model,
        pset=pset, properties=properties)
    return pset

# Example
add_pset(model, wall, "Pset_WallCommon", {
    "IsExternal": True,
    "FireRating": "60",
    "ThermalTransmittance": 0.28,
    "AcousticRating": "Rw 45 dB"
})
```

---

## Querying an IFC File

```python
model = ifcopenshell.open("building.ifc")

# Get all walls
walls = model.by_type("IfcWall")
print(f"Walls: {len(walls)}")

# Get all spaces
spaces = model.by_type("IfcSpace")
for space in spaces:
    print(f"  Space: {space.Name} | {space.LongName}")

# Get element by GlobalId
element = model.by_guid("2O2Fr$t4X7Zf8NOew3FLOH")

# Get property set values
from ifcopenshell.util.element import get_psets
for wall in walls:
    psets = get_psets(wall)
    if "Pset_WallCommon" in psets:
        print(f"  {wall.Name}: {psets['Pset_WallCommon']}")

# Get storey of element
from ifcopenshell.util.element import get_container
for wall in walls:
    container = get_container(wall)
    if container:
        print(f"  {wall.Name} → {container.Name}")
```

---

## Save and Validate

```python
# Save
model.write("output.ifc")
print("Saved: output.ifc")

# Basic validation
def validate_ifc(filepath):
    model = ifcopenshell.open(filepath)
    
    # Check schema
    print(f"Schema: {model.schema}")
    
    # Check required entities
    required = ["IfcProject", "IfcSite", "IfcBuilding"]
    for entity_type in required:
        count = len(model.by_type(entity_type))
        status = "✓" if count > 0 else "✗ MISSING"
        print(f"  {entity_type}: {count} {status}")
    
    # Entity summary
    from collections import Counter
    types = Counter(e.is_a() for e in model)
    for t, c in sorted(types.items(), key=lambda x: -x[1])[:15]:
        print(f"  {t}: {c}")
```

---

## CLI Verification

```bash
# File info
python -c "
import ifcopenshell
m = ifcopenshell.open('output.ifc')
print(f'Schema: {m.schema}')
print(f'Total entities: {len(list(m))}')
print(f'Walls: {len(m.by_type(\"IfcWall\"))}')
print(f'Spaces: {len(m.by_type(\"IfcSpace\"))}')
print(f'Storeys: {len(m.by_type(\"IfcBuildingStorey\"))}')
"

# Validate with ifcopenshell validator (IFC4+)
python -m ifcopenshell.validate output.ifc

# Check file header
head -5 output.ifc
```

---

## IFC Entity Hierarchy (Architecture)

```
IfcProject
└── IfcSite
    └── IfcBuilding
        └── IfcBuildingStorey
            ├── IfcWall / IfcWallStandardCase
            ├── IfcSlab
            ├── IfcColumn
            ├── IfcBeam
            ├── IfcDoor
            ├── IfcWindow
            ├── IfcSpace
            └── IfcStair
```

---

## QA Checklist

- [ ] Schema declared correctly (IFC2x3, IFC4, or IFC4X3)
- [ ] Full spatial hierarchy: Project → Site → Building → Storey
- [ ] All elements assigned to a storey via `spatial.assign_container`
- [ ] Units assigned to project
- [ ] Geometry context defined
- [ ] All elements have valid GlobalId (unique)
- [ ] Property sets use standard Pset names where applicable
- [ ] File opens in BIMvision or similar viewer without errors
- [ ] No orphaned entities (not connected to spatial hierarchy)

---

## Common Mistakes to Avoid

- Missing spatial hierarchy (elements not assigned to storey — invisible in viewers)
- Duplicate GlobalIds (corrupts model)
- Using IFC2x3 entity names in IFC4 files
- Forgetting to assign units (coordinates will be uninterpretable)
- Not defining geometry context (elements have no geometry)
- Hardcoding coordinates without establishing a site reference point

---

## Dependencies

```bash
pip install ifcopenshell --break-system-packages
# Or via conda: conda install -c conda-forge ifcopenshell
```
