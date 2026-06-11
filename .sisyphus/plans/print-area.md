# Replace Row-Counting with Excel Print Area

## TL;DR

> Remove `a4_page_rows` + manual push logic. Use `ws.print_area` + `fitToWidth=1` + `fitToHeight=0`. Excel auto-flows pages.
>
> **Estimated Effort**: Medium

---

## Changes

### Remove from 5-png-inserter:
- `a4_page_rows` config field
- `page_rows` param from `insert_png` and `insert_png_no_label`
- Manual push logic in both functions (`if page_rows: page_end = ...`)

### Add to _setup_a4_print:
```python
def _setup_a4_print(ws):
    ws.page_setup.paperSize = 9
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0          # height auto-flows
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5
```

### Add print_area update after all images inserted:
In `insert.py`, after the PNG loop for a sheet, set print area to content bounds:
```python
# After all PNGs inserted for this sheet, set print area
last_row = ws.max_row
last_col_letter = get_column_letter(ws.max_column)  # or use "K" from config
ws.print_area = f"A1:{last_col_letter}{last_row}"
```

## Tests

- [ ] `test_print_area_set` — verify print_area string matches content bounds
- [ ] `test_fit_to_width` — verify fitToWidth=1, fitToHeight=0
- [ ] `test_no_a4_page_rows` — verify page_rows param removed
- [ ] `test_same_page_count` — run with real data, compare page count to old behavior
- [ ] `test_all_existing_pass` — existing test suite unchanged

## Verification (user)

After implementation, run:
```powershell
cd 5-png-inserter
python insert.py
```

Open `output/test_fixture.xlsx` → File → Print. Verify:
- Page breaks per site ✅
- Content fits A4 width ✅
- No missing images ✅
- Page count same as before ✅

## TODOs

- [x] 1. Remove a4_page_rows from config, code, and tests
- [x] 2. Add print_area to _setup_a4_print
- [x] 3. Update insert.py to set print_area after insertion
- [x] 4. Run tests — all pass + new ones
- [x] 5. Manual verification by user
