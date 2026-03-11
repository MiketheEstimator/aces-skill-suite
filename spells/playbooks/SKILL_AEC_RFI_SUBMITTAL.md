---
name: SKILL_AEC_RFI_SUBMITTAL
description: "Create, manage, track, and export RFI (Request for Information) and Submittal logs for construction projects. Use when generating formal RFI documents, tracking RFI/submittal lifecycles, building log spreadsheets, detecting overdue items, linking communications to scope items and spec sections, or producing transmittal packages. Covers RFI data models, submittal schedules, status workflows, log export (Excel/CSV/PDF), overdue detection, and integration with scope baseline and session state registers. Triggers: 'RFI log', 'submittal log', 'RFI register', 'submittal register', 'RFI tracking', 'submittal tracking', 'transmittal', 'submittal schedule', 'RFI response', 'submittal review', 'construction communication'."
---

# SKILL_AEC_RFI_SUBMITTAL — RFI & Submittal Log Skill

> **Scope:** Full lifecycle management of RFIs and Submittals as the primary
> written communication artifacts of a construction project. Covers data models,
> status workflows, log generation, overdue detection, Excel/CSV export,
> transmittal packages, and integration with scope extraction registers.
> For RFI *generation* from scope contradictions and missing sources see
> `SKILL_AEC_SCOPE_EXTRACTION`. For session state registers see `SKILL_LLM_SESSION_STATE`.

## Quick Reference

