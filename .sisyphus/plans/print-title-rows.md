# Print Title Rows — Header Repetition on Every Printed Page

## TL;DR

> **Quick Summary**: Add configurable `print_title_rows` (e.g., `"1:6"`) so header rows repeat at the top of every printed A4 page. Header rows reduce usable content area per page from 52 to `52 - header_count`. Snap and overflow formulas must account for the offset.
>
> **Deliverables**:
> - Config key `print_title_rows` parsed with input validation and graceful fallback
> - `_setup_a4_print()` updated to set `ws.print_title_rows` from config
> - Snap formula fixed for header-aware page boundaries (with Metis-identified off-by-one correction)
> - Overflow guard updated in both `insert_png()` and `insert_png_no_label()`
> - Full test coverage (TDD): config parsing, property setting, snap, overflow, integration, backward compat
> - Excel COM calibration to verify real-world page break positions
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves + final verification
> **Critical Path**: Task 1 → Task 6 → Task 7 → Final Verification

---

## Context

### Original Request
Add `print_title_rows` support to the 5-png-inserter tool so template header rows (rows 1-6) appear at the top of every printed A4 page, not just page 1.

### Interview Summary
**Key Discussions**:
- **Plan approach**: Generate fresh Prometheus-quality execution plan (not use existing rough plan as-is)
- **Test strategy**: TDD — write failing tests first, RED → GREEN → REFACTOR per task
- **Test infrastructure**: 31 existing pytest tests (test_matcher.py: 14, test_page_breaks.py: 17), tmp_path fixtures, conftest.py adds tool root to sys.path

**Research Findings**:
- **No existing print_title_rows code** — clean slate, zero references anywhere in the codebase
- **All call sites use keyword arguments** for params we'll add — no signature breakage risk with sensible defaults
- **`_setup_a4_print(ws)`** line 69, `_calc_page_rows(ws, config_override=None)` line 84, `insert_png()` line 105, `insert_png_no_label()` line 180 — all in inserter.py
- **Config loading** at insert.py lines 22-24, per-sheet init block at lines 172-187
- **Snap formula** (line 140): `page_end = ((start_row - 2) // page_rows + 1) * page_rows + 1`
- **Overflow guard** (lines 151, 209): `page_end = ((start_row - 1) // page_rows + 1) * page_rows`

### Metis Review
**Identified Gaps** (all addressed in plan):

| # | Gap | Severity | Resolution |
|---|-----|----------|------------|
| 1 | Snap formula off-by-one at exact page boundaries (`-1` should be `-2`) | 🔴 Critical | Fixed in Task 3 — verified boundary-preserving for rows 53, 99, 145 |
| 2 | No input validation for malformed `print_title_rows` strings (`"1:"`, `":6"`, `"a:b"`) | 🟡 Medium | Added try/except with graceful fallback in Task 1 |
| 3 | No warning for degenerate `content_rows` (e.g., `header_count=51` → 1 content row/page) | 🟡 Low | Warning when `content_rows < 5` in Task 1 |
| 4 | `print_title_rows` overlap with `purge_from` not validated | 🟡 Medium | Validation: if `end_row > purge_from`, warn + document limitation in Task 1 |
| 5 | Column print titles not explicitly excluded | 🟡 Low | Added to "Must NOT Have" guardrails |
| 6 | `autoPageBreaks` + manual content accounting double-count risk | 🟡 Low | Documented in Verification Strategy — validated via Excel COM in Final QA |

---

## Work Objectives

### Core Objective
Add `print_title_rows` support so header rows repeat on every printed A4 page, with snap-to-page and overflow-guard logic correctly accounting for reduced content area per page.

### Concrete Deliverables
- `5-png-inserter/config.json` — new `print_title_rows` key with comment
- `5-png-inserter/src/inserter.py` — updated `_setup_a4_print()`, `insert_png()`, `insert_png_no_label()` signatures and formulas
- `5-png-inserter/insert.py` — config parsing, header_count flow, updated call sites
- `5-png-inserter/tests/test_page_breaks.py` — new test class `TestPrintTitleRows` (~9 tests)
- `5-png-inserter/tests/test_matcher.py` — no changes (backward compat verified)

### Definition of Done
- [ ] `python -m pytest tests/ -v` — all tests pass (31 existing + 9 new = 40+)
- [ ] `python insert.py` with `print_title_rows="1:6"` — no crashes, correct debug output
- [ ] Excel COM verification: auto-breaks at correct positions with headers active
- [ ] Backward compat: `print_title_rows=null` behaves identically to current

