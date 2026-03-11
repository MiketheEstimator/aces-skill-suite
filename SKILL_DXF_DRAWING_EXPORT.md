---
name: dxf-drawing-export
description: "Use this skill when producing .dxf files — 2D CAD drawings, site plans, floor plans, section drawings, or geometry exports for architecture and construction. Covers ezdxf, layer management, blocks, dimensions, and text styles. Trigger on any .dxf output request."
---

# DXF Drawing Export SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create DXF | `ezdxf` (Python) |
| Read/edit DXF | `ezdxf` |
| Verify output | `ezdxf` audit + DXF viewer |
| Convert DXF → PDF | LibreOffice Draw or Inkscape CLI |
| DXF → DWG | ODA File Converter (separate skill) |

---

## Setup and Document Creation

```python
# pip install ezdxf --break-system-packages
import ezdxf
from ezdxf.enums import TextEntityAlignment

# Create new DXF document (R2010 = AutoCAD 2010+ format, good compatibility)
doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4  # 4 = mm, 1 = inch, 6 = meters
msp = doc.modelspace()
```

---

## Layer Management

```python
# Define layers before drawing
def setup_layers(doc):
    layers = [
        # (name,         color_index, linetype,    lineweight)
        ("A-WALL",       2,           "CONTINUOUS", 50),   # Yellow, walls
        ("A-DOOR",       1,           "CONTINUOUS", 25),   # Red, doors
        ("A-WINDOW",     3,           "CONTINUOUS", 18),   # Green, windows
        ("A-ANNO-TEXT",  7,           "CONTINUOUS", 13),   # White/black, text
        ("A-ANNO-DIM",   4,           "CONTINUOUS", 13),   # Cyan, dimensions
        ("A-GRID",       8,           "CENTER2",    13),   # Gray, grid lines
        ("A-BORDER",     7,           "CONTINUOUS", 50),   # White/black, border
    ]
    for name, color, linetype, lw in layers:
        if linetype != "CONTINUOUS":
            try:
                doc.linetypes.add(linetype)
            except:
                pass
        layer = doc.layers.add(name)
        layer.color = color
        layer.linetype = linetype
        layer.lineweight = lw
    return doc
```

---

## Drawing Entities

```python
# Line
msp.add_line(
    start=(0, 0),
    end=(5000, 0),
    dxfattribs={"layer": "A-WALL", "lineweight": 50}
)

# Polyline (wall outline)
points = [(0,0), (5000,0), (5000,3000), (0,3000), (0,0)]
msp.add_lwpolyline(
    points,
    dxfattribs={"layer": "A-WALL", "lineweight": 50, "closed": True}
)

# Rectangle helper
def add_rect(msp, x, y, width, height, layer, lw=25):
    pts = [(x,y), (x+width,y), (x+width,y+height), (x,y+height)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": layer, "lineweight": lw, "closed": True})

# Circle
msp.add_circle(
    center=(2500, 1500),
    radius=500,
    dxfattribs={"layer": "A-ANNO-TEXT"}
)

# Arc
msp.add_arc(
    center=(0, 0),
    radius=900,
    start_angle=0,
    end_angle=90,
    dxfattribs={"layer": "A-DOOR"}
)

# Hatch (fill pattern)
hatch = msp.add_hatch(color=254, dxfattribs={"layer": "A-WALL"})
hatch.set_pattern_fill("ANSI31", scale=50)  # Concrete hatch
boundary = hatch.paths.add_polyline_path(
    [(0,0), (200,0), (200,3000), (0,3000)],
    is_closed=True
)
```

---

## Text and Annotations

```python
# Single-line text
msp.add_text(
    "GROUND FLOOR PLAN",
    height=250,
    dxfattribs={
        "layer": "A-ANNO-TEXT",
        "style": "STANDARD",
        "insert": (2500, -500),
    }
).set_placement((2500, -500), align=TextEntityAlignment.MIDDLE_CENTER)

# Multi-line text (MTEXT)
msp.add_mtext(
    "NOTES:\n1. All dimensions in mm.\n2. Do not scale from drawing.",
    dxfattribs={
        "layer": "A-ANNO-TEXT",
        "insert": (100, -800),
        "char_height": 150,
        "width": 3000,
    }
)
```

---

## Dimensions

