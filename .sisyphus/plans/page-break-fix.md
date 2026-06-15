# Page Break Protection for 5-png-inserter

## TL;DR

> **Quick Summary**: Add automatic page break insertion to prevent PNG images from splitting across printed A4 pages. Uses openpyxl's `Break` API with auto-calculated page capacity (~48 rows) and a two-layer protection system (site breaks + overflow guard). Feature is opt-in via existing `page_break_before_label` config key for full backward compatibility.
> 
> **Deliverables**:
> - Updated `config.json` with documented `page_break_before_label` (re-purposed) and optional `a4_page_rows`
> - Modified `_setup_a4_print()` to disable auto page breaks
> - Page break insertion logic in `insert_png()` (before site labels) and `insert_png_no_label()` (overflow guard)
> - Page capacity auto-calculation from A4 margins
> - 17 new TDD tests (7 config/setup + 6 break logic + 4 edge cases)
> - All 14 existing tests pass unchanged (31 total)
> 
> **Estimated Effort**: Short
> **Parallel Execution**: YES — 2 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 5 → Task 6

---

## Context

### Original Request
Fix the open issue in the PAT tool where images can split across printed pages in the 5-png-inserter. The handout notes: "Images can split across printed pages. No page boundary protection active."

### Interview Summary
**Key Discussions**:
- **Page capacity method**: Auto-calculate from A4 margins with optional config override (`a4_page_rows`)
- **Print title rows**: Keep removed — no `print_title_rows`, no `header_count`
- **Break placement**: Both — break before site label + overflow guard within a site
- **Old bug**: Labels weren't getting their own page in the old logic — fixed with clean page-boundary math
- **Test strategy**: TDD with pytest (existing infrastructure, 14 tests)

**Research Findings**:
- Working tree has **zero** page-break logic (all stripped in uncommitted changes)
- openpyxl CAN insert breaks via `ws.row_breaks.append(Break(id=N))` but CANNOT predict natural breaks
- Stale key `page_break_before_label: false` exists in config but has zero effect — re-purpose as feature toggle
- A4 actual capacity: ~48 rows (A4 height 841.89pt minus margins 72pt = 769.89pt / 15pt per row = 51, minus header/footer ≈ 48)

### Metis Review
**Identified Gaps** (addressed):
- **CRITICAL**: `autoPageBreaks` property is on `ws.page_setup`, not `ws` directly — plan corrected
- **CRITICAL**: A4 row count is ~48 not ~55 — plan uses auto-calc, not hardcoded 55
- **IMPORTANT**: Read breaks via `ws.row_breaks.brk` (not direct iteration which yields tuples)
- **IMPORTANT**: Re-purpose `page_break_before_label` as backward-compatible feature toggle (default: false)
- **EDGE**: Single image > A4 page — log warning, let overflow (can't prevent what can't fit)
- **EDGE**: Stale breaks accumulate across runs — clear breaks in `_setup_a4_print()` when feature disabled
- **EDGE**: No break before first site on sheet (current_row == purge_from)

---

## Work Objectives

### Core Objective
Add configurable page break protection to the 5-png-inserter so images never split across printed A4 pages.

### Concrete Deliverables
- `5-png-inserter/config.json` — documented `page_break_before_label` (re-purposed) + optional `a4_page_rows`
- `5-png-inserter/src/inserter.py` — modified `_setup_a4_print()`, `insert_png()`, `insert_png_no_label()`
- `5-png-inserter/insert.py` — parse new config, pass `page_rows` to insert functions
- `5-png-inserter/tests/test_page_breaks.py` — 17 new TDD tests
- All 14 existing `test_matcher.py` tests pass unchanged

### Definition of Done
- [ ] `page_break_before_label: true` → `Break` objects present in output XLSX `row_breaks.brk`
- [ ] `page_break_before_label: false` → no breaks, behavior identical to current (backward compat)
- [ ] Images at page boundary pushed to next page (verified by break IDs in output)
- [ ] `python -m pytest tests/ -v` → 14 existing + 17 new = 31 pass
- [ ] Manual verification: open output XLSX in Excel, check Page Break Preview — no image splitting

### Must Have
- Backward compatibility: `page_break_before_label: false` (default) behaves identically to current code
- Auto-calculate A4 page capacity from margins (~48 rows) when `a4_page_rows` absent
- Break before each new site label on same sheet (when enabled)
- Overflow guard: push image to next page if it would cross boundary
- `autoPageBreaks = False` in page setup

