# Copy Headers to Page Boundaries

## Problem

`print_title_rows` consumes body rows on every page. Page 2 content starts visually lower than page 1. No Excel fix.

## Fix

Remove `print_title_rows`. Insert header rows as actual data at page boundaries.

### How

```python
# After snap to next page:
# Copy header rows (1-6) to the page boundary
if title_rows:
    for r in range(1, header_count + 1):
        for c in range(1, ws.max_column + 1):
            val = ws.cell(row=r, column=c).value
            if val is not None:
                ws.cell(row=page_start + r - 1, column=c).value = val
```

### Result

```
Page 1:
  Row 1-6: headers
  Row 7-9: mock data
  Row 10: SITE03 label
  Row 12: image

Page 2:
  Row 55-60: headers (copied)     ← same visual offset
  Row 61: SITE04 label
  Row 63: image
```

## Config

Remove `print_title_rows`. Add `header_rows: "1:6"`.

## TODOs

- [x] 1. Remove print_title_rows from config + _setup_a4_print
- [x] 2. Add header_rows config + copy logic in insert.py snap
- [x] 3. Test — labels at same visual position every page
- [x] 4. Print Preview verify