```python
# Horizontal dimension
dim = msp.add_linear_dim(
    base=(0, -200),         # Dimension line position
    p1=(0, 0),              # Start point
    p2=(5000, 0),           # End point
    dimstyle="EZDXF",
    dxfattribs={"layer": "A-ANNO-DIM"}
)
dim.render()

# Aligned dimension (follows entity angle)
dim2 = msp.add_aligned_dim(
    p1=(0, 0),
    p2=(3000, 4000),
    distance=300,
    dxfattribs={"layer": "A-ANNO-DIM"}
)
dim2.render()
```

---

## Title Block / Border

```python
def add_title_block(msp, sheet_width=420, sheet_height=297):
    """Add A3 title block border (dimensions in mm)."""
    # Outer border
    add_rect(msp, 0, 0, sheet_width, sheet_height, "A-BORDER", lw=50)
    
    # Title block at bottom
    tb_height = 40
    add_rect(msp, 0, 0, sheet_width, tb_height, "A-BORDER", lw=35)
    
    # Column dividers
    dividers = [sheet_width * 0.25, sheet_width * 0.55, sheet_width * 0.75]
    for x in dividers:
        msp.add_line((x, 0), (x, tb_height), dxfattribs={"layer": "A-BORDER"})
    
    # Labels
    labels = [
        (sheet_width * 0.125, 15, "PROJECT", 5),
        (sheet_width * 0.40,  15, "DRAWING TITLE", 5),
        (sheet_width * 0.65,  15, "SCALE", 5),
        (sheet_width * 0.875, 15, "DATE / REV", 5),
    ]
    for x, y, text, h in labels:
        msp.add_text(text, height=h, dxfattribs={"layer": "A-ANNO-TEXT",
                     "insert": (x, y)}).set_placement(
                     (x, y), align=TextEntityAlignment.MIDDLE_CENTER)
```

---

## Save and Audit

```python
# Audit before saving
auditor = doc.audit()
if auditor.has_errors:
    print(f"Audit errors: {len(auditor.errors)}")
    for error in auditor.errors:
        print(f"  {error}")
else:
    print("Audit passed ✓")

doc.saveas("output.dxf")
print("Saved: output.dxf")
```

---

## CLI Verification

```bash
# Audit DXF file
python -c "
import ezdxf
doc = ezdxf.readfile('output.dxf')
auditor = doc.audit()
print(f'Version: {doc.dxfversion}')
print(f'Entities: {len(list(doc.modelspace()))}')
print(f'Layers: {[l.dxf.name for l in doc.layers]}')
print(f'Audit errors: {len(auditor.errors)}')
"

# List all entities
python -c "
import ezdxf
from collections import Counter
doc = ezdxf.readfile('output.dxf')
types = Counter(e.dxftype() for e in doc.modelspace())
for t, count in sorted(types.items()):
    print(f'  {t}: {count}')
"

# Check extents
python -c "
import ezdxf
doc = ezdxf.readfile('output.dxf')
msp = doc.modelspace()
extents = ezdxf.bbox.extents(msp)
print(f'Extents: {extents}')
"
```

---

## QA Checklist

- [ ] Audit passes with zero errors
- [ ] All entities on correct named layers
- [ ] Units set correctly in `$INSUNITS`
- [ ] Title block populated with project information
- [ ] Dimensions rendered (`.render()` called on all dim objects)
- [ ] No entities on Layer 0 (Layer 0 is for blocks/inserts only)
- [ ] DXF version appropriate for target software
- [ ] Text heights legible at drawing scale
- [ ] File opens in DXF viewer without errors

---

## Layer Naming Convention (AIA/NCS Standard)

```
Format: Discipline-Major-Minor-Status
Example: A-WALL-FULL-E (Architecture, Wall, Full height, Existing)

Discipline codes: A=Arch, S=Structural, M=Mechanical, E=Electrical, P=Plumbing, C=Civil
```

---

## Common Mistakes to Avoid

- Drawing on Layer 0 (reserved for block definitions)
- Forgetting to call `.render()` on dimension objects (they won't appear)
- Setting `$INSUNITS` incorrectly (coordinates will be misinterpreted)
- Using color index 0 (ByBlock) or 256 (ByLayer) when explicit color needed
- Hardcoding lineweights to 0 (hairline — invisible in print)
- Not auditing before saving

---

## Dependencies

```bash
pip install ezdxf --break-system-packages
# Optional: matplotlib for DXF preview
pip install matplotlib --break-system-packages
```
