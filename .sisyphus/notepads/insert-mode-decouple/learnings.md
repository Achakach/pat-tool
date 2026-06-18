# Learnings: insert-mode-decouple

## Task
Add `insert_mode` config key to `3-column-copier/copier.py` to decouple insert-rows behavior from page-break formatting.

## Changes Made
1. **Line 79-80**: Added config read with comment after `page_break_enabled` line
   ```python
   # insert_mode: push content down on append, independent of page formatting
   insert_mode = config.get("insert_mode", False)
   ```
2. **Line 189**: Changed condition from `page_break_enabled` to `(page_break_enabled or insert_mode)`
   ```python
   if paste_mode == "append" and (page_break_enabled or insert_mode):
   ```

## Key Details
- OR condition preserves backward compatibility — `page_break_enabled=True` still triggers insert
- `insert_mode` defaults to `False` when key is missing from config
- Lines 164 (`if page_break_enabled:` for A4 setup) and 251 (`if page_break_enabled:` for snap_gap_rows) left untouched
- No new imports needed
- Line numbers shifted by +2 due to the 2-line insert (comment + variable)

## Verification
- `grep "insert_mode" copier.py` → 3 matches (comment, config read, condition)
- `grep "page_break_enabled" copier.py` → lines 78, 164, 189 (now with or), 251 — all correct
