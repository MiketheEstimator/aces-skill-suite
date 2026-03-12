---
name: DATA_TABULAR_FINANCE_MASTER
description: "Master playbook for financial tabular modeling outputs in XLSX format with deterministic validation and auditability."
---

# DATA_TABULAR_FINANCE_MASTER

## Objective
Generate financial-grade XLSX workbooks that are explainable, recalculable, and QA-verifiable.

## Required Output Contract
1. Workbook must include at minimum:
   - `Inputs` sheet
   - `Calculations` sheet
   - `Outputs` sheet
2. Hardcoded inputs are styled in blue (`RGB 0,0,255`).
3. Formula cells are styled in black (`RGB 0,0,0`).
4. Include a short "model assumptions" section at the top of `Inputs`.

## Validation Protocol
- Validate formatting and formula consistency against `QA_GATE_XLSX_01`.
- Provide operator instruction to run formula recalculation where applicable.
- Reject output if broken references (`#REF!`) or divide-by-zero (`#DIV/0!`) errors are detected.

## Recommended Build Steps
1. Build canonical input ranges.
2. Create named ranges for high-impact assumptions.
3. Author formulas only in calculation and output sections.
4. Recalculate, then export final workbook.
5. Summarize major assumptions and sensitivity variables.
