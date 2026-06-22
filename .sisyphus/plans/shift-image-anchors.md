# Shift Image Anchors After insert_rows in Tool 3

## TL;DR

> **Quick Summary**: openpyxl's `insert_rows()` shifts cell content and merged ranges but leaves image anchors frozen. Fix: add `shift_image_anchors()` helper that manually shifts `AnchorMarker.row` for both `OneCellAnchor` and `TwoCellAnchor` images on the target worksheet, called after both `insert_rows()` call sites in copier.py.
>
> **Deliverables**:
> - `3-column-copier/src/images.py` — new helper module: `shift_image_anchors(ws, insert_at_row, num_rows)`
> - `3-column-copier/tests/test_images.py` — TDD test suite (~10 tests)
> - `3-column-copier/copier.py` — 2 call sites + import
>
> **Estimated Effort**: Short
> **Parallel Execution**: Limited — TDD workflow is mostly sequential (RED → GREEN → INTEGRATE)
> **Critical Path**: Task 1 (tests/RED) → Task 2 (implementation/GREEN) → Task 3 (integration) → Task 4 (full verification)

---

## Context

### Original Request
User identified that the existing plan at `.sisyphus/plans/shift-image-anchors.md` is underspecified and needs a complete re-plan. The handover.md marks it as "⚠️ underspecified — needs re-plan."

### Problem Statement
openpyxl's `Worksheet.insert_rows()` shifts `self._cells` (cell data) and merged cell ranges, but does **NOT** adjust `self._images` (drawing objects). Images stay frozen at their original `AnchorMarker.row` coordinates while rows below shift down, causing visual overlap and misplacement.

### Interview Summary

**Key Discussions**:
- **Scope**: Fix BOTH `insert_rows()` calls — primary at line 216 (`paste_row` + `src_data_rows`) AND snap at line 260 (`paste_end` + `gap`)
- **Anchor types**: Handle `OneCellAnchor` (has `_from` only) and `TwoCellAnchor` (has both `_from` and `to`). Skip `AbsoluteAnchor` with stderr warning — it uses EMU pixel positions, not row coordinates
- **Spanning images**: When an image straddles the insertion point (`_from.row < insert_row <= to.row`), shift only `to.row` down — the image gets taller to accommodate the new rows
- **Organization**: Extract logic to `src/images.py` helper module, following existing `src/columns.py` / `src/print_setup.py` pattern
- **Test strategy**: TDD — write failing tests first (RED), then implement (GREEN), then integrate (REFACTOR)
- **Column shifting**: NOT needed — only rows are inserted, not columns. `AnchorMarker.col` stays unchanged

**Research Findings**:
- **AnchorMarker.row is 0-BASED**: `row=0` = Excel row 1. Confirmed by openpyxl source (`_check_anchor()` subtracts 1 when converting `'A1'` → `OneCellAnchor`). The helper must use 0-based comparison and addition
- **insert_rows() confirmed image-unaware**: openpyxl docs explicitly state "Openpyxl does not manage dependencies, such as formulae, tables, charts, etc., when rows or columns are inserted or deleted. This is considered to be out of scope"
- **`ws._images` is private API**: The only way to access existing drawing objects. May raise `AttributeError` if never populated — must guard with `hasattr(ws, '_images')`
- **TwoCellAnchor structure**: Has both `_from` and `to` attributes (both `AnchorMarker`). Must shift both when entirely below insertion, only `to` when spanning. Has `editAs` attribute (`'twoCell'`, `'oneCell'`, `'absolute'`) — but row shifting ignores this
- **Existing patterns**: Tool 1 (`1-png-extractor`) already accesses `ws._images` for reading. `generate_fixture.py` shows canonical `TwoCellAnchor` creation. `test_drawing.py` has `_PNG_DATA` constant (minimal valid 1×1 PNG) usable for tests
- **No existing image code in tool 3**: Zero `_images` references, zero `openpyxl.drawing` imports. Entirely new code

### Metis Review

**Identified Gaps** (addressed):

