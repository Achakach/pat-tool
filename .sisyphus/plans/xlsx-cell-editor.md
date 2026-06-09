# XLSX Cell Text Editor

## TL;DR

> **Quick Summary**: Batch tool that scans all cells in XLSX files for prefix matches and replaces them. Config is a simple key-value JSON map. Outputs edited copies — originals untouched.
>
> **Deliverables**:
> - `cell-editor/edit.py` — main CLI script
> - `cell-editor/config.json` — prefix→replacement rules
> - `cell-editor/src/` — library modules
> - `cell-editor/tests/` — pytest tests
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 2 waves

---

## Context

### Original Request
User wants to edit cell text in XLSX files before running the PNG extractor. Labels like "name:" should become "name: kacha thanaphithak". Cells can be in any position — same cell, merged cells, different columns — so the tool scans every cell.

### Interview Summary
- **Match type**: Prefix — cell starts with key → entire cell replaced with value
- **Batch mode**: Process all .xlsx in input folder
- **Output**: Copies saved to output folder, originals untouched
- **Config**: Simple key-value JSON map `{"find_prefix": "replacement_text"}`
- **Folder**: `cell-editor/` — separate from the PNG extractor

### Merged Cells
openpyxl handles merged cells naturally — only the top-left cell of a merge range has a value. Editing that cell is sufficient to change what the merged area displays.

---

## New Structure

```
cell-editor/
├── edit.py              ← you run this
├── config.json          ← {"prefix": "replacement", ...}
├── src/
│   ├── __init__.py
│   └── editor.py        ← cell scanning + replacement logic
├── tests/
│   └── test_editor.py
└── conftest.py
```

---

## How It Works

**config.json**:
```json
{
  "name:": "name: kacha thanaphithak",
  "age:": "age: 25",
  "Q1": "Q1 2026"
}
```

**Run**:
```powershell
cd cell-editor
python edit.py
```

**What happens**:
1. Reads `config.json` for prefix→replacement rules
2. Iterates all .xlsx in input folder
3. For each sheet, scans every cell
4. If cell text starts with any key, replaces entire cell with the value
5. Saves edited copy to output folder

---

## Work Objectives

### Core Objective
Build a standalone CLI tool that batch-edits XLSX cell text using prefix-match replacement rules, saving copies to an output folder.

### Concrete Deliverables
- `cell-editor/edit.py` — CLI entry point
- `cell-editor/config.json` — replacement rules
- `cell-editor/src/editor.py` — cell scanning + editing logic
- `cell-editor/tests/test_editor.py` — pytest tests

### Must Have
- Config: JSON key-value map (keys are prefixes, values are replacements)
- Scan every cell in every sheet
- Prefix match: `cell.value.startswith(key)` → replace with value
- Handle merged cells (openpyxl's `merged_cells` is auto-handled)
- Save edited copy to output folder (original untouched)
- Batch: process all .xlsx in input folder
- Skip `~$*.xlsx` temp files

### Must NOT Have
- NO modifying original XLSX files
- NO PNG extraction (separate tool)
- NO GUI or progress bars
- NO exact/contains match — prefix only
- NO non-XLSX file support

---

## TODOs

- [x] 1. Project setup — create `cell-editor/` folder, `config.json`, `src/`, `tests/`
- [x] 2. Editor module — `src/editor.py` with cell scanning + replacement logic
- [x] 3. CLI — `edit.py` with argparse, main loop, error handling
- [x] 4. Tests — `tests/test_editor.py` with pytest
- [x] 5. Run tool + pytest — verify editing works

---

## Verification

```bash
cd cell-editor
python edit.py
# Expected: processes XLSX, saves copies with edited cells

pytest tests/test_editor.py -v
# Expected: all pass
```
