# SKILL_SHEET_DATABASE_PARQUET_OPTIMIZE
## Track
DOC_AUTHORING

## Intent
Authoring, parsing, and publishing document outputs.

## Primary References
- Playbook: `./spells/playbooks/SKILL_DATABASE_PARQUET_OPTIMIZE.md`
- Registry: `./spells/skill_cards.json`
- QA gates: `./ontology/qa_gates.json`

## Execution Contract
1. Resolve user intent against router triggers.
2. Load the referenced playbook and enforce hard constraints.
3. Emit output that conforms to `./schemas/artifact_envelope.schema.json`.
4. Attach validation status and correction notes when a gate fails.

## Focus Code
`DOC_AUTHORING-019`
