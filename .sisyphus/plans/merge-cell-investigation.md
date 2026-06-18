# Investigate: MergedCell Error Without Obvious Merged Cells

## TL;DR

> **Quick Summary**: User confirms no visible merged cells in the sheet, yet got `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Need to scan the actual file that crashed to find the hidden merge.
>
> **Deliverables**:
> - Diagnostic script that scans an XLSX for all merged cells (even hidden ones)
> - Root cause determination
>
> **Estimated Effort**: Quick (1 script, 1 scan)

---

## Context

User got `MergedCell` crash at `copier.py:219` but visually confirms the target sheet has no merged cells. The `MergedCell` error can only come from openpyxl encountering a merge — so a merge MUST exist somewhere in that file. It may be:
- A merged cell in a different sheet that was loaded as the target
- A merged cell at row/column intersection not noticed visually
- A merged cell in the template that carries over
- An issue with `insert_rows` triggering merge re-check

---

## Work Objectives

Find the exact merged cell(s) in the crashing XLSX file, and explain why it caused the crash.

---

## TODOs

- [ ] 1. Write diagnostic script to scan XLSX for merged cells
  - Script: `find-merged-cells.py` — accepts XLSX path, prints all merged ranges per sheet
  - Output: sheet name, merge range, row/col boundaries for every merge found

- [ ] 2. Run the script on the file that crashed
  - User runs: `python find-merged-cells.py <path-to-crashing-file>`
  - Report findings — all merged ranges found

- [ ] 3. Determine root cause
  - Map the merged ranges to the paste logic in copier.py
  - Identify which merge range overlaps with the paste target column/row
  - Explain why the crash happened at line 219

---

## Success Criteria

- [ ] Exact merge range(s) in the file identified
- [ ] Explanation of why it caused the crash at line 219
- [ ] User understands the root cause
