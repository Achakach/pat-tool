# Site Label on New Page

## TL;DR

> If next site label would split across pages, push to new page. Each site starts clean.

## Change

### src/inserter.py — insert_png
After page boundary check (image), ADD check for site transitions:

```python
# Site transition: if label + gap + image won't fit on current page, push to next
if current_row > 1 and page_rows:
    page_start = ((current_row - 1) // page_rows) * page_rows + 1
    if current_row != page_start:
        # Not at page start — new site, push to next page
        current_row = ((current_row - 1) // page_rows + 1) * page_rows + 1
```

Wait — simpler: in insert.py, when site changes (new label), check if current row is near page end. If so, snap to next page.

Actually, even simpler: in insert.py before calling insert_png with a NEW label, check:

```python
if (site, sheet_name) not in labeled and page_rows:
    # New site label — ensure it starts on proper page
    page_end = ((current_row - 1) // page_rows + 1) * page_rows
    if current_row > page_end - 5:  # less than 5 rows remaining
        current_row = page_end + 1
```

## TODOs

- [x] 1. Add page boundary check for new site labels in insert.py
- [x] 2. Test