| Gap | How Resolved |
|-----|-------------|
| `ws._images` may raise `AttributeError` | Guard with `hasattr(ws, '_images')` in helper |
| Save/reload survival not specified | Added `test_survives_save_reload` test case (TC-7) |
| Negative/zero `num_rows` edge case | Guard: `if num_rows <= 0: return` (no-op) |
| Invalid `insert_at_row < 1` edge case | Guard: `if insert_at_row < 1: return` (no-op) |
| Snap insert_rows (line 260) was missing from original plan | Both call sites included in this plan |
| Multiple images at same anchor row | Loop handles this naturally — no special case needed |
| `editAs` attribute on TwoCellAnchor | Row shifting ignores `editAs` — only modifies `.row` integers |
| Spanning image `_from` above, `to` below | Separate condition: only shift `to.row`, leave `_from.row` unchanged |
| No `delete_rows` counterpart needed | Copier has no `delete_rows` calls — symmetrical fix not needed |

**Guardrails Applied**:
- GR1: DO NOT modify any tool outside `3-column-copier/`
- GR2: DO NOT handle `AbsoluteAnchor` beyond stderr warning
- GR3: DO NOT add column anchor shifting
- GR4: DO NOT add `delete_rows` symmetry
- GR5: DO NOT modify existing insert_rows logic
- GR6: DO NOT duplicate all existing insert_rows tests with images (1-2 per anchor type per call site = ~10 tests max)

---

## Work Objectives

### Core Objective
Shift image anchors on the target worksheet after `insert_rows()` so images move with their surrounding cells, preventing visual overlap and misplacement.

### Concrete Deliverables
1. `3-column-copier/src/images.py` — `shift_image_anchors(ws, insert_at_row, num_rows)` function
2. `3-column-copier/tests/test_images.py` — TDD test suite with ~10 test cases
3. `3-column-copier/copier.py` — import + two call sites (after lines 216 and 260)

### Definition of Done
- [ ] `shift_image_anchors()` passes all 10 test cases (agent-verified)
- [ ] All 43 existing tests still pass — zero regressions
- [ ] Both `insert_rows()` calls followed by `shift_image_anchors()`
- [ ] Anchors survive save-reload round-trip (tested)
- [ ] AbsoluteAnchor is skipped with stderr warning (tested)

### Must Have
- Fix BOTH insert_rows call sites (lines 216 and 260)
- Handle `OneCellAnchor` (shift `_from.row`)
- Handle `TwoCellAnchor` (shift both `_from.row` and `to.row`)
- Handle spanning images (only `to.row` shifts when straddling insert point)
- Guard: `hasattr(ws, '_images')` before accessing
- Guard: `num_rows <= 0` → no-op
- Guard: `insert_at_row < 1` → no-op
- Warning log for skipped `AbsoluteAnchor`

### Must NOT Have (Guardrails)
- Changes to any file outside `3-column-copier/`
- Modifications to existing insert_rows logic or behavior
- Column anchor shifting (`AnchorMarker.col`)
- `delete_rows` symmetry (no delete_rows in copier)
- New config options or tool-wide settings
- Manual/visual verification — all verification is automated
- Duplication of all existing insert_rows tests with images

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.
> Acceptance criteria requiring "user manually tests/confirms" are FORBIDDEN.

### Test Decision
- **Infrastructure exists**: YES (pytest 9.0.3, 43 tests passing in 3.14s)
- **Automated tests**: TDD (RED → GREEN → REFACTOR)
- **Framework**: pytest
- **Test pattern**: Class-based unit tests with inline Workbook creation, openpyxl in-memory Workbooks, `tmp_path` for file-backed save/reload tests

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/Tool**: Use `bash` (python subprocess) — Run `python -m pytest tests/ -v`, verify exit code and output
- **API/Module**: Use `bash` (python REPL) — Import and call `shift_image_anchors()`, verify anchor row attributes

---

## Execution Strategy

### Parallel Execution Waves

> TDD workflow limits parallelism, but test file and src helper can proceed once test cases are defined.

```
Wave 1 (Start Immediately — RED):
└── Task 1: Create failing test suite tests/test_images.py [deep]

Wave 2 (After Wave 1 — GREEN + INTEGRATE):
├── Task 2: Implement src/images.py with shift_image_anchors() [quick]
└── Task 3: Integrate into copier.py (import + two call sites) [quick]

Wave 3 (After Wave 2 — VERIFY):
└── Task 4: Full test suite verification + QA scenarios [unspecified-high]

Critical Path: Task 1 → Task 2 → Task 3 → Task 4
Max Concurrent: 2 (Wave 2: Tasks 2 & 3 can run in parallel after Task 1)
```

