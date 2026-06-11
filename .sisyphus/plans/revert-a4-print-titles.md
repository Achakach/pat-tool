# Revert a4_page_rows + Add Print Title Rows

## TL;DR

Bring back manual page boundary logic. Add `print_title_rows` for repeating headers on every printed page.

## Step 1: Revert a4_page_rows

Restore from before print-area plan:
- Add `"a4_page_rows": 54` to config.json
- Add `page_rows` param to `insert_png` and `insert_png_no_label`
- Add page boundary push logic in both functions
- Read + pass `page_rows` from insert.py

## Step 2: Add print_title_rows

In `_setup_a4_print`, add:
```python
ws.print_title_rows = "1:2"  # header rows repeat on every page
```

Config for header rows:
```json
"print_title_rows": "1:2"
```

## Step 3: Keep print_area

Keep dynamic print area — still useful:
```python
ws.print_area = f"A1:{last_col}{last_row}"
```

## Step 4: Keep row_breaks

Page breaks per site label stay.

## TODOs

- [x] 1. Revert a4_page_rows from git or re-implement
- [x] 2. Add print_title_rows config + code
- [x] 3. Test — images don't split, same page count as before
- [x] 4. Print Preview — verify headers repeat on every page