| Task | Section |
|------|---------|
| RFI data model and lifecycle | [RFI Data Model](#rfi-data-model) |
| Submittal data model and lifecycle | [Submittal Data Model](#submittal-data-model) |
| Log assembly and export | [Log Assembly and Export](#log-assembly-and-export) |
| Overdue detection | [Overdue Detection](#overdue-detection) |
| Transmittal package | [Transmittal Package](#transmittal-package) |
| Link to scope baseline | [Scope Linkage](#scope-linkage) |
| Submittal schedule generation | [Submittal Schedule](#submittal-schedule) |
| Excel log with formatting | [Excel Log](#excel-log) |
| Metrics and dashboard | [Metrics and Dashboard](#metrics-and-dashboard) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## RFI Data Model

### Status Workflow

```
DRAFT → ISSUED → UNDER_REVIEW → ANSWERED → CLOSED
                     ↓
                 OVERDUE (if response_due passes without answer)
                     ↓
               ESCALATED → ANSWERED → CLOSED

Closed conditions:
  CLOSED_ANSWERED   — response received and accepted
  CLOSED_VOID       — RFI withdrawn; question no longer applicable
  CLOSED_SUPERSEDED — resolved by addendum or design change
```

### RFI Record

```python
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

@dataclass
class RFIRecord:
    # Identity
    rfi_number:       str             # "RFI-042" — exact, never renumbered
    project_id:       str
    project_name:     str

    # Classification
    priority:         str             # FATAL | HIGH | ADVISORY
    discipline:       str             # Architectural | Structural | MEP | Civil | General
    spec_section:     str             # "05 12 00" — primary affected section
    drawing_ref:      str             # "S2.1" — primary affected sheet

    # Content
    subject:          str             # ≤ 80 chars — appears in log
    question:         str             # precise, answerable question
    background:       str             # context and source of conflict
    attachments:      list[str]       # filenames of attached documents

    # Dates
    date_issued:      Optional[date]  = None
    response_due:     Optional[date]  = None     # typically 7–14 calendar days
    date_answered:    Optional[date]  = None
    date_closed:      Optional[date]  = None

    # Parties
    issued_by:        str             = ""       # company issuing the RFI (usually GC)
    issued_to:        str             = ""       # Architect | Engineer | Owner
    answered_by:      str             = ""

    # Response
    status:           str             = "DRAFT"  # see workflow above
    response:         str             = ""
    response_source:  str             = ""       # document or meeting minutes backing response

    # Linkage to scope/session registers
    source_register:  str             = ""       # friction_log | contradiction_register | etc.
    source_entry_id:  str             = ""       # FRIC-001 | CONTRA-001 | etc.
    affected_scope:   list[str]       = field(default_factory=list)   # SCOPE-XXX ids

    # Impact tracking
    cost_impact:      Optional[str]   = None     # "None" | "TBD" | "$X,XXX"
    schedule_impact:  Optional[str]   = None     # "None" | "TBD" | "X days"
    revised_by:       Optional[str]   = None     # RFI-XXX if superseded

    # Metadata
    tags:             list[str]       = field(default_factory=list)


    def is_overdue(self, as_of: date = None) -> bool:
        as_of = as_of or date.today()
        return (
            self.status in ("ISSUED", "UNDER_REVIEW")
            and self.response_due is not None
            and as_of > self.response_due
        )


    def days_open(self, as_of: date = None) -> Optional[int]:
        as_of = as_of or date.today()
        if self.date_issued:
            end = self.date_closed or as_of
            return (end - self.date_issued).days
        return None


    def days_overdue(self, as_of: date = None) -> Optional[int]:
        as_of = as_of or date.today()
        if self.is_overdue(as_of) and self.response_due:
            return (as_of - self.response_due).days
        return None


    def to_log_row(self) -> dict:
        """Return a flat dict suitable for DataFrame / Excel row."""
        today = date.today()
        return {
            "RFI #":          self.rfi_number,
            "Priority":       self.priority,
            "Discipline":     self.discipline,
            "Spec Section":   self.spec_section,
            "Drawing":        self.drawing_ref,
            "Subject":        self.subject,
            "Issued By":      self.issued_by,
            "Issued To":      self.issued_to,
            "Date Issued":    str(self.date_issued) if self.date_issued else "",
            "Response Due":   str(self.response_due) if self.response_due else "",
            "Date Answered":  str(self.date_answered) if self.date_answered else "",
            "Status":         self.status,
            "Days Open":      self.days_open(today),
            "Days Overdue":   self.days_overdue(today) or "",
            "Cost Impact":    self.cost_impact or "TBD",
            "Schedule Impact": self.schedule_impact or "TBD",
            "Response":       self.response[:200] if self.response else "",
        }
```

### RFI Factory

```python
from datetime import date, timedelta

def create_rfi(rfi_number: str,
               project_id: str,
               project_name: str,
               subject: str,
               question: str,
               discipline: str,
               spec_section: str,
               drawing_ref: str = "",
               priority: str = "HIGH",
               issued_by: str = "",
               issued_to: str = "Architect of Record",
               response_days: int = 10,
               background: str = "",
               source_register: str = "",
               source_entry_id: str = "",
               affected_scope: list = None) -> RFIRecord:
    """
    Create a new RFI record with standard response deadline.
    response_days: calendar days for response (commonly 7, 10, or 14).
    """
    today = date.today()
    return RFIRecord(
        rfi_number      = rfi_number,
        project_id      = project_id,
        project_name    = project_name,
        priority        = priority,
        discipline      = discipline,
        spec_section    = spec_section,
        drawing_ref     = drawing_ref,
        subject         = subject,
        question        = question,
        background      = background,
        attachments     = [],
        date_issued     = today,
        response_due    = today + timedelta(days=response_days),
        issued_by       = issued_by,
        issued_to       = issued_to,
        status          = "ISSUED",
        source_register = source_register,
        source_entry_id = source_entry_id,
        affected_scope  = affected_scope or [],
    )


def answer_rfi(rfi: RFIRecord,
               response: str,
               answered_by: str,
               response_source: str = "",
               cost_impact: str = "None",
               schedule_impact: str = "None") -> RFIRecord:
    """Record a response to an open RFI."""
    rfi.response         = response
    rfi.answered_by      = answered_by
    rfi.response_source  = response_source
    rfi.cost_impact      = cost_impact
    rfi.schedule_impact  = schedule_impact
    rfi.date_answered    = date.today()
    rfi.status           = "ANSWERED"
    return rfi


def close_rfi(rfi: RFIRecord,
              close_type: str = "CLOSED_ANSWERED") -> RFIRecord:
    """Close an answered RFI."""
    rfi.status      = close_type
    rfi.date_closed = date.today()
    return rfi
```

---

## Submittal Data Model

### Submittal Types

```
TYPE 1 — SHOP DRAWINGS
  Fabrication drawings prepared by contractors/subs showing exact
  dimensions, materials, and installation details.
  Review authority: Architect / Engineer of Record.

TYPE 2 — PRODUCT DATA
  Manufacturer cut sheets, data sheets, installation instructions.
  Review authority: Architect / Specifier.

TYPE 3 — SAMPLES
  Physical material samples (tile, fabric, paint chip, mock-up panel).
  Review authority: Architect / Interior Designer.

TYPE 4 — CERTIFICATES / TEST REPORTS
  Mill certificates, weld certifications, test reports, commissioning data.
  Review authority: Engineer of Record / Owner's rep.

TYPE 5 — OPERATION & MAINTENANCE MANUALS
  O&M manuals for equipment and systems (often at substantial completion).
  Review authority: Owner / Facilities Manager.

TYPE 6 — CLOSEOUT DOCUMENTS
  As-builts, warranties, attic stock confirmations, LEED documentation.
  Review authority: Owner / Project Manager.
```

### Submittal Status Workflow

```
NOT_SUBMITTED → SUBMITTED → UNDER_REVIEW → REVIEWED
                                 ↓
                             OVERDUE (past promised review date)

Review dispositions:
  APPROVED              — fabricate / install as submitted
  APPROVED_AS_NOTED     — fabricate / install per reviewer markups
  REVISE_AND_RESUBMIT   — correct and resubmit; do not fabricate
  REJECTED              — does not meet spec; resubmit with different product
  FOR_INFORMATION_ONLY  — no action required; informational

Resubmittal path:
  REVISE_AND_RESUBMIT → RESUBMITTED → UNDER_REVIEW → REVIEWED
```

### Submittal Record

```python
@dataclass
class SubmittalRecord:
    # Identity
    submittal_number:  str        # "SUB-0142" — never renumbered
    project_id:        str
    spec_section:      str        # "05 12 00"
    spec_section_title: str       # "Structural Steel Framing"
    submittal_type:    str        # SHOP_DRAWING | PRODUCT_DATA | SAMPLE |
                                  # CERTIFICATE | OM_MANUAL | CLOSEOUT

    # Description
    description:       str        # what is being submitted
    manufacturer:      str        # product manufacturer (if applicable)
    model_number:      str        # exact model / product number

    # Dates and schedule
    required_on_site:  Optional[date] = None    # date material must be on site
    lead_time_days:    int             = 0       # procurement lead time
    submit_by:         Optional[date]  = None    # latest submission date
                                                 # = required_on_site - lead_time - review_time
    date_submitted:    Optional[date]  = None
    review_due:        Optional[date]  = None
    date_reviewed:     Optional[date]  = None

    # Parties
    submitted_by:      str        = ""   # subcontractor / GC
    reviewed_by:       str        = ""   # Architect / Engineer

    # Review outcome
    status:            str        = "NOT_SUBMITTED"
    disposition:       str        = ""   # APPROVED | APPROVED_AS_NOTED |
                                         # REVISE_AND_RESUBMIT | REJECTED | FOR_INFO_ONLY
    review_comments:   str        = ""
    revision:          int        = 0    # 0 = initial; 1, 2 = resubmittals

    # Linkage
    rfi_links:         list[str]  = field(default_factory=list)   # RFI-XXX
    drawing_ref:       str        = ""
    scope_item_ids:    list[str]  = field(default_factory=list)

    # Flags
    long_lead:         bool       = False   # procurement lead > 12 weeks
    critical_path:     bool       = False   # on critical path
    substitution_request: bool    = False   # requesting product substitution


    def compute_submit_by(self, review_days: int = 14) -> Optional[date]:
        """Calculate latest submission date from required-on-site date."""
        if self.required_on_site:
            self.submit_by = (
                self.required_on_site
                - timedelta(days=self.lead_time_days + review_days)
            )
            return self.submit_by
        return None


    def is_overdue(self, as_of: date = None) -> bool:
        as_of = as_of or date.today()
        return (
            self.status in ("NOT_SUBMITTED", "SUBMITTED", "UNDER_REVIEW")
            and self.submit_by is not None
            and as_of > self.submit_by
            and self.disposition not in ("APPROVED", "APPROVED_AS_NOTED")
        )


    def to_log_row(self) -> dict:
        today = date.today()
        return {
            "Submittal #":     self.submittal_number,
            "Spec Section":    self.spec_section,
            "Title":           self.spec_section_title,
            "Type":            self.submittal_type,
            "Description":     self.description,
            "Manufacturer":    self.manufacturer,
            "Submit By":       str(self.submit_by) if self.submit_by else "",
            "Date Submitted":  str(self.date_submitted) if self.date_submitted else "",
            "Review Due":      str(self.review_due) if self.review_due else "",
            "Date Reviewed":   str(self.date_reviewed) if self.date_reviewed else "",
            "Status":          self.status,
            "Disposition":     self.disposition,
            "Revision":        self.revision,
            "Long Lead":       "YES" if self.long_lead else "",
            "Critical Path":   "YES" if self.critical_path else "",
            "Lead Time (days)": self.lead_time_days,
            "Submitted By":    self.submitted_by,
        }
```

---

## Log Assembly and Export

### Assemble Log from Records

```python
import pandas as pd
from datetime import date

class CommunicationLog:
    """Manages the combined RFI and Submittal log for a project."""

    def __init__(self, project_id: str, project_name: str):
        self.project_id   = project_id
        self.project_name = project_name
        self.rfis:        list[RFIRecord]       = []
        self.submittals:  list[SubmittalRecord] = []

    def add_rfi(self, rfi: RFIRecord) -> None:
        # Check for duplicate number
        existing = [r for r in self.rfis if r.rfi_number == rfi.rfi_number]
        if existing:
            raise ValueError(f"Duplicate RFI number: {rfi.rfi_number}")
        self.rfis.append(rfi)

    def add_submittal(self, sub: SubmittalRecord) -> None:
        existing = [s for s in self.submittals
                    if s.submittal_number == sub.submittal_number]
        if existing:
            raise ValueError(f"Duplicate submittal number: {sub.submittal_number}")
        self.submittals.append(sub)

    def rfi_dataframe(self) -> pd.DataFrame:
        if not self.rfis:
            return pd.DataFrame()
        return pd.DataFrame([r.to_log_row() for r in self.rfis])

    def submittal_dataframe(self) -> pd.DataFrame:
        if not self.submittals:
            return pd.DataFrame()
        return pd.DataFrame([s.to_log_row() for s in self.submittals])

    def open_rfis(self) -> list[RFIRecord]:
        return [r for r in self.rfis
                if r.status not in ("CLOSED_ANSWERED","CLOSED_VOID","CLOSED_SUPERSEDED")]

    def overdue_rfis(self, as_of: date = None) -> list[RFIRecord]:
        return [r for r in self.rfis if r.is_overdue(as_of)]

    def overdue_submittals(self, as_of: date = None) -> list[SubmittalRecord]:
        return [s for s in self.submittals if s.is_overdue(as_of)]

    def long_lead_submittals(self) -> list[SubmittalRecord]:
        return [s for s in self.submittals if s.long_lead]

    def to_csv(self, rfi_path: str, submittal_path: str) -> None:
        self.rfi_dataframe().to_csv(rfi_path, index=False)
        self.submittal_dataframe().to_csv(submittal_path, index=False)
        print(f"RFI log:       {rfi_path}  ({len(self.rfis)} records)")
        print(f"Submittal log: {submittal_path}  ({len(self.submittals)} records)")
```

---

## Excel Log

```python
import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from datetime import date

# Colour palette
COLOUR = {
    "header_bg":     "1F3864",   # dark blue
    "header_font":   "FFFFFF",
    "fatal_bg":      "FF0000",
    "fatal_font":    "FFFFFF",
    "high_bg":       "FF9900",
    "advisory_bg":   "FFFF00",
    "overdue_bg":    "FF6666",
    "approved_bg":   "C6EFCE",
    "revise_bg":     "FFEB9C",
    "rejected_bg":   "FFC7CE",
    "alt_row":       "F2F7FF",
    "grid":          "CCCCCC",
}


def export_rfi_log_excel(log: "CommunicationLog", output_path: str) -> None:
    """
    Export RFI log to a formatted Excel workbook.
    Sheet 1: RFI Log | Sheet 2: Summary | Sheet 3: Overdue
    """
    wb  = openpyxl.Workbook()
    today = date.today()

    # ── Sheet 1: Full RFI Log ─────────────────────────────────────────────────
    ws  = wb.active
    ws.title = "RFI Log"

    df = log.rfi_dataframe()
    if df.empty:
        ws["A1"] = "No RFIs on record."
    else:
        _write_dataframe_to_sheet(ws, df, freeze_row=1)
        _apply_rfi_row_colours(ws, df, log.rfis)

    # ── Sheet 2: Summary ──────────────────────────────────────────────────────
    ws2 = wb.create_sheet("Summary")
    _write_rfi_summary(ws2, log, today)

    # ── Sheet 3: Overdue ──────────────────────────────────────────────────────
    ws3 = wb.create_sheet("Overdue RFIs")
    overdue = [r for r in log.rfis if r.is_overdue(today)]
    if overdue:
        df_od = pd.DataFrame([r.to_log_row() for r in overdue])
        _write_dataframe_to_sheet(ws3, df_od, freeze_row=1)
        _highlight_all_rows(ws3, df_od, COLOUR["overdue_bg"])
    else:
        ws3["A1"] = "No overdue RFIs."

    wb.save(output_path)
    print(f"RFI log Excel: {output_path}")


def export_submittal_log_excel(log: "CommunicationLog", output_path: str) -> None:
    """Export Submittal log to a formatted Excel workbook."""
    wb    = openpyxl.Workbook()
    today = date.today()

    ws = wb.active
    ws.title = "Submittal Log"

    df = log.submittal_dataframe()
    if df.empty:
        ws["A1"] = "No submittals on record."
    else:
        _write_dataframe_to_sheet(ws, df, freeze_row=1)
        _apply_submittal_row_colours(ws, df, log.submittals)

    ws2 = wb.create_sheet("Long Lead")
    ll  = [s for s in log.submittals if s.long_lead]
    if ll:
        df_ll = pd.DataFrame([s.to_log_row() for s in ll])
        _write_dataframe_to_sheet(ws2, df_ll, freeze_row=1)
    else:
        ws2["A1"] = "No long-lead submittals identified."

    ws3 = wb.create_sheet("Overdue")
    od  = [s for s in log.submittals if s.is_overdue(today)]
    if od:
        df_od = pd.DataFrame([s.to_log_row() for s in od])
        _write_dataframe_to_sheet(ws3, df_od, freeze_row=1)
        _highlight_all_rows(ws3, df_od, COLOUR["overdue_bg"])
    else:
        ws3["A1"] = "No overdue submittals."

    wb.save(output_path)
    print(f"Submittal log Excel: {output_path}")


def _write_dataframe_to_sheet(ws, df: pd.DataFrame, freeze_row: int = 1) -> None:
    """Write a DataFrame to a worksheet with header formatting."""
    header_fill = PatternFill("solid", fgColor=COLOUR["header_bg"])
    header_font = Font(bold=True, color=COLOUR["header_font"], size=10)
    thin        = Side(style="thin", color=COLOUR["grid"])
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)

    for c_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=c_idx, value=col_name)
        cell.fill   = header_fill
        cell.font   = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                    wrap_text=True)

    for r_idx, row in enumerate(df.itertuples(index=False), start=2):
        fill_colour = COLOUR["alt_row"] if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx,
                           value="" if pd.isna(value) else value)
            cell.fill   = PatternFill("solid", fgColor=fill_colour)
            cell.font   = Font(size=9)
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=False)

    # Auto-size columns
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=8)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 2, 40)

    if freeze_row:
        ws.freeze_panes = ws.cell(row=freeze_row + 1, column=1)


def _apply_rfi_row_colours(ws, df: pd.DataFrame,
                             rfis: list[RFIRecord]) -> None:
    """Apply priority and overdue colour coding to RFI rows."""
    today  = date.today()
    n_cols = len(df.columns)

    for r_idx, rfi in enumerate(rfis, start=2):
        if rfi.is_overdue(today):
            colour = COLOUR["overdue_bg"]
        elif rfi.priority == "FATAL":
            colour = COLOUR["fatal_bg"]
        elif rfi.priority == "HIGH":
            colour = COLOUR["high_bg"]
        else:
            colour = None

        if colour:
            for c_idx in range(1, n_cols + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.fill = PatternFill("solid", fgColor=colour)
                if colour in (COLOUR["fatal_bg"],):
                    cell.font = Font(size=9, color=COLOUR["fatal_font"])


def _apply_submittal_row_colours(ws, df: pd.DataFrame,
                                   submittals: list[SubmittalRecord]) -> None:
    today  = date.today()
    n_cols = len(df.columns)
    disp_col = list(df.columns).index("Disposition") + 1 if "Disposition" in df.columns else None

    colour_map = {
        "APPROVED":           COLOUR["approved_bg"],
        "APPROVED_AS_NOTED":  COLOUR["approved_bg"],
        "REVISE_AND_RESUBMIT": COLOUR["revise_bg"],
        "REJECTED":           COLOUR["rejected_bg"],
    }
    for r_idx, sub in enumerate(submittals, start=2):
        if sub.is_overdue(today):
            colour = COLOUR["overdue_bg"]
        else:
            colour = colour_map.get(sub.disposition)
        if colour:
            for c_idx in range(1, n_cols + 1):
                ws.cell(row=r_idx, column=c_idx).fill = PatternFill("solid", fgColor=colour)


def _highlight_all_rows(ws, df: pd.DataFrame, colour: str) -> None:
    for r_idx in range(2, len(df) + 2):
        for c_idx in range(1, len(df.columns) + 1):
            ws.cell(row=r_idx, column=c_idx).fill = PatternFill("solid", fgColor=colour)


def _write_rfi_summary(ws, log: "CommunicationLog", today: date) -> None:
    """Write summary statistics to a worksheet."""
    rfis = log.rfis
    ws.title = "RFI Summary"
    rows = [
        ("Project", log.project_name),
        ("Project ID", log.project_id),
        ("Report Date", str(today)),
        ("", ""),
        ("TOTAL RFIs", len(rfis)),
        ("Open", sum(1 for r in rfis if r.status not in
                     ("CLOSED_ANSWERED","CLOSED_VOID","CLOSED_SUPERSEDED"))),
        ("Answered", sum(1 for r in rfis if r.status == "ANSWERED")),
        ("Closed", sum(1 for r in rfis if "CLOSED" in r.status)),
        ("Overdue", sum(1 for r in rfis if r.is_overdue(today))),
        ("", ""),
        ("BY PRIORITY", ""),
        ("FATAL", sum(1 for r in rfis if r.priority == "FATAL")),
        ("HIGH", sum(1 for r in rfis if r.priority == "HIGH")),
        ("ADVISORY", sum(1 for r in rfis if r.priority == "ADVISORY")),
    ]
    for row_idx, (label, value) in enumerate(rows, start=1):
        ws.cell(row=row_idx, column=1, value=label).font = Font(bold=True)
        ws.cell(row=row_idx, column=2, value=value)
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 30
```

---

## Overdue Detection

```python
from datetime import date, timedelta

def overdue_report(log: CommunicationLog,
                    as_of: date = None,
                    warn_days: int = 2) -> dict:
    """
    Generate an overdue report for RFIs and Submittals.
    warn_days: flag items due within this many days as 'warning'.
    """
    as_of   = as_of or date.today()
    warning_horizon = as_of + timedelta(days=warn_days)

    rfi_overdue  = [r for r in log.rfis if r.is_overdue(as_of)]
    rfi_warning  = [r for r in log.rfis
                     if (r.status in ("ISSUED","UNDER_REVIEW")
                         and r.response_due
                         and as_of <= r.response_due <= warning_horizon)]

    sub_overdue  = [s for s in log.submittals if s.is_overdue(as_of)]
    sub_warning  = [s for s in log.submittals
                     if (s.status in ("NOT_SUBMITTED","SUBMITTED","UNDER_REVIEW")
                         and s.submit_by
                         and as_of <= s.submit_by <= warning_horizon
                         and s.disposition not in ("APPROVED","APPROVED_AS_NOTED"))]

    report = {
        "as_of":          str(as_of),
        "rfi_overdue":    [(r.rfi_number, r.subject, r.days_overdue(as_of))
                           for r in rfi_overdue],
        "rfi_warning":    [(r.rfi_number, r.subject, str(r.response_due))
                           for r in rfi_warning],
        "sub_overdue":    [(s.submittal_number, s.description,
                            (as_of - s.submit_by).days if s.submit_by else None)
                           for s in sub_overdue],
        "sub_warning":    [(s.submittal_number, s.description, str(s.submit_by))
                           for s in sub_warning],
    }

    print(f"Overdue Report — {as_of}")
    print(f"  RFIs overdue:      {len(rfi_overdue)}")
    print(f"  RFIs due in {warn_days}d:  {len(rfi_warning)}")
    print(f"  Submittals overdue: {len(sub_overdue)}")
    print(f"  Submittals due in {warn_days}d: {len(sub_warning)}")

    for num, subj, days in report["rfi_overdue"]:
        print(f"  ⚠ RFI {num} ({days}d overdue): {subj}")

    return report
```

---

## Transmittal Package

```python
from pathlib import Path
import json
from datetime import date

def generate_rfi_transmittal(rfi: RFIRecord,
                               output_dir: str,
                               attachments_dir: str = None) -> dict:
    """
    Generate a formal RFI transmittal package:
    - JSON record (machine-readable)
    - Plain text transmittal letter
    Returns dict with paths to generated files.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # JSON record
    json_path = out / f"{rfi.rfi_number}.json"
    record = {
        "rfi_number":     rfi.rfi_number,
        "project_id":     rfi.project_id,
        "project_name":   rfi.project_name,
        "priority":       rfi.priority,
        "discipline":     rfi.discipline,
        "spec_section":   rfi.spec_section,
        "drawing_ref":    rfi.drawing_ref,
        "subject":        rfi.subject,
        "question":       rfi.question,
        "background":     rfi.background,
        "date_issued":    str(rfi.date_issued),
        "response_due":   str(rfi.response_due),
        "issued_by":      rfi.issued_by,
        "issued_to":      rfi.issued_to,
        "status":         rfi.status,
        "attachments":    rfi.attachments,
    }
    json_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    # Plain text transmittal
    txt_path = out / f"{rfi.rfi_number}_transmittal.txt"
    transmittal = (
        f"REQUEST FOR INFORMATION\n"
        f"{'='*60}\n"
        f"RFI Number:      {rfi.rfi_number}\n"
        f"Project:         {rfi.project_name} ({rfi.project_id})\n"
        f"Priority:        {rfi.priority}\n"
        f"Discipline:      {rfi.discipline}\n"
        f"Spec Section:    {rfi.spec_section}\n"
        f"Drawing Ref:     {rfi.drawing_ref}\n"
        f"Subject:         {rfi.subject}\n"
        f"{'─'*60}\n"
        f"Date Issued:     {rfi.date_issued}\n"
        f"Response Due:    {rfi.response_due}\n"
        f"Issued By:       {rfi.issued_by}\n"
        f"Issued To:       {rfi.issued_to}\n"
        f"{'─'*60}\n"
        f"QUESTION:\n{rfi.question}\n\n"
        f"BACKGROUND:\n{rfi.background}\n"
        f"{'─'*60}\n"
        f"Attachments: {', '.join(rfi.attachments) or 'None'}\n"
        f"{'='*60}\n"
        f"[RESPONSE SECTION — TO BE COMPLETED BY {rfi.issued_to.upper()}]\n\n"
        f"Response:\n\n\n"
        f"Answered By:     ______________________  Date: ____________\n"
        f"Cost Impact:     ______________________\n"
        f"Schedule Impact: ______________________\n"
    )
    txt_path.write_text(transmittal, encoding="utf-8")

    return {"json": str(json_path), "transmittal": str(txt_path)}
```

---

## Scope Linkage

```python
def link_rfi_to_scope(rfi: RFIRecord,
                       scope_items: list,
                       session_state) -> list[str]:
    """
    Propagate RFI answer back to linked scope items.
    Updates evidence status and cost-ability where answer resolves ambiguity.
    Returns list of updated scope item IDs.
    """
    updated = []

    if rfi.status not in ("ANSWERED", "CLOSED_ANSWERED"):
        print(f"RFI {rfi.rfi_number} not yet answered — no propagation")
        return []

    for item in scope_items:
        if item.item_id in rfi.affected_scope:
            # If item was AMBIGUOUS or MISSING_UPSTREAM, answer may resolve it
            if item.evidence_status in ("AMBIGUOUS", "MISSING_UPSTREAM", "CONTRADICTORY"):
                item.evidence_status = "VERIFIED"
                item.rfi_required    = False
                item.rfi_id          = rfi.rfi_number
                if item.cost_ability == "NOT_COSTABLE":
                    item.cost_ability = "COSTABLE"
                updated.append(item.item_id)

    if updated and session_state:
        from SKILL_LLM_SESSION_STATE import propagate_change
        propagate_change(
            state              = session_state,
            changed_register   = "friction_log",
            changed_entry_id   = rfi.source_entry_id,
            change_description = f"{rfi.rfi_number} answered — scope items updated"
        )

    print(f"Linked {rfi.rfi_number} answer → {len(updated)} scope items updated")
    return updated


def build_scope_rfi_matrix(scope_items: list,
                            rfis: list[RFIRecord]) -> pd.DataFrame:
    """
    Build a cross-reference matrix: scope items × RFIs.
    Useful for bid scope review and GC coordination.
    """
    rows = []
    rfi_lookup = {r.rfi_number: r for r in rfis}

    for item in scope_items:
        if not item.rfi_required and not item.rfi_id:
            continue
        rfi = rfi_lookup.get(item.rfi_id) if item.rfi_id else None
        rows.append({
            "Scope Item":     item.item_id,
            "Trade":          item.trade,
            "Description":    item.description[:80],
            "RFI #":          item.rfi_id or "pending",
            "RFI Status":     rfi.status if rfi else "not issued",
            "RFI Priority":   rfi.priority if rfi else "",
            "Days Overdue":   rfi.days_overdue() if rfi else "",
            "Blocked":        "YES" if item.cost_ability == "NOT_COSTABLE" else "",
        })

    return pd.DataFrame(rows)
```

---

## Submittal Schedule

```python
def generate_submittal_schedule(spec_sections: list[dict],
                                  project_start: date,
                                  review_days: int = 14) -> list[SubmittalRecord]:
    """
    Generate a submittal schedule from a list of spec section dicts.
    Each dict: {"section", "title", "type", "lead_time_days",
                "required_on_site", "submitted_by", "long_lead", "critical_path"}
    Numbers submittals sequentially: SUB-0001, SUB-0002, ...
    """
    submittals = []
    for i, spec in enumerate(spec_sections, start=1):
        required = spec.get("required_on_site")
        if isinstance(required, str):
            from datetime import datetime
            required = datetime.strptime(required, "%Y-%m-%d").date()

        sub = SubmittalRecord(
            submittal_number   = f"SUB-{i:04d}",
            project_id         = spec.get("project_id", ""),
            spec_section       = spec["section"],
            spec_section_title = spec["title"],
            submittal_type     = spec.get("type", "SHOP_DRAWING"),
            description        = spec.get("description", spec["title"]),
            manufacturer       = spec.get("manufacturer", ""),
            model_number       = spec.get("model_number", ""),
            required_on_site   = required,
            lead_time_days     = spec.get("lead_time_days", 0),
            submitted_by       = spec.get("submitted_by", ""),
            long_lead          = spec.get("long_lead", False),
            critical_path      = spec.get("critical_path", False),
        )
        sub.compute_submit_by(review_days=review_days)
        submittals.append(sub)

    # Sort by submit_by date
    submittals.sort(key=lambda s: s.submit_by or date.max)
    return submittals
```

---

## Metrics and Dashboard

```python
def compute_log_metrics(log: CommunicationLog,
                          as_of: date = None) -> dict:
    """Compute KPIs for the RFI and Submittal logs."""
    as_of    = as_of or date.today()
    rfis     = log.rfis
    subs     = log.submittals

    answered = [r for r in rfis if r.date_answered and r.date_issued]
    avg_response = (
        sum((r.date_answered - r.date_issued).days for r in answered) / len(answered)
        if answered else None
    )

    reviewed = [s for s in subs
                if s.date_reviewed and s.date_submitted
                and s.disposition in ("APPROVED","APPROVED_AS_NOTED")]
    avg_review = (
        sum((s.date_reviewed - s.date_submitted).days for s in reviewed) / len(reviewed)
        if reviewed else None
    )

    first_pass = [s for s in subs
                   if s.revision == 0 and s.disposition == "APPROVED"]

    return {
        "rfi": {
            "total":          len(rfis),
            "open":           len([r for r in rfis if r.status in ("ISSUED","UNDER_REVIEW")]),
            "answered":       len([r for r in rfis if r.status == "ANSWERED"]),
            "closed":         len([r for r in rfis if "CLOSED" in r.status]),
            "overdue":        len([r for r in rfis if r.is_overdue(as_of)]),
            "fatal":          len([r for r in rfis if r.priority == "FATAL"]),
            "avg_response_days": round(avg_response, 1) if avg_response else None,
        },
        "submittal": {
            "total":               len(subs),
            "approved":            len([s for s in subs if s.disposition == "APPROVED"]),
            "approved_as_noted":   len([s for s in subs if s.disposition == "APPROVED_AS_NOTED"]),
            "revise_resubmit":     len([s for s in subs if s.disposition == "REVISE_AND_RESUBMIT"]),
            "overdue":             len([s for s in subs if s.is_overdue(as_of)]),
            "long_lead":           len([s for s in subs if s.long_lead]),
            "first_pass_approval": len(first_pass),
            "avg_review_days":     round(avg_review, 1) if avg_review else None,
        }
    }
```

---

## Validation & QA

```python
def validate_log(log: CommunicationLog) -> dict:
    errors, warnings = [], []
    today = date.today()

    # Duplicate number check
    rfi_nums = [r.rfi_number for r in log.rfis]
    if len(rfi_nums) != len(set(rfi_nums)):
        errors.append("DUPLICATE RFI numbers detected")

    sub_nums = [s.submittal_number for s in log.submittals]
    if len(sub_nums) != len(set(sub_nums)):
        errors.append("DUPLICATE Submittal numbers detected")

    # Answered RFIs must have response text
    answered_no_text = [r for r in log.rfis
                         if r.status == "ANSWERED" and not r.response]
    if answered_no_text:
        warnings.append(f"{len(answered_no_text)} ANSWERED RFIs with no response text")

    # Approved submittals must have review date
    approved_no_date = [s for s in log.submittals
                         if s.disposition in ("APPROVED","APPROVED_AS_NOTED")
                         and not s.date_reviewed]
    if approved_no_date:
        warnings.append(f"{len(approved_no_date)} approved submittals missing review date")

    # Fatal RFIs should not be open > 7 days
    fatal_stale = [r for r in log.rfis
                    if r.priority == "FATAL"
                    and r.status in ("ISSUED","UNDER_REVIEW")
                    and r.date_issued
                    and (today - r.date_issued).days > 7]
    if fatal_stale:
        errors.append(f"{len(fatal_stale)} FATAL RFIs open > 7 days without response")

    # Submittals missing submit_by dates
    no_date = [s for s in log.submittals if not s.submit_by]
    if no_date:
        warnings.append(f"{len(no_date)} submittals missing submit_by date — run compute_submit_by()")

    print(f"Log Validation — {log.project_id}")
    print(f"  RFIs: {len(log.rfis)}  |  Submittals: {len(log.submittals)}")
    for e in errors:   print(f"  ERROR: {e}")
    for w in warnings: print(f"  WARN:  {w}")
    print(f"  Verdict: {'FAIL' if errors else 'WARN' if warnings else 'PASS'}")
    return {"pass": not errors, "errors": errors, "warnings": warnings}
```

### QA Checklist

- [ ] No duplicate RFI or submittal numbers
- [ ] All FATAL RFIs issued within 24 hours of discovery
- [ ] All RFIs linked to a source register entry (friction_log, contradiction_register, etc.)
- [ ] All ANSWERED RFIs have response text and `date_answered`
- [ ] All APPROVED submittals have `date_reviewed` and `disposition`
- [ ] All submittals have `submit_by` computed — run `compute_submit_by()` on schedule generation
- [ ] Long-lead submittals flagged and sorted to top of schedule
- [ ] Overdue report run weekly — escalate FATAL overdue items same day
- [ ] RFI answers propagated to linked scope items via `link_rfi_to_scope()`
- [ ] Excel export reviewed in Excel before delivery — conditional formatting confirmed

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| RFI renumbered after issue | Number changed to fill gap | Never renumber — void the original, issue new with note "supersedes RFI-XXX" |
| Submittal approved but work wrong | `APPROVED_AS_NOTED` not tracked — notes not distributed | Always attach reviewer's marked-up document; log `review_comments` field |
| Overdue items not caught | `is_overdue()` not called on report runs | Schedule weekly `overdue_report()` call; alert on any result > 0 |
| RFI answer doesn't reach field | Response stored in log but not transmitted | Generate transmittal package for every answered RFI; distribute to affected subs |
| Submit-by date impossible | Long lead time not subtracted | Call `compute_submit_by()` with `lead_time_days` populated; flag negatives immediately |
| Scope item still blocked after RFI answered | `link_rfi_to_scope()` not called | Run linkage propagation after every RFI status change to ANSWERED |
| Excel formatting broken | Row colour applied before data | Apply `_write_dataframe_to_sheet()` before colour functions |

---

## Dependencies

```bash
pip install openpyxl pandas
# For Word transmittal documents: see SKILL_DOC_WORD_DOCX
# For PDF transmittal: see SKILL PDF
```
