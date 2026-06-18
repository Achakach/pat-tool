# Decisions — real-column-mapping-test

## 2026-06-16T07:12 Session Start

### Architecture decisions (from plan)
- Test data format: Python generator script (not pre-committed .xlsx)
- Test methodology: Tests-after (verify implementation)
- No merged cells in test data
- print_title_rows: null (header_count=0)
- Source integrity: verify original columns unchanged (not whole-file SHA256 since copier writes temp columns)

### From previous session (confirmed with user)
- copy_column: Deleted from src/columns.py ✅
- cleanup bug: Fixed in build-at-config-split ✅
- Test data: Python generator script ✅
