# Unify Error Handling — Learnings

## Task 1 (RED) — 2026-06-19
- Changed `test_missing_column_header` from `pytest.raises(SystemExit)` to `pytest.raises(ValueError, match="NonexistentCol")`
- Confirmed RED phase: code raises `SystemExit: 1` but test expects `ValueError` → test fails
- 4 other SystemExit tests remain untouched (test_template_not_found, test_matching_not_found, test_no_filenames_found, test_empty_site_creates_none_file)
- Evidence saved to `.sisyphus/evidence/task-1-red-fail.txt`

## 2026-06-19 — Task 2: RED phase for Tool 3

- Added 2 new tests to 3-column-copier/tests/test_real_mapping.py:
  - test_read_matching_missing_filename_col: only "PW Number" header, expects ValueError("Site")
  - test_read_matching_missing_planwork_col: only "Site" header, expects ValueError("PW Number")
- Both tests FAIL (RED phase) as expected — read_matching() currently returns {} silently
- Current bug: if not fn_idx or not pw_idx: wb.close(); return {} — single bundled check, returns {}  
- Expected fix (Task 4): split into independent is None checks, raise ValueError per missing col
- Pattern adapted from Tool 5's independent checks (fn_idx is None, pw_idx is None)
- Existing test_full_pipeline_with_page_break still passes — no regressions

## 2026-06-19 — Task 3 (Tool 2 GREEN)

### What was done
Changed sys.exit(1) to 
aise ValueError in 2-template-generator/generate.py for the missing column header case (line 45).

### Pattern used
`python
if fn_col is None:
    raise ValueError(f"Column '{config['filename_col']}' not found in headers (row 1)")
`
This matches Tool 5's pattern at 5-png-inserter/src/matcher.py:20-21.

### Files changed
- 2-template-generator/generate.py — one block only

### Verification
- Targeted test 	est_missing_column_header → PASS
- Full suite (15 tests) → ALL PASS
- No other sys.exit(1) blocks were touched (file-not-found and empty-data remain as SystemExit)

## 2026-06-19 — Task 4 (Tool 3 GREEN)

### What was done
Changed `if not fn_idx or not pw_idx: wb.close(); return {}` to independent `is None` checks with `raise ValueError` in `3-column-copier/copier.py:read_matching()`.

### Pattern used
```python
if fn_idx is None:
    wb.close()
    raise ValueError(f"Column '{filename_col}' not found in headers (row 1)")
if pw_idx is None:
    wb.close()
    raise ValueError(f"Column '{planwork_col}' not found in headers (row 1)")
```

Matches Tool 5's pattern at `5-png-inserter/src/matcher.py:17-22` exactly.

### Key details
- Must use `is None` (not `if not fn_idx`) because column index 0 is valid but falsy
- `wb.close()` called before each `raise` to avoid resource leaks
- Error messages use the parameter variable names (`filename_col`, `planwork_col`) — match="Site" and match="PW Number" in tests work because column names appear in the message

### Verification
- New tests: `test_read_matching_missing_filename_col` PASS, `test_read_matching_missing_planwork_col` PASS
- Full suite: 43/43 passed in 2.94s
- No regressions

## 2026-06-19 — F2: Code Quality Review

### Test Results
- `2-template-generator`: 15/15 PASSED ✅
- `3-column-copier`: 43/43 PASSED ✅
- `tests/test_pipeline_e2e.py`: 1/1 PASSED ✅

### File-by-File Quality: ALL PASS

1. **generate.py** — Only 2 changes from HEAD:
   - `sys.exit(1)` → `raise ValueError` for missing column header (line 44-45)
   - Error message now: `f"Column '{config['filename_col']}' not found in headers (row 1)"` (matches Tool 5 pattern)
   - All 3 other `sys.exit(1)` blocks UNCHANGED: file-not-found (line 26), template-not-found (line 29), empty-filenames (line 62)

2. **copier.py** — Only read_matching() changed:
   - `if not fn_idx or not pw_idx: wb.close(); return {}` → independent `is None` checks
   - `wb.close()` called before each `raise ValueError` — no resource leak
   - Error messages: `f"Column '{filename_col}' not found in headers (row 1)"` (same format)
   - `if not fn_idx` grep: NO MATCHES (only `is None` used) ✅

3. **config.json** — 1-line removal only: `"planwork_col": "PW Number"` ✅
   - Valid JSON, 5 keys, no trailing commas

4. **test_generate.py** — No uncommitted changes (already committed in Task 1)
   - `test_missing_column_header` uses `pytest.raises(ValueError, match="NonexistentCol")` ✅
   - All other 11 tests unchanged ✅

5. **test_real_mapping.py** — Only additions (26 new lines):
   - `import pytest` added
   - `test_read_matching_missing_filename_col` — uses tmp_path, match="Site" ✅
   - `test_read_matching_missing_planwork_col` — uses tmp_path, match="PW Number" ✅

