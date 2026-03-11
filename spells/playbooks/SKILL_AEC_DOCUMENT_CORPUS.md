---
name: SKILL_AEC_DOCUMENT_CORPUS
description: "Structure, classify, prepare, and ingest construction document corpora for LLM-based analysis. Use when assembling drawing sets, specifications, addenda, RFIs, bid forms, and project collateral for deterministic contract auditing, scope extraction, or proposal generation pipelines. Covers document family classification, project purity verification, PDF extraction strategies, identifier integrity, chunking for context window management, and metadata schemas for source authority tracking. Triggers: 'construction documents', 'spec book', 'drawing set', 'addenda ingestion', 'RFI log', 'bid documents', 'document corpus', 'project purity', 'AEC LLM pipeline', 'contract audit prep'."
---

# SKILL_AEC_DOCUMENT_CORPUS — AEC Document Corpus Skill

> **Scope:** Preparing, classifying, extracting, and staging construction documents
> for LLM-based analysis pipelines. This skill covers the intake layer —
> everything that happens before the LLM receives a prompt.
> For session state management (registers, gates, rehydration) see `SKILL_LLM_SESSION_STATE`.
> For scope extraction, condition classification, and evidence tagging see `SKILL_AEC_SCOPE_EXTRACTION`.

## Quick Reference

