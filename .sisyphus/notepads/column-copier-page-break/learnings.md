
## Task 2: Config + wiring (2026-06-16)

- Added 4 config keys to config.json: page_break_enabled, 4_page_rows, print_title_rows, _comment_print
- Added import of _setup_a4_print, _calc_page_rows, _parse_print_title_rows from src.print_setup
- Parse config after columns = config["columns"]
- Call _setup_a4_print(tws, print_title_rows_str) after target sheet opens
- 8 existing tests still pass (they test src.columns, not src.print_setup)
- JSON validated successfully
- Note: src.print_setup.py not yet created (Task 1) — copier.py will fail at runtime until Task 1 completes

## Task 1: print_setup.py + tests (2026-06-16)

- TDD: RED (import error) → GREEN (7 pass) → REFACTOR (15 pass total)
- Copied 3 functions from 5-png-inserter, applied 3 bug fixes:
  - #8: `_parse_print_title_rows` returns `end-start+1` (was `end`)
  - #9: `_parse_print_title_rows` guards `content_rows < 1` → disables with `(0, None)`
  - #10: `_setup_a4_print` removed global `_a4_print_setup_done`, fixed debug string to `autoPageBreaks=True`, prints unconditionally
- New function `snap_gap_rows` for page-boundary snapping (used in Task 4)
- openpyxl stores `print_title_rows` as `"$1:$3"` internally (with $ signs)
- A4 page_rows: 52 (ceil(769.89/15)) — tests accept 49-53 range

## Task 4: snap_gap_rows wiring + tests (2026-06-16)

- Added 2 tests to `test_print_setup.py`: `TestSnapGapRows` class
  - `test_no_gap_when_content_at_page_start`: content at clean page boundary → gap=0
  - `test_inserts_gap_when_content_mid_page`: content mid-page → gap=2 to reach next boundary
- Wired `snap_gap_rows` into `copier.py` after paste loop:
  - `paste_end = paste_row` initialized before column loop
  - `paste_end = max(paste_end, dst_row)` after each column's while loop
  - After all columns: `gap = snap_gap_rows(paste_end, tws, page_rows, header_count)` then `tws.insert_rows(paste_end, gap)` if gap>0
  - Only activates when `page_break_enabled` is True
- Import updated: added `snap_gap_rows` to the `from src.print_setup import ...` line
- Final: 20/20 tests pass (18 existing + 2 new)
- Key design: snap happens ONCE after all columns finish pasting, not per-row
- `paste_end` tracks the row AFTER the last pasted row (dst_row is incremented past the last written row)

## Task 3: insert_rows in append mode (2026-06-16)

- Added 3 tests to `TestAppendInsertRows` in `tests/test_columns.py`
  - Tests verify openpyxl's `insert_rows()` behavior directly (correct level since copier call is one-liner)
  - `test_append_insert_rows_shifts_content`: content at row 10, paste 5 rows at row 5 → content shifts to row 15
  - `test_append_no_insert_rows_when_no_content_below`: empty target — insert_rows still works (no error)
  - `test_insert_rows_detects_content_at_paste_row`: content AT paste_row → shifts correctly
- Added `import tempfile, from pathlib import Path, from openpyxl import load_workbook` to test file
- insert_rows code inserted at copier.py line 160-183, AFTER append mode block, BEFORE `paste_end` and paste loop
- Guard: `paste_mode == "append" and page_break_enabled` — no insert_rows in overwrite or when disabled
- Guard: merged cell detection — skips insert_rows with stderr warning
- Guard: `src_data_rows > 0` — no insert when source has no data
- Counts source data rows by scanning sws from start_row until empty row
- All 20 tests pass (8 + 7 + 3 + 2)

## Task 5: Integration test + backward compat (2026-06-16)

- Added 1 integration test `test_full_append_with_page_break` to `TestAppendInsertRows`
- Test simulates full append pipeline: insert_rows → paste → snap_gap_rows
- Scenario: target content at row 9, 5 data rows, page_rows=10
  - insert_rows(3, 5): content shifts row 9→14
  - paste_end=8, snap_gap_rows: row 14 mid-page → gap=7
  - insert_rows(8, 7): content shifts row 14→21 (clean page 3 start)
- No changes to existing tests, config, fixtures, or source files
- Backward compat: `page_break_enabled: false` in config.json confirmed
- Final: 21/21 tests pass (8 columns + 4 insert_rows + 7 print_setup + 2 snap = 21)
- Pre-existing test counts: 8 columns base + 3 insert_rows (Task 3) + 7 print_setup (Task 1) + 2 snap (Task 4) + 1 integration (Task 5) = 21
