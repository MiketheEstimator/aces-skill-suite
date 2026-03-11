---
name: SKILL_GIS_GEOSPATIAL
description: "Create, read, transform, and analyze geospatial data in GeoJSON and Shapefile formats for AEC site and building workflows. Use when working with site boundaries, survey control points, utility corridors, zoning overlays, setbacks, grading extents, phasing zones, or any geometry that bridges site (GIS/civil) and building (BIM/CAD) coordinate systems. Covers CRS management, coordinate transformation, feature attribution, spatial joins, site analysis, and export to formats consumed by GIS, BIM, and CAD tools. Triggers: 'GeoJSON', 'Shapefile', '.shp', 'coordinate system', 'CRS', 'EPSG', 'site boundary', 'survey control', 'geospatial', 'GIS', 'spatial analysis', 'site-to-building', 'georeferencing', 'projection'."
---

# SKILL_GIS_GEOSPATIAL — GIS / Geospatial Skill

> **Scope:** GeoJSON and Shapefile production, transformation, and analysis for AEC
> workflows — particularly the site-to-building interface where GIS coordinate systems
> (geographic/projected) must be reconciled with BIM/CAD local coordinate systems.
> For BIM clash and BCF workflows see `SKILL_BIM_BCF_COORDINATE_CLASH`.
> For construction scope tied to spatial boundaries see `SKILL_AEC_SCOPE_EXTRACTION`.

## Quick Reference

