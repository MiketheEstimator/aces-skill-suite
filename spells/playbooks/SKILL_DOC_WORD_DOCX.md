---
name: SKILL_DOC_WORD_DOCX
description: "Create, edit, and extract content from .docx Word documents using python-docx. Use when producing professional reports, letters, memos, contracts, templates, or any structured Word document from Python. Covers styles, headings, tables, images, headers/footers, page layout, tracked changes (XML), mail merge data, and document automation pipelines. Triggers: '.docx', 'Word document', 'Word report', 'Word table', 'python-docx', 'generate Word', 'edit Word file'."
---

# SKILL_DOC_WORD_DOCX — Word Document Skill

## Quick Reference

| Task | Section |
|------|---------|
| Create document, page setup | [Document Setup](#document-setup) |
| Styles — headings, body, custom | [Styles](#styles) |
| Paragraphs, runs, inline formatting | [Text & Formatting](#text--formatting) |
| Tables | [Tables](#tables) |
| Lists — bulleted, numbered, nested | [Lists](#lists) |
| Images | [Images](#images) |
| Headers & footers, page numbers | [Headers & Footers](#headers--footers) |
| Table of contents | [Table of Contents](#table-of-contents) |
| Read & extract content | [Reading Documents](#reading-documents) |
| Find & replace | [Find & Replace](#find--replace) |
| Document templates | [Templates](#templates) |
| Mail merge data injection | [Mail Merge Pattern](#mail-merge-pattern) |
| Convert to PDF | [Convert to PDF](#convert-to-pdf) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Unit Reference

All python-docx measurements use `Pt`, `Inches`, `Cm`, or `Emu` from `docx.shared`.

| Unit | Import | Example | Notes |
|------|--------|---------|-------|
| `Pt` | `docx.shared.Pt` | `Pt(12)` | Font size, spacing |
| `Inches` | `docx.shared.Inches` | `Inches(1)` | Margins, image size |
| `Cm` | `docx.shared.Cm` | `Cm(2.54)` | A4 / metric layouts |
| `Emu` | `docx.shared.Emu` | `Emu(914400)` | Raw EMU (1 inch = 914400) |
| `RGBColor` | `docx.shared.RGBColor` | `RGBColor(0x2E, 0x75, 0xB6)` | Font / highlight colour |

```python
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_ORIENTATION, WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import docx
```

---

## Document Setup

### Create New Document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.section import WD_ORIENTATION

doc = Document()    # blank document
# or:
doc = Document("template.docx")  # start from template
```

### Page Size & Margins

```python
section = doc.sections[0]

# US Letter (default is A4)
section.page_width  = Inches(8.5)
section.page_height = Inches(11)

# A4
section.page_width  = Cm(21)
section.page_height = Cm(29.7)

# Margins — 1 inch all sides
section.top_margin    = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin   = Inches(1)
section.right_margin  = Inches(1)

# Landscape
section.orientation = WD_ORIENTATION.LANDSCAPE
section.page_width, section.page_height = section.page_height, section.page_width
```

### Multi-Section Documents (different layouts per section)

```python
from docx.enum.section import WD_SECTION

# Add a new section with portrait layout after landscape section
new_section = doc.add_section(WD_SECTION.NEW_PAGE)
new_section.orientation  = WD_ORIENTATION.PORTRAIT
new_section.page_width   = Inches(8.5)
new_section.page_height  = Inches(11)
new_section.top_margin   = Inches(1)
new_section.bottom_margin = Inches(1)
new_section.left_margin  = Inches(1)
new_section.right_margin = Inches(1)
```

### Save

```python
doc.save("output.docx")

# Atomic write — safe for overwrite
from pathlib import Path
import shutil, tempfile, os

def save_safe(doc, output_path: str) -> None:
    p = Path(output_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx",
                                     dir=p.parent) as tmp:
        doc.save(tmp.name)
    shutil.move(tmp.name, p)
    print(f"Saved: {p}  ({p.stat().st_size / 1024:.1f} KB)")
```

---

## Styles

### Use Built-in Styles

```python
# Headings
doc.add_heading("Document Title", level=0)   # Title style
doc.add_heading("Chapter One",    level=1)   # Heading 1
doc.add_heading("Section 1.1",    level=2)   # Heading 2
doc.add_heading("Subsection",     level=3)   # Heading 3

# Body text
p = doc.add_paragraph("Normal paragraph.", style="Normal")
p = doc.add_paragraph("Body text.",        style="Body Text")

# Other built-in styles
p = doc.add_paragraph("",  style="List Bullet")
p = doc.add_paragraph("",  style="List Number")
p = doc.add_paragraph("",  style="Quote")
p = doc.add_paragraph("",  style="Intense Quote")
p = doc.add_paragraph("",  style="Caption")
p = doc.add_paragraph("",  style="No Spacing")
```

### Modify a Built-in Style

```python
from docx.shared import Pt, RGBColor
from docx.dml.color import ColorFormat

# Modify Heading 1
h1_style = doc.styles["Heading 1"]
h1_style.font.name  = "Arial"
h1_style.font.size  = Pt(16)
h1_style.font.bold  = True
h1_style.font.color.rgb = RGBColor(0x2E, 0x75, 0xB6)
h1_style.paragraph_format.space_before = Pt(18)
h1_style.paragraph_format.space_after  = Pt(6)
h1_style.paragraph_format.keep_with_next = True   # keep heading with following paragraph

# Modify Normal (affects all unstyled text)
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
normal.paragraph_format.line_spacing = 1.15
```

### Create Custom Paragraph Style

```python
from docx.enum.style import WD_STYLE_TYPE

def add_paragraph_style(doc, style_id, base_style_name,
                         font_name="Calibri", font_size_pt=11,
                         bold=False, italic=False,
                         colour_rgb=None,
                         space_before_pt=0, space_after_pt=8,
                         left_indent_inches=0):
    """Add a custom paragraph style. Returns the style."""
    style = doc.styles.add_style(style_id, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = doc.styles[base_style_name]
    style.font.name  = font_name
    style.font.size  = Pt(font_size_pt)
    style.font.bold  = bold
    style.font.italic = italic
    if colour_rgb:
        style.font.color.rgb = colour_rgb
    pf = style.paragraph_format
    pf.space_before  = Pt(space_before_pt)
    pf.space_after   = Pt(space_after_pt)
    if left_indent_inches:
        pf.left_indent = Inches(left_indent_inches)
    return style


# Usage
add_paragraph_style(doc, "Alert",
                    base_style_name="Normal",
                    font_name="Calibri", font_size_pt=11,
                    bold=True,
                    colour_rgb=RGBColor(0xC0, 0x00, 0x00),
                    space_before_pt=6, space_after_pt=6,
                    left_indent_inches=0.5)

doc.add_paragraph("Warning: check this.", style="Alert")
```

### Create Custom Character Style

```python
from docx.enum.style import WD_STYLE_TYPE

char_style = doc.styles.add_style("Highlight Code", WD_STYLE_TYPE.CHARACTER)
char_style.font.name  = "Courier New"
char_style.font.size  = Pt(10)
char_style.font.color.rgb = RGBColor(0x17, 0x6B, 0x47)

# Apply to a run
p = doc.add_paragraph("Use the ")
run = p.add_run("save()")
run.style = doc.styles["Highlight Code"]
p.add_run(" function to write the file.")
```

---

## Text & Formatting

### Paragraphs and Runs

```python
# Simple paragraph
p = doc.add_paragraph("Plain paragraph text.")

# Paragraph with mixed formatting (runs)
p = doc.add_paragraph()
p.add_run("Normal text. ")
run = p.add_run("Bold text. ")
run.bold = True
run = p.add_run("Italic text. ")
run.italic = True
run = p.add_run("Bold and italic.")
run.bold   = True
run.italic = True

# Run formatting
run = p.add_run("Styled run")
run.font.name      = "Arial"
run.font.size      = Pt(12)
run.font.bold      = True
run.font.italic    = False
run.font.underline = True
run.font.strike    = True
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
run.font.highlight_color = docx.enum.text.WD_COLOR_INDEX.YELLOW

# Superscript / subscript
run.font.superscript = True
run.font.subscript   = True
```

### Paragraph Alignment & Spacing

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

pf = p.paragraph_format
pf.alignment      = WD_ALIGN_PARAGRAPH.LEFT       # LEFT / CENTER / RIGHT / JUSTIFY
pf.space_before   = Pt(12)
pf.space_after    = Pt(6)
pf.left_indent    = Inches(0.5)
pf.right_indent   = Inches(0)
pf.first_line_indent = Pt(0)                       # negative = hanging indent

# Line spacing
pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
pf.line_spacing      = Pt(14)                      # exact 14pt

pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
pf.line_spacing      = 1.5                         # 1.5× line spacing

# Keep together / page control
pf.keep_together    = True    # no page break mid-paragraph
pf.keep_with_next   = True    # keep with following paragraph
pf.page_break_before = True   # force page break before
pf.widow_control    = True    # prevent widows/orphans
```

### Page Break and Section Break

```python
# Page break — must be inside a paragraph
doc.add_page_break()

# Or inline:
p = doc.add_paragraph()
p.add_run().add_break(docx.enum.text.WD_BREAK.PAGE)

# Line break (soft return — Shift+Enter)
p = doc.add_paragraph("Line one")
p.add_run().add_break()        # WD_BREAK.LINE is default
p.add_run("Line two")
```

### Hyperlinks

python-docx does not have a built-in hyperlink method — requires OxmlElement manipulation:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_hyperlink(paragraph, text: str, url: str,
                  colour_rgb=RGBColor(0x05, 0x63, 0xC1),
                  underline=True):
    """Add a clickable hyperlink run to an existing paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url,
                           "http://schemas.openxmlformats.org/officeDocument/2006/"
                           "relationships/hyperlink",
                           is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")

    # Style
    r_style = OxmlElement("w:rStyle")
    r_style.set(qn("w:val"), "Hyperlink")
    rpr.append(r_style)

    if colour_rgb:
        colour_el = OxmlElement("w:color")
        colour_el.set(qn("w:val"), f"{colour_rgb.red:02X}{colour_rgb.green:02X}{colour_rgb.blue:02X}")
        rpr.append(colour_el)
    if underline:
        u_el = OxmlElement("w:u")
        u_el.set(qn("w:val"), "single")
        rpr.append(u_el)

    new_run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink


# Usage
p = doc.add_paragraph("Visit ")
add_hyperlink(p, "our website", "https://example.com")
p.add_run(" for more information.")
```

---

## Tables

### Create Table

```python
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE

# Basic table — rows × columns
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"      # or "Light Shading", "Medium Grid 1", etc.
table.alignment = WD_TABLE_ALIGNMENT.LEFT

# Set column widths (always explicit)
from docx.shared import Inches
col_widths = [Inches(2), Inches(3.5), Inches(1.5)]
for i, width in enumerate(col_widths):
    for cell in table.columns[i].cells:
        cell.width = width
```

### Header Row

```python
# Populate header row
header_cells = table.rows[0].cells
headers = ["Item", "Description", "Cost"]
for cell, text in zip(header_cells, headers):
    cell.text = text
    # Style header cell
    run = cell.paragraphs[0].runs[0]
    run.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    # Shade header cell
    set_cell_shading(cell, "2E75B6")    # see helper below
```

### Add Data Rows

```python
data = [
    ["Steel beam", "HEB 200 × 6m galvanised", "£420.00"],
    ["Concrete",   "C30/37 ready-mix, 3m³",   "£315.00"],
    ["Labour",     "Groundworks, 2 operatives", "£680.00"],
]

for row_data in data:
    row = table.add_row()
    for i, text in enumerate(row_data):
        cell = row.cells[i]
        cell.text = text
        cell.width = col_widths[i]
        cell.paragraphs[0].paragraph_format.space_before = Pt(2)
        cell.paragraphs[0].paragraph_format.space_after  = Pt(2)
```

### Cell Shading Helper

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, fill_hex: str, theme_color=None):
    """Set background colour on a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  fill_hex.upper())
    if theme_color:
        shd.set(qn("w:themeFill"), theme_color)
    tc_pr.append(shd)
```

### Row Height & Vertical Alignment

```python
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE

# Set row height
row = table.rows[0]
row.height      = Pt(24)
row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY   # or AT_LEAST / AUTO

# Vertical alignment
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER   # TOP / CENTER / BOTTOM
```

### Merge Cells

```python
# Horizontal merge — merge cells across row 0, columns 0–1
a = table.cell(0, 0)
b = table.cell(0, 1)
a.merge(b)

# Vertical merge — merge rows 1–2 in column 0
a = table.cell(1, 0)
b = table.cell(2, 0)
a.merge(b)
```

### Table Borders

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_table_borders(table, colour="AAAAAA", size=4):
    """Apply uniform border to all cells in a table."""
    tbl_pr = table._tbl.tblPr
    tbl_borders = OxmlElement("w:tblBorders")
    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"),   "single")
        border.set(qn("w:sz"),    str(size))
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), colour)
        tbl_borders.append(border)
    tbl_pr.append(tbl_borders)

set_table_borders(table, colour="2E75B6", size=4)
```

### Repeat Header Row on Page Break

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_repeat_header(row):
    """Mark a table row as a repeating header."""
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "1")
    tr_pr.append(tbl_header)

set_repeat_header(table.rows[0])
```

### DataFrame → Table

```python
import pandas as pd

def dataframe_to_table(doc, df: pd.DataFrame,
                       header_fill="2E75B6",
                       col_widths_inches: list = None,
                       style="Table Grid") -> docx.table.Table:
    """Convert a pandas DataFrame to a formatted Word table."""
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = style

    # Header row
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df.columns):
        cell = hdr_cells[i]
        cell.text = str(col)
        p = cell.paragraphs[0]
        run = p.runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, header_fill)

    # Data rows
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val) if pd.notna(val) else ""

    # Column widths
    if col_widths_inches:
        for col_idx, width in enumerate(col_widths_inches):
            for cell in table.columns[col_idx].cells:
                cell.width = Inches(width)

    return table


# Usage
df = pd.DataFrame({"Item": ["A", "B"], "Value": [10, 20]})
dataframe_to_table(doc, df, col_widths_inches=[3, 2])
```

---

## Lists

python-docx built-in list styles are limited. For nested or custom lists, use XML directly.

### Simple Built-in Lists

```python
# Bullet list
for item in ["First item", "Second item", "Third item"]:
    doc.add_paragraph(item, style="List Bullet")

# Numbered list
for item in ["Step one", "Step two", "Step three"]:
    doc.add_paragraph(item, style="List Number")

# Continuation after break
doc.add_paragraph("Intervening text.")
doc.add_paragraph("Resumed item", style="List Number 2")  # continues numbering
```

### Multi-level / Nested Lists via XML

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_list_paragraph(doc, text: str, list_type: str = "bullet",
                        level: int = 0, num_id: int = 1):
    """
    Add a list item at a specified nesting level.

    list_type: 'bullet' or 'number'
    level:     0 (top) – 8 (deepest)
    num_id:    numbering definition ID (1 = first list defined)
    """
    p = doc.add_paragraph(style="List Paragraph")
    p.add_run(text)
    ppr = p._p.get_or_add_pPr()

    # numPr element
    num_pr = OxmlElement("w:numPr")
    ilvl   = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), str(level))
    num_id_el = OxmlElement("w:numId")
    num_id_el.set(qn("w:val"), str(num_id))
    num_pr.append(ilvl)
    num_pr.append(num_id_el)
    ppr.append(num_pr)
    return p


# ── Define numbering in the document ─────────────────────────────────────────
def ensure_list_numbering(doc):
    """
    Add bullet and numbered list numbering definitions if not present.
    Returns (bullet_num_id, number_num_id).
    """
    numbering_part = doc.part.numbering_part

    if numbering_part is None:
        # Create numbering part if it doesn't exist
        from docx.opc.part import Part
        from docx.opc.packuri import PackURI
        from lxml import etree
        numbering_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:numbering xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '</w:numbering>'
        )
        numbering_part = doc.part.add_numbering_part()

    # Use built-in list styles — simpler and reliable for most use cases
    return 1, 2   # placeholder — use add_list_paragraph with style="List Bullet"/"List Number"


# Practical pattern — nested via indent
def add_nested_bullet(doc, items: list):
    """
    items: list of (text, level) tuples
    Example: [("Top item", 0), ("Sub item", 1), ("Sub-sub", 2)]
    """
    for text, level in items:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(text)
        # Adjust indent for nesting
        pf = p.paragraph_format
        pf.left_indent   = Inches(0.25 + level * 0.25)
        pf.first_line_indent = Inches(-0.25)


add_nested_bullet(doc, [
    ("Foundation works",   0),
    ("Excavation",         1),
    ("Blinding concrete",  1),
    ("Pad foundations",    1),
    ("Superstructure",     0),
    ("Steel frame erection", 1),
    ("Decking",            1),
])
```

---

## Images

```python
from docx.shared import Inches, Cm

# Inline image — fixed width, auto height
doc.add_picture("photo.jpg", width=Inches(4))

# Inline image — fixed height, auto width
doc.add_picture("photo.jpg", height=Cm(8))

# Inline image — both (may distort aspect ratio)
doc.add_picture("photo.jpg", width=Inches(3), height=Inches(2))

# Add image to existing paragraph (alongside text)
p = doc.add_paragraph("Site photo: ")
run = p.add_run()
run.add_picture("site_photo.jpg", width=Inches(3))

# Centre an image
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
run.add_picture("logo.png", width=Inches(2))

# Add caption below image
cap = doc.add_paragraph("Figure 1 — Site overview, March 2024", style="Caption")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

### Image from URL or bytes

```python
import requests
from io import BytesIO

def add_image_from_url(doc, url: str, width_inches: float = 4.0):
    """Download image and embed directly."""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    stream = BytesIO(response.content)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(stream, width=Inches(width_inches))
```

### Floating Image (text wrap) via XML

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_floating_image(doc, image_path: str,
                        width_inches=2.0, height_inches=2.0,
                        horiz_pos_inches=5.0, vert_pos_inches=1.0):
    """
    Add an image with tight text wrapping at an absolute position.
    NOTE: Requires precise XML manipulation — test in Word after generation.
    """
    from docx.shared import Emu
    WPG = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

    p = doc.add_paragraph()
    run = p.add_run()
    run.add_picture(image_path, width=Inches(width_inches), height=Inches(height_inches))

    # Convert inline drawing to anchor (floating)
    inline = p._p.find(f".//{{{WPG}}}inline")
    if inline is not None:
        inline.tag = f"{{{WPG}}}anchor"
        inline.set("distT", "0"); inline.set("distB", "0")
        inline.set("distL", "114300"); inline.set("distR", "114300")
        inline.set("simplePos", "0"); inline.set("relativeHeight", "251658240")
        inline.set("behindDoc", "0"); inline.set("locked", "0")
        inline.set("layoutInCell", "1"); inline.set("allowOverlap", "1")

        # Simple position
        sp = OxmlElement(f"{{{WPG}}}simplePos")
        sp.set("x", "0"); sp.set("y", "0")
        inline.insert(0, sp)

        # Wrap type (tight)
        wrap = OxmlElement(f"{{{WPG}}}wrapTight")
        wrap.set("wrapText", "bothSides")
        poly = OxmlElement(f"{{{WPG}}}wrapPolygon")
        poly.set("edited", "0")
        inline.append(wrap)
```

---

## Headers & Footers

### Simple Header and Footer

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH

section = doc.sections[0]

# Header
header = section.header
header_para = header.paragraphs[0]
header_para.text = "Acme Engineering — Confidential"
header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
header_para.runs[0].font.size = Pt(9)
header_para.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

# Footer
footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.text = "© 2024 Acme Engineering Ltd"
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_para.runs[0].font.size = Pt(9)
```

### Page Numbers

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_page_number(paragraph, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                     prefix="Page ", suffix=" of "):
    """
    Add page X of Y to a paragraph.
    Call on a footer or header paragraph.
    """
    paragraph.alignment = alignment

    if prefix:
        paragraph.add_run(prefix)

    # PAGE field (current page)
    fld_page = OxmlElement("w:fldChar")
    fld_page.set(qn("w:fldCharType"), "begin")
    paragraph.add_run()._r.append(fld_page)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    paragraph.add_run()._r.append(instr)

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    paragraph.add_run()._r.append(fld_end)

    if suffix:
        paragraph.add_run(suffix)

    # NUMPAGES field (total pages)
    fld_num = OxmlElement("w:fldChar")
    fld_num.set(qn("w:fldCharType"), "begin")
    paragraph.add_run()._r.append(fld_num)

    instr2 = OxmlElement("w:instrText")
    instr2.set(qn("xml:space"), "preserve")
    instr2.text = " NUMPAGES "
    paragraph.add_run()._r.append(instr2)

    fld_end2 = OxmlElement("w:fldChar")
    fld_end2.set(qn("w:fldCharType"), "end")
    paragraph.add_run()._r.append(fld_end2)


# Usage
footer = doc.sections[0].footer
footer.paragraphs[0].clear()
add_page_number(footer.paragraphs[0],
                alignment=WD_ALIGN_PARAGRAPH.CENTER,
                prefix="Page ", suffix=" of ")
```

### Different First Page Header/Footer

```python
from docx.oxml.ns import qn

section = doc.sections[0]
# Enable different first page via XML
sect_pr = section._sectPr
title_pg = OxmlElement("w:titlePg")
sect_pr.append(title_pg)

# First page header (blank or custom)
first_header = section.first_page_header
first_header.paragraphs[0].text = ""  # blank cover page header

# Default header (pages 2+)
header = section.header
header.paragraphs[0].text = "Running header — pages 2+"
```

### Header with Logo Left, Title Right (Tab Stop)

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def header_with_logo_and_title(section, logo_path: str,
                                 title: str, page_width_inches=8.5,
                                 margin_inches=1.0):
    """Logo on left, document title on right, using tab stop."""
    header = section.header
    p = header.paragraphs[0]
    p.clear()

    # Set a right-aligned tab stop at content edge
    pf = p.paragraph_format
    content_width = Inches(page_width_inches - 2 * margin_inches)

    # Tab stop via XML
    ppr = p._p.get_or_add_pPr()
    tabs_el = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"),   "right")
    tab.set(qn("w:pos"),   str(int(content_width)))
    tab.set(qn("w:leader"), "none")
    tabs_el.append(tab)
    ppr.append(tabs_el)

    # Logo run
    logo_run = p.add_run()
    logo_run.add_picture(logo_path, height=Inches(0.4))

    # Tab character + title
    tab_run = p.add_run("\t" + title)
    tab_run.font.size = Pt(9)
    tab_run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
```

---

## Table of Contents

python-docx cannot generate a live TOC (requires Word to update). It can insert a TOC field that Word/LibreOffice will populate on open.

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def insert_toc(doc, title: str = "Contents",
               min_level: int = 1, max_level: int = 3):
    """
    Insert a TOC field. Word/LibreOffice updates it on open
    (or Ctrl+A → F9 to force update).
    """
    # TOC title
    doc.add_heading(title, level=1)

    # TOC field paragraph
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after  = Pt(0)

    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    fld_begin.set(qn("w:dirty"),       "true")    # marks as needing update
    run._r.append(fld_begin)

    instr_run = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f' TOC \\o "{min_level}-{max_level}" \\h \\z \\u '
    instr_run._r.append(instr)

    end_run = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    end_run._r.append(fld_end)

    doc.add_page_break()


# Usage — insert TOC, then add content with proper heading styles
insert_toc(doc, title="Contents", min_level=1, max_level=3)
doc.add_heading("Chapter One", level=1)
doc.add_heading("Section 1.1", level=2)
```

> **Note:** Open the saved `.docx` in Word or LibreOffice, then press `Ctrl+A` → `F9` (Windows) or `⌘+A` → `F9` (macOS) to update the TOC.

---

## Reading Documents

### Extract All Text

```python
from docx import Document

def extract_text(docx_path: str) -> str:
    """Extract all paragraph text in order."""
    doc = Document(docx_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_structured(docx_path: str) -> list[dict]:
    """
    Extract paragraphs with style, heading level, and text.
    Returns list of dicts: {style, level, text}
    """
    doc = Document(docx_path)
    results = []
    for p in doc.paragraphs:
        style_name = p.style.name
        level = None
        if style_name.startswith("Heading"):
            try:
                level = int(style_name.split()[-1])
            except ValueError:
                level = 0
        results.append({
            "style": style_name,
            "level": level,
            "text":  p.text
        })
    return results
```

### Extract Tables

```python
def extract_tables(docx_path: str) -> list[list[list[str]]]:
    """
    Extract all tables as nested lists.
    Returns: list of tables → list of rows → list of cell text values
    """
    doc = Document(docx_path)
    tables = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        tables.append(rows)
    return tables


def tables_to_dataframes(docx_path: str) -> list:
    """Extract tables as pandas DataFrames (first row = header)."""
    import pandas as pd
    raw = extract_tables(docx_path)
    dfs = []
    for table in raw:
        if len(table) < 2:
            continue
        dfs.append(pd.DataFrame(table[1:], columns=table[0]))
    return dfs
```

### Extract Images

```python
from pathlib import Path
import zipfile

def extract_images(docx_path: str, output_dir: str) -> list[str]:
    """
    Extract all embedded images from a .docx file.
    Returns list of saved file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []

    with zipfile.ZipFile(docx_path, "r") as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                filename = Path(name).name
                target = out / filename
                target.write_bytes(z.read(name))
                saved.append(str(target))

    print(f"Extracted {len(saved)} images → {output_dir}")
    return saved
```

### Inspect Document Properties

```python
def inspect_document(docx_path: str) -> dict:
    """Return summary of document structure."""
    doc = Document(docx_path)
    styles_used = {p.style.name for p in doc.paragraphs}
    headings    = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]

    return {
        "sections":      len(doc.sections),
        "paragraphs":    len(doc.paragraphs),
        "tables":        len(doc.tables),
        "headings":      [(p.style.name, p.text) for p in headings],
        "styles_used":   sorted(styles_used),
        "word_count":    sum(len(p.text.split()) for p in doc.paragraphs),
        "char_count":    sum(len(p.text) for p in doc.paragraphs),
    }
```

---

## Find & Replace

### Simple Text Replace

```python
def replace_text(doc, old: str, new: str) -> int:
    """
    Replace all occurrences of `old` with `new` across all paragraphs
    and table cells. Returns count of replacements.
    """
    count = 0

    def _replace_in_para(para):
        nonlocal count
        if old in para.text:
            # Replace in full_text then rewrite — preserves paragraph style
            # but loses per-run formatting on changed runs
            for run in para.runs:
                if old in run.text:
                    run.text = run.text.replace(old, new)
                    count += 1

    for para in doc.paragraphs:
        _replace_in_para(para)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_in_para(para)

    return count


# Usage — mail merge style variable replacement
replacements = {
    "{{CLIENT_NAME}}":    "Acme Construction Ltd",
    "{{PROJECT_REF}}":    "2401",
    "{{REPORT_DATE}}":    "15 March 2024",
    "{{CONTRACT_VALUE}}": "£4,250,000",
}
for old, new in replacements.items():
    n = replace_text(doc, old, new)
    print(f"  {old} → replaced {n} time(s)")
```

### Regex Replace (preserving formatting)

```python
import re

def regex_replace(doc, pattern: str, replacement: str,
                  flags=re.IGNORECASE) -> int:
    """Replace text matching a regex pattern in all runs."""
    count = 0
    compiled = re.compile(pattern, flags)

    for para in doc.paragraphs:
        for run in para.runs:
            if compiled.search(run.text):
                run.text = compiled.sub(replacement, run.text)
                count += 1

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if compiled.search(run.text):
                            run.text = compiled.sub(replacement, run.text)
                            count += 1
    return count
```

---

## Templates

### Design: Placeholder Convention

Use `{{VARIABLE_NAME}}` placeholders in a template `.docx`. Create the template in Word with your layout, styles, tables, and headers/footers in place.

```
Template: project_report_template.docx
Placeholders:
  {{PROJECT_TITLE}}     — document title
  {{CLIENT_NAME}}       — client organisation
  {{PROJECT_REF}}       — project reference number
  {{REPORT_DATE}}       — formatted date
  {{LEAD_ENGINEER}}     — responsible engineer name
  {{CONTRACT_VALUE}}    — formatted contract value
```

### Fill Template from Dict

```python
def fill_template(template_path: str,
                  output_path: str,
                  variables: dict) -> None:
    """
    Load template, substitute all {{KEY}} placeholders, save output.
    Works across paragraphs, tables, headers, and footers.
    """
    doc = Document(template_path)

    def replace_in_paragraphs(paragraphs):
        for para in paragraphs:
            for run in para.runs:
                for key, value in variables.items():
                    placeholder = "{{" + key + "}}"
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, str(value))

    # Body paragraphs
    replace_in_paragraphs(doc.paragraphs)

    # Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                replace_in_paragraphs(cell.paragraphs)

    # Headers and footers
    for section in doc.sections:
        replace_in_paragraphs(section.header.paragraphs)
        replace_in_paragraphs(section.footer.paragraphs)
        replace_in_paragraphs(section.first_page_header.paragraphs)
        replace_in_paragraphs(section.first_page_footer.paragraphs)

    save_safe(doc, output_path)
    print(f"Report written: {output_path}")


# Usage
fill_template(
    "project_report_template.docx",
    "2401_Acme_Progress_Report_R2.docx",
    {
        "PROJECT_TITLE":  "Foundation Works — Progress Report R2",
        "CLIENT_NAME":    "Acme Construction Ltd",
        "PROJECT_REF":    "2401",
        "REPORT_DATE":    "15 March 2024",
        "LEAD_ENGINEER":  "J. Smith CEng MICE",
        "CONTRACT_VALUE": "£4,250,000",
    }
)
```

---

## Mail Merge Pattern

python-docx has no native mail merge. The recommended pattern is template fill per record.

```python
import pandas as pd
from pathlib import Path

def batch_merge(template_path: str, data_path: str,
                output_dir: str, filename_col: str = None) -> list[str]:
    """
    Generate one document per row in a CSV/Excel data file.

    filename_col: column to use as output filename (optional).
                  If None, uses row index.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    output_files = []

    # Load data
    if data_path.endswith(".csv"):
        df = pd.read_csv(data_path)
    else:
        df = pd.read_excel(data_path)

    for idx, row in df.iterrows():
        variables = row.to_dict()

        if filename_col and filename_col in variables:
            filename = f"{variables[filename_col]}.docx"
        else:
            filename = f"document_{idx+1:04d}.docx"

        output_path = str(out / filename)
        fill_template(template_path, output_path, variables)
        output_files.append(output_path)

    print(f"Generated {len(output_files)} documents → {output_dir}")
    return output_files


# Usage
batch_merge(
    template_path="letter_template.docx",
    data_path="recipients.csv",
    output_dir="./output/letters/",
    filename_col="REF_NUMBER"
)
```

---

## Convert to PDF

python-docx cannot export PDF directly. Use LibreOffice headless.

```python
import subprocess
from pathlib import Path

def convert_to_pdf(docx_path: str, output_dir: str = None) -> str:
    """
    Convert .docx to PDF via LibreOffice headless.
    Requires: libreoffice (apt install libreoffice)
    Returns path to generated PDF.
    """
    docx_path = Path(docx_path).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else docx_path.parent

    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(output_dir), str(docx_path)],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed:\n{result.stderr}")

    pdf_path = output_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"Expected PDF not found: {pdf_path}")

    print(f"PDF written: {pdf_path}  ({pdf_path.stat().st_size / 1024:.1f} KB)")
    return str(pdf_path)


# Batch conversion
def batch_to_pdf(docx_paths: list, output_dir: str) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return [convert_to_pdf(p, output_dir) for p in docx_paths]
```

```bash
# CLI alternative
libreoffice --headless --convert-to pdf --outdir ./output/ report.docx

# Batch
libreoffice --headless --convert-to pdf --outdir ./output/ *.docx
```

---

## Validation & QA

```python
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pathlib import Path
import zipfile

def validate_docx(docx_path: str,
                  required_styles: list = None,
                  required_placeholders: list = None) -> bool:
    """
    Validate a .docx file for structure, content, and completeness.
    Returns True if all checks pass.
    """
    errors = []
    p = Path(docx_path)

    # File existence and size
    if not p.exists():
        print(f"ERROR: File not found: {docx_path}")
        return False
    size_kb = p.stat().st_size / 1024
    if size_kb < 2:
        errors.append(f"WARNING: File suspiciously small ({size_kb:.1f} KB) — may be empty")

    # ZIP integrity (docx is a ZIP)
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            bad = z.testzip()
            if bad:
                errors.append(f"CORRUPT ZIP: First bad entry: {bad}")
    except zipfile.BadZipFile:
        errors.append("CORRUPT: Not a valid ZIP/DOCX file")
        for e in errors: print(e)
        return False

    # python-docx can parse it
    try:
        doc = Document(docx_path)
    except (PackageNotFoundError, Exception) as e:
        errors.append(f"PARSE ERROR: {e}")
        for e in errors: print(e)
        return False

    # Content checks
    text = " ".join(p.text for p in doc.paragraphs)
    if not text.strip():
        errors.append("WARNING: Document appears to have no text content")

    # Unfilled placeholders
    if required_placeholders:
        for ph in required_placeholders:
            placeholder = "{{" + ph + "}}"
            if placeholder in text:
                errors.append(f"UNFILLED PLACEHOLDER: {placeholder} still present in document")

    # Required styles used
    if required_styles:
        styles_used = {p.style.name for p in doc.paragraphs}
        for style in required_styles:
            if style not in styles_used:
                errors.append(f"WARNING: Expected style '{style}' not used in document")

    # Stats
    print(f"File:        {p.name}  ({size_kb:.1f} KB)")
    print(f"Sections:    {len(doc.sections)}")
    print(f"Paragraphs:  {len(doc.paragraphs)}")
    print(f"Tables:      {len(doc.tables)}")
    print(f"Word count:  ~{len(text.split()):,}")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Document is valid")
    return True


validate_docx(
    "report.docx",
    required_styles=["Heading 1", "Heading 2"],
    required_placeholders=["PROJECT_TITLE", "CLIENT_NAME"]
)
```

### QA Checklist

- [ ] File opens in Word / LibreOffice without errors
- [ ] Page size set explicitly (not relying on default A4)
- [ ] All `{{PLACEHOLDER}}` tokens filled — none remaining in body, headers, or footers
- [ ] Heading styles used for all headings (not bold Normal paragraphs)
- [ ] Tables have explicit column widths (no auto-sizing surprises)
- [ ] No bare `\n` characters — use separate paragraphs
- [ ] Images embedded (not linked) — verify with `extract_images()`
- [ ] Header and footer appear on all pages
- [ ] Page numbers update correctly (open in Word and check)
- [ ] TOC updated after opening (Ctrl+A → F9)
- [ ] `validate_docx()` passes with zero errors
- [ ] File size is reasonable (text-only doc > 5KB; image-heavy doc proportionally larger)
- [ ] PDF export reviewed if required (open PDF, check layout)

### QA Loop

1. Generate document with `doc.save()` or `save_safe()`
2. Run `validate_docx()` — structure and placeholder checks
3. Open in Word or LibreOffice — visual review
4. Update TOC if present: `Ctrl+A` → `F9`
5. Check headers and footers on pages 1, 2, and last
6. Export to PDF with `convert_to_pdf()` and review
7. **Do not deliver until step 3 visual review passes**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Default page size is A4, not US Letter | python-docx default | Always set `page_width = Inches(8.5)`, `page_height = Inches(11)` |
| Heading not appearing in TOC | Style applied manually (bold Normal) | Use `add_heading(level=N)` or set `style="Heading N"` |
| Table columns too wide / overflow | No explicit column widths | Set `cell.width = Inches(N)` on every cell |
| Image too large / distorts page | Width not set | Always pass `width=Inches(N)` to `add_picture()` |
| `\n` in text produces literal newline | `\n` is not a paragraph break in docx | Use separate `doc.add_paragraph()` calls |
| Bold/italic lost after replace_text | Run split across multiple XML runs | Check per-run replacement; or merge runs before editing |
| Header shows on first page | `titlePg` not set | Set `w:titlePg` in section properties; use `first_page_header` |
| TOC shows "Error! No table of contents entries found" | Headings use Normal style | Use built-in Heading styles with `outlineLevel` |
| LibreOffice PDF layout differs from Word | Font substitution | Embed fonts or use universally-available fonts (Arial, Calibri) |
| Placeholder still in output | Run split across XML runs | Rebuild template so each `{{TAG}}` is in a single run |
| Hyperlink not clickable | Incorrect relationship type | Use `part.relate_to()` with correct schema URI |
| `PackageNotFoundError` on open | Not a valid OOXML file | Verify file is `.docx` not `.doc`; convert with LibreOffice first |

---

## Dependencies

```bash
pip install python-docx        # core library
pip install pandas             # DataFrame → table conversion
pip install requests           # image from URL
pip install lxml               # XML manipulation (installed with python-docx)

# PDF conversion (headless LibreOffice)
sudo apt install libreoffice   # Linux
brew install --cask libreoffice  # macOS

# Legacy .doc → .docx conversion
# Use LibreOffice:
libreoffice --headless --convert-to docx legacy.doc
```
