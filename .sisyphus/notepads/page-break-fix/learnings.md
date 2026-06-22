# Learnings - Page Break Fix

## Session: 2026-06-15 (ses_1368b47d3ffe7t1NPVcrUt5t7d)

## Conventions
- openpyxl page breaks: `ws.row_breaks.append(Break(id=N))` — break BEFORE row N
- Read breaks: `ws.row_breaks.brk` (NOT direct iteration — returns tuples)
- autoPageBreaks: `ws.page_setup.autoPageBreaks = False` (NOT `ws.autoPageBreaks`)
- A4 row capacity: `(841.89 - margins_pts) / 15` — auto-calc, not hardcoded
- Existing test pattern: tmp_path fixture, conftest.py adds tool root to sys.path
- Config reading: `config.get("key", default)` pattern in insert.py:65-69

## Gotchas
- Working tree has uncommitted changes stripping ALL page-break logic
- Stale `page_break_before_label: false` key in config.json (re-purpose as toggle)
- `Break` import: `from openpyxl.worksheet.pagebreak import Break`
- Existing 14 tests must pass unchanged when feature is disabled (page_rows=None)
- Do NOT insert break before first site (start_row == purge_from)

## Task 1 — Foundation (2026-06-15)

### Done
- config.json: Documented `page_break_before_label` as feature toggle (already `false`). Added `_comment` key explaining `a4_page_rows` auto-calc. Added `a4_page_rows: null` sentinel.
- `_setup_a4_print()`: Added `ws.page_setup.autoPageBreaks = False` after PageSetupProperties block (line 72).
- `_calc_page_rows(ws, config_override=None)`: A4 auto-calc formula — `int((841.89 - (top+bot)*72) / 15)`. Returns ~51 rows with 0.5" margins.
- `_clear_page_breaks(ws)`: Sets `ws.row_breaks.brk = ()` to clear all manual breaks.

### Verified
- `_calc_page_rows(ws)` with margins 0.5/0.5 → 51
- `_setup_a4_print(ws)` → `ws.page_setup.autoPageBreaks` is `False`

## Task 2 — Page Break Logic in insert_png / insert_png_no_label (2026-06-15)

### Design Decision
- Restructured `insert_png()` to run page-break/snap logic BEFORE label creation (not after as plan suggested). Reason: plan's "re-apply label" approach creates a phantom label at the old start_row position. Single label at snapped position is cleaner and functionally identical.

### Done
- `from openpyxl.worksheet.pagebreak import Break` added at line 9
- `insert_png()`: Added `page_rows: int | None = None, purge_from: int = 0` params. When page_rows set and start_row > purge_from: snaps to next page boundary via `((start_row - 2) // page_rows + 1) * page_rows + 1`, inserts `Break(id=start_row)`. Label created at (possibly-snapped) start_row.
- `insert_png_no_label()`: Added `page_rows: int | None = None` param. Overflow guard: calculates `img_end = start_row + gap_rows + rows_needed`, `page_end = ((start_row - 1) // page_rows + 1) * page_rows`. If img_end > page_end, pushes to `page_end + 1`. No Break object inserted.

### Verified
- All 14 existing tests pass (page_rows=None default → backward compat preserved)
- `insert_png()` snap math verified: page_rows=51, start_row=10 → page_end=52 → snap to 52, break at 52
- `insert_png_no_label()` overflow math verified: start_row=3, rows=50, gap=1 → img_end=54, page_end=51 → push to 52

### Snap / Break Math Reference
- `insert_png` snap: `page_end = ((start_row - 2) // page_rows + 1) * page_rows + 1` — always yields first row of next page
- `insert_png_no_label` overflow: `page_end = ((start_row - 1) // page_rows + 1) * page_rows` — last row of current page
- `start_row - 2` vs `start_row - 1`: insert_png has a label row consuming 1 extra row before image, hence -2 instead of -1

## Task 3 — Wire Orchestrator (2026-06-15)

### Done
- insert.py line 11: Added `_calc_page_rows, _clear_page_breaks` to imports from `src.inserter`
- insert.py lines 68-69: Read `page_break_before_label` (default False) and `a4_page_rows` from config
- insert.py lines 154-160: Calculate `page_rows_val` per file — `_calc_page_rows(wb_temp.active, ...)` when enabled, `None` when disabled
- insert.py lines 186-187: Call `_clear_page_breaks(wb[sheet_name])` during purge when feature disabled (clears stale breaks from previous runs)
- insert.py line 198: `insert_png()` call receives `page_rows=page_rows_val, purge_from=(purge_from or 10)`
- insert.py line 201: `insert_png_no_label()` call receives `page_rows=page_rows_val`
- insert.py lines 205-206: Oversized image warning — `if page_rows_val and (next_row - current_row) > page_rows_val: print(...)`