| Task | Section |
|------|---------|
| Coordinate systems — CRS, EPSG, WGS84, state plane | [Coordinate Systems](#coordinate-systems) |
| GeoJSON — structure, read, write | [GeoJSON](#geojson) |
| Shapefile — read, write, inspect | [Shapefile](#shapefile) |
| CRS transformation — reproject geometry | [CRS Transformation](#crs-transformation) |
| Site-to-building coordinate bridge | [Site-to-Building Bridge](#site-to-building-bridge) |
| Feature attribution and properties | [Feature Attribution](#feature-attribution) |
| Spatial analysis — buffer, intersection, dissolve | [Spatial Analysis](#spatial-analysis) |
| Site boundary and setback generation | [Site Boundaries and Setbacks](#site-boundaries-and-setbacks) |
| Utility corridor mapping | [Utility Corridors](#utility-corridors) |
| Export to CAD/BIM formats | [Export to CAD and BIM](#export-to-cad-and-bim) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Unit Reference

| Unit System | Typical Use | EPSG Range |
|---|---|---|
| Geographic (degrees lat/lon) | WGS84 base, web maps, data exchange | EPSG:4326 |
| State Plane (US survey feet) | US site/civil, legal descriptions | EPSG:26700–26999 |
| UTM (meters) | Large sites, international projects | EPSG:32600–32799 |
| Local project CRS | BIM/CAD internal coordinates | Custom / project-defined |

```python
# Install
# pip install geopandas shapely pyproj fiona geojson

import geopandas as gpd
import pandas as pd
from shapely.geometry import (
    Point, LineString, Polygon, MultiPolygon,
    MultiLineString, MultiPoint, shape, mapping
)
from shapely.ops import unary_union, transform, split
import pyproj
from pyproj import CRS, Transformer
import json
from pathlib import Path
```

---

## Coordinate Systems

### CRS Fundamentals for AEC

```
GEOGRAPHIC CRS (angular units — degrees)
  EPSG:4326  WGS84 — GPS, GeoJSON standard, web services
             Order: (longitude, latitude) in spec; many tools use (lat, lon) — verify!

PROJECTED CRS (linear units — feet or meters)
  State Plane (US feet) — legal surveys, civil drawings, setback calculations
    EPSG:2263  New York Long Island (US survey feet)
    EPSG:2230  California Zone 6 (US survey feet)
    EPSG:3454  Texas South (US survey feet)
  UTM (meters) — large sites, international
    EPSG:32618  UTM Zone 18N (eastern US, meters)
    EPSG:32614  UTM Zone 14N (central US, meters)

LOCAL / PROJECT CRS
  BIM and CAD tools use a local Cartesian system (origin at a project base point).
  The bridge between project local and a real-world CRS requires:
    - Survey control points in both systems
    - A rotation angle (true north vs. project north)
    - A translation (real-world origin of project 0,0)
    - A scale factor (negligible for most building-scale projects)
```

### Look Up EPSG Code

```python
from pyproj import CRS

# Look up by name
crs = CRS.from_string("EPSG:2263")  # New York State Plane
print(crs.name)            # "NAD83 / New York Long Island"
print(crs.axis_info)       # axis order and units
print(crs.linear_units)    # "US survey foot"

# From WKT or PROJ string
crs_from_wkt = CRS.from_wkt(wkt_string)

# Identify CRS of an existing file
gdf = gpd.read_file("site_boundary.shp")
print(gdf.crs)             # e.g. EPSG:2263
print(gdf.crs.to_epsg())   # integer EPSG code

# Check axis order (critical for lon/lat vs lat/lon confusion)
print(crs.axis_info[0].direction)   # "east" = x=longitude; "north" = x=latitude
```

---

## GeoJSON

### GeoJSON Structure

```
GeoJSON spec (RFC 7946):
  - Always WGS84 (EPSG:4326)
  - Coordinate order: [longitude, latitude] (x, y)
  - Top-level type: FeatureCollection | Feature | Geometry

FeatureCollection
  └── features: [ Feature, Feature, ... ]
        └── Feature
              ├── type: "Feature"
              ├── geometry: { type, coordinates }
              └── properties: { key: value, ... }
```

### Read GeoJSON

```python
import geopandas as gpd
import json

# Via geopandas (recommended — handles CRS automatically)
gdf = gpd.read_file("site_boundary.geojson")
print(gdf.crs)          # should be EPSG:4326
print(gdf.head())
print(gdf.geometry.geom_type.unique())

# Via stdlib json (for inspection / raw manipulation)
with open("site_boundary.geojson") as f:
    fc = json.load(f)

print(f"Features: {len(fc['features'])}")
for feat in fc["features"]:
    print(feat["geometry"]["type"], feat["properties"])
```

### Write GeoJSON

```python
import geopandas as gpd
from shapely.geometry import Polygon, Point
import json

# From shapely geometries
polygons = [
    Polygon([(0,0),(1,0),(1,1),(0,1)]),
    Polygon([(2,0),(3,0),(3,1),(2,1)]),
]
properties = [
    {"zone": "A", "area_sf": 43560},
    {"zone": "B", "area_sf": 43560},
]

gdf = gpd.GeoDataFrame(properties, geometry=polygons, crs="EPSG:4326")
gdf.to_file("zones.geojson", driver="GeoJSON")

# Manual FeatureCollection construction
def build_feature_collection(geometries: list,
                               properties_list: list) -> dict:
    """Build a GeoJSON FeatureCollection from shapely geometries."""
    from shapely.geometry import mapping
    features = []
    for geom, props in zip(geometries, properties_list):
        features.append({
            "type":       "Feature",
            "geometry":   mapping(geom),
            "properties": props
        })
    return {"type": "FeatureCollection", "features": features}


fc = build_feature_collection(polygons, properties)
Path("output.geojson").write_text(
    json.dumps(fc, indent=2), encoding="utf-8"
)
```

### GeoJSON Geometry Types

```python
from shapely.geometry import (
    Point, LineString, Polygon,
    MultiPoint, MultiLineString, MultiPolygon
)

# Point — survey control, utility stub, column base
point = Point(-73.9857, 40.7484)   # lon, lat

# LineString — utility run, property line segment, road centerline
line = LineString([(-73.99, 40.75), (-73.98, 40.74), (-73.97, 40.73)])

# Polygon — site boundary, zoning lot, phase area, building footprint
# Last coordinate must equal first (closed ring)
boundary = Polygon([
    (-73.990, 40.750),
    (-73.985, 40.750),
    (-73.985, 40.745),
    (-73.990, 40.745),
    (-73.990, 40.750),   # close ring
])

# Polygon with hole (donut) — site boundary excluding existing easement
exterior = [(-73.990,40.750),(-73.980,40.750),(-73.980,40.740),(-73.990,40.740),(-73.990,40.750)]
hole      = [(-73.988,40.748),(-73.982,40.748),(-73.982,40.742),(-73.988,40.742),(-73.988,40.748)]
parcel_with_easement = Polygon(exterior, [hole])
```

---

## Shapefile

### Shapefile Components

```
A Shapefile is always four or more files with the same stem:
  .shp   — geometry (binary)
  .shx   — geometry index
  .dbf   — attribute table (dBase III format)
  .prj   — CRS definition (WKT)
  .cpg   — encoding declaration (e.g. UTF-8)

All four core files (.shp .shx .dbf .prj) must be present.
Missing .prj = unknown CRS — high risk of misalignment.
```

### Read Shapefile

```python
import geopandas as gpd

gdf = gpd.read_file("survey_control.shp")
print(gdf.crs)                  # CRS from .prj file
print(gdf.dtypes)               # column types
print(gdf[["geometry","ID","NORTHING","EASTING"]].head())

# Read specific columns only (large files)
gdf = gpd.read_file("parcel_fabric.shp",
                     include_fields=["APN", "OWNER", "ZONE_CODE"])
```

### Write Shapefile

```python
# geopandas to shapefile
gdf.to_file("output/site_boundary.shp")   # creates all 4 files

# Explicit CRS
gdf = gdf.set_crs("EPSG:2263")
gdf.to_file("output/site_boundary_sp.shp")

# Ensure encoding declared
gdf.to_file("output/site_boundary.shp", encoding="utf-8")

# Check output files exist
out_dir = Path("output")
required = [".shp", ".shx", ".dbf", ".prj"]
for ext in required:
    p = out_dir / f"site_boundary{ext}"
    assert p.exists(), f"Missing: {p}"
```

### Inspect Shapefile Without Loading

```python
import fiona

with fiona.open("parcels.shp") as src:
    print(f"CRS:    {src.crs}")
    print(f"Schema: {src.schema}")
    print(f"Count:  {len(src)}")
    print(f"Bounds: {src.bounds}")   # (minx, miny, maxx, maxy)
    # Read first feature only
    first = next(iter(src))
    print(first)
```

---

## CRS Transformation

### Reproject a GeoDataFrame

```python
import geopandas as gpd

# Load in source CRS
gdf = gpd.read_file("site_survey.shp")
print(f"Source CRS: {gdf.crs}")   # e.g. EPSG:2263

# Reproject to WGS84 for GeoJSON output
gdf_wgs84 = gdf.to_crs("EPSG:4326")
gdf_wgs84.to_file("site_survey.geojson", driver="GeoJSON")

# Reproject to UTM for metric area calculations
gdf_utm = gdf.to_crs("EPSG:32618")   # UTM Zone 18N, meters
gdf_utm["area_m2"] = gdf_utm.geometry.area
gdf_utm["area_sf"] = gdf_utm["area_m2"] * 10.7639   # m² to ft²
```

### Transform Individual Geometries

```python
from pyproj import Transformer
from shapely.ops import transform

# Always use always_xy=True to enforce (lon, lat) / (x, y) order
transformer = Transformer.from_crs(
    "EPSG:4326",    # source: WGS84
    "EPSG:2263",    # target: NY State Plane (US survey feet)
    always_xy=True
)

def reproject_geom(geom, transformer):
    """Reproject a single shapely geometry."""
    return transform(transformer.transform, geom)

# Example
point_wgs84  = Point(-73.9857, 40.7484)    # lon, lat
point_sp     = reproject_geom(point_wgs84, transformer)
print(f"State Plane: {point_sp.x:.2f}E, {point_sp.y:.2f}N (US survey feet)")
```

### Axis Order Trap

```python
# CRITICAL: WGS84 (EPSG:4326) axis order is (latitude, longitude) in the CRS spec
# but most software and GeoJSON use (longitude, latitude) = (x, y)
# always_xy=True forces x=longitude, y=latitude regardless of CRS axis order

# WITHOUT always_xy=True — will silently swap coordinates
bad_transformer = Transformer.from_crs("EPSG:4326", "EPSG:2263")

# WITH always_xy=True — safe
safe_transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:2263", always_xy=True
)
```

---

## Site-to-Building Bridge

The hardest problem in AEC geospatial work: BIM and CAD tools use a local Cartesian
coordinate system. GIS uses real-world projected coordinates.
The bridge requires three parameters: **origin**, **rotation**, and **scale**.

### Concepts

```
SURVEY BASE POINT (Revit) / PROJECT BASE POINT
  The real-world anchor of the BIM model.
  Has known coordinates in a real-world CRS (State Plane or UTM).
  Has a known angle-to-true-north.

PROJECT NORTH vs TRUE NORTH
  Project North: the Y-axis of the BIM/CAD drawing (usually aligned to a building face)
  True North:    geographic north
  Rotation angle: degrees clockwise from True North to Project North

SHARED COORDINATES (Revit)
  When Shared Coordinates are acquired from a civil file (DWG with survey data),
  Revit records the real-world CRS binding.
  Export using Shared Coordinates to get real-world-positioned geometry.

SCALE FACTOR
  State Plane and UTM projections introduce a small scale distortion.
  For building-scale work (< 1 mile), scale factor ≈ 1.0000 — negligible.
  For large campus or infrastructure projects, apply combined scale factor.
```

### Bridge: Local BIM → Real-World GIS

```python
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import rotate, translate, scale
from pyproj import Transformer

class SiteToBuildingBridge:
    """
    Converts geometry between BIM/CAD local coordinates and a real-world CRS.

    Parameters
    ----------
    survey_base_point_local : tuple (x, y)
        Coordinates of the survey base point in BIM local units (feet or meters).
    survey_base_point_realworld : tuple (easting, northing)
        Coordinates of the same point in the real-world CRS (projected, linear units).
    true_north_rotation_deg : float
        Degrees clockwise from Project North to True North.
        Positive = True North is clockwise from Project North.
    local_unit : str
        "feet" or "meters" — BIM/CAD internal unit.
    realworld_crs : str
        EPSG code of the real-world CRS (e.g. "EPSG:2263").
    """

    def __init__(self, survey_base_point_local: tuple,
                  survey_base_point_realworld: tuple,
                  true_north_rotation_deg: float,
                  local_unit: str = "feet",
                  realworld_crs: str = "EPSG:2263"):

        self.sbp_local      = survey_base_point_local
        self.sbp_real       = survey_base_point_realworld
        self.rotation_deg   = true_north_rotation_deg
        self.local_unit     = local_unit
        self.realworld_crs  = realworld_crs

        # Unit conversion factor to meters
        self.to_meters = 0.3048 if local_unit == "feet" else 1.0

        # Transformer from realworld CRS to WGS84 (for GeoJSON output)
        self.to_wgs84 = Transformer.from_crs(
            realworld_crs, "EPSG:4326", always_xy=True
        )


    def local_to_realworld(self, geom):
        """
        Convert a shapely geometry from BIM local coordinates to the real-world CRS.
        Steps: translate to origin → rotate by true north → translate to real-world origin.
        """
        # 1. Translate so survey base point is at origin
        geom = translate(geom,
                          xoff=-self.sbp_local[0],
                          yoff=-self.sbp_local[1])

        # 2. Rotate by true north correction
        #    Shapely rotate is counter-clockwise; true north rotation is clockwise
        geom = rotate(geom, -self.true_north_rotation_deg, origin=(0, 0))

        # 3. Translate to real-world survey base point
        geom = translate(geom,
                          xoff=self.sbp_real[0],
                          yoff=self.sbp_real[1])

        return geom

    @property
    def true_north_rotation_deg(self):
        return self.rotation_deg


    def local_to_geojson(self, geom) -> dict:
        """
        Convert local BIM geometry to GeoJSON (WGS84) via real-world CRS.
        """
        from shapely.ops import transform
        from shapely.geometry import mapping

        # Step 1: local → real-world projected
        geom_rw = self.local_to_realworld(geom)

        # Step 2: real-world projected → WGS84
        geom_wgs = transform(self.to_wgs84.transform, geom_rw)

        return {
            "type":     "Feature",
            "geometry": mapping(geom_wgs),
            "properties": {
                "crs_source":    "BIM local",
                "crs_realworld": self.realworld_crs,
                "crs_output":    "EPSG:4326"
            }
        }


    def realworld_to_local(self, geom):
        """
        Convert a shapely geometry from the real-world CRS to BIM local coordinates.
        Inverse of local_to_realworld.
        """
        from shapely.affinity import rotate, translate

        # 1. Translate so real-world survey base point is at origin
        geom = translate(geom,
                          xoff=-self.sbp_real[0],
                          yoff=-self.sbp_real[1])

        # 2. Rotate back (reverse direction)
        geom = rotate(geom, self.true_north_rotation_deg, origin=(0, 0))

        # 3. Translate to BIM survey base point
        geom = translate(geom,
                          xoff=self.sbp_local[0],
                          yoff=self.sbp_local[1])
        return geom


# Usage
bridge = SiteToBuildingBridge(
    survey_base_point_local     = (0.0, 0.0),          # BIM origin
    survey_base_point_realworld = (987654.32, 201234.56), # NY State Plane
    true_north_rotation_deg     = 14.5,                 # degrees clockwise
    local_unit                  = "feet",
    realworld_crs               = "EPSG:2263"
)

# Convert building footprint (in BIM local feet) to GeoJSON
bldg_footprint_local = Polygon([
    (0, 0), (120, 0), (120, 80), (0, 80), (0, 0)
])
feature = bridge.local_to_geojson(bldg_footprint_local)
```

### Survey Control Point Registry

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def build_control_point_registry(points: list[dict],
                                   source_crs: str = "EPSG:2263") -> gpd.GeoDataFrame:
    """
    Build a GeoDataFrame of survey control points.
    Each point dict: {"id", "name", "easting", "northing", "elevation_ft",
                       "local_x", "local_y", "type"}
    type: "primary_control" | "secondary_control" | "base_point" | "benchmark"
    """
    geoms = [Point(p["easting"], p["northing"]) for p in points]
    gdf   = gpd.GeoDataFrame(points, geometry=geoms, crs=source_crs)

    # Add WGS84 columns for GeoJSON compatibility
    gdf_wgs = gdf.to_crs("EPSG:4326")
    gdf["longitude"] = gdf_wgs.geometry.x
    gdf["latitude"]  = gdf_wgs.geometry.y

    return gdf


# Example
control_points = [
    {"id": "CP-01", "name": "NW Corner Monument",
     "easting": 987654.32, "northing": 201234.56, "elevation_ft": 42.5,
     "local_x": 0.0, "local_y": 0.0, "type": "base_point"},
    {"id": "CP-02", "name": "SE Corner Monument",
     "easting": 988234.67, "northing": 200654.21, "elevation_ft": 38.2,
     "local_x": 580.35, "local_y": -580.35, "type": "primary_control"},
]
cp_gdf = build_control_point_registry(control_points)
cp_gdf.to_file("survey_control_points.geojson", driver="GeoJSON")
```

---

## Feature Attribution

Properties are the non-geometric data attached to each feature.
For AEC use, properties must support traceability, scope linkage, and phase assignment.

### Standard AEC Feature Properties

```python
# Site boundary feature — minimum viable properties
SITE_BOUNDARY_SCHEMA = {
    "project_id":    str,    # links to AEC project register
    "parcel_id":     str,    # APN or legal lot identifier
    "area_sf":       float,
    "area_acres":    float,
    "perimeter_ft":  float,
    "zoning_code":   str,
    "setback_front": float,  # feet
    "setback_rear":  float,
    "setback_side":  float,
    "phase":         int,    # construction phase
    "status":        str,    # "existing" | "proposed" | "demolish"
}

# Utility corridor feature
UTILITY_SCHEMA = {
    "project_id":  str,
    "utility_type": str,   # "water" | "sewer" | "storm" | "gas" | "electric" | "telecom"
    "size_in":     float,  # pipe/conduit diameter in inches
    "material":    str,
    "depth_ft":    float,  # invert depth
    "status":      str,    # "existing" | "proposed" | "abandon"
    "spec_section": str,   # links to spec corpus
    "drawing_ref":  str,   # links to drawing sheet
}

# Phase zone feature
PHASE_SCHEMA = {
    "project_id":  str,
    "phase_id":    int,
    "phase_name":  str,
    "start_date":  str,    # ISO 8601
    "end_date":    str,
    "trades":      list,   # list of trade strings
    "constraints": list,   # links to CON-XXX from constraint register
}
```

### Compute Area and Perimeter Properties

```python
def enrich_polygon_properties(gdf: gpd.GeoDataFrame,
                                area_crs: str = "EPSG:32618") -> gpd.GeoDataFrame:
    """
    Add area (sf, acres) and perimeter (ft) columns.
    Reprojects to a metric CRS for accurate calculation, then converts.
    """
    gdf_metric = gdf.to_crs(area_crs)
    gdf["area_m2"]    = gdf_metric.geometry.area
    gdf["area_sf"]    = gdf["area_m2"] * 10.7639
    gdf["area_acres"] = gdf["area_m2"] / 4046.856
    gdf["perim_m"]    = gdf_metric.geometry.length
    gdf["perim_ft"]   = gdf["perim_m"] * 3.28084
    return gdf
```

---

## Spatial Analysis

```python
import geopandas as gpd
from shapely.ops import unary_union

# ── Buffer ────────────────────────────────────────────────────────────────────
# Always buffer in a projected (linear) CRS, not geographic (degrees)
gdf_proj = gdf.to_crs("EPSG:32618")          # meters
gdf_proj["buffer_50ft"] = gdf_proj.geometry.buffer(15.24)   # 50ft in meters

# ── Intersection ──────────────────────────────────────────────────────────────
# Features in both layers
intersection = gpd.overlay(layer_a, layer_b, how="intersection")

# ── Difference (clip) ─────────────────────────────────────────────────────────
# Features in A but not B (e.g. buildable area minus easements)
buildable = gpd.overlay(site_boundary, easements, how="difference")

# ── Union ─────────────────────────────────────────────────────────────────────
combined = gpd.overlay(phase_1, phase_2, how="union")

# ── Dissolve — merge features by attribute ───────────────────────────────────
dissolved = gdf.dissolve(by="zone_code", aggfunc="sum")

# ── Spatial join — attach attributes from one layer to another ───────────────
# "within": attach parcel attributes to points that fall within parcels
joined = gpd.sjoin(points_gdf, parcels_gdf, how="left", predicate="within")

# ── Convex hull and bounding box ─────────────────────────────────────────────
hull    = gdf.geometry.unary_union.convex_hull
bbox    = gdf.total_bounds   # [minx, miny, maxx, maxy]
```

---

## Site Boundaries and Setbacks

```python
def generate_setback_polygon(site_boundary: Polygon,
                              front_ft: float, rear_ft: float,
                              side_ft: float,
                              crs_proj: str = "EPSG:32618") -> dict:
    """
    Generate buildable area polygon by applying setbacks to a site boundary.
    Returns dict with site, setback zone, and buildable area geometries.
    """
    import geopandas as gpd
    from shapely.geometry import mapping

    # Work in projected CRS for accurate distances
    site_gdf = gpd.GeoDataFrame(geometry=[site_boundary], crs="EPSG:4326")
    site_proj = site_gdf.to_crs(crs_proj).geometry.iloc[0]

    # Uniform setback approximation (use directional for exact legal work)
    setback_dist_m = min(front_ft, rear_ft, side_ft) * 0.3048
    buildable_proj = site_proj.buffer(-setback_dist_m)

    # Back to WGS84
    result_gdf = gpd.GeoDataFrame(
        geometry=[site_proj, buildable_proj], crs=crs_proj
    ).to_crs("EPSG:4326")

    setback_zone = site_proj.difference(buildable_proj)
    setback_gdf  = gpd.GeoDataFrame(geometry=[setback_zone], crs=crs_proj).to_crs("EPSG:4326")

    return {
        "site_boundary": mapping(result_gdf.geometry.iloc[0]),
        "setback_zone":  mapping(setback_gdf.geometry.iloc[0]),
        "buildable_area": mapping(result_gdf.geometry.iloc[1]),
        "buildable_area_sf": buildable_proj.area * 10.7639,
    }
```

---

## Utility Corridors

```python
def build_utility_corridor(centerline: LineString,
                             width_ft: float,
                             utility_type: str,
                             depth_ft: float,
                             spec_section: str = "",
                             drawing_ref: str = "",
                             crs_proj: str = "EPSG:32618") -> gpd.GeoDataFrame:
    """
    Generate a utility corridor polygon from a centerline and corridor width.
    """
    gdf_line = gpd.GeoDataFrame(geometry=[centerline], crs="EPSG:4326")
    gdf_proj = gdf_line.to_crs(crs_proj)

    half_width_m = (width_ft / 2) * 0.3048
    corridor_proj = gdf_proj.geometry.iloc[0].buffer(
        half_width_m, cap_style=2   # flat caps
    )

    gdf_corridor = gpd.GeoDataFrame(
        [{
            "utility_type": utility_type,
            "width_ft":     width_ft,
            "depth_ft":     depth_ft,
            "length_ft":    gdf_proj.geometry.iloc[0].length * 3.28084,
            "spec_section": spec_section,
            "drawing_ref":  drawing_ref,
            "status":       "proposed",
        }],
        geometry=[corridor_proj],
        crs=crs_proj
    )
    return gdf_corridor.to_crs("EPSG:4326")
```

---

## Export to CAD and BIM

### To DXF (AutoCAD)

```python
import ezdxf

def geojson_to_dxf(geojson_path: str, output_path: str,
                    layer_map: dict = None) -> None:
    """
    Export GeoJSON features to DXF.
    layer_map: {feature_type: layer_name} — defaults to geometry type.
    Coordinates must be in a projected (linear) CRS before export.
    """
    import json
    from shapely.geometry import shape

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    with open(geojson_path) as f:
        fc = json.load(f)

    for feat in fc["features"]:
        geom  = shape(feat["geometry"])
        props = feat.get("properties", {})
        layer = (layer_map or {}).get(geom.geom_type, geom.geom_type.upper())

        if geom.geom_type == "Polygon":
            coords = list(geom.exterior.coords)
            msp.add_lwpolyline([(x, y) for x, y in coords],
                                close=True, dxfattribs={"layer": layer})

        elif geom.geom_type == "LineString":
            coords = list(geom.coords)
            msp.add_lwpolyline([(x, y) for x, y in coords],
                                dxfattribs={"layer": layer})

        elif geom.geom_type == "Point":
            msp.add_point((geom.x, geom.y, 0),
                           dxfattribs={"layer": layer})

    doc.saveas(output_path)
    print(f"DXF written: {output_path}")
```

### To CSV (for Revit/Navisworks import)

```python
def control_points_to_csv(gdf: gpd.GeoDataFrame,
                            output_path: str,
                            x_col: str = "easting",
                            y_col: str = "northing",
                            z_col: str = "elevation_ft") -> None:
    """
    Export survey control points to CSV for import into Revit Shared Coordinates.
    """
    export = gdf[[x_col, y_col, z_col, "id", "name", "type"]].copy()
    export.columns = ["Easting", "Northing", "Elevation", "ID", "Name", "Type"]
    export.to_csv(output_path, index=False)
    print(f"Control points CSV: {output_path}  ({len(export)} points)")
```

---

## Validation & QA

```python
def validate_geospatial_file(path: str,
                               expected_crs: str = None,
                               required_properties: list = None) -> dict:
    """
    Validate a GeoJSON or Shapefile for AEC use.
    """
    import geopandas as gpd
    errors, warnings = [], []

    try:
        gdf = gpd.read_file(path)
    except Exception as e:
        return {"pass": False, "errors": [f"Cannot read file: {e}"], "warnings": []}

    # CRS check
    if gdf.crs is None:
        errors.append("No CRS defined — .prj missing or GeoJSON missing CRS declaration")
    elif expected_crs and gdf.crs.to_epsg() != CRS(expected_crs).to_epsg():
        warnings.append(f"CRS is {gdf.crs.to_epsg()} — expected {expected_crs}")

    # Geometry validity
    invalid = gdf[~gdf.geometry.is_valid]
    if not invalid.empty:
        errors.append(f"{len(invalid)} invalid geometries — run gdf.geometry.buffer(0) to repair")

    # Empty geometries
    empty = gdf[gdf.geometry.is_empty]
    if not empty.empty:
        warnings.append(f"{len(empty)} empty geometries")

    # Null geometries
    nulls = gdf[gdf.geometry.isna()]
    if not nulls.empty:
        errors.append(f"{len(nulls)} null geometries")

    # Required properties
    if required_properties:
        for col in required_properties:
            if col not in gdf.columns:
                errors.append(f"Missing required property: '{col}'")
            elif gdf[col].isna().any():
                warnings.append(f"Null values in required property: '{col}'")

    # GeoJSON-specific: should be WGS84
    if path.endswith(".geojson") and gdf.crs and gdf.crs.to_epsg() != 4326:
        errors.append(f"GeoJSON must be EPSG:4326 (WGS84) per RFC 7946 — current CRS: {gdf.crs.to_epsg()}")

    print(f"Validation: {path}")
    print(f"  Features: {len(gdf)}  |  CRS: {gdf.crs}  |  Types: {gdf.geometry.geom_type.unique().tolist()}")
    for e in errors:   print(f"  ERROR: {e}")
    for w in warnings: print(f"  WARN:  {w}")
    print(f"  Verdict: {'FAIL' if errors else 'WARN' if warnings else 'PASS'}")

    return {"pass": not errors, "errors": errors, "warnings": warnings,
            "feature_count": len(gdf), "crs": str(gdf.crs)}
```

### QA Checklist

- [ ] CRS declared on every file — no missing `.prj`, no undefined GeoJSON CRS
- [ ] GeoJSON output is EPSG:4326 (WGS84) per RFC 7946
- [ ] Shapefiles include `.prj` — never deliver without it
- [ ] All geometries valid — `gdf.geometry.is_valid.all()`
- [ ] No null or empty geometries
- [ ] `always_xy=True` used in all `Transformer` calls
- [ ] Site-to-building bridge verified against at least two survey control points
- [ ] Areas and perimeters computed in projected CRS (not geographic)
- [ ] All features carry `project_id` for traceability back to session state
- [ ] DXF export reviewed in CAD before delivery — layer names and geometry types confirmed

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| Geometry lands in ocean after transform | Axis order (lat/lon swapped) | Use `always_xy=True` in all `Transformer` calls |
| Area calculation returns degrees² | Computing area in geographic CRS | Reproject to metric CRS before `.area` |
| Missing `.prj` in Shapefile delivery | geopandas didn't write CRS | Use `gdf.set_crs("EPSG:XXXX")` before `to_file()` |
| GeoJSON coordinate order wrong | RFC 7946 requires [lon, lat] but tool uses [lat, lon] | Verify with `always_xy=True`; check first coordinate against known landmark |
| BIM geometry offset after bridge | Wrong rotation sign | Shapely rotates CCW; true north correction is CW — negate the angle |
| Invalid polygon after buffer | Self-intersection in source | Apply `geom.buffer(0)` to repair before buffering |
| Setback polygon is empty | Site boundary too small for setback distance | Check input units — setback must be in same units as CRS |
| DXF export coordinate mismatch | Source is WGS84 (degrees) not projected | Reproject to State Plane or UTM before DXF export |

---

## Dependencies

```bash
pip install geopandas shapely pyproj fiona geojson
pip install ezdxf          # DXF export to AutoCAD
pip install pandas numpy

# System dependencies (Linux)
sudo apt install libgdal-dev libspatialindex-dev
# macOS
brew install gdal spatialindex
```