### Must Have
- Config key `print_title_rows` parsed from Excel-format string (`"1:6"`)
- `_setup_a4_print()` sets `ws.print_title_rows` from config value
- Snap formula preserves exact page boundary rows (53, 99, 145 stay at those rows)
- Overflow guard uses `content_rows = page_rows - header_count` for fit checks
- Input validation with graceful fallback for malformed config values
- All 31 existing tests pass unchanged with `header_count=0` (default)

### Must NOT Have (Guardrails)
- **NO column print titles** (`print_title_cols`) — out of scope
- **NO multi-range** `print_title_rows` (e.g., `"1:3,8:10"`) — error if detected
- **NO per-sheet header variance** — config is global (consistent with project pattern)
- **NO CLI flags** — config-file-only pattern (consistent with all other tools)
- **NO changes to `_calc_page_rows()` signature or return value** — it stays returning 52
- **NO changes to `autoPageBreaks` behavior** — stays `True`
- **NO changes to tools 1-4** or shared `matching.xlsx` infrastructure

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES — pytest with 31 tests, tmp_path fixtures
- **Automated tests**: TDD — each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR
- **Framework**: pytest (existing)

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Python/pytest**: Use Bash — `python -m pytest tests/ -v -k "test_name"`
- **Excel COM calibration**: Use Bash — PowerShell COM script to open XLSX and inspect `HPageBreaks`
- **CLI integration**: Use Bash — `cd 5-png-inserter && python insert.py`

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation, MAX PARALLEL):
├── Task 1: Config parsing + input validation [TDD, quick]
├── Task 2: _setup_a4_print() print_title_rows support [TDD, quick]

Wave 2 (After Wave 1 — formula updates, MAX PARALLEL):
├── Task 3: Snap formula with header_count in insert_png() [TDD, deep]
├── Task 4: Overflow guard with header_count in insert_png() [TDD, deep]
├── Task 5: Overflow guard with header_count in insert_png_no_label() [TDD, deep]

