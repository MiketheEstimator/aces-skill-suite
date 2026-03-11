---
name: SKILL_LLM_SESSION_STATE
description: "Design and maintain structured register state across multi-turn LLM sessions. Use when building deterministic, auditable LLM workflows that must track constraints, contradictions, authority hierarchies, missing dependencies, and change propagation across many turns. Applies to contract auditing, document analysis, agentic pipelines, and any session where state drift or qualifier loss would produce wrong outputs. Triggers: 'session state', 'register', 'constraint tracking', 'multi-turn LLM', 'stateful prompt', 'auditable LLM', 'constraint register', 'change propagation', 'rehydration'."
---

# SKILL_LLM_SESSION_STATE — LLM Session State Management

> **Scope:** This skill covers the *architecture* of structured state in LLM sessions —
> how to design registers, serialize them, detect conflicts, propagate changes, and
> rehydrate state before synthesis outputs. It is format-agnostic and domain-agnostic,
> with AEC construction audit used as the primary worked example throughout.
> For document corpus preparation see `SKILL_AEC_DOCUMENT_CORPUS`.
> For scope extraction and tagging see `SKILL_AEC_SCOPE_EXTRACTION`.

## Quick Reference

| Task | Section |
|------|---------|
| Why sessions drift and how to prevent it | [The Drift Problem](#the-drift-problem) |
| Register architecture — what to track | [Register Architecture](#register-architecture) |
| State serialization formats | [State Serialization](#state-serialization) |
| Rehydration — injecting state before synthesis | [Rehydration Protocol](#rehydration-protocol) |
| Conflict detection — new input vs locked state | [Conflict Detection](#conflict-detection) |
| Change propagation — cascading register updates | [Change Propagation](#change-propagation) |
| Phase / workflow gate design | [Phase Gate Design](#phase-gate-design) |
| Evidence status tagging | [Evidence Status Tagging](#evidence-status-tagging) |
| Prompt patterns for register-aware outputs | [Prompt Patterns](#prompt-patterns) |
| Python implementation | [Python Implementation](#python-implementation) |
| Testing stateful sessions | [Testing Stateful Sessions](#testing-stateful-sessions) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## The Drift Problem

LLMs have no persistent memory between turns. In a multi-turn session, each new response
is generated from the visible context window only. Without explicit state management,
sessions accumulate four failure modes:

| Failure Mode | Description | Consequence |
|---|---|---|
| **Constraint dropout** | A constraint established in turn 3 is not present in the context by turn 15 | Output violates a rule the system "agreed to" earlier |
| **Qualifier compression** | A compressed summary omits a cost-additive modifier | Scope items become under-specified or mis-priced |
| **Contradiction flattening** | A conflict between two sources is silently resolved in favour of whichever was mentioned most recently | Wrong governing truth used downstream |
| **Propagation failure** | A correction in one register does not update dependent outputs | Deliverables are internally inconsistent |

The solution is **explicit serialized state** — registers written into the context at
every turn, structured so the model can read, update, and reason from them reliably.

---

## Register Architecture

A **register** is a named, structured state container that persists across turns.
Design registers around the question: *what decision would break if this were forgotten?*

### Core Register Set

```yaml
# Minimum viable register set for a document-analysis session

registers:
  constraint_register:       # What is forbidden, capped, required, or sequenced
  authority_hierarchy:       # Document precedence order (which source wins conflicts)
  contradiction_register:    # Cross-source conflicts, unresolved
  missing_source_register:   # Referenced but absent governing documents
  supersedence_index:        # What has been overruled and by what
  friction_log:              # Decision-critical ambiguities awaiting resolution
  open_risk_register:        # Live risks not yet mitigated or assigned
  operator_override_register: # Human-injected directives with no document source
  traceability_ledger:       # Source → claim mappings for every asserted fact
```

### Register Design Principles

**1. Append-only by default**
Never delete a register entry — only supersede it.
A superseded entry stays in the register with a `status: superseded` tag and a pointer
to the superseding entry. This preserves the audit trail.

**2. Each entry carries its own evidence status**
An entry without an evidence status is an untagged assumption.
Every register entry must declare one of:

```
VERIFIED               — explicitly stated in a primary source
AMBIGUOUS              — present but unclear; classification pending
CONTRADICTORY          — conflicts with another source
SUPERSEDED             — overruled by a higher-authority source
OPERATOR_DIRECTIVE     — injected by human with no document source
UNDEFINED              — referenced but not defined in available corpus
MISSING_UPSTREAM       — depends on a source not in the corpus
INFERRED               — plausible from context; not explicitly stated
```

**3. Register entries are typed**
Do not mix constraint types in one flat list.
A constraint is not the same as a contradiction, which is not the same as a missing
dependency. Mixing them produces ambiguous state during conflict detection.

**4. Registers are scoped to a session**
A session = one project, one document corpus, one authority hierarchy.
If the project changes, the session resets. Multi-project contamination invalidates the
entire state.

---

## State Serialization

### JSON Format (machine-readable, recommended for pipelines)

```json
{
  "session_id": "PROJ-2401-AUDIT-001",
  "project_id": "2401",
  "session_turn": 7,
  "locked": true,
  "registers": {

    "constraint_register": [
      {
        "id": "CON-001",
        "type": "negative",
        "description": "No work permitted in occupied zones before 7am or after 6pm",
        "source": "Spec Section 01 10 00, Para 1.4.B",
        "evidence_status": "VERIFIED",
        "affects": ["scheduling", "trade_scope", "staffing"],
        "active": true,
        "turn_discovered": 2
      },
      {
        "id": "CON-002",
        "type": "material",
        "description": "No substitutions permitted on structural steel: ASTM A992 only",
        "source": "Spec Section 05 12 00, Para 2.1.A",
        "evidence_status": "VERIFIED",
        "affects": ["steel_scope", "procurement", "cost"],
        "active": true,
        "turn_discovered": 2
      }
    ],

    "authority_hierarchy": {
      "locked": true,
      "turn_locked": 3,
      "order": [
        {"rank": 1, "type": "Addenda",       "note": "Supersedes all below"},
        {"rank": 2, "type": "RFI/ASI",       "note": "Governs over specs and drawings"},
        {"rank": 3, "type": "Bid Forms",     "note": "Quantity and scope binding"},
        {"rank": 4, "type": "Specifications","note": "Quality and method governing"},
        {"rank": 5, "type": "Drawings",      "note": "Dimensional and spatial governing"},
        {"rank": 6, "type": "Narratives",    "note": "Contextual only; not binding"}
      ]
    },

    "contradiction_register": [
      {
        "id": "CONTRA-001",
        "system": "Structural slab thickness — Grid B/3 area",
        "source_a": "Drawing S2.1: 6-inch slab",
        "source_b": "Spec Section 03 30 00, Schedule: 8-inch slab",
        "authority_resolves": false,
        "evidence_status": "CONTRADICTORY",
        "impact": "decision_critical",
        "affects": ["concrete_scope", "cost", "schedule"],
        "resolution": null,
        "turn_discovered": 4
      }
    ],

    "missing_source_register": [
      {
        "id": "MISS-001",
        "description": "Geotechnical Report referenced in Spec Section 31 00 00",
        "severity": "fatal",
        "blocks": ["earthwork_scope", "foundation_scope", "dewatering_scope"],
        "evidence_status": "MISSING_UPSTREAM",
        "turn_discovered": 2
      }
    ],

    "friction_log": [
      {
        "id": "FRIC-001",
        "conflict_type": "scope_ownership",
        "description": "Demolition of existing MEP in renovation zone assigned to GC in narrative, to MEP sub in spec",
        "source_a": "Project Narrative p.4",
        "source_b": "Spec Section 02 41 00, Para 3.2",
        "affected_deliverable": "Trade Scope Matrix",
        "verdict": "HALT — authority hierarchy does not resolve; requires owner adjudication",
        "resolution": null,
        "turn_discovered": 5
      }
    ],

    "open_risk_register": [
      {
        "id": "RISK-001",
        "description": "Dewatering scope undefined pending absent geotechnical report",
        "severity": "high",
        "linked_missing_source": "MISS-001",
        "mitigation": null,
        "evidence_status": "MISSING_UPSTREAM"
      }
    ],

    "operator_override_register": [],

    "supersedence_index": [],

    "traceability_ledger": []
  }
}
```

### YAML Format (human-readable, recommended for prompts)

```yaml
session_id: PROJ-2401-AUDIT-001
project_id: "2401"
session_turn: 7
locked: true

# ── AUTHORITY HIERARCHY (LOCKED turn 3) ──────────────────────────────────────
authority_hierarchy:
  - rank: 1  type: Addenda
  - rank: 2  type: RFI/ASI
  - rank: 3  type: Bid Forms
  - rank: 4  type: Specifications
  - rank: 5  type: Drawings
  - rank: 6  type: Narratives

# ── ACTIVE CONSTRAINTS ────────────────────────────────────────────────────────
constraints:
  - id: CON-001  status: ACTIVE  evidence: VERIFIED
    rule: "No work before 07:00 or after 18:00 in occupied zones"
    source: "Spec 01 10 00 §1.4.B"
    affects: [scheduling, staffing, trade_scope]

  - id: CON-002  status: ACTIVE  evidence: VERIFIED
    rule: "No substitutions on structural steel — ASTM A992 only"
    source: "Spec 05 12 00 §2.1.A"
    affects: [steel_scope, procurement, cost]

# ── OPEN CONTRADICTIONS ───────────────────────────────────────────────────────
contradictions:
  - id: CONTRA-001  status: UNRESOLVED  impact: decision_critical
    system: "Slab thickness Grid B/3"
    conflict: "S2.1 = 6in vs Spec 03 30 00 Schedule = 8in"
    blocks: [concrete_scope, cost]

# ── MISSING SOURCES ───────────────────────────────────────────────────────────
missing_sources:
  - id: MISS-001  severity: fatal
    description: "Geotechnical Report (ref: Spec 31 00 00)"
    blocks: [earthwork, foundation, dewatering]

# ── OPEN FRICTION ─────────────────────────────────────────────────────────────
friction:
  - id: FRIC-001  status: HALTED
    issue: "MEP demolition ownership — GC vs MEP sub conflict"
    blocks: [trade_scope_matrix]
```

### Minimal Inline Format (for context window economy)

When context is tight, serialize state as a compact header block:

```
=== SESSION STATE [Turn 7 | Project 2401] ===
HIERARCHY LOCKED: Addenda > RFI > BidForms > Specs > Drawings > Narratives
ACTIVE CONSTRAINTS: CON-001 (no work <07:00/>18:00 occupied), CON-002 (no steel sub ASTM A992)
OPEN CONTRADICTIONS: CONTRA-001 (slab thickness B/3 — DECISION CRITICAL — UNRESOLVED)
MISSING SOURCES: MISS-001 (Geotech Report — FATAL — blocks earthwork/foundation/dewatering)
OPEN FRICTION: FRIC-001 (MEP demo ownership — HALTED)
OPERATOR OVERRIDES: none
=== END STATE ===
```

---

## Rehydration Protocol

**Rehydration** = injecting the current register state into the prompt immediately before
any synthesis, extraction, or deliverable output.

Without rehydration, the model synthesizes from the visible conversation only —
which may not include constraints or contradictions established in earlier turns.

### When to Rehydrate

| Output Type | Rehydrate? |
|---|---|
| Simple factual question | No |
| Extracting scope from a single document | Constraint register only |
| Drafting a narrative, proposal, or personnel section | Full register set |
| Generating an RFI log | Friction log + missing source register |
| Emitting a final deliverable | **Full register set — mandatory** |
| Running an adversarial audit | **Full register set — mandatory** |

### Rehydration Prompt Template

```
Before generating the output below, load and apply the active session state.

=== ACTIVE SESSION STATE ===
{state_yaml_or_json}
=== END SESSION STATE ===

REHYDRATION CHECKLIST (verify before emitting):
□ All ACTIVE constraints reflected in output
□ No UNRESOLVED contradictions silently resolved
□ All MISSING sources noted where they affect scope
□ No HALTED friction items treated as resolved
□ OPERATOR DIRECTIVES tagged separately from document-sourced content
□ Evidence status declared on all material claims

Now generate: {task_description}
```

### Python Rehydration Helper

```python
import json
from pathlib import Path

class SessionState:
    """Manages LLM session register state across turns."""

    def __init__(self, session_id: str, project_id: str):
        self.session_id  = session_id
        self.project_id  = project_id
        self.turn        = 0
        self.registers   = {
            "constraint_register":       [],
            "authority_hierarchy":       {"locked": False, "order": []},
            "contradiction_register":    [],
            "missing_source_register":   [],
            "friction_log":              [],
            "open_risk_register":        [],
            "operator_override_register": [],
            "supersedence_index":        [],
            "traceability_ledger":       [],
        }

    def add_constraint(self, id: str, rule: str, source: str,
                       evidence: str, affects: list,
                       constraint_type: str = "negative") -> None:
        self.registers["constraint_register"].append({
            "id":             id,
            "type":           constraint_type,
            "description":    rule,
            "source":         source,
            "evidence_status": evidence,
            "affects":        affects,
            "active":         True,
            "turn_discovered": self.turn
        })

    def add_contradiction(self, id: str, system: str,
                          source_a: str, source_b: str,
                          impact: str, affects: list) -> None:
        self.registers["contradiction_register"].append({
            "id":               id,
            "system":           system,
            "source_a":         source_a,
            "source_b":         source_b,
            "authority_resolves": False,
            "evidence_status":  "CONTRADICTORY",
            "impact":           impact,
            "affects":          affects,
            "resolution":       None,
            "turn_discovered":  self.turn
        })

    def add_missing_source(self, id: str, description: str,
                            severity: str, blocks: list) -> None:
        self.registers["missing_source_register"].append({
            "id":              id,
            "description":     description,
            "severity":        severity,
            "blocks":          blocks,
            "evidence_status": "MISSING_UPSTREAM",
            "turn_discovered": self.turn
        })

    def lock_hierarchy(self, ordered_types: list[str]) -> None:
        self.registers["authority_hierarchy"] = {
            "locked":      True,
            "turn_locked": self.turn,
            "order":       [{"rank": i+1, "type": t}
                            for i, t in enumerate(ordered_types)]
        }

    def add_friction(self, id: str, conflict_type: str,
                     description: str, source_a: str, source_b: str,
                     affected_deliverable: str) -> None:
        self.registers["friction_log"].append({
            "id":                   id,
            "conflict_type":        conflict_type,
            "description":          description,
            "source_a":             source_a,
            "source_b":             source_b,
            "affected_deliverable": affected_deliverable,
            "verdict":              "HALTED — awaiting resolution",
            "resolution":           None,
            "turn_discovered":      self.turn
        })

    def resolve_friction(self, friction_id: str,
                          resolution: str, resolved_by: str) -> None:
        for item in self.registers["friction_log"]:
            if item["id"] == friction_id:
                item["resolution"]  = resolution
                item["resolved_by"] = resolved_by
                item["verdict"]     = "RESOLVED"
                item["turn_resolved"] = self.turn
                return
        raise KeyError(f"Friction item {friction_id} not found")

    def add_operator_override(self, id: str, directive: str,
                               affects: list) -> None:
        self.registers["operator_override_register"].append({
            "id":        id,
            "directive": directive,
            "affects":   affects,
            "tag":       "[OPERATOR DIRECTIVE; NO DOCUMENT SOURCE FOUND]",
            "turn":      self.turn
        })

    def supersede(self, target_id: str, superseded_by_id: str,
                   superseding_source: str, note: str = "") -> None:
        """Mark a register entry as superseded and log the supersedence."""
        self.registers["supersedence_index"].append({
            "target_id":          target_id,
            "superseded_by_id":   superseded_by_id,
            "superseding_source": superseding_source,
            "note":               note,
            "turn":               self.turn
        })
        # Mark the original entry in its register
        for reg_name, reg in self.registers.items():
            if isinstance(reg, list):
                for entry in reg:
                    if entry.get("id") == target_id:
                        entry["active"]      = False
                        entry["status"]      = "SUPERSEDED"
                        entry["superseded_by"] = superseded_by_id

    def to_yaml_header(self) -> str:
        """Emit compact YAML state header for prompt injection."""
        lines = [
            f"=== SESSION STATE [Turn {self.turn} | Project {self.project_id}] ===",
        ]

        # Hierarchy
        if self.registers["authority_hierarchy"]["locked"]:
            order = " > ".join(
                e["type"] for e in self.registers["authority_hierarchy"]["order"]
            )
            lines.append(f"HIERARCHY (LOCKED): {order}")
        else:
            lines.append("HIERARCHY: NOT YET LOCKED")

        # Active constraints
        active = [c for c in self.registers["constraint_register"] if c.get("active")]
        if active:
            lines.append("ACTIVE CONSTRAINTS:")
            for c in active:
                lines.append(f"  {c['id']} [{c['evidence_status']}]: {c['description']} | src: {c['source']}")

        # Unresolved contradictions
        unresolved = [c for c in self.registers["contradiction_register"]
                      if c.get("resolution") is None]
        if unresolved:
            lines.append("OPEN CONTRADICTIONS:")
            for c in unresolved:
                lines.append(f"  {c['id']} [{c['impact'].upper()}]: {c['system']} | {c['source_a']} vs {c['source_b']}")

        # Missing sources
        missing = self.registers["missing_source_register"]
        if missing:
            lines.append("MISSING SOURCES:")
            for m in missing:
                lines.append(f"  {m['id']} [{m['severity'].upper()}]: {m['description']} | blocks: {', '.join(m['blocks'])}")

        # Open friction
        open_friction = [f for f in self.registers["friction_log"]
                         if f.get("resolution") is None]
        if open_friction:
            lines.append("OPEN FRICTION (HALTED):")
            for f in open_friction:
                lines.append(f"  {f['id']}: {f['description']} | blocks: {f['affected_deliverable']}")

        # Operator overrides
        overrides = self.registers["operator_override_register"]
        if overrides:
            lines.append("OPERATOR OVERRIDES:")
            for o in overrides:
                lines.append(f"  {o['id']}: {o['directive']}")

        lines.append("=== END STATE ===")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            "session_id":  self.session_id,
            "project_id":  self.project_id,
            "session_turn": self.turn,
            "registers":   self.registers
        }, indent=2)

    def save(self, path: str) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")
        print(f"State saved: {path} (turn {self.turn})")

    @classmethod
    def load(cls, path: str) -> "SessionState":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        s = cls(data["session_id"], data["project_id"])
        s.turn      = data["session_turn"]
        s.registers = data["registers"]
        return s

    def advance_turn(self) -> None:
        self.turn += 1
```

---

## Conflict Detection

New input must always be tested against locked register state before being accepted.

### Conflict Types

| Type | Description | Action |
|---|---|---|
| **Constraint violation** | New input contradicts an active constraint | Halt; issue friction item |
| **Hierarchy challenge** | New source claims authority over a locked hierarchy | Test against supersedence rules; update or reject |
| **Contradiction injection** | New source conflicts with an existing verified claim | Add contradiction record; do not silently resolve |
| **Scope ownership conflict** | New input assigns work already assigned to another party | Halt; issue friction item |
| **Identifier mutation** | New input changes a locked project/sheet/spec identifier | Flag as potential contamination or drift |

### Conflict Detection Logic

```python
from dataclasses import dataclass
from typing import Optional

EVIDENCE_PRIORITY = {
    "VERIFIED":         5,
    "OPERATOR_DIRECTIVE": 4,
    "INFERRED":         2,
    "AMBIGUOUS":        1,
    "UNDEFINED":        0,
}

@dataclass
class ConflictResult:
    has_conflict:    bool
    conflict_type:   Optional[str]
    existing_entry:  Optional[dict]
    new_input:       Optional[str]
    verdict:         str
    action_required: str


def check_new_input_against_constraints(
        state: SessionState,
        new_input_text: str,
        new_input_source: str) -> list[ConflictResult]:
    """
    Check whether new input text conflicts with any active constraint.
    Returns a list of ConflictResult for any conflicts found.

    In production: replace keyword matching with an LLM call that receives
    the constraint register + new input and returns conflict analysis.
    """
    conflicts = []
    new_lower = new_input_text.lower()

    for constraint in state.registers["constraint_register"]:
        if not constraint.get("active"):
            continue

        # Keyword-based trigger (replace with LLM semantic check in production)
        keywords = constraint["description"].lower().split()
        trigger_words = [w for w in keywords if len(w) > 4]
        if any(word in new_lower for word in trigger_words):
            conflicts.append(ConflictResult(
                has_conflict    = True,
                conflict_type   = "potential_constraint_violation",
                existing_entry  = constraint,
                new_input       = new_input_text,
                verdict         = f"New input may violate {constraint['id']}: {constraint['description']}",
                action_required = "Review against constraint before accepting"
            ))

    return conflicts


def test_source_against_hierarchy(
        state: SessionState,
        new_source_type: str,
        existing_claim_source_type: str) -> dict:
    """
    Determine whether a new source outranks an existing claim's source.
    Returns governance decision.
    """
    hierarchy = state.registers["authority_hierarchy"]
    if not hierarchy.get("locked"):
        return {"governs": None, "reason": "Hierarchy not yet locked"}

    order = {e["type"]: e["rank"] for e in hierarchy["order"]}
    new_rank      = order.get(new_source_type)
    existing_rank = order.get(existing_claim_source_type)

    if new_rank is None:
        return {"governs": False, "reason": f"Source type '{new_source_type}' not in hierarchy"}
    if existing_rank is None:
        return {"governs": True,  "reason": f"Existing source type '{existing_claim_source_type}' not in hierarchy"}

    if new_rank < existing_rank:
        return {"governs": True,  "reason": f"{new_source_type} (rank {new_rank}) outranks {existing_claim_source_type} (rank {existing_rank})"}
    elif new_rank > existing_rank:
        return {"governs": False, "reason": f"{new_source_type} (rank {new_rank}) subordinate to {existing_claim_source_type} (rank {existing_rank})"}
    else:
        return {"governs": None,  "reason": "Same rank — contradiction; cannot auto-resolve"}
```

---

## Change Propagation

When a register entry is updated (resolved, superseded, or corrected), dependent
outputs must be flagged for revision.

### Propagation Map

Define which registers affect which output types:

```python
PROPAGATION_MAP = {
    "constraint_register": [
        "trade_scope_narratives",
        "schedule_logic",
        "staffing_section",
        "final_proposal",
        "rfi_log",
    ],
    "contradiction_register": [
        "scope_baseline",
        "trade_scope_narratives",
        "rfi_log",
        "final_proposal",
    ],
    "missing_source_register": [
        "scope_baseline",
        "open_risk_register",
        "rfi_log",
        "final_proposal",
    ],
    "authority_hierarchy": [
        # Hierarchy change cascades everywhere
        "all_outputs"
    ],
    "friction_log": [
        "trade_scope_narratives",
        "scope_baseline",
        "final_proposal",
    ],
    "operator_override_register": [
        "all_outputs"   # operator content must be tagged in every output
    ],
}


def propagate_change(state: SessionState,
                     changed_register: str,
                     changed_entry_id: str,
                     change_description: str) -> list[str]:
    """
    When a register entry changes, return list of outputs that need revision.
    Log the propagation event.
    """
    affected_outputs = PROPAGATION_MAP.get(changed_register, [])
    if "all_outputs" in affected_outputs:
        affected_outputs = ["ALL OUTPUTS"]

    propagation_record = {
        "turn":               state.turn,
        "changed_register":   changed_register,
        "changed_entry_id":   changed_entry_id,
        "change_description": change_description,
        "outputs_requiring_revision": affected_outputs,
    }

    # Log in supersedence index as a change event
    state.registers["supersedence_index"].append(propagation_record)

    print(f"[PROPAGATION] {changed_entry_id} change in {changed_register}")
    print(f"  Outputs requiring revision: {', '.join(affected_outputs)}")
    return affected_outputs
```

---

## Phase Gate Design

A **phase gate** is a checkpoint that must pass before the session advances to the
next workflow stage. Gates enforce the principle that synthesis cannot proceed
on a poisoned or incomplete state.

### Gate Conditions

```python
from enum import Enum

class GateStatus(Enum):
    PASS    = "PASS"
    WARN    = "WARN"     # Recoverable — log and continue
    HALT    = "HALT"     # Decision-critical — stop and resolve


@dataclass
class GateResult:
    status:   GateStatus
    phase:    str
    failures: list[str]
    warnings: list[str]
    verdict:  str


def gate_phase_3_extraction(state: SessionState) -> GateResult:
    """
    Gate check before Phase 3 (Deep Extraction).
    Requires: hierarchy locked, no fatal missing sources,
              no unresolved decision-critical friction.
    """
    failures = []
    warnings = []

    # Hierarchy must be locked
    if not state.registers["authority_hierarchy"].get("locked"):
        failures.append("Authority hierarchy not locked — Phase 2 must complete first")

    # Fatal missing sources block extraction
    fatal_missing = [
        m for m in state.registers["missing_source_register"]
        if m["severity"] == "fatal"
    ]
    if fatal_missing:
        failures.append(
            f"Fatal missing sources present: {[m['id'] for m in fatal_missing]} — "
            "cannot extract with confidence"
        )

    # Decision-critical unresolved friction halts
    dc_friction = [
        f for f in state.registers["friction_log"]
        if f.get("resolution") is None
    ]
    if dc_friction:
        failures.append(
            f"Unresolved decision-critical friction: {[f['id'] for f in dc_friction]}"
        )

    # High-risk missing sources are warnings, not halts
    high_missing = [
        m for m in state.registers["missing_source_register"]
        if m["severity"] == "high"
    ]
    if high_missing:
        warnings.append(
            f"High-risk missing sources: {[m['id'] for m in high_missing]} — "
            "extraction proceeding with reduced confidence"
        )

    status = (GateStatus.HALT if failures
              else GateStatus.WARN if warnings
              else GateStatus.PASS)

    return GateResult(
        status   = status,
        phase    = "PHASE_3_EXTRACTION",
        failures = failures,
        warnings = warnings,
        verdict  = (
            "HALT — resolve failures before extraction"  if status == GateStatus.HALT
            else "WARN — proceed with noted limitations" if status == GateStatus.WARN
            else "PASS — proceed to extraction"
        )
    )


def gate_phase_5_synthesis(state: SessionState) -> GateResult:
    """
    Gate check before Phase 5 (Strategic Synthesis / deliverable drafting).
    Stricter than Phase 3 — synthesis outputs go to clients.
    """
    failures = []
    warnings = []

    # Hierarchy must be locked
    if not state.registers["authority_hierarchy"].get("locked"):
        failures.append("Authority hierarchy not locked")

    # Any unresolved decision-critical contradiction blocks synthesis
    dc_contradictions = [
        c for c in state.registers["contradiction_register"]
        if c.get("impact") == "decision_critical" and c.get("resolution") is None
    ]
    if dc_contradictions:
        failures.append(
            f"Unresolved decision-critical contradictions: "
            f"{[c['id'] for c in dc_contradictions]}"
        )

    # Any open friction blocks synthesis
    open_friction = [
        f for f in state.registers["friction_log"]
        if f.get("resolution") is None
    ]
    if open_friction:
        failures.append(
            f"Open friction items: {[f['id'] for f in open_friction]}"
        )

    # Operator overrides must be tagged in output — warn if present
    if state.registers["operator_override_register"]:
        warnings.append(
            f"{len(state.registers['operator_override_register'])} operator override(s) "
            "present — must be tagged [OPERATOR DIRECTIVE] in all outputs"
        )

    status = (GateStatus.HALT if failures
              else GateStatus.WARN if warnings
              else GateStatus.PASS)

    return GateResult(
        status   = status,
        phase    = "PHASE_5_SYNTHESIS",
        failures = failures,
        warnings = warnings,
        verdict  = (
            "HALT — resolve failures before drafting deliverables" if status == GateStatus.HALT
            else "WARN — proceed; operator tags required"          if status == GateStatus.WARN
            else "PASS — proceed to synthesis"
        )
    )
```

---

## Evidence Status Tagging

All material claims in LLM outputs must carry an evidence status tag.
This is the mechanism that prevents synthesis from presenting inferences as facts.

### Tag Reference

| Tag | Meaning | When to Use |
|---|---|---|
| `[VERIFIED]` | Explicitly stated in a primary source present in the corpus | Direct quote or unambiguous extract from a governing document |
| `[AMBIGUOUS]` | Present in source but unclear in scope, quantity, or applicability | Conflicting units, vague language, unclear boundaries |
| `[CONTRADICTORY]` | Conflicts with another source in the corpus | Same system described differently across two sources |
| `[SUPERSEDED]` | Overruled by a higher-authority source | Earlier spec clause overruled by addendum |
| `[OPERATOR DIRECTIVE]` | Injected by human with no document source | Instructions that have no backing in the document corpus |
| `[UNDEFINED]` | Referenced but not defined anywhere in the corpus | A spec section number cited but not provided |
| `[MISSING UPSTREAM]` | Depends on a source not present in the corpus | Scope that can't be determined without an absent document |
| `[INFERRED]` | Plausible from context; not explicitly stated | Industry-standard practice applied where spec is silent |

### Tagging in Prompts

Instruct the model explicitly:

```
When drafting scope items or making claims about project requirements:
- Tag each claim with its evidence status in brackets
- [VERIFIED] = directly supported by a source in the corpus
- [INFERRED] = your best interpretation, not explicit in source
- [CONTRADICTORY] = conflicts exist across sources
- [MISSING UPSTREAM] = depends on a source not provided
- Never present an [INFERRED] claim as if it were [VERIFIED]
- Never silently resolve a [CONTRADICTORY] item
```

### Example Tagged Output

```
SCOPE ITEM: Structural Steel Frame, Grid Lines A–D / 1–5

- Supply and install W-shape steel columns, ASTM A992, per Drawing S3.1  [VERIFIED]
- Hot-dip galvanize all exterior columns per Spec 05 12 00 §2.3.C  [VERIFIED]
- No substitutions permitted on steel grade  [VERIFIED — CON-002]
- Column base plate dimensions per Drawing S3.1 Detail 4/S3.1  [VERIFIED]
- Anchor rod embedment depth: 18 inches per drawing note  [VERIFIED]
- Grout type at base plates: non-shrink, per Spec 03 60 00 §2.1  [VERIFIED]
- Fireproofing thickness: [CONTRADICTORY — CONTRA-001: Drawing shows 1.5" SFRM;
  Spec 07 81 00 Schedule shows 2" SFRM — awaiting authority resolution]
- Erection sequence relative to concrete core: [MISSING UPSTREAM —
  sequence specification not provided; MISS-002 registered]
```

---

## Prompt Patterns

### Pattern 1: State-Primed Extraction

Use this when extracting scope, constraints, or claims from a new document:

```
[SESSION STATE]
{state.to_yaml_header()}
[END STATE]

TASK: Extract scope items from the following specification section.

EXTRACTION RULES:
1. Every extracted item must cite its source (section, paragraph, clause)
2. Tag each item with evidence status: [VERIFIED], [AMBIGUOUS], or [INFERRED]
3. Preserve all cost-additive qualifiers exactly as written
4. Flag any item that conflicts with an ACTIVE CONSTRAINT in the state above
5. Flag any item that contradicts an existing OPEN CONTRADICTION
6. Do not convert existing-condition references into new work requirements

SOURCE:
{spec_section_text}
```

### Pattern 2: State-Primed Synthesis

Use this when drafting a deliverable:

```
[SESSION STATE]
{state.to_yaml_header()}
[END STATE]

REHYDRATION CHECK — before drafting, confirm:
□ All ACTIVE CONSTRAINTS reflected
□ All OPEN CONTRADICTIONS noted where they affect scope
□ All MISSING UPSTREAM items noted where they create uncertainty
□ All OPERATOR DIRECTIVE content tagged separately
□ No HALTED friction items treated as resolved

TASK: Draft the structural trade scope narrative for inclusion in the bid proposal.

SYNTHESIS RULES:
1. Map every scope statement to a source
2. Preserve no-substitution clauses, galvanization, loading class, and coating requirements
3. Do not describe [MISSING UPSTREAM] scope as if it is known
4. Tag any operator-directed additions as [OPERATOR DIRECTIVE]
5. Note all open items that require RFI before pricing
```

### Pattern 3: Adversarial Audit

Use this to red-team a previously generated output:

```
[SESSION STATE]
{state.to_yaml_header()}
[END STATE]

TASK: Adversarial audit of the following draft output.

AUDIT CHECKLIST:
□ Identifier drift — do any sheet IDs, spec sections, or product names differ from source?
□ Qualifier loss — were any no-substitution, galvanization, or coating requirements dropped?
□ Constraint dropout — do all ACTIVE CONSTRAINTS appear where relevant?
□ Contradiction flattening — were any OPEN CONTRADICTIONS silently resolved?
□ Operator tag loss — are all OPERATOR DIRECTIVE items still tagged?
□ Silent inference — are any [INFERRED] claims presented without a tag?
□ Propagation failure — does this output reflect the current state (turn {state.turn})?

DRAFT TO AUDIT:
{draft_text}

Return: structured audit report with finding ID, location in draft, violation type, and required correction.
```

### Pattern 4: Conflict Resolution Intake

Use this when the user provides a resolution to a halted friction item:

```
[SESSION STATE]
{state.to_yaml_header()}
[END STATE]

The following friction item has been resolved by the project owner:

Friction ID: {friction_id}
Resolution: {resolution_text}
Resolved by: {authority_name}
Source of resolution: {source_document}

REQUIRED ACTIONS:
1. Update friction log: mark {friction_id} as RESOLVED
2. Determine if resolution changes any ACTIVE CONSTRAINT
3. Determine which outputs are now unblocked
4. Issue propagation notice: list all outputs that must be revised
5. If resolution introduces a new constraint, add it to the constraint register

Process this resolution and emit: updated state summary + propagation notice.
```

---

## Python Implementation

### Full Session Lifecycle Example

```python
from pathlib import Path

# ── Initialize session ────────────────────────────────────────────────────────
state = SessionState(
    session_id = "PROJ-2401-AUDIT-001",
    project_id = "2401"
)

# ── Phase 1: Ingest constraints ───────────────────────────────────────────────
state.advance_turn()   # Turn 1

state.add_constraint(
    id       = "CON-001",
    rule     = "No work before 07:00 or after 18:00 in occupied zones",
    source   = "Spec 01 10 00 §1.4.B",
    evidence = "VERIFIED",
    affects  = ["scheduling", "staffing", "trade_scope"],
    constraint_type = "negative"
)
state.add_constraint(
    id       = "CON-002",
    rule     = "No substitutions — structural steel ASTM A992 only",
    source   = "Spec 05 12 00 §2.1.A",
    evidence = "VERIFIED",
    affects  = ["steel_scope", "procurement", "cost"],
    constraint_type = "material"
)
state.add_missing_source(
    id          = "MISS-001",
    description = "Geotechnical Report referenced in Spec 31 00 00",
    severity    = "fatal",
    blocks      = ["earthwork", "foundation", "dewatering"]
)

# ── Phase 2: Lock hierarchy ───────────────────────────────────────────────────
state.advance_turn()   # Turn 2

state.lock_hierarchy([
    "Addenda", "RFI/ASI", "Bid Forms",
    "Specifications", "Drawings", "Narratives"
])

# ── Phase 3: Gate check before extraction ────────────────────────────────────
state.advance_turn()   # Turn 3

gate = gate_phase_3_extraction(state)
print(f"Phase 3 Gate: {gate.verdict}")
if gate.status == GateStatus.HALT:
    for f in gate.failures:
        print(f"  HALT: {f}")
    # In production: surface to user; do not proceed

# ── Phase 3: Contradiction discovered during extraction ───────────────────────
state.add_contradiction(
    id       = "CONTRA-001",
    system   = "Slab thickness — Grid B/3",
    source_a = "Drawing S2.1: 6-inch slab",
    source_b = "Spec 03 30 00 Schedule: 8-inch slab",
    impact   = "decision_critical",
    affects  = ["concrete_scope", "cost", "schedule"]
)
state.add_friction(
    id                  = "FRIC-001",
    conflict_type       = "scope_ownership",
    description         = "MEP demolition: GC (narrative p.4) vs MEP sub (Spec 02 41 00 §3.2)",
    source_a            = "Project Narrative p.4",
    source_b            = "Spec 02 41 00 §3.2",
    affected_deliverable = "Trade Scope Matrix"
)

# ── Save state to disk ────────────────────────────────────────────────────────
state.save("session_state_turn3.json")

# ── Rehydrate into prompt ─────────────────────────────────────────────────────
print(state.to_yaml_header())

# ── Later: resolve friction and propagate ────────────────────────────────────
state.advance_turn()   # Turn 8

state.resolve_friction(
    friction_id  = "FRIC-001",
    resolution   = "MEP demolition assigned to MEP sub per Addendum 2, §4.1",
    resolved_by  = "Addendum 2"
)
affected = propagate_change(
    state              = state,
    changed_register   = "friction_log",
    changed_entry_id   = "FRIC-001",
    change_description = "MEP demo ownership resolved — MEP sub confirmed"
)
state.save("session_state_turn8.json")

# ── Gate check before synthesis ──────────────────────────────────────────────
gate5 = gate_phase_5_synthesis(state)
print(f"Phase 5 Gate: {gate5.verdict}")
```

### Build Rehydration Prompt

```python
def build_rehydration_prompt(state: SessionState,
                              task_description: str,
                              source_text: str = "",
                              mode: str = "extraction") -> str:
    """
    Build a complete rehydration-primed prompt.
    mode: 'extraction' | 'synthesis' | 'audit'
    """
    mode_rules = {
        "extraction": (
            "Tag each item: [VERIFIED], [AMBIGUOUS], [INFERRED], or [CONTRADICTORY]\n"
            "Cite source for every claim.\n"
            "Flag conflicts with ACTIVE CONSTRAINTS.\n"
            "Do not convert existing-condition references to new work.\n"
            "Preserve all qualifiers exactly as written."
        ),
        "synthesis": (
            "Map every scope statement to a source.\n"
            "Preserve no-substitution, galvanization, coating, and sequence qualifiers.\n"
            "Do not describe MISSING UPSTREAM scope as if known.\n"
            "Tag operator-directed content [OPERATOR DIRECTIVE].\n"
            "Note all open items requiring RFI before pricing."
        ),
        "audit": (
            "Check: identifier drift, qualifier loss, constraint dropout,\n"
            "contradiction flattening, operator tag loss, silent inference,\n"
            "propagation failure.\n"
            "Return structured findings: ID | location | violation | correction."
        )
    }

    source_block = (
        f"\nSOURCE MATERIAL:\n{source_text}\n" if source_text else ""
    )

    return (
        f"{state.to_yaml_header()}\n\n"
        f"TASK: {task_description}\n\n"
        f"RULES FOR THIS OUTPUT:\n"
        f"{mode_rules.get(mode, mode_rules['extraction'])}\n"
        f"{source_block}\n"
        f"NOW EXECUTE TASK:"
    )
```

---

## Testing Stateful Sessions

### Unit Tests for Register Logic

```python
import pytest

def test_constraint_persists_across_turns():
    state = SessionState("TEST-001", "PROJ-X")
    state.add_constraint("CON-T1", "No night work", "Spec §1.1",
                         "VERIFIED", ["scheduling"])
    state.advance_turn()
    state.advance_turn()
    active = [c for c in state.registers["constraint_register"] if c["active"]]
    assert len(active) == 1
    assert active[0]["id"] == "CON-T1"


def test_supersede_marks_entry_inactive():
    state = SessionState("TEST-002", "PROJ-X")
    state.add_constraint("CON-S1", "Use Type A waterproofing",
                         "Spec §07 10 00", "VERIFIED", ["waterproofing"])
    state.supersede("CON-S1", "CON-S2", "Addendum 1 §3.2",
                    "Type A replaced by Type B in Addendum 1")
    original = next(c for c in state.registers["constraint_register"]
                    if c["id"] == "CON-S1")
    assert original["active"] == False
    assert original["status"] == "SUPERSEDED"


def test_phase3_gate_halts_on_locked_fatal_missing():
    state = SessionState("TEST-003", "PROJ-X")
    state.lock_hierarchy(["Addenda", "Specs", "Drawings"])
    state.add_missing_source("MISS-T1", "Geotech Report",
                              "fatal", ["earthwork"])
    result = gate_phase_3_extraction(state)
    assert result.status == GateStatus.HALT


def test_phase3_gate_passes_with_no_blockers():
    state = SessionState("TEST-004", "PROJ-X")
    state.lock_hierarchy(["Addenda", "Specs", "Drawings"])
    result = gate_phase_3_extraction(state)
    assert result.status == GateStatus.PASS


def test_friction_resolution_updates_status():
    state = SessionState("TEST-005", "PROJ-X")
    state.add_friction("FRIC-T1", "scope_ownership",
                       "Demo ownership conflict",
                       "Narrative", "Spec §02 41", "Trade Scope")
    state.resolve_friction("FRIC-T1", "MEP sub confirmed by Addendum 2", "Addendum 2")
    item = next(f for f in state.registers["friction_log"] if f["id"] == "FRIC-T1")
    assert item["verdict"] == "RESOLVED"
    assert item["resolution"] is not None


def test_yaml_header_includes_active_constraints():
    state = SessionState("TEST-006", "PROJ-X")
    state.lock_hierarchy(["Addenda", "Specs"])
    state.add_constraint("CON-H1", "No open flame within 10ft of fuel storage",
                         "Safety Plan §4.1", "VERIFIED", ["hot_work"])
    header = state.to_yaml_header()
    assert "CON-H1" in header
    assert "No open flame" in header


def test_save_and_load_round_trip():
    state = SessionState("TEST-007", "PROJ-X")
    state.lock_hierarchy(["Addenda", "Specs", "Drawings"])
    state.add_constraint("CON-R1", "Firewatch required after hot work",
                         "Safety Plan §4.2", "VERIFIED", ["hot_work"])
    state.save("/tmp/test_state.json")

    loaded = SessionState.load("/tmp/test_state.json")
    assert loaded.session_id == "TEST-007"
    constraints = loaded.registers["constraint_register"]
    assert any(c["id"] == "CON-R1" for c in constraints)
```

---

## Validation & QA

### State Health Check

```python
def validate_state_health(state: SessionState) -> dict:
    """
    Run integrity checks on all session registers.
    Returns dict with pass/fail per check and overall verdict.
    """
    checks = {}

    # 1. All constraint entries have evidence status
    constraints = state.registers["constraint_register"]
    missing_evidence = [c["id"] for c in constraints
                        if not c.get("evidence_status")]
    checks["constraint_evidence_tags"] = {
        "pass": len(missing_evidence) == 0,
        "detail": f"Missing evidence tags: {missing_evidence}" if missing_evidence else "OK"
    }

    # 2. All contradiction entries have impact classification
    contradictions = state.registers["contradiction_register"]
    missing_impact = [c["id"] for c in contradictions if not c.get("impact")]
    checks["contradiction_impact_tags"] = {
        "pass": len(missing_impact) == 0,
        "detail": f"Missing impact tags: {missing_impact}" if missing_impact else "OK"
    }

    # 3. Hierarchy is locked (required by Phase 3+)
    checks["hierarchy_locked"] = {
        "pass": state.registers["authority_hierarchy"].get("locked", False),
        "detail": "Locked" if state.registers["authority_hierarchy"].get("locked") else "NOT LOCKED"
    }

    # 4. No orphaned traceability ledger entries
    # (every claim should map to a known source)
    ledger = state.registers["traceability_ledger"]
    orphaned = [e for e in ledger if not e.get("source")]
    checks["traceability_no_orphans"] = {
        "pass": len(orphaned) == 0,
        "detail": f"{len(orphaned)} orphaned entries" if orphaned else "OK"
    }

    # 5. All friction items have an impact classification
    friction = state.registers["friction_log"]
    missing_conflict_type = [f["id"] for f in friction if not f.get("conflict_type")]
    checks["friction_typed"] = {
        "pass": len(missing_conflict_type) == 0,
        "detail": f"Untyped: {missing_conflict_type}" if missing_conflict_type else "OK"
    }

    all_pass = all(v["pass"] for v in checks.values())
    print(f"State Health: {'PASS' if all_pass else 'FAIL'} (Turn {state.turn})")
    for check_name, result in checks.items():
        status = "✓" if result["pass"] else "✗"
        print(f"  {status} {check_name}: {result['detail']}")

    return {"overall": "PASS" if all_pass else "FAIL", "checks": checks}
```

### QA Checklist

- [ ] Session ID and project ID set before any register writes
- [ ] Authority hierarchy locked before Phase 3 extraction
- [ ] Every constraint entry has: `id`, `description`, `source`, `evidence_status`, `affects`, `active`
- [ ] Every contradiction entry has: `id`, `system`, `source_a`, `source_b`, `impact`, `resolution`
- [ ] Every missing source entry has: `id`, `description`, `severity`, `blocks`
- [ ] No entry has been deleted — only superseded with pointer
- [ ] State serialized to disk after every phase advance
- [ ] Rehydration header injected before every synthesis or extraction prompt
- [ ] All open friction items resolved before Phase 5 gate
- [ ] Propagation map applied after every friction resolution or constraint supersedence
- [ ] Adversarial audit run before final deliverable emission
- [ ] `validate_state_health()` passes before Phase 7

### QA Loop

1. Initialize `SessionState` — set IDs, clear registers
2. Ingest Phase 1 — add constraints, missing sources; save state
3. Lock hierarchy in Phase 2 — verify `authority_hierarchy.locked == True`
4. Run `gate_phase_3_extraction()` — resolve any HALT conditions
5. Extract — add contradictions and friction as discovered; save state each turn
6. Run `gate_phase_5_synthesis()` — resolve all open friction before proceeding
7. Synthesize with `build_rehydration_prompt()` — inject full state header
8. Run adversarial audit — use Pattern 3 prompt with current state
9. Run `validate_state_health()` — zero failures required before Phase 7
10. Emit final deliverable — confirm state turn matches expected turn count

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| Constraint appears in turn 3, gone by turn 12 | State not serialized and injected into later turns | Save state after every phase; always inject `to_yaml_header()` at prompt start |
| Model resolves a contradiction silently | No explicit instruction to tag contradictions | Add `[CONTRADICTORY]` tagging rule to every extraction prompt |
| Qualifier dropped in synthesis | Compression during summarization | Use qualifier preservation rule in synthesis prompt; run adversarial audit |
| Operator directive appears as document fact | Override not tagged | Add `[OPERATOR DIRECTIVE; NO DOCUMENT SOURCE FOUND]` instruction to synthesis rules |
| Hierarchy challenged by a late-added source | New source not tested against hierarchy | Run `test_source_against_hierarchy()` before accepting any new source claim |
| State grows too large for context window | Too many register entries accumulated | Use compact inline format `to_yaml_header()` instead of full JSON; or summarize resolved items |
| Gate passes but output still has drift | Gate checks logic but not content | Always follow gate pass with adversarial audit prompt (Pattern 3) |
| Friction resolved but dependent outputs not updated | Propagation not triggered | Always call `propagate_change()` after `resolve_friction()` |

---

## Dependencies

```bash
# Python stdlib only — no external packages required for core state management
# json, dataclasses, enum, pathlib

# For LLM API calls in production pipelines
pip install anthropic          # Anthropic Claude API
pip install openai             # OpenAI API
pip install tiktoken           # Token counting (context window management)

# For structured data validation
pip install pydantic           # Type-safe register schemas

# For testing
pip install pytest

# Optional: structured logging
pip install structlog
```

### Pydantic Schemas (production hardening)

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

EvidenceStatus = Literal[
    "VERIFIED", "AMBIGUOUS", "CONTRADICTORY", "SUPERSEDED",
    "OPERATOR_DIRECTIVE", "UNDEFINED", "MISSING_UPSTREAM", "INFERRED"
]

class ConstraintEntry(BaseModel):
    id:               str
    type:             str
    description:      str
    source:           str
    evidence_status:  EvidenceStatus
    affects:          list[str]
    active:           bool = True
    turn_discovered:  int

class ContradictionEntry(BaseModel):
    id:                 str
    system:             str
    source_a:           str
    source_b:           str
    authority_resolves: bool = False
    evidence_status:    EvidenceStatus = "CONTRADICTORY"
    impact:             Literal["decision_critical", "recoverable", "cosmetic"]
    affects:            list[str]
    resolution:         Optional[str] = None
    turn_discovered:    int

class MissingSourceEntry(BaseModel):
    id:              str
    description:     str
    severity:        Literal["fatal", "high", "advisory"]
    blocks:          list[str]
    evidence_status: EvidenceStatus = "MISSING_UPSTREAM"
    turn_discovered: int

class FrictionEntry(BaseModel):
    id:                   str
    conflict_type:        str
    description:          str
    source_a:             str
    source_b:             str
    affected_deliverable: str
    verdict:              str
    resolution:           Optional[str] = None
    resolved_by:          Optional[str] = None
    turn_discovered:      int
    turn_resolved:        Optional[int] = None
```
