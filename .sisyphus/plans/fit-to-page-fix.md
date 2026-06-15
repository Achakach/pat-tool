# Fix: Remove fitToPage — Let Manual Breaks Control Pages

## TL;DR

> **Quick Summary**: `_setup_a4_print()` sets `fitToWidth=1` and `fitToPage=True`, which causes Excel to override manual page breaks with its own scaling algorithm. Images still split and labels appear at bottom because Excel ignores our Break objects. Fix: remove fit-to-page settings so manual breaks are strictly respected.

> **Root Cause**: `fitToPage=True` in Excel causes the rendering engine to calculate its own page boundaries, overriding `autoPageBreaks=False` and any manual `Break` objects. This is an Excel-level behavior, not a code bug.

## Work Objectives

### Core Objective
Remove `fitToWidth`, `fitToHeight`, and `fitToPage` from `_setup_a4_print()` so manual page breaks inserted by `insert_png()` are respected by Excel during printing.

---

## TODOs

- [x] 1. **Remove fit-to-page settings from `_setup_a4_print()`**

  **What to do**:
  - In `5-png-inserter/src/inserter.py`, function `_setup_a4_print()`:
    - Remove lines 69-70: `ws.page_setup.fitToWidth = 1` and `ws.page_setup.fitToHeight = 0`
    - Remove lines 71-72: `from openpyxl.worksheet.properties import PageSetupProperties` and `ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)`
  - Keep: paperSize, orientation, autoPageBreaks=False, margins (lines 67-68, 73-77)
  - After the change, `_setup_a4_print()` should be ~7 lines:
    ```python
    def _setup_a4_print(ws):
        """Configure sheet for A4 portrait printing."""
        ws.page_setup.paperSize = 9
        ws.page_setup.orientation = 'portrait'
        ws.page_setup.autoPageBreaks = False
        ws.page_margins.left = 0.25
        ws.page_margins.right = 0.25
        ws.page_margins.top = 0.5
        ws.page_margins.bottom = 0.5
    ```

  **Must NOT do**:
  - Do NOT change margins, paperSize, or autoPageBreaks
  - Do NOT change `insert_png()`, `insert_png_no_label()`, or `_calc_page_rows()`
  - Do NOT change `insert.py`
  - Do NOT change any config.json values

  **Verification**:
  ```bash
  cd 5-png-inserter && python -m pytest tests/ -v
  ```
  Expected: at least the page break tests should pass. Tests that check fitToWidth/fitToHeight values may need updating.

- [x] 2. **Update tests for removed fit-to-page settings**

  **What to do**:
  - Check `5-png-inserter/tests/test_page_breaks.py` for tests that assert `fitToWidth` or `fitToHeight` values
  - Update assertions to match new behavior (no fit-to-page settings)
  - Specifically check:
    - `test_auto_page_breaks_disabled` — currently checks `ws.page_setup.autoPageBreaks is False` (should still pass)
    - Any test using `_setup_a4_print()` and checking fitToWidth/fitToHeight
  - Run full test suite to find any failures

  **Verification**:
  ```bash
  cd 5-png-inserter && python -m pytest tests/ -v
  ```
  Expected: all tests pass after updates

- [x] 3. **Integration QA — verify no image splits, labels at top in Excel**

  **What to do**:
  - Ensure `page_break_before_label: true` in config.json
  - Run `python insert.py` to generate fresh output
  - Verify output XLSX files:
    - Manual breaks present and aligned: `(break.id - 1) % 51 == 0`
    - Labels at page top: position 1 on their page
  - **Crucially**: open output in Excel → Print Preview → verify NO image splits and labels at page top
  - Test with test_fixture.xlsx which has the oversized images (60+ row images will still warn but shouldn't split mid-image)

  **Verification**:
  ```bash
  cd 5-png-inserter
  python -m pytest tests/ -v
  python insert.py
  # Then manually: open out/test_fixture.xlsx in Excel → Print Preview
  ```

---

## Success Criteria
```bash
cd 5-png-inserter
python -m pytest tests/ -v                    # Expected: all pass
python insert.py                               # Expected: no crashes
# Excel Print Preview: no image splits, labels at page top
```