Wave 3 (After Wave 2 — integration):
├── Task 6: Wire header_count through insert.py call chain [quick]
├── Task 7: Integration tests + backward compat verification [deep]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan Compliance Audit (oracle)
├── Task F2: Code Quality Review (unspecified-high)
├── Task F3: Real Manual QA — Excel COM calibration (unspecified-high)
└── Task F4: Scope Fidelity Check (deep)
```

**Critical Path**: Task 1 → Task 6 → Task 7 → Final Verification
**Parallel Speedup**: ~55% faster than sequential (Tasks 1-2 in parallel, 3-5 in parallel)
**Max Concurrent**: 3 (Wave 2)

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 3, 4, 5, 6 | 1 |
| 2 | — | 6 | 1 |
| 3 | 1 | — | 2 |
| 4 | 1 | — | 2 |
| 5 | 1 | — | 2 |
| 6 | 1, 2 | 7 | 3 |
| 7 | 6 | F1-F4 | 3 |
| F1-F4 | 7 | — | FINAL |

---

## TODOs

- [x] 1. **Config parsing + input validation (TDD)**

  **What to do**:
  - **RED**: Write 5 failing tests in new `TestPrintTitleRows` class in `test_page_breaks.py`:
    1. `test_parse_print_title_rows_valid` — `"1:6"` → `header_count=6`
    2. `test_parse_print_title_rows_null` — `None` → `header_count=0`
    3. `test_parse_print_title_rows_malformed_colon_only` — `"1:"` → `header_count=0` + stderr warning
    4. `test_parse_print_title_rows_malformed_non_numeric` — `"a:b"` → `header_count=0` + stderr warning
    5. `test_parse_print_title_rows_degenerate` — `"1:51"` with `page_rows=52` → `header_count=51`, `content_rows=1`, stderr warning
  - **GREEN**: In `insert.py` (near config loading at lines 22-69), add parsing function:
    ```python
    def _parse_print_title_rows(value, page_rows=None):
        """Parse print_title_rows config value. Returns (header_count, print_title_rows_str)."""
        header_count = 0
        title_str = None
        if value and isinstance(value, str) and ":" in value:
            parts = value.split(":")
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                if len(parts) > 2:
                    raise ValueError("Multi-range not supported")
                header_count = end - start + 1
                title_str = value
                if page_rows and header_count >= page_rows:
                    print(f"WARNING: print_title_rows header_count ({header_count}) >= page_rows ({page_rows}), disabling", file=sys.stderr)
                    header_count = 0
                    title_str = None
                elif page_rows and (page_rows - header_count) < 5:
                    print(f"WARNING: print_title_rows leaves only {page_rows - header_count} content rows per page", file=sys.stderr)
            except (ValueError, IndexError) as e:
                print(f"WARNING: Invalid print_title_rows '{value}' ({e}), disabling", file=sys.stderr)
                header_count = 0
        return header_count, title_str
    ```
  - Add `"print_title_rows": null` to `config.json` with `"_comment_print_title_rows"` key
  - Read config key: `print_title_rows_raw = config.get("print_title_rows")`
  - **REFACTOR**: Verify all 5 tests pass, ensure debug messages go to stderr

  **Must NOT do**:
  - Do NOT add CLI flags — config-file-only pattern
  - Do NOT support multi-range (e.g., `"1:3,8:10"`) — raise ValueError
  - Do NOT change any existing config keys

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single function + config key addition, well-bounded scope
  - **Skills**: [`xlsx`]
    - `xlsx`: Understanding openpyxl config patterns in the project

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 3, 4, 5, 6
  - **Blocked By**: None (can start immediately)

  **References**:
  - `5-png-inserter/insert.py:22-69` — Config loading pattern: how keys are read, default values applied, variables named
  - `5-png-inserter/config.json:1-17` — Current config structure, `_comment` key naming convention
  - `5-png-inserter/insert.py:207-208` — Warning message pattern for `sys.stderr` output
  - `5-png-inserter/tests/test_page_breaks.py:58-68` — Test pattern: `_make_test_xlsx` + inline workbook creation

  **Acceptance Criteria**:
  - [ ] `config.json` contains `"print_title_rows": null` with comment key
  - [ ] `_parse_print_title_rows("1:6")` returns `(6, "1:6")`
  - [ ] `_parse_print_title_rows(None)` returns `(0, None)`
  - [ ] `_parse_print_title_rows("1:")` returns `(0, None)` + stderr warning
  - [ ] `_parse_print_title_rows("1:52", page_rows=52)` returns `(0, None)` + stderr warning (guard)
  - [ ] `_parse_print_title_rows("1:49", page_rows=52)` returns `(49, "1:49")` + stderr warning (content_rows=3 < 5)

  **QA Scenarios**:
  ```
  Scenario: Valid config parsed correctly
    Tool: Bash
    Preconditions: pytest installed, config.json has print_title_rows="1:6"
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_parse_print_title_rows_valid -v
    Expected Result: 1 test PASS, header_count=6 returned
    Failure Indicators: Test FAIL, ValueError raised, or wrong header_count
    Evidence: .sisyphus/evidence/task-1-valid-parse.txt

  Scenario: Malformed config gracefully handled
    Tool: Bash
    Preconditions: Test uses mock config value "1:"
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_parse_print_title_rows_malformed_colon_only -v
    Expected Result: 1 test PASS, header_count=0 returned, stderr contains "WARNING"
    Failure Indicators: Test FAIL or ValueError uncaught (crash)
    Evidence: .sisyphus/evidence/task-1-malformed.txt
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(inserter): add print_title_rows config parsing with validation`
  - Files: `5-png-inserter/config.json`, `5-png-inserter/insert.py`, `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_page_breaks.py -v -k "parse_print_title_rows"`

- [x] 2. **Update `_setup_a4_print()` to accept and set print_title_rows (TDD)**

  **What to do**:
  - **RED**: Write 2 failing tests in `TestPrintTitleRows`:
    1. `test_setup_a4_print_sets_print_title_rows` — `_setup_a4_print(ws, "1:6")` → `ws.print_title_rows == "1:6"`
    2. `test_setup_a4_print_none_does_not_set` — `_setup_a4_print(ws, None)` → `ws.print_title_rows` is None or unset
  - **GREEN**: In `src/inserter.py` line 69, change signature:
    ```python
    def _setup_a4_print(ws, print_title_rows=None):
    ```
    Add after the margins block (after line 78):
    ```python
    if print_title_rows:
        ws.print_title_rows = print_title_rows
    ```
    Update the debug print on line 81 to include `print_title_rows` value:
    ```python
    print(f"[DEBUG] _setup_a4_print: ... print_title_rows={print_title_rows}", file=sys.stderr)
    ```
  - **REFACTOR**: Verify tests pass, ensure existing 31 tests still pass (backward compat via default `None`)

  **Must NOT do**:
  - Do NOT change the margins or paper size
  - Do NOT change `autoPageBreaks` behavior
  - Do NOT add validation logic here — that's Task 1's responsibility

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single function signature change, 2-line implementation
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl `ws.print_title_rows` property usage

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 6
  - **Blocked By**: None (can start immediately — tests define expected API contract)

  **References**:
  - `5-png-inserter/src/inserter.py:69-81` — Current `_setup_a4_print()` full implementation
  - `5-png-inserter/insert.py:178` — Call site: `_setup_a4_print(wb[sheet_name])`
  - `5-png-inserter/tests/test_page_breaks.py:114-120` — `test_auto_page_breaks_enabled` — existing test pattern for `_setup_a4_print`

  **Acceptance Criteria**:
  - [ ] `_setup_a4_print(ws, "1:6")` sets `ws.print_title_rows = "1:6"`
  - [ ] `_setup_a4_print(ws, None)` leaves `ws.print_title_rows` unset/None
  - [ ] `_setup_a4_print(ws)` (no arg) preserves backward compat (default None)
  - [ ] Existing test `test_auto_page_breaks_enabled` still passes

  **QA Scenarios**:
  ```
  Scenario: print_title_rows property set on worksheet
    Tool: Bash
    Preconditions: pytest installed
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_setup_a4_print_sets_print_title_rows -v
    Expected Result: 1 test PASS, ws.print_title_rows == "1:6"
    Failure Indicators: Test FAIL, AttributeError on ws.print_title_rows, or wrong value
    Evidence: .sisyphus/evidence/task-2-property-set.txt

  Scenario: Backward compat — no print_title_rows argument
    Tool: Bash
    Preconditions: pytest installed
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPageBreakConfig::test_auto_page_breaks_enabled -v
    Expected Result: 1 test PASS (existing test unchanged)
    Failure Indicators: Test FAIL due to signature mismatch
    Evidence: .sisyphus/evidence/task-2-backward-compat.txt
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(inserter): add print_title_rows support to _setup_a4_print`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/ -v -k "setup_a4_print or auto_page_breaks"`

