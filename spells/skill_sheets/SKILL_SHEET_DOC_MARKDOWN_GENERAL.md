# SKILL_SHEET_DOC_MARKDOWN_GENERAL
## Track
KNOWLEDGE_STATE

## Intent
Session state, ontology, and knowledge graph operations.

## Primary References
- Playbook: `./spells/playbooks/SKILL_DOC_MARKDOWN_GENERAL.md`
- Registry: `./spells/skill_cards.json`
- QA gates: `./ontology/qa_gates.json`

## Execution Contract
1. Resolve user intent against router triggers.
2. Load the referenced playbook and enforce hard constraints.
3. Emit output that conforms to `./schemas/artifact_envelope.schema.json`.
4. Attach validation status and correction notes when a gate fails.

## Focus Code
`KNOWLEDGE_STATE-024`