### Must NOT Have (Guardrails)
- ❌ `print_title_rows` — stays removed
- ❌ `header_count` — stays removed
- ❌ Letter paper support — A4 only, hardcoded
- ❌ Dynamic row height scanning — use fixed 15pt default
- ❌ Smart image resizing — images at configured scale, no auto-shrink
- ❌ Break before first site on sheet (current_row == purge_from)
- ❌ Changes to any tool other than 5-png-inserter
- ❌ Changes to PNG extraction, naming, matching, column copying, or cell editing

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest, conftest.py, tmp_path fixtures)
- **Automated tests**: TDD — RED (failing test) → GREEN (minimal impl) → REFACTOR
- **Framework**: pytest with openpyxl

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.txt`.

- **Backend/CLI**: Use Bash to run `pytest`, `python insert.py`, parse XLSX with openpyxl
- **Verification**: Read `ws.row_breaks.brk` for Break IDs, `ws.page_setup.autoPageBreaks` for setting

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation):
├── Task 1: Config update + auto-calc + _setup_a4_print() changes [quick]
├── Task 2: Page break logic in insert_png() + insert_png_no_label() [deep]
└── Task 3: Orchestrator changes in insert.py [quick]

Wave 2 (After Wave 1 — TDD tests):
├── Task 4: Tests — config parsing + backward compat + _setup_a4_print [quick]
├── Task 5: Tests — break insertion (site label + overflow) [deep]
├── Task 6: Tests — edge cases (large image, multi-sheet, gap_rows=0) [deep]
├── Task 7: Run full test suite, verify 14 existing + 17 new = 31 pass [quick]
└── Task 8: Final integration QA — run tool end-to-end, verify output XLSX [quick]
```

```
Wave FINAL (After ALL tasks):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
```

**Critical Path**: Task 1 → Task 2 → Task 3 → Tasks 4-6 (parallel) → Task 7 → Task 8
**Parallel Speedup**: ~40% faster than sequential (Wave 2 tests run in parallel)
**Max Concurrent**: 4 (Wave 2)

---

## TODOs

- [x] 1. **Config update + auto-calc + `_setup_a4_print()` changes**

  **What to do**:
  - In `config.json`: Document `page_break_before_label` (existing key, now functional). Set default to `false`. Add optional `a4_page_rows` with comment explaining auto-calc behavior.
  - In `src/inserter.py > _setup_a4_print()` (line 64-76): Add `ws.page_setup.autoPageBreaks = False` to prevent Excel from inserting automatic breaks that conflict with manual ones.
  - In `src/inserter.py`: Add new function `_calc_page_rows(ws, config_override=None)` that computes A4 page capacity from margins: `paper_height_pts = 841.89; margins_pts = (top + bottom) * 72; printable_pts = paper_height_pts - margins_pts; return int(printable_pts / 15)`. Default result ≈ 51, document as ~48 in config comment for safety.
  - In `src/inserter.py`: Add `_clear_page_breaks(ws)` helper to reset `ws.row_breaks.brk` to empty tuple (for when feature is disabled to prevent stale breaks).

  **Must NOT do**:
  - Do NOT add `print_title_rows` or `header_count`
  - Do NOT hardcode `55` — use auto-calc
  - Do NOT set `ws.autoPageBreaks` (wrong path — must be `ws.page_setup.autoPageBreaks`)

  **Test cases to cover** (implemented in Task 4):
  - `autoPageBreaks` is `False` after `_setup_a4_print()`
  - `_calc_page_rows()` returns ~51 with 0.5" margins, different value with custom margins
  - `_calc_page_rows()` returns config override when provided
  - `_clear_page_breaks()` empties `row_breaks.brk`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward config + small function additions, no complex logic
  - **Skills**: [`xlsx`]
    - `xlsx`: Working with openpyxl, XLSX manipulation

  **Parallelization**:
  - **Can Run In Parallel**: NO (foundation — Tasks 2 and 3 depend on this)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 2, 3
  - **Blocked By**: None (can start immediately)

  **References**:
  - `5-png-inserter/src/inserter.py:64-76` — Current `_setup_a4_print()` function to modify
  - `5-png-inserter/config.json:13` — Stale `page_break_before_label: false` key to document
  - `openpyxl.worksheet.page.PageSetupProperties` — `autoPageBreaks` property on page_setup
  - `openpyxl.worksheet.properties.PageSetupProperties` — Already imported in current code

  **Acceptance Criteria**:
  - [ ] `config.json` has documented `page_break_before_label` (default: `false`) and optional `a4_page_rows`
  - [ ] `_setup_a4_print()` sets `ws.page_setup.autoPageBreaks = False`
  - [ ] `_calc_page_rows()` returns correct value for current margins
  - [ ] `_clear_page_breaks()` exists and clears `ws.row_breaks.brk`

  **QA Scenarios**:

  ```
  Scenario: autoPageBreaks is disabled after page setup
    Tool: Bash (python REPL)
    Preconditions: openpyxl installed, import inserter module
    Steps:
      1. Create new Workbook, get active sheet
      2. Call _setup_a4_print(ws)
      3. Read ws.page_setup.autoPageBreaks
    Expected Result: ws.page_setup.autoPageBreaks is False
    Failure Indicators: Returns True, AttributeError on wrong path, None
    Evidence: .sisyphus/evidence/task-1-autopagebreaks.txt

  Scenario: _calc_page_rows with 0.5" margins returns ~51
    Tool: Bash (python REPL)
    Preconditions: _calc_page_rows function imported
    Steps:
      1. Create mock ws with page_margins.top=0.5, page_margins.bottom=0.5
      2. Call _calc_page_rows(ws)
      3. Assert result is 51 (841.89 - 72) / 15
    Expected Result: 51
    Failure Indicators: Returns 0, returns >100, TypeError
    Evidence: .sisyphus/evidence/task-1-calc-rows.txt
  ```

  **Commit**: NO (groups with Task 2)