- [x] 3. **Update snap formula in `insert_png()` for header_count (TDD)**

  **What to do**:
  - **RED**: Write 3 failing tests in `TestPrintTitleRows` using `_make_test_png` + `_make_test_xlsx`:
    1. `test_snap_with_headers_keeps_boundary` — `start_row=53, page_rows=52, header_count=6, purge_from=10` → label stays at row 53 (boundary preserved)
    2. `test_snap_with_headers_mid_page` — `start_row=54, page_rows=52, header_count=6, purge_from=10` → label snaps to row 99 (next boundary with offset)
    3. `test_snap_no_headers_unchanged` — `start_row=53, page_rows=52, header_count=0, purge_from=10` → label stays at row 53 (original behavior preserved)
  - **GREEN**: In `src/inserter.py`, update `insert_png()` (lines 137-146):
    Add `header_count=0` parameter (before `page_rows`):
    ```python
    def insert_png(xlsx_path, sheet_name, png_path, label, start_row,
                   merge_to_col=None, gap_rows=1, col="A",
                   display_width=None, page_rows=None, purge_from=0,
                   header_count=0):
    ```
    Replace snap logic (lines 137-146) with:
    ```python
    if page_rows is not None and start_row > purge_from:
        if header_count and header_count > 0:
            content_rows = page_rows - header_count
            if start_row <= page_rows:
                page_end = page_rows + 1  # snap to page 2 start (row 53)
            else:
                offset = start_row - page_rows - 2  # CRITICAL: -2 preserves boundaries (Metis fix)
                pages_after = offset // content_rows + 1
                page_end = page_rows + 1 + pages_after * content_rows
        else:
            page_end = ((start_row - 2) // page_rows + 1) * page_rows + 1
        start_row = max(start_row, page_end)
    ```
    Add debug print showing `header_count` and `content_rows` (follow existing pattern at lines 141-146).
  - **REFACTOR**: Verify 3 new + 17 existing page_break tests pass

  **Must NOT do**:
  - Do NOT change the `purge_from` guard logic (`start_row > purge_from` stays)
  - Do NOT use `-1` offset — Metis identified this as buggy (use `-2`)
  - Do NOT modify `_calc_page_rows()` — header_count flows separately

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Formula change with boundary math — requires careful verification of edge cases
  - **Skills**: [`xlsx`]
    - `xlsx`: Understanding of openpyxl row insertion and page layout

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 1 (needs parsed header_count concept)

  **References**:
  - `5-png-inserter/src/inserter.py:137-146` — Current snap formula with debug prints
  - `5-png-inserter/tests/test_page_breaks.py:143-164` — `test_snap_to_page_boundary` — existing snap test pattern
  - `5-png-inserter/tests/test_page_breaks.py:19-35` — `_make_test_png()` helper — how test PNGs are created
  - `5-png-inserter/tests/test_page_breaks.py:38-48` — `_make_test_xlsx()` helper — how test workbooks are created

  **Acceptance Criteria**:
  - [ ] `insert_png(..., page_rows=52, header_count=6, start_row=53, purge_from=10)` → label at row 53 (kept)
  - [ ] `insert_png(..., page_rows=52, header_count=6, start_row=54, purge_from=10)` → label at row 99 (snapped)
  - [ ] `insert_png(..., page_rows=52, header_count=0, start_row=53, purge_from=10)` → label at row 53 (original)
  - [ ] Existing test `test_snap_to_page_boundary` still passes
  - [ ] Existing test `test_no_break_before_first_site` still passes

  **QA Scenarios**:
  ```
  Scenario: Boundary row preserved with headers
    Tool: Bash
    Preconditions: pytest installed
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_snap_with_headers_keeps_boundary -v
    Expected Result: 1 test PASS, label inserted at row 53 (not 99)
    Failure Indicators: Test FAIL or label at wrong row (99 instead of 53)
    Evidence: .sisyphus/evidence/task-3-boundary-kept.txt

  Scenario: Mid-page snap with headers
    Tool: Bash
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_snap_with_headers_mid_page -v
    Expected Result: 1 test PASS, label snapped from 54 to 99
    Failure Indicators: Label at wrong row or not snapped at all
    Evidence: .sisyphus/evidence/task-3-midpage-snap.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `fix(inserter): update snap formula for header_count with boundary-preserving offset`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_page_breaks.py -v -k "snap"`

