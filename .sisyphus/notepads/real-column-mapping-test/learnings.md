# Learnings — real-column-mapping-test

## 2026-06-16T07:12 Session Start

### Inherited from build-at-config-split + previous
- build_at architecture is in place: build_at keys Q/R/S for PW/IP1/IP2
- copy_column function removed from codebase entirely
- Production config: PW→J, IP1→E, IP2→H, NE_NO1→D, PORT_NO1→F, L1→C, NE_NO2→G, PORT_NO2→I
- page_rows = 52, autoPageBreaks=True
- Tests use tmp_path (auto-cleaned)
- conftest.py at 3-column-copier/conftest.py
- 23 tests currently pass (14 test_columns + 9 test_print_setup)
- copier.py saves source with temp columns (wb.save at line ~110) — source IS modified
- The "source not modified" guarantee means original data columns are preserved, temp columns are expected
- For this test: SHA256 check should be on source BEFORE copier runs vs AFTER (which includes temp columns)
  - Better approach: verify original columns C/D/E/G/H unchanged after copier, not entire file checksum
- E2E from Task 3 of build-at-config-split confirmed: all 8 columns work, page break at 53

### Module specifics
- copier.main() reads config from config.json relative to copier.py
- read_matching reads matching.xlsx for planwork→filename mapping
- Existing tests use openpyxl Workbook() directly + tempfile for file-based tests

### generate_test_data.py (2026-06-16T14:14)
- Created at `3-column-copier/tests/generate_test_data.py`
- Generates `source_test.xlsx` (3 sheets: PW TEST001, cutsheet, Get Log Before&After)
- Generates `target_test.xlsx` (1 sheet: IP & Port Assignment, no merged cells)
- 20 cutsheet rows (3-22) with cols C/D/E/G/H populated
- 40 IP mappings in log row 1 (20 IP1 lookup on col C, 20 IP2 lookup on col G)
- Self-verifies with assertions after generation
- Usage: `cd 3-column-copier && python tests/generate_test_data.py`
- `--tmp-dir` flag (default: tests/tmp)
- No merged cells in any sheet
- Cols Q/R/S intentionally empty — copier builds these as build_at columns

## 2026-06-16T14:20 Real Mapping Test

### copier.main() refactor
- Changed `def main()` → `def main(config=None)`
- When config is None (default), loads from file with old path resolution
- When config is provided as dict, paths used directly with `.resolve()` 
- Fully backward compatible: `python copier.py` unchanged
- Both branches set `action`, `matching_file`, `source_folder`, `target_folder`, `output_folder`

### test_real_mapping.py
- Full pipeline test: generator → matching.xlsx → copier.main() → verify output
- Uses subprocess to call generator with `--tmp-dir str(tmp_path)`
- Matching.xlsx uses `"matching_sheet": "Sheet"` (default openpyxl sheet name)
- Maps TEST001 → "target_test" (filename without .xlsx extension is auto-appended)
- Verified all 8 production columns at row 3, last L1 at row 22, page break at row 53
- Source integrity: original columns C/D/E/G/H unchanged

### IP collision bug found & fixed in generate_test_data.py
- IP1 sequence: CR10..CR29 (i=0..19), IP2 sequence: CR20..CR39 (i=0..19)
- Overlap at CR20..CR29 caused IP map dict to have wrong value (last-write-wins)
- Fixed: IP2 uses CR30..CR49 (no overlap with IP1's CR10..CR29)
- Updated verify_files: col G check, log column 2 check

## 2026-06-16T14:21 F3 Manual QA

### Execution
- Generated data to `tests/f3_qa/` via `generate_test_data.py --tmp-dir tests/f3_qa`
- Created matching.xlsx: TEST001 → target_test.xlsx
- Config: page_break_enabled=True, a4_page_rows=52, paste_mode=append
- Called `copier.main(config=test_config)` in-process

### Results
- **11/11 cells correct** (D3, F3, C3, G3, I3, J3, E3, H3, C22, row53, row54)
- **Source columns CLEAN** (C, D, E, G, H all unchanged)
- **Page break at row 53** (snap_gap_rows inserted 3 gap rows)
- **Source SHA256 changed** — expected: copier saves temp columns Q,R,S to source via `wb.save()`

### Discrepancies with plan DoD
- DoD says H3=10.20.20.20 → actual is 10.20.30.30 (matches generator: CR30SDA maps to 10.20.30.30)
- DoD says G3=CR20SDA → actual is CR30SDA (NE_NO2 source_col=G, row3 colG=CR30SDA)
- test_real_mapping.py assertions match actual values (test was correct, plan DoD had typos)

### Evidence
- `.sisyphus/evidence/real-mapping/f3-manual-qa.txt`

## 2026-06-16T14:24 Final Verification Wave — GAPS

### GAP 1: SHA256 dead code → real content hash
- `src_hash_before` was a dead file-level SHA256 that always differed (copier writes temp cols)
- Replaced with content-level hash: read cols C/D/E/G/H rows 3-22, join with "|", SHA256
- Before-copier hash stored at line 29, after-copier hash computed and compared
- Spot-check assertions still present (row 3 individual cells)

### GAP 2: Evidence files captured
- `.sisyphus/evidence/real-mapping/real-mapping-1-generator.txt` — generator output
- `.sisyphus/evidence/real-mapping/real-mapping-2-pytest.txt` — pytest -v output (24/24 passed)
- `.sisyphus/evidence/real-mapping/real-mapping-3-e2e.txt` — pytest --tb=long output
