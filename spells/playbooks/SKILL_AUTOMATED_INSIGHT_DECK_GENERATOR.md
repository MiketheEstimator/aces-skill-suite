---
name: automated-insight-deck-generator
description: "Use this skill when generating .pptx presentation files programmatically, especially data-driven or insight-focused decks. Covers creating from scratch with pptxgenjs, chart integration, consistent theming, and visual QA. Trigger on any .pptx creation request. For editing existing presentations, also read editing.md."
---

# Automated Insight Deck Generator SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Create from scratch | `pptxgenjs` (Node.js) |
| Edit existing template | `python-pptx` |
| Extract content | `markitdown` |
| Visual inspection | `pdftoppm` via LibreOffice |
| Charts | `pptxgenjs` built-in chart API |

---

## Setup

```bash
npm install -g pptxgenjs
# Or local:
npm install pptxgenjs
```

---

## Base Deck Structure (pptxgenjs)

```javascript
const pptx = require("pptxgenjs");
const pres = new pptx();

// Master settings
pres.layout = "LAYOUT_WIDE";  // 16:9
pres.author = "Generated";
pres.title = "Insight Report";

// Define theme colors
const THEME = {
    primary:    "1E2761",  // Navy
    accent:     "F96167",  // Coral
    light:      "F5F7FA",  // Off-white
    dark:       "1A1A2E",  // Near-black
    muted:      "8892A4",  // Gray
    white:      "FFFFFF"
};

const FONT = {
    heading:    "Calibri",
    body:       "Calibri"
};
```

---

## Title Slide

```javascript
function addTitleSlide(pres, title, subtitle, date) {
    const slide = pres.addSlide();
    
    // Dark background
    slide.background = { color: THEME.dark };
    
    // Accent bar
    slide.addShape(pres.ShapeType.rect, {
        x: 0, y: 3.2, w: "100%", h: 0.06,
        fill: { color: THEME.accent }
    });
    
    // Title
    slide.addText(title, {
        x: 0.6, y: 1.5, w: 8.8, h: 1.2,
        fontSize: 40, bold: true,
        color: THEME.white,
        fontFace: FONT.heading
    });
    
    // Subtitle
    slide.addText(subtitle, {
        x: 0.6, y: 2.8, w: 8.8, h: 0.5,
        fontSize: 18,
        color: THEME.muted,
        fontFace: FONT.body
    });
    
    // Date
    slide.addText(date, {
        x: 0.6, y: 4.6, w: 8.8, h: 0.3,
        fontSize: 12,
        color: THEME.muted
    });
}
```

---

## Content Slide with Two Columns

```javascript
function addTwoColSlide(pres, title, leftContent, rightContent) {
    const slide = pres.addSlide();
    slide.background = { color: THEME.light };
    
    // Title bar
    slide.addShape(pres.ShapeType.rect, {
        x: 0, y: 0, w: "100%", h: 0.9,
        fill: { color: THEME.primary }
    });
    slide.addText(title, {
        x: 0.5, y: 0.1, w: 9, h: 0.7,
        fontSize: 22, bold: true,
        color: THEME.white, fontFace: FONT.heading
    });
    
    // Left column
    slide.addText(leftContent, {
        x: 0.5, y: 1.1, w: 4.2, h: 3.8,
        fontSize: 14, color: "333333",
        fontFace: FONT.body, valign: "top"
    });
    
    // Divider
    slide.addShape(pres.ShapeType.rect, {
        x: 4.9, y: 1.0, w: 0.02, h: 4.0,
        fill: { color: "CCCCCC" }
    });
    
    // Right column
    slide.addText(rightContent, {
        x: 5.1, y: 1.1, w: 4.2, h: 3.8,
        fontSize: 14, color: "333333",
        fontFace: FONT.body, valign: "top"
    });
}
```

---

## Big Stat Callout Slide

```javascript
function addStatSlide(pres, title, stats) {
    // stats = [{value: "94%", label: "On Budget"}, ...]
    const slide = pres.addSlide();
    slide.background = { color: THEME.primary };
    
    slide.addText(title, {
        x: 0.5, y: 0.3, w: 9, h: 0.6,
        fontSize: 24, bold: true,
        color: THEME.white, align: "center"
    });
    
    const colWidth = 9.0 / stats.length;
    stats.forEach((stat, i) => {
        const x = 0.5 + (i * colWidth);
        
        // Large number
        slide.addText(stat.value, {
            x, y: 1.5, w: colWidth, h: 1.5,
            fontSize: 64, bold: true,
            color: THEME.accent, align: "center"
        });
        
        // Label
        slide.addText(stat.label, {
            x, y: 3.0, w: colWidth, h: 0.5,
            fontSize: 16,
            color: THEME.white, align: "center"
        });
    });
}
```

---

## Bar Chart Slide

```javascript
function addBarChartSlide(pres, title, labels, values, seriesName) {
    const slide = pres.addSlide();
    slide.background = { color: THEME.light };
    
    slide.addText(title, {
        x: 0.5, y: 0.2, w: 9, h: 0.6,
        fontSize: 22, bold: true,
        color: THEME.primary
    });
    
    slide.addChart(pres.ChartType.bar, [
        {
            name: seriesName,
            labels: labels,
            values: values
        }
    ], {
        x: 0.5, y: 0.9, w: 9, h: 4.2,
        barDir: "col",
        chartColors: [THEME.primary, THEME.accent],
        showValue: true,
        dataLabelFontSize: 10,
        valAxisMajorUnit: Math.ceil(Math.max(...values) / 5)
    });
}
```

---

## Save and Export

```javascript
async function buildDeck() {
    // ... add slides ...
    await pres.writeFile({ fileName: "output.pptx" });
    console.log("Saved: output.pptx");
}
buildDeck();
```

---

## Visual QA Workflow

```bash
# 1. Convert to images
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# 2. Inspect each slide image
# slide-01.jpg, slide-02.jpg, etc.

# 3. Text content check
python -m markitdown output.pptx

# 4. Check for placeholder text
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder"
```

---

## QA Checklist

- [ ] All slides use consistent color theme
- [ ] No slide has text-only layout (every slide has a visual element)
- [ ] Title font ≥ 36pt, body ≥ 14pt
- [ ] No overlapping text/shapes (check slide images)
- [ ] Charts reference real data (not placeholder values)
- [ ] Dark title slide + light content slides (sandwich structure)
- [ ] No accent underlines beneath titles
- [ ] Slide count matches brief
- [ ] File opens without repair in PowerPoint

---

## Common Mistakes to Avoid

- Hardcoding pixel positions without accounting for slide dimensions (use percentages or proportion of 10" × 7.5")
- Forgetting `await` on `writeFile()`
- Using accent lines under titles (AI hallmark — never do this)
- Equal visual weight to all colors (one must dominate)
- Text-only slides with bullet lists

---

## Dependencies

```bash
npm install -g pptxgenjs
pip install markitdown --break-system-packages
# LibreOffice + Poppler: pre-configured in sandbox
```
