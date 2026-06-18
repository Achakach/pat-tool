# Simplify Insert Logic

## TL;DR

> **Quick Summary**: Remove conflicting append-scan and merged-cell-skip logic. Always insert rows at `paste_start_row` from config. `insert_mode: true` = insert + paste; `insert_mode: false` = paste without insert.
>
> **Deliverables**:
> - `copier.py`: Remove blank scan, merged check, `paste_mode`; simplify insert gate to `insert_mode` only
> - `config.json`: Remove `paste_mode` key
> - 3 test configs: Remove `paste_mode`
> - 2 new tests: insert with content at paste row, no-insert mode
>
> **Estimated Effort**: Medium (code removal + test updates)
> **Parallel Execution**: NO — sequential dependency chain
> **Critical Path**: copier.py → config.json → tests → full suite

---

## Context

### Original Request
User wants simpler behavior: always insert at the configured `paste_start_row`, push everything down. No scanning for blank rows. No merged cell skipping.

### Current Problem (3 conflicting logics)
```
1. Append scan:    finds first blank row → paste_row
2. Insert mode:    inserts rows at paste_row → pushes content down
3. Merged check:   if merged cells → WARNING + skip insert (silent failure)
```
These don't work well together. The merged cell check silently kills the insert. The blank scan makes paste position unpredictable.

### Metis Review
**Key findings**:
- Removing merged cell check is **safe** — openpyxl ≥3.0 handles insert_rows across merged ranges natively
- `paste_mode` config is redundant with `insert_mode` — remove it
- Zero data loss risk — content shifts, never overwritten
- Only 3 test configs need updating
- Need 2 new tests for the simplified behavior

---

## Work Objectives

### Core Objective
Replace 3-stage scan/check/insert with single predictable behavior: always insert at configured `paste_start_row`.

### Concrete Deliverables
- `copier.py`: ~30 lines removed, gate simplified
- `config.json`: remove `paste_mode`
- 3 test files: update configs
- 2 new tests added

### Definition of Done
- [ ] `insert_mode: true` → insert at paste_start_row, paste data, content shifts down
- [ ] `insert_mode: false` → paste at paste_start_row, no insert (overwrite behavior)
- [ ] Multi-source: each source inserts at same row, last-processed on top
- [ ] No blank row scanning
- [ ] No merged cell skip
- [ ] All existing tests pass (with updated configs) + 2 new tests

### Must Have
- Simple gate: `if insert_mode:` only (line 189)
- Remove `paste_mode` config key
- Keep paste-loop MergedCell guard (line 242)
- Keep page break snap logic (lines 251-255)

### Must NOT Have (Guardrails)
- Do NOT remove paste-loop MergedCell guard (line 242) — different concern
- Do NOT change page break snap (lines 251-255)
- Do NOT change source row counting (lines 191-199)
- Do NOT change column pasting logic
- Do NOT touch `5-png-inserter/` or other tools
- Do NOT rename `insert_mode`

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest, 39 tests)
- **Automated tests**: Tests-after (update configs first, add new tests, verify)
- **Framework**: pytest

### QA Policy
Every task includes Agent-Executed QA Scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

---

## Execution Strategy

```
Wave 1 (copier.py changes):
├── Task 1: Remove blank scan, merged check, paste_mode read [quick]
└── Task 2: Simplify insert gate + dst_row logic [quick]

Wave 2 (config + test updates):
├── Task 3: Update config.json (remove paste_mode) [quick]
├── Task 4: Update test configs (3 files) [quick]
└── Task 5: Add 2 new tests [quick]

Wave 3 (verification):
└── Task 6: Run full test suite — all pass [quick]
```

---

## TODOs