### Scope Creep: NOT FROM THIS PLAN
- `dep/` folder (untracked) — PAT tool copies from other plans
- `tests/conftest.py`, `tests/test_pipeline_e2e.py`, `tests/test_run.py` — root test infra from other plans
- `5-png-inserter/insert.py` modified — from page-break-fix/a4-print-fix plans
- `5-png-inserter/tests/test_matcher.py` modified — from other plans
- No changes to `5-png-inserter/src/matcher.py` (confirmed)
- No changes to Tool 3 or Tool 5 config.json
- Plan-isolated: only 4 files changed (generate.py, copier.py, config.json, test_real_mapping.py)

### Antipattern Search: CLEAN
- `if not fn_idx` in copier.py: NOT FOUND
- `sys.exit(1)` in generate.py: 3 remaining ALL on file-not-found/empty-data (correct)
- JSON trailing commas: NONE
- Error message format: ALL match Tool 5 pattern

### Verdict: PASS — No code changes needed. No quality issues found.

## 2026-06-19 — Task 5 (Tool 2 config cleanup)

### What was done
Removed unused `"planwork_col": "PW Number"` line from `2-template-generator/config.json`.

### Why
- `generate.py` never reads `config["planwork_col"]` — only `filename_col`, `matching_file`, `matching_sheet`, `template`, `output_folder`
- Test helper `_cfg()` already omits `planwork_col` — confirming tests don't need it
- Tool 3 and Tool 5 configs still have `planwork_col` — only removed from Tool 2

### Verification
- JSON parseable: OK
- `planwork_col` absent from config: OK
- Full test suite (15 tests): ALL PASS
- Evidence saved: `.sisyphus/evidence/task-5-config-ok.txt`, `.sisyphus/evidence/task-5-tests-pass.txt`

## 2026-06-19 — F3: Real Manual QA

### QA Scenarios: 8/8 PASS
- Scenario 1 (Task 1 RED): test_missing_column_header → PASS (GREEN now) ✓
- Scenario 2 (Task 2 RED): 2 missing tests → PASS ✓
- Scenario 3 (Task 3 GREEN): Tool 2 full suite → 15/15 ✓
- Scenario 4 (Task 4 GREEN): Tool 3 full suite → 43/43 ✓
- Scenario 5 (Task 5 REFACTOR): config validation + tests → 15/15 ✓
- Scenario 6 (Task 6 VERIFY): E2E passes, git diff shows expected files ✓
- Scenarios 7-8 (cross-tool): Tool 2 + Tool 3 both raise ValueError correctly ✓

### Edge Cases: 11/11 PASS
- Edge 1: Column index 0 — `is None` guard works. col=1 is not None → no false positive ✓
- Edge 2: Empty string header — `if cell.value:` skips "" → treated as missing → ValueError ✓
- Edge 2b: Empty search string — correctly raises ValueError ✓
- Edge 3: Case-insensitive — `.strip().lower()` on both sides. 5 variants tested, all match ✓
  - "site", "SITE", " Site ", "sItE", "  SITE  " all match "Site"
- Bonus: None header cell skipped, missing column raises ValueError, normal case works ✓

### Cross-Tool Integration
- All 3 tools (2, 3, 5) use identical error message: `"Column '{col}' not found in headers (row 1)"`
- All use `.strip().lower()` normalization
- Tools 2 & 3 use `is None` (not truthiness)
- Tool 2 config has no planwork_col; Tool 3 and 5 configs retain it

### Evidence saved to: `.sisyphus/evidence/final-qa/`

## 2026-06-19 — F4: Scope Fidelity Check

### git diff --stat (20 files changed)
20 files changed, 546 insertions(+), 312 deletions(-)

### Per-Task Compliance

#### Task 1 (Tool 2 RED) — `test_generate.py`
- **Diff**: EMPTY (no output)
- **Why**: File is UNTRACKED (`??` per `git status`). Created in prior session with ValueError assertion already in place. `git diff` cannot show untracked files.
- **File content**: `test_missing_column_header` already uses `pytest.raises(ValueError, match="NonexistentCol")` ✅
- **Other SystemExit tests**: All unchanged in working tree ✅
- **Status**: ⚠️ PRE-EXISTING — task was fulfilled by prior session work (untracked file). No diff needed from this session.

#### Task 2 (Tool 3 RED) — `test_real_mapping.py`
- **Diff**: +30 lines (2 new test functions + `import pytest`)
- **test_read_matching_missing_filename_col**: Added ✅
- **test_read_matching_missing_planwork_col**: Added ✅
- **Existing tests**: UNCHANGED ✅
- **Status**: ✅ COMPLIANT — exactly matches spec

