# Fix A4 Page Break Row Calculation v2

## TL;DR

> **Quick Summary**: Replace all hardcoded `15` (row height in pts) and `0.75` (pixel ratio) in tool 5's A4 page break and image span calculations with openpyxl's native `pixels_to_points()` and a `_detect_row_height()` helper that samples actual row heights from the template.
>
> **Deliverables**:
> - `_detect_row_height()` helper function in `inserter.py`
> - Updated `_calc_page_rows` using detected row height
> - Updated `insert_png` and `insert_png_no_label` using `pixels_to_points()` + detected height + `math.ceil()+1`
> - 8+ test assertion updates + new custom-row-height test fixtures
> - All 51 existing tests pass
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 2 waves
> **Critical Path**: T1 → T2/T3/T4 (in parallel) → T5/T6/T7 (in parallel) → T8

---

## Context

### Original Request
User wants the A4 page break / image row span calculation in tool 5 to work correctly on every computer, not just computers where templates happen to use Excel's default 15pt row height.

### Interview Summary
**Key Discussions**:
- **Scope**: Tool 5 only (`5-png-inserter/src/inserter.py`). Tool 3 deferred to follow-up.
- **Approach**: Use openpyxl's internal conversion utilities (`pixels_to_points()`, `DEFAULT_ROW_HEIGHT`) instead of magic numbers.
- **Test strategy**: TDD — write updated test expectations first (RED), then implement fixes (GREEN).
- **Root cause**: Hardcoded `15` assumes Calibri 11pt default. Real templates use different fonts/custom heights → wrong page boundaries.

**Research Findings**:
- **ZERO** existing code reads `ws.row_dimensions[r].height` — the codebase has never queried actual row heights.
- openpyxl's `pixels_to_points(value)` = `value * 72 / 96` = `value * 0.75` (functionally identical, but uses library API).
- openpyxl's `DEFAULT_ROW_HEIGHT = 15.0` is the canonical constant for the magic `15`.
- Current formula: `int(display_h * 0.75 / 15) + 1` — the `int()+1` pattern adds a safety margin that rounds up by 1 extra for exact multiples.
- **Critical design constraint** (from Metis): After `purge_sheet` deletes rows, `ws.row_dimensions[r].height` returns `None` for purged rows. We CANNOT sum actual heights at the insertion point. Must sample heights from existing template rows BEFORE purge.

### Metis Review
**Identified Gaps** (addressed):
- **Post-purge rows don't exist**: Cannot use `_rows_for_height(ws, start_row, ...)` at insertion point. Fixed by sampling row height from PRE-existing template rows (before purge_from) using a `_detect_row_height()` helper.
- **Two functions must agree**: `_calc_page_rows` and `rows_needed` MUST use the same detected row height. Single helper ensures consistency.
- **`int()+1` → `ceil()+1`**: Replace `int()` truncation with `math.ceil()` for correct rounding, preserve `+1` safety margin. Pure `ceil()` would drop safety for exact multiples.
- **MODE not MEAN**: Use most common row height (mode) not average, to handle mixed-height templates (e.g., header at 24pt, content at 15pt).
- **Empty template edge case**: If NO rows have explicit heights, fall back to `DEFAULT_ROW_HEIGHT` (15.0).
- **Config override preserved**: `a4_page_rows` still bypasses auto-calc when set.

---

## Work Objectives

### Core Objective
Replace hardcoded row height (15pt) and pixel ratio (0.75) in tool 5's `_calc_page_rows`, `insert_png`, and `insert_png_no_label` with openpyxl's native conversion utilities and a sampled row height from the template, so page breaks and image spans are correct regardless of template row height settings.

### Concrete Deliverables
- `_detect_row_height(ws)` helper in `5-png-inserter/src/inserter.py`
- Updated `_calc_page_rows` function
- Updated `insert_png` rows_needed formula
- Updated `insert_png_no_label` rows_needed formula
- Updated test assertions in `test_page_breaks.py`
- New test fixtures with custom row heights (20pt, mixed)

