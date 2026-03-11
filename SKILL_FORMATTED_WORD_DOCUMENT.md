---
name: formatted-word-document
description: "Use this skill when creating or editing Microsoft Word .docx files. Covers professional documents, reports, letters, memos, templates, tracked changes, tables of contents, headers/footers, and page numbering. Trigger on any .docx output request."
---

# Formatted Word Document SKILL

## Quick Reference

| Task | Approach |
|------|----------|
| Create from scratch | `python-docx` |
| Apply styles | `doc.styles` + named style application |
| Table of contents | XML injection (python-docx doesn't natively support TOC) |
| Headers / footers | `section.header` / `section.footer` |
| Page numbers | Footer with `PAGE` field XML |
| Images | `doc.add_picture()` |
| Tables | `doc.add_table()` |

---

## Basic Document Creation

```python
# pip install python-docx --break-system-packages
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('Document Title', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Section heading
doc.add_heading('Section 1', level=1)

# Body paragraph
p = doc.add_paragraph('Body text content here.')
p.style = doc.styles['Normal']

# Save
doc.save('output.docx')
```

---

## Styling Text

```python
from docx.shared import Pt, RGBColor
from docx.util import Pt

para = doc.add_paragraph()
run = para.add_run('Bold important text')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1E, 0x27, 0x61)  # Navy

# Italic
run2 = para.add_run(' with italic continuation')
run2.italic = True
```

---

## Tables

```python
table = doc.add_table(rows=1, cols=3)
table.style = 'Table Grid'

# Header row
hdr = table.rows[0].cells
hdr[0].text = 'Column A'
hdr[1].text = 'Column B'
hdr[2].text = 'Column C'

# Data rows
data = [('val1','val2','val3'), ('val4','val5','val6')]
for row_data in data:
    row = table.add_row().cells
    for i, val in enumerate(row_data):
        row[i].text = val

# Column widths
from docx.shared import Inches
for row in table.rows:
    row.cells[0].width = Inches(2)
    row.cells[1].width = Inches(2)
    row.cells[2].width = Inches(2)
```

---

## Headers and Footers

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

section = doc.sections[0]

# Header
header = section.header
header_para = header.paragraphs[0]
header_para.text = "Company Name — Confidential"
header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

# Footer with page number
footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

run = footer_para.add_run()
fldChar1 = OxmlElement('w:fldChar')
fldChar1.set(qn('w:fldCharType'), 'begin')
instrText = OxmlElement('w:instrText')
instrText.text = 'PAGE'
fldChar2 = OxmlElement('w:fldChar')
fldChar2.set(qn('w:fldCharType'), 'end')
run._r.append(fldChar1)
run._r.append(instrText)
run._r.append(fldChar2)
```

---

## Page Setup

```python
from docx.shared import Inches, Mm
from docx.enum.section import WD_ORIENT

section = doc.sections[0]
section.page_width = Mm(210)   # A4
section.page_height = Mm(297)
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
```

---

## Inserting Images

```python
doc.add_picture('image.png', width=Inches(5))
# Always specify width OR height (not both) to preserve aspect ratio
```

---

## CLI Verification

```bash
# Extract text to verify content
python -m docx2txt output.docx

# Or using markitdown
python -m markitdown output.docx

# Check file is valid
python -c "from docx import Document; Document('output.docx'); print('Valid')"
```

---

## QA Checklist

- [ ] File opens without repair prompt in Word
- [ ] All headings use correct heading styles (not just bold text)
- [ ] Tables have consistent column widths
- [ ] Images are not stretched or distorted
- [ ] Page numbers appear correctly
- [ ] Headers/footers render on all pages
- [ ] No placeholder text (`XXXX`, `Lorem ipsum`)
- [ ] Margins consistent throughout
- [ ] Font sizes consistent across same-level headings

---

## Common Mistakes to Avoid

- Using bold formatting instead of proper Heading styles (breaks TOC)
- Hardcoding colors without establishing a consistent palette
- Forgetting to set `table.style` (results in invisible borders)
- Setting both width and height on images (distorts aspect ratio)
- Not calling `doc.save()` at the end

---

## Dependencies

```bash
pip install python-docx --break-system-packages
pip install markitdown --break-system-packages   # for QA text extraction
pip install docx2txt --break-system-packages     # alternative extraction
```
