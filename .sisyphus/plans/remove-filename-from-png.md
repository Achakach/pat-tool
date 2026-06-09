# Remove XLSX Filename from PNG Output Names

## TL;DR

> **Quick Summary**: Drop the `{XLSXstem}_` prefix from output filenames. Change naming from `Report_Sheet1_Revenue.png` → `Sheet1_Revenue.png`.
>
> **Estimated Effort**: Trivial (3 files, ~10 lines changed)

---

## What Changes

### naming.py — `build_filename()` signature
- **Remove** `xlsx_stem: str` parameter
- **Remove** `stem = sanitize(xlsx_stem)` line
- **Change** return format: `f"{sheet}_{lbl}.png"` / `f"{sheet}_row{row}_col{col}.png"`

### extract_pngs.py — line 221-227
- **Remove** `xlsx_path.stem,` argument from `build_filename()` call
- Final call should be: `build_filename(sheet_name, label, anchor_row, anchor_col)`

### test_extract_pngs.py — all test expectations
- Update `build_filename()` calls to omit the first argument
- Old: `build_filename("report", "Sheet1", "Revenue", 3, 1)` → `"report_Sheet1_Revenue.png"`
- New: `build_filename("Sheet1", "Revenue", 3, 1)` → `"Sheet1_Revenue.png"`

---

## TODOs

- [x] 1. Update naming.py — remove xlsx_stem from build_filename signature and output
- [x] 2. Update extract_pngs.py — stop passing xlsx_path.stem to build_filename
- [x] 3. Update test_extract_pngs.py — update all build_filename test expectations
- [x] 4. Run pytest — all 28 tests should pass with updated expectations

---

## Verification

```bash
# Run the tool — output names should NOT include XLSX filename
python extract_pngs.py --config config.json
# Expected: Sheet1_row2_colB.png (not Book1_Sheet1_row2_colB.png)

# Run tests
pytest test_extract_pngs.py -v
# Expected: 28/28 pass
```