- [x] 4. **Update overflow guard in `insert_png()` for header_count (TDD)**

  **What to do**:
  - **RED**: Write 2 failing tests in `TestPrintTitleRows`:
    1. `test_overflow_with_headers_pushes` — `insert_png(..., page_rows=10, header_count=2, start_row=9, purge_from=1, gap_rows=0)` with 100px tall PNG → image pushed past row 10 (content_rows=8, row 9-10 only 2 rows left)
    2. `test_overflow_no_headers_unchanged` — same scenario with `header_count=0` → verify original overflow behavior preserved
  - **GREEN**: In `src/inserter.py`, update overflow guard in `insert_png()` (lines 148-156):
    Replace with:
    ```python
    if page_rows is not None:
        img_end = start_row + 1 + gap_rows + rows_needed
        if header_count and header_count > 0:
            content_rows = page_rows - header_count
            if start_row <= page_rows:
                page_end = page_rows  # end of page 1 content = row 52
            else:
                offset = start_row - page_rows - 1
                pages_before = offset // content_rows
                page_end = page_rows + (pages_before + 1) * content_rows
        else:
            page_end = ((start_row - 1) // page_rows + 1) * page_rows
        if img_end > page_end:
            start_row = page_end + 1
    ```
    Add debug print showing `header_count`, `content_rows`, and overflow decision.
  - **REFACTOR**: Verify 2 new + all existing overflow tests pass

  **Must NOT do**:
  - Do NOT change the `img_end` formula (`start_row + 1 + gap_rows + rows_needed` stays — the `+1` is the label row)
  - Do NOT change `page_end` formula for `header_count=0` case

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Formula change parallel to Task 3, similar boundary math
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl image insertion and row layout

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 3, 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 1 (needs header_count concept)

  **References**:
  - `5-png-inserter/src/inserter.py:148-156` — Current overflow guard in `insert_png()`
  - `5-png-inserter/tests/test_page_breaks.py:181-193` — `test_overflow_guard_pushes_image` — existing overflow test pattern
  - `5-png-inserter/tests/test_page_breaks.py:195-206` — `test_image_fits_no_push` — non-overflow verification

  **Acceptance Criteria**:
  - [ ] Tall image near page end with headers → pushed to next page
  - [ ] Small image within page boundary with headers → stays
  - [ ] `header_count=0` → identical overflow behavior to current
  - [ ] `test_overflow_guard_pushes_image` still passes
  - [ ] `test_image_fits_no_push` still passes

  **QA Scenarios**:
  ```
  Scenario: Overflow with headers pushes image to next page
    Tool: Bash
    Preconditions: pytest installed
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_overflow_with_headers_pushes -v
    Expected Result: 1 test PASS, start_row pushed past page_end
    Failure Indicators: Test FAIL or image not pushed (would overflow in real Excel)
    Evidence: .sisyphus/evidence/task-4-overflow-push.txt

  Scenario: Backward compat — no headers, original overflow behavior
    Tool: Bash
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPageBreakInsertion::test_overflow_guard_pushes_image -v
    Expected Result: 1 test PASS (existing)
    Failure Indicators: Test FAIL
    Evidence: .sisyphus/evidence/task-4-backward-overflow.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `fix(inserter): update insert_png overflow guard for content_rows`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_page_breaks.py -v -k "overflow"`

