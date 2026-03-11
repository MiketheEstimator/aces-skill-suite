---
name: legacy-ppt-apple-key
description: "Use this skill when producing legacy .ppt (PowerPoint 97-2003) or Apple .key (Keynote) files. Trigger when the user explicitly requests these formats, needs compatibility with older PowerPoint versions, or is targeting an Apple Keynote workflow."
---

# Legacy .ppt / Apple .key SKILL

## Quick Reference

| Format | Best Path | Notes |
|--------|-----------|-------|
| `.ppt` | Create `.pptx` → convert via LibreOffice | No native Python .ppt writer |
| `.key` | Create `.pptx` → convert via LibreOffice or Keynote CLI | Fidelity varies |
| `.ppt` QA | Open in LibreOffice Impress | Check layout fidelity |
| `.key` QA | Keynote (macOS only) | or LibreOffice fallback |

---

## .ppt Output (via LibreOffice Conversion)

The safest pipeline: produce a clean `.pptx` first, then convert.

```bash
# Step 1: Create output.pptx (use automated-insight-deck-generator skill)

# Step 2: Convert pptx → ppt
python scripts/office/soffice.py --headless \
  --convert-to ppt output.pptx

# Output: output.ppt
```

---

## .ppt Compatibility Constraints

When building the source `.pptx` for `.ppt` conversion, restrict features to maximize fidelity:

```javascript
// pptxgenjs — .ppt-safe feature set
// AVOID:
// - Gradients with multiple stops (use flat fills)
// - SmartArt (convert to shapes)
// - 3D effects
// - Video/audio embeds
// - Custom fonts (stick to Arial, Times New Roman, Courier)
// - Transparency effects
// - Complex animations (will be dropped)

// SAFE:
// - Solid fills
// - Standard shapes (rect, oval, line, arrow)
// - Embedded images (JPEG/PNG)
// - Standard bar/pie/line charts
// - Tables with simple borders
// - Arial / Helvetica / Times New Roman fonts
```

---

## Verified .ppt-Safe Slide Template

```javascript
const pptx = require("pptxgenjs");
const pres = new pptx();
pres.layout = "LAYOUT_4x3";  // Legacy decks often use 4:3

function addPptSafeSlide(pres, title, bodyText) {
    const slide = pres.addSlide();
    
    // Solid fill only (no gradients)
    slide.background = { color: "FFFFFF" };
    
    // Title — Arial only
    slide.addText(title, {
        x: 0.5, y: 0.3, w: 9, h: 0.8,
        fontSize: 28, bold: true,
        color: "003366",
        fontFace: "Arial"  // Safe legacy font
    });
    
    // Horizontal rule (shape, not CSS)
    slide.addShape(pres.ShapeType.rect, {
        x: 0.5, y: 1.1, w: 9, h: 0.04,
        fill: { color: "003366" }
    });
    
    // Body
    slide.addText(bodyText, {
        x: 0.5, y: 1.3, w: 9, h: 4.5,
        fontSize: 16,
        color: "333333",
        fontFace: "Arial",
        valign: "top"
    });
}
```

---

## Apple .key (Keynote) Output

```bash
# Path 1: LibreOffice conversion (pptx → key)
python scripts/office/soffice.py --headless \
  --convert-to key output.pptx
# Note: LibreOffice .key support is limited — use for simple decks only

# Path 2: macOS Keynote CLI (if on Mac with Keynote installed)
osascript -e '
tell application "Keynote"
    set theDoc to open POSIX file "/path/to/output.pptx"
    export theDoc to POSIX file "/path/to/output.key" \
        as Keynote 09
    close theDoc
end tell
'
```

### Keynote-Specific Considerations

- Keynote uses its own transition and animation system — PowerPoint animations will not transfer
- Custom fonts must be installed on the Mac running Keynote
- Charts will convert but may lose styling nuances
- Master slide/theme may reset to Keynote defaults
- Keynote `.key` files are actually ZIP archives containing XML + assets

---

## Inspecting .key Archive

```bash
# .key is a zip — inspect contents
cp output.key output_key.zip
unzip -l output_key.zip

# Extract and view index.apxl (main XML)
unzip output_key.zip index.apxl
head -100 index.apxl
```

---

## CLI Verification

```bash
# Verify .ppt file
python -c "
import struct
with open('output.ppt', 'rb') as f:
    magic = f.read(8)
# OLE2 compound doc magic bytes
assert magic[:4] == b'\xd0\xcf\x11\xe0', 'Not valid OLE2/PPT format'
print('Valid .ppt binary format ✓')
"

# Open in LibreOffice for visual check
python scripts/office/soffice.py output.ppt

# Convert to images for inspection
python scripts/office/soffice.py --headless --convert-to pdf output.ppt
pdftoppm -jpeg -r 150 output.pdf slide
```

---

## QA Checklist

- [ ] File opens in LibreOffice Impress without errors
- [ ] No missing font warnings (only Arial/Times/Courier used)
- [ ] Images render correctly (not broken)
- [ ] Slide layout preserved (check against source .pptx images)
- [ ] Tables render with correct borders
- [ ] Charts display data correctly
- [ ] Slide count matches source
- [ ] File binary header valid (OLE2 magic bytes for .ppt)

---

## Common Mistakes to Avoid

- Using gradient fills (often lost in .ppt conversion)
- Embedding web fonts or unusual font faces
- Using 16:9 layout when legacy target expects 4:3
- Assuming animation/transition fidelity (it won't transfer)
- Building directly in `.ppt` format — always go via `.pptx`

---

## Dependencies

```bash
npm install -g pptxgenjs
# LibreOffice: pre-configured in sandbox via scripts/office/soffice.py
# Keynote: macOS only (not available in sandbox)
```
