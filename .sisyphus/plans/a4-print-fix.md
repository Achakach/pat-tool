# Fix: A4 Print `autoPageBreaks` AttributeError Crash

## TL;DR

> **Quick Summary**: Fix `AttributeError` crash when `_setup_a4_print` sets `autoPageBreaks=True` on XLSX files lacking a `pageSetupPr` XML element. Gate the call behind `page_break_enabled` in tool 3, add defensive `try/except` in both tools 3 and 5.
>
> **Deliverables**:
> - `3-column-copier/copier.py`: gate `_setup_a4_print` behind `page_break_enabled`
> - `3-column-copier/src/print_setup.py`: defensive try/except on `autoPageBreaks`
> - `5-png-inserter/src/inserter.py`: defensive try/except + fix debug message
> - Tests: regression test with XLSX lacking `pageSetupPr` + guard behavior tests
> - E2E: remove monkey-patch workaround from `test_pipeline_e2e.py`
>
> **Estimated Effort**: Quick (~3 files changed, ~4 test additions)
> **Parallel Execution**: YES — 3 waves (foundation → fixes → tests + E2E cleanup)
> **Critical Path**: Task 1 → Task 3 → Task 4 → Task 5

---

## Context

### Original Request
User runs tool 3 (`3-column-copier`) on another computer and gets:
```
AttributeError: 'NoneType' object has no attribute 'sheet_properties'
```
at `_setup_a4_print` → `ws.page_setup.autoPageBreaks = True` → openpyxl's `page.py:93` → `self._parent.sheet_properties.pageSetupPr` where `sheet_properties` is `None`.

### Root Cause
`copier.py:143` calls `_setup_a4_print(tws, print_title_rows_str)` **unconditionally** — regardless of `page_break_enabled` setting. The XLSX file on the other computer lacks `<pageSetupPr>` in its worksheet XML, so openpyxl's `sheet_properties` is `None` when deserialized.

### Interview Summary
- **Confirmed**: crash only on XLSX files without `pageSetupPr` XML element
- **Tool 5**: same code pattern, same latent vulnerability (but only runs post-purge_sheet which may help)
- **E2E test**: has a monkey-patch workaround at `test_pipeline_e2e.py:43-56` that masks this bug — will be removed
- **Test infrastructure**: pytest 9.0.3, plain `assert`, `tmp_path` fixtures, no plugins

### Metis Review
**Key directives incorporated**:
- **E2E patch**: Remove monkey-patch after fix to properly validate
- **Tool 5 gate**: Keep `_setup_a4_print` unconditional (margins/paper setup needed regardless) but add try/except
- **Narrow try/except**: Only wrap `autoPageBreaks = True`, not entire function
- **Debug message**: Fix tool 5's misleading `autoPageBreaks=False` → `True`
- **Scope boundary**: Do NOT unify tool 3/tool 5 A4 modules, do NOT fix `_parse_print_title_rows` divergence

---

## Work Objectives

### Core Objective
Prevent `AttributeError` crash when setting `autoPageBreaks=True` on XLSX files lacking `pageSetupPr` XML element, and ensure `_setup_a4_print` is only called when `page_break_enabled=True` in tool 3.

### Concrete Deliverables
- `3-column-copier/copier.py`: restructured lines 143-147 (gate + page_rows)
- `3-column-copier/src/print_setup.py`: try/except at line 25
- `5-png-inserter/src/inserter.py`: try/except at line 79 + fix debug message line 87
- `tests/test_pipeline_e2e.py`: remove `_OPENPYXL_PATCH` monkey-patch (lines 43-56)
- `3-column-copier/tests/test_print_setup.py`: 2 new tests
- `5-png-inserter/tests/test_page_breaks.py`: 1 new test

### Definition of Done
- [ ] `python -m pytest 3-column-copier/tests/ -v` → all 31 tests pass (including new ones)
- [ ] `python -m pytest 5-png-inserter/tests/ -v` → all 50 tests pass (including new one)
- [ ] `python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v` → all 6 tests pass (no monkey-patch)