- [x] 2. **Page break logic in `insert_png()` and `insert_png_no_label()`**

  **What to do**:
  - Add `page_rows` parameter to both `insert_png()` and `insert_png_no_label()` (default `None` = disabled)
  - Add `purge_from` parameter to `insert_png()` to know when we're at the first site (skip break)
  - **In `insert_png()`**: When `page_rows is not None` and `start_row > purge_from` (not first site):
    1. Snap `start_row` to next page boundary: `page_end = ((start_row - 2) // page_rows + 1) * page_rows + 1`, set `start_row = max(start_row, page_end)`
    2. Insert break: `ws.row_breaks.append(Break(id=start_row))`
  - **In `insert_png_no_label()`**: When `page_rows is not None`:
    1. Calculate `total_rows = gap_rows + rows_needed + gap_rows`
    2. Check overflow: `img_end = start_row + gap_rows + rows_needed; page_end = ((start_row - 1) // page_rows + 1) * page_rows`
    3. If `img_end > page_end`: push to next page: `start_row = page_end + 1`
  - Import `Break` at top of `inserter.py`: `from openpyxl.worksheet.pagebreak import Break`
  - When `page_break_before_label` is `False`, pass `page_rows=None` (no breaks at all)

  **Must NOT do**:
  - Do NOT insert break before first site (check `start_row > purge_from`)
  - Do NOT insert break between label and its first image (they stay consecutive)
  - Do NOT change row counting formula — use existing `rows_needed = max(1, int(display_h * 0.75 / 15) + 1)`
  - Do NOT modify `extract_label()`, `extract_site()`, `clean_sheet_name()`, or `find_matching_sheet()`

  **Test cases to cover** (implemented in Task 5):
  - Break inserted before second site on same sheet
  - No break before first site (start_row == purge_from)
  - Image that fits on current page → no push
  - Image that overflows → pushed to next page
  - Multiple images within same site → overflow guard triggers correctly

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core page-break algorithm with boundary math, must get off-by-one correct
  - **Skills**: [`xlsx`]
    - `xlsx`: Working with openpyxl page breaks, row calculations

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 1 for helpers)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 3, 4, 5, 6
  - **Blocked By**: Task 1

  **References**:
  - `5-png-inserter/src/inserter.py:91-121` — Current `insert_png()` signature and image placement logic
  - `5-png-inserter/src/inserter.py:123-151` — Current `insert_png_no_label()` signature and logic
  - `5-png-inserter/src/inserter.py:113-114` — `rows_needed` calculation to reuse
  - `openpyxl.worksheet.pagebreak.Break` — `Break(id=N)` constructor, break occurs BEFORE row N
  - `openpyxl.worksheet.pagebreak.RowBreak` — `ws.row_breaks.append(Break(id=N))` API
  - Git commit `a9d82eb:5-png-inserter/src/inserter.py` — Old page boundary logic (reference for pattern, NOT copy-paste)

  **Acceptance Criteria**:
  - [ ] `Break` imported at top of `inserter.py`
  - [ ] `insert_png()` and `insert_png_no_label()` accept `page_rows` parameter
  - [ ] `insert_png()` inserts break before label when `start_row > purge_from` and `page_rows` is set
  - [ ] `insert_png_no_label()` checks overflow and pushes to next page when needed
  - [ ] When `page_rows=None`, no breaks inserted (backward compat)
  - [ ] Break math uses correct convention: `Break(id=X)` → break BEFORE row X

  **QA Scenarios**:

  ```
  Scenario: Break inserted before second site on same sheet
    Tool: Bash (pytest)
    Preconditions: Test XLSX with two sites, page_break_before_label=true
    Steps:
      1. Run inserter with two sites on same sheet
      2. Open output XLSX with openpyxl
      3. Read ws.row_breaks.brk → list of Break objects
      4. Check at least one Break.id exists
      5. Verify first Break.id > purge_from (not first site)
    Expected Result: Break list non-empty, break IDs above purge_from
    Failure Indicators: Empty brk, break.id == purge_from, AttributeError
    Evidence: .sisyphus/evidence/task-2-site-break.txt

  Scenario: Image overflows page → pushed to next page
    Tool: Bash (pytest)
    Preconditions: page_rows=10 (small for testing), large image
    Steps:
      1. Start at row 8 (near page end)
      2. Insert image that needs 5 rows
      3. Verify image row > page_end (10)
    Expected Result: Image placed at row >= 12 (page_end + 1 + gap)
    Failure Indicators: Image placed at row 8-10, image crosses page 10 boundary
    Evidence: .sisyphus/evidence/task-2-overflow-guard.txt
  ```

  **Commit**: YES
  - Message: `feat(inserter): add page break protection to prevent image splitting`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/config.json`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_matcher.py -v` (existing 14 must pass)