- [x] 5. **Update overflow guard in `insert_png_no_label()` for header_count (TDD)**

  **What to do**:
  - **RED**: Write 1 failing test in `TestPrintTitleRows`:
    1. `test_overflow_no_label_with_headers` — `insert_png_no_label(..., page_rows=10, header_count=2, start_row=9, gap_rows=0)` with tall PNG → pushed past row 10
  - **GREEN**: In `src/inserter.py`, add `header_count=0` parameter to `insert_png_no_label()` (line 180):
    ```python
    def insert_png_no_label(xlsx_path, sheet_name, png_path, start_row,
                            gap_rows=1, col="A", display_width=None,
                            page_rows=None, header_count=0):
    ```
    Replace overflow guard (lines 206-214) with the same header-aware formula as Task 4, adapted for `img_end = start_row + gap_rows + rows_needed` (no `+1` — no label row):
    ```python
    if page_rows is not None:
        img_end = start_row + gap_rows + rows_needed
        if header_count and header_count > 0:
            content_rows = page_rows - header_count
            if start_row <= page_rows:
                page_end = page_rows
            else:
                offset = start_row - page_rows - 1
                pages_before = offset // content_rows
                page_end = page_rows + (pages_before + 1) * content_rows
        else:
            page_end = ((start_row - 1) // page_rows + 1) * page_rows
        if img_end > page_end:
            start_row = page_end + 1
    ```
  - **REFACTOR**: Verify new test + existing no_label tests pass

  **Must NOT do**:
  - Do NOT add snap logic to `insert_png_no_label()` — it intentionally has no snap, only overflow guard
  - Do NOT change `img_end` formula for no-label case (`start_row + gap_rows + rows_needed`)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward adaptation of Task 4's formula to a simpler function (no label row, no snap)
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl image insertion patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 3, 4)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 1 (needs header_count concept)

  **References**:
  - `5-png-inserter/src/inserter.py:180-222` — Full `insert_png_no_label()` implementation
  - `5-png-inserter/src/inserter.py:206-214` — Current overflow guard in `insert_png_no_label()`
  - `5-png-inserter/tests/test_page_breaks.py:208-224` — `test_multiple_small_images_fill_page` — existing no-label test

  **Acceptance Criteria**:
  - [ ] `insert_png_no_label(..., page_rows=10, header_count=2, start_row=9)` with tall PNG → pushed
  - [ ] `header_count=0` → identical to current behavior
  - [ ] `test_multiple_small_images_fill_page` still passes
  - [ ] `test_gap_rows_zero` still passes

  **QA Scenarios**:
  ```
  Scenario: No-label overflow with headers
    Tool: Bash
    Preconditions: pytest installed
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py::TestPrintTitleRows::test_overflow_no_label_with_headers -v
    Expected Result: 1 test PASS, image pushed past page boundary
    Failure Indicators: Test FAIL or image not pushed
    Evidence: .sisyphus/evidence/task-5-nolabel-overflow.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `fix(inserter): update insert_png_no_label overflow guard for content_rows`
  - Files: `5-png-inserter/src/inserter.py`, `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/test_page_breaks.py -v -k "no_label or gap_rows"`

- [x] 6. **Wire header_count through insert.py call chain**

  **What to do**:
  - In `insert.py`, at the config reading section (lines 26-69), use Task 1's `_parse_print_title_rows()`:
    ```python
    print_title_rows_raw = config.get("print_title_rows")
    header_count, print_title_rows_str = _parse_print_title_rows(print_title_rows_raw)
    ```
  - Update `_setup_a4_print()` call (line 178):
    ```python
    _setup_a4_print(wb[sheet_name], print_title_rows_str)
    ```
  - Update `insert_png()` call (line 197) — add `header_count=header_count` keyword arg
  - Update `insert_png_no_label()` call (line 202) — add `header_count=header_count` keyword arg
  - Update the post-insertion warning (lines 207-208) to use `content_rows`:
    ```python
    content_rows = pr_val - header_count if header_count and pr_val else pr_val
    if pr_val and (next_row - current_row) > content_rows:
        print(f"  WARNING: ... exceeding effective capacity of {content_rows}")
    ```
  - Verify no other call sites need updating

  **Must NOT do**:
  - Do NOT change the config loading pattern (global config, read once)
  - Do NOT add per-sheet header variance — config is global
  - Do NOT change `_calc_page_rows()` or how `sheet_page_rows` is populated

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Wiring — straightforward parameter passing through existing call chain
  - **Skills**: [`xlsx`]
    - `xlsx`: Familiarity with openpyxl and the project's config-to-function flow

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential)
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 1, 2, 3, 4, 5 (all function signatures must be finalized)

  **References**:
  - `5-png-inserter/insert.py:172-187` — Per-sheet init block where `_setup_a4_print` and `_calc_page_rows` are called
  - `5-png-inserter/insert.py:194-204` — `insert_png` and `insert_png_no_label` call sites with all keyword args
  - `5-png-inserter/insert.py:207-208` — Post-insertion warning message
  - `5-png-inserter/insert.py:22-69` — Config reading section (where to add `_parse_print_title_rows` call)

  **Acceptance Criteria**:
  - [ ] `print_title_rows="1:6"` in config → `header_count=6`, `print_title_rows_str="1:6"` passed through
  - [ ] `print_title_rows=null` → `header_count=0`, `print_title_rows_str=None` → no headers (backward compat)
  - [ ] `python insert.py` runs without crashes with test data
  - [ ] Debug output shows `header_count` and `print_title_rows` values

  **QA Scenarios**:
  ```
  Scenario: insert.py runs with print_title_rows configured
    Tool: Bash
    Preconditions: test fixture XLSX and PNGs in place, config.json has print_title_rows="1:3"
    Steps:
      1. cd 5-png-inserter
      2. python insert.py
    Expected Result: No crashes, output shows "print_title_rows=1:3" in debug
    Failure Indicators: Crash, AttributeError, or missing print_title_rows in output
    Evidence: .sisyphus/evidence/task-6-insert-run.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `feat(inserter): wire header_count through insert.py call chain`
  - Files: `5-png-inserter/insert.py`
  - Pre-commit: `cd 5-png-inserter && python insert.py` (sanity check — no crash)

