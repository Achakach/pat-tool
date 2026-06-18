# Fix: IP Lookup Regex — Handle Wrapped Log Sheet Values

## TL;DR

> **Quick Summary**: Replace naive `split("_", 1)` in `build_ip_column` with a regex that finds the `NE_NO_IP` pattern embedded within noisy strings like `new_100_10.0.0.1(MXaxxxx)`.
>
> **Deliverables**:
> - `3-column-copier/src/columns.py`: regex-based IP extraction in `build_ip_column`
> - `3-column-copier/tests/test_columns.py`: test cases for wrapped/noisy formats
>
> **Estimated Effort**: Quick (~1 function changed, ~3 test cases added)
> **Parallel Execution**: NO — single file, sequential
> **Critical Path**: Task 1 → Task 2 → Task 3

---

## Context

### Original Request
User reports that IP lookup in "Get Log Before&After" sheet fails when log values have extra wrapping, e.g., `new_100_10.0.0.1(MXaxxxx)` instead of clean `100_10.0.0.1`. The current `split("_", 1)` splits on the first underscore, yielding wrong results.

### Root Cause
`columns.py:38-40`:
```python
if "_" in text:
    prefix, ip = text.split("_", 1)  # ❌ splits on first _, breaks on wrapped values
    ip_map[prefix.strip()] = ip.strip()
```

For `new_100_10.0.0.1(MXaxxxx)`, `split("_", 1)` gives `prefix="new"`, `ip="100_10.0.0.1(MXaxxxx)"` — completely wrong.

### Agreed Approach
Use regex to find the `NE_NO_IP` pattern **embedded** in the string:
```python
match = re.search(r'([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
```
This naturally skips head noise (word_ prefixes) and tail noise (anything after IP).

---

## Work Objectives

### Core Objective
Make `build_ip_column` robust against wrapped/noisy log sheet values by using regex pattern matching instead of naive string splitting.

### Concrete Deliverables
- `3-column-copier/src/columns.py`: lines 35-40 replaced with regex approach
- `3-column-copier/tests/test_columns.py`: new parametrized test for wrapped formats

### Definition of Done
- [ ] `python -m pytest 3-column-copier/tests/test_columns.py -v` → all tests pass
- [ ] Wrapped formats (`new_100_10.0.0.1(MXaxxxx)`, `exist_CR10SDA_10.10.10.10_backup`) resolve correctly

### Must Have
- Regex that finds `NE_NO_IP` pattern anywhere in the cell value
- Backward compatibility: clean formats still work (`100_10.0.0.1`, `CR10SDA_10.10.10.10`)
- Multiple wrapped prefixes handled (`old_new_100_10.0.0.1`)

