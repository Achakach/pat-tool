# Fix: Multi-Source Append to One Target

## TL;DR

> **Quick Summary**: When multiple source files map to the same target, the copier should append data into a single growing output file instead of overwriting it.
>
> **Deliverables**:
> - Modified `copier.py`: checks if output file already exists, loads that as target instead of fresh template
>
> **Estimated Effort**: Quick (1 code change ~5 lines)
> **Critical Path**: Single task → verify

---

## Context

Currently each source file loads the clean template from `target_folder/` and saves to `output_folder/`. If 3 sources map to `e2e_v3_target.xlsx`, the last one overwrites the previous two. Need to accumulate: first file creates output, second and third append to it.

---

## Work Objectives

### Core Objective
Multiple sources appending into one output file — each source's data appears sequentially in the target.

### Concrete Deliverables
- `3-column-copier/copier.py`: line ~136 — before loading target, check if output already exists

### Definition of Done
- [ ] Running E2E004, E2E005, E2E003 in sequence produces 29 rows (8+5+16) in one output
- [ ] First run (no output yet) uses template from target_folder
- [ ] Subsequent runs load existing output and append
- [ ] All 38 tests still pass

### Must Have
- Output accumulates across source files targeting same file
- Template used only when output doesn't exist yet

### Must NOT Have
- Do NOT change append mode behavior
- Do NOT break 1:1 source→target cases
- Do NOT change how temp columns are cleaned

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: Tests-after
- **Framework**: pytest

---

## Execution Strategy

```
Wave 1:
├── Task 1: Modify target loading to prefer existing output [quick]
└── Task 2: Verify with 3-source test [quick]
```

---

## TODOs

- [x] 1. Load existing output as target if it exists

- [x] 2. Run multi-source test and verify append

- [x] 3. Full test suite verification

---

## Final Verification Wave

- [x] F1. **Full tool 3 test suite** — all tests pass

---

## Success Criteria

```bash
cd 3-column-copier && python copier.py
# Output should have rows from all 3 sources (29 total)
```