- [x] 7. **Integration tests + backward compat verification**

  **What to do**:
  - Run ALL existing tests: `python -m pytest tests/ -v`
  - Verify all 31 existing tests pass with `header_count=0` (default behavior unchanged)
  - Run new test class `TestPrintTitleRows` — verify all ~9 new tests pass
  - Add 1 integration test: `test_full_pipeline_with_headers` — creates multi-sheet workbook, inserts PNGs with `header_count=3`, verifies labels at correct rows
  - Check debug output from `insert.py` with `print_title_rows="1:6"` for correct `header_count` and `content_rows` values
  - Test edge case: `print_title_rows` end row > `purge_from` → verify warning message produced

  **Must NOT do**:
  - Do NOT modify existing tests — only add new ones
  - Do NOT change test fixtures or conftest.py

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Comprehensive integration testing — runs full pipeline, checks backward compat, validates edge cases
  - **Skills**: [`xlsx`]
    - `xlsx`: End-to-end understanding of PNG inserter pipeline

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential — needs Task 6 complete)
  - **Blocks**: Final Verification (F1-F4)
  - **Blocked By**: Task 6

  **References**:
  - `5-png-inserter/tests/test_page_breaks.py:267-298` — `test_multi_sheet_no_manual_breaks` — multi-sheet integration test pattern
  - `5-png-inserter/tests/test_matcher.py:178-212` — `test_insert_creates_label_and_image` — end-to-end insert test pattern
  - `5-png-inserter/tests/test_page_breaks.py:1-17` — Import pattern and test class structure

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/ -v` — ALL tests pass (31 existing + 9+ new = 40+ total)
  - [ ] No existing test modified or broken
  - [ ] Integration test covers multi-sheet scenario with headers
  - [ ] Edge case: purge_from overlap produces warning (not crash)

  **QA Scenarios**:
  ```
  Scenario: Full test suite passes with headers
    Tool: Bash
    Preconditions: All implementation complete
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/ -v
    Expected Result: ALL tests PASS (40+), 0 failures, 0 errors
    Failure Indicators: Any test FAIL or ERROR
    Evidence: .sisyphus/evidence/task-7-full-suite.txt

  Scenario: Backward compat — null config runs identically
    Tool: Bash
    Preconditions: config.json has print_title_rows=null
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/ -v
    Expected Result: Same test count and pass rate as before feature
    Failure Indicators: Tests that previously passed now fail
    Evidence: .sisyphus/evidence/task-7-backward-compat.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `test(inserter): add integration tests and verify backward compat for print_title_rows`
  - Files: `5-png-inserter/tests/test_page_breaks.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/ -v`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval.**
