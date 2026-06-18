# Page Break Protection + Print Title Rows for 3-column-copier

## TL;DR

> **Quick Summary**: Add A4 print setup, `print_title_rows` (repeat headers), and content-collision protection to the 3-column-copier. Two phases: Phase 1 copies proven patterns from 5-png-inserter (print setup + config keys), Phase 2 adds `insert_rows()` for true push-down + page-overflow guard in append mode.
>
> **Deliverables**:
> - New `src/print_setup.py` module with `_setup_a4_print`, `_calc_page_rows`, `_parse_print_title_rows`
> - Config keys: `a4_page_rows`, `print_title_rows`, `page_break_enabled`
> - Append mode: `insert_rows()` before paste to physically push content down
> - Page-overflow check: after paste, if pushed content overflows, snap to next page boundary
> - Full test coverage for all new behavior
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 2 waves + final verification
> **Critical Path**: Task 1 → Task 3 → Task 5 → Final Verification

---

## Context

### Original Request
Add page-break protection and repeat-header logic to 3-column-copier. When pasting many rows in append mode, existing content below gets physically pushed down. If the pushed-down content would overflow a printed page, push it to the next page. Also add `print_title_rows` to repeat header rows on every printed page — same as 5-png-inserter.

### Interview Summary
**Key Discussions**:
- **Content behavior**: User expects pasted rows to physically push existing content down (not overwrite)
- **Page break trigger**: Only push to next page if content below would overflow — not always
- **A4 settings**: Same as 5-png-inserter — 0.5" margins, 52 rows/page
- **Modes**: Applies to both append and overwrite modes; `insert_rows` only in append (preserve overwrite behavior)

**Research Findings**:
- Copier currently **overwrites** cells — `tws.cell().value = val` never inserts rows
- Append mode finds first empty row but **doesn't check** for content below it — can silently overwrite
- `_setup_a4_print`, `_calc_page_rows`, `_parse_print_title_rows` from 5-png-inserter are **fully reusable** with zero dependencies
- Copier has only 5 unit tests (columns.py) — **zero integration tests** for paste behavior

### Metis Review
**Identified Gaps** (all addressed):

| # | Gap | Resolution |
|---|-----|------------|
| 1 | Don't insert manual page breaks — use `autoPageBreaks=True` + snap | Plan uses snap-to-boundary, NOT `row_breaks.append()` |
| 2 | `insert_rows` only in append mode, preserve overwrite | Phase 2 guard: `if paste_mode == "append"` |
| 3 | New module for print functions | `src/print_setup.py` — clean separation |
| 4 | Merged cells risk when inserting rows | Detect merged cells, log warning, skip insert_rows |
| 5 | `page_break_before_label` name doesn't fit copier | Renamed to `page_break_enabled` |
| 6 | cleanup action out of scope | Explicitly excluded |

---

## Work Objectives

### Core Objective
Add A4 print setup, `print_title_rows` header repetition, and content-collision protection to the 3-column-copier so pasted data respects page boundaries and existing content is safely pushed down.

### Concrete Deliverables
- `3-column-copier/src/print_setup.py` — new module: `_setup_a4_print`, `_calc_page_rows`, `_parse_print_title_rows`
- `3-column-copier/config.json` — new keys: `a4_page_rows`, `print_title_rows`, `page_break_enabled`
- `3-column-copier/copier.py` — A4 setup call, `insert_rows` in append mode, page-overflow snap
- `3-column-copier/tests/test_print_setup.py` — new test file for print module (7 tests for Task 1 + 2 tests for Task 4 = 9 tests)
- `3-column-copier/tests/test_columns.py` — updated with append-mode tests (~3 tests)

### Definition of Done
- [ ] `python -m pytest tests/ -v` — all tests pass (5 existing + 7 + 3 + 2 + 1 new = 18)
- [ ] `python copier.py` with `page_break_enabled: true` — no crashes, correct page setup
- [ ] Append mode with content below: insert_rows shifts content down, page overflow snaps correctly
- [ ] Backward compat: `page_break_enabled: false` behaves identically to current (no insert_rows)

