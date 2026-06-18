# Fix A4 Page Break Image Row Calculation

## TL;DR

> **Summary**: Replace hardcoded row height (15pt) and pixel ratio (0.75) with actual worksheet row dimension measurements.
>
> **Effort**: Quick — 2 functions in inserter.py

## Context

Tool 5's `_calc_page_rows` and `insert_png` use hardcoded values:
- `default_ht = 15` — assumes every row is exactly 15 points
- `display_h * 0.75` — assumes 0.75 pixel-to-point ratio

If actual row heights differ (template custom sizing, merged cells), images cross page boundaries.

## The Fix

Two changes in `5-png-inserter/src/inserter.py`:

### 1. `_calc_page_rows` — use actual row heights

Replace `math.ceil(printable_pts / 15)` with a loop that sums `ws.row_dimensions[r].height` starting from row 1 until the sum exceeds `printable_pts`.

### 2. `insert_png` — use actual row heights for image

Replace `int(display_h * 0.75 / 15) + 1` with a loop that sums `ws.row_dimensions[r].height` from `img_row` forward until the sum equals or exceeds `display_h * 0.75`.

Helper function:
```python
def _rows_for_height(ws, start_row, height_pts):
    """Count rows needed to cover height_pts starting at start_row."""
    accumulated = 0
    row = start_row
    while accumulated < height_pts:
        rh = ws.row_dimensions[row].height or 15
        accumulated += rh
        row += 1
    return row - start_row
```

## TODOs

- [ ] 1. Add `_rows_for_height` helper to inserter.py
- [ ] 2. Update `_calc_page_rows` to use helper
- [ ] 3. Update `insert_png` rows_needed to use helper
- [ ] 4. Run tool 5 test suite — 51 pass

## Must NOT Do
- Do NOT change snap/overflow logic
- Do NOT change label/image insertion
- Do NOT change config.json

## Final Verification
- [ ] F1. 51 tests pass
- [ ] F2. Manual verify: image no longer breaks across pages