- [x] 3. **Orchestrator changes in `insert.py`**

  **What to do**:
  - In `main()`: Read `page_break_before_label` from config (default `False`). Read optional `a4_page_rows` from config.
  - Call `_clear_page_breaks(ws)` during sheet setup when `page_break_before_label` is `False` (prevent stale breaks).
  - Calculate `page_rows`: if `page_break_before_label` is `True`, use `_calc_page_rows(ws, a4_page_rows)`; if `False`, use `None`.
  - Pass `page_rows` and `purge_from` to `insert_png()` and `insert_png_no_label()` calls.
  - Warn when an image's total row consumption exceeds page capacity (log warning, don't block).

  **Must NOT do**:
  - Do NOT change the pre-scan, group-by-site, or main loop structure
  - Do NOT add `print_title_rows` or `header_count` parsing
  - Do NOT change the `sheet_rows` tracking mechanism

  **Test cases to cover** (implemented in Task 4 + Task 6):
  - Config `page_break_before_label: true` → `page_rows` is calculated, passed to insert functions
  - Config `page_break_before_label: false` → `page_rows=None`, no breaks
  - Config missing → defaults to `false`, backward compat
  - Config `a4_page_rows: 40` → override used instead of auto-calc
  - Warning logged when image exceeds page capacity

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Config parsing + parameter passing, minimal logic
  - **Skills**: [`xlsx`]
    - `xlsx`: Understanding config.json structure and insert.py orchestration

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 2 for function signatures)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 4, 5, 6, 7, 8
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `5-png-inserter/insert.py:65-69` — Current config reading pattern
  - `5-png-inserter/insert.py:158-198` — Main loop where `insert_png()` and `insert_png_no_label()` are called
  - `5-png-inserter/insert.py:170-175` — Where `purge_sheet()` and `_setup_a4_print()` are called (per sheet)
  - `5-png-inserter/src/inserter.py:_calc_page_rows` — New function from Task 1
  - `5-png-inserter/src/inserter.py:_clear_page_breaks` — New function from Task 1

  **Acceptance Criteria**:
  - [ ] `page_break_before_label` parsed from config with default `False`
  - [ ] `a4_page_rows` parsed from config (optional, default `None`)
  - [ ] `page_rows` computed correctly and passed to insert functions
  - [ ] Warning logged when image row count > page_rows
  - [ ] `_clear_page_breaks()` called when feature disabled

  **QA Scenarios**:

  ```
  Scenario: page_break_before_label=false → no page_rows passed
    Tool: Bash (python insert.py)
    Preconditions: config has page_break_before_label: false, test PNGs + XLSX
    Steps:
      1. Run insert.py with test data
      2. Open output XLSX with openpyxl
      3. Read ws.row_breaks.brk
    Expected Result: row_breaks.brk is empty (or only pre-existing breaks)
    Failure Indicators: New Break objects found in output
    Evidence: .sisyphus/evidence/task-3-backward-compat.txt

  Scenario: page_break_before_label=true with a4_page_rows=40 override
    Tool: Bash (python insert.py)
    Preconditions: config has page_break_before_label: true, a4_page_rows: 40
    Steps:
      1. Run insert.py
      2. Verify _calc_page_rows was NOT called with auto-calc
      3. Verify page_rows=40 was used
    Expected Result: page_rows=40 passed to insert functions
    Failure Indicators: Uses auto-calc (~51) instead of 40
    Evidence: .sisyphus/evidence/task-3-config-override.txt
  ```

  **Commit**: NO (groups with Tasks 1-2)

