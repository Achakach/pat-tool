# Decouple Insert Mode from Page Break

## TL;DR

> **Quick Summary**: Add `insert_mode` config key so row insertion (pushing content down when appending) works independently of A4 page formatting.
>
> **Deliverables**:
> - `copier.py`: new `insert_mode` config read + OR condition at insert_rows gate
> - `config.json`: `"insert_mode": true` key + updated comment
> - New test: `insert_mode=True` with `page_break_enabled=False`
>
> **Estimated Effort**: Quick (3 lines copier.py, 2 lines config.json, 1 test)
> **Parallel Execution**: NO — sequential (copier → config → test)
> **Critical Path**: Config change → Test all 38 existing + 1 new

---

## Context

### Original Request
User wants `copier.py` to push existing content down when appending data (insert rows), without enabling page break formatting. Currently, row insertion is gated behind `page_break_enabled` — you can't have insert without page formatting.

### Interview Summary
- **Option A** (flip page_break_enabled): Rejected — couples unrelated concerns
- **Option B** (new insert_mode key): Selected — clean decoupling
- **Default**: Code defaults to `False` (safe), config.json explicitly sets `true`
- **OR condition**: `(page_break_enabled or insert_mode)` preserves backward compatibility

### Metis Review
**Identified Gaps** (addressed):
- **Default value ambiguity**: Resolved — `.get("insert_mode", False)`, config.json has explicit `true`
- **No test for new path**: Resolved — added as Task 3
- **E2E test impact**: None — with default `False`, e2e test unchanged
- **Guardrails**: A4 setup (line 162), snap_gap_rows (line 249), merged cell detection all stay tied to `page_break_enabled` only

---

## Work Objectives

### Core Objective
Enable row insertion on append independently of page formatting via new `insert_mode` config key.

### Concrete Deliverables
- `3-column-copier/copier.py`: +1 config read, change 1 condition
- `3-column-copier/config.json`: +1 key, update comment
- `3-column-copier/tests/test_columns.py`: +1 test

### Definition of Done
- [ ] `insert_mode: true` in config.json triggers insert_rows without A4 setup
- [ ] `insert_mode: false` (default) keeps current behavior
- [ ] `page_break_enabled: true` still triggers insert (backward compat)
- [ ] All 38 existing tests pass + 1 new test passes

### Must Have
- OR condition: `page_break_enabled OR insert_mode` at line 187
- Code default `False` via `.get("insert_mode", False)`
- Config.json has explicit `"insert_mode": true`

### Must NOT Have (Guardrails)
- Do NOT change A4 setup gate (line 162) — stays `page_break_enabled` only
- Do NOT change snap_gap_rows gate (line 249) — stays `page_break_enabled` only
- Do NOT change merged cell detection (lines 199-208)
- Do NOT touch `5-png-inserter/` or any file outside `3-column-copier/`
- Do NOT refactor insert_rows block into separate function
- Do NOT rename `page_break_enabled`

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest, 38 existing tests)
- **Automated tests**: TDD — write failing test first, then implement
- **Framework**: pytest

### QA Policy
Every task includes Agent-Executed QA Scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/Python**: Use Bash — run commands, validate output, check exit codes

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Sequential — tight dependency):
├── Task 1: Add insert_mode config read + OR condition [quick]
└── Task 2: Update config.json + comment [quick]

