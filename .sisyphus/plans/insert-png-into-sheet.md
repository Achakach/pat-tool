# Insert PNGs into Purged Sheet

## TL;DR

> **Quick Summary**: After purge, for each PNG matched to a sheet: write label in column A, insert PNG in column B. Start from purge_from_row, stack vertically.
>
> **Estimated Effort**: Medium

---

## How It Works

```
Sheet after purge (row 10+ blank):

Row 10: "BKK01"              ← label row (bold, colored)
Row 11: [PNG inserted here]  ← image below label
Row 12: (empty gap)
Row 13: "BKK09"              ← next label row
Row 14: [PNG inserted here]
```

Label in column A. PNG directly below it. Label row formatted bold + background color.

## Implementation

### 4-png-inserter/src/inserter.py — add insert function

```python
from openpyxl.drawing.image import Image as XlImage
from openpyxl.styles import Font, PatternFill

def insert_png(xlsx_path: Path, sheet_name: str, png_path: Path, 
               label: str, start_row: int) -> int:
    """Insert label + PNG. Returns next available row after insertion."""
    wb = load_workbook(str(xlsx_path))
    ws = wb[sheet_name]
    
    # Label row — bold + light blue background
    label_cell = ws.cell(row=start_row, column=1)
    label_cell.value = label
    label_cell.font = Font(bold=True, size=12)
    label_cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    
    # PNG row — directly below label
    img_row = start_row + 1
    img = XlImage(str(png_path))
    cell_ref = f"A{img_row}"
    ws.add_image(img, cell_ref)
    
    # Adjust row height for label
    ws.row_dimensions[start_row].height = 20
    
    wb.save(str(xlsx_path))
    wb.close()
    return img_row + 2  # skip a gap row, return next available
```
```

### insert.py — update main loop

Replace the placeholder in the PNG loop:
```python
        # Track current row per sheet
        sheet_rows = {}  # sheet_name → next available row
        
        for png in pngs:
            label = extract_label(png.name)
            
            wb = load_workbook(str(output_path))
            sheet_name = find_matching_sheet(wb, label)
            wb.close()
            
            if not sheet_name:
                print(f"  WARNING: No sheet matched for '{label}'")
                continue
            
            # Purge once per sheet
            if purge_from and sheet_name not in purged_sheets:
                purge_sheet(output_path, sheet_name, purge_from)
                purged_sheets.add(sheet_name)
                sheet_rows[sheet_name] = purge_from
            
            # Get current row for this sheet
            current_row = sheet_rows.get(sheet_name, purge_from or 10)
            
            # Insert PNG
            next_row = insert_png(output_path, sheet_name, png, label, current_row)
            sheet_rows[sheet_name] = next_row
            
            print(f"  Inserted: {png.name} → '{sheet_name}' row {current_row}")
            inserted += 1
```

---

## TODOs

- [x] 1. Add insert_png function to inserter.py
- [x] 2. Wire insertion into insert.py main loop
- [x] 3. Tests + verify
