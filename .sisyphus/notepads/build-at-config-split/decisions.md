# Decisions — build-at-config-split

## 2026-06-16T05:04 Session Start

### Confirmed with user
- cleanup action bug fix: INCLUDE in this plan scope (delete build_at columns Q/R/S, not paste_to J/E/H)
- copy_column function: DELETE from src/columns.py + update TestCopyColumn test
- Test data for E2E (Task 3): Python generator script (deferred to real-column-mapping-test plan)

### Architecture decisions (from plan)
- build_at is optional — falls back to paste_to when absent
- Build step: col_cfg.get("build_at", col_cfg.get("paste_to"))
- Paste step: read from build_at col (or source_col for copy), write to paste_to col
- Copy columns: use source_col → paste_to directly (no copy_column function)
- Config order no longer matters (build_at eliminates all ordering dependencies)