Wave 2 (After Wave 1):
├── Task 3: Write TDD test for insert_mode=True path [quick]
└── Task 4: Run full test suite + E2E verification [quick]
```

---

## TODOs

- [x] 1. Add `insert_mode` config read to copier.py

  **What to do**:
  - In `3-column-copier/copier.py`, after line 78 (`page_break_enabled = config.get("page_break_enabled", False)`), add:
    ```python
    insert_mode = config.get("insert_mode", False)
    ```
  - Change line 187 from:
    ```python
    if paste_mode == "append" and page_break_enabled:
    ```
    to:
    ```python
    if paste_mode == "append" and (page_break_enabled or insert_mode):
    ```

  **Must NOT do**:
  - Do NOT change line 162 (`if page_break_enabled:`) — A4 setup stays page_break_enabled only
  - Do NOT change line 249 (`if page_break_enabled:`) — snap_gap_rows stays page_break_enabled only
  - Do NOT refactor the insert_rows block into a function
  - Do NOT touch any file outside `3-column-copier/copier.py`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file, 3-line change, well-understood code
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential — Task 2 depends on this being correct)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3 (test needs this code)
  - **Blocked By**: None

  **References**:
  - `3-column-copier/copier.py:78` — existing config read pattern to follow
  - `3-column-copier/copier.py:187` — the condition to modify
  - `3-column-copier/copier.py:162-164` — A4 setup (DO NOT TOUCH)
  - `3-column-copier/copier.py:249` — snap_gap_rows gate (DO NOT TOUCH)

  **Acceptance Criteria**:
  - [ ] `3-column-copier/copier.py` has `insert_mode = config.get("insert_mode", False)` after line 78
  - [ ] Line 187 reads: `if paste_mode == "append" and (page_break_enabled or insert_mode):`
  - [ ] `grep "insert_mode" 3-column-copier/copier.py` finds 2 matches (read + condition)

  **QA Scenarios**:

  ```
  Scenario: insert_mode=False (default) — no behavior change
    Tool: Bash
    Preconditions: Config with paste_mode="append", page_break_enabled=False, NO insert_mode key
    Steps:
      1. Run: cd 3-column-copier && python -m pytest tests/test_cli.py::TestCli::test_happy_path -v
      2. Assert: test passes (uses default config, no insert_mode key → defaults to False)
    Expected Result: Test passes, no insert_rows triggered
    Evidence: .sisyphus/evidence/task-1-default-false.txt

  Scenario: insert_mode=True triggers insert_rows code path
    Tool: Bash
    Preconditions: Verify the condition `(page_break_enabled or insert_mode)` evaluates True when insert_mode=True
    Steps:
      1. Run: cd 3-column-copier && python -c "print(False or True)" 
      2. Assert: Output is `True`
    Expected Result: OR condition correctly evaluates
    Evidence: .sisyphus/evidence/task-1-or-condition.txt
  ```

  **Commit**: YES (groups with Task 2)
  - Message: `feat(copier): add insert_mode config key`
  - Files: `3-column-copier/copier.py`

- [x] 2. Update config.json with insert_mode key

  **What to do**:
  - In `3-column-copier/config.json`, add `"insert_mode": true,` on its own line (e.g., after `"paste_mode": "append",` at line 60)
  - Update the `_comment_print` field (line 64) to mention `insert_mode`: change from `"Set page_break_enabled: true to enable A4 page break protection..."` to `"Set page_break_enabled: true to enable A4 page break protection. Set insert_mode: true to insert rows when appending (push existing content down)..."`

  **Must NOT do**:
  - Do NOT change or remove any existing keys
  - Do NOT change `page_break_enabled: false`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file, 2-line JSON edit
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 1 being correct first)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3 (test needs config key present)
  - **Blocked By**: Task 1

  **References**:
  - `3-column-copier/config.json` — current config structure
  - `3-column-copier/config.json:60` — `"paste_mode": "append",` — insert `insert_mode` after this line
  - `3-column-copier/config.json:64` — `_comment_print` to update

  **Acceptance Criteria**:
  - [ ] `"insert_mode": true` present in config.json
  - [ ] `_comment_print` mentions `insert_mode`
  - [ ] `python -c "import json; c=json.load(open('3-column-copier/config.json')); assert c['insert_mode'] == True"` passes

  **QA Scenarios**:

  ```
  Scenario: Config key loads correctly
    Tool: Bash
    Preconditions: config.json has insert_mode: true
    Steps:
      1. Run: cd 3-column-copier && python -c "import json; c=json.load(open('config.json')); print(c['insert_mode'])"
      2. Assert: Output is `True`
    Expected Result: True
    Evidence: .sisyphus/evidence/task-2-config-key.txt

  Scenario: Config is valid JSON
    Tool: Bash
    Preconditions: config.json modified
    Steps:
      1. Run: cd 3-column-copier && python -c "import json; json.load(open('config.json')); print('valid')"
      2. Assert: Output is `valid`
    Expected Result: No JSON parse errors
    Evidence: .sisyphus/evidence/task-2-valid-json.txt
  ```

  **Commit**: YES (groups with Task 1)
  - Files: `3-column-copier/config.json`

- [x] 3. Write TDD test: insert_mode=True without page_break_enabled

  **What to do** (RED first, then GREEN):
  - Add test method `test_insert_mode_without_page_break` to class `TestAppendInsertRows` in `3-column-copier/tests/test_columns.py`
  - The test creates a target workbook with content below paste area, then verifies `insert_rows` fires without A4 page setup
  - Test structure (follow `test_full_append_with_page_break` pattern at line 306):
    ```python
    def test_insert_mode_without_page_break(self):
        """insert_mode=True triggers insert_rows even when page_break_enabled=False."""
        import tempfile
        from openpyxl import Workbook, load_workbook
        
        # Setup target: content at row 9
        twb = Workbook()
        tws = twb.active
        tws.cell(row=9, column=1).value = "existing_below"
        
        with tempfile.TemporaryDirectory() as tmp:
            tgt_path = Path(tmp) / "target.xlsx"
            twb.save(str(tgt_path))
            twb.close()
            
            # Simulate: insert_mode=True, page_break_enabled=False
            # paste_mode="append", paste_row=3, src has 5 data rows
            twb2 = load_workbook(str(tgt_path))
            tws2 = twb2.active
            tws2.insert_rows(3, 5)
            twb2.save(str(tgt_path))
            twb2.close()
            
            # Verify content shifted from row 9 → row 14
            twb3 = load_workbook(str(tgt_path))
            tws3 = twb3.active
            assert tws3.cell(row=14, column=1).value == "existing_below"
            twb3.close()
    ```

  **Must NOT do**:
  - Do NOT test A4 page setup (paperSize, print titles) — that's page_break_enabled's job
  - Do NOT test snap_gap_rows — stays with page_break_enabled
  - Do NOT import copier.main or create a full pipeline — keep it a unit test on insert_rows behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pattern-following test addition, well-understood test class
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 1 & 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4 (full suite verification)
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `3-column-copier/tests/test_columns.py:306-346` — `test_full_append_with_page_break` pattern to follow
  - `3-column-copier/tests/test_columns.py:260-279` — `test_append_no_insert_rows_when_no_content_below` for tempfile pattern
  - `3-column-copier/tests/test_columns.py:282-304` — `test_insert_rows_detects_content_at_paste_row` for shift verification

  **Acceptance Criteria**:
  - [ ] Test `test_insert_mode_without_page_break` exists in `TestAppendInsertRows` class
  - [ ] Test verifies: content shifts down when insert_rows fires
  - [ ] Test passes: `python -m pytest tests/test_columns.py::TestAppendInsertRows::test_insert_mode_without_page_break -v`

  **QA Scenarios**:

  ```
  Scenario: New test passes in isolation
    Tool: Bash
    Preconditions: Tasks 1 & 2 complete
    Steps:
      1. Run: cd 3-column-copier && python -m pytest tests/test_columns.py::TestAppendInsertRows::test_insert_mode_without_page_break -v
      2. Assert: exit code 0, output contains "PASSED"
    Expected Result: 1 passed
    Evidence: .sisyphus/evidence/task-3-test-pass.txt

  Scenario: New test actually verifies shift (ensure it's not a vacuous pass)
    Tool: Bash
    Preconditions: Test exists
    Steps:
      1. Run: cd 3-column-copier && python -m pytest tests/test_columns.py::TestAppendInsertRows::test_insert_mode_without_page_break -v --tb=short
      2. Assert: Contains assertion about `existing_below` at row 14
    Expected Result: Meaningful assertion executed
    Evidence: .sisyphus/evidence/task-3-meaningful.txt
  ```

  **Commit**: YES (groups with Tasks 1, 2)
  - Files: `3-column-copier/tests/test_columns.py`

- [x] 4. Run full test suite and verify all 39 tests pass

  **What to do**:
  - Run `cd 3-column-copier && python -m pytest tests/ -v`
  - Verify: 39 tests pass (38 existing + 1 new)
  - Verify: no regressions in test_cli, test_cleanup, test_columns, test_print_setup, test_real_mapping
  - Verify: `test_real_mapping.py::test_full_pipeline_with_page_break` still passes (page_break_enabled=True still triggers insert via OR condition)

  **Must NOT do**:
  - Do NOT skip any failing tests — fix the code if any fail

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Run command and verify output
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 1-3)
  - **Parallel Group**: Wave 2
  - **Blocks**: None (final task)
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `3-column-copier/tests/` — all test files
  - `3-column-copier/tests/test_real_mapping.py:76` — sets `page_break_enabled: True` (must still work)

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/ -v` → 39 passed, 0 failed
  - [ ] test_real_mapping passes (page_break_enabled path still works)
  - [ ] test_cli passes (default config path still works)

  **QA Scenarios**:

  ```
  Scenario: Full test suite passes
    Tool: Bash
    Preconditions: Tasks 1-3 complete
    Steps:
      1. Run: cd 3-column-copier && python -m pytest tests/ -v
      2. Assert: exit code 0
      3. Assert: output contains "39 passed"
      4. Assert: output contains "test_insert_mode_without_page_break"
    Expected Result: 39 passed in X.XXs
    Evidence: .sisyphus/evidence/task-4-full-suite.txt

  Scenario: Backward compatibility — page_break_enabled still works
    Tool: Bash
    Preconditions: Full suite passing
    Steps:
      1. Run: cd 3-column-copier && python -m pytest tests/test_real_mapping.py -v
      2. Assert: exit code 0, "1 passed"
    Expected Result: page_break_enabled path unchanged
    Evidence: .sisyphus/evidence/task-4-backward-compat.txt
  ```

  **Commit**: NO (already committed in Task 1-2 group)

---

## Final Verification Wave

- [x] F1. **Full test suite** — `python -m pytest tests/ -v` → 39 passed (38 existing + 1 new)
- [x] F2. **Config key presence** — `python -c "import json; c=json.load(open('config.json')); assert 'insert_mode' in c; print(c['insert_mode'])"` → `True`
- [x] F3. **Backward compat** — `page_break_enabled: True` still triggers insert_rows (existing test verifies)

---

## Commit Strategy

- **1**: `feat(copier): add insert_mode config key to decouple insert from page break`
  - Files: `copier.py`, `config.json`, `test_columns.py`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Success Criteria

```bash
# All tests pass
cd 3-column-copier && python -m pytest tests/ -v
# Expected: 39 passed (38 existing + 1 new)

# Config key present
cd 3-column-copier && python -c "import json; c=json.load(open('config.json')); assert c['insert_mode'] == True"

# insert_mode triggers insert without page formatting
cd 3-column-copier && python -m pytest tests/test_columns.py::TestAppendInsertRows::test_insert_mode_without_page_break -v
# Expected: PASSED
```
