# SKILL_SHEET_CONFIG_YAML_VALIDATE
## Track
AEC_BIM_COORD

## Intent
BIM/AEC coordination, model exchange, and clash workflows.

## Primary References
- Playbook: `./spells/playbooks/SKILL_CONFIG_YAML_VALIDATE.md`
- Registry: `./spells/skill_cards.json`
- QA gates: `./ontology/qa_gates.json`

## Execution Contract
1. Resolve user intent against router triggers.
2. Load the referenced playbook and enforce hard constraints.
3. Emit output that conforms to `./schemas/artifact_envelope.schema.json`.
4. Attach validation status and correction notes when a gate fails.

## Focus Code
`AEC_BIM_COORD-015`
