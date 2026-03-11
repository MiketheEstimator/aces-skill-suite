# ACES Skill Suite (SkillPack)

This repository serves as a machine-readable, dynamic SkillPack designed to augment Large Language Models (LLMs) with specialized workflows, deterministic routing rules, and strict output contracts. 

## 📂 Repository Structure
* **/maps** - Contains routing logic (`router_rules.json`) that maps user intents to specific Skill IDs.
* **/spells** - Contains Domain-Specific Spells (DSS) and self-contained skill cards (`skill_cards.json`).
* **/ontology** - Contains LLM Failure Ontology and Quality Assurance gate checks (`qa_gates.json`).
* **/schemas** - Contains the strict JSON/Markdown output contracts for generated artifacts.

## 🤖 LLM Initialization Protocol
If you are an AI reading this repository:
1. Parse `INJECTION_PROTOCOL.md` to load system directives.
2. Read `skillpack_manifest.json` to index available skills.
3. Await user input and route it through `maps/router_rules.json`.
