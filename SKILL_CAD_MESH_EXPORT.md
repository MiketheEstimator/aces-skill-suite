---
name: SKILL_CAD_MESH_EXPORT
description: "Exporting standardized 3D mesh geometry for printing or external rendering. Use when producing .obj or .stl files from geometry data, converting between mesh formats, or preparing models for 3D printing or render engines. Architecture/Construction context. Triggers: 'OBJ file', 'STL file', '3D mesh', '3D print', 'mesh export', 'geometry export', '.stl', '.obj'."
---

# SKILL_CAD_MESH_EXPORT — OBJ / STL 3D Mesh Export Skill

## Quick Reference

| Task | Section |
|------|---------|
| Format comparison | [Format Comparison](#format-comparison) |
| Write OBJ | [OBJ Format](#obj-format) |
| Write STL (binary + ASCII) | [STL Format](#stl-format) |
| Mesh generation helpers | [Mesh Generation](#mesh-generation) |
| Format conversion | [Format Conversion](#format-conversion) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Format Comparison

| Feature | OBJ | STL Binary |
|---------|-----|-----------|
| Geometry | Vertices, faces, normals, UVs | Triangles only |
| Materials | Yes (via .mtl) | No |
| Colours | Yes (via .mtl) | No (non-standard) |
| Normals | Optional, per-vertex | Per-triangle |
| File size | Larger (ASCII) | Compact |
| 3D printing | Less common | Standard |
| Rendering | Preferred | Less common |
| Textures | Yes | No |

**Use OBJ for:** Rendering, visualisation, BIM-to-renderer workflows.
**Use STL for:** 3D printing, CNC, structural analysis software.

---

## OBJ Format

### Specification

```
# Comment
mtllib material.mtl      # reference material library

o ObjectName             # object name

v  x y z                 # vertex (float)
vn nx ny nz              # vertex normal (unit vector)
vt u v                   # texture coordinate (0–1)

g GroupName              # group

usemtl MaterialName      # apply material

f v1 v2 v3               # triangular face (1-based indices)
f v1/vt1 v2/vt2 v3/vt3          # face with UVs
f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3  # face with UVs + normals
f v1//vn1 v2//vn2 v3//vn3           # face with normals, no UV
```

### Write OBJ

```python
from pathlib import Path

def write_obj(vertices: list, faces: list, normals: list = None,
              output_path: str = "output.obj",
              object_name: str = "Object") -> None:
    """
    Write geometry to OBJ file.

    vertices: list of (x, y, z) tuples
    faces:    list of (i, j, k) tuples — 0-based vertex indices
    normals:  list of (nx, ny, nz) unit vectors (optional)
    """
    lines = [
        "# OBJ Export",
        f"# Vertices: {len(vertices)}  Faces: {len(faces)}",
        f"o {object_name}",
        ""
    ]

    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")

    if normals:
        lines.append("")
        for n in normals:
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")

    lines.append("")

    for f in faces:
        if normals:
            # OBJ is 1-based
            lines.append(
                f"f {f[0]+1}//{f[0]+1} {f[1]+1}//{f[1]+1} {f[2]+1}//{f[2]+1}"
            )
        else:
            lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")

    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OBJ written: {output_path} ({len(vertices)} verts, {len(faces)} faces)")


# Example — unit cube
vertices = [
    (0,0,0),(1,0,0),(1,1,0),(0,1,0),
    (0,0,1),(1,0,1),(1,1,1),(0,1,1),
]
faces = [
    (0,2,1),(0,3,2),  # bottom
    (4,5,6),(4,6,7),  # top
    (0,1,5),(0,5,4),  # front
    (1,2,6),(1,6,5),  # right
    (2,3,7),(2,7,6),  # back
    (3,0,4),(3,4,7),  # left
]
write_obj(vertices, faces, output_path="cube.obj")
```

### Write OBJ + MTL (with materials)

```python
def write_obj_with_material(vertices: list, faces: list,
                             material_name: str, colour_rgb: tuple,
                             output_prefix: str) -> None:
    """Write OBJ with companion MTL material file."""

    # MTL file
    r, g, b = [c / 255.0 for c in colour_rgb]
    mtl_lines = [
        "# Material file",
        f"newmtl {material_name}",
        f"Kd {r:.4f} {g:.4f} {b:.4f}",   # diffuse colour
        "Ka 0.1 0.1 0.1",                 # ambient
        "Ks 0.0 0.0 0.0",                 # specular
        "d 1.0",                          # opacity (1 = opaque)
    ]
    Path(f"{output_prefix}.mtl").write_text(
        "\n".join(mtl_lines), encoding="utf-8"
    )

    # OBJ file
    lines = [
        f"mtllib {output_prefix}.mtl",
        "o Object",
        f"usemtl {material_name}",
        ""
    ]
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    lines.append("")
    for f in faces:
        lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")

    Path(f"{output_prefix}.obj").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"Written: {output_prefix}.obj + {output_prefix}.mtl")
```

---

## STL Format

### Binary STL (preferred for 3D printing)

```python
import struct
from pathlib import Path

def write_stl_binary(triangles: list, output_path: str,
                     header: str = "STL Export") -> None:
    """
    Write binary STL file.

    triangles: list of dicts:
        { 'normal': (nx,ny,nz), 'v1': (x,y,z), 'v2': (x,y,z), 'v3': (x,y,z) }
    """
    header_bytes = header.encode("utf-8")[:80].ljust(80, b"\x00")

    with open(output_path, "wb") as f:
        f.write(header_bytes)
        f.write(struct.pack("<I", len(triangles)))   # uint32 triangle count

        for tri in triangles:
            f.write(struct.pack("<fff", *tri["normal"]))
            f.write(struct.pack("<fff", *tri["v1"]))
            f.write(struct.pack("<fff", *tri["v2"]))
            f.write(struct.pack("<fff", *tri["v3"]))
            f.write(struct.pack("<H", 0))            # attribute byte count

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"STL written: {output_path} ({len(triangles)} triangles, {size_kb:.1f} KB)")
```

### ASCII STL

```python
def write_stl_ascii(triangles: list, output_path: str,
                    solid_name: str = "solid") -> None:
    """Write ASCII STL (human-readable; larger file than binary)."""
    lines = [f"solid {solid_name}"]

    for tri in triangles:
        n = tri["normal"]
        lines.append(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        lines.append("    outer loop")
        for key in ("v1", "v2", "v3"):
            v = tri[key]
            lines.append(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")

    lines.append(f"endsolid {solid_name}")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"STL ASCII written: {output_path} ({len(triangles)} triangles)")
```

---

## Mesh Generation

### Compute Face Normal

```python
import math

def compute_normal(v1: tuple, v2: tuple, v3: tuple) -> tuple:
    """Compute unit normal for a triangle face (right-hand rule)."""
    ax, ay, az = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
    bx, by, bz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
    nx = ay*bz - az*by
    ny = az*bx - ax*bz
    nz = ax*by - ay*bx
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length == 0:
        return (0.0, 0.0, 1.0)
    return (nx/length, ny/length, nz/length)
```

### Faces + Vertices → Triangle List (for STL)

```python
def mesh_to_triangles(vertices: list, faces: list) -> list:
    """Convert indexed mesh to flat triangle list for STL export."""
    triangles = []
    for f in faces:
        v1 = vertices[f[0]]
        v2 = vertices[f[1]]
        v3 = vertices[f[2]]
        triangles.append({
            "normal": compute_normal(v1, v2, v3),
            "v1": v1, "v2": v2, "v3": v3
        })
    return triangles
```

### Primitive Generators

```python
import math

def make_box(width: float, depth: float, height: float,
             origin=(0,0,0)) -> tuple:
    """Generate box mesh. Returns (vertices, faces)."""
    ox, oy, oz = origin
    w, d, h = width, depth, height
    verts = [
        (ox,   oy,   oz),   # 0
        (ox+w, oy,   oz),   # 1
        (ox+w, oy+d, oz),   # 2
        (ox,   oy+d, oz),   # 3
        (ox,   oy,   oz+h), # 4
        (ox+w, oy,   oz+h), # 5
        (ox+w, oy+d, oz+h), # 6
        (ox,   oy+d, oz+h), # 7
    ]
    faces = [
        (0,2,1),(0,3,2),   # bottom  (z-)
        (4,5,6),(4,6,7),   # top     (z+)
        (0,1,5),(0,5,4),   # front   (y-)
        (1,2,6),(1,6,5),   # right   (x+)
        (2,3,7),(2,7,6),   # back    (y+)
        (3,0,4),(3,4,7),   # left    (x-)
    ]
    return verts, faces


def make_cylinder(radius: float, height: float,
                  segments: int = 32,
                  origin=(0,0,0)) -> tuple:
    """Generate cylinder mesh. Returns (vertices, faces)."""
    ox, oy, oz = origin
    verts = []
    faces = []

    # Bottom cap centre (index 0), top cap centre (index 1)
    verts.append((ox, oy, oz))
    verts.append((ox, oy, oz + height))

    # Circumference vertices: bottom (2..segments+1), top (segments+2..2*segments+1)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = ox + radius * math.cos(angle)
        y = oy + radius * math.sin(angle)
        verts.append((x, y, oz))           # bottom ring

    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = ox + radius * math.cos(angle)
        y = oy + radius * math.sin(angle)
        verts.append((x, y, oz + height))  # top ring

    b_off = 2               # bottom ring offset
    t_off = 2 + segments    # top ring offset

    for i in range(segments):
        next_i = (i + 1) % segments

        # Bottom cap (CW from below)
        faces.append((0, b_off + next_i, b_off + i))

        # Top cap (CCW from above)
        faces.append((1, t_off + i, t_off + next_i))

        # Side quad as two triangles
        faces.append((b_off + i, b_off + next_i, t_off + next_i))
        faces.append((b_off + i, t_off + next_i, t_off + i))

    return verts, faces
```

### Full Pipeline Example

```python
# Generate a box, export as both OBJ and STL
verts, faces = make_box(width=5.0, depth=3.0, height=2.5)

# OBJ
write_obj(verts, faces, output_path="column_pad.obj", object_name="ColumnPad")

# STL (binary)
triangles = mesh_to_triangles(verts, faces)
write_stl_binary(triangles, "column_pad.stl")
```

---

## Format Conversion

### OBJ → STL

```python
def obj_to_stl(obj_path: str, stl_path: str) -> None:
    """Convert OBJ file to binary STL."""
    vertices = []
    faces = []

    with open(obj_path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == "v":
                vertices.append(tuple(float(x) for x in parts[1:4]))
            elif parts[0] == "f":
                # Handle v, v/vt, v/vt/vn, v//vn formats
                idx = []
                for token in parts[1:]:
                    vi = int(token.split("/")[0]) - 1   # 1-based → 0-based
                    idx.append(vi)
                # Fan triangulation for quads or n-gons
                for i in range(1, len(idx) - 1):
                    faces.append((idx[0], idx[i], idx[i+1]))

    triangles = mesh_to_triangles(vertices, faces)
    write_stl_binary(triangles, stl_path)
    print(f"Converted: {obj_path} → {stl_path}")


# Using trimesh (recommended for complex conversions)
def convert_mesh(input_path: str, output_path: str) -> None:
    """Convert any mesh format to any other using trimesh."""
    import trimesh
    mesh = trimesh.load(input_path)
    mesh.export(output_path)
    print(f"Converted: {input_path} → {output_path}")
```

### CLI Conversion (Blender headless)

```bash
# Blender can batch-convert mesh formats headlessly

# OBJ → STL
blender --background --python - <<'EOF'
import bpy
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.obj(filepath="input.obj")
bpy.ops.export_mesh.stl(filepath="output.stl")
EOF

# STL → OBJ
blender --background --python - <<'EOF'
import bpy
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_mesh.stl(filepath="input.stl")
bpy.ops.export_scene.obj(filepath="output.obj")
EOF
```

---

## Validation & QA

```python
import struct
from pathlib import Path

def validate_stl_binary(path: str) -> bool:
    errors = []
    data = Path(path).read_bytes()

    if len(data) < 84:
        print("ERROR: File too small to be a valid binary STL")
        return False

    n_triangles = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + n_triangles * 50  # 50 bytes per triangle

    print(f"Declared triangles: {n_triangles}")
    print(f"Expected file size: {expected_size} bytes")
    print(f"Actual file size:   {len(data)} bytes")

    if len(data) != expected_size:
        errors.append(
            f"SIZE MISMATCH: expected {expected_size}, got {len(data)}"
        )

    if n_triangles == 0:
        errors.append("ERROR: Zero triangles declared")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: STL binary structure is valid")
    return True


def validate_obj(path: str) -> bool:
    errors = []
    vertex_count = 0
    face_count = 0
    max_face_index = 0

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == "v":
                vertex_count += 1
            elif parts[0] == "f":
                face_count += 1
                for token in parts[1:]:
                    vi = abs(int(token.split("/")[0]))
                    max_face_index = max(max_face_index, vi)

    print(f"Vertices: {vertex_count}  Faces: {face_count}")

    if vertex_count == 0:
        errors.append("ERROR: No vertices found")
    if face_count == 0:
        errors.append("ERROR: No faces found")
    if max_face_index > vertex_count:
        errors.append(
            f"INDEX ERROR: Face references vertex {max_face_index} "
            f"but only {vertex_count} vertices exist"
        )

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: OBJ structure is valid")
    return True
```

### QA Checklist

- [ ] Vertex count > 0
- [ ] Face count > 0
- [ ] No face index references out-of-range vertex
- [ ] STL binary: file size matches 84 + (n_triangles × 50)
- [ ] Normals are unit vectors (length ≈ 1.0)
- [ ] Winding order is consistent (right-hand rule for outward normals)
- [ ] No degenerate faces (zero-area triangles)
- [ ] Mesh is watertight / manifold (required for 3D printing)
- [ ] Units documented in header/comment (mm vs m vs inches)
- [ ] Opens correctly in target application (Slicer, Blender, Navisworks)

### QA Loop

1. Generate mesh
2. Run `validate_stl_binary()` or `validate_obj()`
3. Open in mesh viewer (MeshLab, Blender) — visual check
4. For 3D printing: check manifold status in slicer (PrusaSlicer, Cura)
5. Fix non-manifold edges and degenerate faces
6. **Do not send to printer / renderer until manifold check passes**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Inside-out faces | Wrong winding order | Reverse face index order: `(a,b,c)` → `(a,c,b)` |
| Mesh not watertight | Missing faces or open edges | Close all holes; check for duplicate vertices |
| Scale wrong in target app | Units mismatch (mm vs m) | Add `# Units: mm` comment; scale on export |
| STL size mismatch | ASCII STL opened as binary | Detect format: `file.read(5) == b"solid"` |
| OBJ materials missing | .mtl file not alongside .obj | Keep .obj and .mtl in same directory |
| Normals flipped in render | Incorrect normal direction | Recalculate normals: `trimesh.fix_normals()` |
| Non-manifold edges | T-junctions or duplicate faces | Use `trimesh.repair.fix_winding()` |

---

## Dependencies

```bash
# Python stdlib only for basic read/write
import struct   # binary STL
import math     # normals

# Recommended mesh library (handles all formats + repair)
pip install trimesh

# Visualisation / conversion
pip install open3d     # point cloud + mesh tools
# or: install Blender (headless available)
# or: install MeshLab (GUI mesh repair)
```
