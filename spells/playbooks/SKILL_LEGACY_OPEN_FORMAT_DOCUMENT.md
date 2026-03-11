---
name: legacy-open-format-document
description: "Use this skill for legacy or open document formats: .odt (OpenDocument Text), .rtf (Rich Text Format), and plain .doc (legacy Word binary). Trigger when the user explicitly requests these formats, needs cross-platform compatibility without Microsoft Office, or is targeting older software systems."
---

# Legacy / Open Format Document SKILL

## Quick Reference

| Format | Best Tool | Use Case |
|--------|-----------|----------|
| `.odt` | `odfpy` or LibreOffice | Open-source, cross-platform docs |
| `.rtf` | Python `rtf` / manual | Legacy systems, universal compatibility |
| `.doc` | LibreOffice CLI conversion | Older Word binary format |
| Any → `.odt` | LibreOffice CLI | Batch conversion |

---

## ODT (OpenDocument Text)

```python
# pip install odfpy --break-system-packages
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties
from odf.text import H, P, Span

doc = OpenDocumentText()

# Define a style
s = Style(name="Heading1", family="paragraph")
s.addElement(TextProperties(attributes={
    'fo:font-size': '16pt',
    'fo:font-weight': 'bold',
    'fo:color': '#1E2761'
}))
doc.styles.addElement(s)

# Add heading
h = H(outlinelevel=1, stylename="Heading1")
h.addText("Document Title")
doc.text.addElement(h)

# Add paragraph
p = P(stylename="Text_20_Body")
p.addText("Body content here.")
doc.text.addElement(p)

doc.save("output.odt")
```

---

## RTF (Rich Text Format)

```python
# Manual RTF construction — most reliable approach
def make_rtf(title, body_paragraphs):
    lines = [
        r'{\rtf1\ansi\deff0',
        r'{\fonttbl{\f0 Arial;}}',
        r'{\colortbl;\red30\green39\blue97;}',  # Navy accent
        r'\f0',
        rf'\b\fs32 {title}\b0\par',
        r'\fs22',
    ]
    for para in body_paragraphs:
        lines.append(rf'{para}\par')
    lines.append(r'}')
    return '\n'.join(lines)

content = make_rtf(
    "Report Title",
    ["First paragraph.", "Second paragraph."]
)

with open("output.rtf", "w", encoding="ascii", errors="replace") as f:
    f.write(content)
```

### RTF Escape Rules
- Special chars must be escaped: `\`, `{`, `}` → `\\`, `\{`, `\}`
- Non-ASCII characters: use `\'XX` hex encoding
- Unicode: `\uN?` where N is decimal codepoint

---

## LibreOffice CLI Conversions

```bash
# Convert docx → odt
python scripts/office/soffice.py --headless \
  --convert-to odt input.docx

# Convert odt → pdf
python scripts/office/soffice.py --headless \
  --convert-to pdf input.odt

# Convert docx → rtf
python scripts/office/soffice.py --headless \
  --convert-to rtf input.docx

# Batch convert all docx in directory
python scripts/office/soffice.py --headless \
  --convert-to odt *.docx
```

---

## Verifying Output

```bash
# ODT is a ZIP — inspect contents
unzip -l output.odt

# Extract ODT text content
python -c "
from odf.opendocument import load
from odf.text import P
doc = load('output.odt')
for p in doc.text.getElementsByType(P):
    print(p)
"

# RTF — preview first 50 lines
head -n 50 output.rtf

# Validate RTF brace balance
python -c "
with open('output.rtf') as f:
    c = f.read()
print('Open:', c.count('{'), 'Close:', c.count('}'))
"
```

---

## QA Checklist

- [ ] File opens in LibreOffice without errors
- [ ] Headings render at correct sizes
- [ ] Special characters display correctly (not garbled)
- [ ] RTF brace count balanced (`{` == `}`)
- [ ] ODT content.xml is well-formed XML
- [ ] No Microsoft-specific features used (ODT target)
- [ ] File size reasonable

---

## Common Mistakes to Avoid

- Using Unicode characters directly in RTF (must hex-encode)
- Unbalanced braces in RTF (corrupts entire file)
- Using Word-only features when targeting ODT
- Forgetting that `.doc` (binary) ≠ `.docx` (XML) — use LibreOffice for `.doc` output
- ODT style names with spaces must use `_20_` encoding (e.g., `Text_20_Body`)

---

## Dependencies

```bash
pip install odfpy --break-system-packages
# LibreOffice: pre-configured in sandbox via scripts/office/soffice.py
```
