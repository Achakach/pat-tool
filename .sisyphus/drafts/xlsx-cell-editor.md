# Draft: XLSX Cell Text Editor

## Requirements (confirmed)
- Separate tool in `cell-editor/` folder
- Prefix match: cell starts with key → replace entire cell with value
- Batch mode: process all .xlsx in input folder
- Creates copy in output folder (original untouched)
- Search ALL cells in every sheet
- Config: JSON file with key-value map `{"find": "replace", ...}`
- Handle: merged cells, same cell, different columns — all covered by "search all cells"

## Technical Decisions
- Uses openpyxl: read cells, detect merged ranges, write new file
- Config: `{"name:": "name: kacha thanaphithak", "age:": "age: 25"}`
- Structure: same pattern as extractor — main script + config + library modules
- Folder: `cell-editor/` with its own `config.json`, `edit.py`, tests

## Scope Boundaries
- INCLUDE: cell text replacement, merged cell handling, batch processing, prefix match
- EXCLUDE: formula editing, formatting changes, image manipulation, PNG extraction