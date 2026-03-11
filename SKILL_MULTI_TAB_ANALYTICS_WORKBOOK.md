---
name: multi-tab-analytics-workbook
description: "Use this skill when creating .xlsx workbooks with multiple sheets, charts, pivot tables, conditional formatting, or data validation. Trigger on any Excel output request involving more than raw data — dashboards, reports, trackers, or analytical workbooks."
---

# Multi-Tab Analytics Workbook SKILL

## Quick Reference

| Task | Library |
|------|---------|
| Create multi-sheet workbook | `openpyxl` |
| DataFrames → sheets | `pandas` + `openpyxl` engine |
| Charts | `openpyxl.chart` |
| Conditional formatting | `openpyxl.formatting` |
| Data validation | `openpyxl.worksheet.datavalidation` |
| Formulas | String cell values starting with `=` |

---

## Multi-Sheet Workbook Structure

```python
# pip install openpyxl --break-system-packages
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()

# Rename default sheet
ws_summary = wb.active
ws_summary.title = "Summary"

# Add sheets
ws_data = wb.create_sheet("Raw Data")
ws_charts = wb.create_sheet("Charts")
ws_config = wb.create_sheet("Config")

# Reorder sheets
wb.move_sheet("Summary", offset=0)  # Move to front
```

---

## Styled Header Row

```python
from openpyxl.styles import Font, PatternFill, Alignment

def style_header_row(ws, headers, row=1):
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="1E2761")  # Navy
    header_align = Alignment(horizontal="center", vertical="center")

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    ws.row_dimensions[row].height = 20
```

---

## Pandas → Multiple Sheets

```python
import pandas as pd

with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='Summary', index=False)
    df_detail.to_excel(writer, sheet_name='Detail', index=False)
    df_lookup.to_excel(writer, sheet_name='Lookups', index=False)
    
    # Access workbook for further styling
    wb = writer.book
    ws = writer.sheets['Summary']
    # ... apply styles
```

---

## Column Width Auto-Fit

```python
def auto_fit_columns(ws, min_width=8, max_width=40):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, min_width), max_width)
```

---

## Conditional Formatting

```python
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule
from openpyxl.styles import PatternFill

# Color scale (green-yellow-red)
ws.conditional_formatting.add('D2:D100',
    ColorScaleRule(
        start_type='min', start_color='63BE7B',
        mid_type='percentile', mid_value=50, mid_color='FFEB84',
        end_type='max', end_color='F8696B'
    )
)

# Highlight cells > threshold
red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
ws.conditional_formatting.add('E2:E100',
    CellIsRule(operator='greaterThan', formula=['10000'], fill=red_fill)
)
```

---

## Bar Chart

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.type = "col"
chart.title = "Monthly Revenue"
chart.y_axis.title = "Amount ($)"
chart.x_axis.title = "Month"
chart.style = 10

data = Reference(ws_data, min_col=2, min_row=1, max_row=13)
cats = Reference(ws_data, min_col=1, min_row=2, max_row=13)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.shape = 4
chart.width = 20
chart.height = 12

ws_charts.add_chart(chart, "B2")
```

---

## Freeze Panes + Filters

```python
# Freeze header row
ws.freeze_panes = 'A2'

# Auto-filter on header row
ws.auto_filter.ref = ws.dimensions
```

---

## Data Validation (Dropdown)

```python
from openpyxl.worksheet.datavalidation import DataValidation

dv = DataValidation(
    type="list",
    formula1='"Option A,Option B,Option C"',
    allow_blank=True
)
dv.error = "Invalid selection"
dv.errorTitle = "Error"
ws.add_data_validation(dv)
dv.add("C2:C100")
```

---

## CLI Verification

```bash
# Verify file validity
python -c "
from openpyxl import load_workbook
wb = load_workbook('output.xlsx')
print('Sheets:', wb.sheetnames)
for name in wb.sheetnames:
    ws = wb[name]
    print(f'  {name}: {ws.max_row} rows x {ws.max_column} cols')
"

# Extract to CSV for data check
python -c "
import pandas as pd
xl = pd.ExcelFile('output.xlsx')
for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    print(f'{sheet}: {df.shape}')
    print(df.head(3))
"
```

---

## QA Checklist

- [ ] All expected sheets present with correct names
- [ ] Header rows styled and frozen
- [ ] Column widths appropriate (not truncated, not excessive)
- [ ] Formulas calculate correctly (no `#REF!`, `#VALUE!`, `#DIV/0!`)
- [ ] Charts reference correct data ranges
- [ ] Conditional formatting applies to correct ranges
- [ ] Data validation dropdowns functional
- [ ] No placeholder data in final output
- [ ] File opens without repair prompt in Excel

---

## Common Mistakes to Avoid

- Forgetting `index=False` in pandas export
- Off-by-one errors in chart `Reference` ranges (openpyxl is 1-indexed)
- Applying styles after data is written (must style cell objects, not values)
- Using merged cells with auto-filter (causes errors)
- Hardcoding column letters instead of using `get_column_letter()`

---

## Dependencies

```bash
pip install openpyxl --break-system-packages
pip install pandas --break-system-packages
```
