# Issues — build-at-config-split

## 2026-06-16T05:04 Session Start

### Known bugs to fix
- cleanup action: deletes paste_to columns (J/E/H) instead of build_at columns (Q/R/S)
  - Fix: use build_at for column deletion, fallback to paste_to

### From previous sessions (fixed, for reference)
- Duplicate TestPrintTitleRows class → renamed
- test_fixture.xlsx mutated → git checkout restore
- Config null confused user → documented
- _parse_print_title_rows unused start var → fixed
- Missing guard for header_count >= page_rows → fixed
- Debug print shows wrong autoPageBreaks value → fixed