- [x] 4. **TDD Tests — Config + backward compat + page setup**

  **What to do**:
  - Create `5-png-inserter/tests/test_page_breaks.py`
  - Write tests that will FAIL before implementation (RED phase):
    1. `test_page_break_before_label_true_enables_feature` — config with `true` → `page_rows` is not None
    2. `test_page_break_before_label_false_disables_feature` — config with `false` → `page_rows` is None
    3. `test_page_break_before_label_missing_defaults_false` — no key → `page_rows` is None (backward compat)
    4. `test_a4_page_rows_override` — `a4_page_rows: 40` → `_calc_page_rows()` returns 40
    5. `test_a4_page_rows_absent_autocalc` — no key → `_calc_page_rows()` returns ~51
    6. `test_auto_page_breaks_disabled` — after `_setup_a4_print()`, `ws.page_setup.autoPageBreaks` is `False`
    7. `test_clear_page_breaks_empties_brk` — `_clear_page_breaks()` on sheet with breaks → `brk` is empty
  - Use `tmp_path` fixture (matching existing test pattern from `conftest.py`)

  **Must NOT do**:
  - Do NOT test insert logic here (that's Task 5)
  - Do NOT import `insert_png` or `insert_png_no_label` (unit test config/helpers only)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard pytest tests with openpyxl, following existing patterns
  - **Skills**: [`xlsx`]
    - `xlsx`: XLSX manipulation with openpyxl in test context

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 5, 6)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `5-png-inserter/tests/test_matcher.py:1-30` — Test structure, imports, tmp_path usage pattern
  - `5-png-inserter/conftest.py` — sys.path setup for imports
  - `5-png-inserter/src/inserter.py:64-76` — `_setup_a4_print()` to test
  - `5-png-inserter/insert.py:65-69` — Config reading pattern to replicate in test setup

  **Acceptance Criteria**:
  - [ ] 7 tests written, all FAIL (RED phase) — feature not yet implemented
  - [ ] Tests use `tmp_path` for temporary XLSX files
  - [ ] Tests follow existing naming convention (`test_*` functions)

  **QA Scenarios**:

  ```
  Scenario: All 7 config/setup tests written and failing (RED)
    Tool: Bash (pytest)
    Preconditions: test_page_breaks.py created, implementation not yet done
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py -v
      3. Count failures
    Expected Result: 7 failed (all RED — TDD phase 1)
    Failure Indicators: Any test passes unexpectedly
    Evidence: .sisyphus/evidence/task-4-red-phase.txt

  Scenario: autoPageBreaks test specifically checks ws.page_setup path
    Tool: Bash (pytest)
    Preconditions: test written, _setup_a4_print not yet modified
    Steps:
      1. Run test_auto_page_breaks_disabled
      2. Verify it asserts on ws.page_setup.autoPageBreaks (not ws.autoPageBreaks)
    Expected Result: Test fails because autoPageBreaks not yet set to False
    Failure Indicators: AttributeError on wrong property path
    Evidence: .sisyphus/evidence/task-4-property-path.txt
  ```

  **Commit**: NO (groups with Task 5 after GREEN)