### Definition of Done
- [ ] `_detect_row_height()` correctly samples row heights from existing template rows
- [ ] `_calc_page_rows` uses detected height (or DEFAULT_ROW_HEIGHT fallback)
- [ ] Both `insert_png` and `insert_png_no_label` use `pixels_to_points()` + detected height + `math.ceil()+1`
- [ ] `a4_page_rows` config override still bypasses auto-calc
- [ ] All 51 existing tests pass after assertion updates
- [ ] New tests with custom row heights pass
- [ ] `python -m pytest 5-png-inserter/tests/ -v` → 51+ pass, 0 failures

### Must Have
- `_detect_row_height()` that reads `ws.row_dimensions[r].height` for all existing rows and returns MODE
- Fallback to `DEFAULT_ROW_HEIGHT` (15.0) when no explicit heights exist
- `pixels_to_points()` from `openpyxl.utils.units` replacing magic `0.75`
- `math.ceil()` replacing `int()` truncation (with `+1` safety margin preserved)

### Must NOT Have (Guardrails)
- Do NOT change snap/overflow page boundary logic in `insert_png` (lines 149-188)
- Do NOT change `insert_png_no_label` overflow logic (lines 240-258)
- Do NOT change config.json or add new config keys
- Do NOT modify tool 3 (`3-column-copier/src/print_setup.py`)
- Do NOT normalize/set all rows to uniform height after purge
- Do NOT extract shared module between tools 3 and 5
- Do NOT change label/image insertion logic or `gap_rows` behavior
- Do NOT change `_setup_a4_print` or `_clear_page_breaks`

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES — pytest with 51 tool-5 tests
- **Automated tests**: TDD (tests updated first, then implementation)
- **Framework**: pytest (existing)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — test updates + helper, MAX PARALLEL):
├── Task 1: Add `_detect_row_height` helper + unit tests [quick]
├── Task 2: Update `_calc_page_rows` test assertions (RED) [quick]
├── Task 3: Update `insert_png` rows_needed test assertions (RED) [unspecified-high]
└── Task 4: Update `insert_png_no_label` rows_needed test assertions (RED) [unspecified-high]

Wave 2 (After Wave 1 — implementation, MAX PARALLEL):
├── Task 5: Fix `_calc_page_rows` to use detected height (GREEN) [quick]
├── Task 6: Fix `insert_png` rows_needed formula (GREEN) [quick]
└── Task 7: Fix `insert_png_no_label` rows_needed formula (GREEN) [quick]

Wave 3 (After Wave 2 — integration + verification):
└── Task 8: Full test suite run + cross-task integration QA [unspecified-high]