- [x] 1. Remove blank scan, merged check, and paste_mode from copier.py

  **What to do**:
  - Remove `paste_mode = config.get("paste_mode", "overwrite")` line (currently ~line 72)
  - Remove blank row scanning block (lines 174-186): the entire `if paste_mode == "append": ... paste_row = actual_row` block
  - Remove merged cell check + WARNING block (lines 201-210): the `has_merged` / WARNING / skip insert_rows logic
  - After removal, `paste_row` always equals `config["paste_start_row"]` (the configured value)

  **Must NOT do**:
  - Do NOT remove the paste-loop MergedCell guard (currently ~line 242, `if not isinstance(cell, MergedCell)`)
  - Do NOT change source row counting (lines 191-199)
  - Do NOT change page break snap logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 1 | **Blocks**: Task 2 | **Blocked By**: None

  **References**:
  - `3-column-copier/copier.py:72` — paste_mode read (remove)
  - `3-column-copier/copier.py:174-186` — blank scan (remove)
  - `3-column-copier/copier.py:201-210` — merged check (remove)
  - `3-column-copier/copier.py:242` — MergedCell guard (KEEP)

  **Acceptance Criteria**:
  - [ ] `grep "paste_mode" 3-column-copier/copier.py` → 0 matches
  - [ ] `grep "blank row\|first blank\|actual_row < max_row_check" 3-column-copier/copier.py` → 0 matches
  - [ ] `grep "has_merged\|WARNING.*Merged" 3-column-copier/copier.py` → 0 matches
  - [ ] `paste_row` assignment line references `config["paste_start_row"]` only

  **QA Scenarios**:
  ```
  Scenario: paste_mode removed from code
    Tool: Bash
    Steps:
      1. grep paste_mode 3-column-copier/copier.py
      2. Assert: no matches
    Evidence: .sisyphus/evidence/task-1-paste-mode-gone.txt
  ```

  **Commit**: YES (groups with Task 2)

- [x] 2. Simplify insert gate and dst_row logic

  **What to do**:
  - Change line 189 from: `if paste_mode == "append" and (page_break_enabled or insert_mode):` to: `if insert_mode:`
  - Change line ~230 from: `dst_row = paste_row if paste_mode == "append" else min(start_row, paste_row)` to: `dst_row = paste_row`
  - Ensure `insert_mode` default is `False` via `.get("insert_mode", False)`

  **Must NOT do**:
  - Do NOT change `page_break_enabled` usage elsewhere
  - Do NOT remove `insert_mode` config read

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 1 | **Blocks**: Tasks 3-5 | **Blocked By**: Task 1

  **References**:
  - `3-column-copier/copier.py:80` — insert_mode config read
  - `3-column-copier/copier.py:189` — insert gate to simplify
  - `3-column-copier/copier.py:230` — dst_row logic to simplify

  **Acceptance Criteria**:
  - [ ] Line 189 reads: `if insert_mode:`
  - [ ] `dst_row` assignment is simply: `dst_row = paste_row`
  - [ ] `insert_mode` defaults to `False` when key missing

  **QA Scenarios**:
  ```
  Scenario: insert_mode gate is clean
    Tool: Bash
    Steps:
      1. grep "if insert_mode:" 3-column-copier/copier.py
      2. Assert: exactly 1 match (the gate), not nested in other conditions
    Evidence: .sisyphus/evidence/task-2-clean-gate.txt
  ```

  **Commit**: YES (groups with Task 1)

- [x] 3. Update config.json — remove paste_mode

  **What to do**:
  - Remove `"paste_mode": "append",` from `3-column-copier/config.json`
  - Keep `"insert_mode": true` as the sole mode control
  - Update `_comment_print` to reflect simplified config

  **Must NOT do**:
  - Do NOT remove `insert_mode`
  - Do NOT change any other keys

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 2 | **Blocks**: Task 6 | **Blocked By**: Tasks 1, 2

  **Acceptance Criteria**:
  - [ ] `"paste_mode"` not in config.json
  - [ ] `"insert_mode": true` present
  - [ ] Valid JSON

  **QA Scenarios**:
  ```
  Scenario: Config is valid and paste_mode absent
    Tool: Bash
    Steps:
      1. python -c "import json; c=json.load(open('config.json')); assert 'paste_mode' not in c; assert c['insert_mode'] == True; print('OK')"
      2. Assert: "OK"
    Evidence: .sisyphus/evidence/task-3-config-clean.txt
  ```

  **Commit**: YES (groups with Tasks 1-2)

