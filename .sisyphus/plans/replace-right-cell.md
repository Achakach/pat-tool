# Replace Adjacent Cell Instead of Label Cell

## TL;DR

> **Quick Summary**: Change cell-editor to replace the cell to the RIGHT of the matched label, not the label itself. `name:` in A1 → `kacha` in B1.
>
> **Estimated Effort**: Trivial (1 file, 2 lines changed)

---

## What Changes

### Before
```
Find ALL cells starting with "name:" → replace ALL to the right
```

### After
```
Find FIRST cell starting with "name:" → replace to the right → stop looking for "name:"
```

Each prefix triggers only once per workbook. Scan top-to-bottom, left-to-right — first match wins, rest ignored.

### editor.py — `process_workbook()`

```python
def process_workbook(xlsx_path, output_path, replacements):
    wb = load_workbook(xlsx_path)
    changed = 0
    matched = set()  # track which prefixes already matched
    
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                text = str(cell.value)
                for prefix, replacement in replacements.items():
                    if prefix in matched:
                        continue  # already found this one, skip
                    if text.startswith(prefix):
                        # Find first non-merged cell to the right
                        right_col = cell.column + 1
                        for merged in ws.merged_cells.ranges:
                            if (merged.min_row <= cell.row <= merged.max_row and
                                merged.min_col <= right_col <= merged.max_col):
                                right_col = merged.max_col + 1
                        ws.cell(row=cell.row, column=right_col).value = replacement
                        changed += 1
                        matched.add(prefix)
                        break
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    wb.close()
    return changed
```

---

## TODOs

- [x] 1. Update `cell-editor/src/editor.py` — replace right cell, not label cell
- [x] 2. Update `cell-editor/config.json` — values without prefix
- [x] 3. Update tests — verify new behavior
- [x] 4. Run tool + pytest — verify

---

## Verification

```bash
cd cell-editor
python edit.py
pytest tests/test_editor.py -v
```
