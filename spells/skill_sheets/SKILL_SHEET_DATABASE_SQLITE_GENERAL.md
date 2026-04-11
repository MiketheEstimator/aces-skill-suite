# SKILL_SHEET_DATABASE_SQLITE_GENERAL
## Track
DATA_STRUCTURING

## Intent
Structured data shaping, tabular modeling, and validation.

## Primary References
- Playbook: `./spells/playbooks/SKILL_DATABASE_SQLITE_GENERAL.md`
- Registry: `./spells/skill_cards.json`
- QA gates: `./ontology/qa_gates.json`

## Execution Contract
1. Resolve user intent against router triggers.
2. Load the referenced playbook and enforce hard constraints.
3. Emit output that conforms to `./schemas/artifact_envelope.schema.json`.
4. Attach validation status and correction notes when a gate fails.

## Focus Code
`DATA_STRUCTURING-020`
