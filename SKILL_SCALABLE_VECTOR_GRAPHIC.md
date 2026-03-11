---
name: scalable-vector-graphic
description: "Use this skill when producing .svg files — icons, diagrams, floor plan overlays, charts, logos, or illustrations. Covers hand-crafted SVG, Python-generated SVG, and svgwrite. Trigger on any .svg output request or when a resolution-independent graphic is needed."
---

# Scalable Vector Graphic SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Hand-crafted SVG | Direct XML authoring |
| Programmatic SVG | `svgwrite` (Python) |
| Diagrams / charts | `matplotlib` → SVG export |
| Complex paths | Inkscape CLI |
| SVG → PDF | `cairosvg` or Inkscape CLI |
| SVG → PNG | `cairosvg` or Inkscape CLI |

---

## SVG File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 800 600"
     width="800" height="600">

  <!-- Definitions: gradients, patterns, clip paths -->
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#1E2761;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#065A82;stop-opacity:1" />
    </linearGradient>
    <style>
      text { font-family: Arial, sans-serif; }
      .label { font-size: 12px; fill: #333333; }
      .title { font-size: 20px; font-weight: bold; fill: #1E2761; }
    </style>
  </defs>

  <!-- Background -->
  <rect width="800" height="600" fill="#F5F7FA"/>

  <!-- Header bar with gradient -->
  <rect x="0" y="0" width="800" height="60" fill="url(#headerGrad)"/>
  <text x="24" y="38" font-size="22" font-weight="bold" fill="white">Diagram Title</text>

  <!-- Grouped elements -->
  <g id="nodes" transform="translate(50, 100)">
    <rect x="0" y="0" width="160" height="60" rx="8" ry="8"
          fill="#FFFFFF" stroke="#1E2761" stroke-width="2"/>
    <text x="80" y="35" text-anchor="middle" class="label">Node Label</text>
  </g>

  <!-- Arrow -->
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7"
            refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#1E2761"/>
    </marker>
  </defs>
  <line x1="210" y1="130" x2="340" y2="130"
        stroke="#1E2761" stroke-width="2"
        marker-end="url(#arrow)"/>

</svg>
```

---

## svgwrite (Python)

```python
# pip install svgwrite --break-system-packages
import svgwrite

dwg = svgwrite.Drawing("output.svg", size=("800px", "600px"),
                        viewBox="0 0 800 600")

# Background
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#F5F7FA"))

# Header
dwg.add(dwg.rect(insert=(0, 0), size=(800, 60), fill="#1E2761"))
dwg.add(dwg.text("Diagram Title",
                  insert=(24, 38),
                  font_size=22, font_weight="bold",
                  fill="white", font_family="Arial"))

# Shape
g = dwg.g(id="nodes")
g.add(dwg.rect(insert=(50, 100), size=(160, 60),
               rx=8, ry=8, fill="white",
               stroke="#1E2761", stroke_width=2))
g.add(dwg.text("Node", insert=(130, 135),
               text_anchor="middle", font_size=14,
               fill="#333333", font_family="Arial"))
dwg.add(g)

dwg.save()
```

---

## Matplotlib → SVG

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(['Q1', 'Q2', 'Q3', 'Q4'], [125, 148, 132, 165], color='#1E2761')
ax.set_title('Quarterly Revenue', fontsize=16, fontweight='bold')
ax.set_ylabel('$000s')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("chart.svg", format="svg", bbox_inches="tight", dpi=150)
plt.close()
```

---

## Conversion

```bash
# SVG → PNG (cairosvg)
pip install cairosvg --break-system-packages
python -c "
import cairosvg
cairosvg.svg2png(url='output.svg', write_to='output.png', scale=2.0)
"

# SVG → PDF
python -c "
import cairosvg
cairosvg.svg2pdf(url='output.svg', write_to='output.pdf')
"

# Inkscape CLI
inkscape output.svg --export-filename=output.png --export-dpi=150
inkscape output.svg --export-filename=output.pdf
```

---

## CLI Verification

```bash
# Validate SVG is well-formed XML
python -c "
from lxml import etree
tree = etree.parse('output.svg')
print('Valid SVG XML ✓')
print('ViewBox:', tree.getroot().get('viewBox'))
"

# Check file size
wc -c output.svg

# Preview element count
python -c "
from lxml import etree
tree = etree.parse('output.svg')
print('Elements:', len(tree.findall('.//*')))
"
```

---

## QA Checklist

- [ ] `viewBox` defined on root `<svg>` element
- [ ] `xmlns="http://www.w3.org/2000/svg"` declared
- [ ] All `id` attributes are unique
- [ ] No absolute pixel positions that break at different viewBox scales
- [ ] Fonts specified with fallbacks (`Arial, sans-serif`)
- [ ] Text remains readable at 50% scale
- [ ] Arrow markers defined in `<defs>` and referenced correctly
- [ ] Gradient/pattern `id` values match their `url()` references
- [ ] File is valid XML (parses without error)

---

## Common Mistakes to Avoid

- Omitting `viewBox` (SVG won't scale correctly)
- Hardcoding `width`/`height` in px without `viewBox` (breaks responsiveness)
- Duplicate `id` attributes (breaks `url()` references)
- Using CSS `font-family` not available in all SVG renderers (always include fallbacks)
- Forgetting `text-anchor="middle"` for centered labels
- Overly complex paths without grouping (hard to maintain)

---

## Dependencies

```bash
pip install svgwrite --break-system-packages
pip install cairosvg --break-system-packages
pip install matplotlib --break-system-packages
pip install lxml --break-system-packages
# Inkscape: system-installed (may not be in all sandboxes)
```
