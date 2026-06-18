# Fix PW Fill Range + Auto-Cleanup Temp Columns

## TL;DR

> **Quick Summary**: Fix two bugs in tool 3: (1) PW fills all rows instead of stopping at NE_NO data end, (2) build_at temp columns (Q,R,S) stay permanently in source files.
>
> **Deliverables**:
> - Modified `columns.py`: `build_pw_column` accepts `lookup_col` parameter, stops at NE_NO end
> - Modified `copier.py`: passes lookup col to PW build, auto-deletes Q,R,S after copy
> - New test source file: `multi-record-source.xlsx` with cutsheet + log sheet, 15+ records
> - Tests for both fixes
>
> **Estimated Effort**: Medium (1 source file, 3 code changes, 2 test additions)
> **Parallel Execution**: YES — 2 waves
> **Critical Path**: File creation → Code fixes → Tests → Verification

---

## Context

User wants PW column to only fill rows where NE_NO/IP data exists, not all rows. Also wants temp columns deleted from source after copy so they don't accumulate. User explicitly wants crash (not silent skip) when log sheet is missing.

---

## Work Objectives

### Core Objective
PW fill range tied to NE_NO data end; temp columns auto-cleaned after copy.

### Concrete Deliverables
- `3-column-copier/src/columns.py`: `build_pw_column` with lookup_col parameter
- `3-column-copier/copier.py`: pass lookup col, auto-delete build_at cols after copy
- `3-column-copier/source/multi-record-source.xlsx`: test file with 15+ records
- Tests for PW fill range and cleanup

### Definition of Done
- [ ] PW fills only rows where NE_NO data exists
- [ ] Q,R,S columns deleted from source after copy completes
- [ ] All existing 38 tests still pass
- [ ] New tests verify both fixes
- [ ] Test file has 15+ records with matching log sheet entries

### Must Have
- PW column tied to NE_NO column data range
- Temp columns deleted right-to-left (S→R→Q) to avoid index shift
- Source files restored to original state after copy

### Must NOT Have
- Do NOT silently skip missing log sheet — crash is correct
- Do NOT change paste loop behavior
- Do NOT delete original source columns (only build_at columns Q,R,S)

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: Tests-after
- **Framework**: pytest

---

## Execution Strategy

```
Wave 1 (independent - can run in parallel):
├── Task 1: Create multi-record test source file [quick]
├── Task 2: Modify build_pw_column to accept lookup_col [quick]
└── Task 3: Add auto-cleanup + pass lookup_col in copier.py [quick]

Wave 2 (after Wave 1):
├── Task 4: Add test for PW fill range [quick]
├── Task 5: Add test for auto-cleanup [quick]
└── Task 6: Full test suite verification [quick]
```

---

## TODOs

- [x] 1. Create multi-record test source file

- [x] 2. Modify `build_pw_column` to accept `lookup_col`

- [x] 3. Auto-cleanup + pass lookup_col in copier.py

- [x] 4. Add test for PW fill range

- [x] 5. Add test for auto-cleanup

- [x] 6. Full test suite verification (38+ new tests pass)

---

## Final Verification Wave

- [x] F1. **Full tool 3 test suite** — all tests pass

---

## Commit Strategy

- **1**: `fix(3-column-copier): tie PW fill range to NE_NO data end` — columns.py, copier.py
- **2**: `fix(3-column-copier): auto-cleanup build_at columns after copy` — copier.py
- **3**: `test(3-column-copier): add multi-record test fixture` — source/multi-record-source.xlsx

---

## Success Criteria

```bash
cd 3-column-copier && python -m pytest tests/ -v    # Expected: 40+ passed
```
