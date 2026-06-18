# Fix: MergedCell AttributeError in Column Copier

## TL;DR

> **Quick Summary**: Guard `tws.cell(...).value = val` against `MergedCell` objects — skip merged cells during paste instead of crashing.
>
> **Deliverables**:
> - `3-column-copier/copier.py`: `isinstance` guard on line 219 + `MergedCell` import
> - `3-column-copier/tests/test_columns.py`: test for merged cell paste behavior
>
> **Estimated Effort**: Quick (~2 lines changed, 1 test added)
> **Parallel Execution**: NO — sequential
> **Critical Path**: Task 1 → Task 2 → Task 3

---

## Context

### Original Request
User runs tool 3 on another machine and gets:
```
copier.py line 219 in main
tws.cell(row=dst_row, column=dst_idx).value = val
AttributeError: 'MergedCell' object attribute 'value' is read-only
```
The target XLSX has merged cells. `tws.cell()` returns a `MergedCell` which has `.value` as read-only.

### Root Cause
`copier.py:219` unconditionally writes to every cell in the paste range. When a cell is part of a merged range (other than the top-left anchor), openpyxl returns a `MergedCell` object that rejects writes. The code already checks for merged cells before `insert_rows` (lines 180-190) but does NOT check at the paste point.

### Agreed Approach
Skip merged cells during paste — leave them intact, write to non-merged cells normally.

---

## Work Objectives

### Core Objective
Prevent `AttributeError` crash when pasting into sheets that contain merged cells.

### Concrete Deliverables
- `3-column-copier/copier.py`: import `MergedCell`, guard line 219
- `3-column-copier/tests/test_columns.py`: test verifying merged cells are skipped

### Definition of Done
- [ ] Paste loop skips merged cells without crashing
- [ ] Non-merged cells still written normally
- [ ] `python -m pytest 3-column-copier/tests/ -v` → all 37+ pass (no regressions)

### Must Have
- `isinstance` check against `MergedCell` before writing
- Existing paste behavior unchanged for sheets without merged cells

### Must NOT Have
- Do NOT unmerge cells — leave merged ranges intact
- Do NOT change the `insert_rows` merged cell logic (lines 180-190)
- Do NOT change any other paste logic

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest 9.0.3)
- **Automated tests**: Tests-after
- **Framework**: pytest (plain `assert`, `Workbook()` fixtures)

---

## Execution Strategy

```
Wave 1 (sequential):
├── Task 1: Add import + isinstance guard to copier.py
├── Task 2: Add test for merged cell paste
└── Task 3: Full test suite verification
```

---

## TODOs

- [x] 1. Guard paste against MergedCell in copier.py

  **What to do**:
  - Add import: `from openpyxl.cell.cell import MergedCell` after line 9
  - Guard line 219:
    ```python
    # Before:
    tws.cell(row=dst_row, column=dst_idx).value = val
    
    # After:
    cell = tws.cell(row=dst_row, column=dst_idx)
    if not isinstance(cell, MergedCell):
        cell.value = val
    ```

  **Must NOT do**:
  - Do NOT change the `insert_rows` merged cell check (lines 180-190)
  - Do NOT unmerge cells

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Two surgical edits, well-defined target

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  - `3-column-copier/copier.py:9` — existing openpyxl import
  - `3-column-copier/copier.py:217-221` — paste loop to guard
  - `3-column-copier/copier.py:180-190` — existing merged cell check (for context)

  **Acceptance Criteria**:
  - [ ] `MergedCell` imported from openpyxl
  - [ ] Line 219 guarded with `isinstance` check
  - [ ] Normal paste (no merged cells) behavior unchanged
  - [ ] Paste into sheet with merged cells skips them, no crash

  **QA Scenarios**:

  ```
  Scenario: Normal paste still works (no merged cells)
    Tool: Bash (PowerShell)
    Preconditions: Fix applied
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_columns.py::TestPasteDirect::test_paste_direct_source_to_target -v
    Expected Result: 1 passed
    Evidence: .sisyphus/evidence/merge-task-1-normal.txt
  ```

  ```
  Scenario: Paste into merged cell sheet does not crash
    Tool: Bash (PowerShell)
    Preconditions: Fix applied
    Steps:
      1. cd 3-column-copier
      2. python -c "from openpyxl import Workbook; from openpyxl.cell.cell import MergedCell; wb = Workbook(); ws = wb.active; ws.merge_cells('A1:B1'); ws['A1'] = 'merged header'; ws['A2'] = 'data'; from src.columns import col_letter_to_index; tws = wb.active; swb = Workbook(); sws = swb.active; sws['C2'] = 'source_val'; dst_row = 1; val = sws.cell(row=2, column=3).value; cell = tws.cell(row=dst_row, column=2); print('MergedCell' if isinstance(cell, MergedCell) else 'NormalCell'); wb.close(); swb.close()"
    Expected Result: Prints "MergedCell" (B1 is part of A1:B1 merge), no crash
    Evidence: .sisyphus/evidence/merge-task-1-merged.txt
  ```

  **Commit**: YES
  - Message: `fix(3-column-copier): skip merged cells during paste to prevent AttributeError`
  - Files: `3-column-copier/copier.py`
  - Pre-commit: `cd 3-column-copier && python -m pytest tests/ -v`