- [x] 5. **TDD Tests — Break insertion logic**

  **What to do**:
  - Add to `test_page_breaks.py` — write tests that FAIL before implementation:
    1. `test_break_before_second_site` — two sites on same sheet → Break at second site's label row
    2. `test_no_break_before_first_site` — first site at purge_from → no break inserted
    3. `test_overflow_guard_pushes_image` — image near page boundary → placed on next page
    4. `test_image_fits_no_push` — image fits within page → stays on current page
    5. `test_multiple_small_images_fill_page` — 3 small images, 3rd overflows → pushed
    6. `test_break_ids_correct_convention` — Break(id=X) means break BEFORE row X (verify in output)
  - Use real XLSX with real PNG insertion (or mock the image with known dimensions)
  - Read breaks back via `ws.row_breaks.brk` (NOT direct iteration)
  - Verify row positions, not just break existence

  **Must NOT do**:
  - Do NOT iterate `ws.row_breaks` directly — yields tuples, not Break objects
  - Do NOT test with real PNG files if a mock/stub `Image` works
  - Do NOT test config behavior (Task 4 covers that)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex test setup with XLSX + image insertion + break verification
  - **Skills**: [`xlsx`]
    - `xlsx`: Deep openpyxl knowledge for creating test fixtures and reading breaks

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 6)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `5-png-inserter/tests/test_matcher.py:120-213` — `TestInsertPng` class for insert test patterns
  - `5-png-inserter/src/inserter.py:91-121` — `insert_png()` to test
  - `5-png-inserter/src/inserter.py:123-151` — `insert_png_no_label()` to test
  - `openpyxl.worksheet.pagebreak.Break` — Break object structure
  - `openpyxl.drawing.image.Image` — Image object for test fixtures

  **Acceptance Criteria**:
  - [ ] 6 tests written, all FAIL (RED phase)
  - [ ] Tests read breaks via `ws.row_breaks.brk` (correct API)
  - [ ] Tests verify both break existence AND correct row positions

  **QA Scenarios**:

  ```
  Scenario: Two-site test verifies second site gets break
    Tool: Bash (pytest)
    Preconditions: test_break_before_second_site written, not yet implemented
    Steps:
      1. Run test — expect FAIL (RED)
      2. Verify test creates sheet with 2 sites, calls insert_png twice
      3. Verify test reads ws.row_breaks.brk and checks Break.id matches second label row
    Expected Result: Test fails (no breaks yet) — correctly structured
    Failure Indicators: Test passes before implementation, AttributeError on brk
    Evidence: .sisyphus/evidence/task-5-site-break-red.txt

  Scenario: Overflow guard test with small page_rows for easy testing
    Tool: Bash (pytest)
    Preconditions: test_overflow_guard_pushes_image uses page_rows=10
    Steps:
      1. Insert image near row 8 (end of "page")
      2. Image needs 5 rows (8+5=13 > 10)
      3. Verify image placed at row >= 12 (page 2 start)
    Expected Result: Test fails (no overflow guard yet)
    Failure Indicators: Image placed at row 8, wrong page math
    Evidence: .sisyphus/evidence/task-5-overflow-red.txt
  ```

  **Commit**: NO (groups with Task 4)

