---
name: cross-platform-image-export
description: "Use this skill when producing images that must work across platforms, devices, and contexts — print, web, mobile, and large format. Covers DPI/PPI targeting, color profile management, multi-resolution export, and format compatibility matrices. Trigger when output must meet specific platform or print specifications."
---

# Cross-Platform Image Export SKILL

## Quick Reference

| Target | Format | DPI | Color Mode |
|--------|--------|-----|------------|
| Web / screen | JPEG, PNG, WebP | 72–96 | sRGB |
| Mobile retina | PNG @2x, WebP | 144–192 | sRGB |
| Print (standard) | TIFF, PDF, PNG | 300 | CMYK or sRGB |
| Print (large format) | TIFF, PDF | 150 | CMYK |
| Archival | TIFF | 600 | sRGB or Adobe RGB |
| Email | JPEG | 96 | sRGB |

---

## DPI-Aware Export

```python
from PIL import Image

def export_for_print(img_path, output_path, dpi=300):
    """Export image with correct DPI metadata for print."""
    img = Image.open(img_path).convert("RGB")
    img.save(output_path, dpi=(dpi, dpi), quality=95)
    print(f"Saved {output_path} at {dpi} DPI")

def export_for_web(img_path, output_path, max_width=1920):
    """Optimize for web: correct DPI, progressive, optimized."""
    img = Image.open(img_path).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    img.save(output_path, format="JPEG",
             quality=85, optimize=True,
             progressive=True, dpi=(96, 96))
```

---

## Multi-Resolution Export (Retina / HiDPI)

```python
from PIL import Image
from pathlib import Path

def export_responsive_set(img_path, output_dir, base_width=800):
    """Export @1x, @2x, @3x versions for responsive/retina use."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    img = Image.open(img_path).convert("RGB")
    stem = Path(img_path).stem

    sizes = {
        "":    base_width,
        "@2x": base_width * 2,
        "@3x": base_width * 3,
    }

    for suffix, width in sizes.items():
        if img.width < width:
            print(f"Warning: source image too small for {suffix} ({width}px)")
            continue
        ratio = width / img.width
        h = int(img.height * ratio)
        resized = img.resize((width, h), Image.LANCZOS)
        outfile = f"{output_dir}/{stem}{suffix}.jpg"
        resized.save(outfile, quality=85, optimize=True, dpi=(96, 96))
        print(f"Saved: {outfile} ({width}×{h})")
```

---

## Color Profile Handling

```python
# Check color profile
from PIL import Image
img = Image.open("input.jpg")
icc_profile = img.info.get("icc_profile")
if icc_profile:
    print(f"Has ICC profile: {len(icc_profile)} bytes")
else:
    print("No ICC profile (assume sRGB)")

# Preserve ICC profile on save
img.save("output.jpg", icc_profile=icc_profile, quality=90)

# Strip ICC profile (web optimization — reduces file size)
img_no_icc = Image.open("input.jpg")
img_no_icc.info.pop("icc_profile", None)
img_no_icc.save("output_no_icc.jpg", quality=85)
```

---

## CMYK for Print

```python
# Convert sRGB to CMYK for print production
# Note: Pillow's CMYK conversion is approximate — use a color-managed workflow for critical print work

img_rgb = Image.open("input.jpg").convert("RGB")
img_cmyk = img_rgb.convert("CMYK")

# Save as TIFF (preferred for print)
img_cmyk.save("print_ready.tif", format="TIFF",
              compression="lzw", dpi=(300, 300))

# Or as JPEG CMYK
img_cmyk.save("print_ready.jpg", format="JPEG",
              quality=95, dpi=(300, 300))
```

---

## Physical Size Calculator

