---
name: SKILL_SLIDES_REVEALJS_AUTOGEN
description: "Browser-based presentation generation with embedded code execution and styling. Use when producing HTML5 slide decks using Reveal.js for technical presentations, self-contained browser-based decks, or presentations with live code, diagrams, or interactive elements. Triggers: 'Reveal.js', 'HTML5 presentation', 'browser-based slides', 'HTML slides', 'interactive deck'."
---

# SKILL_SLIDES_REVEALJS_AUTOGEN — Reveal.js Slide Deck Skill

## Quick Reference

| Task | Section |
|------|---------|
| Single-file HTML deck | [Single-File Template](#single-file-template) |
| Slide layouts | [Slide Layouts](#slide-layouts) |
| Code highlighting | [Code Highlighting](#code-highlighting) |
| Fragments & animations | [Fragments](#fragments) |
| Themes & styling | [Themes & Styling](#themes--styling) |
| Speaker notes | [Speaker Notes](#speaker-notes) |
| Export to PDF | [Export to PDF](#export-to-pdf) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Single-File Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Presentation Title</title>

  <!-- Reveal.js CDN -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/theme/black.min.css" id="theme">
  <!-- Code highlight theme -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/highlight/monokai.min.css">

  <style>
    :root {
      --r-background-color: #1a1a2e;
      --r-main-font: 'Segoe UI', Arial, sans-serif;
      --r-heading-font: 'Segoe UI', Arial, sans-serif;
      --r-heading-color: #e94560;
      --r-link-color: #4fc3f7;
    }

    .reveal .slides section {
      text-align: left;
    }

    .reveal h1, .reveal h2 {
      text-transform: none;    /* disable ALL-CAPS default */
    }

    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
    }

    .highlight-box {
      background: rgba(233, 69, 96, 0.15);
      border-left: 4px solid #e94560;
      padding: 1rem 1.5rem;
      border-radius: 4px;
    }

    .tag {
      display: inline-block;
      background: #e94560;
      color: white;
      padding: 0.2em 0.6em;
      border-radius: 3px;
      font-size: 0.7em;
      font-weight: bold;
    }
  </style>
</head>
<body>
<div class="reveal">
  <div class="slides">

    <!-- ── TITLE SLIDE ─────────────────────────────────────────────────────── -->
    <section data-background-color="#16213e">
      <h1 style="font-size:2em; color:#e94560;">Presentation Title</h1>
      <h3 style="color:#aaa; font-weight:300;">Subtitle or tagline</h3>
      <br>
      <p style="color:#888; font-size:0.8em;">
        Presenter Name &nbsp;·&nbsp; Date &nbsp;·&nbsp; Organisation
      </p>
    </section>

    <!-- ── SECTION DIVIDER ─────────────────────────────────────────────────── -->
    <section data-background-color="#e94560">
      <h2 style="color:white; text-align:center; font-size:2em;">
        01 — Section Title
      </h2>
    </section>

    <!-- ── TWO COLUMN ──────────────────────────────────────────────────────── -->
    <section>
      <h2>Two Column Layout</h2>
      <div class="two-col">
        <div>
          <h3>Left Column</h3>
          <ul>
            <li>Point A</li>
            <li>Point B</li>
            <li>Point C</li>
          </ul>
        </div>
        <div>
          <h3>Right Column</h3>
          <p>Supporting content, image, or code block.</p>
          <div class="highlight-box">Key insight or callout text here.</div>
        </div>
      </div>
      <aside class="notes">
        Speaker notes — not visible to audience.
        Elaborate on the points in the left column.
      </aside>
    </section>

    <!-- ── CODE SLIDE ──────────────────────────────────────────────────────── -->
    <section>
      <h2>Code Example</h2>
      <pre><code class="python" data-trim data-noescape data-line-numbers="1-3|5-8|10">
        def process(data: list) -> dict:
            """Transform input data."""
            results = {}

            for item in data:
                key = item['id']
                results[key] = item['value'] * 2

            return results
      </code></pre>
      <p class="fragment" style="color:#4fc3f7;">
        ↑ Lines highlight sequentially on advance
      </p>
    </section>

    <!-- ── FRAGMENTS ───────────────────────────────────────────────────────── -->
    <section>
      <h2>Reveal on Advance</h2>
      <ul>
        <li class="fragment">First point appears</li>
        <li class="fragment fade-in-then-semi-out">Second appears, first dims</li>
        <li class="fragment highlight-red">Third highlights red</li>
      </ul>
      <div class="fragment highlight-box" style="margin-top:1.5rem;">
        Final callout appears last.
      </div>
    </section>

    <!-- ── VERTICAL SLIDES ─────────────────────────────────────────────────── -->
    <section>
      <section>
        <h2>Vertical Stack — Top</h2>
        <p>Press ↓ to go deeper.</p>
      </section>
      <section>
        <h2>Vertical Stack — Detail</h2>
        <p>Sub-content for this topic.</p>
      </section>
      <section>
        <h2>Vertical Stack — Bottom</h2>
        <p>Press → to advance to next topic.</p>
      </section>
    </section>

    <!-- ── CLOSING SLIDE ───────────────────────────────────────────────────── -->
    <section data-background-color="#16213e">
      <h2 style="color:#e94560; text-align:center;">Thank You</h2>
      <p style="text-align:center; color:#aaa;">
        name@email.com &nbsp;·&nbsp; @handle
      </p>
    </section>

  </div><!-- /slides -->
</div><!-- /reveal -->

<!-- Reveal.js scripts -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/highlight/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/notes/notes.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/zoom/zoom.min.js"></script>

<script>
  Reveal.initialize({
    hash: true,             // slide URLs update in address bar
    slideNumber: 'c/t',     // current/total slide number
    controls: true,
    progress: true,
    center: false,          // don't vertically centre content
    transition: 'slide',    // none | fade | slide | convex | concave | zoom
    transitionSpeed: 'fast',
    backgroundTransition: 'fade',
    autoAnimateEasing: 'ease',

    plugins: [ RevealHighlight, RevealNotes, RevealZoom ]
  });
</script>
</body>
</html>
```

---

## Slide Layouts

### Full-Screen Background Image

```html
<section data-background-image="images/hero.jpg"
         data-background-size="cover"
         data-background-opacity="0.4">
  <h2>Overlay Title</h2>
  <p>Text over image with opacity control.</p>
</section>
```

### Big Stat / Number Callout

```html
<section>
  <h2>Key Metric</h2>
  <div style="display:flex; align-items:baseline; gap:0.5rem; margin:2rem 0;">
    <span style="font-size:5em; font-weight:900; color:#e94560;">94%</span>
    <span style="font-size:1.5em; color:#aaa;">completion rate</span>
  </div>
  <p>Supporting context sentence here.</p>
</section>
```

### Table Slide

```html
<section>
  <h2>Comparison</h2>
  <table style="font-size:0.8em;">
    <thead>
      <tr style="background:rgba(233,69,96,0.3);">
        <th>Method</th><th>Speed</th><th>Accuracy</th><th>Cost</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Baseline</td><td>Fast</td><td>82%</td><td>Low</td></tr>
      <tr style="background:rgba(255,255,255,0.05);">
        <td><strong>Proposed</strong></td>
        <td>Medium</td>
        <td><strong style="color:#4fc3f7;">94%</strong></td>
        <td>Medium</td>
      </tr>
    </tbody>
  </table>
</section>
```

---

## Code Highlighting

```html
<!-- Basic -->
<pre><code class="python" data-trim>
def hello():
    return "world"
</code></pre>

<!-- Line numbers -->
<pre><code class="python" data-trim data-line-numbers>
line 1
line 2
line 3
</code></pre>

<!-- Highlight specific lines -->
<pre><code class="python" data-trim data-line-numbers="2,4">
line 1          <!-- normal -->
line 2          <!-- highlighted -->
line 3          <!-- normal -->
line 4          <!-- highlighted -->
</code></pre>

<!-- Step through line highlights on advance -->
<pre><code class="python" data-trim data-line-numbers="1|3|5-7">
...
</code></pre>
```

Supported language classes: `python`, `javascript`, `bash`, `sql`, `json`, `yaml`, `html`, `css`, `java`, `cpp`, `rust`, `go`, `dockerfile`.

---

## Fragments

```html
<!-- Appear on advance -->
<p class="fragment">Appears first</p>
<p class="fragment">Appears second</p>

<!-- Animation styles -->
class="fragment fade-in"            <!-- default -->
class="fragment fade-out"
class="fragment fade-up"
class="fragment fade-in-then-out"
class="fragment fade-in-then-semi-out"
class="fragment highlight-red"
class="fragment highlight-green"
class="fragment highlight-blue"
class="fragment grow"
class="fragment shrink"
class="fragment strike"

<!-- Control order -->
<p class="fragment" data-fragment-index="2">I appear second</p>
<p class="fragment" data-fragment-index="1">I appear first</p>
```

---

## Themes & Styling

### Built-in Themes

```html
<!-- Replace theme link href with: -->
theme/black.min.css       <!-- dark background -->
theme/white.min.css       <!-- light background -->
theme/league.min.css      <!-- dark, grey tones -->
theme/beige.min.css       <!-- warm light -->
theme/sky.min.css         <!-- blue/white -->
theme/night.min.css       <!-- dark blue -->
theme/serif.min.css       <!-- serif fonts -->
theme/simple.min.css      <!-- minimal -->
theme/solarized.min.css   <!-- solarized -->
theme/moon.min.css        <!-- dark teal -->
theme/dracula.min.css     <!-- purple dark -->
```

### Auto-Animate Between Slides

```html
<!-- Elements with matching data-id animate between slides -->
<section data-auto-animate>
  <h2 data-id="title">Before</h2>
  <div data-id="box" style="width:100px; height:100px; background:red;"></div>
</section>

<section data-auto-animate>
  <h2 data-id="title">After</h2>
  <div data-id="box" style="width:300px; height:50px; background:blue;"></div>
</section>
```

---

## Speaker Notes

```html
<section>
  <h2>Slide Content</h2>
  <p>Visible to audience.</p>

  <aside class="notes">
    Speaker notes here.
    - Remind audience of context
    - Mention the Q2 case study
    - Allow 2 minutes for questions
    Timing: ~3 minutes for this slide.
  </aside>
</section>
```

Open speaker view: press `S` during presentation.

---

## Export to PDF

```bash
# Method 1: Chrome headless (recommended)
# Add ?print-pdf to URL before printing:
# file:///path/to/presentation.html?print-pdf
# Then: Print → Save as PDF → set paper size to match slide ratio

# Method 2: decktape CLI
npm install -g decktape

decktape reveal presentation.html presentation.pdf
decktape reveal --size 1920x1080 presentation.html presentation.pdf

# Method 3: puppeteer script
npm install puppeteer

node - <<'EOF'
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(`file://${process.cwd()}/presentation.html?print-pdf`);
  await page.pdf({ path: 'presentation.pdf', format: 'A4', landscape: true });
  await browser.close();
  console.log('PDF exported');
})();
EOF
```

---

## Validation & QA

```python
from pathlib import Path
from html.parser import HTMLParser

class SlideCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slides = 0
        self.has_title = False
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            self.slides += 1
        if tag in ("h1", "h2") and self.slides == 1:
            self.has_title = True

def validate_revealjs(html_path: str) -> bool:
    content = Path(html_path).read_text(encoding="utf-8")
    errors = []

    # Check Reveal.js included
    if "reveal.min.js" not in content and "reveal.js" not in content:
        errors.append("ERROR: Reveal.js script not found")

    # Check Reveal.initialize called
    if "Reveal.initialize" not in content:
        errors.append("ERROR: Reveal.initialize() not found")

    # Count slides
    parser = SlideCounter()
    parser.feed(content)
    print(f"Total <section> elements: {parser.slides}")

    if parser.slides < 2:
        errors.append("WARNING: Fewer than 2 slides found")

    # Check for speaker notes plugin if notes exist
    if "aside class=\"notes\"" in content and "RevealNotes" not in content:
        errors.append("WARNING: Notes found but RevealNotes plugin not loaded")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Deck structure is valid")
    return True

validate_revealjs("presentation.html")
```

### QA Checklist

- [ ] Opens in browser without console errors
- [ ] All slides navigate correctly (→ and ↓)
- [ ] Vertical stacks (sub-slides) work as intended
- [ ] Code blocks render with syntax highlighting
- [ ] Fragments appear in correct order
- [ ] Speaker notes accessible via `S` key
- [ ] `hash: true` enabled (slide URLs are shareable)
- [ ] Slide number shown (`slideNumber: 'c/t'`)
- [ ] Title slide has presenter name and date
- [ ] Exported PDF reviewed — no content cut off

### QA Loop

1. Write HTML deck
2. Open in browser — navigate all slides
3. Check console (F12) — zero errors
4. Press `S` — verify speaker notes open
5. Test on mobile / smaller window — check responsive
6. Export PDF — spot-check all slides render
7. **Do not distribute until full navigation test passes**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Slides don't scroll / navigate | JS not loaded | Check CDN URL and network; use local fallback |
| Content overflows slide | Too much text | Reduce font size; split into two slides |
| Code not highlighted | Missing highlight plugin / CSS | Add `RevealHighlight` plugin and monokai CSS |
| Vertical slides not working | Nested sections not inside parent `<section>` | Wrap sub-sections in a parent `<section>` |
| `text-transform: uppercase` on headings | Reveal.js default | Override: `h2 { text-transform: none; }` |
| PDF export cuts off content | Slide overflow | Reduce content; use `data-auto-animate` or scrollable |
| Background image not loading | Relative path issue | Use absolute path or embed as base64 |

---

## Dependencies

```bash
# No install needed — CDN-based
# CDN: https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/

# PDF export
npm install -g decktape

# Local Reveal.js install (offline use)
npm install reveal.js
```