### Must NOT Have
- Do NOT change the IP map lookup logic (rows 42-56)
- Do NOT change config.json or add config options
- Do NOT affect other tools

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
├── Task 1: Fix build_ip_column regex
├── Task 2: Add regression tests for wrapped formats
└── Task 3: Run full test suite verification
```

---

## TODOs

- [x] 1. Fix `build_ip_column` regex in columns.py

  **What to do**:
  - Replace lines 35-40 in `3-column-copier/src/columns.py`:
    ```python
    # Before:
    ip_map = {}
    for cell in log_sheet[1]:
        if cell.value:
            text = str(cell.value)
            if "_" in text:
                prefix, ip = text.split("_", 1)
                ip_map[prefix.strip()] = ip.strip()
    
    # After:
    ip_map = {}
    for cell in log_sheet[1]:
        if cell.value:
            text = str(cell.value)
            match = re.search(r'([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
            if match:
                ip_map[match.group(1).strip()] = match.group(2).strip()
    ```
  - The regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` captures:
    - Group 1: NE_NO (any non-underscore chars before the IP) — naturally skips head `word_` prefixes
    - Group 2: IPv4 address — anchors the match, naturally truncates tail noise

  **Must NOT do**:
  - Do NOT change the loop structure or IP map lookup logic (rows 42-56)
  - Do NOT add config options

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Surgical regex replacement, well-defined target

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  - `3-column-copier/src/columns.py:29-56` — full `build_ip_column` function
  - `3-column-copier/src/columns.py:1` — `import re` already present at top of file

  **Acceptance Criteria**:
  - [ ] Regex replaces `split("_", 1)` logic in lines 35-40
  - [ ] `import re` is at top of file (already present)
  - [ ] Clean format `CR10SDA_10.10.10.10` still works (existing test passes)

  **QA Scenarios**:

  ```
  Scenario: Clean format still resolves correctly (backward compat)
    Tool: Bash (PowerShell)
    Preconditions: Fix applied to columns.py
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_columns.py::TestIpColumn::test_lookup -v
    Expected Result: 1 passed — existing test still passes
    Evidence: .sisyphus/evidence/ip-task-1-backward-compat.txt
  ```

  ```
  Scenario: Wrapped format resolves via regex
    Tool: Bash (PowerShell)
    Preconditions: Fix applied to columns.py
    Steps:
      1. cd 3-column-copier
      2. python -c "from openpyxl import Workbook; from src.columns import build_ip_column; wb = Workbook(); ws = wb.active; ws['A2'] = '100'; log = wb.create_sheet('Log'); log['A1'] = 'new_100_10.0.0.1(MXaxxxx)'; build_ip_column(ws, 'A', log, 'B', 2); print('Result:', ws['B2'].value); wb.close()"
    Expected Result: Prints "Result: 10.0.0.1"
    Failure Indicators: Prints wrong value or empty
    Evidence: .sisyphus/evidence/ip-task-1-wrapped.txt
  ```

  **Commit**: YES
  - Message: `fix(3-column-copier): use regex for IP lookup to handle wrapped log values`
  - Files: `3-column-copier/src/columns.py`
  - Pre-commit: `cd 3-column-copier && python -m pytest tests/test_columns.py -v`

- [x] 2. Add regression tests for wrapped/noisy formats

  **What to do**:
  - Add new test method `test_lookup_wrapped_formats` to `TestIpColumn` class in `test_columns.py`
  - Use `@pytest.mark.parametrize` to test multiple wrapped patterns:
    - `new_100_10.0.0.1(MXaxxxx)` → IP `10.0.0.1` matched to NE_NO `100`
    - `exist_CR10SDA_10.10.10.10_backup` → IP `10.10.10.10` matched to NE_NO `CR10SDA`
    - `old_new_200_192.168.1.5_v2` → IP `192.168.1.5` matched to NE_NO `200`
    - `prefix_300_10.20.30.40(suffix)` → IP `10.20.30.40` matched to NE_NO `300`

  **Must NOT do**:
  - Do NOT modify the existing `test_lookup` test
  - Do NOT test edge cases that can't happen (e.g., no IP at all — that's covered by the `if match:` guard)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Add parametrized test following existing test patterns

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - `3-column-copier/tests/test_columns.py:31-45` — existing `TestIpColumn.test_lookup` test pattern
  - `3-column-copier/tests/test_columns.py:12-15` — existing `@pytest.mark.parametrize` usage pattern

  **Acceptance Criteria**:
  - [ ] New test `test_lookup_wrapped_formats` with 4 parametrized cases
  - [ ] All parametrized cases pass
  - [ ] Existing `test_lookup` still passes

  **QA Scenarios**:

  ```
  Scenario: All wrapped format tests pass
    Tool: Bash (PowerShell)
    Preconditions: Task 1 fix applied, new test added
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_columns.py::TestIpColumn -v
    Expected Result: 2 tests collected (test_lookup + test_lookup_wrapped_formats), both pass. Parametrized shows 4 sub-tests passed.
    Evidence: .sisyphus/evidence/ip-task-2-tests.txt
  ```

  **Commit**: YES (groups with Task 1 commit)
  - Files: `3-column-copier/tests/test_columns.py`

- [x] 3. Full test suite verification

  **What to do**:
  - Run tool 3's full test suite to confirm no regressions
  - All existing column copier tests must still pass

  **Must NOT do**:
  - Do NOT skip any test file

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`
  - **Reason**: Run commands and verify

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: FINAL
  - **Blocks**: None
  - **Blocked By**: Task 2

  **Acceptance Criteria**:
  - [ ] `cd 3-column-copier && python -m pytest tests/ -v` → all 31 tests pass (no regressions from existing + new test)

  **QA Scenarios**:

  ```
  Scenario: Full tool 3 test suite passes
    Tool: Bash (PowerShell)
    Preconditions: Tasks 1-2 complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/ -v --tb=short
    Expected Result: All tests pass (31 + new parametrized = 32 collected), exit 0
    Evidence: .sisyphus/evidence/ip-task-3-full-suite.txt
  ```

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

- **1**: `fix(3-column-copier): use regex for IP lookup to handle wrapped log values` — columns.py, test_columns.py

---

## Success Criteria

### Verification Commands
```bash
cd 3-column-copier && python -m pytest tests/test_columns.py::TestIpColumn -v  # 2 tests + 4 parametrized
cd 3-column-copier && python -m pytest tests/ -v                              # all 32 pass
```

### Final Checklist
- [ ] Wrapped formats resolve correctly
- [ ] Clean formats still work (backward compatible)
- [ ] All existing tests pass
- [ ] No config changes needed
