#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel_path: str):
    path = ROOT / rel_path
    with path.open() as f:
        return json.load(f)


def check_path(path_str: str, label: str, errors: list[str]):
    path = ROOT / path_str
    if not path.exists():
        errors.append(f"{label} missing path: {path_str}")


def main() -> int:
    errors: list[str] = []

    manifest = load_json("skillpack_manifest.json")
    router = load_json("maps/router_rules.json")
    skills = load_json("spells/skill_cards.json")
    qa = load_json("ontology/qa_gates.json")

    for key, rel_path in manifest.get("manifest_index", {}).items():
        check_path(rel_path, f"manifest_index.{key}", errors)

    skill_ids = {item["skill_id"] for item in skills.get("skills", [])}
    qa_ids = set(qa.get("qa_checks", {}).keys())

    for idx, item in enumerate(skills.get("skills", []), start=1):
        check_path(item.get("playbook_ref", ""), f"skills[{idx}].playbook_ref", errors)
        qa_gate_id = item.get("qa_gate_id")
        if qa_gate_id not in qa_ids:
            errors.append(f"skills[{idx}] unknown qa_gate_id: {qa_gate_id}")

    for idx, route in enumerate(router.get("routing_table", []), start=1):
        check_path(route.get("playbook_ref", ""), f"routing_table[{idx}].playbook_ref", errors)
        for skill_id in route.get("target_skill_ids", []):
            if skill_id not in skill_ids:
                errors.append(f"routing_table[{idx}] unknown target_skill_id: {skill_id}")

    required_schemas = [
        "schemas/docx.schema.json",
        "schemas/pdf.schema.json",
        "schemas/xlsx.schema.json",
        "schemas/json.schema.json",
    ]
    for rel_path in required_schemas:
        check_path(rel_path, "schema", errors)

    if errors:
        print("Referential integrity check failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Referential integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