- [x] 4. Update test configs — remove paste_mode from 3 test files

  **What to do**:
  - `test_cli.py`: Remove `"paste_mode": "overwrite"` from 2 test configs (lines ~75, ~152). Add `"insert_mode": False` explicitly or let default.
  - `test_real_mapping.py`: Remove `"paste_mode": "append"` (line ~75). Add `"insert_mode": True`.
  - `test_pipeline_e2e.py`: Remove `"paste_mode": "append"` (line ~191). Let `insert_mode` default to `False` (Stage 3 just needs file creation, no insert).

  **Must NOT do**:
  - Do NOT change test assertions
  - Do NOT change other config keys

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 2 | **Blocks**: Task 6 | **Blocked By**: Tasks 1, 2 | **Can run parallel with Task 3, 5**

  **Acceptance Criteria**:
  - [ ] `grep "paste_mode" 3-column-copier/tests/` → 0 matches
  - [ ] test_real_mapping has `"insert_mode": True`
  - [ ] test_cli has no paste_mode (default insert_mode=False)

  **QA Scenarios**:
  ```
  Scenario: No paste_mode in any test config
    Tool: Bash
    Steps:
      1. grep -r paste_mode 3-column-copier/tests/
      2. Assert: no matches
    Evidence: .sisyphus/evidence/task-4-no-paste-mode.txt
  ```

  **Commit**: YES (groups with Tasks 1-3)

- [x] 5. Add 2 new tests for simplified behavior

  **What to do**:
  - **Test A**: `test_insert_mode_shifts_content_at_paste_row` — target has content AT paste_start_row, insert_mode=true shifts it down
  - **Test B**: `test_no_insert_mode_leaves_content_in_place` — insert_mode=false, paste at paste_start_row without insert

  **Must NOT do**:
  - Do NOT test for merged cell behavior
  - Do NOT test page break behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 2 | **Blocks**: Task 6 | **Blocked By**: Tasks 1, 2 | **Can run parallel with Task 3, 4**

  **References**:
  - `3-column-copier/tests/test_columns.py:348-374` — test_insert_mode_without_page_break pattern

  **Acceptance Criteria**:
  - [ ] Both new tests pass in isolation
  - [ ] Full suite: existing + 2 new = all pass

  **QA Scenarios**:
  ```
  Scenario: Content at paste_start_row shifts with insert_mode=true
    Tool: Bash
    Steps:
      1. cd 3-column-copier && python -m pytest tests/test_columns.py::TestAppendInsertRows::test_insert_mode_shifts_content_at_paste_row -v
      2. Assert: PASSED
    Evidence: .sisyphus/evidence/task-5-shift-test.txt
  ```

  **Commit**: YES (groups with Tasks 1-4)

- [x] 6. Run full test suite — all pass

  **What to do**:
  - `cd 3-column-copier && python -m pytest tests/ -v`
  - Verify all tests pass (existing + new)
  - Verify test_real_mapping still passes
  - Verify test_cli still passes

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**: Wave 3 | **Blocked By**: Tasks 1-5

  **Acceptance Criteria**:
  - [ ] All tests pass, 0 failures

  **QA Scenarios**:
  ```
  Scenario: Full test suite
    Tool: Bash
    Steps:
      1. cd 3-column-copier && python -m pytest tests/ -v
      2. Assert: exit 0, all passed
    Evidence: .sisyphus/evidence/task-6-full-suite.txt
  ```

  **Commit**: NO (committed with tasks 1-5)

---

## Final Verification Wave

- [x] F1. **Full test suite** — `python -m pytest tests/ -v` → all pass (existing + new)
- [x] F2. **Multi-source integration** — 3 sources → one output, data accumulated
- [x] F3. **Push-down verified** — content at paste_start_row shifts down with insert_mode

---

## Commit Strategy

- **1**: `refactor(copier): simplify insert logic — remove blank scan, merged check, paste_mode`
  - Files: `copier.py`, `config.json`, `test_cli.py`, `test_real_mapping.py`, `test_columns.py`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Success Criteria

```bash
# All tests pass
cd 3-column-copier && python -m pytest tests/ -v
# Expected: all pass

# insert_mode: true pushes content
cd 3-column-copier && python -c "
from copier import main
# ... test insert_mode: true shifts content at paste_start_row
"

# insert_mode: false does not insert
cd 3-column-copier && python -c "
from copier import main
# ... test insert_mode: false leaves content in place
"
```