> **Never mark F1-F4 as checked before getting user's okay.**

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. Verify: `print_title_rows` key exists in config.json, `_setup_a4_print()` accepts and sets `print_title_rows`, snap formula uses `-2` offset (not `-1`), overflow guard uses `content_rows`, input validation exists with try/except, all guardrails enforced (no column titles, no multi-range, no `_calc_page_rows` changes, no CLI flags). Search codebase for forbidden patterns.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [7/7] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Verify all tests pass (31 existing + new). Check changed files for: bare excepts, missing debug prints for new logic paths, inconsistent formula variable naming, commented-out code. Check `sys.stderr` prints follow existing patterns.
  Output: `Build [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA — Excel COM Calibration** — `unspecified-high`
  Create test XLSX with 200 data rows, `print_title_rows="1:6"`, `autoPageBreaks=True`, A4 settings. Open via Excel COM, verify auto-break positions at rows 53, 99, 145 (not 53, 105, 157 — because headers reduce effective content). Run `python insert.py` with test data and verify: no crashes, labels at correct page tops, `header_count=0` behaves identically to current. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `COM Breaks [PASS/FAIL] | Insert [PASS/FAIL] | Backward Compat [PASS/FAIL] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no column titles, no multi-range, no _calc_page_rows changes, no CLI flags, no tools 1-4 changes. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [7/7 compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Wave | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat(inserter): add print_title_rows config parsing with validation` | `config.json`, `insert.py` |
| 2 | `feat(inserter): add print_title_rows to _setup_a4_print` | `src/inserter.py` |
| 2 | `test(inserter): add TDD tests for config parsing and _setup_a4_print` | `tests/test_page_breaks.py` |
| 3 | `fix(inserter): update snap formula for header_count offset` | `src/inserter.py`, `tests/test_page_breaks.py` |
| 3 | `fix(inserter): update overflow guard for content_rows per page` | `src/inserter.py`, `tests/test_page_breaks.py` |
| 4 | `feat(inserter): wire header_count through insert.py call chain` | `insert.py` |
| 4 | `test(inserter): add integration tests + backward compat verification` | `tests/test_page_breaks.py` |

---

## Success Criteria

### Verification Commands
```bash
cd 5-png-inserter
python -m pytest tests/ -v                    # Expected: ALL pass (40+ tests)
python insert.py                               # Expected: no crashes, correct debug output
```

### Final Checklist
- [ ] All "Must Have" present (config key, _setup_a4_print, snap formula, overflow guard, input validation)
- [ ] All "Must NOT Have" absent (no column titles, multi-range, _calc_page_rows changes, CLI flags)
- [ ] All tests pass (31 existing + 9+ new)
- [ ] Excel COM calibration confirms correct page breaks with headers
- [ ] Backward compat: null config behaves identically to current