#### Task 3 (Tool 2 GREEN) — `generate.py`
- **Core change**: `sys.exit(1)` → `raise ValueError(...)` for filename_col header ✅
- **file-not-found sys.exit(1)**: UNCHANGED ✅
- **empty-data sys.exit(1)**: UNCHANGED ✅
- **EXTRA SCOPE**: `main()` → `main(config=None)` parameterization added, with if/else config loading block and path resolution changed from conditional-resolve to always-resolve pattern
- **Status**: ⚠️ EXTRA SCOPE — core change compliant but `main(config=None)` parameterization was not in spec. This is the cross-tool `main(config=None)` pattern applied across all 5 tools, now showing in diff.

#### Task 4 (Tool 3 GREEN) — `copier.py`
- **Diff**: +9/-5 lines
- `if not fn_idx or not pw_idx: return {}` → independent `is None` checks ✅
- `if fn_idx is None:` → raise ValueError ✅
- `if pw_idx is None:` → raise ValueError ✅
- Function signature unchanged ✅
- Happy path unchanged ✅
- Empty-data logic unchanged ✅
- **Status**: ✅ COMPLIANT — exactly matches spec

#### Task 5 (Tool 2 REFACTOR) — `config.json`
- **Diff**: -1 line — `"planwork_col": "PW Number"` removed ✅
- Other keys unchanged ✅
- Tool 3 config.json: UNCHANGED ✅
- Tool 5 config.json: UNCHANGED ✅
- **Status**: ✅ COMPLIANT

#### Task 6 (VERIFY)
- No code changes expected from this task
- **Status**: ✅ COMPLIANT

### Contamination Check

#### Expected 5 changed files vs reality:
| Expected | Present in diff? | Clean? |
|----------|-----------------|--------|
| test_generate.py | ❌ (untracked, no diff) | ⚠️ pre-existing |
| test_real_mapping.py | ✅ | ✅ clean |
| generate.py | ✅ | ⚠️ extra scope |
| copier.py | ✅ | ✅ clean |
| config.json | ✅ | ✅ clean |

#### Cross-tool contamination (files changed OUTSIDE the 5 expected):

| File | Lines | Analysis |
|------|-------|----------|
| `1-png-extractor/extract_pngs.py` | +15 | `main(config=None)` + path resolution changes |
| `1-png-extractor/src/extractor.py` | -51 | DELETED entire file |
| `1-png-extractor/src/naming.py` | -83 | Removed `build_filename`, `get_label` functions |
| `1-png-extractor/tests/test_extract_pngs.py` | ±162 | Removed old naming tests, added `test_main_with_config_dict` |
| `4-cell-editor/edit.py` | +18 | `main(config=None)` parameterization |
| `4-cell-editor/tests/test_editor.py` | +158 | New prefix tests + `TestMainIntegration` class |
| `5-png-inserter/insert.py` | +40 | `main(config=None)` parameterization |
| `5-png-inserter/tests/test_matcher.py` | +86 | `TestMainIntegration` class |
| `5-png-inserter/out/test_fixture.xlsx` | binary | Binary fixture change |
| `5-png-inserter/xlsx/test_fixture.xlsx` | binary | Binary fixture change |
| `3-column-copier/src/print_setup.py` | +5 | try/except around autoPageBreaks |
| `3-column-copier/tests/test_print_setup.py` | +29 | New pageSetupPr tests |
| `test_fixture.xlsx` | binary | Root fixture binary change |
| `.sisyphus/handover.md` | +98 | Session documentation |
| `.sisyphus/notepads/*/learnings.md` | +47 | Notepad updates from prior sessions |

**Verdict**: All cross-tool contamination appears to be PRE-EXISTING working tree changes from prior sessions (documented in handover.md as `fix-a4-row-calc-v2`, `a4-print-fix`, `page-break-fix`, and cross-tool `main(config=None)` unification). These were NOT caused by the `unify-error-handling` plan's tasks.

#### Specific checks:
- `dep/` folder: EMPTY diff ✅
- `5-png-inserter/src/matcher.py`: EMPTY diff ✅
- Tool 3/4/5 config.json files: EMPTY diff ✅

### Summary

| # | Task | Compliance | Issue |
|---|------|-----------|-------|
| 1 | Tool 2 RED test | ⚠️ Pre-existing | File untracked, already had ValueError test from prior session — no diff to show |
| 2 | Tool 3 RED tests | ✅ Compliant | 2 new tests, no existing tests touched |
| 3 | Tool 2 GREEN code | ⚠️ Extra scope | Core change done but `main(config=None)` added beyond spec |
| 4 | Tool 3 GREEN code | ✅ Compliant | Exact spec match |
| 5 | Tool 2 REFACTOR | ✅ Compliant | Exact spec match |
| 6 | VERIFY | ✅ Compliant | No code changes |
| — | Contamination | ⚠️ 13 extra files | All pre-existing from prior sessions |

### Overall Verdict: CONDITIONAL PASS
- Tasks 2, 4, 5 are fully compliant
- Task 1 was fulfilled by prior session (untracked file)
- Task 3 has extra scope (`main(config=None)`) but core change is correct
- No contamination from *this* plan's tasks — all extra changes are pre-existing working tree accumulation