| Task | Section |
|------|---------|
| Document family taxonomy | [Document Family Taxonomy](#document-family-taxonomy) |
| Project purity verification | [Project Purity Verification](#project-purity-verification) |
| File naming conventions | [File Naming Conventions](#file-naming-conventions) |
| PDF extraction strategies | [PDF Extraction Strategies](#pdf-extraction-strategies) |
| Raster vs vector vs OCR | [Raster, Vector, and OCR](#raster-vector-and-ocr) |
| Identifier integrity scanning | [Identifier Integrity Scanning](#identifier-integrity-scanning) |
| Chunking for context windows | [Chunking for Context Windows](#chunking-for-context-windows) |
| Metadata schema | [Metadata Schema](#metadata-schema) |
| Authority hierarchy declaration | [Authority Hierarchy Declaration](#authority-hierarchy-declaration) |
| Corpus assembly pipeline | [Corpus Assembly Pipeline](#corpus-assembly-pipeline) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Document Family Taxonomy

Every document in a construction corpus belongs to exactly one family.
Families determine authority rank, extraction strategy, and how contradictions are resolved.

### Primary Families

| Family | Authority Role | Typical Formats | Examples |
|--------|---------------|-----------------|---------|
| **Addenda** | Highest — supersedes all below | PDF, DOC | Addendum 1, 2, 3 |
| **RFI / ASI** | High — governs over specs and drawings | PDF, DOC, XLS | RFI-042, ASI-07 |
| **Bid Forms / Proposal Forms** | Binding on quantities and alternates | PDF, XLS, DOC | Bid Schedule, Alternates Form |
| **Specifications** | Quality, method, material governing | PDF (multi-section) | Project Manual, CSI MasterFormat |
| **Drawings** | Dimensional, spatial, and configuration governing | PDF (vector/raster) | Architectural, Structural, MEP sets |
| **Schedules** | Linked to drawings and specs; often cross-reference both | PDF, XLS | Door Schedule, Finish Schedule, Equipment Schedule |
| **Geotechnical / Survey** | Governs subsurface scope; often fatal if absent | PDF | Geotech Report, Boring Logs, Topographic Survey |
| **Owner Narratives / Scope Summaries** | Contextual only; not binding | PDF, DOC | Project Description, Scope Narrative |
| **Collateral / User Notes** | Lowest — operator-originated; must be tagged | DOC, TXT, Email | Estimator notes, meeting recaps, AI summaries |

### Sub-families Within Specifications

CSI MasterFormat division structure — used for section-level authority and extraction routing:

```
Division 00 — Procurement & Contracting Requirements
  00 10 00  Solicitation Documents
  00 20 00  Instructions to Bidders
  00 40 00  Procurement Forms (Bid Bond, Proposal Form)
  00 70 00  Conditions of Contract (General, Supplementary)
  00 90 00  Revisions, Clarifications, Modifications (Addenda live here)

Division 01 — General Requirements
  01 10 00  Summary of Work (scope limits, phasing, occupancy rules)
  01 20 00  Price and Payment Procedures (unit prices, allowances)
  01 30 00  Administrative Requirements (submittals, RFIs, schedule)
  01 40 00  Quality Requirements (testing, inspections)
  01 50 00  Temporary Facilities
  01 60 00  Product Requirements (no-sub lists, substitution procedure)
  01 70 00  Execution Requirements (cutting, patching, cleaning)

Divisions 02–49 — Technical Specifications (by trade/system)
  02 — Existing Conditions
  03 — Concrete
  05 — Metals
  06 — Wood, Plastics, Composites
  07 — Thermal & Moisture Protection
  08 — Openings
  09 — Finishes
  10 — Specialties
  11 — Equipment
  14 — Conveying Equipment
  21 — Fire Suppression
  22 — Plumbing
  23 — HVAC
  26 — Electrical
  27 — Communications
  28 — Electronic Safety & Security
  31 — Earthwork
  32 — Exterior Improvements
  33 — Utilities
```

### Drawing Discipline Codes

```
A  — Architectural
S  — Structural
C  — Civil / Site
L  — Landscape
P  — Plumbing
M  — Mechanical / HVAC
E  — Electrical
FA — Fire Alarm
FP — Fire Protection / Sprinkler
T  — Telecommunications / AV
G  — General / Cover sheets
SK — Sketches (typically issued with ASIs)
```

---

## Project Purity Verification

**The single most critical pre-processing step.**
A corpus containing documents from more than one project produces contaminated analysis.
All downstream extraction is invalid until purity is confirmed.

### Purity Indicators to Extract and Compare

For every document in the corpus, extract these identifiers and compare across all documents:

```python
PURITY_INDICATORS = [
    "project_number",      # e.g. "2401", "23-045"
    "project_name",        # e.g. "Main Street Renovation"
    "architect_number",    # e.g. "ARC-2024-112"
    "bid_number",          # e.g. "BID-2024-031"
    "owner_name",          # e.g. "City of Springfield"
    "drawing_title_block", # project name on sheet title block
    "spec_section_header", # project identifier in spec page headers
    "addendum_reference",  # which bid package the addendum targets
    "issue_date_set",      # drawing set issue date
]
```

### Project Purity Check

```python
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import re

@dataclass
class DocumentRecord:
    filename:       str
    family:         str
    project_number: Optional[str] = None
    project_name:   Optional[str] = None
    bid_number:     Optional[str] = None
    architect_num:  Optional[str] = None
    issue_date:     Optional[str] = None
    sheet_ids:      list[str] = field(default_factory=list)
    spec_sections:  list[str] = field(default_factory=list)
    raw_text_head:  str = ""    # first 500 chars for heuristic checks


@dataclass
class PurityResult:
    status:          str       # "PURE" | "SUSPECT" | "CONTAMINATED"
    dominant_project: Optional[str]
    suspect_files:   list[str]
    conflicts:       list[str]
    verdict:         str


def check_project_purity(records: list[DocumentRecord],
                          expected_project_id: str = None) -> PurityResult:
    """
    Verify all documents belong to the same project.
    Returns PurityResult with status and list of suspect files.
    """
    project_numbers = defaultdict(list)
    bid_numbers     = defaultdict(list)
    suspect_files   = []
    conflicts       = []

    for rec in records:
        if rec.project_number:
            project_numbers[rec.project_number].append(rec.filename)
        if rec.bid_number:
            bid_numbers[rec.bid_number].append(rec.filename)

    # Determine dominant project
    if not project_numbers:
        dominant = expected_project_id or "[UNKNOWN]"
    else:
        dominant = max(project_numbers, key=lambda k: len(project_numbers[k]))

    # Flag documents with non-dominant project numbers
    for proj_num, files in project_numbers.items():
        if proj_num != dominant:
            for f in files:
                suspect_files.append(f)
                conflicts.append(
                    f"Project number mismatch: '{proj_num}' in {f} "
                    f"(dominant: '{dominant}')"
                )

    # Flag mismatched bid numbers
    if len(bid_numbers) > 1:
        for bid_num, files in bid_numbers.items():
            if len(bid_numbers[bid_num]) < max(len(v) for v in bid_numbers.values()):
                for f in files:
                    if f not in suspect_files:
                        suspect_files.append(f)
                    conflicts.append(
                        f"Bid number mismatch: '{bid_num}' in {f}"
                    )

    # Validate against expected project ID if provided
    if expected_project_id and dominant != expected_project_id:
        conflicts.append(
            f"Dominant project '{dominant}' does not match "
            f"expected '{expected_project_id}'"
        )

    if conflicts:
        status = "CONTAMINATED" if len(suspect_files) > 2 else "SUSPECT"
    else:
        status = "PURE"

    verdict = {
        "PURE":         "Corpus verified — single project detected",
        "SUSPECT":      f"WARNING — {len(suspect_files)} suspect file(s) detected; quarantine before analysis",
        "CONTAMINATED": f"HALT — mixed-project corpus detected; analysis blocked until resolved"
    }[status]

    return PurityResult(
        status           = status,
        dominant_project = dominant,
        suspect_files    = suspect_files,
        conflicts        = conflicts,
        verdict          = verdict
    )
```

### Quarantine Pattern

```python
def quarantine_files(suspect_files: list[str],
                     corpus_dir: str,
                     quarantine_dir: str) -> None:
    """
    Move suspect files to a quarantine directory.
    Quarantined files are excluded from analysis until adjudicated.
    """
    import shutil
    qdir = Path(quarantine_dir)
    qdir.mkdir(parents=True, exist_ok=True)

    for fname in suspect_files:
        src = Path(corpus_dir) / fname
        dst = qdir / fname
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"QUARANTINED: {fname} → {quarantine_dir}")
        else:
            print(f"WARNING: Could not quarantine {fname} — file not found")

    # Write quarantine manifest
    manifest_path = qdir / "QUARANTINE_MANIFEST.txt"
    manifest_path.write_text(
        "QUARANTINE MANIFEST\n"
        "===================\n"
        + "\n".join(suspect_files)
        + f"\n\nStatus: AWAITING ADJUDICATION\n"
    )
```

---

## File Naming Conventions

Consistent naming is required for reliable family classification, identifier extraction,
and audit traceability. Apply before ingestion.

### Canonical Naming Pattern

```
{ProjectID}_{Family}_{Identifier}_{Date}_{Revision}.{ext}

Examples:
  2401_SPEC_Division03_20240115_Rev0.pdf
  2401_DWG_S2.1_20240115_Issued-for-Bid.pdf
  2401_ADD_Addendum-2_20240210.pdf
  2401_RFI_042_20240220_Response.pdf
  2401_BID_ProposalForm_20240301.pdf
  2401_GEOTECH_BoringLogs_20231210.pdf
  2401_NARRATIVE_ProjectSummary_20240101.pdf
```

### Family Code Map

```python
FAMILY_CODES = {
    "ADD":       "Addenda",
    "ASI":       "Architectural Supplemental Instructions",
    "RFI":       "Request for Information",
    "SPEC":      "Specifications",
    "DWG":       "Drawings",
    "BID":       "Bid / Proposal Forms",
    "SCHED":     "Schedules",
    "GEOTECH":   "Geotechnical / Survey",
    "NARRATIVE": "Owner Narrative / Scope Summary",
    "COLLAT":    "User Collateral / Operator Notes",
}
```

### Rename Utility

```python
import shutil
from pathlib import Path

def normalize_filename(src_path: str,
                        project_id: str,
                        family_code: str,
                        identifier: str,
                        date: str,
                        revision: str = None,
                        dest_dir: str = None) -> str:
    """
    Rename a file to canonical convention.
    Returns the new path.
    """
    src = Path(src_path)
    rev_part = f"_{revision}" if revision else ""
    new_name = f"{project_id}_{family_code}_{identifier}_{date}{rev_part}{src.suffix}"

    dest_dir  = Path(dest_dir) if dest_dir else src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    new_path  = dest_dir / new_name

    shutil.copy2(src, new_path)
    print(f"Renamed: {src.name} → {new_name}")
    return str(new_path)
```

---

## PDF Extraction Strategies

Construction documents arrive as PDFs in three states, each requiring a different
extraction approach.

### State Classification

| State | Description | Detection | Extraction Tool |
|-------|-------------|-----------|-----------------|
| **Vector PDF** | Text is real; fonts are embedded or substituted | `pdfminer` returns clean text | `pdfminer.six` or `pypdf` |
| **Raster PDF** | Scanned pages; text is pixels | `pdfminer` returns empty or garbage | OCR required (`pytesseract`, `easyocr`) |
| **Mixed PDF** | Some pages vector, some raster | Varies per page | Per-page detection + routing |

```bash
pip install pdfminer.six pypdf pytesseract pdf2image pillow easyocr
# Also requires: apt install tesseract-ocr poppler-utils
```

### Detect PDF State Per Page

```python
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from io import StringIO
from pdf2image import convert_from_path
import re

def classify_pdf_page(pdf_path: str, page_num: int = 0) -> str:
    """
    Classify a single PDF page as 'vector', 'raster', or 'mixed'.
    page_num is 0-indexed.
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTFigure

    text_chars   = 0
    figure_count = 0

    for i, page_layout in enumerate(extract_pages(pdf_path)):
        if i != page_num:
            continue
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text_chars += len(element.get_text().strip())
            elif isinstance(element, LTFigure):
                figure_count += 1
        break

    if text_chars > 50:
        return "vector"
    elif figure_count > 0 and text_chars < 10:
        return "raster"
    else:
        return "raster"   # default to OCR if uncertain


def classify_pdf(pdf_path: str) -> dict:
    """
    Classify all pages of a PDF and return per-page state.
    """
    from pdfminer.high_level import extract_pages
    results = {}
    for i, _ in enumerate(extract_pages(pdf_path)):
        results[i] = classify_pdf_page(pdf_path, i)
    return results
```

### Extract Vector PDF Text

```python
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def extract_vector_text(pdf_path: str,
                         page_numbers: list[int] = None) -> str:
    """
    Extract text from a vector PDF.
    page_numbers: 0-indexed list; None = all pages.
    """
    laparams = LAParams(
        line_overlap      = 0.5,
        char_margin       = 2.0,
        line_margin       = 0.5,
        word_margin       = 0.1,
        boxes_flow        = 0.5,
        detect_vertical   = False,
        all_texts         = False,
    )
    text = extract_text(
        pdf_path,
        page_numbers = page_numbers,
        laparams     = laparams
    )
    return text.strip()
```

### Extract Raster PDF via OCR

```python
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from pathlib import Path

def extract_raster_text_tesseract(pdf_path: str,
                                   dpi: int = 300,
                                   lang: str = "eng") -> str:
    """
    Convert each page to image and OCR with Tesseract.
    DPI 300 is minimum for construction spec text.
    DPI 400+ recommended for small-print schedules and tables.
    """
    pages = convert_from_path(pdf_path, dpi=dpi)
    text_parts = []

    for i, page_image in enumerate(pages):
        page_text = pytesseract.image_to_string(
            page_image,
            lang     = lang,
            config   = "--psm 6"   # Uniform block of text
        )
        text_parts.append(f"[PAGE {i+1}]\n{page_text.strip()}")

    return "\n\n".join(text_parts)


def extract_raster_text_easyocr(pdf_path: str, dpi: int = 300) -> str:
    """
    EasyOCR alternative — better on irregular layouts (title blocks, legends).
    """
    import easyocr
    reader = easyocr.Reader(["en"], gpu=False)
    pages  = convert_from_path(pdf_path, dpi=dpi)
    text_parts = []

    for i, page_image in enumerate(pages):
        import numpy as np
        result = reader.readtext(np.array(page_image))
        page_text = " ".join([item[1] for item in result])
        text_parts.append(f"[PAGE {i+1}]\n{page_text.strip()}")

    return "\n\n".join(text_parts)
```

### Unified Per-Page Router

```python
def extract_pdf_text(pdf_path: str,
                      dpi: int = 300,
                      ocr_engine: str = "tesseract") -> dict:
    """
    Auto-detect PDF state per page and route to correct extractor.
    Returns dict: {page_index: {"state": str, "text": str}}
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTFigure
    from pdf2image import convert_from_path

    results   = {}
    pages_img = None   # lazy-load; only convert if raster pages detected

    for i, page_layout in enumerate(extract_pages(pdf_path)):
        text_chars = 0
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text_chars += len(element.get_text().strip())

        if text_chars > 50:
            # Vector — extract directly
            page_text = extract_vector_text(pdf_path, page_numbers=[i])
            results[i] = {"state": "vector", "text": page_text}
        else:
            # Raster — OCR this page
            if pages_img is None:
                pages_img = convert_from_path(pdf_path, dpi=dpi)
            if i < len(pages_img):
                if ocr_engine == "easyocr":
                    import easyocr, numpy as np
                    reader = easyocr.Reader(["en"], gpu=False)
                    result = reader.readtext(np.array(pages_img[i]))
                    page_text = " ".join([item[1] for item in result])
                else:
                    page_text = pytesseract.image_to_string(
                        pages_img[i], lang="eng", config="--psm 6"
                    )
                results[i] = {"state": "raster", "text": page_text.strip()}
            else:
                results[i] = {"state": "unknown", "text": ""}

    return results
```

---

## Raster, Vector, and OCR

### Triangulation Rule

When a drawing contains both vector text (sheet title, callout notes) and raster
content (scanned detail images), treat the two layers as separate evidence streams.
If they disagree, apply the Multimodal Triangulation rule:

```
Priority for conflict resolution (highest to lowest):
1. Vector PDF text — most reliable; direct extraction
2. Legend / keynote text — usually vector; governs symbol interpretation
3. OCR of raster page content — prone to character errors; verify before using
4. Sheet title and callout labels — usually vector; use for context only
5. Adjacent reference (nearby text on same page) — corroborative only

Rule: if vector and OCR disagree on a number, dimension, or identifier:
  - Log as [AMBIGUOUS]
  - Do not assert either version
  - Issue RFI for clarification
```

### OCR Quality Checks

```python
def assess_ocr_quality(ocr_text: str) -> dict:
    """
    Heuristic assessment of OCR output quality.
    Returns dict with quality score and issues list.
    """
    issues = []
    total_chars = len(ocr_text)

    if total_chars < 100:
        issues.append("Very low character count — possible blank or failed OCR")

    # High ratio of non-alphanumeric characters suggests OCR noise
    non_alnum = sum(1 for c in ocr_text if not c.isalnum() and c not in " \n\t.,;:()/-%\"'")
    noise_ratio = non_alnum / total_chars if total_chars > 0 else 1.0
    if noise_ratio > 0.15:
        issues.append(f"High noise ratio: {noise_ratio:.2%} non-standard chars — OCR quality suspect")

    # Check for common OCR confusions in construction docs
    common_confusions = {
        r"\b0\b(?=\s*[']|inch)": "Zero/O confusion in dimension",
        r"\bI\b(?=\s*\d)":       "I/1 confusion in identifier",
        r"[A-Z]{5,}(?!\s)":      "Run-on capitalized text — possible word-break failure",
    }
    import re
    for pattern, label in common_confusions.items():
        if re.search(pattern, ocr_text):
            issues.append(f"Possible {label}")

    score = max(0.0, 1.0 - (len(issues) * 0.25) - noise_ratio)

    return {
        "quality_score":    round(score, 2),
        "char_count":       total_chars,
        "noise_ratio":      round(noise_ratio, 4),
        "issues":           issues,
        "verdict":          "ACCEPTABLE" if score >= 0.7 else "SUSPECT — verify before use"
    }
```

---

## Identifier Integrity Scanning

Construction documents are governed by exact identifiers.
Normalization, alias substitution, or near-match correction destroys auditability.

### Identifier Types to Preserve Exactly

```python
IDENTIFIER_TYPES = {
    "sheet_id":         r"\b[A-Z]{1,3}[-.]?\d{1,2}\.?\d{0,2}\b",  # A2.1, S3, MEP-04
    "spec_section":     r"\b\d{2}\s?\d{2}\s?\d{2}\b",              # 03 30 00
    "room_name":        None,   # free-text; preserve exactly as written
    "project_number":   r"\b\d{4,6}[-/]\d{0,4}\b",                 # 2401, 23-045
    "bid_alternate":    r"\b(Alternate|Alt\.?)\s*\d+[A-Z]?\b",     # Alternate 2, Alt. 3A
    "addendum_number":  r"\b(Addendum|ADD)\s*[-#]?\d+\b",
    "rfi_number":       r"\bRFI[-\s]?\d{2,4}\b",
    "asi_number":       r"\bASI[-\s]?\d{1,3}\b",
    "detail_reference": r"\d{1,2}/[A-Z]\d{1,2}\.\d{1,2}",         # 4/S3.1
    "keynote":          r"\b[Kk][Nn]?\s*[-.]?\s*\d{1,3}\b",
    "csi_division":     r"\bDivision\s+\d{2}\b",
}


def extract_identifiers(text: str) -> dict:
    """
    Extract all construction identifiers from text.
    Returns dict of identifier_type → list of exact matches.
    """
    import re
    found = {}
    for id_type, pattern in IDENTIFIER_TYPES.items():
        if pattern:
            matches = re.findall(pattern, text)
            if matches:
                found[id_type] = list(dict.fromkeys(matches))   # deduplicate, preserve order
    return found


def scan_identifier_drift(original: str, processed: str,
                            id_type: str = None) -> list[dict]:
    """
    Compare identifiers in original vs processed text.
    Returns list of drift events (identifiers that changed or disappeared).
    """
    orig_ids  = extract_identifiers(original)
    proc_ids  = extract_identifiers(processed)
    drift     = []

    types_to_check = [id_type] if id_type else list(IDENTIFIER_TYPES.keys())

    for t in types_to_check:
        orig_set = set(orig_ids.get(t, []))
        proc_set = set(proc_ids.get(t, []))

        dropped  = orig_set - proc_set
        added    = proc_set - orig_set

        for item in dropped:
            drift.append({
                "type":   t,
                "event":  "DROPPED",
                "value":  item,
                "risk":   "Identifier loss — may represent omitted scope or source"
            })
        for item in added:
            drift.append({
                "type":   t,
                "event":  "ADDED",
                "value":  item,
                "risk":   "New identifier — verify source; may indicate contamination"
            })

    return drift
```

---

## Chunking for Context Windows

A full project manual may be 300–800 pages. Drawing sets for a major project may exceed
1,000 sheets. Context windows cannot hold an entire corpus simultaneously.
Chunking strategy determines what the model sees — and therefore what it can reason about.

### Chunking Principles

1. **Never split a spec section across chunks** — a split section loses its governing context
2. **Never split a table or schedule** — partial tables produce wrong data
3. **Keep keynotes and their legend on the same chunk** — keynotes without their legend are uninterpretable
4. **Attach sheet metadata to every chunk** — sheet ID, discipline, revision, issue date
5. **Include a session state header in every chunk prompt** — constraints must travel with content

### Spec Book Chunking

```python
import re
from dataclasses import dataclass, field

@dataclass
class SpecChunk:
    chunk_id:       str
    source_file:    str
    division:       str
    section_number: str
    section_title:  str
    page_range:     tuple[int, int]
    text:           str
    token_count:    int = 0
    metadata:       dict = field(default_factory=dict)


def chunk_spec_by_section(spec_text: str,
                            source_file: str,
                            max_tokens: int = 6000) -> list[SpecChunk]:
    """
    Split a specification book into chunks at CSI section boundaries.
    Each chunk = one spec section (or sub-section if section exceeds max_tokens).

    Assumes sections begin with patterns like:
    'SECTION 03 30 00 - CAST-IN-PLACE CONCRETE'
    'SECTION 03 30 00'
    """
    section_pattern = re.compile(
        r"(?:^|\n)(SECTION\s+(\d{2}\s?\d{2}\s?\d{2})\s*[-–—]?\s*([^\n]{0,80}))",
        re.MULTILINE
    )

    chunks   = []
    matches  = list(section_pattern.finditer(spec_text))

    for i, match in enumerate(matches):
        section_num   = match.group(2).strip().replace(" ", " ")
        section_title = match.group(3).strip()
        start_pos     = match.start()
        end_pos       = matches[i+1].start() if i+1 < len(matches) else len(spec_text)

        section_text = spec_text[start_pos:end_pos].strip()
        division     = section_num[:2]

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        est_tokens = len(section_text) // 4

        if est_tokens <= max_tokens:
            chunks.append(SpecChunk(
                chunk_id       = f"SPEC-{section_num.replace(' ', '')}",
                source_file    = source_file,
                division       = f"Division {division}",
                section_number = section_num,
                section_title  = section_title,
                page_range     = (0, 0),   # populate from PDF if available
                text           = section_text,
                token_count    = est_tokens,
            ))
        else:
            # Split long sections at PART boundaries (Part 1, Part 2, Part 3)
            part_pattern = re.compile(r"\n(PART\s+\d+\s*[-–—]?\s*[A-Z ]{0,40})", re.MULTILINE)
            parts = list(part_pattern.finditer(section_text))

            if parts:
                for j, part_match in enumerate(parts):
                    part_start = part_match.start()
                    part_end   = parts[j+1].start() if j+1 < len(parts) else len(section_text)
                    part_text  = section_text[part_start:part_end].strip()
                    part_label = part_match.group(1).strip()

                    chunks.append(SpecChunk(
                        chunk_id       = f"SPEC-{section_num.replace(' ', '')}-{j+1}",
                        source_file    = source_file,
                        division       = f"Division {division}",
                        section_number = section_num,
                        section_title  = f"{section_title} — {part_label}",
                        page_range     = (0, 0),
                        text           = part_text,
                        token_count    = len(part_text) // 4,
                    ))
            else:
                # No PART boundaries — hard split with overlap
                step    = max_tokens * 4
                overlap = 500
                pos     = 0
                part_n  = 0
                while pos < len(section_text):
                    end  = min(pos + step, len(section_text))
                    part_n += 1
                    chunks.append(SpecChunk(
                        chunk_id       = f"SPEC-{section_num.replace(' ', '')}-P{part_n}",
                        source_file    = source_file,
                        division       = f"Division {division}",
                        section_number = section_num,
                        section_title  = f"{section_title} (Part {part_n})",
                        page_range     = (0, 0),
                        text           = section_text[pos:end],
                        token_count    = (end - pos) // 4,
                    ))
                    pos = end - overlap   # overlap for continuity

    return chunks
```

### Drawing Sheet Chunking

Each sheet is a self-contained chunk. The chunk must carry:
- Sheet ID and title
- Discipline and phase
- Issue date and revision
- Reference to linked spec sections and details

```python
@dataclass
class DrawingChunk:
    chunk_id:       str
    sheet_id:       str        # e.g. "S2.1"
    discipline:     str        # e.g. "Structural"
    sheet_title:    str
    issue_date:     str
    revision:       str
    source_file:    str
    extracted_text: str        # vector text + OCR
    keynotes:       list[str]  # extracted keynote references
    linked_details: list[str]  # detail references found on sheet (e.g. "4/S3.1")
    linked_specs:   list[str]  # spec section references found on sheet
    token_count:    int = 0
    ocr_quality:    dict = field(default_factory=dict)


def build_drawing_chunk(sheet_id: str, sheet_title: str,
                         discipline: str, issue_date: str,
                         revision: str, source_file: str,
                         extracted_text: str) -> DrawingChunk:
    """Build a DrawingChunk from extracted text, auto-parsing references."""
    identifiers   = extract_identifiers(extracted_text)
    ocr_quality   = assess_ocr_quality(extracted_text)

    return DrawingChunk(
        chunk_id       = f"DWG-{sheet_id}",
        sheet_id       = sheet_id,
        discipline     = discipline,
        sheet_title    = sheet_title,
        issue_date     = issue_date,
        revision       = revision,
        source_file    = source_file,
        extracted_text = extracted_text,
        keynotes       = identifiers.get("keynote", []),
        linked_details = identifiers.get("detail_reference", []),
        linked_specs   = identifiers.get("spec_section", []),
        token_count    = len(extracted_text) // 4,
        ocr_quality    = ocr_quality,
    )
```

### Chunk Prompt Template

Every chunk fed to the LLM must carry its identity and the active session state:

```python
def build_chunk_prompt(chunk, session_state_header: str,
                        task: str) -> str:
    """Build a fully-labelled prompt for a single document chunk."""

    if isinstance(chunk, SpecChunk):
        source_block = (
            f"SOURCE: {chunk.source_file}\n"
            f"TYPE: Specification\n"
            f"SECTION: {chunk.section_number} — {chunk.section_title}\n"
            f"DIVISION: {chunk.division}\n"
            f"CHUNK ID: {chunk.chunk_id}\n"
            f"AUTHORITY RANK: Per locked hierarchy\n"
        )
    elif isinstance(chunk, DrawingChunk):
        source_block = (
            f"SOURCE: {chunk.source_file}\n"
            f"TYPE: Drawing\n"
            f"SHEET: {chunk.sheet_id} — {chunk.sheet_title}\n"
            f"DISCIPLINE: {chunk.discipline}\n"
            f"ISSUE DATE: {chunk.issue_date}  REVISION: {chunk.revision}\n"
            f"CHUNK ID: {chunk.chunk_id}\n"
            f"AUTHORITY RANK: Per locked hierarchy\n"
            f"LINKED SPECS: {', '.join(chunk.linked_specs) or 'none detected'}\n"
            f"LINKED DETAILS: {', '.join(chunk.linked_details) or 'none detected'}\n"
            f"OCR QUALITY: {chunk.ocr_quality.get('verdict', 'N/A')}\n"
        )
    else:
        source_block = f"SOURCE: {getattr(chunk, 'source_file', 'unknown')}\n"

    return (
        f"{session_state_header}\n\n"
        f"=== DOCUMENT CHUNK ===\n"
        f"{source_block}"
        f"=== CONTENT ===\n"
        f"{chunk.text if hasattr(chunk, 'text') else chunk.extracted_text}\n"
        f"=== END CHUNK ===\n\n"
        f"TASK: {task}\n"
    )
```

---

## Metadata Schema

Every document in the corpus must have a metadata record.
This record drives authority assignment, purity checking, and source citation.

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

@dataclass
class DocumentMetadata:
    # Identity
    doc_id:          str           # canonical ID: "2401_SPEC_033000"
    filename:        str           # original filename
    canonical_name:  str           # renamed per convention
    family:          str           # Addenda | Specifications | Drawings | etc.
    family_code:     str           # ADD | SPEC | DWG | RFI | etc.

    # Project binding
    project_id:      str
    project_name:    Optional[str] = None
    bid_number:      Optional[str] = None

    # Document identity
    identifier:      str = ""      # section number, sheet ID, addendum number, etc.
    title:           str = ""
    issue_date:      Optional[str] = None
    revision:        Optional[str] = None

    # Authority
    authority_rank:  int = 99      # populated when hierarchy is locked; lower = higher authority
    supersedes:      list[str] = field(default_factory=list)    # doc_ids this supersedes
    superseded_by:   list[str] = field(default_factory=list)    # doc_ids that supersede this

    # Extraction
    page_count:       int = 0
    extraction_state: str = "PENDING"    # PENDING | VECTOR | RASTER | MIXED | FAILED
    ocr_quality:      Optional[float] = None
    text_extracted:   bool = False
    chunks:           list[str] = field(default_factory=list)    # chunk_ids

    # Evidence
    evidence_status: str = "VERIFIED"   # VERIFIED | AMBIGUOUS | SUPERSEDED
    purity_status:   str = "UNVERIFIED" # PURE | SUSPECT | CONTAMINATED | UNVERIFIED

    # Cross-references
    linked_spec_sections:  list[str] = field(default_factory=list)
    linked_sheets:         list[str] = field(default_factory=list)
    linked_addenda:        list[str] = field(default_factory=list)
    references_missing:    list[str] = field(default_factory=list)   # referenced but absent


def metadata_to_citation(meta: DocumentMetadata) -> str:
    """Generate a source citation string for use in extracted scope items."""
    parts = [meta.family]
    if meta.identifier:
        parts.append(meta.identifier)
    if meta.title:
        parts.append(meta.title)
    if meta.revision:
        parts.append(f"Rev {meta.revision}")
    if meta.issue_date:
        parts.append(meta.issue_date)
    return " — ".join(parts)
```

---

## Authority Hierarchy Declaration

The authority hierarchy must be explicitly declared and locked before any extraction begins.
It is project-specific — no default may be assumed.

### Declaration Procedure

```python
from typing import Optional

@dataclass
class HierarchyEntry:
    rank:        int
    family:      str
    family_code: str
    note:        str
    doc_ids:     list[str] = field(default_factory=list)   # actual documents at this rank


def declare_hierarchy(entries: list[HierarchyEntry],
                       project_id: str,
                       declared_by: str = "Operator",
                       source_basis: str = "Division 00 70 00 — General Conditions") -> dict:
    """
    Declare and lock the authority hierarchy for the session.
    Returns a locked hierarchy record for injection into SessionState.
    """
    locked = {
        "locked":       True,
        "project_id":   project_id,
        "declared_by":  declared_by,
        "source_basis": source_basis,
        "order": [
            {
                "rank":        e.rank,
                "type":        e.family,
                "family_code": e.family_code,
                "note":        e.note,
                "doc_ids":     e.doc_ids,
            }
            for e in sorted(entries, key=lambda x: x.rank)
        ]
    }

    print(f"Authority Hierarchy LOCKED — Project {project_id}")
    for entry in locked["order"]:
        print(f"  Rank {entry['rank']}: {entry['type']} — {entry['note']}")

    return locked


# Standard AEC hierarchy (declare explicitly — never assume)
standard_hierarchy = declare_hierarchy([
    HierarchyEntry(1, "Addenda",        "ADD",      "Supersedes all other documents"),
    HierarchyEntry(2, "RFI/ASI",        "RFI/ASI",  "Governs over specs and drawings"),
    HierarchyEntry(3, "Bid Forms",      "BID",      "Binding on scope and quantities"),
    HierarchyEntry(4, "Specifications", "SPEC",     "Quality, method, material governing"),
    HierarchyEntry(5, "Drawings",       "DWG",      "Dimensional and spatial governing"),
    HierarchyEntry(6, "Geotech/Survey", "GEOTECH",  "Governs subsurface scope"),
    HierarchyEntry(7, "Narratives",     "NARRATIVE","Contextual only — not binding"),
], project_id="2401")
```

---

## Corpus Assembly Pipeline

### Full Pipeline

```python
from pathlib import Path
import json

def assemble_corpus(raw_dir: str,
                     project_id: str,
                     output_dir: str,
                     expected_families: list[str] = None) -> dict:
    """
    Full corpus assembly pipeline:
    1. Discover documents
    2. Classify by family
    3. Verify project purity
    4. Extract text (vector + OCR routing)
    5. Scan identifiers
    6. Chunk for LLM ingestion
    7. Build metadata registry
    8. Report missing source dependencies

    Returns corpus summary dict.
    """
    raw      = Path(raw_dir)
    out      = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdf_files = list(raw.glob("**/*.pdf")) + list(raw.glob("**/*.PDF"))
    print(f"Discovered {len(pdf_files)} PDF files in {raw_dir}")

    # ── Step 1: Classify by family ────────────────────────────────────────────
    records  = []
    metadata = []

    for pdf in pdf_files:
        family, family_code = classify_document_family(pdf.name)
        rec = DocumentRecord(
            filename    = pdf.name,
            family      = family,
        )
        records.append(rec)
        meta = DocumentMetadata(
            doc_id        = f"{project_id}_{family_code}_{pdf.stem}",
            filename      = pdf.name,
            canonical_name = pdf.name,
            family        = family,
            family_code   = family_code,
            project_id    = project_id,
        )
        metadata.append(meta)

    # ── Step 2: Project purity ────────────────────────────────────────────────
    purity = check_project_purity(records, expected_project_id=project_id)
    print(f"Project Purity: {purity.status} — {purity.verdict}")

    if purity.status == "CONTAMINATED":
        quarantine_files(purity.suspect_files, raw_dir,
                         str(out / "quarantine"))
        print("HALT: Contaminated corpus — resolve before extraction")
        return {"status": "HALTED", "purity": purity.__dict__}

    # ── Step 3: Extract text ──────────────────────────────────────────────────
    chunks_all  = []
    for pdf, meta in zip(pdf_files, metadata):
        print(f"Extracting: {pdf.name}")
        try:
            pages = extract_pdf_text(str(pdf))
            full_text = "\n".join(p["text"] for p in pages.values())

            states = set(p["state"] for p in pages.values())
            meta.extraction_state = (
                "MIXED"  if len(states) > 1
                else "VECTOR" if "vector" in states
                else "RASTER"
            )
            meta.text_extracted = True
            meta.page_count = len(pages)

            # Save extracted text
            text_path = out / "extracted" / f"{meta.doc_id}.txt"
            text_path.parent.mkdir(exist_ok=True)
            text_path.write_text(full_text, encoding="utf-8")

            # Chunk by type
            if meta.family == "Specifications":
                section_chunks = chunk_spec_by_section(full_text, pdf.name)
                chunks_all.extend(section_chunks)
                meta.chunks = [c.chunk_id for c in section_chunks]
            else:
                # One chunk per document for non-spec families
                meta.chunks = [meta.doc_id]

            # Identifier scan
            ids_found = extract_identifiers(full_text)
            meta.linked_spec_sections = ids_found.get("spec_section", [])
            meta.linked_sheets        = ids_found.get("sheet_id", [])

        except Exception as e:
            meta.extraction_state = "FAILED"
            print(f"  ERROR: {pdf.name} — {e}")

    # ── Step 4: Detect missing source dependencies ────────────────────────────
    all_referenced_specs = set()
    all_present_specs    = set()

    for meta in metadata:
        if meta.family == "Specifications":
            all_present_specs.update(meta.linked_spec_sections)
        all_referenced_specs.update(meta.linked_spec_sections)

    missing_specs = all_referenced_specs - all_present_specs
    if missing_specs:
        print(f"MISSING SPEC SECTIONS (referenced but not in corpus): {sorted(missing_specs)}")

    # ── Step 5: Save metadata registry ───────────────────────────────────────
    registry_path = out / "corpus_registry.json"
    registry_data = {
        "project_id":     project_id,
        "document_count": len(metadata),
        "purity_status":  purity.status,
        "missing_specs":  sorted(missing_specs),
        "documents":      [vars(m) for m in metadata],
    }
    registry_path.write_text(json.dumps(registry_data, indent=2), encoding="utf-8")
    print(f"Registry saved: {registry_path}")

    return registry_data


def classify_document_family(filename: str) -> tuple[str, str]:
    """Heuristic family classification by filename keywords."""
    name = filename.upper()
    if any(k in name for k in ("ADDENDUM", "ADD-", "ADD_", "ADDEN")):
        return "Addenda", "ADD"
    if any(k in name for k in ("ASI", "RFI")):
        return "RFI/ASI", "RFI"
    if any(k in name for k in ("BID", "PROPOSAL", "FORM")):
        return "Bid Forms", "BID"
    if any(k in name for k in ("SPEC", "DIVISION", "PROJECT MANUAL")):
        return "Specifications", "SPEC"
    if any(k in name for k in ("GEOTECH", "BORING", "SURVEY", "SOILS")):
        return "Geotechnical/Survey", "GEOTECH"
    if any(k in name for k in ("NARRATIVE", "SUMMARY", "DESCRIPTION")):
        return "Narratives", "NARRATIVE"
    # Drawing discipline codes
    for code in ("A", "S", "C", "L", "P", "M", "E", "FA", "FP", "T", "G"):
        if re.match(rf"^{code}\d", filename.upper()):
            return "Drawings", "DWG"
    return "Unknown", "UNK"
```

---

## Validation & QA

```python
def validate_corpus(registry_path: str) -> dict:
    """
    Validate a corpus registry for completeness, purity, and readiness.
    Returns validation report dict.
    """
    import json
    data   = json.loads(Path(registry_path).read_text())
    issues = []
    warns  = []

    # Purity
    if data.get("purity_status") != "PURE":
        issues.append(f"CORPUS NOT PURE: status = {data.get('purity_status')}")

    # All documents extracted
    failed = [d["filename"] for d in data["documents"]
              if d.get("extraction_state") == "FAILED"]
    if failed:
        issues.append(f"Extraction failed on {len(failed)} file(s): {failed}")

    # Missing spec sections
    missing = data.get("missing_specs", [])
    if missing:
        for m in missing:
            div = m[:2]
            # Divisions 31+ (earthwork, utilities) — fatal if absent
            severity = "FATAL" if int(div) >= 31 else "HIGH"
            warns.append(f"[{severity}] Missing spec section: {m}")

    # Hierarchy not yet declared — only a warning at corpus stage
    # (hierarchy is declared in the session, not the corpus)

    # Check for unknown family documents
    unknown = [d["filename"] for d in data["documents"]
               if d.get("family_code") == "UNK"]
    if unknown:
        warns.append(f"{len(unknown)} document(s) with unknown family — classify before analysis: {unknown}")

    # Document count sanity
    if data.get("document_count", 0) == 0:
        issues.append("Empty corpus — no documents registered")

    print(f"Corpus Validation: {'PASS' if not issues else 'FAIL'}")
    print(f"  Documents: {data.get('document_count')}")
    print(f"  Purity:    {data.get('purity_status')}")
    for i in issues: print(f"  ERROR: {i}")
    for w in warns:  print(f"  WARN:  {w}")

    return {
        "pass":     len(issues) == 0,
        "issues":   issues,
        "warnings": warns,
        "stats":    {k: data.get(k) for k in ("document_count", "purity_status", "missing_specs")}
    }
```

### QA Checklist

- [ ] All source PDFs renamed to canonical convention before ingestion
- [ ] Project purity check run — status is PURE; no quarantined files
- [ ] Every document has a `DocumentMetadata` record in the registry
- [ ] Authority hierarchy explicitly declared and locked
- [ ] All spec sections that are referenced by other documents are present — or registered as missing sources
- [ ] Every raster PDF page passed through OCR; quality score ≥ 0.70
- [ ] Mixed PDF pages classified correctly (vector vs raster per page)
- [ ] Identifier scan run — no unexpected sheet IDs or spec sections that don't match known documents
- [ ] All chunks carry source metadata (doc_id, section/sheet, issue date, revision)
- [ ] `validate_corpus()` passes with zero errors before handing off to extraction phase
- [ ] Missing source dependencies ranked (fatal / high / advisory) and registered in session state

### QA Loop

1. Drop raw files into `raw_dir/`
2. Run `assemble_corpus()` — generates registry and extracted text
3. Run `validate_corpus()` — resolve all errors before proceeding
4. Classify any `UNK` family documents manually
5. Register missing spec sections in `SessionState.missing_source_register`
6. Declare and lock authority hierarchy via `declare_hierarchy()`
7. Run identifier drift scan on any OCR-extracted pages with quality < 0.80
8. Hand chunks + locked session state to extraction phase (`SKILL_AEC_SCOPE_EXTRACTION`)

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| Raster PDF returns empty text | pdfminer only handles vector; scanned pages return nothing | Route to OCR; use `classify_pdf()` per page before extraction |
| OCR quality score < 0.50 on spec pages | DPI too low | Re-extract at 400 DPI minimum for small-print specs |
| Sheet ID "A2.1" normalised to "A2" | Regex or string stripping | Use `extract_identifiers()` with exact match; no post-processing of IDs |
| Project purity returns SUSPECT on single project | Different project number formats in different documents | Normalize to dominant format; log discrepancy; verify with owner |
| Spec section split mid-paragraph | Hard chunk on token count | Split at PART or article boundaries; never mid-paragraph |
| Addendum references Addendum 1 but Addendum 1 is absent | Missing dependency not detected | Run identifier scan; check for `ADD-\d` patterns; register missing addenda |
| Keynotes extracted without legend | Legend on separate sheet | Always pair keynote sheet with its legend sheet in the same chunk or include legend text in metadata |
| Mixed PDF loses vector layer after OCR | Replacing vector text with OCR output | Keep vector and OCR as separate evidence streams; triangulate, do not overwrite |
| Unknown family classification blocks pipeline | Filename doesn't match any heuristic pattern | Manually classify and rename; add custom keyword to `classify_document_family()` |

---

## Dependencies

```bash
# PDF extraction
pip install pdfminer.six pypdf

# OCR
pip install pytesseract pdf2image pillow easyocr
sudo apt install tesseract-ocr poppler-utils   # Linux
brew install tesseract poppler                  # macOS

# Data handling
pip install pandas

# Type validation (optional — production hardening)
pip install pydantic

# Testing
pip install pytest
```
