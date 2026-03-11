---
name: optimized-video-export
description: "Use this skill when producing or processing video files — format conversion, compression, trimming, frame extraction, or adding overlays. Covers .mp4, .webm, .mov output via FFmpeg. Trigger on any video output request or media processing task."
---

# Optimized Video Export SKILL

## Quick Reference

| Task | FFmpeg Command |
|------|---------------|
| Convert to MP4 (H.264) | `ffmpeg -i input -c:v libx264 -crf 23 output.mp4` |
| Convert to WebM (VP9) | `ffmpeg -i input -c:v libvpx-vp9 -b:v 0 -crf 33 output.webm` |
| Compress video | `-crf 28` (higher = smaller/lower quality) |
| Trim | `-ss 00:00:10 -to 00:01:30` |
| Extract frames | `-vf fps=1 frame_%04d.png` |
| Add watermark | `-i watermark.png -filter_complex overlay=10:10` |
| Scale/resize | `-vf scale=1920:1080` or `-vf scale=1280:-1` |

---

## MP4 / H.264 (Primary Web Format)

```bash
# Standard web-optimized MP4
ffmpeg -i input.mov \
  -c:v libx264 \
  -preset slow \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  -pix_fmt yuv420p \
  output.mp4

# Flags explained:
# -crf 23       Quality: 0 (lossless) to 51 (worst). 18-28 typical.
# -preset slow  Better compression at cost of encode time
# -movflags +faststart  Move metadata to front (web streaming)
# -pix_fmt yuv420p      Browser compatibility
```

---

## WebM / VP9 (Open Format)

```bash
# Two-pass VP9 for best quality/size ratio
ffmpeg -i input.mp4 \
  -c:v libvpx-vp9 \
  -b:v 0 -crf 33 \
  -pass 1 -an \
  -f null /dev/null

ffmpeg -i input.mp4 \
  -c:v libvpx-vp9 \
  -b:v 0 -crf 33 \
  -pass 2 \
  -c:a libopus -b:a 128k \
  output.webm
```

---

## Resolution Presets

```bash
# 1080p
ffmpeg -i input.mp4 -vf scale=1920:1080 -c:v libx264 -crf 23 1080p.mp4

# 720p (maintain aspect ratio)
ffmpeg -i input.mp4 -vf scale=1280:-2 -c:v libx264 -crf 23 720p.mp4

# 480p
ffmpeg -i input.mp4 -vf scale=854:-2 -c:v libx264 -crf 23 480p.mp4

# Square (social media)
ffmpeg -i input.mp4 \
  -vf "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2" \
  square.mp4
```

---

## Trimming

```bash
# Trim without re-encoding (fast, may be imprecise)
ffmpeg -ss 00:01:00 -to 00:02:30 -i input.mp4 -c copy trimmed.mp4

# Trim with re-encoding (precise)
ffmpeg -i input.mp4 -ss 00:01:00 -to 00:02:30 \
  -c:v libx264 -crf 23 trimmed_precise.mp4
```

---

## Frame Extraction

```bash
# Extract 1 frame per second
ffmpeg -i input.mp4 -vf fps=1 frames/frame_%04d.jpg

# Extract specific frame at timestamp
ffmpeg -i input.mp4 -ss 00:00:30 -vframes 1 thumbnail.jpg

# Extract all frames (use with caution on long videos)
ffmpeg -i input.mp4 frames/frame_%04d.png
```

---

## Add Text Overlay

```bash
ffmpeg -i input.mp4 \
  -vf "drawtext=text='CONFIDENTIAL':
       fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
       fontsize=36:fontcolor=white@0.5:
       x=(w-text_w)/2:y=h-th-20" \
  -c:a copy \
  watermarked.mp4
```

---

## Image Sequence → Video

```bash
# PNG sequence to MP4 (e.g. from rendered frames)
ffmpeg -framerate 30 -i frame_%04d.png \
  -c:v libx264 -crf 20 -pix_fmt yuv420p \
  output.mp4
```

---

## CLI Verification

```bash
# Get video info
ffprobe -v quiet -print_format json -show_streams output.mp4 | \
  python -m json.tool | grep -E '"codec_name"|"width"|"height"|"duration"|"bit_rate"'

# Quick info summary
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,duration \
  -of csv=p=0 output.mp4

# File size
ls -lh output.mp4

# Verify playable
ffmpeg -v error -i output.mp4 -f null - 2>&1 | head -20
```

---

## CRF Quality Reference

| CRF | H.264 Quality | Use Case |
|-----|--------------|----------|
| 18 | Near-lossless | Archival |
| 23 | High (default) | Web streaming |
| 28 | Medium | Mobile / bandwidth-limited |
| 33+ | Low | Preview / thumbnail |

---

## QA Checklist

- [ ] Output plays without errors
- [ ] Resolution matches target spec
- [ ] Aspect ratio preserved (no stretching)
- [ ] Audio sync correct (check at 30s+ intervals)
- [ ] `-movflags +faststart` set for web delivery
- [ ] `-pix_fmt yuv420p` set for browser compatibility
- [ ] File size within acceptable range
- [ ] Codec verified with `ffprobe`

---

## Common Mistakes to Avoid

- Forgetting `-movflags +faststart` (video won't stream, must fully download)
- Forgetting `-pix_fmt yuv420p` (H.264 may not play in some browsers)
- Using `-crf 0` (lossless — massive file sizes)
- Trimming with `-c copy` when exact frame accuracy needed
- Scaling to odd pixel dimensions (H.264 requires even width/height — use `-2` not `-1`)

---

## Dependencies

```bash
# FFmpeg: system-installed on Ubuntu
sudo apt-get install ffmpeg  # if not present
ffmpeg -version  # verify
```
