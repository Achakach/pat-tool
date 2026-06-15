# Fix: PNG Still Breaking + Site Label Not Getting Its Own Page

## TL;DR

> **Quick Summary**: Fix two bugs in `insert_png()` — missing overflow guard for first image of a site (PNG splits across pages) and label created before overflow check (label stranded mid-page). Restructure function so `rows_needed` is calculated before label creation, and overflow guard keeps label+image together.

> **Root Cause**: `insert_png()` created the label BEFORE calculating `rows_needed`, so no overflow check existed for the first image. When the first image was tall enough to cross a page boundary, it split. Additionally, when the overflow push DID happen (for subsequent images via `insert_png_no_label`), the previous site's label was already locked in place — causing the "label not getting its own page" appearance.

> **Fix**: Reorder `insert_png()` so `rows_needed` is calculated early (before label creation), then add an overflow guard that pushes the entire label+image group to the next page when it won't fit.

## Work Objectives

### Core Objective
Ensure EVERY image (first or subsequent) is guarded against page-boundary splitting, and site labels always start at the top of a fresh page.

### Concrete Deliverables
- `5-png-inserter/src/inserter.py` — restructured `insert_png()` with overflow guard

---

## TODOs

- [x] 1. **Restructure `insert_png()` — move rows_needed before label, add overflow guard**

  **What to do**:
  - In `insert_png()` (currently lines 98-151 in `5-png-inserter/src/inserter.py`):
    1. Move image dimension reading + `rows_needed` calculation to AFTER the PNG dimension read (lines 109-112) but BEFORE the label creation (line 120). This means moving lines 131-143 up to right after line 112.
    2. After the site-break logic (lines 114-118), add an overflow guard block:
       ```python
       # Overflow guard: if label+image won't fit, push to next page boundary
       if page_rows is not None:
           img_end = start_row + 1 + gap_rows + rows_needed
           page_end = ((start_row - 1) // page_rows + 1) * page_rows
           if img_end > page_end:
               start_row = page_end + 1  # push label+image group to next page
       ```
    3. The label creation (lines 120-129) and image placement (lines 145-147) remain in place — they now use the possibly-pushed `start_row`.
    4. Remove the moved code from its old position (avoid duplication).

  **Key behavior**: 
  - First site at purge_from: no site-break snap, but overflow guard still protects the first image
  - Subsequent sites: site-break snap + overflow guard (both can push independently)
  - Label and first image stay together — never split across pages

  **Must NOT do**:
  - Do NOT change `insert_png_no_label()` — its overflow guard is already correct
  - Do NOT change the site-break snap formula
  - Do NOT remove the `Break(id=start_row)` insertion

  **Verification**:
  ```bash
  cd 5-png-inserter && python -m pytest tests/ -v
  ```
  Expected: 31 passed (existing tests should still pass; the fix is additive protection, not behavior change)

  **QA**: Run `insert.py` with `page_break_before_label: true`, verify:
  - Multi-site sheets: breaks exist, labels at page starts
  - Tall images: pushed to next page, not split
  - `page_break_before_label: false`: zero behavioral change (backward compat)

  **Commit**: `fix(inserter): add overflow guard in insert_png to prevent image splitting`

- [x] 2. **Run full test suite + integration QA**

  **What to do**:
  - `cd 5-png-inserter && python -m pytest tests/ -v` → 31 passed
  - Enable feature, run `python insert.py`, verify output XLSX has breaks and no split images
  - Disable feature, re-run, verify backward compat

---

## Success Criteria

```bash
cd 5-png-inserter
python -m pytest tests/ -v                    # Expected: 31 passed
python insert.py                               # Expected: runs, breaks in multi-site sheets
```
