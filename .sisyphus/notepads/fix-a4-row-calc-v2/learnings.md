# Learnings

## Task 1: _detect_row_height helper
- Added `_detect_row_height(ws, fallback=None)` to `5-png-inserter/src/inserter.py`
- Uses MODE (Counter.most_common), not mean, for mixed-height templates
- Falls back to openpyxl's DEFAULT_ROW_HEIGHT (15.0)
- 4 unit tests in TestDetectRowHeight all pass
- Empty worksheet with active sheet defaults to max_row=1 (row_dimensions[1].height=None), correctly falls back — fix-a4-row-calc-v2

## Session: ses_126169309ffe6DiCk1LQuWmv9z
## Started: 2026-06-18T09:28:20Z
## Plan: .sisyphus/plans/fix-a4-row-calc-v2.md

## Conventions
- TDD: RED (fail) → GREEN (pass) per wave
- MODE sampling for row height detection
- `math.ceil()` without `+1` — ceil already rounds up
- `pixels_to_points()` from openpyxl replaces magic 0.75
- `DEFAULT_ROW_HEIGHT` (15.0) is fallback when no explicit heights

## Key Files
- `5-png-inserter/src/inserter.py` — all source changes
- `5-png-inserter/tests/test_page_breaks.py` — all test changes
- `5-png-inserter/config.json` — read-only reference

## Task 4: RED — update insert_png_no_label test assertions
- Updated 4 tests in `test_page_breaks.py` for rows_needed formula change:
  `max(1, int(display_h * 0.75 / 15) + 1)` → `max(1, math.ceil(pixels_to_points(display_h) / 15))`
- rows_needed changes: 60px PNG 4→3, 100px PNG 6→5
- `test_overflow_guard_pushes_image` (100px): 6→5, return 14→13 ✓ FAIL
- `test_multiple_small_images_fill_page` (60px): 4→3, r1=7→6, r2=13→11, r3=22→16. r3 no longer overflows (15≤15) ✓ FAIL
- `test_gap_rows_zero` (60px): 4→3, return 10→9, guard assertion ≥9 passes both ✓ PASS (lax)
- `test_overflow_no_label_with_headers` (100px): 6→5, return 17→16 ✓ FAIL
- RED phase confirmed: 3 FAIL (asserting new values vs old impl), 1 PASS (guard ≥9 covers both)
- Used exact `==` assertions where math is deterministic, kept `>=` for `gap_rows_zero` per task spec

## Task 5: Fix _calc_page_rows to use _detect_row_height
- Changed `_calc_page_rows` to use `_detect_row_height(ws)` instead of hardcoded `15`
- CORRECTION: `_detect_row_height` stays MODE (as plan specifies), NOT MAX
  - Mixed 5×24pt + 10×15pt: MODE=15.0, so ceil(769.89/15)=52
  - `test_calc_page_rows_mixed_mode` was updated to expect 52 (not 33)
- `Counter` import restored, function signature untouched
- Result: `TestDetectRowHeight` (4 tests) + `TestPageBreakConfig` (10 tests) = 14/14 PASS

## F2: Code Quality Review

### Tests: 57/57 PASS ✅
Full suite (test_cli 4, test_matcher 18, test_page_breaks 35) all green.

### Import check ✅
- `Counter` (inserter.py:12) — used line 29 in `_detect_row_height`
- `pixels_to_points` (inserter.py:13) — used lines 166, 259
- `DEFAULT_ROW_HEIGHT` (inserter.py:13) — used line 20 as fallback default
- Zero unused imports

### Magic numbers ✅
- No hardcoded `15` or `0.75` remaining in row calc logic (src/inserter.py)
- Paper height 841.89, 72 pts/inch, margin values are acceptable constants
- Row height now dynamically detected via `_detect_row_height()`

### Dead code / slop ✅
- No dead code, no commented-out blocks
- Debug `print()` to stderr: intentional per plan
- `_a4_print_setup_done` global: functional (suppresses duplicate debug)

### Lint: N/A
- basedpyright LSP not installed; manual review performed instead

### Minor concern (non-blocking)
- ~30 lines overflow/snap logic duplicated between `insert_png` (lines 169-209) and `insert_png_no_label` (lines 263-281)
- Out of scope for this fix; acceptable tech debt

### VERDICT: PASS — 0 quality issues, 0 regressions
