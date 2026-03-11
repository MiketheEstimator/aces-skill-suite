---
name: SKILL_DOC_MARKDOWN_GENERAL
description: "Universal handler for repo-ready, version-controlled markdown creation and editing. Use when producing .md files for documentation, READMEs, wikis, changelogs, ADRs, runbooks, or any markdown-first content pipeline. Triggers: 'markdown', '.md file', 'README', 'docs', 'wiki page', 'changelog', 'runbook', 'write documentation'."
---

# SKILL_DOC_MARKDOWN_GENERAL — Markdown Document Skill

## Quick Reference

| Task | Section |
|------|---------|
| Document type patterns | [Document Type Patterns](#document-type-patterns) |
| Syntax & formatting rules | [Syntax Rules](#syntax-rules) |
| Linting & validation | [Linting & Validation](#linting--validation) |
| Frontmatter (YAML) | [Frontmatter](#frontmatter) |
| Repo structure conventions | [Repo Conventions](#repo-conventions) |
| QA loop | [Validation & QA](#validation--qa) |

---

## Document Type Patterns

### README.md

```markdown
# Project Name

> One-line description of what this does.

## Overview

Brief explanation — what it is, who it's for, why it exists.

## Requirements

- Requirement A
- Requirement B

## Installation

```bash
pip install package-name
```

## Usage

```python
import package_name
package_name.do_thing()
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_VAR` | `value` | What it controls |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
```

### CHANGELOG.md (Keep a Changelog format)

```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

## [1.2.0] — 2024-03-15

### Added
- Feature X that does Y

### Changed
- Behaviour of Z now does W

### Fixed
- Bug where A caused B

### Removed
- Deprecated method `old_function()`

## [1.1.0] — 2024-01-10
...

[Unreleased]: https://github.com/org/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/org/repo/compare/v1.1.0...v1.2.0
```

### Architecture Decision Record (ADR)

```markdown
# ADR-0001: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX]

## Context

What situation or problem prompted this decision?

## Decision

What was decided, and what is the approach?

## Consequences

### Positive
- Outcome A

### Negative
- Trade-off B

### Neutral
- Implication C

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Option A | Reason |
| Option B | Reason |
```

### Runbook / Operational Doc

```markdown
# Runbook: [Process Name]

**Owner:** Team/Person
**Last reviewed:** YYYY-MM-DD
**Severity:** P1 | P2 | P3

## Purpose

What this runbook covers.

## Prerequisites

- [ ] Access to X
- [ ] Tool Y installed

## Procedure

### Step 1: Name

```bash
command --flag value
```

Expected output:
```
output here
```

### Step 2: Name

...

## Rollback

Steps to undo if something goes wrong.

## Escalation

If this fails, contact: @person or #slack-channel
```

---

## Syntax Rules

### Headings

```markdown
# H1 — document title only (one per file)
## H2 — major sections
### H3 — subsections
#### H4 — use sparingly
```

- Never skip heading levels (H1 → H3 without H2)
- One blank line before and after every heading
- No trailing punctuation on headings

### Lists

```markdown
# Unordered
- Item A
- Item B
  - Nested (2 spaces indent)

# Ordered
1. First
2. Second
3. Third

# Task list
- [x] Done
- [ ] Not done
```

### Code

````markdown
# Inline
Use `backticks` for inline code, filenames, variables.

# Fenced block — always specify language
```python
def hello():
    return "world"
```

```bash
echo "shell command"
```

```json
{"key": "value"}
```
````

### Tables

```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Left     | Left     | Left     |

# Alignment
| Left | Centre | Right |
|:-----|:------:|------:|
| a    |   b    |     c |
```

### Links & Images

```markdown
# Absolute
[Link text](https://example.com)

# Relative (repo-safe)
[See docs](./docs/guide.md)
[Parent](../README.md)

# Image
![Alt text](./images/screenshot.png)

# Reference-style (preferred for repeated links)
See [the docs][docs-link].

[docs-link]: https://example.com/docs
```

### Emphasis

```markdown
**Bold** — for UI labels, key terms (use sparingly)
*Italic* — for titles, light emphasis
`Code` — for anything technically literal
~~Strikethrough~~ — for deprecated items
> Blockquote — for callouts, warnings, notes
```

### Callout Blocks (GitHub-flavoured)

```markdown
> [!NOTE]
> Informational context.

> [!WARNING]
> Something that could cause problems.

> [!IMPORTANT]
> Must-read before proceeding.

> [!TIP]
> Optional helpful suggestion.
```

---

## Frontmatter

YAML frontmatter for static site generators, documentation platforms:

```markdown
---
title: "Document Title"
description: "One-line summary for SEO and search."
date: 2024-03-15
updated: 2024-06-01
author: "Name"
tags: [tag1, tag2, tag3]
status: draft | review | published
version: "1.0.0"
---
```

Frontmatter rules:
- Must be first thing in file (before any content)
- Delimited by `---` on both sides
- Strings with colons or special characters must be quoted
- Dates: always `YYYY-MM-DD` format

---

## Linting & Validation

### Install markdownlint

```bash
# CLI
npm install -g markdownlint-cli

# Lint a file
markdownlint README.md

# Lint all .md files in project
markdownlint "**/*.md"

# Auto-fix where possible
markdownlint --fix "**/*.md"
```

### `.markdownlint.json` Config (recommended defaults)

```json
{
  "default": true,
  "MD013": false,
  "MD033": false,
  "MD041": true,
  "MD024": { "siblings_only": true }
}
```

Key rules:
- `MD013` — line length (disable for prose-heavy docs)
- `MD033` — no inline HTML (disable if HTML callouts needed)
- `MD041` — first line must be H1
- `MD024` — no duplicate headings (siblings_only allows same name in different sections)

### Python-based Lint

```bash
pip install pymarkdownlnt

pymarkdown scan README.md
pymarkdown scan --recurse ./docs/
```

### Link Validation

```bash
# Check for broken links
npm install -g markdown-link-check

markdown-link-check README.md
markdown-link-check --config .mlc-config.json "**/*.md"
```

`.mlc-config.json`:
```json
{
  "ignorePatterns": [
    { "pattern": "^https://localhost" }
  ],
  "timeout": "10s",
  "retryOn429": true
}
```

---

## Repo Conventions

### Standard File Locations

```
repo-root/
├── README.md              # Project overview (required)
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guide
├── LICENSE                # Licence text (no .md extension)
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── api-reference.md
│   └── adr/
│       ├── 0001-initial-architecture.md
│       └── 0002-database-choice.md
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

### Naming Conventions

```
# Files
README.md          — uppercase, standard
CHANGELOG.md       — uppercase, standard
getting-started.md — lowercase-kebab for all other docs
api-reference.md
adr-0001-title.md

# Headings → anchors (GitHub auto-generates)
## My Heading     → #my-heading
## API Reference  → #api-reference
## C++ Support    → #c-support  (special chars stripped)
```

---

## Validation & QA

```bash
# Full QA pipeline
markdownlint --fix "**/*.md"          # fix style issues
markdown-link-check README.md        # check links
pymarkdown scan --recurse ./docs/    # deep structural lint

# Render preview (if mkdocs)
mkdocs serve

# Render preview (if docusaurus)
npm run start
```

### QA Checklist

- [ ] Single H1 per file
- [ ] No skipped heading levels
- [ ] All code blocks have language specifier
- [ ] No broken relative links
- [ ] Frontmatter present and valid (if required by platform)
- [ ] No trailing whitespace on lines
- [ ] File ends with single newline
- [ ] Tables are aligned and render correctly
- [ ] All images have alt text

### QA Loop

1. Write document
2. Run `markdownlint --fix` — auto-fix style
3. Run `markdown-link-check` — fix broken links
4. Render in target platform (GitHub preview, mkdocs, etc.)
5. Visual check — headings, tables, code blocks render correctly
6. **Do not commit until zero lint errors**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Table doesn't render | Missing header separator row | Add `|---|---|` row after headers |
| Code block not highlighted | Missing language specifier | Add language after opening ` ``` ` |
| Relative link broken | Wrong path from file location | Use `./` prefix; verify from file's directory |
| Heading not generating anchor | Special characters in heading | GitHub strips non-alphanumeric; test the anchor manually |
| Frontmatter not parsed | Not first in file / wrong delimiter | Move to top; use `---` not `===` |
| List not rendering | Missing blank line before list | Add blank line before first list item |

---

## Dependencies

```bash
npm install -g markdownlint-cli      # linting
npm install -g markdown-link-check   # link validation
pip install pymarkdownlnt            # Python-based lint
pip install mkdocs mkdocs-material   # local rendering (optional)
```