### Must Have
- `_setup_a4_print` in copier.py gated behind `page_break_enabled`
- Both `_setup_a4_print` implementations wrapped with try/except `AttributeError` on `autoPageBreaks = True`
- Regression test that loads XLSX without `pageSetupPr` and verifies no crash
- All 155 existing tests still pass

### Must NOT Have (Guardrails)
- Do NOT unify tool 3 and tool 5 A4 modules
- Do NOT fix tool 5's `_parse_print_title_rows` bug (returns `end` instead of `end-start+1`)
- Do NOT change margin values, paper size, orientation
- Do NOT modify page-break insertion logic in `insert_png`/`insert_png_no_label`
- Do NOT refactor `snap_gap_rows`, `_calc_page_rows`, or any other helper
- Do NOT remove `_a4_print_setup_done` global guard from tool 5

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (pytest 9.0.3)
- **Automated tests**: Tests-after (add tests alongside fix)
- **Framework**: pytest (plain `assert`, `tmp_path`, `capsys`)

### QA Policy
Every task includes agent-executed QA scenarios:
- **Backend/CLI**: `bash` (PowerShell) — run pytest, check output, verify exit codes

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation):
├── Task 1: Create test fixture (XLSX without pageSetupPr) [quick]
└── Task 2: Update draft/test infrastructure [quick]

Wave 2 (After Wave 1 — fixes, MAX PARALLEL):
├── Task 3: Fix copier.py gate + print_setup.py try/except [quick]
└── Task 4: Fix inserter.py try/except + debug message [quick]

Wave 3 (After Wave 2 — tests + E2E cleanup):
├── Task 5: Add regression + guard tests (tool 3) [quick]
├── Task 6: Add regression test (tool 5) [quick]
└── Task 7: Remove E2E monkey-patch + verify [quick]

