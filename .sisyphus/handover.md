# Handover — PAT Tool Sessions (Updated)

> **Date**: 2026-06-18 | **Sessions**: full-pipeline-e2e ✅ | cli-integration-tests ✅ | zip-distribution ✅ | a4-print-fix ✅ | ip-lookup-fix ✅ | merged-cell-fix ✅ | merge-cell-debug ✅ | pw-fill-cleanup-fix ✅ | multi-source-append ✅ | insert-mode-decouple ✅ | simplify-insert-logic ✅ (reverted) | revert-to-v5-behavior ✅ | copy-cell-alignment ✅

---

## ⚠️ Current Issues

| Priority | Issue | Plan |
|----------|-------|------|
| 🔴 HIGH | A4 page break: images break across pages due to hardcoded row height (15pt) and pixel ratio (0.75) | `.sisyphus/plans/fix-a4-row-calc.md` |
| 🟡 MEDIUM | Image anchors don't shift with insert_rows in tool 3 | `.sisyphus/plans/shift-image-anchors.md` |

---

## What's Next

| Priority | Task | Plan |
|----------|------|------|
| 🔴 NOW | Fix A4 page break row calculation in tool 5 | `.sisyphus/plans/fix-a4-row-calc.md` |
| 🟡 Later | Fix `_parse_print_title_rows` bug in tool 5 | Not planned |
| 🟡 Later | Unify 3 matching.xlsx parsers | Not planned |
| 🟡 Later | Unify config injection across tools | Not planned |
| 🟡 Later | Shift image anchors on insert_rows in tool 3 | `.sisyphus/plans/shift-image-anchors.md` |

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

---

## 2. Test Coverage

| Tool | Tests |
|------|-------|
| 1-png-extractor | 38 |
| 2-template-generator | 15 |
| 3-column-copier | **41** (+3 from original: insert_mode tests) |
| 4-cell-editor | 15 |
| 5-png-inserter | 51 |
| run.py | 5 |
| Pipeline E2E | 1 |
| **Total** | **166** |

---

## 3. Tool 3 — Current Behavior

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
5. Paste: copy values with force center alignment
6. Cleanup: delete temp columns (Q,R,S) right-to-left
```

### Key Behaviors
| Feature | How |
|---------|-----|
| Multi-source append | Before loading target, check if output exists. If yes, use it as base. |
| Insert rows | Gated by OR: `page_break_enabled OR insert_mode`. Counts source rows, inserts at paste_row. |
| Blank row scan | Scans ALL columns for emptiness. Steps past non-empty rows. |
| Merged cell safety | If merged cells overlap paste range → WARNING + skip insert. Does NOT crash. |
| Cell alignment | All pasted cells forced to `horizontal='center', vertical='center'`. Source alignment ignored. |
| IP lookup | Regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` on log sheet row 1. |
| PW fill range | Tied to NE_NO column via `lookup_col`. Stops where NE_NO ends. |
| Temp column cleanup | Auto-deletes Q,R,S right-to-left after copy. |
| MergedCell guard | Paste loop skips `MergedCell` instances (doesn't crash). |

---

## 4. What We Fixed

### 4.1 multi-source-append ✅
When multiple source files map to the same target, each source loads the clean template — overwriting previous output. Fix: check if output already exists, use it as base. First source uses template, subsequent sources accumulate.

### 4.2 insert-mode-decouple ✅
`insert_rows` was gated behind `page_break_enabled` — couldn't insert without A4 formatting. Fix: added `insert_mode` config key. Gate changed to `(page_break_enabled OR insert_mode)`.

### 4.3 simplify-insert-logic (reverted) ✅
Removed blank scan, merged check, paste_mode to simplify. User preferred V5 behavior — reverted.

### 4.4 revert-to-v5-behavior ✅
Restored blank row scan, merged cell skip, paste_mode config. Kept multi-source append and insert_mode decoupling.

### 4.5 copy-cell-alignment ✅
Changed from copying source alignment to force center-aligning all pasted cells: `Alignment(horizontal='center', vertical='center')`.

### Previous fixes (from prior sessions)
- merged-cell-fix: MergedCell guard in paste loop
- merge-cell-debug: Debug logging for merged cell positions
- pw-fill-cleanup-fix: PW column tied to NE_NO data boundary + temp column cleanup
- ip-lookup-fix: IP regex handles wrapped formats
- a4-print-fix: Defensive try/except on autoPageBreaks

---

## 5. Remaining Technical Debt

| Issue | Severity | Detail |
|-------|----------|--------|
| A4 page break row calc | 🔴 HIGH | `_calc_page_rows` and `insert_png` use hardcoded 15pt row height + 0.75 pixel ratio. Causes image break across pages. Plan: `.sisyphus/plans/fix-a4-row-calc.md` |
| Image anchor shift | 🟡 MEDIUM | openpyxl `insert_rows` doesn't shift image anchors. Images stay frozen while cells move. Plan: `.sisyphus/plans/shift-image-anchors.md` |
| A4 print code diverged | 🟡 MEDIUM | `_parse_print_title_rows` duplicated between tools 3 & 5; tool 5 has global `_a4_print_setup_done` guard |
| Three matching.xlsx parsers | 🟡 MEDIUM | Tool 2 (inline, `list[str]`), Tool 3 (`{pw→filename}`), Tool 5 (`{filename→[pw]}`) |
| Config injection not unified | 🟡 MEDIUM | All 5 tools accept `main(config=None)` but path resolution differs |

---

## 6. Quick Start

```bash
pip install -r requirements.txt
python run.py                     # full pipeline

# Per-tool tests
cd 3-column-copier && python -m pytest tests/ -v       # 41
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
| Tool 3 paste | Force center-aligned, values only (no formatting) |
| IP lookup | Regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` on log sheet row 1 |
| Multi-source | Checks output folder; loads existing output as base if present |
| Insert mode | `insert_mode: true` enables row insertion independently of page breaks |
| Blank scan | Append mode scans all columns for completely empty rows |
| Merged cells | WARNING + skip insert (doesn't crash); paste loop skips MergedCell |
| PW fill range | Tied to NE_NO column via `lookup_col` parameter |
| Temp column cleanup | Auto-deletes Q,R,S right-to-left after copy |
| Debug logging | Stderr: file/sheet info, merge overlap warnings, MergedCell skip positions |
| Multi-record fixtures | 3 source files (16+8+5 rows) targeting e2e_v3_target.xlsx |