### Dependency Matrix

| Task | Blocks | Blocked By |
|------|--------|------------|
| 1 (test_images.py) | 2, 3, 4 | — |
| 2 (src/images.py) | 4 | 1 |
| 3 (copier.py integration) | 4 | 1 |
| 4 (full verification) | — | 2, 3 |

### Agent Dispatch Summary

- **Wave 1**: **1** — T1 → `deep`
- **Wave 2**: **2** — T2 → `quick`, T3 → `quick`
- **Wave 3**: **1** — T4 → `unspecified-high`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**

- [x] 1. Create failing test suite `tests/test_images.py` (TDD: RED)

  **What to do**:
  - Create `3-column-copier/tests/test_images.py`
  - Include a minimal valid 1×1 PNG as `_PNG_DATA` constant (base64-encoded)
  - Write 10 test cases as class-based pytest tests that ALL fail initially (the `shift_image_anchors` import will fail since `src/images.py` doesn't exist yet — but the test *structure* must be complete and correct)
  - Each test creates an in-memory Workbook via `openpyxl.Workbook()`, adds images to `ws._images`, then calls (or attempts to call) `shift_image_anchors(ws, insert_at_row, num_rows)`, then asserts anchor row values

  **Test cases to write**:
  1. `test_one_cell_anchor_shifts_below_insert` — OneCellAnchor at row 7 (0-based: 6), insert at row 5 (0-based: 4), num_rows=3 → `_from.row` changes from 6 to 9
  2. `test_two_cell_anchor_both_shifts_below` — TwoCellAnchor from row 7→10, insert at row 5, num_rows=3 → `_from.row` 6→9, `to.row` 9→12
  3. `test_two_cell_anchor_spanning_insert` — TwoCellAnchor from row 3→7, insert at row 5, num_rows=3 → `_from.row` stays 2, `to.row` shifts 6→9 (only `to` moves)
  4. `test_absolute_anchor_skipped` — AbsoluteAnchor (no row attributes) → no change, verify stderr warning about skipping
  5. `test_images_above_insert_untouched` — Image at row 2, insert at row 5 → `_from.row` unchanged at 1
  6. `test_no_images_no_crash` — Worksheet with zero `_images` → no-op, no error
  7. `test_zero_rows_noop` — `num_rows=0` → no change to any anchor
  8. `test_multiple_images_all_shift` — 3 OneCellAnchor images all below insert → all shift correctly
  9. `test_survives_save_reload` — shift anchors, `ws.save()` to BytesIO, reload, verify anchors persist
  10. `test_image_exactly_at_insert_row_shifts` — Image at row 5, insert at row 5, num_rows=2 → shifts to row 7

  **Must NOT do**:
  - Do NOT create `src/images.py` in this task (that's Task 2)
  - Do NOT modify `copier.py` in this task (that's Task 3)
  - Do NOT use manual assertions — all assertions must be `assert img.anchor._from.row == expected_value`
  - Do NOT skip edge cases (zero rows, AbsoluteAnchor, spanning)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Writing 10 thorough TDD tests requires careful thought about anchor types, 0-based indexing, edge cases, and test patterns. Need autonomous problem-solving to get assertions right.
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl-specific patterns for creating images with proper anchor types
  - **Skills Evaluated but Omitted**:
    - `caveman`: Not needed — full communication preferred for test writing

  **Parallelization**:
  - **Can Run In Parallel**: NO (first task in TDD pipeline)
  - **Parallel Group**: Wave 1 (sole task)
  - **Blocks**: Tasks 2, 3, 4
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References** (existing code to follow):
  - `3-column-copier/tests/test_columns.py:TestAppendInsertRows` — Test class structure, inline Workbook creation pattern, assertion style
  - `1-png-extractor/tests/test_drawing.py:_PNG_DATA` — Minimal valid 1×1 PNG base64 constant to use for `XlImage` creation
  - `generate_fixture.py` — Canonical pattern for creating `TwoCellAnchor` with `AnchorMarker(col=..., row=...)` and `XlImage(anchor=TwoCellAnchor(_from=marker))`
  - `dep/PAT for testing V7/5-png-inserter/tests/test_page_breaks.py:352` — Example of accessing `wb["Sheet"]._images` to verify image state

  **API/Type References** (contracts to implement against):
  - `openpyxl.drawing.spreadsheet_drawing.OneCellAnchor` — Has `_from` (AnchorMarker), NO `to` attribute
  - `openpyxl.drawing.spreadsheet_drawing.TwoCellAnchor` — Has both `_from` and `to` (both AnchorMarker)
  - `openpyxl.drawing.spreadsheet_drawing.AbsoluteAnchor` — Has `pos` (XDRPoint2D), NO `_from` or `to`
  - `openpyxl.drawing.spreadsheet_drawing.AnchorMarker` — Has `row: int` (0-based), `col: int` (0-based), `rowOff: int`, `colOff: int`

  **External References**:
  - `openpyxl.drawing.image.Image` (aliased as `XlImage`) — `Image(data_or_path)` constructor accepting bytes
  - Official docs: https://openpyxl.readthedocs.io/en/stable/editing_worksheets.html — Confirms insert_rows does NOT shift images

  **Acceptance Criteria**:

  **TDD (RED phase — tests MUST fail):**
  - [ ] Test file created: `3-column-copier/tests/test_images.py`
  - [ ] `python -m pytest tests/test_images.py -v` → ALL 10 FAIL (import error or assertion failure expected)
  - [ ] No syntax errors in test file

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Test file is syntactically valid and fails as expected (RED phase)
    Tool: Bash
    Preconditions: Task 1 only — src/images.py does NOT exist yet
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_images.py -v --tb=short 2>&1
      3. Verify exit code is non-zero (tests fail — expected in RED phase)
      4. Verify test names appear in output (10 collected)
    Expected Result: Pytest collects 10 tests, all fail (ImportError or AssertionError), no SyntaxError
    Failure Indicators: SyntaxError in output, tests pass (shouldn't — no implementation yet), wrong test count
    Evidence: .sisyphus/evidence/task-1-red-phase.txt
  ```

  **Evidence to Capture:**
  - [ ] `.sisyphus/evidence/task-1-red-phase.txt` — pytest output showing 10 tests collected, all failing

  **Commit**: YES
  - Message: `test(3-column-copier): add failing image anchor shift tests (TDD RED)`
  - Files: `3-column-copier/tests/test_images.py`
  - Pre-commit: verify tests fail with `cd 3-column-copier && python -m pytest tests/test_images.py --tb=short`

---

- [x] 2. Implement `src/images.py` with `shift_image_anchors()` (TDD: GREEN)

  **What to do**:
  - Create `3-column-copier/src/images.py`
  - Implement `shift_image_anchors(ws, insert_at_row, num_rows)` function:
    1. Guard: `if num_rows <= 0:` → return (no-op)
    2. Guard: `if not hasattr(ws, '_images'):` → return (no images)
    3. `insert_row_0 = insert_at_row - 1` (convert to 0-based for AnchorMarker comparison)
    4. Iterate `ws._images`:
       - For `OneCellAnchor`: if `_from.row >= insert_row_0` → `_from.row += num_rows`
       - For `TwoCellAnchor`:
         - If `_from.row >= insert_row_0` → `_from.row += num_rows` (entirely below)
         - If `to.row >= insert_row_0` → `to.row += num_rows` (shift `to` even if `_from` is above — spanning case)
       - For `AbsoluteAnchor`: print `[WARNING] Skipping AbsoluteAnchor at pos x={pos.x}, y={pos.y} — manual repositioning required` to stderr, continue
       - For unknown types: print `[WARNING] Unknown anchor type: {type(anchor).__name__} — skipping` to stderr
    5. No return value
  - Add module docstring explaining purpose, 0-based convention, and anchor type handling
  - Follow `src/columns.py` module pattern (no `if __name__ == '__main__'`, pure function module)

  **Must NOT do**:
  - Do NOT modify `copier.py` (Task 3)
  - Do NOT handle `AbsoluteAnchor` beyond stderr warning
  - Do NOT shift `AnchorMarker.col` (column shifting out of scope)
  - Do NOT use `isinstance` for anchor type detection on objects that may not be from openpyxl.drawing

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single function, well-defined behavior, straightforward logic. ~30 lines of code. No architectural decisions needed.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `xlsx`: Not needed — pure openpyxl drawing API, no spreadsheet creation/manipulation

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 3 — both depend on Task 1 completion)
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:

  **Pattern References** (existing code to follow):
  - `3-column-copier/src/columns.py` — Module structure: imports at top, pure functions, no main guard
  - `3-column-copier/src/print_setup.py` — Same module pattern, helper functions imported by copier.py
  - `generate_fixture.py` — Using `from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor`

  **API/Type References**:
  - `openpyxl.drawing.spreadsheet_drawing.OneCellAnchor` — `_from: AnchorMarker`, no `to` attribute
  - `openpyxl.drawing.spreadsheet_drawing.TwoCellAnchor` — `_from: AnchorMarker`, `to: AnchorMarker`, `editAs: str`
  - `openpyxl.drawing.spreadsheet_drawing.AbsoluteAnchor` — `pos: XDRPoint2D`, no `_from`/`to`
  - `openpyxl.drawing.spreadsheet_drawing.AnchorMarker` — `row: int` (0-based), `col: int` (0-based)

  **Acceptance Criteria**:

  **TDD (GREEN phase — tests MUST pass):**
  - [ ] File created: `3-column-copier/src/images.py`
  - [ ] `shift_image_anchors()` function implemented
  - [ ] `python -m pytest tests/test_images.py -v` → ALL 10 PASS
  - [ ] `python -m pytest tests/ -v` → 43 existing tests still pass (53 total: 43 + 10)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All image anchor tests pass (GREEN phase)
    Tool: Bash
    Preconditions: Task 1 (test file) and Task 2 (src/images.py) both complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_images.py -v 2>&1
      3. Assert exit code is 0
      4. Assert output shows "10 passed"
      5. Scan output for FAILED — must be zero
    Expected Result: 10 passed, 0 failed, 0 warnings
    Failure Indicators: Any FAILED test, exit code non-zero, fewer than 10 collected
    Evidence: .sisyphus/evidence/task-2-green-phase.txt

  Scenario: Existing tests not broken by new module
    Tool: Bash
    Preconditions: Task 2 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_columns.py tests/test_cli.py tests/test_cleanup.py tests/test_print_setup.py tests/test_real_mapping.py -v 2>&1
      3. Assert exit code is 0
      4. Assert output shows "43 passed"
    Expected Result: 43 passed, 0 failed (zero regressions from new src/images.py)
    Failure Indicators: Any FAILED test in existing suite
    Evidence: .sisyphus/evidence/task-2-no-regressions.txt
  ```

  **Evidence to Capture:**
  - [ ] `.sisyphus/evidence/task-2-green-phase.txt` — all 10 image tests passing
  - [ ] `.sisyphus/evidence/task-2-no-regressions.txt` — all 43 existing tests passing

  **Commit**: YES (groups with Task 3)
  - Message: `feat(3-column-copier): add shift_image_anchors() helper for image anchor drift after insert_rows`
  - Files: `3-column-copier/src/images.py`

---

- [x] 3. Integrate `shift_image_anchors()` into `copier.py` call sites

  **What to do**:
  - Add import to `copier.py`: `from src.images import shift_image_anchors`
  - **Call site 1** (after primary insert_rows at line 216): Inside the `if src_data_rows > 0:` block, after `tws.insert_rows(paste_row, src_data_rows)`, add:
    ```python
    shift_image_anchors(tws, paste_row, src_data_rows)
    ```
  - **Call site 2** (after snap insert_rows at line 260): Inside the `if gap > 0:` block, after `tws.insert_rows(paste_end, gap)`, add:
    ```python
    shift_image_anchors(tws, paste_end, gap)
    ```
  - Both call sites pass the target worksheet (`tws`), the insertion row (1-based, directly from `paste_row`/`paste_end`), and the number of rows inserted (`src_data_rows`/`gap`)
  - Verify both call sites are inside their respective `if` blocks (i.e., only called when insert_rows actually executed)

  **Must NOT do**:
  - Do NOT call `shift_image_anchors` outside the `if` blocks (avoid no-op calls)
  - Do NOT change existing logic flow or variable names
  - Do NOT add new imports beyond `from src.images import shift_image_anchors`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Mechanical integration — two import additions, two function calls at known line numbers. Straightforward editing.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `xlsx`: Not needed — no spreadsheet manipulation, just code editing

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2 — both depend on Task 1, neither depends on the other)
  - **Parallel Group**: Wave 2 (with Task 2)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:

  **Pattern References** (existing code to follow):
  - `3-column-copier/copier.py:15-17` — Existing import pattern for `src/` modules: `from src.columns import ...`
  - `3-column-copier/copier.py:216` — Primary `tws.insert_rows(paste_row, src_data_rows)` call site
  - `3-column-copier/copier.py:260` — Snap `tws.insert_rows(paste_end, gap)` call site
  - `3-column-copier/copier.py:257-261` — Snap block structure showing `if gap > 0:` guard

  **Acceptance Criteria**:
  - [ ] Import added: `from src.images import shift_image_anchors` in copier.py imports
  - [ ] Call site 1: `shift_image_anchors(tws, paste_row, src_data_rows)` after line 216
  - [ ] Call site 2: `shift_image_anchors(tws, paste_end, gap)` after line 260
  - [ ] Both calls inside their respective `if` blocks
  - [ ] `python -m pytest tests/ -v` → 53 passed (43 existing + 10 new image tests)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Full copier flow with images — insert_rows shifts anchors
    Tool: Bash
    Preconditions: Tasks 1-3 complete
    Steps:
      1. cd 3-column-copier
      2. python -c "
      from openpyxl import Workbook
      from openpyxl.drawing.image import Image as XlImage
      from src.images import shift_image_anchors
      import base64
      # Create target with an image below the paste area
      wb = Workbook()
      tws = wb.active
      tws['A1'] = 'Header'
      tws['A10'] = 'Existing Data'
      # Add image at row 10
      png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
      img = XlImage(png)
      tws.add_image(img, 'A10')
      anchor_before = tws._images[0].anchor._from.row
      # Insert rows at row 3
      tws.insert_rows(3, 5)
      shift_image_anchors(tws, 3, 5)
      anchor_after = tws._images[0].anchor._from.row
      assert anchor_before == 9, f'Expected 9, got {anchor_before}'
      assert anchor_after == 14, f'Expected 14, got {anchor_after}'
      print('PASS: anchor shifted from', anchor_before, 'to', anchor_after)
      "
      3. Assert output contains "PASS:"
    Expected Result: Anchor at row 10 (0-based: 9) shifts to row 15 (0-based: 14) after inserting 5 rows at row 3
    Failure Indicators: AssertionError, anchor not shifted, wrong value
    Evidence: .sisyphus/evidence/task-3-integration-repl.txt
  ```

  **Evidence to Capture:**
  - [ ] `.sisyphus/evidence/task-3-integration-repl.txt` — Python REPL output showing anchor shifted correctly

  **Commit**: YES
  - Message: `feat(3-column-copier): integrate shift_image_anchors at both insert_rows call sites`
  - Files: `3-column-copier/copier.py`

---

- [x] 4. Full test suite verification and edge case validation

  **What to do**:
  - Run the FULL test suite: `cd 3-column-copier && python -m pytest tests/ -v`
  - Confirm: 53 tests pass (43 existing + 10 new image tests)
  - Run the 10 image tests in isolation: `python -m pytest tests/test_images.py -v --tb=long`
  - Manually verify each edge case by reading test assertions in output
  - Verify no regressions in: `test_columns.py`, `test_cli.py`, `test_cleanup.py`, `test_print_setup.py`, `test_real_mapping.py`
  - Check that `python -c "import sys; sys.path.insert(0, '.'); from src.images import shift_image_anchors; print('import OK')"` succeeds from the tool root
  - Verify save/reload test specifically confirms anchor persistence

  **Must NOT do**:
  - Do NOT skip the save/reload test verification
  - Do NOT introduce new assertions or logic changes
  - Do NOT skip any test file

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Orchestration — running multiple test commands, parsing output, cross-referencing results, verifying no regressions across 5 test files. Higher effort than a single quick task.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `xlsx`: Not needed — verification only, no spreadsheet manipulation

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sole task — runs after all implementation)
  - **Blocks**: Final Verification Wave (F1-F4)
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `3-column-copier/tests/` — All 5 test files
  - `3-column-copier/tests/test_images.py` — New test file from Task 1
  - `3-column-copier/src/images.py` — New module from Task 2

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_images.py -v` → 10 passed, 0 failed
  - [ ] `python -m pytest tests/ -v` → 53 passed, 0 failed
  - [ ] test_survives_save_reload → specifically PASS
  - [ ] Zero regressions in existing tests (all 43 pass)
  - [ ] `from src.images import shift_image_anchors` succeeds

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Full test suite all green
    Tool: Bash
    Preconditions: Tasks 1-3 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/ -v 2>&1
      3. Scan for "FAILED" — must be zero
      4. Scan for "ERROR" — must be zero
      5. Verify "53 passed" in summary line
      6. Parse output for any "WARNING" lines from AbsoluteAnchor test — verify expected warnings present
    Expected Result: 53 passed, 0 failed, 0 errors, AbsoluteAnchor warnings in stderr
    Failure Indicators: Any FAILED or ERROR test, fewer than 53 passed
    Evidence: .sisyphus/evidence/task-4-full-suite.txt

  Scenario: Image tests in isolation with verbose output
    Tool: Bash
    Preconditions: Tasks 1-3 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_images.py -v --tb=long 2>&1
      3. For each of the 10 test names, verify PASS
      4. Verify test_survives_save_reload explicitly PASS
      5. Verify test_absolute_anchor_skipped captures stderr warning
    Expected Result: 10 passed, all test names visible, save/reload explicitly confirmed
    Failure Indicators: Any FAILED, save/reload test skipped or failed
    Evidence: .sisyphus/evidence/task-4-image-tests.txt
  ```

  **Evidence to Capture:**
  - [ ] `.sisyphus/evidence/task-4-full-suite.txt` — Full 53-test run output
  - [ ] `.sisyphus/evidence/task-4-image-tests.txt` — Image tests with verbose traceback

  **Commit**: NO (verification only — no code changes)

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read `.sisyphus/plans/shift-image-anchors.md` end-to-end. For each "Must Have": verify implementation exists (read `src/images.py`, grep `copier.py` for `shift_image_anchors` calls). For each "Must NOT Have": search for forbidden patterns — verify no changes outside `3-column-copier/`, no column shifting, no delete_rows symmetry. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [4/4] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Review all changed files for: unused imports, bare except, `as any`/type ignore, commented-out code, AI slop (excessive comments, over-abstraction, generic names). Check that `shift_image_anchors()` has proper docstring, guards for edge cases.
  Output: `Tests [53 pass/0 fail] | Imports [CLEAN/N issues] | Guards [N/N present] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration: verify import works from copier context, verify both call sites are active. Test edge cases: empty `_images`, negative num_rows, AbsoluteAnchor warning. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (`git diff`). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [4/4 compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Commit 1** (Task 1): `test(3-column-copier): add failing image anchor shift tests (TDD RED)`
  - Files: `3-column-copier/tests/test_images.py`
  - Pre-commit: verify tests fail with `cd 3-column-copier && python -m pytest tests/test_images.py --tb=short`

- **Commit 2** (Tasks 2+3 grouped): `feat(3-column-copier): shift image anchors after insert_rows to prevent drift`
  - Files: `3-column-copier/src/images.py`, `3-column-copier/copier.py`
  - Pre-commit: `cd 3-column-copier && python -m pytest tests/ -v` → 53 pass

---

## Success Criteria

### Verification Commands
```bash
cd 3-column-copier && python -m pytest tests/test_images.py -v
# Expected: 10 passed in X.XXs

cd 3-column-copier && python -m pytest tests/ -v
# Expected: 53 passed in X.XXs (43 existing + 10 new)
```

### Final Checklist
- [ ] All "Must Have" present: both call sites, OneCellAnchor + TwoCellAnchor, spanning, guards, AbsoluteAnchor warning
- [ ] All "Must NOT Have" absent: no changes outside tool 3, no column shifting, no delete_rows, no config changes
- [ ] All 53 tests pass (zero regressions)
- [ ] Anchor shift survives save/reload round-trip
- [ ] Evidence files captured for all 4 tasks
- [ ] Final Verification Wave (F1-F4) all APPROVED
