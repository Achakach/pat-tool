# Learnings — build-at-config-split

## 2026-06-16T05:04 Session Start

### Inherited from handover + previous sessions
- page_rows = 52 (math.ceil(769.89/15) on A4 with 0.5" margins)
- openpyxl stores print_title_rows as "$1:$6"
- autoPageBreaks=True + no manual breaks (let Excel handle)
- Tests use tmp_path (auto-cleaned by pytest)
- conftest.py at tool root (3-column-copier/conftest.py), not in tests/
- All existing tests must pass after changes (23 total after RED phase, 23 after GREEN + REFACTOR)

### Convention
- Plan is TDD: RED (tests first) → GREEN (impl) → REFACTOR (verify)
- Tools are standalone (no shared lib between pipeline tools)
- Config uses relative paths relative to tool folder
- Previous issues fixed: duplicate class names, test_fixture mutation, config null confusion

## 2026-06-16T05:04 RED Phase - Test Writing

### New RED tests added (3 tests)
1. `TestPasteDirect::test_paste_direct_source_to_target` — Simulates reading from `source_col` (C) in source wb, writing to `paste_to` (D) in target wb. Cross-workbook copy without `copy_column()`.
2. `TestBuildAt::test_build_at_maps_to_target` — Simulates reading from `build_at` column (R=18) in source, writing to `paste_to` (E) in target. Validates column number offset mapping.
3. `TestBackwardCompat::test_backward_compat_no_build_at` — Simulates fallback: no `build_at` key → use `paste_to` for both source read and target write.

### Test patterns established
- All 3 tests use `Workbook()` directly (no tmp_path) — match existing `TestPwColumn`/`TestIpColumn` style.
- Two-workbook pattern: `swb` (source) + `twb` (target), close both.
- Data set via `.cell(row=N, column=M).value` for non-A1 notation columns (col 18=R, col 6=F).
- `col_letter_to_index` used to verify column number mapping.
- `copy_column` removed from imports + `TestCopyColumn` class deleted.

## 2026-06-16T05:07 GREEN Phase - Implementation

### Changes made to copier.py (4 changes, all in one pass)
1. **Build step (Change A)**: Replaced `paste_to` with `build_at = col_cfg.get("build_at", col_cfg.get("paste_to"))` in lines 99-108. `build_pw_column` and `build_ip_column` now receive `build_at` column. Falls back to `paste_to` for backward compat.
2. **Removed copy_column call (Change B)**: Deleted the 2-line `if col_type == "copy": copy_column(...)` block from the paste loop (former lines 188-189).
3. **Paste step src/dst logic (Change C)**: Source column determined by type: planwork/ip_lookup → build_at (fallback paste_to), copy → source_col (fallback paste_to), else → paste_to. Destination always = paste_to.
4. **Cleanup action (Change D)**: Replaced `paste_to` with `col_to_delete = col_cfg.get("build_at", col_cfg.get("paste_to"))` — deletes temp build_at columns instead of target paste_to columns.

### Verification
- All 23 tests pass (including 3 new RED tests: TestPasteDirect, TestBuildAt, TestBackwardCompat)
- `copy_column` function still imported from src/columns (removed in REFACTOR phase)
- Backward compat verified: missing `build_at` → uses `paste_to`

## 2026-06-16 REFACTOR Phase — Remove dead code

### Changes made
1. **copier.py line 12**: Removed copy_column from the import tuple
2. **src/columns.py lines 59-77**: Deleted the entire copy_column function

### Verification
- All 23 tests still pass
- No broken imports — copier.py still imports from src.columns cleanly
- copy_column fully removed from codebase (was already dead code — no callers remaining)

## 2026-06-16T05:?? Task 2 — Config production column mapping

### Changes to config.json
- Replaced entire `columns` section with production mapping
- **PW**: added `build_at: "Q"`, changed `paste_to` from Q → J
- **IP1**: added `build_at: "R"`, changed `paste_to` from R → E
- **IP2**: added `build_at: "S"`, changed `paste_to` from S → H
- **NE_NO1**: changed `paste_to` from C → D
- **PORT_NO1**: changed `paste_to` from D → F
- **L1**: changed `paste_to` from E → C
- **NE_NO2**: unchanged (`paste_to`: G → G)
- **PORT_NO2**: changed `paste_to` from H → I
- All other top-level keys untouched
- Config order within columns: PW, IP1, IP2, NE_NO1, PORT_NO1, L1, NE_NO2, PORT_NO2

### Verification
- `python -c "import json; json.load(open('config.json')); print('OK')"` prints OK
- All 23 tests pass with new config
- No code changes needed — copier.py already handles `build_at` from Task 1

## 2026-06-16 E2E Spot-check — build_at + page_break_enabled

### Test setup
- Source: `source/test_source.xlsx` — cutsheet (5 rows, cols C/D/E/G/H), Get Log (10 IP mappings), PW sheet "PW TEST001"
- Target: `target/test_site.xlsx` — "IP & Port Assignment" sheet, EXISTING_DATA_30 at row 30 col A
- matching.xlsx: row 11 → test_site / TEST001
- Config: `page_break_enabled: true`, `a4_page_rows: 52`, `paste_mode: append`
- SHA256 before run: `1850A20B3FB4EDEA1518739237D0C15D62F138720080D830B13FEF53A174050A`

### Results — ALL output verifications PASS
| Cell | Expected | Got | Status |
|------|----------|-----|--------|
| C3 | CR10-KM01 | CR10-KM01 | ✓ |
| D3 | CR10SDA | CR10SDA | ✓ |
| E3 | 10.10.10.10 | 10.10.10.10 | ✓ |
| F3 | 1/1/1 | 1/1/1 | ✓ |
| H3 | 10.20.20.20 | 10.20.20.20 | ✓ |
| J3 | TEST001 | TEST001 | ✓ |
| Row 53 | EXISTING_DATA_30 | EXISTING_DATA_30 | ✓ |

### Page break behavior
- 5 data rows + 18 gap rows snapped at row 8
- EXISTING_DATA_30 pushed from row 30 → row 35 (by 5 data row insert) → row 53 (by 18 gap row insert) = row 53 ✓
- `snap_gap_rows` correctly identified next non-empty at row 35, calculated gap to next clean start (53)

### Important finding — Source file IS modified by copier
- **SHA256 before**: `1850A20B3FB4EDEA1518739237D0C15D62F138720080D830B13FEF53A174050A`
- **SHA256 after**: `74B2FF39F565B567B63C206BEE1712F4385E0958BB26E22697BE0147377DB095`
- The copier DOES save the source file (lines 110-111) with build_at temp columns (Q/R/S) added
- This contradicts the "Source should NOT be modified" guarantee in build_at design
- If source preservation is required, either: (a) add cleanup action after copy, or (b) copy source before building
- Exit code 0, clean run, no errors