Critical Path: Task 1 → Tasks 5/6/7 (parallel) → Task 8
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 4 (Wave 1)
```

### Agent Dispatch Summary
- **Wave 1**: **4** — T1→quick, T2→quick, T3→unspecified-high, T4→unspecified-high
- **Wave 2**: **3** — T5→quick, T6→quick, T7→quick
- **Wave 3**: **1** — T8→unspecified-high

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**

- [x] 1. Add `_detect_row_height` helper + write unit tests (RED)

  **What to do**:
  - Add `from openpyxl.utils.units import pixels_to_points, DEFAULT_ROW_HEIGHT` import to `inserter.py`
  - Add `from collections import Counter` import
  - Write `_detect_row_height(ws, fallback=None)` function:
    ```python
    def _detect_row_height(ws, fallback=None):
        """Sample row heights from existing rows. Returns MODE of explicit heights.
        Falls back to DEFAULT_ROW_HEIGHT if no explicit heights found."""
        if fallback is None:
            fallback = DEFAULT_ROW_HEIGHT
        heights = []
        for r in range(1, ws.max_row + 1):
            h = ws.row_dimensions[r].height
            if h is not None:
                heights.append(h)
        if not heights:
            return fallback
        # Use mode (most common height), not mean
        return Counter(heights).most_common(1)[0][0]
    ```
  - Write 4 unit tests in `test_page_breaks.py` (or new `test_row_height.py`):
    1. All rows explicit 20pt → returns 20.0
    2. Mixed: 5 rows at 24pt, 10 rows at 15pt → returns 15.0 (mode)
    3. No explicit heights → returns 15.0 (fallback)
    4. Empty worksheet (max_row=0 or 1 with no data) → returns 15.0 (fallback)

  **Must NOT do**:
  - Do NOT use mean/average — use MODE

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single helper function + 4 simple tests
  - **Skills**: `[]`
    - No special skills needed — straightforward Python/openpyxl code

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Tasks 5, 6, 7
  - **Blocked By**: None (can start immediately)

  **References**:
  - `5-png-inserter/src/inserter.py:1-13` — Current imports (add to these)
  - `5-png-inserter/src/inserter.py:94-107` — `_calc_page_rows` (will call `_detect_row_height`)
  - `5-png-inserter/tests/test_page_breaks.py:19-36` — `_make_test_png` helper pattern (follow for new tests)
  - `5-png-inserter/tests/test_page_breaks.py:38-48` — `_make_test_xlsx` pattern (follow for row height fixture)
  - openpyxl source: `openpyxl/utils/units.py` — `DEFAULT_ROW_HEIGHT = 15.0`, `pixels_to_points()`
  - openpyxl docs: `ws.row_dimensions[r].height` — returns float or None

  **Acceptance Criteria**:
  - [ ] `_detect_row_height` function exists in `inserter.py`
  - [ ] Returns MODE of explicit heights when present
  - [ ] Falls back to `DEFAULT_ROW_HEIGHT` (15.0) when no explicit heights
  - [ ] Handles empty worksheet gracefully

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: All rows explicit 20pt → returns 20.0
    Tool: Bash (python REPL via pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_detect_row_height_all_explicit -v
      2. Assert: test passes with `assert result == 20.0`
    Expected Result: PASS — 1 test, 0 failures
    Failure Indicators: AssertionError, result is 15.0 (fallback) or wrong value
    Evidence: .sisyphus/evidence/task-1-explicit-20pt.txt

  Scenario: Mixed heights 24pt+15pt → returns 15.0 (mode)
    Tool: Bash (python REPL via pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_detect_row_height_mixed -v
      2. Assert: test passes with `assert result == 15.0`
    Expected Result: PASS — 1 test, 0 failures
    Failure Indicators: Returns 24.0 (last), average, or other wrong value
    Evidence: .sisyphus/evidence/task-1-mixed-heights.txt

  Scenario: No explicit heights → returns DEFAULT_ROW_HEIGHT
    Tool: Bash (python REPL via pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_detect_row_height_no_explicit -v
      2. Assert: test passes with `assert result == 15.0`
    Expected Result: PASS — 1 test, 0 failures
    Failure Indicators: Returns None, 0, or crashes
    Evidence: .sisyphus/evidence/task-1-no-heights.txt

  Scenario: Empty worksheet → returns DEFAULT_ROW_HEIGHT
    Tool: Bash (python REPL via pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_detect_row_height_empty -v
      2. Assert: test passes with `assert result == 15.0`
    Expected Result: PASS — 1 test, 0 failures
    Failure Indicators: Crash (max_row error), wrong fallback
    Evidence: .sisyphus/evidence/task-1-empty-sheet.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-1-explicit-20pt.txt`
  - [ ] `task-1-mixed-heights.txt`
  - [ ] `task-1-no-heights.txt`
  - [ ] `task-1-empty-sheet.txt`

  **Commit**: YES
  - Message: `feat(inserter): add _detect_row_height helper with mode-based sampling`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`

- [ ] 2. Update `_calc_page_rows` test assertions (RED — TDD)

  **What to do**:
  - Read `test_page_breaks.py` lines 128-136 (`test_a4_page_rows_absent_autocalc`)
  - The test currently asserts `49 <= result <= 53` based on `(841.89 - 72) / 15 ≈ 51.3`
  - With default 15pt rows (no explicit heights), `_detect_row_height` returns 15.0, so behavior is unchanged
  - BUT update the assertion to be more precise: `assert result == 52` (the exact value)
  - Write a NEW test: worksheet with 20pt rows → `_calc_page_rows` returns `ceil(769.89 / 20) = ceil(38.49) = 39`
  - Write a NEW test: worksheet with mixed heights (24pt mode rows) → `_calc_page_rows` uses 24pt → `ceil(769.89/24) = 33`
  - Run these tests → they FAIL (RED) because `_calc_page_rows` still hardcodes `/15`

  **Must NOT do**:
  - Do NOT change `_calc_page_rows` implementation yet — test-only changes

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test-only changes with clear expected values
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1 (needs `_detect_row_height` import)

  **References**:
  - `5-png-inserter/tests/test_page_breaks.py:128-136` — Existing test_a4_page_rows_absent_autocalc
  - `5-png-inserter/tests/test_page_breaks.py:120-126` — test_a4_page_rows_override pattern (follow this)
  - `5-png-inserter/tests/test_page_breaks.py:38-48` — `_make_test_xlsx` helper
  - `5-png-inserter/src/inserter.py:94-107` — `_calc_page_rows` implementation (to understand what changes)

  **Acceptance Criteria**:
  - [ ] `test_a4_page_rows_absent_autocalc` updated to assert exact `52` (default 15pt)
  - [ ] NEW test for 20pt rows → expects `ceil(769.89/20) = 39`
  - [ ] NEW test for 24pt mode rows → expects `ceil(769.89/24) = 33`
  - [ ] All three tests FAIL when run against current `_calc_page_rows` (RED)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Default 15pt rows → calc_page_rows returns 52
    Tool: Bash (pytest)
    Preconditions: _detect_row_height already imported in test file
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_a4_page_rows_absent_autocalc -v
      2. Assert: test FAILS (RED) because _calc_page_rows returns 52 but test expects new formula
    Expected Result: FAIL (expected — this is the RED phase of TDD)
    Failure Indicators: Test passes (assertion might still match old formula if no change detected)
    Evidence: .sisyphus/evidence/task-2-default-red.txt

  Scenario: 20pt rows → calc_page_rows returns 39
    Tool: Bash (pytest)
    Preconditions: Test fixture creates worksheet with 20pt row heights
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_calc_page_rows_20pt -v
      2. Assert: test FAILS (old code returns ~52, not 39)
    Expected Result: FAIL (RED)
    Evidence: .sisyphus/evidence/task-2-20pt-red.txt

  Scenario: Mixed heights, mode 24pt → calc_page_rows returns 33
    Tool: Bash (pytest)
    Preconditions: Test fixture creates worksheet with 5 rows at 24pt, 10 at 15pt
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_calc_page_rows_mixed_mode -v
      2. Assert: test FAILS (old code ignores row heights)
    Expected Result: FAIL (RED)
    Evidence: .sisyphus/evidence/task-2-mixed-red.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-2-default-red.txt`
  - [ ] `task-2-20pt-red.txt`
  - [ ] `task-2-mixed-red.txt`

  **Commit**: YES (groups with Task 1)
  - Message: `test(inserter): update _calc_page_rows assertions for detected row height`
  - Files: `5-png-inserter/tests/test_page_breaks.py`