```python
def pixels_for_print(width_mm, height_mm, dpi=300):
    """Calculate pixel dimensions for a physical print size."""
    px_per_mm = dpi / 25.4
    px_w = int(width_mm * px_per_mm)
    px_h = int(height_mm * px_per_mm)
    print(f"{width_mm}mm × {height_mm}mm @ {dpi}dpi = {px_w} × {px_h}px")
    return px_w, px_h

# Common print sizes
pixels_for_print(210, 297, 300)   # A4 at 300 DPI
pixels_for_print(594, 841, 150)   # A1 at 150 DPI (large format)
pixels_for_print(25.4, 25.4, 96)  # 1 inch at screen resolution
```

---

## Platform Export Matrix

```python
def export_all_platforms(source_path, output_dir, base_name):
    """Export a source image for all common platform targets."""
    from pathlib import Path
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    img = Image.open(source_path).convert("RGB")

    exports = [
        # (suffix, width, format, quality, dpi)
        ("_web_1x.jpg",    960,  "JPEG", 85,  96),
        ("_web_2x.jpg",    1920, "JPEG", 85,  96),
        ("_web.webp",      960,  "WEBP", 80,  96),
        ("_mobile.jpg",    640,  "JPEG", 80,  96),
        ("_email.jpg",     600,  "JPEG", 75,  96),
        ("_thumb.jpg",     300,  "JPEG", 80,  96),
        ("_print_300.jpg", None, "JPEG", 95,  300),  # None = keep original size
    ]

    for suffix, width, fmt, quality, dpi in exports:
        out = img.copy()
        if width and out.width > width:
            ratio = width / out.width
            out = out.resize((width, int(out.height * ratio)), Image.LANCZOS)
        out_path = f"{output_dir}/{base_name}{suffix}"
        out.save(out_path, format=fmt, quality=quality,
                 optimize=True, dpi=(dpi, dpi))
        size_kb = Path(out_path).stat().st_size // 1024
        print(f"Saved: {out_path} ({out.size[0]}×{out.size[1]}, {size_kb}KB)")
```

---

## CLI Verification

```bash
# Check DPI and dimensions
python -c "
from PIL import Image
img = Image.open('output.jpg')
dpi = img.info.get('dpi', 'Not set')
print(f'Size: {img.size}, Mode: {img.mode}, DPI: {dpi}')
"

# Identify with ImageMagick (detailed info)
identify -verbose output.jpg | grep -E "Geometry|Resolution|Colorspace|Type"

# Check all exports
for f in output_dir/*.jpg output_dir/*.webp; do
  python -c "
from PIL import Image; import sys, os
img = Image.open('$f')
size = os.path.getsize('$f') // 1024
print(f'$f: {img.size} | {img.mode} | {size}KB | DPI:{img.info.get(\"dpi\",\"N/A\")}')
"
done
```

---

## QA Checklist

- [ ] DPI metadata correct for intended output (72/96 for screen, 300 for print)
- [ ] Physical dimensions correct (verify with `pixels_for_print()` if print target)
- [ ] Color mode correct (RGB for screen, CMYK for print)
- [ ] ICC profile preserved for print output; stripped for web optimization
- [ ] @2x / @3x versions have correct pixel dimensions (exact 2× or 3× of @1x)
- [ ] No upscaling (output ≤ source resolution)
- [ ] File sizes within platform targets (web: <500KB, email: <200KB, print: no limit)
- [ ] Aspect ratio preserved across all export sizes

---

## Common Mistakes to Avoid

- Setting DPI metadata without actually having enough pixels (DPI in JPEG is just metadata — physical resolution depends on pixel count)
- Upscaling source images (never improves quality)
- Saving all web images at 300 DPI (wastes bandwidth — browsers ignore DPI for screen rendering)
- Forgetting to strip ICC profile for email (increases file size, may cause color shifts in some clients)
- Using CMYK for web (browsers don't support CMYK JPEG correctly)

---

## Dependencies

```bash
pip install Pillow --break-system-packages
# ImageMagick: sudo apt-get install imagemagick
# cwebp: sudo apt-get install webp
# exiftool: sudo apt-get install exiftool
```