### Must Have
- A4 print setup on target sheet after paste (paperSize=9, margins, autoPageBreaks=True)
- `print_title_rows` from config applied to target sheet
- `insert_rows()` before paste in append mode — physically pushes content down
- Page-overflow check after paste: if content below overflows, snap to next page boundary
- Config keys: `a4_page_rows`, `print_title_rows`, `page_break_enabled`
- All 5 existing tests still pass

### Must NOT Have (Guardrails)
- **NO manual page breaks** (`row_breaks.append(Break(...))`) — use `autoPageBreaks=True` + snap
- **NO `insert_rows` in overwrite mode** — preserve backward compat (overwrite stays overwrite)
- **NO changes to `action: cleanup` path**
- **NO per-row overflow detection** — tabular data has uniform row height
- **NO changes to other tools** (1-png-extractor, 2-template-generator, 4-cell-editor, 5-png-inserter)
- **NO cell styling on pasted data** — just `.value`, no fonts/fills/alignment

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES — pytest with 5 tests, tmp_path fixtures
- **Automated tests**: TDD — RED (failing) → GREEN (minimal) → REFACTOR
- **Framework**: pytest (existing)

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation, MAX PARALLEL):
├── Task 1: Create src/print_setup.py + copy reusable functions [TDD, quick]
├── Task 2: Add config keys + wire print setup in copier.py [quick]

Wave 2 (After Wave 1 — behavior changes, MAX PARALLEL):
├── Task 3: Add insert_rows in append mode + content-collision detection [TDD, deep]
├── Task 4: Add page-overflow snap after paste [TDD, deep]

