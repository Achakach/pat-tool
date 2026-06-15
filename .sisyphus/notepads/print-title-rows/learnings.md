# Learnings — print-title-rows

## Conventions
- Debug prints go to stderr: `print(f"[DEBUG] ...", file=sys.stderr)`
- Warnings go to stderr: `print(f"WARNING: ...", file=sys.stderr)`
- Config keys in config.json follow `_comment` naming pattern
- All new function params use keyword defaults (e.g., `header_count=0`)
- `_calc_page_rows()` MUST NOT be modified — header_count flows separately
- TDD: RED (failing test) → GREEN (minimal impl) → REFACTOR

## Gotchas
- Snap formula offset MUST be `-2`, not `-1` (Metis-identified boundary bug)
- `_setup_a4_print` call is at insert.py line 177, not 178 (Momus noted off-by-1)
- `_setup_a4_print` debug print says `autoPageBreaks=False` but code sets `True`
- Test fixture XLSX in `5-png-inserter/xlsx/` may be locked → use individual tests
- openpyxl auto-prefixes `$` to print_title_rows (stored as `"$1:$6"` not `"1:6"`)
- `_parse_print_title_rows` returns `(end, value)` — for `"1:N"` this equals `end - start + 1`; for non-1-start ranges, fix needed: `end - start + 1`