- [x] 2. Add test for merged cell paste

  **What to do**:
  - Add test method to `TestPasteDirect` or new test class in `test_columns.py`
  - Creates a target sheet with merged cells, pastes into it, verifies no crash and merged cell value preserved
  - Test structure:
    ```python
    def test_paste_skips_merged_cells(self):
        """Pasting into merged cells should skip them, not crash."""
        from openpyxl import Workbook
        from openpyxl.cell.cell import MergedCell
        
        # Target with merged cells
        twb = Workbook()
        tws = twb.active
        tws.merge_cells('B2:C2')
        tws['B2'] = 'merged content'
        tws['A1'] = 'header'
        tws['A2'] = 'data below merge'
        
        # Verify B2 (top-left of merge) is writable, C2 (part of merge) is MergedCell
        cell_c2 = tws.cell(row=2, column=3)
        assert isinstance(cell_c2, MergedCell), "C2 should be a MergedCell"
        
        # Write attempt should be guarded
        if not isinstance(cell_c2, MergedCell):
            cell_c2.value = "should not reach here"
        
        assert tws['B2'].value == 'merged content'  # merged cell untouched
        twb.close()
    ```

  **Must NOT do**:
  - Do NOT modify existing test cases
  - Do NOT change source code — only tests

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Add one test following existing patterns

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - `3-column-copier/tests/test_columns.py:22-28` — `TestPasteDirect.test_paste_direct_source_to_target` pattern
  - `3-column-copier/copier.py:9` — MergedCell import location

  **Acceptance Criteria**:
  - [ ] Test verifies MergedCell is detected and skipped
  - [ ] `python -m pytest tests/test_columns.py -v -k "merged"` → passes

  **Commit**: YES (groups with Task 1 commit)
  - Files: `3-column-copier/tests/test_columns.py`

- [x] 3. Full test suite verification

  **What to do**:
  - Run `cd 3-column-copier && python -m pytest tests/ -v`
  - All 38+ tests pass (37 existing + new)

  **Must NOT do**:
  - Do NOT skip any test file

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: FINAL
  - **Blocked By**: Task 2

  **Acceptance Criteria**:
  - [ ] All tests pass, zero regressions

  **Commit**: NO (verification only)

---

## Final Verification Wave

- [x] F1. **Full tool 3 test suite** — all tests pass
  ```bash
  cd 3-column-copier && python -m pytest tests/ -v
  ```
  Output: `All [N/N] pass | VERDICT`

---

## Commit Strategy

- **1**: `fix(3-column-copier): skip merged cells during paste` — copier.py, test_columns.py

---

## Success Criteria

### Verification Commands
```bash
cd 3-column-copier && python -m pytest tests/ -v    # Expected: 38+ passed
```

### Final Checklist
- [ ] Paste skips merged cells without crashing
- [ ] Normal paste unchanged
- [ ] All existing tests pass
