---
name: native-artifact
description: "Use this skill when producing any native Claude artifact — rendered output directly in the chat interface. Covers React components, HTML pages, SVG, Mermaid diagrams, plain Markdown, and code blocks. Trigger when the user wants something rendered, previewed, or interacted with inside Claude without downloading a file."
---

# Native Artifact / Output SKILL

## Quick Reference

| Output Type | Format | Trigger |
|-------------|--------|---------|
| UI component | `.jsx` | "make a component", "build a widget" |
| Web page | `.html` | "create a page", "render HTML" |
| Diagram | `.mermaid` | "flowchart", "sequence diagram" |
| Vector graphic | `.svg` | "icon", "logo", "illustration" |
| Document | `.md` | "write a doc", "draft content" |
| Code block | language tag | "write a script", "show me code" |

---

## Supported Artifact Types

### React (`.jsx`)
- Full component with hooks, state, interactivity
- Use Tailwind core utility classes only (no compiler)
- Available libraries: `lucide-react`, `recharts`, `d3`, `three`, `mathjs`, `lodash`, `shadcn/ui`
- Default export required; no required props (or provide defaults)
- **Never use** `localStorage`, `sessionStorage`, or browser storage APIs

### HTML (`.html`)
- Single file: inline all CSS and JS — no separate files
- External scripts via `https://cdnjs.cloudflare.com` only
- No `<form>` tags — use `onClick`/`onChange` handlers

### Mermaid (`.mermaid`)
- Flowcharts, sequence diagrams, Gantt, class diagrams, ER diagrams
- Keep node labels short; avoid special characters in labels

### SVG (`.svg`)
- Fully self-contained vector output
- Define `viewBox`; use named colors or hex values
- Group related elements with `<g>` tags

### Markdown (`.md`)
- Use for standalone written content >4 paragraphs
- Headers, tables, code blocks, blockquotes all supported

---

## Design Standards (React / HTML)

- **Never produce generic AI aesthetics** — no plain white cards with gray text
- Pick a deliberate color palette; establish visual hierarchy
- Use spacing, contrast, and typography intentionally
- Read `/mnt/skills/public/frontend-design/SKILL.md` for full design guidance on any UI artifact

---

## QA Checklist

- [ ] Component renders without errors
- [ ] No missing imports
- [ ] No `localStorage` / browser storage calls
- [ ] All props have defaults
- [ ] Interactive elements respond correctly
- [ ] No external URLs that may be unavailable
- [ ] Mobile/narrow viewport doesn't break layout
- [ ] Contrast ratio sufficient for readability

---

## Common Mistakes to Avoid

- Using libraries not on the approved list
- Importing CSS files separately (must be inline)
- Using `<form>` submit — always use button `onClick`
- Assuming Tailwind JIT classes work (only core utility classes)
- Forgetting `default export` on React components
- Using `THREE.CapsuleGeometry` (only available in r142+; use `CylinderGeometry` instead)

---

## Dependencies

None — all rendering is native to the Claude interface.