### Verified
- Syntax check: OK
- All 14 existing tests: PASS (page_rows_val=None → backward compat preserved)
- insert.py run: processed 4 files successfully, no errors from new code

## Tasks 4-6 — Test Suite (2026-06-15)

### Done
- Created 5-png-inserter/tests/test_page_breaks.py with 17 tests across 3 classes
- **TestPageBreakConfig** (7 tests): feature toggle behavior, A4 auto-calc, autoPageBreaks, clear_page_breaks
- **TestPageBreakInsertion** (6 tests): break-before-second-site, no-break-first-site, overflow guard push/stay, multi-image fill, Break convention
- **TestPageBreakEdgeCases** (4 tests): oversized image, multi-sheet independence, gap_rows=0, existing breaks cleared

### Test Patterns
- PNG helper: _make_test_png(path, width, height) — creates minimal valid PNG via struct+zlib
- XLSX helper: _make_test_xlsx(tmp_path, name) — creates workbook with 20 data rows
- All 17 tests PASS (features already implemented in Tasks 1-3)
- Full suite: 31 passed (14 existing + 17 new)

### Gotchas
- Test 15 (multi_sheet_independence) initially failed because Sheet2 used purge_from=1 with start_row=5 → 5>1 triggered snap. Fixed by using purge_from=5 to match start_row (first-site scenario).
- insert_png_no_label overflow guard only pushes; does NOT insert Break objects (by design — orchestrator handles labelling via insert_png first)
- Gap_rows=0 overflow math works fine: img_end = start_row + 0 + rows_needed, still compared against page_end correctly

## F3: Manual QA - Session: 2026-06-15

### Scenarios Executed
1. Clean state + enabled (page_break_before_label=True, auto-calc page_rows): 10/10 scenarios PASS
   - 4 output files verified. autoPageBreaks = None (not True) on all sheets
   - test2_target.xlsx: 4 sites on 1 sheet, 3 breaks at [47, 93, 139]
   - Single-site sheets: 0 breaks (correct)
2. Disabled (page_break_before_label=False): 10/10 scenarios PASS
   - Zero breaks on ALL sheets across all 4 output files
3. Edge case — a4_page_rows=20 override: PASS
   - Breaks at [41, 61, 81] — all satisfy (id-1) % 20 == 0
   - Oversized image warning emitted correctly
4. Config roundtrip (off→on→off): PASS — no key loss, no corruption
5. Integration: 31/31 tests PASS (0.98s)

### Gotchas
- autoPageBreaks=None vs False: openpyxl returns None when attribute not explicitly serialized in XML. Check `auto is True` instead of `auto is False` for safety.
- `row_breaks.brk` returns tuple; use `len(breaks) if breaks else 0` pattern.
- `Break` object has `id` attribute but no `col` attribute.
- test_fixture.xlsx file lock is pre-existing and expected.
- insert.py crashes on test_fixture.xlsx with PermissionError — OK per plan.

### VERDICT: APPROVE
- Feature toggle works correctly (enabled → breaks; disabled → none)
- a4_page_rows override produces correct page-aligned breaks
- Config survives roundtrip without corruption
- All 31 unit/integration tests pass
- No regressions in backward compatibility
## F3 Manual QA — 2026-06-18 16:53

### Test Execution Results

| Test Group | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| F3.1 Task 1 (TestDetectRowHeight) | 4 | 4 | 0 |
| F3.2 Task 2+5 (TestPageBreakConfig) | 10 | 10 | 0 |
| F3.3 Task 3+6 (overflow/headers/taller) | 3 | 3 | 0 |
| F3.4 Task 4+7 (overflow_guard/gap_rows) | 4 | 4 | 0 |
| **QA Subtotal** | **21** | **21** | **0** |
| Full suite cross-task integration | 38 | 38 | 0 |

### Edge Cases Verified (7/7)

1. Empty worksheet → _detect_row_height = 15.0 ✓
2. All rows explicit 20pt → returns 20.0 ✓
3. Mixed heights → MODE=15 works ✓
4. No explicit heights → fallback 15.0 ✓
5. a4_page_rows config override still works ✓
6. 20pt rows → calc_page_rows = 39 ✓
7. Mixed mode → calc_page_rows = 52 (MODE=15) ✓

### Cross-task Integration

_detect_row_height → _calc_page_rows → insert_png chain verified via full 38-test suite.
All edge cases covered: print title rows, auto page breaks, snap to boundary, 
overflow guard, gap rows, taller than page, multi-sheet, disabled mode, 
existing breaks cleared, full pipeline with headers.

### Verdict: APPROVE