Wave 3 (After Wave 2 — integration):
├── Task 5: Integration tests + backward compat verification [deep]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan Compliance Audit (oracle)
├── Task F2: Code Quality Review (unspecified-high)
├── Task F3: Real Manual QA (unspecified-high)
└── Task F4: Scope Fidelity Check (deep)
```

**Critical Path**: Task 1 → Task 3 → Task 5 → Final Verification
**Max Concurrent**: 2 (Waves 1 and 2)

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 3, 4 | 1 |
| 2 | — | 5 | 1 |
| 3 | 1 | 5 | 2 |
| 4 | 1 | 5 | 2 |
| 5 | 2, 3, 4 | F1-F4 | 3 |
| F1-F4 | 5 | — | FINAL |

---

## TODOs

- [x] 1. **Create `src/print_setup.py` — copy reusable functions (TDD)**

  **What to do**:
  - **RED**: Create `tests/test_print_setup.py` with 7 failing tests:
    - Import from `src.print_setup` (NOT from `insert` — the functions live in the new module):
      ```python
      from src.print_setup import _setup_a4_print, _calc_page_rows, _parse_print_title_rows
      ```
    1. `test_setup_a4_print_sets_properties` — `_setup_a4_print(ws)` → `paperSize=9`, `orientation='portrait'`, `autoPageBreaks=True`, `margins.top=0.5`
    2. `test_setup_a4_print_sets_print_title_rows` — `_setup_a4_print(ws, "1:3")` → `ws.print_title_rows == "$1:$3"`
    3. `test_setup_a4_print_none_does_not_set` — `_setup_a4_print(ws, None)` → `ws.print_title_rows is None`
    4. `test_calc_page_rows_returns_52` — `_calc_page_rows(ws)` returns ~52
    5. `test_parse_print_title_rows_valid_1_to_6` — `"1:6"` → `(6, "1:6")` (handover #8 fix: end-start+1 = 6, coincidentally same)
    6. `test_parse_print_title_rows_valid_3_to_8` — `"3:8"` → `(6, "3:8")` (handover #8 fix: end-start+1 = 6, NOT 8)
    7. `test_parse_print_title_rows_guard_too_many_headers` — `"1:52"` with `page_rows=52` → `(0, None)` + stderr warning (handover #9 fix)
  - **GREEN**: Create `3-column-copier/src/print_setup.py`:
    - Copy `_setup_a4_print(ws, print_title_rows=None)` from `5-png-inserter/src/inserter.py:69-88`
    - Copy `_calc_page_rows(ws, config_override=None)` from `5-png-inserter/src/inserter.py:91-104`
    - Copy `_parse_print_title_rows(value, page_rows=None)` from `5-png-inserter/insert.py:21-48`
    - Add `import math, sys` at top of module
    - Remove the global `_a4_print_setup_done` flag — it's a debug-print guard that doesn't matter
    - **FIX (handover #10)**: In `_setup_a4_print` debug string, change `autoPageBreaks=False` to `autoPageBreaks=True`
    - **FIX (handover #8)**: In `_parse_print_title_rows`, change `return (end, value)` to `return (end - start + 1, value)` and add `start` to the `return` tuple impact comment
    - **FIX (handover #9)**: After computing `content_rows = page_rows - end`, add guard: `if content_rows < 1: print(f"WARNING: print_title_rows '{value}' leaves 0 content rows (page_rows={page_rows}). Disabled.", file=sys.stderr); return (0, None)`
  - **REFACTOR**: Verify all 7 tests pass, functions match originals with bugs fixed

  **Must NOT do**:
  - Do NOT rewrite functions — copy verbatim, only remove global flag
  - Do NOT put functions in `copier.py` or `src/columns.py`

  **QA Scenarios**:
  ```
  Scenario: All print_setup tests pass
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/test_print_setup.py -v
    Expected: 7 passed
    Evidence: .sisyphus/evidence/task-c1-tests.txt
  ```

  **Commit**: `feat(copier): add print_setup module with A4 and print_title_rows support`

- [x] 2. **Add config keys + wire print setup in copier.py**

  **What to do**:
  - In `3-column-copier/config.json`, add:
    ```json
    "page_break_enabled": false,
    "a4_page_rows": null,
    "print_title_rows": null,
    "_comment_print": "Set page_break_enabled: true to enable A4 page break protection. Set print_title_rows to '1:3' to repeat header rows."
    ```
  - In `3-column-copier/copier.py`:
    - Import from print_setup: `from src.print_setup import _setup_a4_print, _calc_page_rows, _parse_print_title_rows`
    - After config loading (line 44), parse print_title_rows:
      ```python
      print_title_rows_raw = config.get("print_title_rows")
      header_count, print_title_rows_str = _parse_print_title_rows(print_title_rows_raw)
      page_break_enabled = config.get("page_break_enabled", False)
      ```
    - After opening target sheet (after line 128), add A4 setup:
      ```python
      _setup_a4_print(tws, print_title_rows_str)
      if page_break_enabled:
          page_rows = _calc_page_rows(tws, config.get("a4_page_rows"))
      else:
          page_rows = None
      ```
  - Verify existing 5 tests still pass

  **Must NOT do**:
  - Do NOT change existing config keys
  - Do NOT add CLI flags

  **QA Scenarios**:
  ```
  Scenario: copier.py runs with page_break_enabled: false (backward compat)
    Tool: Bash
    Steps: cd 3-column-copier && python copier.py
    Expected: No crashes, debug output shows A4 setup
    Evidence: .sisyphus/evidence/task-c2-run.txt
  ```

  **Commit**: `feat(copier): add page_break config keys and wire print setup`

- [x] 3. **Add `insert_rows` in append mode + content-collision detection (TDD)**

  **What to do**:
  - **RED**: Add 3 failing tests to `tests/test_columns.py` (or new `TestAppendInsert` class):
    1. `test_append_insert_rows_shifts_content` — append mode, content at row 10, paste 5 rows starting at row 5 → content now at row 15
    2. `test_append_no_insert_rows_when_no_content_below` — append mode, no content below, paste 5 rows → no insert_rows call, no gap
    3. `test_append_insert_rows_detects_at_paste_row` — append mode, content starts AT paste_row → insert_rows at paste_row, content shifted
  - **GREEN**: In `copier.py`, BEFORE the paste loop (after append mode has determined `paste_row`, around line 145):
    ```python
    if paste_mode == "append" and page_break_enabled:
        # Count source data rows
        src_data_rows = 0
        check_row = start_row
        while True:
            empty = all(sws.cell(row=check_row, column=c).value is None
                        for c in range(1, sws.max_column + 1))
            if empty and check_row > start_row:
                break
            src_data_rows += 1
            check_row += 1
        
        # Check for merged cells in paste range
        has_merged = False
        for merged_range in tws.merged_cells.ranges:
            if merged_range.min_row <= paste_row + src_data_rows and merged_range.max_row >= paste_row:
                has_merged = True
                break
        
        if has_merged:
            print(f"WARNING: Merged cells detected in paste area, skipping insert_rows", file=sys.stderr)
        elif src_data_rows > 0:
            tws.insert_rows(paste_row, src_data_rows)
    ```
  - **REFACTOR**: Verify 3 new + 5 existing tests pass

  **Must NOT do**:
  - Do NOT call `insert_rows` in overwrite mode (check `paste_mode == "append"`)
  - Do NOT insert rows if `src_data_rows == 0` (no source data)
  - Do NOT insert rows through merged cells — log warning and skip

  **QA Scenarios**:
  ```
  Scenario: Append mode shifts content down
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/test_columns.py -v -k "append_insert"
    Expected: 3 passed
    Evidence: .sisyphus/evidence/task-c3-append.txt
  ```

  **Commit**: `feat(copier): add insert_rows in append mode with collision detection`

- [x] 4. **Add page-overflow snap after paste (TDD)**

  **What to do**:
  - **RED**: Add 2 tests to `tests/test_print_setup.py`:
    1. `test_snap_no_gap_when_content_at_page_start` — `paste_end_row=8, next_content_row=11, page_rows=10` → returns 0 (row 11 = start of page 2, already clean)
    2. `test_snap_inserts_gap_when_content_mid_page` — `paste_end_row=8, next_content_row=9, page_rows=10` → returns 2 (row 9 is mid page 1; gap pushes it to row 11 = start of page 2)
  - **GREEN**: Add to `src/print_setup.py`:
    ```python
    def snap_gap_rows(paste_end_row, tws, page_rows, header_count=0):
        """Return number of gap rows to insert so existing content below
        paste_end_row starts at a clean page boundary.
        
        Scans tws for the first non-empty row after paste_end_row.
        Returns 0 if no content below, or if already at page start,
        or if page_rows is None (page break disabled).
        
        Clean page starts are: row 1, row page_rows+1, 
        row page_rows+content_rows+1, etc.
        """
        if page_rows is None:
            return 0
        
        content_rows = page_rows - header_count if header_count else page_rows
        
        # Find next non-empty row below paste area
        next_row = None
        for row in range(paste_end_row + 1, tws.max_row + 200):
            for c in range(1, tws.max_column + 1):
                if tws.cell(row=row, column=c).value is not None:
                    next_row = row
                    break
            if next_row is not None:
                break
        
        if next_row is None:
            return 0  # no content below
        
        # Check if already at a clean page start
        # Clean starts: row 1, row page_rows+1, row page_rows+content_rows+1, ...
        if next_row == 1:
            return 0
        
        k = (next_row - page_rows - 1) // content_rows
        clean_start = page_rows + k * content_rows + 1
        
        if next_row == clean_start:
            return 0  # already at a clean page boundary
        
        # Not at a clean start — find the NEXT clean start
        next_clean = page_rows + (k + 1) * content_rows + 1
        return next_clean - next_row
    ```
    In `copier.py`, after the column paste loop (after line 170):
    ```python
    # After all columns pasted, track max_dst_row
    # (already available from paste loop — track it with paste_end = dst_row after loop)
    
    if page_break_enabled:
        gap = snap_gap_rows(paste_end, tws, page_rows, header_count)
        if gap > 0:
            tws.insert_rows(paste_end, gap)
            print(f"  Snapped: inserted {gap} gap rows at row {paste_end} to push content to page boundary", file=sys.stderr)
    ```
    **IMPORTANT**: Track `paste_end` during the paste loop — initialize `paste_end = paste_row` before the loop, update `paste_end = max(paste_end, dst_row)` inside each column's paste loop, so after all columns finish, `paste_end` is the highest row written.
  - **REFACTOR**: Verify 2 new tests + all existing pass

  **Must NOT do**:
  - Do NOT insert manual page breaks via `row_breaks.append()`
  - Do NOT apply per-row — check once after all paste columns complete
  - Do NOT snap if `next_content_row` is already at a clean boundary

  **QA Scenarios**:
  ```
  Scenario: Page-overflow snap inserts gap rows when content would be mid-page
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/test_print_setup.py -v -k "snap"
    Expected: 2 passed (test_snap_no_gap + test_snap_inserts_gap)
    Evidence: .sisyphus/evidence/task-c4-snap.txt

  Scenario: Snap does nothing when page_break disabled
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/test_print_setup.py -v -k "snap"
    Expected: snap_gap_rows returns 0 when page_rows=None
    Evidence: .sisyphus/evidence/task-c4-disabled.txt
  ```

  **Commit**: `feat(copier): add page-overflow snap after batch paste`

- [x] 5. **Integration tests + backward compat verification**

  **What to do**:
  - Run ALL tests: `python -m pytest tests/ -v`
  - Verify all existing tests pass with `page_break_enabled: false`
  - Add 1 integration test: `test_full_append_with_page_break` — creates source with 20 rows, target with content at row 30, runs append + page_break → verifies insert_rows fired, content shifted, A4 setup applied
  - Test edge case: zero-row source → no insert_rows
  - Test edge case: merged cells in target → warning logged, insert_rows skipped
  - Run `python copier.py` with real test data — verify no crashes

  **Must NOT do**:
  - Do NOT modify existing tests — only add new ones
  - Do NOT change test fixtures or conftest.py

  **QA Scenarios**:
  ```
  Scenario: Full suite passes
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/ -v
    Expected: 18 passed (5 existing + 7 print_setup + 3 insert_rows + 2 snap + 1 integration), 0 failures
    Evidence: .sisyphus/evidence/task-c5-full-suite.txt
  ```

  **Commit**: `test(copier): integration tests + backward compat for page break feature`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results and get explicit "okay".

- [x] F1. **Plan Compliance Audit** — `oracle`
  Verify: `print_setup.py` exists with 4 functions (`_setup_a4_print`, `_calc_page_rows`, `_parse_print_title_rows`, `snap_gap_rows`), config keys present, `_setup_a4_print` called after paste, `insert_rows` called only in append mode, snap called after paste, no manual breaks, no cleanup changes, no other tools touched.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [5/5] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Verify all tests pass. Check: bare excepts, commented-out code, duplicate test class names, stderr patterns consistent.
  Output: `Tests [N pass/N fail] | Smells [N] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Run `python copier.py` with append mode + `page_break_enabled: true`. Verify no crashes. Test with content below paste area — verify insert_rows shifts it. Test with content mid-page — verify snap inserts gap rows to push to next boundary. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `Append [PASS/FAIL] | Overwrite [PASS/FAIL] | Snap [PASS/FAIL] | Backward Compat [PASS/FAIL] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  Compare plan tasks against git diff. Verify 1:1 compliance, no unaccounted changes, no contamination.
  Output: `Tasks [5/5 compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Wave | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat(copier): add print_setup module with A4 and print_title_rows support` | `src/print_setup.py`, `tests/test_print_setup.py` |
| 1 | `feat(copier): add page_break_enabled, a4_page_rows, print_title_rows config keys` | `config.json`, `copier.py` |
| 2 | `feat(copier): add insert_rows in append mode with content-collision detection` | `copier.py`, `tests/test_columns.py` |
| 2 | `feat(copier): add page-overflow snap after paste` | `copier.py` |
| 3 | `test(copier): integration tests + backward compat verification` | `tests/test_columns.py` |

---

## Success Criteria

### Verification Commands
```bash
cd 3-column-copier
python -m pytest tests/ -v                    # Expected: ALL pass (18 tests)
python copier.py                               # Expected: no crashes with page_break_enabled: false
python copier.py                               # Expected: no crashes with page_break_enabled: true
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Backward compat: `page_break_enabled: false` = current behavior