- [x] 6. **TDD Tests — Edge cases**

  **What to do**:
  - Add to `test_page_breaks.py` — write edge case tests:
    1. `test_single_image_taller_than_page` — image > page_rows → warning logged, image still inserted (overflows gracefully)
    2. `test_multi_sheet_independence` — breaks on Sheet1 don't affect Sheet2
    3. `test_gap_rows_zero` — `gap_rows=0` doesn't break overflow math
    4. `test_existing_breaks_cleared_when_disabled` — `_clear_page_breaks()` removes pre-existing breaks
  - Use Python's `logging` module or `capsys`/`caplog` fixture for warning verification

  **Must NOT do**:
  - Do NOT test normal break behavior (Task 5 covers that)
  - Do NOT skip edge cases because they're "unlikely"

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Edge case testing requires creative test setup and boundary condition verification
  - **Skills**: [`xlsx`]
    - `xlsx`: Openpyxl edge case manipulation

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `5-png-inserter/src/inserter.py:11` — `purge_sheet()` behavior
  - `5-png-inserter/config.json:10` — `insert_gap_rows: 1` current default
  - `5-png-inserter/src/inserter.py:113-114` — `rows_needed` formula for large image test
  - Python `logging.warning()` — for warning verification in test

  **Acceptance Criteria**:
  - [ ] 4 edge case tests written, all FAIL (RED phase)
  - [ ] Test covers gap_rows=0, multi-sheet, oversized image, stale break clearing
  - [ ] Warning test uses `caplog` or `capsys` fixture

  **QA Scenarios**:

  ```
  Scenario: Multi-sheet test verifies sheet independence
    Tool: Bash (pytest)
    Preconditions: test_multi_sheet_independence written
    Steps:
      1. Create workbook with 2 sheets
      2. Insert images on both sheets with page_break_before_label=true
      3. Verify Sheet1 has breaks, Sheet2 has its own breaks
      4. Verify Sheet1's breaks don't appear in Sheet2's brk
    Expected Result: Each sheet's breaks are independent
    Failure Indicators: Breaks cross-contaminated between sheets
    Evidence: .sisyphus/evidence/task-6-multi-sheet.txt

  Scenario: Oversized image logs warning, doesn't crash
    Tool: Bash (pytest)
    Preconditions: test_single_image_taller_than_page written
    Steps:
      1. Create image taller than page_rows
      2. Insert via insert_png
      3. Verify warning was logged
      4. Verify image was still inserted (no exception)
    Expected Result: Warning in log, image in sheet
    Failure Indicators: Crash, no warning, image missing
    Evidence: .sisyphus/evidence/task-6-oversized.txt
  ```

  **Commit**: NO (groups with Tasks 4-5 after GREEN)

- [x] 7. **GREEN phase — Implement to pass all tests + run full suite**

  **What to do**:
  - Implement the actual code changes in Tasks 1-3 to make ALL tests from Tasks 4-6 pass (GREEN phase)
  - Run full test suite: `cd 5-png-inserter && python -m pytest tests/ -v`
  - Verify: 14 existing tests + 17 new tests = 31 pass
  - Fix any failures
  - If any existing test breaks, investigate and fix (backward compat is mandatory)
  - Run REFACTOR pass: clean up any duplication, improve readability, remove debug prints

  **Must NOT do**:
  - Do NOT modify existing tests to make them pass
  - Do NOT skip any failing test
  - Do NOT leave `print()` debug statements in production code

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integration work across all changes, must ensure nothing breaks
  - **Skills**: [`xlsx`]
    - `xlsx`: Full openpyxl knowledge across all modified files

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all previous tasks)
  - **Parallel Group**: Wave 2 (final step)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 1, 2, 3, 4, 5, 6

  **References**:
  - `5-png-inserter/tests/test_matcher.py` — All existing tests (must pass)
  - `5-png-inserter/tests/test_page_breaks.py` — All new tests (must pass)
  - `5-png-inserter/insert.py` — Entry point
  - `5-png-inserter/src/inserter.py` — Core logic

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/ -v` → 31 passed, 0 failed
  - [ ] All 14 existing tests pass unchanged
  - [ ] All 17 new tests pass
  - [ ] No `print()` statements, no commented-out code, no `# TODO`

  **QA Scenarios**:

  ```
  Scenario: Full test suite passes — GREEN phase complete
    Tool: Bash (pytest)
    Preconditions: All implementation done
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/ -v
      3. Count passed/failed
    Expected Result: 31 passed, 0 failed
    Failure Indicators: Any test failure, any existing test broke
    Evidence: .sisyphus/evidence/task-7-green-phase.txt
  ```

  **Commit**: YES
  - Message: `test(inserter): add page break tests, all 31 passing`
  - Files: `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/ -v`

