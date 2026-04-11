# ACES Skill Suite (SkillPack)

This repository serves as a machine-readable, dynamic SkillPack designed to augment Large Language Models (LLMs) with specialized workflows, deterministic routing rules, and strict output contracts.

## 📂 Repository Structure
* **/maps** - Routing logic (`router_rules.json`) that maps user intents to specific Skill IDs.
* **/spells** - Domain-Specific Spells (DSS), skill cards (`skill_cards.json`), and referential skill sheets (`skill_sheets/index.json`).
* **/ontology** - LLM Failure Ontology and Quality Assurance gate checks (`qa_gates.json`).
* **/schemas** - Strict JSON contracts for generated artifacts.
* **/scripts** - Validation and maintenance utilities for CI and deployment.
* **/external/google_drive** - Deterministic staging area for normalized external data imports.

## 🤖 LLM Initialization Protocol
If you are an AI reading this repository:
1. Parse `INJECTION_PROTOCOL.md` to load system directives.
2. Read `skillpack_manifest.json` to index available skills.
3. Route user intent through `maps/router_rules.json`.
4. Optionally load referential sheets from `spells/skill_sheets/index.json` to increase task-specific precision.

## ✅ Validation (required before deployment)
Run:

```bash
python scripts/validate_skillpack.py
```

This performs cross-file integrity checks for:
- manifest index paths,
- router playbook references,
- `target_skill_ids` alignment with registered skills,
- skill playbook references,
- QA gate references,
- condensed referential skill sheets (24) and their referenced playbooks/files,
- external Google Drive staging paths (`external/google_drive`).

## 📚 Referential Skill Sheets
The repository now includes a condensed set of 24 distinct skill sheets (subject-based names like `SKILL_SHEET_DOC_MARKDOWN_GENERAL` and `SKILL_SHEET_CODE_PYTHON_GENERAL`) under `spells/skill_sheets/` with an index at `spells/skill_sheets/index.json`.

These sheets are lightweight execution overlays for repeatable, auditable outcomes and can be retrieved by ID/focus code during orchestration.

## ☁️ External Data Integration (Google Drive)
Use a sync-first, normalize-second workflow:
1. Sync Google Drive assets into `external/google_drive/` using your approved org workflow.
2. Register normalized metadata in `external/google_drive/catalog.json`.
3. Reference normalized local entries from playbooks/skill sheets (avoid direct remote URLs in core routing files).

This keeps builds deterministic, auditable, and reproducible.
