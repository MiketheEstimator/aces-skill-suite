---
name: optimized-css-js-asset
description: "Use this skill when producing standalone .css or .js files intended as production assets — minified, linted, and optimized. Covers CSS architecture, JS bundling, minification, source maps, and asset optimization. Trigger when producing CSS/JS files for use outside of an HTML artifact."
---

# Optimized CSS / JS Asset SKILL

## Quick Reference

| Task | Tool |
|------|------|
| CSS minify | `csscompressor` (Python) or `cleancss` (Node) |
| JS minify | `terser` (Node) |
| CSS lint | `stylelint` |
| JS lint | `eslint` |
| Bundle JS | `esbuild` |
| Source map | `terser --source-map` |

---

## CSS Architecture

### File Header Convention

```css
/*!
 * Component: Card Layout
 * Version:   1.0.0
 * Author:    Generated
 * Date:      2024-03-15
 */
```

### BEM Naming Convention

```css
/* Block */
.card { }

/* Element */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier */
.card--featured { }
.card--compact { }
.card__header--dark { }
```

### CSS Custom Properties (Variables)

```css
:root {
    /* Colors */
    --color-primary:    #1E2761;
    --color-accent:     #F96167;
    --color-text:       #2d2d2d;
    --color-muted:      #8892A4;
    --color-bg:         #F5F7FA;
    --color-surface:    #FFFFFF;
    --color-border:     #E0E4EC;

    /* Typography */
    --font-sans:        'Segoe UI', Arial, sans-serif;
    --font-mono:        'Consolas', 'Courier New', monospace;
    --text-base:        1rem;
    --text-sm:          0.875rem;
    --text-lg:          1.125rem;
    --leading-normal:   1.6;

    /* Spacing scale */
    --space-1:  0.25rem;
    --space-2:  0.5rem;
    --space-4:  1rem;
    --space-6:  1.5rem;
    --space-8:  2rem;
    --space-12: 3rem;

    /* Shadows */
    --shadow-sm:  0 1px 3px rgba(0,0,0,0.08);
    --shadow-md:  0 4px 12px rgba(0,0,0,0.10);
    --shadow-lg:  0 8px 24px rgba(0,0,0,0.12);

    /* Border radius */
    --radius-sm:  4px;
    --radius-md:  8px;
    --radius-lg:  16px;
    --radius-full: 9999px;
}
```

### Responsive Breakpoints

```css
/* Mobile-first */
/* Base: < 640px */
@media (min-width: 640px)  { /* sm  */ }
@media (min-width: 768px)  { /* md  */ }
@media (min-width: 1024px) { /* lg  */ }
@media (min-width: 1280px) { /* xl  */ }
```

---

## JavaScript Asset Structure

```javascript
/*!
 * Module: DataFormatter
 * Version: 1.0.0
 */
(function(global) {
    'use strict';

    const DataFormatter = {
        // Public API
        formatCurrency(value, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency
            }).format(value);
        },

        formatDate(dateStr, locale = 'en-GB') {
            return new Date(dateStr).toLocaleDateString(locale, {
                year: 'numeric', month: 'short', day: 'numeric'
            });
        }
    };

    // Export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = DataFormatter;   // CommonJS
    } else {
        global.DataFormatter = DataFormatter;  // Browser global
    }

}(typeof globalThis !== 'undefined' ? globalThis : this));
```

---

## Minification

### CSS Minification (Python)

```python
# pip install csscompressor --break-system-packages
import csscompressor

with open("styles.css", "r") as f:
    css = f.read()

minified = csscompressor.compress(css)

with open("styles.min.css", "w") as f:
    f.write(minified)

print(f"Original: {len(css):,} bytes")
print(f"Minified: {len(minified):,} bytes")
print(f"Savings:  {(1 - len(minified)/len(css))*100:.1f}%")
```

### JS Minification (Node / Terser)

```bash
# Install terser
npm install -g terser

# Minify with source map
terser input.js \
  --compress \
  --mangle \
  --source-map "filename='output.min.js.map'" \
  --output output.min.js

# Verify output
wc -c input.js output.min.js
```

### esbuild (Bundle + Minify)

```bash
npm install -g esbuild

# Bundle and minify
esbuild src/main.js \
  --bundle \
  --minify \
  --sourcemap \
  --outfile=dist/bundle.min.js
```

---

## Linting

```bash
# CSS lint
npm install -g stylelint stylelint-config-standard
echo '{"extends":["stylelint-config-standard"]}' > .stylelintrc.json
stylelint "**/*.css"

# JS lint
npm install -g eslint
eslint --init
eslint output.js

# Python-based CSS analysis
pip install tinycss2 --break-system-packages
python -c "
import tinycss2
with open('styles.css') as f:
    rules, _ = tinycss2.parse_stylesheet_bytes(f.read().encode())
print(f'Rules parsed: {len(rules)}')
"
```

---

## CLI Verification

```bash
# CSS: check syntax
python -c "
import tinycss2
with open('styles.css', 'rb') as f:
    rules, errors = tinycss2.parse_stylesheet_bytes(f.read())
if errors:
    for e in errors: print('Error:', e)
else:
    print('CSS syntax OK ✓')
"

# JS: basic syntax check
node --check output.js && echo "JS syntax OK ✓"

# File sizes
ls -lh *.css *.js *.min.css *.min.js 2>/dev/null

# Gzip estimates
gzip -c styles.css | wc -c
gzip -c styles.min.css | wc -c
```

---

## QA Checklist

- [ ] No syntax errors (lint passes clean)
- [ ] CSS custom properties used consistently (no hardcoded color values scattered)
- [ ] Minified file produced alongside readable source
- [ ] Source map generated for minified JS
- [ ] No `!important` overuse in CSS
- [ ] No `console.log` or debug statements in production JS
- [ ] No `var` — use `const`/`let` (ES6+)
- [ ] Gzip size acceptable (CSS <30KB, JS <100KB for typical components)
- [ ] Responsive breakpoints cover mobile/tablet/desktop

---

## Common Mistakes to Avoid

- Hardcoding pixel values without CSS custom properties
- `!important` to override specificity (fix the specificity issue instead)
- Inline styles in JS (use CSS classes)
- Not declaring `'use strict'` in non-module JS files
- Missing fallback fonts in `font-family`
- Forgetting to update source files before minifying

---

## Dependencies

```bash
pip install csscompressor --break-system-packages
pip install tinycss2 --break-system-packages
npm install -g terser esbuild stylelint eslint
```
