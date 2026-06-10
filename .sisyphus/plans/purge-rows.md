# Add Purge Row to PNG Inserter

## TL;DR

> **Quick Summary**: Before inserting PNGs, delete everything from a configurable row downward. Clears template mockup data.
>
> **Estimated Effort**: Quick (config + 5 lines in inserter)

---

## Config Update

Add to `4-png-inserter/config.json`:
```json
{
  "matching_file": "../matching.xlsx",
  "matching_sheet": "match",
  "filename_col": "Site",
  "planwork_col": "PW Number",
  "xlsx_folder": "./xlsx",
  "png_folder": "./input",
  "output_folder": "./output",
  "purge_from_row": 10
}
```

## What It Does

For each XLSX in output:
1. Open the workbook
2. For each sheet: delete all rows from `purge_from_row` to end
3. This clears mockup images, placeholder text, old data
4. Save — ready for fresh PNG insertion

## Implementation

In insert.py, after copying XLSX to output, before inserting:

```python
purge_from = config.get("purge_from_row")
purged_sheets = set()  # track already-purged sheets

# For each matched PNG:
for png in pngs:
    sheet_name = find_matching_sheet(wb, png_label)  # TBD
    
    if sheet_name and sheet_name not in purged_sheets:
        ws = wb[sheet_name]
        ws.delete_rows(purge_from, ws.max_row - purge_from + 1)
        purged_sheets.add(sheet_name)
    
    # ... insert PNG
```

Each sheet purged only once, regardless of how many PNGs match it.

---

## TODOs

- [x] 1. Add purge_from_row to config.json
- [x] 2. Add purge logic to insert.py
- [x] 3. Test — verify rows deleted
