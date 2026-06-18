# Add Debug Logging for MergedCell Investigation

## TL;DR

> **Quick Summary**: Add `print()` debug statements to copier.py so the user can see exactly which file, sheet, and cell causes the MergedCell crash on the production machine.
>
> **Deliverables**:
> - Debug output showing: file name, sheet name, paste row/column, whether MergedCell detected
>
> **Estimated Effort**: Quick (3-4 print statements)

---

## Context

User confirmed no merged cells in local test files, but the crash happens on another machine with different data. Need to add diagnostic output so when the tool runs, it logs exactly what's happening — which file, which sheet, which cell triggered the merged-cell guard.

---

## Work Objectives

Add debug prints to copier.py so the user can run it on the crashing machine and send back the output.

---

## TODOs

- [x] 1. Add debug output at paste loop start — log file + sheet being processed

- [x] 2. Add debug output inside the MergedCell guard — log when a MergedCell is detected and skipped at the paste point (row, column, file, sheet)

- [x] 3. Add debug output at the existing merged cell check (lines 180-190) — log when merged cells are detected during insert_rows scan

- [x] 4. Run local tests to confirm debug output doesn't break anything

---

## Success Criteria

- [ ] User can run tool 3 on crashing machine, send back output showing exactly what was happening
- [ ] All existing 38 tests still pass
