# SKILL_SHEET_DIAGRAM_PLANTUML_AUTOGEN
## Track
CODE_AUTOMATION

## Intent
Code generation, scripting, and packaging automation.

## Primary References
- Playbook: `./spells/playbooks/SKILL_DIAGRAM_PLANTUML_AUTOGEN.md`
- Registry: `./spells/skill_cards.json`
- QA gates: `./ontology/qa_gates.json`

## Execution Contract
1. Resolve user intent against router triggers.
2. Load the referenced playbook and enforce hard constraints.
3. Emit output that conforms to `./schemas/artifact_envelope.schema.json`.
4. Attach validation status and correction notes when a gate fails.

## Focus Code
`CODE_AUTOMATION-022`
