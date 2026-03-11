---
name: SKILL_IMAGE_GIF_OPTIMIZE
description: "Looping, lossless animation extraction and optimization for UI feedback. Use when producing, converting, or optimizing .gif files for animated documentation, UI demos, loading indicators, or web assets. Triggers: 'GIF', 'animated GIF', '.gif', 'animation', 'screen recording to GIF', 'optimize GIF', 'loading spinner', 'UI feedback animation'."
---

# SKILL_IMAGE_GIF_OPTIMIZE — Animated GIF Skill

## Quick Reference

| Task | Section |
|------|---------|
| Create GIF from frames (Python) | [Create GIF from Frames](#create-gif-from-frames) |
| Screen recording → GIF | [Screen Recording to GIF](#screen-recording-to-gif) |
| Video → GIF | [Video to GIF](#video-to-gif) |
| Optimize existing GIF | [Optimization](#optimization) |
| Pillow animation pipeline | [Pillow Pipeline](#pillow-pipeline) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Format Overview

| Feature | GIF |
|---------|-----|
| Colour depth | 256 colours max per frame (8-bit palette) |
| Transparency | 1-bit (on/off, no partial) |
| Animation | Yes — frame-based with per-frame delay |
| Compression | LZW (lossless within 256-colour limit) |
| Loop control | 0 = infinite loop; N = loop N times |
| Max frame size | No hard limit; practical limit ~800×600 for web |
| Best for | UI demos, loading spinners, diagrams, badges |
| Not ideal for | Full-colour photography (use WebP/APNG) |

---

## Create GIF from Frames

### Pillow — Frame List to GIF

```python
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def frames_to_gif(frames: list, output_path: str,
                  duration_ms: int = 100,
                  loop: int = 0,
                  optimize: bool = True) -> None:
    """
    Save a list of PIL Image frames as an animated GIF.

    frames:      list of PIL.Image objects (RGB or RGBA)
    duration_ms: display time per frame in milliseconds
    loop:        0 = infinite, N = repeat N times
    optimize:    enable palette optimisation
    """
    if not frames:
        raise ValueError("No frames provided")

    # Convert all frames to palette mode for GIF
    palette_frames = [f.convert("P", palette=Image.ADAPTIVE, colors=256)
                      for f in frames]

    palette_frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=palette_frames[1:],
        duration=duration_ms,
        loop=loop,
        optimize=optimize,
        disposal=2       # clear frame before drawing next (avoids ghosting)
    )

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"GIF written: {output_path} "
          f"({len(frames)} frames, {size_kb:.1f} KB)")
```

### Load Frames from Image Files

```python
from PIL import Image
from pathlib import Path

def load_frames_from_dir(frames_dir: str,
                         pattern: str = "*.png") -> list:
    """Load sorted frames from a directory."""
    paths = sorted(Path(frames_dir).glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No files matching {pattern} in {frames_dir}")
    frames = [Image.open(p).convert("RGBA") for p in paths]
    print(f"Loaded {len(frames)} frames from {frames_dir}")
    return frames

frames = load_frames_from_dir("./frames/", "frame_*.png")
frames_to_gif(frames, "animation.gif", duration_ms=80)
```

---

## Pillow Pipeline

### Generate Programmatic Animation

```python
from PIL import Image, ImageDraw
import math

def make_loading_spinner(size: int = 64, frames: int = 12,
                         bg_colour=(255,255,255,0),
                         dot_colour=(50, 120, 230)) -> list:
    """Generate a smooth loading spinner animation."""
    result = []
    radius = size * 0.35
    dot_r  = size * 0.07
    cx = cy = size // 2

    for i in range(frames):
        img = Image.new("RGBA", (size, size), bg_colour)
        draw = ImageDraw.Draw(img)

        for j in range(8):
            angle = (2 * math.pi * j / 8) + (2 * math.pi * i / frames)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            alpha = int(255 * (j + 1) / 8)
            colour = dot_colour + (alpha,)
            draw.ellipse(
                [x - dot_r, y - dot_r, x + dot_r, y + dot_r],
                fill=colour
            )
        result.append(img)

    return result


spinner_frames = make_loading_spinner(size=64, frames=12)
frames_to_gif(spinner_frames, "spinner.gif", duration_ms=80)
```

### Progress Bar Animation

```python
from PIL import Image, ImageDraw

def make_progress_bar(width: int = 400, height: int = 40,
                      steps: int = 20,
                      bar_colour=(46, 160, 67),
                      bg_colour=(240, 240, 240)) -> list:
    """Generate an animated progress bar."""
    frames = []
    for step in range(steps + 1):
        img = Image.new("RGB", (width, height), bg_colour)
        draw = ImageDraw.Draw(img)

        fill_width = int(width * step / steps)
        if fill_width > 0:
            draw.rectangle([0, 0, fill_width, height], fill=bar_colour)

        # Border
        draw.rectangle([0, 0, width-1, height-1], outline=(180,180,180), width=1)
        frames.append(img)

    return frames

bar_frames = make_progress_bar()
frames_to_gif(bar_frames, "progress.gif", duration_ms=60)
```

### Per-Frame Duration (variable timing)

```python
from PIL import Image

def frames_to_gif_variable(frames_with_timing: list,
                            output_path: str,
                            loop: int = 0) -> None:
    """
    frames_with_timing: list of (PIL.Image, duration_ms) tuples
    """
    images   = [f.convert("P", palette=Image.ADAPTIVE) for f, _ in frames_with_timing]
    durations = [d for _, d in frames_with_timing]

    images[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=loop,
        disposal=2
    )

# Example: pause on first and last frames
frames_with_timing = (
    [(frames[0], 1000)]    +   # 1 second pause on first
    [(f, 80) for f in frames[1:-1]] +
    [(frames[-1], 1000)]       # 1 second pause on last
)
frames_to_gif_variable(frames_with_timing, "animation_timed.gif")
```

---

## Screen Recording to GIF

### macOS (using ffmpeg)

```bash
# Install ffmpeg
brew install ffmpeg

# Capture screen region → GIF
# First, record a short video
ffmpeg -f avfoundation -i "1" -t 5 -vf "scale=800:-1" screen_recording.mp4

# Then convert to GIF (see Video to GIF section)
```

### Linux

```bash
# Install tools
sudo apt install peek          # GUI screen-to-GIF recorder
# or: sudo apt install byzanz

# byzanz CLI
byzanz-record --duration=5 --x=0 --y=0 --width=800 --height=600 output.gif
```

### Windows

```powershell
# Install ScreenToGif (GUI app)
winget install NickeManarin.ScreenToGif

# Or use ffmpeg for video → GIF conversion
```

---

## Video to GIF

### ffmpeg (recommended — best quality)

```bash
# Basic video → GIF
ffmpeg -i input.mp4 output.gif

# Optimised: generate palette first, then apply (much better colours)
ffmpeg -i input.mp4 -vf "fps=15,scale=640:-1:flags=lanczos,palettegen" palette.png
ffmpeg -i input.mp4 -i palette.png \
  -filter_complex "fps=15,scale=640:-1:flags=lanczos[x];[x][1:v]paletteuse" \
  output.gif

# Crop time range
ffmpeg -ss 00:00:02 -t 5 -i input.mp4 \
  -vf "fps=12,scale=480:-1:flags=lanczos,palettegen" palette.png
ffmpeg -ss 00:00:02 -t 5 -i input.mp4 -i palette.png \
  -filter_complex "fps=12,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" \
  output.gif

# Parameters to tune:
# fps=10-15   — lower = smaller file, less smooth
# scale=W:-1  — width in px, height auto-preserves aspect ratio
# flags=lanczos — best downscaling algorithm
```

### Python (moviepy)

```python
from moviepy.editor import VideoFileClip

def video_to_gif(input_path: str, output_path: str,
                 fps: int = 12, width: int = 480,
                 start: float = 0, end: float = None) -> None:
    """Convert video clip to GIF."""
    clip = VideoFileClip(input_path)

    if end:
        clip = clip.subclip(start, end)
    elif start:
        clip = clip.subclip(start)

    clip = clip.resize(width=width)
    clip.write_gif(output_path, fps=fps, opt="OptimizePlus")
    clip.close()
    print(f"GIF written: {output_path}")

video_to_gif("demo.mp4", "demo.gif", fps=12, width=600, start=2, end=8)
```

---

## Optimization

### gifsicle (CLI — best compression)

```bash
# Install
sudo apt install gifsicle      # Linux
brew install gifsicle          # macOS

# Optimize (level 1-3, higher = slower but smaller)
gifsicle -O3 input.gif -o output_optimized.gif

# Resize
gifsicle --resize-width 400 input.gif -o output_400.gif

# Reduce colours (fewer colours = smaller file)
gifsicle --colors 64 input.gif -o output_64col.gif

# Combine optimize + resize + reduce colours
gifsicle -O3 --colors 128 --resize-width 480 input.gif -o output.gif

# In-place optimization
gifsicle -O3 -b animation.gif

# Info / inspect
gifsicle -I animation.gif
```

### Python Optimization

```python
from PIL import Image
from pathlib import Path

def optimize_gif(input_path: str, output_path: str,
                 max_colours: int = 128,
                 target_width: int = None) -> dict:
    """
    Optimize GIF: reduce palette and optionally resize.
    Returns dict with before/after size info.
    """
    original_size = Path(input_path).stat().st_size

    img = Image.open(input_path)
    frames = []
    durations = []

    try:
        while True:
            frame = img.copy().convert("RGBA")

            if target_width and frame.width > target_width:
                ratio = target_width / frame.width
                new_size = (target_width, int(frame.height * ratio))
                frame = frame.resize(new_size, Image.LANCZOS)

            frames.append(
                frame.convert("P", palette=Image.ADAPTIVE, colors=max_colours)
            )
            durations.append(img.info.get("duration", 100))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=img.info.get("loop", 0),
        optimize=True,
        disposal=2
    )

    new_size = Path(output_path).stat().st_size
    saving = (1 - new_size / original_size) * 100

    result = {
        "frames":         len(frames),
        "original_kb":    round(original_size / 1024, 1),
        "optimized_kb":   round(new_size / 1024, 1),
        "saving_percent": round(saving, 1)
    }
    print(f"Optimized: {result['original_kb']} KB → {result['optimized_kb']} KB "
          f"({result['saving_percent']}% saving, {result['frames']} frames)")
    return result

optimize_gif("animation.gif", "animation_opt.gif",
             max_colours=128, target_width=480)
```

---

## Validation & QA

```python
from PIL import Image
from pathlib import Path

def validate_gif(path: str, max_size_kb: int = 2048) -> bool:
    errors = []
    p = Path(path)

    if not p.exists():
        print(f"ERROR: File not found: {path}")
        return False

    size_kb = p.stat().st_size / 1024

    try:
        img = Image.open(path)

        if img.format != "GIF":
            errors.append(f"FORMAT ERROR: Expected GIF, got {img.format}")

        # Count frames
        frames = 0
        try:
            while True:
                frames += 1
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        loop    = img.info.get("loop", 0)
        duration = img.info.get("duration", "unknown")

        print(f"Dimensions:  {img.width}×{img.height}")
        print(f"Frames:      {frames}")
        print(f"Loop:        {'infinite' if loop == 0 else loop}")
        print(f"Frame delay: {duration}ms")
        print(f"File size:   {size_kb:.1f} KB")

        if frames < 1:
            errors.append("ERROR: No frames found")
        if size_kb > max_size_kb:
            errors.append(
                f"WARNING: File is {size_kb:.0f} KB "
                f"(exceeds target {max_size_kb} KB)"
            )
        if img.width > 1000 or img.height > 1000:
            errors.append(
                f"WARNING: Large dimensions {img.width}×{img.height} "
                "— consider resizing for web use"
            )

    except Exception as e:
        errors.append(f"READ ERROR: {e}")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: GIF is valid")
    return True

validate_gif("animation.gif", max_size_kb=500)
```

### QA Checklist

- [ ] File opens without error
- [ ] Frame count is correct
- [ ] Loop set to 0 (infinite) for UI feedback animations
- [ ] Frame duration appropriate (60–120ms for smooth animation)
- [ ] File size within target (< 500KB for web, < 2MB for docs)
- [ ] Dimensions appropriate for target use (< 800px wide for web)
- [ ] No ghosting / frame bleed (use `disposal=2`)
- [ ] Colours render correctly (256-colour limit respected)
- [ ] Runs gifsicle `-O3` optimization pass before delivery

### QA Loop

1. Generate or convert GIF
2. Run `validate_gif()` — structure and size check
3. Visual review — play in browser or image viewer
4. Run `gifsicle -O3` — optimize
5. Re-validate post-optimization
6. **Do not deliver until size target met and visual review passes**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Colours look washed out | 256-colour palette limitation | Use `palettegen` + `paletteuse` in ffmpeg |
| Ghosting between frames | `disposal` not set | Add `disposal=2` in Pillow save |
| File too large | High FPS + large dimensions | Reduce FPS to 10–12; resize to ≤ 480px wide |
| Animation plays once and stops | `loop` not set to 0 | Set `loop=0` for infinite loop |
| Jerky animation | Inconsistent frame durations | Standardise all durations to same value |
| Transparency not working | RGBA converted incorrectly | Convert to `P` mode with `palette=Image.ADAPTIVE` |
| White background on transparent GIF | Wrong conversion mode | Keep as RGBA until final `.save()` |

---

## Dependencies

```bash
pip install Pillow           # core image processing
pip install moviepy          # video → GIF conversion

# CLI tools
sudo apt install ffmpeg      # video processing
sudo apt install gifsicle    # GIF optimization
brew install gifsicle        # macOS
```
