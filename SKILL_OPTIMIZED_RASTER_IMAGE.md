---
name: optimized-raster-image
description: "Use this skill when producing or processing raster images — JPEG, PNG, GIF, WebP. Covers compression, resizing, color correction, watermarking, and format optimization. Trigger on any image processing, thumbnail generation, or raster output task."
---

# Optimized Raster Image SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Resize, convert, compress | `Pillow` (Python) |
| Batch processing | `Pillow` + `pathlib` |
| JPEG optimization | `Pillow` + `mozjpeg` or `optimize-images` |
| PNG optimization | `pngquant` CLI |
| WebP conversion | `Pillow` or `cwebp` CLI |
| EXIF stripping | `Pillow` (`ImageOps.exif_transpose` + resave) |
| Image info | `Pillow` or `exiftool` |

---

## Core Pillow Operations

```python
# pip install Pillow --break-system-packages
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont
import os

# Open
img = Image.open("input.jpg")
print(f"Size: {img.size}, Mode: {img.mode}, Format: {img.format}")

# Resize (maintain aspect ratio)
img.thumbnail((1920, 1080), Image.LANCZOS)  # In-place max dimensions

# Resize to exact dimensions
img_resized = img.resize((800, 600), Image.LANCZOS)

# Resize to width, preserve aspect ratio
w_target = 1280
ratio = w_target / img.width
h_target = int(img.height * ratio)
img_resized = img.resize((w_target, h_target), Image.LANCZOS)

# Crop (left, upper, right, lower)
img_cropped = img.crop((100, 100, 900, 700))

# Rotate
img_rotated = img.rotate(90, expand=True)

# Convert mode
img_rgb = img.convert("RGB")        # Force RGB (removes alpha)
img_gray = img.convert("L")         # Grayscale
img_rgba = img.convert("RGBA")      # Add alpha channel
```

---

## Saving with Quality Control

```python
# JPEG — high quality web
img.save("output.jpg", format="JPEG",
         quality=85,
         optimize=True,
         progressive=True)  # Progressive JPEG for web

# PNG — lossless with compression
img.save("output.png", format="PNG",
         optimize=True,
         compress_level=6)  # 0-9, default 6

# WebP — modern format, excellent compression
img.save("output.webp", format="WEBP",
         quality=80,
         method=6)  # method 0-6, higher = slower but smaller

# WebP lossless
img.save("output.webp", format="WEBP", lossless=True)

# GIF (for simple graphics/animations only)
img.save("output.gif", format="GIF", optimize=True)
```

---

## Batch Processing

```python
from pathlib import Path

def batch_resize_and_convert(input_dir, output_dir, max_size=(1920, 1080), quality=85):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for img_file in input_path.glob("*.{jpg,jpeg,png,webp,tiff}"):
        with Image.open(img_file) as img:
            img = img.convert("RGB")
            img.thumbnail(max_size, Image.LANCZOS)
            out_file = output_path / (img_file.stem + ".jpg")
            img.save(out_file, format="JPEG", quality=quality, optimize=True)
            print(f"Processed: {img_file.name} → {out_file.name}")
```

---

## Watermarking

```python
from PIL import Image, ImageDraw, ImageFont

def add_text_watermark(img_path, text, output_path, opacity=80):
    img = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(20, img.width // 30)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = img.width - text_w - 20
    y = img.height - text_h - 20

    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    watermarked = Image.alpha_composite(img, overlay)
    watermarked.convert("RGB").save(output_path, quality=90)
```

---

## Thumbnail Generation

```python
def generate_thumbnails(img_path, sizes):
    """sizes: dict of {label: (width, height)}"""
    img = Image.open(img_path).convert("RGB")
    base = Path(img_path).stem

    for label, size in sizes.items():
        thumb = img.copy()
        thumb.thumbnail(size, Image.LANCZOS)
        thumb.save(f"{base}_{label}.jpg", quality=80, optimize=True)
        print(f"Saved: {base}_{label}.jpg ({thumb.size})")

generate_thumbnails("hero.jpg", {
    "sm":  (320, 240),
    "md":  (640, 480),
    "lg":  (1280, 960),
})
```

---

## CLI Optimization Tools

```bash
# PNG compression with pngquant
pngquant --quality=60-80 --output output_compressed.png input.png

# WebP conversion
cwebp -q 80 input.jpg -o output.webp
dwebp output.webp -o restored.png

# Strip EXIF metadata
exiftool -all= -overwrite_original output.jpg

# Image info
identify output.jpg  # ImageMagick
exiftool output.jpg

# Check file sizes
ls -lh *.jpg *.png *.webp 2>/dev/null
```

---

## Format Selection Guide

| Format | Best For | Avoid When |
|--------|----------|------------|
| JPEG | Photos, complex images | Transparency needed |
| PNG | Screenshots, logos, transparency | Photos (large size) |
| WebP | Web delivery (photos + graphics) | Legacy browser support needed |
| GIF | Simple animations | Photos, >256 colors |
| TIFF | Archival, print production | Web delivery |

---

## QA Checklist

- [ ] Output resolution correct
- [ ] Aspect ratio preserved (no distortion)
- [ ] File size within target range
- [ ] No visible compression artifacts at 100% zoom
- [ ] Color mode correct (RGB for web, CMYK only for print)
- [ ] Alpha channel preserved if required (PNG/WebP)
- [ ] Progressive JPEG used for web images > 10KB
- [ ] EXIF metadata stripped if privacy required
- [ ] Batch: all source files processed (count matches)

---

## Common Mistakes to Avoid

- Enlarging images (only shrink — `thumbnail()` won't upscale)
- Saving JPEG with `quality=100` (doesn't mean lossless — use PNG instead)
- Converting RGBA → JPEG directly (removes alpha, may produce black background — convert to RGB first)
- Using `Image.NEAREST` for photos (produces pixelation — use `Image.LANCZOS`)
- Forgetting `optimize=True` for JPEG/PNG (leaves significant file size on table)

---

## Dependencies

```bash
pip install Pillow --break-system-packages
# pngquant: sudo apt-get install pngquant
# cwebp/dwebp: sudo apt-get install webp
# exiftool: sudo apt-get install exiftool
# ImageMagick: sudo apt-get install imagemagick
```
