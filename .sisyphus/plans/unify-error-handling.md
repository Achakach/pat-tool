# Unify matching.xlsx Error Handling + Dead Config Cleanup

## TL;DR

> **Quick Summary**: Make all 3 matching.xlsx parsers raise `ValueError` on missing header columns (Tool 5 already does this; fix Tools 2 and 3). Remove unused `planwork_col` from Tool 2's config.json. TDD workflow.
>
> **Deliverables**:
> - Tool 2: `sys.exit(1)` → `raise ValueError` for missing `filename_col` header
> - Tool 3: `return {}` → `raise ValueError` for missing `filename_col` or `planwork_col` header (checked independently)
> - Tool 2: `config.json` cleaned of unused `planwork_col` key
> - Tool 2: 1 test assertion updated (SystemExit → ValueError)
> - Tool 3: 2 new error-state tests added
> - All 58 tests across both tools pass (15 + 43)
>
> **Estimated Effort**: Quick
> **Parallel Execution**: YES — 3 waves (2 parallel pairs + verify)
> **Critical Path**: Task 1 → Task 3 → Task 5 → Task 6

---

## Context

### Original Request
User reviewed the 4 remaining technical debt items from `handover.md` and chose to fix:
- **Problem 2**: Inconsistent error handling across 3 `matching.xlsx` parsers
- **Problem 4**: Dead `planwork_col` config key in Tool 2

