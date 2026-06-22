# Handover — PAT Tool

> **Date**: 2026-06-19
> **Sessions**: 16 completed
> **Status**: All planned work done. 3 backlog items remain (unplanned).

---

## Sessions Completed

| # | Session | Status |
|---|---------|--------|
| 1 | full-pipeline-e2e | ✅ |
| 2 | cli-integration-tests | ✅ |
| 3 | zip-distribution | ✅ |
| 4 | a4-print-fix | ✅ |
| 5 | ip-lookup-fix | ✅ |
| 6 | merged-cell-fix | ✅ |
| 7 | merge-cell-debug | ✅ |
| 8 | pw-fill-cleanup-fix | ✅ |
| 9 | multi-source-append | ✅ |
| 10 | insert-mode-decouple | ✅ |
| 11 | simplify-insert-logic | ✅ (reverted — user preferred V5 behavior) |
| 12 | revert-to-v5-behavior | ✅ |
| 13 | copy-cell-alignment | ✅ |
| 14 | fix-a4-row-calc-v2 | ✅ |
| 15 | unify-error-handling | ✅ |
| 16 | shift-image-anchors | ✅ |

---

## What We Achieved (16 sessions)

### Latest: shift-image-anchors ✅
**Problem**: openpyxl's `insert_rows()` shifts cells and merged ranges but NOT image anchors — images freeze while rows move, causing overlap.

**Fix**: Created `3-column-copier/src/images.py` with `shift_image_anchors(ws, insert_at_row, num_rows)`. Called after BOTH `insert_rows` sites in copier.py (line 218 primary, line 263 snap).

- 3 guards: `num_rows <= 0`, `insert_at_row < 1`, `hasattr(ws, '_images')`
- OneCellAnchor: shifts `_from.row`
- TwoCellAnchor: shifts both `_from.row` + `to.row` (spanning images: only `to` shifts)
- AbsoluteAnchor: skipped with stderr warning
- 10 TDD tests, 53/53 pass (43 existing + 10 new)
- **Real-world test PASS**: TwoCellAnchor image at rows 15-19, after `insert_rows(3, 5)` shifted to rows 20-24 through full `copier.main()` run
- Commits: `613d77c`, `28ab818`, `3c58049`

### fix-a4-row-calc-v2 ✅
**Problem**: Tool 5 hardcoded 15pt row height and 0.75 pixel ratio — images broke across A4 page boundaries on templates with non-default row heights.

**Fix**: Replaced with `_detect_row_height(ws)` (mode-sampling) + openpyxl's `pixels_to_points()`. 57 tests, live-verified on real fixture (53 PNGs, 9 files, zero crashes).

### unify-error-handling ✅
**Problem**: matching.xlsx error handling inconsistent — Tool 2 used `sys.exit(1)`, Tool 3 returned `{}`, Tool 5 raised `ValueError`.

**Fix**: All 3 tools now raise `ValueError` with format `"Column '{col}' not found in headers (row 1)"`. Independent `is None` checks per column. Added 2 error-state tests to Tool 3.

### multi-source-append ✅
**Problem**: Multiple source files mapping to same target overwrote previous output.

**Fix**: Check if output exists, use it as base. First source uses template, subsequent sources accumulate.

### insert-mode-decouple ✅
**Problem**: `insert_rows` gated behind `page_break_enabled` — couldn't insert without A4 formatting.

**Fix**: Added `insert_mode` config key. Gate changed to `(page_break_enabled OR insert_mode)`.

### copy-cell-alignment ✅
**Problem**: Source cell alignment was copied, causing inconsistent formatting.

**Fix**: All pasted cells force center-aligned: `Alignment(horizontal='center', vertical='center')`.

### revert-to-v5-behavior ✅
Restored blank row scan, merged cell skip, paste_mode config after simplify-insert-logic was reverted.