Critical Path: Task 1 → Task 3 → Task 4 → Task 5 → Task 8
Parallel Speedup: Tasks 3/4 run in parallel (different tools, no dependency)
```

### Dependency Matrix
- **1-2**: — — 3-4, 1
- **3**: 1 — 5, 2
- **4**: 1 — 6, 2
- **5**: 3 — 8, 3
- **6**: 4 — 8, 3
- **7**: 3, 4 — 8, 3
- **8**: 5, 6, 7 — —, FINAL

### Agent Dispatch Summary
- **1**: **3** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `quick`
- **2**: **3** — T5 → `quick`, T6 → `quick`, T7 → `quick`
- **FINAL**: **1** — T8 → `quick`

---

## TODOs

- [x] 1. Create test fixture XLSX without `pageSetupPr`

  **What to do**:
  - Create a minimal XLSX file that lacks `<pageSetupPr>` in its worksheet XML
  - Save it as `3-column-copier/tests/fixtures/no_page_setup_pr.xlsx`
  - Verify: loading this file and accessing `ws.page_setup.autoPageBreaks` raises `AttributeError` (before fix)
  - The fixture should be a valid XLSX with at least one sheet and some cell data — just missing the `pageSetupPr` element

  **Must NOT do**:
  - Do NOT create the fixture by editing XML manually — use openpyxl API to write, then strip the element by re-zipping
  - Do NOT use a large/complex fixture — 2 rows × 2 columns is sufficient

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Simple file creation, no specialized domain needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3, Task 4
  - **Blocked By**: None

  **References**:
  - `3-column-copier/tests/test_print_setup.py` — existing test patterns using `Workbook()`, `tmp_path`, plain `assert`
  - `3-column-copier/conftest.py` — sys.path setup for importing `from src.print_setup import _setup_a4_print`
  - openpyxl docs: workbook creation without pageSetupPr — use `openpyxl.Workbook()` + `ws['A1'] = 'test'` + save, then strip `pageSetupPr` from the zip

  **Acceptance Criteria**:
  - [ ] File exists: `3-column-copier/tests/fixtures/no_page_setup_pr.xlsx`
  - [ ] Loading it with `load_workbook` + accessing `ws.page_setup.autoPageBreaks` to read does NOT crash (read is safe, write crashes)
  - [ ] Setting `ws.page_setup.autoPageBreaks = True` on this file's sheet DOES crash with `AttributeError: 'NoneType' object has no attribute 'sheet_properties'`

  **QA Scenarios**:

  ```
  Scenario: Verify fixture triggers the bug (before fix)
    Tool: Bash (PowerShell)
    Preconditions: Fixture file created at 3-column-copier/tests/fixtures/no_page_setup_pr.xlsx
    Steps:
      1. cd 3-column-copier
      2. python -c "from openpyxl import load_workbook; wb = load_workbook('tests/fixtures/no_page_setup_pr.xlsx'); ws = wb.active; ws.page_setup.autoPageBreaks = True"
    Expected Result: Command exits with AttributeError containing "NoneType" and "sheet_properties"
    Failure Indicators: Command exits 0 (no crash) — fixture doesn't reproduce the bug
    Evidence: .sisyphus/evidence/task-1-fixture-crash.txt
  ```

  ```
  Scenario: Normal Workbook fixture does NOT crash (baseline)
    Tool: Bash (PowerShell)
    Preconditions: None
    Steps:
      1. cd 3-column-copier
      2. python -c "from openpyxl import Workbook; wb = Workbook(); ws = wb.active; ws.page_setup.autoPageBreaks = True; print('OK')"
    Expected Result: Prints "OK", exit 0
    Evidence: .sisyphus/evidence/task-1-normal-baseline.txt
  ```

  **Commit**: YES (groups with Task 3)
  - Message: `test(3-column-copier): add fixture for missing pageSetupPr`
  - Files: `3-column-copier/tests/fixtures/no_page_setup_pr.xlsx`

- [x] 2. Verify existing test baseline

  **What to do**:
  - Run the full test suite BEFORE any changes to confirm green baseline
  - Run tool 3 tests, tool 5 tests, E2E test, run.py test
  - Record the baseline: all tests should pass (E2E passes with monkey-patch)

  **Must NOT do**:
  - Do NOT change any code yet — this is baseline verification only

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Run commands and record output

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 8 (comparison)
  - **Blocked By**: None

  **References**:
  - `AGENTS.md` — commands section for pytest invocation
  - `requirements.txt` — dependencies: pytest>=7.0, openpyxl>=3.0

  **Acceptance Criteria**:
  - [ ] `cd 3-column-copier && python -m pytest tests/ -v` → all 31 pass
  - [ ] `cd 5-png-inserter && python -m pytest tests/ -v` → all 50 pass
  - [ ] `python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v` → 6 pass
  - [ ] E2E test uses monkey-patch (verified in output)
  - [ ] Output saved to `.sisyphus/evidence/task-2-baseline.txt`

  **QA Scenarios**:

  ```
  Scenario: Full test suite passes before changes
    Tool: Bash (PowerShell)
    Preconditions: Clean working tree (no uncommitted changes)
    Steps:
      1. python -m pytest 3-column-copier/tests/ -v --tb=short
      2. python -m pytest 5-png-inserter/tests/ -v --tb=short
      3. python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v --tb=short
    Expected Result: All tests pass, exit 0 from each command. E2E test output mentions "patch_openpyxl" or monkey-patch.
    Failure Indicators: Any FAILED test — baseline is broken, fix before proceeding
    Evidence: .sisyphus/evidence/task-2-baseline.txt
  ```

  **Commit**: NO (baseline only)

- [x] 3. Fix copier.py gate + print_setup.py defensive try/except

  **What to do**:
  - **copier.py**: Move `_setup_a4_print(tws, print_title_rows_str)` from BEFORE the `if page_break_enabled:` guard to INSIDE it. Restructure lines 143-147:
    ```python
    if page_break_enabled:
        _setup_a4_print(tws, print_title_rows_str)
        page_rows = _calc_page_rows(tws, config.get("a4_page_rows"))
    else:
        page_rows = None
    ```
  - **print_setup.py**: Wrap `ws.page_setup.autoPageBreaks = True` (line 25) in try/except:
    ```python
    try:
        ws.page_setup.autoPageBreaks = True
    except AttributeError:
        print("[WARNING] Could not set autoPageBreaks: worksheet XML missing pageSetupPr element", file=sys.stderr)
    ```

  **Must NOT do**:
  - Do NOT change the order of `_setup_a4_print` vs `_calc_page_rows` — setup must run first (sets margins that calc reads)
  - Do NOT add try/except around the ENTIRE function — only `autoPageBreaks` line
  - Do NOT change any other lines in `_setup_a4_print`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Two surgical edits, well-defined target lines

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 4 — different tool)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 5
  - **Blocked By**: Task 1 (fixture)

  **References**:
  - `3-column-copier/copier.py:140-148` — current structure showing unconditional `_setup_a4_print` + gated `_calc_page_rows`
  - `3-column-copier/src/print_setup.py:15-34` — `_setup_a4_print` function, line 25 is the crash site
  - `3-column-copier/config.json:61` — `"page_break_enabled": false` — confirms this is the normal config on your machine
  - `3-column-copier/tests/fixtures/no_page_setup_pr.xlsx` — fixture created in Task 1 for verification

  **Acceptance Criteria**:
  - [ ] `_setup_a4_print` is inside `if page_break_enabled:` block (copier.py)
  - [ ] `autoPageBreaks = True` is wrapped in try/except `AttributeError` (print_setup.py)
  - [ ] With `page_break_enabled=False`, `_setup_a4_print` is NOT called (no debug output)
  - [ ] With `page_break_enabled=True` + normal file, behavior unchanged
  - [ ] With `page_break_enabled=True` + fixture file, prints WARNING to stderr but does NOT crash

  **QA Scenarios**:

  ```
  Scenario: page_break_enabled=False does NOT trigger A4 print setup
    Tool: Bash (PowerShell)
    Preconditions: Fix applied to copier.py
    Steps:
      1. cd 3-column-copier
      2. python -c "from copier import main; config = {'matching_file': '../matching.xlsx', 'matching_sheet': 'match', 'filename_col': 'Site', 'planwork_col': 'PW Number', 'data_sheet': 'cutsheet', 'target_sheet': 'IP & Port Assignment', 'source_start_row': 3, 'paste_start_row': 3, 'columns': {}, 'source_folder': './source', 'target_folder': './target', 'output_folder': './output', 'action': 'copy', 'paste_mode': 'append', 'page_break_enabled': False, 'a4_page_rows': None, 'print_title_rows': None}; print('page_break_enabled:', config['page_break_enabled'])"
    Expected Result: No "[DEBUG] _setup_a4_print" in stderr output
    Evidence: .sisyphus/evidence/task-3-gate-disabled.txt
  ```

  ```
  Scenario: Graceful handling of missing pageSetupPr
    Tool: Bash (PowerShell)
    Preconditions: Fixture from Task 1 exists, fix applied to print_setup.py
    Steps:
      1. cd 3-column-copier
      2. python -c "from openpyxl import load_workbook; from src.print_setup import _setup_a4_print; wb = load_workbook('tests/fixtures/no_page_setup_pr.xlsx'); ws = wb.active; _setup_a4_print(ws); print('SUCCESS: no crash'); wb.close()"
    Expected Result: Prints "SUCCESS: no crash", exit 0. Stderr contains "[WARNING] Could not set autoPageBreaks"
    Failure Indicators: AttributeError crash — fix not working
    Evidence: .sisyphus/evidence/task-3-graceful.txt
  ```

  **Commit**: YES
  - Message: `fix(3-column-copier): gate A4 print setup behind page_break_enabled, handle missing pageSetupPr`
  - Files: `3-column-copier/copier.py`, `3-column-copier/src/print_setup.py`
  - Pre-commit: `cd 3-column-copier && python -m pytest tests/ -v`

- [x] 4. Fix inserter.py defensive try/except + debug message

  **What to do**:
  - **inserter.py**: Wrap `ws.page_setup.autoPageBreaks = True` (line 79) in try/except (same pattern as tool 3):
    ```python
    try:
        ws.page_setup.autoPageBreaks = True
    except AttributeError:
        print("[WARNING] Could not set autoPageBreaks: worksheet XML missing pageSetupPr element", file=sys.stderr)
    ```
  - **inserter.py**: Fix debug message on line 87 from `autoPageBreaks=False` to `autoPageBreaks=True`:
    ```python
    # Before: f"... autoPageBreaks=False, print_title_rows=..."
    # After:  f"... autoPageBreaks=True, print_title_rows=..."
    ```

  **Must NOT do**:
  - Do NOT gate `_setup_a4_print` behind `page_break_enabled` in tool 5 — it's called unconditionally for margins/paper setup, and that's correct
  - Do NOT remove the `_a4_print_setup_done` global guard — it only gates debug output, not functionality
  - Do NOT fix the `_parse_print_title_rows` return value bug — separate issue

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Two surgical edits in one function, identical pattern to Task 3

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 3 — different tool)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 1 (fixture)

  **References**:
  - `5-png-inserter/src/inserter.py:69-88` — `_setup_a4_print` function: line 79 crash site, line 87 buggy debug message
  - `5-png-inserter/insert.py:211-219` — call site showing unconditional `_setup_a4_print` + gated `_calc_page_rows` (this is correct for tool 5 — margins always needed)
  - `3-column-copier/src/print_setup.py:25` — completed Task 3 fix for identical pattern reference

  **Acceptance Criteria**:
  - [ ] `autoPageBreaks = True` is wrapped in try/except `AttributeError` (inserter.py:79)
  - [ ] Debug message says `autoPageBreaks=True` not `False` (inserter.py:87)
  - [ ] With fixture file, `_setup_a4_print` prints WARNING but does NOT crash
  - [ ] With normal file, behavior unchanged (margins set, paperSize=9, portrait)

  **QA Scenarios**:

  ```
  Scenario: Graceful handling of missing pageSetupPr in tool 5
    Tool: Bash (PowerShell)
    Preconditions: Fixture from Task 1 exists (copy or recreate for tool 5), fix applied to inserter.py
    Steps:
      1. cd 5-png-inserter
      2. Copy fixture: Copy-Item ../3-column-copier/tests/fixtures/no_page_setup_pr.xlsx tests/fixtures/ -Force
      3. python -c "from openpyxl import load_workbook; from src.inserter import _setup_a4_print; wb = load_workbook('tests/fixtures/no_page_setup_pr.xlsx'); ws = wb.active; _setup_a4_print(ws); print('SUCCESS: no crash'); wb.close()"
    Expected Result: Prints "SUCCESS: no crash", exit 0. Stderr contains "[WARNING] Could not set autoPageBreaks"
    Failure Indicators: AttributeError crash — fix not working
    Evidence: .sisyphus/evidence/task-4-graceful.txt
  ```

  ```
  Scenario: Debug message now says autoPageBreaks=True
    Tool: Bash (PowerShell)
    Preconditions: Fix applied to inserter.py
    Steps:
      1. cd 5-png-inserter
      2. python -c "from openpyxl import Workbook; from src.inserter import _setup_a4_print; wb = Workbook(); ws = wb.active; _setup_a4_print(ws); wb.close()" 2>&1
    Expected Result: Stderr contains "autoPageBreaks=True" (not "False")
    Evidence: .sisyphus/evidence/task-4-debug-msg.txt
  ```

  **Commit**: YES
  - Message: `fix(5-png-inserter): handle missing pageSetupPr, fix debug message`
  - Files: `5-png-inserter/src/inserter.py`
  - Pre-commit: `cd 5-png-inserter && python -m pytest tests/ -v`

- [x] 5. Add regression + guard tests for tool 3

  **What to do**:
  - Add to `3-column-copier/tests/test_print_setup.py`:
    - `test_no_crash_on_missing_page_setup_pr`: Loads fixture from Task 1, calls `_setup_a4_print(ws)`, asserts no exception raised
    - `test_warning_printed_on_missing_page_setup_pr`: Same as above + captures stderr via `capsys`, asserts "[WARNING]" appears
  - Run tool 3 tests to verify all pass

  **Must NOT do**:
  - Do NOT modify existing test cases — add new ones only
  - Do NOT test copier.main() guard behavior via unit test — that's covered by Task 2 baseline + Task 3 QA scenario

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Add 2 test methods following existing patterns in test_print_setup.py

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 6 and Task 7)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 8
  - **Blocked By**: Task 3 (fix must be in place)

  **References**:
  - `3-column-copier/tests/test_print_setup.py:11-20` — `TestSetupA4Print.test_sets_properties` pattern: `wb = Workbook()`, `ws = wb.active`, call function, `assert` properties, `wb.close()`
  - `3-column-copier/tests/test_print_setup.py:66-71` — `test_guard_too_many_headers` — example of `capsys` usage for stderr assertion
  - `3-column-copier/tests/fixtures/no_page_setup_pr.xlsx` — fixture from Task 1
  - `3-column-copier/conftest.py` — sys.path setup for imports

  **Acceptance Criteria**:
  - [ ] `test_no_crash_on_missing_page_setup_pr` passes — loads fixture, calls `_setup_a4_print`, no exception
  - [ ] `test_warning_printed_on_missing_page_setup_pr` passes — captures stderr, asserts WARNING present
  - [ ] ALL existing `test_print_setup.py` tests still pass
  - [ ] `python -m pytest 3-column-copier/tests/ -v` → all 33 pass (31 existing + 2 new)

  **QA Scenarios**:

  ```
  Scenario: New regression tests pass
    Tool: Bash (PowerShell)
    Preconditions: Tasks 1 and 3 complete (fixture exists, fix applied)
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_print_setup.py -v -k "missing_page_setup_pr"
    Expected Result: 2 tests collected, 2 passed
    Evidence: .sisyphus/evidence/task-5-regression-tests.txt
  ```

  ```
  Scenario: Full tool 3 test suite still green
    Tool: Bash (PowerShell)
    Preconditions: All changes applied, new tests added
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/ -v --tb=short
    Expected Result: All tests pass (31 + 2 = 33), exit 0
    Failure Indicators: Any FAILED test
    Evidence: .sisyphus/evidence/task-5-full-suite.txt
  ```

  **Commit**: YES (groups with Task 3 commit)
  - Files: `3-column-copier/tests/test_print_setup.py`

- [x] 6. Add regression test for tool 5

  **What to do**:
  - Add to `5-png-inserter/tests/test_page_breaks.py`:
    - `test_no_crash_on_missing_page_setup_pr`: Loads fixture (copied from tool 3), calls `_setup_a4_print(ws)`, asserts no exception raised
  - Run tool 5 tests to verify all pass

  **Must NOT do**:
  - Do NOT add tests for guard behavior — tool 5 doesn't gate `_setup_a4_print` (correctly: margins always needed)
  - Do NOT modify existing test cases

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Add 1 test method following existing TestPageBreakConfig patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5 and Task 7)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 8
  - **Blocked By**: Task 4 (fix must be in place)

  **References**:
  - `5-png-inserter/tests/test_page_breaks.py:138-144` — `test_auto_page_breaks_enabled` pattern: `wb = Workbook()`, `ws = wb.active`, `_setup_a4_print(ws)`, `assert autoPageBreaks is True`
  - `5-png-inserter/tests/test_page_breaks.py:19-35` — `_make_test_png()` helper (not needed for this test, but shows module conventions)
  - `5-png-inserter/conftest.py` — sys.path setup for imports

  **Acceptance Criteria**:
  - [ ] `test_no_crash_on_missing_page_setup_pr` passes — loads fixture, calls `_setup_a4_print`, no exception
  - [ ] ALL existing `test_page_breaks.py` tests still pass
  - [ ] `python -m pytest 5-png-inserter/tests/ -v` → all 51 pass (50 existing + 1 new)

  **QA Scenarios**:

  ```
  Scenario: New regression test passes for tool 5
    Tool: Bash (PowerShell)
    Preconditions: Tasks 1 and 4 complete (fixture copied, fix applied)
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/test_page_breaks.py -v -k "missing_page_setup_pr"
    Expected Result: 1 test collected, 1 passed
    Evidence: .sisyphus/evidence/task-6-regression-test.txt
  ```

  ```
  Scenario: Full tool 5 test suite still green
    Tool: Bash (PowerShell)
    Preconditions: All changes applied, new test added
    Steps:
      1. cd 5-png-inserter
      2. python -m pytest tests/ -v --tb=short
    Expected Result: All tests pass (50 + 1 = 51), exit 0
    Failure Indicators: Any FAILED test
    Evidence: .sisyphus/evidence/task-6-full-suite.txt
  ```

  **Commit**: YES (groups with Task 4 commit)
  - Files: `5-png-inserter/tests/test_page_breaks.py`

- [x] 7. Remove E2E monkey-patch + verify

  **What to do**:
  - Remove `_OPENPYXL_PATCH` variable and the monkey-patch logic from `tests/test_pipeline_e2e.py` (lines 43-56)
  - Remove `patch_openpyxl` parameter from `_write_stage_script` for stages 3 and 5 (or set to `False`)
  - Verify E2E test passes WITHOUT the monkey-patch — confirming the fix works end-to-end

  **Must NOT do**:
  - Do NOT change any other part of the E2E test
  - Do NOT change the stage scripts' actual logic — only the patching wrapper

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Remove dead code + verify

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5 and Task 6)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 8
  - **Blocked By**: Task 3, Task 4 (fixes must be in place)

  **References**:
  - `tests/test_pipeline_e2e.py:43-56` — `_OPENPYXL_PATCH` monkey-patch to remove
  - `tests/test_pipeline_e2e.py` — search for `_OPENPYXL_PATCH` and `patch_openpyxl` to find all references
  - `tests/test_pipeline_e2e.py` — `_write_stage_script` calls for stages 3 and 5 that pass `patch_openpyxl=True`

  **Acceptance Criteria**:
  - [ ] `_OPENPYXL_PATCH` variable removed from `test_pipeline_e2e.py`
  - [ ] No remaining references to `patch_openpyxl` or `_OPENPYXL_PATCH` in the file
  - [ ] `python -m pytest tests/test_pipeline_e2e.py -v` → 1 test passes, exit 0
  - [ ] `python -m pytest tests/test_run.py -v` → 5 tests pass, exit 0

  **QA Scenarios**:

  ```
  Scenario: E2E test passes without monkey-patch
    Tool: Bash (PowerShell)
    Preconditions: All fixes applied (Tasks 3, 4), Tasks 5-6 tests pass
    Steps:
      1. python -m pytest tests/test_pipeline_e2e.py -v --tb=long
    Expected Result: 1 test collected, 1 passed, exit 0. No "patch_openpyxl" or "_OPENPYXL_PATCH" in output.
    Failure Indicators: E2E test fails with AttributeError — fixes not sufficient
    Evidence: .sisyphus/evidence/task-7-e2e-clean.txt
  ```

  ```
  Scenario: run.py tests still pass
    Tool: Bash (PowerShell)
    Preconditions: E2E test passes
    Steps:
      1. python -m pytest tests/test_run.py -v --tb=short
    Expected Result: 5 tests passed, exit 0
    Evidence: .sisyphus/evidence/task-7-run-tests.txt
  ```

  **Commit**: YES
  - Message: `test: remove E2E autoPageBreaks monkey-patch (fix applied)`
  - Files: `tests/test_pipeline_e2e.py`

- [x] 8. Final verification — full test suite

  **What to do**:
  - Run the COMPLETE test suite across all tools and root tests
  - Compare against Task 2 baseline: all tests that passed before must still pass
  - Verify new tests pass
  - Report final numbers: total tests, pass/fail, any regressions

  **Must NOT do**:
  - Do NOT skip any test suite
  - Do NOT ignore test failures — investigate every one

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Run commands and verify output

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential — compares against baseline)
  - **Parallel Group**: FINAL
  - **Blocks**: None (last task)
  - **Blocked By**: Task 5, Task 6, Task 7

  **References**:
  - `.sisyphus/evidence/task-2-baseline.txt` — pre-fix baseline to compare against
  - `AGENTS.md` — commands section

  **Acceptance Criteria**:
  - [ ] `cd 3-column-copier && python -m pytest tests/ -v` → 33 tests pass (31 original + 2 new)
  - [ ] `cd 5-png-inserter && python -m pytest tests/ -v` → 51 tests pass (50 original + 1 new)
  - [ ] `python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v` → 6 tests pass (no monkey-patch)
  - [ ] Zero regressions: no test that passed in Task 2 baseline now fails
  - [ ] Total: 33 + 51 + 6 = 90 tests pass

  **QA Scenarios**:

  ```
  Scenario: Complete test suite passes
    Tool: Bash (PowerShell)
    Preconditions: All prior tasks complete, all changes applied
    Steps:
      1. python -m pytest 3-column-copier/tests/ -v --tb=short
      2. python -m pytest 5-png-inserter/tests/ -v --tb=short
      3. python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v --tb=short
    Expected Result: All three commands exit 0. Total: 33+51+6 = 90 passed, 0 failed.
    Failure Indicators: Any FAILED or ERROR test
    Evidence: .sisyphus/evidence/task-8-final-suite.txt
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave

- [x] F1. **Full Test Suite** — run ALL 155+ tests across all tools + root
  ```bash
  cd 3-column-copier && python -m pytest tests/ -v
  cd 5-png-inserter && python -m pytest tests/ -v
  python -m pytest tests/test_pipeline_e2e.py tests/test_run.py -v
  ```
  Output: `Tool 3 [N/N pass] | Tool 5 [N/N pass] | E2E [PASS] | VERDICT`

---

## Commit Strategy

- **1**: `fix(3-column-copier): gate A4 print setup behind page_break_enabled` — copier.py, print_setup.py, test_print_setup.py
- **2**: `fix(5-png-inserter): defensive try/except on autoPageBreaks` — inserter.py, test_page_breaks.py
- **3**: `test: remove E2E autoPageBreaks monkey-patch` — test_pipeline_e2e.py

---

## Success Criteria

### Verification Commands
```bash
cd 3-column-copier && python -m pytest tests/ -v    # Expected: 33 passed (31 original + 2 new)
cd 5-png-inserter && python -m pytest tests/ -v     # Expected: 51 passed (50 original + 1 new)
python -m pytest tests/test_pipeline_e2e.py -v       # Expected: 1 passed (no monkey-patch)
python -m pytest tests/test_run.py -v                # Expected: 5 passed
```

### Final Checklist
- [ ] `_setup_a4_print` in copier.py only called when `page_break_enabled=True`
- [ ] Both `_setup_a4_print` implementations survive missing `pageSetupPr`
- [ ] Existing behavior unchanged when `page_break_enabled=True` with normal files
- [ ] All 155+ tests pass
- [ ] E2E test passes without monkey-patch