### Interview Summary
**Key Discussions**:
- Problem 1 (different return types): Clarified — Tools 3 and 5 need opposite-direction maps. Not a bug, not in scope.
- Problem 3 (duplicate PW silently overwritten): User said "don't worry about this, it won't happen." Excluded.
- Error handling: All parsers should raise `ValueError` (following Tool 5's existing pattern)
- Dead config: Remove `planwork_col` from Tool 2's config.json only (not unify into shared module yet)
- Test strategy: **TDD** — RED (write/update tests) → GREEN (implement) → VERIFY

**Research Findings**:
- Tool 2 has 5 `pytest.raises(SystemExit)` tests but **only 1** (`test_missing_column_header`) tests missing column headers. The other 4 test file-not-found / empty-data and must stay.
- Tool 3 has **zero** error-state tests for `read_matching()` — need 2 new tests.
- Tool 3's current guard checks both columns in one condition — must split into independent checks like Tool 5.
- Tool 5 is already correct — no changes needed.

### Metis Review
**Identified Gaps** (addressed):
- **Only 1 test needs updating**: Corrected from "4 tests" to 1. Other SystemExit tests are for non-header conditions.
- **Tool 3 must check columns independently**: Current `if not fn_idx or not pw_idx` can't distinguish which column is missing.
- **Error message format**: Match Tool 5: `f"Column '{col}' not found in headers (row 1)"`.
- **Guardrail: ValueError vs SystemExit boundary**: Missing columns → `ValueError`. File not found / empty data → `sys.exit(1)`.
- **Scope creep lockdown**: Must NOT touch `dep/`, other configs, or unify into shared module.

---

## Work Objectives

### Core Objective
Make `matching.xlsx` header-column error handling consistent across all 3 tools (all raise `ValueError`), and remove dead config from Tool 2.

### Concrete Deliverables
- `2-template-generator/generate.py`: Missing `filename_col` raises `ValueError` (not `sys.exit(1)`)
- `3-column-copier/copier.py`: `read_matching()` raises `ValueError` for missing `filename_col` or `planwork_col` (independent checks)
- `2-template-generator/config.json`: `planwork_col` key removed
- `2-template-generator/tests/test_generate.py`: `test_missing_column_header` updated
- `3-column-copier/tests/test_real_mapping.py`: 2 new error-state tests

### Definition of Done
- [ ] `2-template-generator/`: `python -m pytest tests/ -v` → 15/15 pass
- [ ] `3-column-copier/`: `python -m pytest tests/ -v` → 43/43 pass (41 existing + 2 new)
- [ ] Missing `filename_col` in Tool 2 raises `ValueError` (not `SystemExit`)
- [ ] Missing `filename_col` in Tool 3 raises `ValueError` (not silent `{}`)
- [ ] Missing `planwork_col` in Tool 3 raises `ValueError` (not silent `{}`)
- [ ] Tool 2 config.json has no `planwork_col` key

### Must Have
- Consistent `ValueError` for missing header columns across all 3 tools
- Independent column checks in Tool 3 (matching Tool 5 pattern)
- Error message format: `"Column '{col}' not found in headers (row 1)"`

### Must NOT Have (Guardrails)
- Must NOT change file-not-found errors (still `sys.exit(1)`)
- Must NOT change empty-data errors (still `sys.exit(1)` in Tool 2, still `return {}` in Tool 3)
- Must NOT touch Tool 5 (already correct)
- Must NOT remove `planwork_col` from Tool 3 or Tool 5 configs
- Must NOT touch `dep/` folder
- Must NOT unify into shared module (future work)
- Must NOT add new features

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (pytest, both tools)
- **Automated tests**: TDD (RED-GREEN-VERIFY)
- **Framework**: pytest with `tmp_path` fixtures

### QA Policy
Every task includes agent-executed QA scenarios. Evidence to `.sisyphus/evidence/task-{N}-{slug}.{ext}`.
- **Python/CLI**: Bash — run pytest, check output, verify exit codes
- **Config validation**: Bash — Python one-liner to read JSON, assert key absent

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (RED — Start Immediately, parallel):
├── Task 1: Tool 2 — Update test assertion [quick]
└── Task 2: Tool 3 — Add 2 new error-state tests [quick]

Wave 2 (GREEN — After Wave 1, parallel):
├── Task 3: Tool 2 — Change sys.exit(1) → ValueError [quick]
└── Task 4: Tool 3 — Change return {} → ValueError (independent checks) [quick]

Wave 3 (VERIFY — After Wave 2, sequential):
├── Task 5: Tool 2 — Remove dead planwork_col from config.json [quick]
└── Task 6: Run all tests, verify everything passes [quick]

Critical Path: Task 1 → Task 3 → Task 5 → Task 6
                   Task 2 → Task 4 ↗
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 2 (Waves 1 & 2)
```

### Dependency Matrix

| Task | Blocked By | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 3 | 1 |
| 2 | - | 4 | 1 |
| 3 | 1 | 5 | 2 |
| 4 | 2 | 6 | 2 |
| 5 | 3 | 6 | 3 |
| 6 | 4, 5 | - | 3 |

### Agent Dispatch Summary

- **Wave 1**: 2 `quick` — T1, T2 (independent test file edits)
- **Wave 2**: 2 `quick` — T3, T4 (independent source file edits)
- **Wave 3**: 1 `quick` — T5 then T6 (config then verify)

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. **Tool 2 RED** — Update `test_missing_column_header` assertion

  **What to do**:
  - Open `2-template-generator/tests/test_generate.py`
  - Find `test_missing_column_header` (around line 273)
  - Change `with pytest.raises(SystemExit):` to `with pytest.raises(ValueError, match="NonexistentCol"):`
  - The `match` parameter verifies the error message contains the column name
  - Verify test now FAILS (RED phase — code still uses `sys.exit(1)`)
  - Run: `cd 2-template-generator && python -m pytest tests/test_generate.py::TestGenerate::test_missing_column_header -v` → **FAIL** (expected)

  **Must NOT do**:
  - Must NOT change `test_template_not_found`, `test_matching_not_found`, `test_no_filenames_found`, `test_empty_site_creates_none_file` — these remain `SystemExit`
  - Must NOT change `test_cli.py` tests

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Single test file edit, well-defined change location
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES — Wave 1 (with Task 2)
  - **Blocks**: Task 3
  - **Blocked By**: None

  **References**:
  - `2-template-generator/tests/test_generate.py:273` — `test_missing_column_header` — the test to update
  - `2-template-generator/generate.py:43-46` — current `sys.exit(1)` code being tested
  - `5-png-inserter/src/matcher.py:17-18` — Tool 5's ValueError pattern: `raise ValueError(f"Column '{filename_col}' not found in headers (row 1)")`
  - `2-template-generator/tests/test_generate.py:139` — `test_matching_not_found` — example of SystemExit test that must NOT change

  **Acceptance Criteria**:
  - [ ] `test_missing_column_header` uses `pytest.raises(ValueError, match="NonexistentCol")`
  - [ ] Test FAILS when run (code still raises SystemExit)

  **QA Scenarios**:

  ```
  Scenario: RED phase — test fails because code still uses SystemExit
    Tool: Bash
    Preconditions: Only test file changed, source code unchanged
    Steps:
      1. cd 2-template-generator
      2. python -m pytest tests/test_generate.py::TestGenerate::test_missing_column_header -v
      3. Assert exit code is 1 (test failure)
      4. Assert output contains "SystemExit" or "DID NOT RAISE"
    Expected Result: Test FAILS — code raises SystemExit but test expects ValueError
    Evidence: .sisyphus/evidence/task-1-red-fail.txt
  ```

  **Commit**: YES (groups with Task 3)
  - Message: `test(tool2): expect ValueError for missing matching column`
  - Files: `2-template-generator/tests/test_generate.py`

- [x] 2. **Tool 3 RED** — Add 2 new error-state tests for `read_matching()`

  **What to do**:
  - Open `3-column-copier/tests/test_real_mapping.py`
  - Add new test functions that import `read_matching` directly (already imported)
  - **Test A**: `test_read_matching_missing_filename_col`
    - Create matching.xlsx with ONLY `PW Number` header (no `Site` column)
    - Call `read_matching(path, "match", "Site", "PW Number")`
    - Assert `pytest.raises(ValueError, match="Site")`
  - **Test B**: `test_read_matching_missing_planwork_col`
    - Create matching.xlsx with ONLY `Site` header (no `PW Number` column)
    - Call `read_matching(path, "match", "Site", "PW Number")`
    - Assert `pytest.raises(ValueError, match="PW Number")`
  - Use `tmp_path` fixture + `openpyxl.Workbook()` to create in-memory test files
  - Follow existing test patterns (see `_make_matching` helper in `test_cli.py`)
  - Verify both tests FAIL (RED phase — `read_matching` still returns `{}`)
  - Run: `cd 3-column-copier && python -m pytest tests/test_real_mapping.py -v -k "missing"` → 2 failures

  **Must NOT do**:
  - Must NOT modify existing tests
  - Must NOT add tests for other error conditions (file not found, empty data, bad sheet name)
  - Must NOT change `_make_matching` helper or other test infrastructure

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Two focused test additions in one file
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES — Wave 1 (with Task 1)
  - **Blocks**: Task 4
  - **Blocked By**: None

  **References**:
  - `3-column-copier/tests/test_real_mapping.py` — file to add tests to, has existing `read_matching` import
  - `2-template-generator/tests/test_generate.py:20` — `_make_matching` helper pattern for creating matching.xlsx in tests (adapt for openpyxl.Workbook)
  - `3-column-copier/copier.py:20-42` — `read_matching()` function being tested
  - `5-png-inserter/src/matcher.py:17-22` — Tool 5's separate column checks (pattern Tool 3 will adopt)
  - `2-template-generator/tests/test_generate.py:273` — Tool 2's equivalent test (reference for assertion style)

  **Acceptance Criteria**:
  - [ ] `test_read_matching_missing_filename_col` exists, asserts `pytest.raises(ValueError, match="Site")`
  - [ ] `test_read_matching_missing_planwork_col` exists, asserts `pytest.raises(ValueError, match="PW Number")`
  - [ ] Both tests FAIL when run (code still returns `{}`)

  **QA Scenarios**:

  ```
  Scenario: RED phase — both new tests fail
    Tool: Bash
    Preconditions: Only test file changed, source code unchanged
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_real_mapping.py -v -k "missing"
      3. Assert exit code is 1 (test failures)
      4. Assert both tests show FAILED with "ValueError" in output
    Expected Result: 2 tests FAIL — code returns {} but tests expect ValueError
    Evidence: .sisyphus/evidence/task-2-red-fail.txt
  ```

  **Commit**: YES (groups with Task 4)
  - Message: `test(tool3): add read_matching error-state tests for missing columns`
  - Files: `3-column-copier/tests/test_real_mapping.py`

- [x] 3. **Tool 2 GREEN** — Change `sys.exit(1)` to `raise ValueError`

  **What to do**:
  - Open `2-template-generator/generate.py`
  - Find the missing column header block (around lines 43-46):
    ```python
    if fn_col is None:
        print(f"Column '{config['filename_col']}' not found in matching file headers", file=sys.stderr)
        sys.exit(1)
    ```
  - Replace with:
    ```python
    if fn_col is None:
        raise ValueError(f"Column '{config['filename_col']}' not found in headers (row 1)")
    ```
  - Message format matches Tool 5: `f"Column '{col}' not found in headers (row 1)"`
  - Run targeted test: `cd 2-template-generator && python -m pytest tests/test_generate.py::TestGenerate::test_missing_column_header -v` → PASS
  - Run full suite: `cd 2-template-generator && python -m pytest tests/ -v` → 15/15 pass

  **Must NOT do**:
  - Must NOT change `sys.exit(1)` for file-not-found (`test_template_not_found`, `test_matching_not_found`)
  - Must NOT change `sys.exit(1)` for empty data (`test_no_filenames_found`, `test_empty_site_creates_none_file`)
  - Must NOT change error message format — must match Tool 5 exactly

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Single code block replacement in one file
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES — Wave 2 (with Task 4)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1

  **References**:
  - `2-template-generator/generate.py:43-46` — the `sys.exit(1)` block to replace
  - `5-png-inserter/src/matcher.py:17-18` — Tool 5's ValueError pattern to match
  - `2-template-generator/tests/test_generate.py:273` — the test that asserts this new behavior

  **Acceptance Criteria**:
  - [ ] `test_missing_column_header` → PASS
  - [ ] Full suite → 15/15 pass
  - [ ] Error message: `"Column 'NonexistentCol' not found in headers (row 1)"`

  **QA Scenarios**:

  ```
  Scenario: GREEN phase — test_missing_column_header passes
    Tool: Bash
    Preconditions: Tasks 1 and 3 complete
    Steps:
      1. cd 2-template-generator
      2. python -m pytest tests/test_generate.py::TestGenerate::test_missing_column_header -v
      3. Assert exit code is 0
      4. Assert output contains "1 passed"
    Expected Result: Test PASSES — ValueError raised with correct message
    Evidence: .sisyphus/evidence/task-3-green-pass.txt

  Scenario: Regression check — all Tool 2 tests pass
    Tool: Bash
    Preconditions: Task 3 complete
    Steps:
      1. cd 2-template-generator
      2. python -m pytest tests/ -v
      3. Assert exit code is 0
      4. Assert output contains "15 passed"
    Expected Result: All 15 tests pass, no regressions
    Failure Indicators: Any failure — check if non-header SystemExit was accidentally changed
    Evidence: .sisyphus/evidence/task-3-regression.txt
  ```

  **Commit**: YES (groups with Task 1)
  - Message: `fix(tool2): raise ValueError for missing matching column header`
  - Files: `2-template-generator/generate.py`

- [x] 4. **Tool 3 GREEN** — Change `return {}` to `raise ValueError` (independent checks)

  **What to do**:
  - Open `3-column-copier/copier.py`
  - Find `read_matching()` function (lines 20-42)
  - Current code (lines 29-31):
    ```python
    if not fn_idx or not pw_idx:
        wb.close()
        return {}
    ```
  - Replace with independent checks (matching Tool 5 pattern):
    ```python
    if fn_idx is None:
        wb.close()
        raise ValueError(f"Column '{filename_col}' not found in headers (row 1)")
    if pw_idx is None:
        wb.close()
        raise ValueError(f"Column '{planwork_col}' not found in headers (row 1)")
    ```
  - **Critical**: Must use `is None` (not truthiness) — column index 0 would be falsy
  - Must call `wb.close()` before each raise
  - Run new tests: `cd 3-column-copier && python -m pytest tests/test_real_mapping.py -v -k "missing"` → 2 PASS
  - Run full suite: `cd 3-column-copier && python -m pytest tests/ -v` → 43/43 pass

  **Must NOT do**:
  - Must NOT use `if not fn_idx` — must use `if fn_idx is None`
  - Must NOT change function signature, happy path, or empty-data behavior (still `return {}` for empty rows)

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Single code block replacement, well-defined pattern
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES — Wave 2 (with Task 3)
  - **Blocks**: Task 6
  - **Blocked By**: Task 2

  **References**:
  - `3-column-copier/copier.py:29-31` — the `return {}` block to replace
  - `5-png-inserter/src/matcher.py:17-22` — Tool 5's pattern (separate `is None` checks)
  - `3-column-copier/tests/test_real_mapping.py` — the tests from Task 2

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_real_mapping.py -v -k "missing"` → 2 PASS
  - [ ] `python -m pytest tests/ -v` → 43/43 pass
  - [ ] Missing `filename_col` raises `ValueError` with `"Site"` in message
  - [ ] Missing `planwork_col` raises `ValueError` with `"PW Number"` in message

  **QA Scenarios**:

  ```
  Scenario: GREEN phase — both new tests pass
    Tool: Bash
    Preconditions: Tasks 2 and 4 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_real_mapping.py -v -k "missing"
      3. Assert exit code is 0
      4. Assert output contains "2 passed"
    Expected Result: Both tests PASS — ValueError raised correctly
    Evidence: .sisyphus/evidence/task-4-green-pass.txt

  Scenario: Regression check — all Tool 3 tests pass
    Tool: Bash
    Preconditions: Task 4 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/ -v
      3. Assert exit code is 0
      4. Assert output contains "43 passed"
    Expected Result: All 43 tests pass (41 original + 2 new), no regressions
    Evidence: .sisyphus/evidence/task-4-regression.txt
  ```

  **Commit**: YES (groups with Task 2)
  - Message: `fix(tool3): raise ValueError for missing matching column headers`
  - Files: `3-column-copier/copier.py`

- [x] 5. **Tool 2 REFACTOR** — Remove dead `planwork_col` from config.json

  **What to do**:
  - Open `2-template-generator/config.json`
  - Remove the line: `"planwork_col": "PW Number",`
  - Ensure valid JSON (no trailing comma on previous line)
  - Verify: `python -c "import json; cfg = json.load(open('config.json')); assert 'planwork_col' not in cfg; print('OK')"`
  - Run tests: `cd 2-template-generator && python -m pytest tests/ -v` → 15/15 pass

  **Must NOT do**:
  - Must NOT remove `planwork_col` from any other config.json (Tool 3, Tool 5 still use it)
  - Must NOT touch `dep/` folder configs

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Single line removal from config file
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO — Wave 3 sequential (verify with changed config after Task 3)
  - **Blocks**: Task 6
  - **Blocked By**: Task 3

  **References**:
  - `2-template-generator/config.json:5` — the `"planwork_col": "PW Number",` line to remove
  - `2-template-generator/generate.py` — confirms `planwork_col` is never read
  - `2-template-generator/tests/test_generate.py` — `_cfg()` helper already omits `planwork_col`

  **Acceptance Criteria**:
  - [ ] `config.json` is valid JSON
  - [ ] `"planwork_col"` key is absent
  - [ ] `python -m pytest tests/ -v` → 15/15 pass

  **QA Scenarios**:

  ```
  Scenario: Config is valid and planwork_col removed
    Tool: Bash
    Steps:
      1. cd 2-template-generator
      2. python -c "import json; cfg = json.load(open('config.json')); assert 'planwork_col' not in cfg; assert 'filename_col' in cfg; print('Config OK')"
      3. Assert exit code is 0
    Expected Result: planwork_col absent, filename_col present, valid JSON
    Evidence: .sisyphus/evidence/task-5-config-ok.txt

  Scenario: Tests still pass with cleaned config
    Tool: Bash
    Steps:
      1. cd 2-template-generator
      2. python -m pytest tests/ -v
      3. Assert exit code is 0, "15 passed"
    Expected Result: All tests pass — dead config removal has no impact
    Evidence: .sisyphus/evidence/task-5-tests-pass.txt
  ```

  **Commit**: YES
  - Message: `chore(tool2): remove unused planwork_col from config`
  - Files: `2-template-generator/config.json`

- [x] 6. **VERIFY** — Run all tests and final validation

  **What to do**:
  - Run full suites:
    ```bash
    cd 2-template-generator && python -m pytest tests/ -v
    cd ../3-column-copier && python -m pytest tests/ -v
    ```
  - Confirm: 15/15 Tool 2, 43/43 Tool 3 = 58 total
  - Run E2E: `cd .. && python -m pytest tests/test_pipeline_e2e.py -v`
  - Check git diff for unintended changes

  **Must NOT do**:
  - Must NOT skip the E2E test

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: Test execution and result verification only
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO — Wave 3 final step
  - **Blocks**: None (final)
  - **Blocked By**: Tasks 4, 5

  **References**:
  - `2-template-generator/tests/` — Tool 2 test suite
  - `3-column-copier/tests/` — Tool 3 test suite
  - `tests/test_pipeline_e2e.py` — E2E pipeline test

  **Acceptance Criteria**:
  - [ ] Tool 2: 15/15 pass
  - [ ] Tool 3: 43/43 pass
  - [ ] E2E pipeline test passes
  - [ ] Only 5 expected files in `git diff --stat`

  **QA Scenarios**:

  ```
  Scenario: All tests pass across both tools
    Tool: Bash
    Steps:
      1. cd 2-template-generator; python -m pytest tests/ -v
      2. Assert exit code 0, "15 passed"
      3. cd ../3-column-copier; python -m pytest tests/ -v
      4. Assert exit code 0, "43 passed"
    Evidence: .sisyphus/evidence/task-6-all-tests.txt

  Scenario: E2E pipeline still works
    Tool: Bash
    Steps:
      1. cd "C:\Users\kacha\OneDrive\Desktop\PAT tool"
      2. python -m pytest tests/test_pipeline_e2e.py -v
      3. Assert exit code 0, test passes
    Evidence: .sisyphus/evidence/task-6-e2e.txt

  Scenario: Verify no unintended file changes
    Tool: Bash
    Steps:
      1. git diff --stat
      2. Assert only: generate.py, config.json, test_generate.py, copier.py, test_real_mapping.py
      3. Assert no changes to Tool 5, dep/, or other tools
    Evidence: .sisyphus/evidence/task-6-diff.txt
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present results to user and get explicit "okay".

- [x] F1. **Plan Compliance Audit** — `oracle`
  Verify each "Must Have" exists, each "Must NOT Have" absent. Check evidence files exist.
  Output: `Must Have [6/6] | Must NOT Have [7/7] | Tasks [6/6] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run tests in both tools. Check for: leftover `sys.exit(1)` for columns, `if not fn_idx` truthiness, wrong error messages, JSON trailing commas. Verify no scope creep (Tool 5, dep/, other configs untouched).
  Output: `Tests [58/58] | Code [N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Execute EVERY QA scenario. Test cross-task integration. Edge cases: column index 0 (`is None` works), empty string header, case-insensitive matching.
  Output: `Scenarios [8/8] | Edge Cases [3] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  Verify 1:1 spec-to-diff. Check "Must NOT do" compliance per task. Flag unaccounted changes.
  Output: `Tasks [6/6 compliant] | Contamination [CLEAN/N] | Unaccounted [CLEAN/N] | VERDICT`

---

## Commit Strategy

| Task(s) | Message | Files |
|---------|---------|-------|
| 1 + 3 | `fix(tool2): raise ValueError for missing matching column header` | `generate.py`, `tests/test_generate.py` |
| 2 + 4 | `fix(tool3): raise ValueError for missing matching column headers` | `copier.py`, `tests/test_real_mapping.py` |
| 5 | `chore(tool2): remove unused planwork_col from config` | `config.json` |

**3 commits total.** Each groups RED + GREEN for a tool; config cleanup standalone.

---

## Success Criteria

### Verification Commands
```bash
# Tool 2
cd 2-template-generator && python -m pytest tests/ -v
# Expected: 15 passed

# Tool 3
cd 3-column-copier && python -m pytest tests/ -v
# Expected: 43 passed

# E2E
python -m pytest tests/test_pipeline_e2e.py -v
# Expected: passed
```

### Final Checklist
- [ ] All 3 parsers raise `ValueError` on missing header columns
- [ ] Tool 3 checks columns independently (`is None`, not truthiness)
- [ ] Error message format consistent: `"Column '{col}' not found in headers (row 1)"`
- [ ] Tool 2 file-not-found / empty-data still `sys.exit(1)` (unchanged)
- [ ] Tool 2 config.json has no `planwork_col` key
- [ ] Tool 5 unchanged (already correct)
- [ ] All 58 tests pass (15 + 43)
- [ ] E2E pipeline test passes
- [ ] No changes to `dep/` or other configs
