# Test Quality Review — Learnings

## Verdict: APPROVE

## Review Date: 2026-06-16

## Summary
- 8 files reviewed (5 new, 3 expanded)
- 38 new/expanded tests total
- All tests pass
- 1 minor code-quality issue found (non-blocking)

## Per-File Notes

### 2-template-generator/tests/test_generate.py (12 tests, 287 lines)
- STRUCTURE: Clean. Class `TestGenerate` with helper methods `_make_template`, `_make_matching`, `_cfg`.
- COVERAGE: Happy paths, error paths, inheritance, suffix handling, duplicates, custom config, missing column header.
- PATTERN: All tests use `main(config=config)` pattern for config injection. No CLI subprocess needed.

### 1-png-extractor/tests/test_drawing.py (7 tests, 193 lines)
- STRUCTURE: `TestLocalFind`, `TestFindDrawingPath`, `TestParseDrawingImageMap` classes.
- PATTERN: Real XLSX creation via `_create_xlsx_with_image()`. Zip manipulation for `twoCellAnchor` variant.
- EDGE CASES: Empty drawing XML, no-drawing sheet, both anchor types.
- NOTE: `_PNG_DATA` constant duplicated here and in test_extract_pngs.py. Acceptable (different file scopes).

### 3-column-copier/tests/test_cleanup.py (4 tests, 270 lines)
- STRUCTURE: `TestCleanup` class. Helpers `_make_matching`, `_make_source`.
- COVERAGE: Column deletion, data preservation, backward compat (no build_at), empty source folder.
- MINOR: `test_cleanup_empty_source_folder` assertion is weak (only `out_dir.exists()`).

### tests/test_run.py (5 tests)
- PATTERN: Subprocess-based. Copies run.py to tmp_path, writes pipeline.json, executes.
- COVERAGE: All stages, stop on failure, file copy, empty stage, missing config.
- TIMING: All 5 tests complete in <1s.

### tests/test_pipeline_e2e.py (1 test, 394 lines)
- PATTERN: Monolithic E2E. Creates all 5 tool configs + fixtures. Runs run.py as subprocess.
- WORKAROUND: Monkey-patch for openpyxl `autoPageBreaks` bug (PrintPageSetup._parent is None after XML load).
- COVERAGE: Verifies each stage output, pipeline exit code, final content (replacement text, label, images).
- NOTE: Large single test — OK for E2E but hard to debug individual stage failures.

### 4-cell-editor/tests/test_editor.py (new tests: lines 119-273)
- CLASS: `TestProcessWorkbook` (new tests: lines 121-220), `TestMainIntegration` (lines 223-273).
- COVERAGE: Multi-prefix, multi-worksheet, Thai Unicode, overlapping prefixes, config injection, error paths.
- PATTERN: `process_workbook()` for unit tests, `main(config=config)` for integration.

### 1-png-extractor/tests/test_extract_pngs.py (new test: test_main_with_config_dict)
- LINES: 277-331 within existing `TestIntegration` class.
- PATTERN: Creates XLSX with PW+exist sheets + embedded image + label text. Runs `main(config=config)`.
- VERIFIES: PNG filename format, non-zero size.

### 5-png-inserter/tests/test_matcher.py (new test: test_main_with_config_dict)
- LINES: 180-294 within `TestMainIntegration` class.
- ISSUE: Two test concerns in one method (L180-260 tests main(), L261-294 tests insert_png() directly).
- L261: Orphan docstring string literal (dead expression).
- L85: `purge_sheet` imported inside class method body instead of top-level.
- BOTH cosmetic — tests execute correctly, assertions pass.

## Cross-Check Results
- All 22 function imports verified existing via grep across all source modules.
- `main(config=...)` sig exists on all 5 tool entry points.
- `process_workbook()`, `insert_png()`, `read_matching()`, `match_pngs()`, etc. all confirmed.

## Test Execution
All 38 tests pass across all files. No flaky tests observed.