## Wave 1 Complete
- 7 new tests + 31 existing = 38 passing
- Duplicate `TestPrintTitleRows` class bug found and fixed (renamed Task 2's class to `TestSetupA4PrintTitleRows`)
- `test_fixture.xlsx` accidentally modified by tests — restored via git checkout
- openpyxl stores `print_title_rows` with `$` prefix: setting `"1:6"` → stored as `"$1:$6"`
- Default param value `None` in `_setup_a4_print` preserves backward compat for all existing callers
- Tests import from `insert` directly (not `src.inserter`) via conftest.py adding tool root to sys.path
- `capsys.readouterr().err` captures stderr for warning tests
- `_parse_print_title_rows(value, page_rows=None)` is a module-level function in insert.py
- Degenerate check: warn when content_rows < 2 (header fills nearly entire page)
- Config key pattern: `"print_title_rows": null` + `"_comment_print_title_rows": "..."`
- `header_count` param added to `insert_png_no_label()` — keyword default `0`, inserted between `page_rows` and closing paren
- No-label variant has NO snap logic — overflow guard only (no `+1` for label row in `img_end`)
- Header-aware overflow guard: when `start_row <= page_rows`, `page_end = page_rows`; when beyond, uses `content_rows` for offset calc
- RED failure for header_count test: `TypeError: got an unexpected keyword argument 'header_count'`
- Task 5 (no-label) and Task 4 (label variant) share header_count overflow logic but differ: no-label has no `+1` in `img_end` and no snap

## Task 3 Complete — Snap formula with header_count
- `header_count=0` param added to `insert_png()` at line 116-117, BETWEEN `purge_from=0` and closing `)`
- Snap logic (lines 146-163) replaced with header-aware version using `-2` offset
- `start_row <= page_rows` branch handles first-page snap: `page_end = page_rows + 1` (row 53 for 52-row pages)
- `else` branch: `offset = start_row - page_rows - 2`, `pages_after = offset // content_rows + 1`, `page_end = page_rows + 1 + pages_after * content_rows`
- Debug print at line 124 updated to include `header_count`
- Snap debug prints updated to show `header_count` and `content_rows` when headers active
- `purge_from` guard (`start_row > purge_from`) unchanged
- 3 new tests in `TestPrintTitleRows` class: `test_snap_with_headers_keeps_boundary`, `test_snap_with_headers_mid_page`, `test_snap_no_headers_unchanged`
- 42 tests pass total (38 existing + 3 new + 1 pre-existing overflow test)
- Math verification: row 53 (boundary) → `-1//46 + 1 = 0` pages_after → stays at 53; row 54 → `0//46 + 1 = 1` → snaps to 99

## Task 4 Complete — Header-aware overflow guard in insert_png()
- `header_count=0` param already present (Task 3 added in inserter.py line 117)
- Overflow guard (now lines 165-185) replaced with header-aware version
- `header_count > 0`: `content_rows = page_rows - header_count`, then `start_row <= page_rows` → `page_end = page_rows`; else uses offset calc with `content_rows`
- `header_count == 0`: original formula `((start_row - 1) // page_rows + 1) * page_rows` preserved exactly
- Debug prints include `header_count` and `content_rows` when headers active
- `img_end` formula unchanged: `start_row + 1 + gap_rows + rows_needed`
- 2 new tests added to `TestPrintTitleRows` class: `test_overflow_with_headers_pushes` (header_count=2), `test_overflow_no_headers_unchanged` (header_count=0)
- Both new tests use `purge_from=1` (snap fires first), `start_row=9`, `page_rows=10`, gap_rows=0, 100px PNG
- `test_overflow_no_label_with_headers` already existed (Task 5 pre-work)
- All 44 tests pass (38 existing + 6 new across Tasks 3-5)

## Task 6 Complete — Wire header_count through insert.py call chain
- Added config reading at line 71-73: `print_title_rows_raw` → `_parse_print_title_rows()` → `(header_count, print_title_rows_str)`
- `_setup_a4_print(wb[sheet_name], print_title_rows_str)` at line 211 — passes the raw string like `"1:6"` or `None`
- `insert_png(... header_count=header_count, ...)` at line 231 — added between `page_rows=pr_val` and `purge_from`
- `insert_png_no_label(... header_count=header_count, ...)` at line 236 — added between `page_rows=pr_val` and `)`
- Warning at line 241-243: computes `content_rows = pr_val - header_count if pr_val and header_count else pr_val`, uses "effective capacity" wording
- All 5 changes verified by running `python insert.py` — completes successfully processing 54 PNGs across 6 files
- Debug output shows `header_count=0` (since config has no print_title_rows set yet) and `print_title_rows=None` flowing correctly

## Task 7 Complete — Integration tests + backward compat verification
- 45 tests pass: 14 matcher + 31 page_breaks (17 original + 1 new integration + 13 from Tasks 1-6)
- New test: `test_full_pipeline_with_headers` in `TestPrintTitleRows` class
  - Multi-sheet workbook (Sheet, Sheet2)
  - Exercises: no-snap (start_row==purge_from), no-label overflow, snap with header_count=3, multi-sheet isolation
  - Verified: label@5 on both sheets (no-snap), label@18 on Sheet (snap after gap)
  - Uses `insert_png()` and `insert_png_no_label()` — all header_count=3, page_rows=10, gap_rows=0
- **print_title_rows end > purge_from**: Currently produces NO warning/crash. The `header_count` (end row) and `purge_from` operate independently — `header_count` only affects snap/overflow math, `purge_from` controls which rows get purged. No explicit check exists for header extending past purge_from row. This is by design (they serve different purposes).
- `test_fixture.xlsx` modified by test runs (185 byte binary diff) — restored via `git checkout`
- Backward compat verified: all `header_count=0` default params, existing tests pass unchanged
- Git diff: only +53 lines in `test_page_breaks.py` — zero existing test modifications

## F3 Complete — Excel COM Calibration QA
- Excel COM available — Full Calibration path executed
- Created 200-row XLSX: paperSize=9, margins matching _setup_a4_print, print_title_rows="1:6", autoPageBreaks=True
- COM HPageBreaks: Count=4, confirmed breaks at rows 53, 99 (indices 3-4 had DISP_E_BADINDEX — known COM limitation)
- Break positions validate content_rows=46 formula: page 1 rows 1-52, page 2 rows 53-98 → break at 53 and 99
- 45/45 pytest pass, insert.py null config → PASS, insert.py print_title_rows="1:3" → PASS
- _setup_a4_print correctly sets ws.print_title_rows = "$1:$6" (openpyxl auto-dollar-format)
- All evidence saved to .sisyphus/evidence/final-qa/
- VERDICT: APPROVE — all checks pass, no regressions
