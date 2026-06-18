# Handover — PAT Tool Sessions (Updated)

> **Date**: 2026-06-17 | **Sessions**: full-pipeline-e2e ✅ | cli-integration-tests ✅ | zip-distribution ✅ | a4-print-fix ✅ | ip-lookup-fix ✅ | merged-cell-fix ✅ | merge-cell-debug ✅ | pw-fill-cleanup-fix ✅

---

## ⚠️ Current Issue

When multiple source files map to the same target, the copier **overwrites** instead of **appending**. Each source loads the clean template from `target/`, writes output, but if 3 sources map to the same file, only the last one survives.

**Example**: E2E004 (8 rows), E2E005 (5 rows), E2E003 (16 rows) all target `e2e_v3_target.xlsx`. Output only has 16 rows (E2E003's data). Expected: 29 rows total.

**Fix plan ready**: `.sisyphus/plans/multi-source-append.md` — check if output already exists, load that as target instead of fresh template. Run `/start-work multi-source-append` to execute.

---

## What's Next

| Priority | Task | Plan |
|----------|------|------|
| 🔴 NOW | Fix multi-source append (overwrite → accumulate) | `.sisyphus/plans/multi-source-append.md` |
| 🟡 Later | Fix `_parse_print_title_rows` bug in tool 5 | Not planned |
| 🟡 Later | Unify 3 matching.xlsx parsers | Not planned |
| 🟡 Later | Unify config injection across tools | Not planned |

---

## 1. Pipeline Architecture

```
run.py orchestrates 5 tools sequentially via pipeline.json:

1-png-extractor     extracts PNGs from XLSX, copies → 5-png-inserter/input/
2-template-generator copies template per site, copies → 3-column-copier/target/
3-column-copier     copies 8 columns source→target, copies → 4-cell-editor/input/
4-cell-editor       prefix-match + replace text, copies → 5-png-inserter/xlsx/
5-png-inserter      inserts PNGs into XLSX → FINAL OUTPUT
```

Each tool is self-contained: `src/` for library code, `tests/` for pytest, `config.json` for settings. Dependencies: openpyxl, Pillow, pytest.

---

## 2. Test Coverage — Current State

| Tool | Tests | Notes |
|------|-------|-------|
| 1-png-extractor | 38 | unchanged |
| 2-template-generator | 15 | unchanged |
| 3-column-copier | **38** | +1 merged cell skip test, +multi-record fixtures |
| 4-cell-editor | 15 | unchanged |
| 5-png-inserter | 51 | unchanged |
| run.py | 5 | unchanged |
| Pipeline E2E | 1 | unchanged |
| **Total** | **163** | |

---

## 3. What We Fixed (This Session)

### 3.8 merged-cell-fix ✅
**Problem**: `AttributeError: 'MergedCell' object attribute 'value' is read-only` at `copier.py:219` when target XLSX has merged cells.

**Fix**: Imported `MergedCell` from openpyxl, added `isinstance(cell, MergedCell)` guard before writing. Merged sub-cells are skipped (not overwritten), normal cells write normally. Added `test_paste_skips_merged_cells`.

**Files**: `copier.py` (+2 lines import + guard), `test_columns.py` (+1 test, 38/38 pass)

### 3.9 merge-cell-debug ✅
**Problem**: No visibility into where merged cells exist when the fix fires.

**Fix**: Added 3 debug prints to stderr:
- Source/target sheet info per file
- Which merge ranges overlap paste area (during insert_rows check)
- Exact cell position when MergedCell is skipped (row, column letter)

**Files**: `copier.py` (+8 lines)

### 3.10 pw-fill-cleanup-fix ✅
**Problem 1**: PW column filled ALL rows with any data (e.g., 50+ rows) instead of stopping where NE_NO data ends (e.g., 16 rows).

**Fix**: `build_pw_column` now accepts `lookup_col` parameter. When provided, stops filling when that column is empty (not when ALL columns are empty). Ties PW range to NE_NO data boundary.

**Problem 2**: Temp columns (Q=PW, R=IP1, S=IP2) stayed permanently in source files after copy. Accumulated across runs.

**Fix**: After copy completes, auto-deletes build_at columns from source right-to-left (S→R→Q to avoid index shift). Source files restored to original state.

**Test fixtures**: Created 3 multi-record source files:
- `multi-record-source.xlsx` (E2E003, 16 rows, tests empty IP + no-NE_NO cases)
- `multi-record-source-2.xlsx` (E2E004, 8 rows, tests missing IP1)
- `multi-record-source-3.xlsx` (E2E005, 5 rows, all IPs found)
- Target: `e2e_v3_target.xlsx` with "IP & Port Assignment" sheet

**Files**: `columns.py` (+lookup_col param), `copier.py` (+pass lookup_col, +auto-cleanup, 38/38 pass)

### 3.11 scan-merges.py ✅
Diagnostic tool to scan any XLSX for merged cells across all sheets. Usage: `python scan-merges.py path.xlsx`

---

## 4. Key Discoveries (Deep Audit)

### 4.1 Source files missing log sheet
`demo_source.xlsx` only has `['cutsheet', 'PW 999']` — no `Get Log Before&After` sheet. IP lookup crashes with `KeyError`. User wants crash (not silent skip) so they know something is wrong.

### 4.2 Target files missing correct sheet name
All target files in `3-column-copier/target/` have a sheet named `"Sheet"` but config expects `"IP & Port Assignment"`. Sheet matching uses `clean_sheet_name()` which normalizes names — "Sheet" cleans to "sheet", "IP & Port Assignment" cleans to "ip & port assignment". They don't match → every file gets SKIP.

### 4.3 PW fills too far (root cause)
`build_pw_column` and `build_ip_column` both use `for c in range(1, ws.max_column + 1)` to check row emptiness. If column A has data in row 50, PW fills all 50 rows — even if NE_NO data stops at row 16. Fixed in 3.10 (pw-fill-cleanup-fix).

### 4.4 Cleanup was broken (left-to-right bug)
Old cleanup deleted columns Q→R→S left-to-right. `delete_cols` shifts remaining columns left after each delete. After Q removed, original R shifts to Q's position, original S shifts to R's. Then `delete_cols(18)` deletes what was originally S. Result: R survived, wrong column deleted. Fixed in 3.10 by deleting right-to-left.

---

## 5. Remaining Technical Debt

| Issue | Severity | Detail |
|-------|----------|--------|
| Multi-source overwrite | 🔴 CRITICAL | Multiple sources targeting same file overwrite each other — plan at `.sisyphus/plans/multi-source-append.md` |
| A4 print code diverged (tools 3 & 5) | 🟡 MEDIUM | `_parse_print_title_rows` returns wrong value in tool 5; tool 5 still has global `_a4_print_setup_done` guard; duplicated function |
| Three matching.xlsx parsers | 🟡 MEDIUM | Tool 2 (inline, returns `list[str]`), Tool 3 (`copier.py` — `{pw→filename}`), Tool 5 (`matcher.py` — `{filename→[pw]}`) |
| Config injection not unified | 🟡 MEDIUM | All 5 tools accept `main(config=None)` but path resolution differs |
| No log sheet in demo source | 🟡 LOW | `demo_source.xlsx` missing log sheet — crash is correct per user |

---

## 6. Quick Start

```bash
pip install -r requirements.txt
python run.py                     # full pipeline

# Per-tool tests
cd 3-column-copier && python -m pytest tests/ -v       # 38
cd 5-png-inserter && python -m pytest tests/ -v        # 51
python -m pytest tests/test_run.py tests/test_pipeline_e2e.py -v  # 6

# Diagnostic
python scan-merges.py path/to/file.xlsx
```

---

## 7. Key Details

| Detail | Value |
|--------|-------|
| Config pattern | `def main(config=None)` on all 5 tools |
| Matching format | matching.xlsx: Site + PW Number columns, blank Site inherits |
| PNG naming | `PW {planwork}_{prefix} {site}_{label}.png` |
| Tool 3 output | `./output` |
| IP lookup | Uses regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` |
| A4 print | Defensive try/except on `autoPageBreaks` + gated behind `page_break_enabled` |
| MergedCell fix | `isinstance(cell, MergedCell)` guard at paste point |
| PW fill range | Tied to NE_NO column via `lookup_col` parameter |
| Temp column cleanup | Auto-deletes Q,R,S right-to-left after copy |
| Debug logging | Stderr: file/sheet info, merge overlap warnings, MergedCell skip positions |
| Multi-record fixtures | 3 source files (16+8+5 rows) targeting e2e_v3_target.xlsx |