- [x] 8. **Final integration QA — Run tool end-to-end with real data**

  **What to do**:
  - Set up `page_break_before_label: true` in config
  - Run: `cd 5-png-inserter && python insert.py`
  - Open each output XLSX with openpyxl, verify:
    - `ws.page_setup.autoPageBreaks` is `False` on every sheet
    - `ws.row_breaks.brk` contains Break objects where expected (second+ sites)
    - No images placed at rows that would cross a page boundary
  - Set `page_break_before_label: false`, re-run, verify zero new breaks
  - Verify output XLSX opens in Excel with correct Page Break Preview

  **Must NOT do**:
  - Do NOT skip the `false` config re-run (backward compat verification)
  - Do NOT skip any output file — check all sheets in all output XLSXs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Comprehensive end-to-end verification requiring attention to detail
  - **Skills**: [`xlsx`]
    - `xlsx`: Reading XLSX output, verifying page breaks, checking sheet properties

  **Parallelization**:
  - **Can Run In Parallel**: NO (final verification gate)
  - **Parallel Group**: Wave 2 (final step)
  - **Blocks**: FINAL wave
  - **Blocked By**: Task 7

  **References**:
  - `5-png-inserter/output/` — Output XLSX files to verify (config path: `./out`)
  - `5-png-inserter/config.json` — Config to toggle
  - `run.py` — Full pipeline runner (optional, can run tool standalone)

  **Acceptance Criteria**:
  - [ ] With `page_break_before_label: true`: breaks present in all applicable sheets
  - [ ] With `page_break_before_label: false`: no new breaks (backward compat)
  - [ ] `autoPageBreaks = False` on all sheets
  - [ ] No images at page-boundary-crossing rows

  **QA Scenarios**:

  ```
  Scenario: End-to-end run with page_break_before_label=true
    Tool: Bash (python insert.py + openpyxl)
    Preconditions: PNGs in input/, XLSXs in xlsx/, config has page_break_before_label: true
    Steps:
      1. cd 5-png-inserter
      2. python insert.py
      3. For each .xlsx in out/:
         a. wb = load_workbook(file)
         b. For each sheet: assert ws.page_setup.autoPageBreaks == False
         c. If sheet has >1 site: assert len(ws.row_breaks.brk) > 0
      4. Print summary: files checked, sheets checked, breaks found
    Expected Result: All sheets have autoPageBreaks=False, multi-site sheets have breaks
    Failure Indicators: autoPageBreaks not False, no breaks on multi-site sheet, crash
    Evidence: .sisyphus/evidence/task-8-e2e-enabled.txt

  Scenario: Backward compat run with page_break_before_label=false
    Tool: Bash (python insert.py + openpyxl)
    Preconditions: Same data, config has page_break_before_label: false
    Steps:
      1. python insert.py
      2. For each .xlsx in out/:
         a. Check ws.row_breaks.brk is empty (or unchanged from before)
      3. Verify output looks identical to pre-feature run
    Expected Result: No new breaks, output identical to baseline
    Failure Indicators: New Break objects found
    Evidence: .sisyphus/evidence/task-8-e2e-disabled.txt
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run test). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Review all changed files for: leftover `print()`, commented-out code, unused imports, magic numbers. Check AI slop: excessive comments, generic names. Verify `ws.page_setup.autoPageBreaks` (not `ws.autoPageBreaks`). Verify `ws.row_breaks.brk` used (not direct iteration).
  Output: `Build [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high` (+ `xlsx` skill)
  Start from clean state. Run tool with `page_break_before_label: true` and `false`. Execute EVERY QA scenario from EVERY task. Test cross-task integration: config → calculation → break insertion → output verification. Test edge cases: zero sites, single site, many sites, oversized image. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (`git diff`). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Commit 1**: `feat(inserter): add page break protection to prevent image splitting`
  - Files: `5-png-inserter/config.json`, `5-png-inserter/src/inserter.py`, `5-png-inserter/insert.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_matcher.py -v` (existing 14 must pass)

- **Commit 2**: `test(inserter): add page break tests, all 31 passing`
  - Files: `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/ -v`

---

## Success Criteria

### Verification Commands
```bash
cd 5-png-inserter
python -m pytest tests/ -v                    # Expected: 31 passed
python insert.py                               # Expected: runs without error, output in out/
python -c "from openpyxl import load_workbook; wb = load_workbook('out/test_fixture.xlsx'); ws = wb.active; print(ws.page_setup.autoPageBreaks)"  # Expected: False
```

### Final Checklist
- [ ] All "Must Have" present (backward compat, auto-calc, site breaks, overflow guard, autoPageBreaks)
- [ ] All "Must NOT Have" absent (no print_title_rows, no header_count, no letter support, no ws.autoPageBreaks)
- [ ] All 31 tests pass (14 existing + 17 new)
- [ ] Feature opt-in via `page_break_before_label: true`
- [ ] Backward compat with `page_break_before_label: false`
- [ ] Evidence files in `.sisyphus/evidence/`

