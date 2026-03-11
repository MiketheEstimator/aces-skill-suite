---
name: automated-precision-pdf
description: "Use this skill when generating or manipulating PDF files programmatically. Covers creating PDFs from scratch, converting HTML/Markdown to PDF, merging/splitting, adding watermarks, form filling, and stamping. Trigger on any task involving .pdf output or PDF manipulation."
---

# Automated Precision PDF SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create from scratch | `weasyprint` or `reportlab` |
| Convert HTML → PDF | `weasyprint` |
| Merge / split PDFs | `pypdf` |
| Add watermark / stamp | `pypdf` + overlay PDF |
| Fill PDF forms | `pypdf` or `pdftk` |
| Extract text | `pdfplumber` or `pymupdf` |
| Render to images | `pdftoppm` (Poppler) |

---

## Creating PDF from HTML (Recommended Path)

```python
# pip install weasyprint --break-system-packages
from weasyprint import HTML, CSS

html_content = """
<!DOCTYPE html>
<html>
<head>
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: Arial, sans-serif; font-size: 11pt; }
  h1 { color: #1E2761; }
  table { width: 100%; border-collapse: collapse; }
  td, th { border: 1px solid #ccc; padding: 6px; }
</style>
</head>
<body>
  <h1>Report Title</h1>
  <p>Content here...</p>
</body>
</html>
"""

HTML(string=html_content).write_pdf("output.pdf")
```

---

## Creating PDF Programmatically (ReportLab)

```python
# pip install reportlab --break-system-packages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

c = canvas.Canvas("output.pdf", pagesize=A4)
width, height = A4

c.setFont("Helvetica-Bold", 16)
c.drawString(72, height - 72, "Document Title")

c.setFont("Helvetica", 11)
c.drawString(72, height - 110, "Body text content here.")

c.showPage()
c.save()
```

---

## Merging PDFs

```python
# pip install pypdf --break-system-packages
from pypdf import PdfWriter

writer = PdfWriter()
for filename in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    writer.append(filename)

with open("merged.pdf", "wb") as f:
    writer.write(f)
```

---

## Splitting PDFs

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")

for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as f:
        writer.write(f)
```

---

## Adding Watermark

```python
from pypdf import PdfReader, PdfWriter

base = PdfReader("document.pdf")
watermark = PdfReader("watermark.pdf")
writer = PdfWriter()

for page in base.pages:
    page.merge_page(watermark.pages[0])
    writer.add_page(page)

with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

---

## Extracting Text

```python
# pip install pdfplumber --break-system-packages
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
        
# Extract tables
with pdfplumber.open("input.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            print(table)
```

---

## CLI Tools

```bash
# Render PDF pages to images (150 DPI JPEG)
pdftoppm -jpeg -r 150 output.pdf slide

# Compress PDF
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed.pdf input.pdf

# Get PDF info
pdfinfo output.pdf

# Validate PDF
pdftotext output.pdf /dev/null && echo "Valid" || echo "Corrupt"
```

---

## Page Size Reference

| Size | Width x Height (mm) |
|------|---------------------|
| A4 | 210 × 297 |
| A3 | 297 × 420 |
| Letter | 215.9 × 279.4 |
| Legal | 215.9 × 355.6 |

---

## QA Checklist

- [ ] PDF opens without error
- [ ] Page size correct
- [ ] Margins consistent (min 1.5cm)
- [ ] Fonts embedded (not substituted)
- [ ] Images not pixelated (min 150 DPI for screen, 300 DPI for print)
- [ ] Text extractable (not image-only)
- [ ] Links/bookmarks functional if present
- [ ] File size reasonable (flag if >10MB for a simple doc)
- [ ] No placeholder text remaining

```bash
# Visual QA: render and inspect
pdftoppm -jpeg -r 150 output.pdf preview
# Inspect preview-1.jpg, preview-2.jpg etc.
```

---

## Common Mistakes to Avoid

- Forgetting `@page` margins in WeasyPrint (defaults to 0)
- Using system fonts not available in sandbox (stick to Arial, Helvetica, Times, Courier)
- Not embedding fonts in ReportLab (use `registerFont` for custom fonts)
- Producing image-only PDFs (text must be extractable)
- Overlapping elements due to hardcoded Y positions in ReportLab

---

## Dependencies

```bash
pip install weasyprint --break-system-packages
pip install reportlab --break-system-packages
pip install pypdf --break-system-packages
pip install pdfplumber --break-system-packages
# Poppler (pdftoppm, pdfinfo): usually pre-installed on Ubuntu
# Ghostscript (gs): usually pre-installed
```
