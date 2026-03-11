---
name: rendered-html-document
description: "Use this skill when producing standalone .html files intended as documents, reports, or formatted pages — not interactive apps. Covers print-ready HTML, self-contained assets, semantic structure, and PDF-conversion-ready output. Trigger when the user wants an HTML document to open in a browser or convert to PDF."
---

# Rendered HTML Document SKILL

## Quick Reference

| Task | Approach |
|------|----------|
| Self-contained report | Inline all CSS; base64-encode images |
| Print-ready | `@media print` CSS + `@page` rules |
| HTML → PDF | WeasyPrint or Chrome headless |
| Semantic document | Proper `<article>`, `<section>`, `<header>` tags |
| Tables | Styled `<table>` with `border-collapse` |

---

## Self-Contained Document Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Title</title>
    <style>
        /* ── Reset & Base ── */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #2d2d2d;
            background: #f4f5f7;
        }

        /* ── Page Container ── */
        .page {
            max-width: 210mm;
            margin: 2rem auto;
            padding: 2.5cm;
            background: #ffffff;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }

        /* ── Typography ── */
        h1 { font-size: 26pt; color: #1E2761; margin-bottom: 0.5em; }
        h2 { font-size: 16pt; color: #1E2761; margin: 1.5em 0 0.5em; border-bottom: 2px solid #1E2761; padding-bottom: 0.2em; }
        h3 { font-size: 13pt; color: #333; margin: 1em 0 0.3em; }
        p  { margin-bottom: 0.8em; }

        /* ── Tables ── */
        table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 10pt; }
        thead tr { background: #1E2761; color: white; }
        th { padding: 8px 12px; text-align: left; font-weight: 600; }
        td { padding: 7px 12px; border-bottom: 1px solid #e0e0e0; }
        tbody tr:nth-child(even) { background: #f8f9fc; }

        /* ── Callout Box ── */
        .callout {
            background: #EEF2FF;
            border-left: 4px solid #1E2761;
            padding: 1em 1.2em;
            margin: 1.2em 0;
            border-radius: 0 4px 4px 0;
        }

        /* ── Print ── */
        @media print {
            body { background: white; }
            .page { box-shadow: none; margin: 0; padding: 1.5cm; max-width: 100%; }
            h2 { page-break-after: avoid; }
            table { page-break-inside: avoid; }
            .no-print { display: none; }
        }

        @page {
            size: A4;
            margin: 2cm;
        }
    </style>
</head>
<body>
    <div class="page">
        <header>
            <h1>Document Title</h1>
            <p style="color:#8892A4; font-size:10pt;">Generated: 2024-03-15 · Ref: DOC-001</p>
        </header>

        <main>
            <h2>Section 1</h2>
            <p>Body content here.</p>

            <div class="callout">
                <strong>Key Note:</strong> Important callout content.
            </div>

            <h2>Data Summary</h2>
            <table>
                <thead>
                    <tr><th>Item</th><th>Value</th><th>Status</th></tr>
                </thead>
                <tbody>
                    <tr><td>Alpha</td><td>$125,000</td><td>Active</td></tr>
                    <tr><td>Beta</td><td>$87,500</td><td>On Hold</td></tr>
                </tbody>
            </table>
        </main>
    </div>
</body>
</html>
```

---

## Inlining Images as Base64

```python
import base64

def inline_image(image_path):
    ext = image_path.split('.')[-1].lower()
    mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'svg': 'svg+xml', 'gif': 'gif'}
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/{mime.get(ext, ext)};base64,{b64}"

# Use in HTML:
# <img src="{inline_image('logo.png')}" alt="Logo" width="200">
```

---

## HTML → PDF via WeasyPrint

```python
from weasyprint import HTML

HTML(filename="output.html").write_pdf("output.pdf")

# With custom CSS override
from weasyprint import HTML, CSS
HTML(filename="output.html").write_pdf(
    "output.pdf",
    stylesheets=[CSS(string="@page { size: A4; margin: 1.5cm; }")]
)
```

---

## HTML → PDF via Chrome Headless

```bash
# Chrome headless PDF (highest fidelity)
google-chrome --headless --disable-gpu \
  --print-to-pdf=output.pdf \
  --no-margins \
  file:///path/to/output.html
```

---

## CLI Verification

```bash
# Validate HTML structure
python -c "
from html.parser import HTMLParser
class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
v = Validator()
with open('output.html') as f:
    v.feed(f.read())
print('Parsed OK')
"

# Check file size
wc -c output.html

# Check for broken internal references
grep -n 'src=\|href=' output.html | grep -v 'data:' | grep -v 'http'
```

---

## QA Checklist

- [ ] Validates as well-formed HTML
- [ ] All CSS is inline (no external stylesheets)
- [ ] All images are base64-encoded or absolute URLs
- [ ] Renders correctly at A4 width (210mm / ~794px)
- [ ] `@media print` styles defined
- [ ] Tables have `border-collapse: collapse`
- [ ] Text contrast meets WCAG AA (4.5:1 minimum)
- [ ] No JavaScript required for correct rendering
- [ ] `<title>` tag populated
- [ ] `lang` attribute set on `<html>`

---

## Common Mistakes to Avoid

- Linking to external stylesheets (breaks self-contained requirement)
- Using relative image paths (breaks when moved)
- Forgetting `@page` rules for PDF conversion
- Using `position: fixed` elements in print documents
- Missing `box-sizing: border-box` (causes layout overflow)
- Tables wider than page (use `overflow-x: auto` wrapper for screen, constrain for print)

---

## Dependencies

```bash
pip install weasyprint --break-system-packages
# Chrome headless: system-installed (may not be in all sandboxes)
```
