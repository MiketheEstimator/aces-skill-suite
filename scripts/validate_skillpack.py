#!/usr/bin/env python3
"""Validate ACES SkillPack referential integrity for CI and local checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_path_exists(label: str, relative_path: str, errors: list[str]) -> None:
    path = (ROOT / relative_path).resolve()
    if not path.exists():
        errors.append(f"{label}: missing path '{relative_path}'")


def validate_manifest(errors: list[str]) -> dict:
    manifest_path = ROOT / "skillpack_manifest.json"
    manifest = load_json(manifest_path)

    required_keys = [
        "router",
        "skills_registry",
        "playbooks_dir",
        "skill_sheets_index",
        "qa_gates",
        "schemas",
    ]
    index = manifest.get("manifest_index", {})
    for key in required_keys:
        if key not in index:
            errors.append(f"manifest_index: missing key '{key}'")
            continue
        check_path_exists(f"manifest_index.{key}", index[key], errors)

    external_data = manifest.get("external_data", {})
    for key in ["google_drive_sync_dir", "normalized_catalog"]:
        if key not in external_data:
            errors.append(f"external_data: missing key '{key}'")
            continue
        check_path_exists(f"external_data.{key}", external_data[key], errors)

    return manifest


def validate_router(errors: list[str], known_skills: set[str]) -> None:
    router = load_json(ROOT / "maps/router_rules.json")
    for i, node in enumerate(router.get("routing_table", []), start=1):
        playbook_ref = node.get("playbook_ref")
        if playbook_ref:
            check_path_exists(f"routing_table[{i}].playbook_ref", playbook_ref, errors)

        for skill_id in node.get("target_skill_ids", []):
            if skill_id not in known_skills:
                errors.append(
                    f"routing_table[{i}].target_skill_ids: unknown skill_id '{skill_id}'"
                )


def validate_skills(errors: list[str], qa_gate_ids: set[str]) -> set[str]:
    skills = load_json(ROOT / "spells/skill_cards.json").get("skills", [])
    known_skills: set[str] = set()

    for i, skill in enumerate(skills, start=1):
        skill_id = skill.get("skill_id")
        if not skill_id:
            errors.append(f"skills[{i}]: missing skill_id")
            continue
        if skill_id in known_skills:
            errors.append(f"skills[{i}]: duplicate skill_id '{skill_id}'")
        known_skills.add(skill_id)

        playbook_ref = skill.get("playbook_ref")
        if not playbook_ref:
            errors.append(f"skills[{i}] ({skill_id}): missing playbook_ref")
        else:
            check_path_exists(f"skills[{i}] ({skill_id}).playbook_ref", playbook_ref, errors)

        qa_gate_id = skill.get("qa_gate_id")
        if qa_gate_id is not None and qa_gate_id not in qa_gate_ids:
            errors.append(
                f"skills[{i}] ({skill_id}).qa_gate_id: unknown QA gate '{qa_gate_id}'"
            )

    return known_skills


def validate_skill_sheets(errors: list[str], known_skills: set[str]) -> None:
    index = load_json(ROOT / "spells/skill_sheets/index.json")
    sheets = index.get("skill_sheets", [])
    seen_ids: set[str] = set()
    seen_focus_codes: set[str] = set()

    if len(sheets) < 24:
        errors.append(f"skill_sheets: expected at least 24 entries, found {len(sheets)}")

    for i, sheet in enumerate(sheets, start=1):
        sheet_id = sheet.get("sheet_id")
        if not sheet_id:
            errors.append(f"skill_sheets[{i}]: missing sheet_id")
            continue
        if sheet_id in seen_ids:
            errors.append(f"skill_sheets[{i}]: duplicate sheet_id '{sheet_id}'")
        seen_ids.add(sheet_id)

        focus_code = sheet.get("focus_code")
        if not focus_code:
            errors.append(f"skill_sheets[{i}] ({sheet_id}): missing focus_code")
        elif focus_code in seen_focus_codes:
            errors.append(f"skill_sheets[{i}] ({sheet_id}): duplicate focus_code '{focus_code}'")
        seen_focus_codes.add(focus_code)

        for key in ["sheet_ref", "primary_playbook_ref"]:
            ref = sheet.get(key)
            if not ref:
                errors.append(f"skill_sheets[{i}] ({sheet_id}): missing {key}")
                continue
            check_path_exists(f"skill_sheets[{i}] ({sheet_id}).{key}", ref, errors)

        sheet_ref = sheet.get("sheet_ref")
        filename = Path(sheet_ref).name if sheet_ref else ""
        if filename.startswith("SKILL_SHEET_") and filename[12:15].isdigit():
            errors.append(
                f"skill_sheets[{i}] ({sheet_id}).sheet_ref: numeric-list filenames are not allowed ('{filename}')"
            )

        # Optional link if provided in future
        linked_skill_id = sheet.get("linked_skill_id")
        if linked_skill_id and linked_skill_id not in known_skills:
            errors.append(
                f"skill_sheets[{i}] ({sheet_id}).linked_skill_id: unknown skill '{linked_skill_id}'"
            )


def get_qa_gate_ids() -> set[str]:
    qa = load_json(ROOT / "ontology/qa_gates.json")
    return set(qa.get("qa_checks", {}).keys())


def main() -> int:
    errors: list[str] = []

    validate_manifest(errors)
    qa_gate_ids = get_qa_gate_ids()
    known_skills = validate_skills(errors, qa_gate_ids)
    validate_router(errors, known_skills)
    validate_skill_sheets(errors, known_skills)

    if errors:
        print("SkillPack validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("SkillPack validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
