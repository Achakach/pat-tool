1: # Learnings — xlsx-png-extractor
2: 
3: ## Conventions
4: - Python 3.x with openpyxl for cell reading, zipfile for image extraction
5: - Config via JSON file with `--config` CLI flag
6: - Naming: `{XLSXstem}_{SheetName}_{Label}.png`
7: - Fallback: `{XLSXstem}_{SheetName}_row{N}_col{L}.png`
8: - Flat folder processing only (no recursion)
9: - Stdout for progress, stderr for errors
10: - Exit codes: 0=success, 1=config error, 2=I/O error
11: 
12: ## Task 1 — Project Setup (2026-06-08)
13: - requirements.txt: single dep `openpyxl>=3.0,<4.0`
14: - config.json: `input_folder` and `output_folder` string fields, no extras
15: - .sisyphus/evidence/ created for QA artifacts
16: - Verification: `python -c "import json; c=json.load(open('config.json')); assert 'input_folder' in c; assert 'output_folder' in c; print('OK')"` passes

## Task 5 — Test Fixture (2026-06-08)
- Used PIL for in-memory PNG generation (solid colored rectangles 80x50)
- openpyxl AnchorMarker(col, row, colOff=0, rowOff=0) with TwoCellAnchor for positioning
- col/row are 0-indexed: A1=(0,0), A2=(0,1), B5=(1,4), E2=(4,1), B11=(1,10)
- Three drawing.xml files created: one per sheet (openpyxl auto-numbered drawing1/2/3)
- Each sheet gets its own xl/media/ images: Sales=2 PNGs, Empty=1 PNG, Edge=2 PNGs
- Row-0 edge case (A1 image) handled cleanly — anchor col=0 row=0 in drawing3.xml
- Verification: zipfile inspection confirms 5 PNGs, correct anchor positions, 3 sheets, all labels

## Task 3 — Image Extractor (2026-06-08)
- `extractor.py` created with `extract_images(xlsx_path: Path, output_dir: Path) -> int`
- Uses `zipfile.ZipFile` (not openpyxl) to navigate `/xl/media/` in XLSX
- Filters `.png` case-insensitive, skips non-PNG with warning to stderr
- Output naming: `_raw_{xlsx_stem}_{n}.png` (n=0,1,2...)
- Caught exceptions: `zipfile.BadZipFile` and `PermissionError` → return 0
- Book1.xlsx has 2 PNGs (2374 bytes and 6462 bytes, valid PNG headers)
- Book1.xlsx also has a directory-like entry `xl/media/` (no extension) — warning skipped

## Task 4 — Naming Engine (2026-06-08)
- `naming.py` created with `col_letter`, `sanitize`, `build_filename`, `get_label`
- `col_letter`: recursive formula `n // 26 - 1` for multi-letter columns
- `sanitize`: replaces `/\:*?"<>|` with `_`, strips leading/trailing whitespace + dots
- `build_filename`: sanitizes ALL components before joining (stem, sheet_name, label)
- `get_label`: row 0 → immediate None return; openpyxl cell at `(row=anchor_row, col=anchor_col + 1)`
- `str | None` union syntax works on Python 3.14+ natively
- PowerShell quoting: `"` inside single-quoted `-c` strings causes issues — use temp `.py` file instead

## Task 7 — Test Suite (2026-06-08)
- `test_extract_pngs.py` created with 28 test cases across 3 classes
- **TestNaming** (20 tests): col_letter parametrized 7 cases, sanitize 3, build_filename 6, get_label 4
- **TestConfig** (5 tests): valid config, missing file, invalid schema, non-dict JSON, malformed JSON
- **TestIntegration** (3 tests): full pipeline, missing config exit code 1, bad input folder exit code 2
- Integration test copies `test_fixture.xlsx` into temp input dir, runs CLI via subprocess, verifies 5 output PNGs
- Expected output files: `test_fixture_Sales_Revenue Chart.png`, `test_fixture_Sales_Growth Trend.png`, `test_fixture_Empty_row5_colB.png`, `test_fixture_Edge_row1_colA.png`, `test_fixture_Edge_Deep Label.png`
- MagicMock for `get_label` tests: `ws.cell.return_value.value = "Hello"` simulates cell reads
- `pytest.raises(SystemExit)` for config error assertions, check `exc_info.value.code`
- Absolute paths with `.as_posix()` in temp config to avoid cwd dependency in subprocess
- `tmp_path` fixture auto-cleans — no temp files left behind
- All 28 tests pass: `python -m pytest test_extract_pngs.py -v` → 1.37s, 100% pass

## F2 — Code Quality Review (2026-06-08)
- 10 pattern checks performed across all 6 .py files
- 9/10 patterns clean; hardcoded path found in generate_fixture.py:45
- Additional issues: duplicate filename counter exhaustion (silent overwrite at 100), misleading error message in config.py json.JSONDecodeError handler
- All library modules (config, naming, extractor) use `file=sys.stderr` for prints
- CLI entry point (extract_pngs.py) correctly sends errors to stderr, progress to stdout
- No bare excepts, no `except: pass`, no unused imports, no undefined names
- No `openpyxl._images` private API access (false positives from grep on variable names)
- sanitize() handles all 9 Windows-forbidden chars: / \ : * ? " < > |
- Error handling: BadZipFile, PermissionError, general Exception all caught in extract_pngs.py
- wb.close() in finally block, correctly unreachable when openpyxl.load_workbook fails
- No TODOs/FIXMEs/HACKs/stubs anywhere
- Tests assert real behavior; 28/28 pass on Python 3.14.3