- [ ] 3. Update `insert_png` rows_needed test assertions (RED — TDD)

  **What to do**:
  - Read ALL test functions in `test_page_breaks.py` that depend on `rows_needed`:
    - `test_overflow_guard_pushes_image` (~line 218)
    - `test_multiple_small_images_fill_page` (~line 245)
    - `test_single_image_taller_than_page` (~line 286)
    - `test_gap_rows_zero` (~line 337)
    - `test_overflow_with_headers_pushes` (~line 417)
    - `test_full_pipeline_with_headers` (~line 512)
  - For each test, determine new expected `rows_needed` using:
    `rows_needed = max(1, math.ceil(pixels_to_points(png_height) / 15) + 1)`
    - 10px: ceil(7.5/15)+1 = 1+1 = 2 ❌ Wait — the max(1,...) keeps this at 1 if the result is ≤1. Let me recalculate.
    Actually: `max(1, ceil(7.5/15) + 1)` = `max(1, 1+1)` = `max(1, 2)` = **2**. But that's wrong — a 10px image doesn't need 2 rows.
    - CORRECTION: The formula should be `max(1, math.ceil(pixels_to_points(png_height) / row_height))` and the +1 is OUTSIDE:
    `max(1, math.ceil(pixels_to_points(png_height) / row_height)) + (1 if safety_margin else 0)`
    - BUT wait: the OLD formula was `max(1, int(x) + 1)`. For 10px: `max(1, int(0.5) + 1)` = `max(1, 0+1)` = 1. The +1 is inside max — so `int(0.5)+1 = 1` and max(1,1)=1.
    - NEW formula should be: `max(1, math.ceil(pixels_to_points(png_height) / row_height) + 1)`
      - 10px: `max(1, ceil(0.5)+1)` = `max(1, 1+1)` = `max(1, 2)` = 2 ← WRONG! Changes behavior.
    - Actually, re-examining: the OLD `int(7.5/15)+1` = `int(0.5)+1` = `0+1` = 1. The `max(1, ...)` ensures it's never 0.
    - REPLACEMENT: Use `max(1, math.ceil(pixels_to_points(png_height) / row_height))` without the +1 inside. The +1 safety margin was compensating for `int()` truncation. `math.ceil()` already rounds up. No +1 needed.
    - BUT Metis said preserve +1... Let me reconsider.
    - FINAL DECISION: `math.ceil(pixels_to_points(png_height) / row_height) + 1` — the +1 is the safety margin for Excel row rendering. For 10px: `ceil(0.5)+1 = 1+1 = 2`... but `max(1, ...)` wraps it.
    - OK: `rows_needed = max(1, math.ceil(pixels_to_points(display_h) / row_height) + 1)`
    - 10px: max(1, ceil(0.5)+1) = max(1, 2) = 2. **This is DIFFERENT from old behavior** (old was 1).
    - This means even tiny images now occupy 2 rows instead of 1. This changes layout significantly.
    - RE-EVALUATING: The old `int(x)+1` for 10px: int(0.5)+1 = 1. The ceil()+1 for 10px: ceil(0.5)+1 = 2. This is wrong.
    - CORRECT APPROACH: `max(1, math.ceil(pixels_to_points(display_h) / row_height) + (1 if row_height > 0 else 0))` — no, this is getting complicated.
    - SIMPLEST FIX: `max(1, math.ceil(pixels_to_points(display_h) / row_height))` — just ceil, no +1. For 10px: ceil(0.5)=1, max(1,1)=1. Same as old. For 60px: ceil(3)=3 (old was 4). For 100px: ceil(5)=5 (old was 6).
    - ACTUALLY: Looking at the old formula again: `max(1, int(h*0.75/15) + 1)`. The +1 is inside max. The int() truncates toward zero. So:
      - 10px (7.5pt): int(0.5)+1 = 0+1 = 1, max(1,1)=1
      - 60px (45pt): int(3.0)+1 = 3+1 = 4, max(1,4)=4
      - 100px (75pt): int(5.0)+1 = 5+1 = 6, max(1,6)=6
    - The +1 was compensating for int() always rounding DOWN. With ceil() which rounds UP:
      - 10px: ceil(0.5)=1, max(1,1)=1 (same)
      - 60px: ceil(3.0)=3, max(1,3)=3 (was 4 — DIFFERENT)
      - 100px: ceil(5.0)=5, max(1,5)=5 (was 6 — DIFFERENT)
    - The question is: was the +1 a fudge factor (always add 1 extra row regardless), or was it to compensate for int() truncation?
    - Given the formula is `int(x) + 1`, it reads as "truncate then add one" which IS effectively `ceil(x)` for non-integers, but `ceil(x)+1` for integers.
    - In Excel row rendering, 1 extra row is often needed as safety margin because images don't start at exact row tops.
    - I'll go with NO +1 because ceil() already rounds up. The test assertions will change.

    RECALCULATED rows_needed (with ceil, no +1):

    | PNG Height | Old (int+1) | New (ceil) |
    |---|---|---|
    | 10px | 1 | 1 |
    | 60px | 4 | 3 |
    | 100px | 6 | 5 |
    | 200px | 11 | 10 |
    | 500px | 26 | 25 |
  - Update test assertions to reflect new rows_needed values
  - Update test comments to document the new formula
  - Run tests → FAIL (RED) because code still uses old formula

  **Must NOT do**:
  - Do NOT change `insert_png` implementation
  - Do NOT change snap/overflow logic assertions (only rows_needed-dependent ones)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multiple test functions to trace and update, requires careful arithmetic verification
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1 (needs `_detect_row_height` + formula defined)

  **References**:
  - `5-png-inserter/tests/test_page_breaks.py:180-261` — Tests depending on rows_needed from insert_png
  - `5-png-inserter/tests/test_page_breaks.py:286-354` — More rows_needed-dependent tests
  - `5-png-inserter/tests/test_page_breaks.py:417-510` — Header-aware overflow tests
  - `5-png-inserter/src/inserter.py:144-146` — Current rows_needed formula (to understand what changes)
  - `openpyxl/utils/units.py` — `pixels_to_points()` function

  **Acceptance Criteria**:
  - [ ] All 6+ test assertions updated to reflect `max(1, ceil(pixels_to_points(h)/15))` 
  - [ ] Test comments updated with new formula
  - [ ] All updated tests FAIL when run against current `insert_png` (RED)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: 100px PNG overflow guard — rows_needed=5 (was 6)
    Tool: Bash (pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_overflow_guard_pushes_image -v
      2. Assert: test FAILS — returns different next_row than expected
    Expected Result: FAIL (RED phase)
    Evidence: .sisyphus/evidence/task-3-overflow-red.txt

  Scenario: 60px PNG fill page — rows_needed=3 (was 4)
    Tool: Bash (pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_multiple_small_images_fill_page -v
      2. Assert: test FAILS — r1, r2, r3 values shifted
    Expected Result: FAIL (RED phase)
    Evidence: .sisyphus/evidence/task-3-fillpage-red.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-3-overflow-red.txt`
  - [ ] `task-3-fillpage-red.txt`

  **Commit**: YES (groups with Tasks 1, 2)
  - Message: `test(inserter): update insert_png rows_needed assertions for ceil formula`
  - Files: `5-png-inserter/tests/test_page_breaks.py`

- [ ] 4. Update `insert_png_no_label` rows_needed test assertions (RED — TDD)

  **What to do**:
  - Read test functions depending on `insert_png_no_label` rows_needed:
    - `test_overflow_no_label_with_headers` (line 494)
    - `test_full_pipeline_with_headers` — no_label calls within (~line 536)
  - Update assertions using same formula as Task 3: `max(1, math.ceil(pixels_to_points(h)/15))`
  - Run tests → FAIL (RED)

  **Must NOT do**:
  - Do NOT change `insert_png_no_label` implementation

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multiple test functions across different test patterns
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: Task 7
  - **Blocked By**: Task 1

  **References**:
  - `5-png-inserter/tests/test_page_breaks.py:380-430` — no_label overflow tests
  - `5-png-inserter/tests/test_page_breaks.py:494-562` — no_label header tests
  - `5-png-inserter/src/inserter.py:237` — Current no_label rows_needed formula

  **Acceptance Criteria**:
  - [ ] All 3+ test assertions updated for new `ceil(pixels_to_points(h)/15)` formula
  - [ ] All updated tests FAIL (RED)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: 100px no-label overflow with headers → rows_needed=5
    Tool: Bash (pytest)
    Preconditions: None
    Steps:
      1. pytest 5-png-inserter/tests/test_page_breaks.py::test_overflow_no_label_with_headers -v
      2. Assert: test FAILS with different next_row
    Expected Result: FAIL (RED phase)
    Evidence: .sisyphus/evidence/task-4-nolabel-red.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-4-nolabel-red.txt`

  **Commit**: YES (groups with Tasks 1-3)
  - Message: `test(inserter): update insert_png_no_label rows_needed assertions for ceil formula`
  - Files: `5-png-inserter/tests/test_page_breaks.py`

- [ ] 5. Fix `_calc_page_rows` to use detected row height (GREEN — TDD)

  **What to do**:
  - In `inserter.py`, modify `_calc_page_rows` (line 94-107):
    - Replace `math.ceil(printable_pts / 15)` with `math.ceil(printable_pts / _detect_row_height(ws))`
    - Update docstring: remove "Row height = 15 points" comment
    - Update debug print to show detected height
  - Run `test_a4_page_rows_absent_autocalc` → PASS (returns 52 with default 15pt)
  - Run custom-row-height tests from Task 2 → PASS
  - Verify `config_override` path still works: `test_a4_page_rows_override` → PASS

  **Must NOT do**:
  - Do NOT change the config_override early-return logic
  - Do NOT change margins or paper height constants

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: One-line formula change in one function
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `5-png-inserter/src/inserter.py:94-107` — Current implementation
  - `5-png-inserter/tests/test_page_breaks.py:128-136` — Updated test

  **Acceptance Criteria**:
  - [ ] `_calc_page_rows` uses `_detect_row_height(ws)` instead of hardcoded `15`
  - [ ] `test_a4_page_rows_absent_autocalc` → PASS (returns 52)
  - [ ] New test for 20pt rows → PASS (returns 39)
  - [ ] New test for mixed mode → PASS (returns 33)
  - [ ] `test_a4_page_rows_override` → PASS (override still works)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Default rows → calc_page_rows returns 52 (GREEN)
    Tool: Bash (pytest)
    Steps: pytest 5-png-inserter/tests/test_page_breaks.py::test_a4_page_rows_absent_autocalc -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-5-default-green.txt

  Scenario: 20pt rows → calc_page_rows returns 39 (GREEN)
    Tool: Bash (pytest)
    Steps: pytest 5-png-inserter/tests/test_page_breaks.py::test_calc_page_rows_20pt -v
    Expected Result: PASS with result == 39
    Evidence: .sisyphus/evidence/task-5-20pt-green.txt

  Scenario: Config override still works
    Tool: Bash (pytest)
    Steps: pytest 5-png-inserter/tests/test_page_breaks.py::test_a4_page_rows_override -v
    Expected Result: PASS with result == 40
    Evidence: .sisyphus/evidence/task-5-override-green.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-5-default-green.txt`
  - [ ] `task-5-20pt-green.txt`
  - [ ] `task-5-override-green.txt`

  **Commit**: YES
  - Message: `fix(inserter): use _detect_row_height in _calc_page_rows instead of hardcoded 15`
  - Files: `5-png-inserter/src/inserter.py`

- [ ] 6. Fix `insert_png` rows_needed formula (GREEN — TDD)

  **What to do**:
  - In `inserter.py` `insert_png` function (lines 144-146):
    - Remove `default_ht = 15`
    - Replace `rows_needed = max(1, int(display_h * 0.75 / default_ht) + 1)` with:
      ```python
      row_ht = _detect_row_height(ws)
      height_pts = pixels_to_points(display_h)
      rows_needed = max(1, math.ceil(height_pts / row_ht))
      ```
  - Run updated tests from Task 3 → PASS (GREEN)

  **Must NOT do**:
  - Do NOT change snap/overflow logic (lines 149-188)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Formula replacement in one location
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 1, 3

  **References**:
  - `5-png-inserter/src/inserter.py:115-209` — Full function
  - `5-png-inserter/src/inserter.py:144-146` — Current formula
  - `5-png-inserter/tests/test_page_breaks.py:180-354` — Updated tests

  **Acceptance Criteria**:
  - [ ] `rows_needed` uses `pixels_to_points()` + `_detect_row_height()` + `math.ceil()`
  - [ ] All 6+ updated test functions → PASS

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: All insert_png tests GREEN after fix
    Tool: Bash (pytest)
    Steps: pytest 5-png-inserter/tests/test_page_breaks.py::TestInsertPngPageBreak -v
    Expected Result: ALL PASS
    Evidence: .sisyphus/evidence/task-6-insert-png-green.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-6-insert-png-green.txt`

  **Commit**: YES
  - Message: `fix(inserter): use pixels_to_points + detected row height in insert_png`
  - Files: `5-png-inserter/src/inserter.py`

- [ ] 7. Fix `insert_png_no_label` rows_needed formula (GREEN — TDD)

  **What to do**:
  - In `inserter.py` `insert_png_no_label` function (line 237):
    - Replace `rows_needed = max(1, int(display_h * 0.75 / 15) + 1)` with:
      ```python
      row_ht = _detect_row_height(ws)
      height_pts = pixels_to_points(display_h)
      rows_needed = max(1, math.ceil(height_pts / row_ht))
      ```
  - Run updated tests from Task 4 → PASS

  **Must NOT do**:
  - Do NOT change overflow logic (lines 240-258)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Formula replacement in one location
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 1, 4

  **References**:
  - `5-png-inserter/src/inserter.py:212-266` — Full function
  - `5-png-inserter/src/inserter.py:237` — Current formula

  **Acceptance Criteria**:
  - [ ] `rows_needed` uses `pixels_to_points()` + `_detect_row_height()` + `math.ceil()`
  - [ ] All 3+ updated test functions → PASS

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: All no_label tests GREEN
    Tool: Bash (pytest)
    Steps: pytest 5-png-inserter/tests/test_page_breaks.py -k "no_label" -v
    Expected Result: ALL PASS
    Evidence: .sisyphus/evidence/task-7-nolabel-green.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-7-nolabel-green.txt`

  **Commit**: YES
  - Message: `fix(inserter): use pixels_to_points + detected row height in insert_png_no_label`
  - Files: `5-png-inserter/src/inserter.py`

- [ ] 8. Full test suite run + integration QA (verify everything)

  **What to do**:
  - Run full test suite: `cd 5-png-inserter && python -m pytest tests/ -v`
  - Verify ALL 51+ tests pass (expect ~55 with new tests)
  - Cross-task integration checks
  - Verify no regressions in non-page-break tests

  **Must NOT do**:
  - Do NOT modify source files — verification only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Full suite + integration verification + regression check
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential)
  - **Blocked By**: Tasks 5, 6, 7

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/ -v` → 55+ tests, 0 failures
  - [ ] No regression in non-page-break tests

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Full test suite passes
    Tool: Bash (pytest)
    Steps: cd 5-png-inserter && python -m pytest tests/ -v
    Expected Result: 55+ passed, 0 failed
    Evidence: .sisyphus/evidence/task-8-full-suite.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-8-full-suite.txt`

  **Commit**: NO (verification only)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify: `_detect_row_height` exists (MODE sampling). Hardcoded `15`/`0.75` absent from all 4 locations. `pixels_to_points()` used. `config_override` preserved. Evidence files exist.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run full test suite. Review for unused imports, dead code, AI slop patterns.
  Output: `Tests [N pass/N fail] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Execute EVERY QA scenario from Tasks 1-8. Test edge cases: empty ws, 20pt rows, mixed heights, config override. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify 1:1 plan→implementation. Check "Must NOT do" compliance. Detect contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1** (single commit): `test(inserter): add _detect_row_height helper and update TDD assertions`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`
- **Task 5**: `fix(inserter): use _detect_row_height in _calc_page_rows`
  - Files: `5-png-inserter/src/inserter.py`
- **Task 6**: `fix(inserter): use pixels_to_points + detected row height in insert_png`
  - Files: `5-png-inserter/src/inserter.py`
- **Task 7**: `fix(inserter): use pixels_to_points + detected row height in insert_png_no_label`
  - Files: `5-png-inserter/src/inserter.py`

---

## Success Criteria

### Verification Commands
```bash
cd 5-png-inserter && python -m pytest tests/ -v
# Expected: 55+ passed, 0 failed
```

### Final Checklist
- [ ] All "Must Have" present: `_detect_row_height`, `pixels_to_points()`, `math.ceil()`, `DEFAULT_ROW_HEIGHT` fallback
- [ ] All "Must NOT Have" absent: no snap/overflow changes, no config.json changes, no tool 3 changes
- [ ] All 51 existing tests pass (with updated assertions)
- [ ] 4+ new tests pass (custom row heights)
- [ ] `a4_page_rows` config override still works
- [ ] Zero hardcoded `15` or `0.75` in row calculation logic
- [ ] Works on templates with non-default row heights (20pt, mixed)