### Previous fixes
| Fix | What |
|-----|------|
| merged-cell-fix | MergedCell guard in paste loop (doesn't crash) |
| merge-cell-debug | Debug logging for merged cell positions |
| pw-fill-cleanup-fix | PW column tied to NE_NO data boundary + temp column cleanup |
| ip-lookup-fix | IP regex handles wrapped formats |
| a4-print-fix | Defensive try/except on autoPageBreaks |

---

## What We're Trying To Do (Backlog)

These are known issues but have no plans yet:

| Priority | Issue | Detail |
|----------|-------|--------|
| 🟡 MEDIUM | Unify 3 matching.xlsx parsers | Error handling now consistent, but 3 separate implementations with different return types remain across tools 2/3/5 |
| 🟡 MEDIUM | Unify config injection | All 5 tools accept `main(config=None)` but path resolution differs |
| 🟡 MEDIUM | Fix `_parse_print_title_rows` bug + stale `/15` in tool 3 | `_parse_print_title_rows` duplicated between tools 3 & 5; tool 5 has global guard. Tool 3's `src/print_setup.py` still has hardcoded `/15` (same `_detect_row_height` fix pattern applies) |

---

## Pipeline Architecture

```
run.py orchestrates 5 tools sequentially via pipeline.json:

1-png-extractor     extracts PNGs from XLSX, copies → 5-png-inserter/input/
2-template-generator copies template per site, copies → 3-column-copier/target/
3-column-copier     copies 8 columns source→target, copies → 4-cell-editor/input/
4-cell-editor       prefix-match + replace text, copies → 5-png-inserter/xlsx/
5-png-inserter      inserts PNGs into XLSX → FINAL OUTPUT
```

---

## Test Coverage

| Tool | Tests |
|------|-------|
| 1-png-extractor | 38 |
| 2-template-generator | 15 |
| 3-column-copier | **53** (+10 image anchor shift tests) |
| 4-cell-editor | 15 |
| 5-png-inserter | 57 |
| run.py | 5 |
| Pipeline E2E | 1 |
| **Total** | **184** |

---

## Tool 3 — Current Behavior

### Config (`3-column-copier/config.json`)
```json
"paste_mode": "append",
"insert_mode": true,
"page_break_enabled": false,
"paste_start_row": 3
```

### Copy Logic (in order)
```
1. Multi-source: check output folder, load existing output if present
2. Blank row scan: find first completely empty row → paste_row (append mode)
3. Insert gate: paste_mode=="append" AND (page_break_enabled OR insert_mode)
4. Merged cell check: if overlap → WARNING + skip insert_rows
5. Insert rows: tws.insert_rows(paste_row, src_data_rows)
6. Shift image anchors: shift_image_anchors(tws, paste_row, src_data_rows)
7. Paste: copy values with force center alignment
8. Page-overflow snap: if gap > 0, insert_rows(paste_end, gap)
9. Shift image anchors (snap): shift_image_anchors(tws, paste_end, gap)
10. Cleanup: delete temp columns (Q,R,S) right-to-left
```

### Key Behaviors
| Feature | How |
|---------|-----|
| Multi-source append | Before loading target, check if output exists. If yes, use it as base. |
| Insert rows | Gated by OR: `page_break_enabled OR insert_mode`. Counts source rows, inserts at paste_row. |
| Image anchor shift | `shift_image_anchors(tws, row, n)` after BOTH `insert_rows` calls. OneCellAnchor + TwoCellAnchor, AbsoluteAnchor skip+warn. |
| Blank row scan | Scans ALL columns for emptiness. Steps past non-empty rows. |
| Merged cell safety | If merged cells overlap paste range → WARNING + skip insert. Does NOT crash. |
| Cell alignment | All pasted cells forced to center. Source alignment ignored. |
| IP lookup | Regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` on log sheet row 1. |
| PW fill range | Tied to NE_NO column via `lookup_col`. Stops where NE_NO ends. |
| Temp column cleanup | Auto-deletes Q,R,S right-to-left after copy. |
| MergedCell guard | Paste loop skips `MergedCell` instances (doesn't crash). |

---

## Tool 5 — A4 Row Height Fix

### Helper: `_detect_row_height(ws)`
- Scans rows 1 → `ws.max_row` for `ws.row_dimensions[r].height`
- Returns MODE (most common height) via `Counter.most_common`
- Falls back to `DEFAULT_ROW_HEIGHT` (15.0) when no explicit heights
- Uses openpyxl's native `pixels_to_points()` and `DEFAULT_ROW_HEIGHT`

### Formulas replaced
| Before | After |
|---|---|
| `math.ceil(printable_pts / 15)` | `math.ceil(printable_pts / _detect_row_height(ws))` |
| `int(display_h * 0.75 / 15) + 1` | `math.ceil(pixels_to_points(display_h) / _detect_row_height(ws))` |

---

## Image Anchor Shift — Detailed

### Helper: `shift_image_anchors(ws, insert_at_row, num_rows)` in `src/images.py`

**3 guards:**
- `num_rows <= 0` → no-op
- `insert_at_row < 1` → no-op (invalid Excel row)
- `not hasattr(ws, '_images')` → no-op (no images)

**Anchor type handling:**
| Type | Behavior |
|------|---------|
| OneCellAnchor | Shift `_from.row` if `>= insert_row_0` |
| TwoCellAnchor (entirely below) | Shift both `_from.row` and `to.row` |
| TwoCellAnchor (spanning) | Only shift `to.row` — image gets taller |
| AbsoluteAnchor | Skip with stderr warning |
| Unknown | Skip with stderr warning |

**0-based convention**: `AnchorMarker.row` is 0-based. Helper converts: `insert_row_0 = insert_at_row - 1`

**Verification:**
- 10 TDD unit tests (synthetic 1×1 PNGs, in-memory)
- Real-world test: TwoCellAnchor at rows 15-19 → shifted to 20-24 after `insert_rows(3, 5)` through full `copier.main()` run
- Save/reload persistence verified

---

## Remaining Technical Debt

| Issue | Severity | Detail |
|-------|----------|--------|
| Unify matching.xlsx parsers | 🟡 MEDIUM | 3 separate implementations with different return types (tools 2/3/5). Error handling now consistent. |
| Unify config injection | 🟡 MEDIUM | All 5 tools accept `main(config=None)` but path resolution differs |
| `_parse_print_title_rows` duplication | 🟡 MEDIUM | Duplicated between tools 3 & 5; tool 5 has global guard |
| Tool 3 `src/print_setup.py` hardcoded `/15` | 🟡 LOW | Same `_detect_row_height` fix pattern from tool 5 applies |

---

## Quick Start

```bash
pip install -r requirements.txt
python run.py                     # full pipeline

# Per-tool tests
cd 3-column-copier && python -m pytest tests/ -v       # 53
cd 5-png-inserter && python -m pytest tests/ -v        # 57
python -m pytest tests/test_run.py tests/test_pipeline_e2e.py -v  # 6

# Diagnostic
python scan-merges.py path/to/file.xlsx
```

---

## Key Details

| Detail | Value |
|--------|-------|
| Config pattern | `def main(config=None)` on all 5 tools |
| Matching format | matching.xlsx: Site + PW Number columns, blank Site inherits |
| PNG naming | `PW {planwork}_{prefix} {site}_{label}.png` |
| Matching error handling | All 3 tools raise `ValueError`: `"Column '{col}' not found in headers (row 1)"` |
| Row height detection | `_detect_row_height(ws)` — MODE of row heights, fallback 15.0 |
| Pixel conversion | `pixels_to_points()` from `openpyxl.utils.units` |
| Rows needed formula | `max(1, math.ceil(pixels_to_points(display_h) / row_ht))` |
| Page row calc | `math.ceil(769.89 / _detect_row_height(ws))` |
| Image anchor shift | `shift_image_anchors(ws, insert_at_row, num_rows)` — 3 guards, OneCell + TwoCell, AbsoluteAnchor skip+warn |
| Tool 3 output | `./output` |
| Tool 3 paste | Force center-aligned, values only |
| IP lookup | Regex on log sheet row 1 |
| Multi-source | Checks output folder; loads existing output as base |
| Insert mode | `insert_mode: true` enables row insertion independently of page breaks |
| Blank scan | Append mode scans all columns for completely empty rows |
| Merged cells | WARNING + skip insert; paste loop skips MergedCell |
| PW fill range | Tied to NE_NO column via `lookup_col` |
| Temp column cleanup | Auto-deletes Q,R,S right-to-left |
| Debug logging | Stderr: file/sheet info, row height, page_rows, snap decisions |
| Multi-record fixtures | 3 source files (16+8+5 rows) targeting e2e_v3_target.xlsx |