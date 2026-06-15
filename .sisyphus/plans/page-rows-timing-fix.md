# Fix: Page Break Miscalculation — Label at Bottom of Page

## TL;DR

> **Quick Summary**: `_calc_page_rows()` runs before `_setup_a4_print()`, reading default margins (0.75") instead of the margins that `_setup_a4_print` configures (0.5"). This makes page_rows ~46 instead of ~51, placing breaks near the bottom of Excel's actual pages. Fix: calculate page_rows AFTER _setup_a4_print on each matched sheet.

> **Root Cause**: In `insert.py`, `page_rows_val` is calculated once per file from the first sheet's default margins. But `_setup_a4_print()` sets different margins (0.5" top/bottom) on each matched sheet AFTER the calculation. The mismatch causes breaks at wrong positions — labels appear at the bottom of printed pages.

## Work Objectives

### Core Objective
Calculate page_rows from the ACTUAL margins set by `_setup_a4_print()`, so page breaks align with Excel's true page boundaries.

---

## TODOs

- [x] 1. **Move page_rows calculation into the per-sheet purge block**

  **What to do**:
  - In `insert.py`, remove the file-level `page_rows_val` calculation at lines 154-160
  - Move `page_rows_val` calculation INSIDE the purge block (lines 180-189), AFTER `_setup_a4_print(wb[sheet_name])` is called
  - Store the calculated value in a new dict `sheet_page_rows = {}` keyed by sheet_name
  - When `page_break_enabled` is False, store `None` in the dict instead
  - Pass `sheet_page_rows.get(sheet_name)` (instead of `page_rows_val`) to `insert_png()` and `insert_png_no_label()` calls

  **Key behavior change**: Different sheets may have different margins → different page_rows. The dict tracks per-sheet values. The first sheet to be purged gets its page_rows calculated from the margins that `_setup_a4_print()` just set.

  **Must NOT do**:
  - Do NOT change `_calc_page_rows()` or `_setup_a4_print()` — they are correct
  - Do NOT change `insert_png()` or `insert_png_no_label()` — they are correct
  - Do NOT change margin values in `_setup_a4_print()`

  **Verification**:
  ```bash
  cd 5-png-inserter && python -m pytest tests/ -v
  ```
  Expected: 31 passed

- [x] 2. **Run integration QA — verify labels at top of page**

  **What to do**:
  - Enable `page_break_before_label: true`
  - Run `python insert.py`
  - Verify breaks are at correct positions: `(break.id - 1) % auto_calc_page_rows == 0` (within tolerance)
  - Verify labels are at the TOP of their pages (label row = break.id, image below)

---

## Success Criteria
```bash
cd 5-png-inserter
python -m pytest tests/ -v                    # Expected: 31 passed
python insert.py                               # Expected: breaks at page boundaries, labels at page tops
```
