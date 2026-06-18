# Full Pipeline E2E — Test All 5 Tools + run.py + Integration

## TL;DR

> **Quick Summary**: Close all test coverage gaps across the 5-tool PAT pipeline. Fill unit test gaps (2-template-generator has 0 tests, 4-cell-editor sparse, XML parsing untested), add integration tests for each tool, create full-pipeline E2E tests, and test the run.py orchestrator.
>
> **Deliverables**:
> - Unit tests for 2-template-generator (0→~10 tests)
> - Unit tests for 4-cell-editor main() + edge cases (5→~12 tests)
> - Unit tests for 1-png-extractor XML parsing (new coverage)
> - Unit tests for 3-column-copier cleanup action (new coverage)
> - Integration tests for tools 1,2,4,5 via config injection
> - Full pipeline E2E tests (run.py with fixture data)
> - run.py unit tests (execution, failure, copy, edges)
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves of parallel work
> **Critical Path**: Prereqs → Unit tests wave → Integration wave → E2E wave → Final verification

---

## Context

### The Pipeline (5 tools via run.py)

```
run.py → reads pipeline.json → runs 5 stages sequentially:

1-png-extractor     extracts PNGs, copies → 5-png-inserter/input/
2-template-generator copies template, copies → 3-column-copier/target/
3-column-copier     copies 8 columns, copies → 4-cell-editor/input/
4-cell-editor       find-and-replace text, copies → 5-png-inserter/xlsx/
5-png-inserter      inserts PNGs into XLSX → FINAL OUTPUT
```

### Current Test Coverage

| Tool | Tests | Gaps |
|------|-------|------|
| 1-png-extractor | ~24 | XML drawing parsing (0), main() error paths |
| 2-template-generator | **0** | Entire tool untested |
| 3-column-copier | ~22 | Cleanup action, overwrite mode, error paths |
| 4-cell-editor | 5 | main(), multi-worksheet, multi-prefix, edge cases |
| 5-png-inserter | ~43 | main(), PNG matching edge cases |
| run.py | **0** | Pipeline orchestrator untested |
| **Integration** | **0** | No cross-tool E2E tests |

### Cross-Cutting Issues (from Metis + explore + librarian)

1. **Duplicated A4 print code** — `_setup_a4_print`, `_calc_page_rows`, `_parse_print_title_rows` exist in both tool 3 and tool 5. They have **diverged**: tool 5 has a global-flag bug (says `autoPageBreaks=False` when it's actually `True`), different `header_count` semantics (`end` vs `end-start+1`), and missing overflow guard.
2. **Three different matching.xlsx parsers** — tools 2, 3, 5 all parse matching.xlsx differently (list vs dict vs dict-of-lists). Integration tests must verify consistency.
3. **Dead code** — `1-png-extractor/src/extractor.py` (unused), `naming.py:build_filename()` and `get_label()` (superseded).
4. **Config injection inconsistency** — only tool 3 supports `main(config=None)`. Others read from disk, making unit testing fragile.
5. **Critical edge case in tool 2**: `str(None)` becomes `"None"` string when empty Site cell processed, creating a "None.xlsx" file.

### Metis Review

**Identified Gaps** (addressed):
- **Config injection**: Task 0 refactors tools 1,2,4,5 to accept optional config dicts
- **Dead code removal**: Prerequisites task removes extractor.py + old naming functions
- **A4 divergence**: Documented as known issue; test both versions independently
- **matching.xlsx consistency**: Integration tests verify all 3 parsers agree
- **Tool 2 "None" bug**: Unit test covers the `str(None)` edge case
- **Priority ordering**: P0 (tool 2, run.py) first, P1 (XML parsing, cleanup) second, P2 (4-cell-editor edges) third

---

## Work Objectives

### Core Objective
Achieve comprehensive test coverage across all 5 pipeline tools, the run.py orchestrator, and cross-tool integration, filling every identified gap.

### Concrete Deliverables
- `2-template-generator/tests/test_generate.py` — unit + integration tests
- `4-cell-editor/tests/test_editor.py` — expanded tests
- `1-png-extractor/tests/test_drawing.py` — XML parsing unit tests
- `3-column-copier/tests/test_cleanup.py` — cleanup action tests
- `tests/test_run.py` — run.py orchestrator tests
- `tests/test_pipeline_e2e.py` — full pipeline E2E test
- All new tests pass alongside existing ~94 tests

### Definition of Done
- [ ] 2-template-generator: 10+ tests, all pass
- [ ] 4-cell-editor: 12+ tests (up from 5), all pass
- [ ] 1-png-extractor: XML parsing tests added, all pass
- [ ] 3-column-copier: cleanup action tested, all pass
- [ ] run.py: 4+ tests (happy path, failure, copy, empty), all pass
- [ ] Pipeline E2E: 1+ test exercising full run.py flow, passes
- [ ] All ~100+ existing tests still pass
- [ ] Dead code removed (extractor.py, old naming functions)

### Must Have
- Every tool's `main()` testable via config injection (refactor tools 1,2,4,5)
- Unit tests for every previously uncovered function
- At least 1 integration test per tool exercising main() end-to-end
- At least 1 full pipeline E2E test
- run.py tested for happy path + error propagation + file copy + empty stages
- All tests use `tmp_path` fixture (no file system pollution)
- Test data generated programmatically (no pre-committed .xlsx/.png fixtures)

### Must NOT Have (Guardrails)
- No testing of dead code (remove it first, then no need to test)
- No mocking of openpyxl — use real Workbooks and tmp_path
- No CI/CD pipeline setup
- No property-based/fuzz testing
- No "extracted shared test utility" module — each tool's tests self-contained
- No over-testing of already-well-covered functions
- No docstring mandates for test methods

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES — pytest with tmp_path, conftest.py per tool
- **Automated tests**: Yes (test-first for new coverage, tests-after for refactored tools)
- **Framework**: pytest + openpyxl
- **Agent-Executed QA**: Run pytest suites, verify output, capture evidence

### QA Policy
Evidence saved to `.sisyphus/evidence/full-pipeline-e2e/`.

- **Unit tests**: `python -m pytest tests/ -v` per tool directory
- **Integration**: Subprocess run of tool entry scripts with temp configs
- **E2E**: Subprocess run of `run.py` with temp pipeline.json + fixtures
- **Cell verification**: Python one-liners via Bash for output .xlsx verification

---

## Execution Strategy

### Task Waves

```
Wave 0 (Prerequisites — START FIRST, unblocks everything):
├── Task 0: Remove dead code + refactor main() for config injection

Wave 1 (Unit tests — MAX PARALLEL, 4 tasks):
├── Task 1: 2-template-generator unit tests (0→10+)
├── Task 2: 4-cell-editor expanded tests (5→12+)
├── Task 3: 1-png-extractor XML parsing tests
└── Task 4: 3-column-copier cleanup action tests

Wave 2 (Integration + E2E — depends on Wave 1):
├── Task 5: Tool integration tests (tools 1,2,4,5 via config injection)
├── Task 6: run.py tests (execution, failure, copy, edges)
└── Task 7: Full pipeline E2E test

Wave FINAL (After ALL tasks):
├── F1: Plan Compliance Audit (oracle)
├── F2: Test Quality Review (unspecified-high)
├── F3: Real Manual QA (unspecified-high)
└── F4: Scope Fidelity Check (deep)
```

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 0. **Prerequisites — Remove dead code + refactor main() for config injection**

  **What to do**:
  - A. Delete dead code:
    - `1-png-extractor/src/extractor.py` — entire file (unused, superseded by inline code in extract_pngs.py)
    - `1-png-extractor/src/naming.py`: Remove `build_filename()` function (superseded by `build_pw_filename()`)
    - `1-png-extractor/src/naming.py`: Remove `get_label()` function (superseded by `get_label_with_row()`)
  - B. Refactor `main()` to accept optional config for tools that don't yet:
    - `1-png-extractor/extract_pngs.py`: `def main(config=None)` — if config dict provided, use it; else read from config.json
    - `2-template-generator/generate.py`: `def main(config=None)` — same pattern
    - `4-cell-editor/edit.py`: `def main(config=None)` — same pattern
    - `5-png-inserter/insert.py`: `def main(config=None)` — same pattern
    - All 4 follow the exact same pattern as `3-column-copier/copier.py:42-58`
  - Verify: All existing tests still pass after changes

  **Must NOT do**:
  - Do NOT change any tool behavior — config injection is purely additive
  - Do NOT delete `_local_find` / `_local_findall` from extract_pngs.py
  - Do NOT touch any test files
  - Do NOT refactor duplicated A4 code (document it, don't fix it here)

  **QA**:
  ```
  Scenario: All existing tests still pass after refactor
    Tool: Bash
    Steps: Run pytest for all 5 tools
    Expected: All existing tests pass, 0 failures
  ```

  **Commit**: `chore: remove dead code, refactor main() for testability`

- [x] 1. **2-template-generator unit tests** (0→10+ tests)

  **What to do**:
  - Create `2-template-generator/tests/__init__.py` and `2-template-generator/tests/test_generate.py`
  - Create `2-template-generator/conftest.py` (sys.path setup, same pattern as other tools)
  - Tests (minimum 10):
    1. `test_generates_from_matching` — 3 rows, 2 unique sites → 2 output files
    2. `test_blank_site_inherits` — blank Site cell inherits from above
    3. `test_appends_xlsx_suffix` — filename without .xlsx gets suffix
    4. `test_already_has_xlsx_suffix` — filename with .xlsx stays
    5. `test_template_not_found` — exits 1
    6. `test_matching_not_found` — exits 1
    7. `test_no_filenames_found` — empty matching → exits 1
    8. `test_empty_site_creates_none_file` — BUG: `str(None)` becomes "None.xlsx" (document as known issue)
    9. `test_skip_duplicate_filenames` — same filename appears twice → only one output
    10. `test_generate_with_config_dict` — test using `main(config=test_config)` injection
  - Use `tmp_path` fixture for isolated file I/O
  - Create minimal matching.xlsx + template.xlsx programmatically via openpyxl

  **References**:
  - `3-column-copier/tests/test_columns.py` — existing test patterns
  - `2-template-generator/generate.py` — the tool to test
  - `3-column-copier/conftest.py` — conftest pattern to follow

  **QA**:
  ```
  Scenario: All template-generator tests pass
    Tool: Bash
    Steps: cd 2-template-generator && python -m pytest tests/ -v
    Expected: 10+ passed, 0 failed
  ```

  **Commit**: `test(template-generator): add unit + integration tests`

- [x] 2. **4-cell-editor expanded tests** (5→12+ tests)

  **What to do**:
  - Expand `4-cell-editor/tests/test_editor.py` with 7+ new tests:
    1. `test_multiple_prefixes` — 3 replacement prefixes in one workbook, all applied
    2. `test_multi_worksheet` — replacements applied across 2 sheets
    3. `test_main_with_config_dict` — full integration via `main(config=test_config)` injection
    4. `test_main_empty_replacements` — exits 1 with stderr message
    5. `test_main_missing_input_folder` — exits 2 with stderr message  
    6. `test_thai_unicode_replacements` — Thai text in prefix (config has `ชื่อ`, `วันที่`)
    7. `test_overlapping_prefixes` — prefix "name:" and "name_detailed:" — first wins in "first" mode
  - Keep existing 5 tests unchanged

  **Must NOT do**:
  - Do NOT change existing test logic — only add new tests
  - Do NOT modify editor.py logic (test behavior as-is)

  **QA**:
  ```
  Scenario: All cell-editor tests pass
    Tool: Bash
    Steps: cd 4-cell-editor && python -m pytest tests/ -v
    Expected: 12+ passed, 0 failed
  ```

  **Commit**: `test(cell-editor): expand test coverage 5→12`

- [x] 3. **1-png-extractor XML parsing tests**

  **What to do**:
  - Create `1-png-extractor/tests/test_drawing.py` with tests for previously untested XML/drawing functions:
    1. `test_find_drawing_path_has_drawing` — sheet with drawing relationship returns path
    2. `test_find_drawing_path_no_drawing` — sheet without drawing returns None
    3. `test_parse_drawing_image_map_two_cell_anchor` — parses twoCellAnchor with row/col
    4. `test_parse_drawing_image_map_one_cell_anchor` — parses oneCellAnchor
    5. `test_parse_drawing_image_map_no_drawing` — empty drawing returns {}
    6. `test_local_find` — finds element by local tag name
    7. `test_local_findall` — finds all elements by local tag name
  - Create a minimal test XLSX fixture with embedded images (use openpyxl `ws.add_image()`)
  - Test functions are in `extract_pngs.py` — import directly from there

  **Must NOT do**:
  - Do NOT modify extract_pngs.py (just import and test existing functions)
  - Do NOT delete the existing integration test

  **QA**:
  ```
  Scenario: All png-extractor tests pass (existing + new)
    Tool: Bash
    Steps: cd 1-png-extractor && python -m pytest tests/ -v
    Expected: 30+ passed, 0 failed
  ```

  **Commit**: `test(png-extractor): add XML drawing parsing unit tests`

- [x] 4. **3-column-copier cleanup action tests**

  **What to do**:
  - Create `3-column-copier/tests/test_cleanup.py` with tests for `action="cleanup"`:
    1. `test_cleanup_deletes_build_at_columns` — config with build_at:Q,R,S, verify Q,R,S deleted from source
    2. `test_cleanup_preserves_data_columns` — columns C,D,E,G,H intact after cleanup
    3. `test_cleanup_with_backward_compat` — config without build_at, falls back to deleting paste_to columns
    4. `test_cleanup_empty_source_folder` — no files → no error, exit 0
  - Use `main(config=test_config)` with `action: "cleanup"`
  - Create minimal source XLSX with both data and temp columns

  **QA**:
  ```
  Scenario: All copier tests pass (existing + new)
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/ -v
    Expected: 28+ passed, 0 failed
  ```

  **Commit**: `test(column-copier): add cleanup action tests`

- [x] 5. **Tool integration tests** (tools 1,2,4,5 via config injection)

  **What to do**:
  - Add integration tests that exercise each tool's `main()` end-to-end with config injection:
  - **Tool 1** (`test_extract_pngs.py`): Add `test_main_with_config_dict` — creates XLSX with embedded image, extracts via config injection, verifies PNG filename matches convention
  - **Tool 2** (`test_generate.py`): Already covered by Task 1's `test_generate_with_config_dict`
  - **Tool 4** (`test_editor.py`): Already covered by Task 2's `test_main_with_config_dict`
  - **Tool 5** (`test_matcher.py` or new file): Add `test_main_with_config_dict` — creates matching.xlsx, XLSX, and PNGs in tmp dirs, runs main() with config dict, verifies output XLSX has image inserted
  - Each test creates all necessary fixture files in `tmp_path` programmatically

  **Must NOT do**:
  - Do NOT add config injection tests for tool 3 (already tested via test_real_mapping.py)
  - Do NOT test via subprocess — use in-process `main(config=...)`

  **QA**:
  ```
  Scenario: All integration tests pass
    Tool: Bash
    Steps: Run pytest for tools 1,2,4,5 with --verbose
    Expected: New integration tests pass alongside existing tests
  ```

  **Commit**: `test: add main() integration tests for tools 1,4,5`

- [x] 6. **run.py orchestrator tests**

  **What to do**:
  - Create `tests/test_run.py` at project root
  - Create `tests/conftest.py` at project root (adds root to sys.path)
  - Tests (minimum 4):
    1. `test_runs_all_stages` — pipeline.json with no-op stages (echo commands), all succeed
    2. `test_stops_on_failure` — stage 2 exits 1, stage 3 never runs
    3. `test_copies_files_between_stages` — stage 1 creates files, stage 2 sees them in input
    4. `test_handles_empty_stage` — stage produces no output, copy prints "Copied 0 files" without error
    5. `test_missing_pipeline_json` — exits with error
  - Use `tmp_path` for pipeline.json and working directories
  - Run `run.py` via subprocess with `cwd=tmp_path`
  - Mock pipeline stages to be fast no-ops (e.g., `echo stage1 && echo done`)

  **Must NOT do**:
  - Do NOT run the actual PAT tools during run.py tests (use no-op commands)
  - Do NOT modify run.py

  **QA**:
  ```
  Scenario: All run.py tests pass
    Tool: Bash
    Steps: cd project-root && python -m pytest tests/test_run.py -v
    Expected: 4+ passed, 0 failed
  ```

  **Commit**: `test(run): add pipeline orchestrator tests`

- [x] 7. **Full pipeline E2E test**

  **What to do**:
  - Create `tests/test_pipeline_e2e.py` at project root
  - Single comprehensive test that:
    1. Creates a complete fixture set in `tmp_path`:
       - `matching.xlsx` with 1 site → 1 planwork
       - `template.xlsx` for tool 2 (minimal template)
       - Source XLSX with cutsheet data + embedded images for tool 1
       - Target XLSX for tool 3
       - Realistic `pipeline.json` pointing to tmp_path directories
    2. Runs `run.py` via subprocess
    3. Verifies:
       - Stage 1: PNGs extracted with correct naming (`PW {pw}_{prefix} {site}_{label}.png`)
       - Stage 2: Template copied to correct filename
       - Stage 3: Target XLSX has all 8 columns pasted correctly
       - Stage 4: Replacement text applied (verify at least 1 cell changed)
       - Stage 5: Final output XLSX exists with images inserted
    4. Verifies file copy between ALL stages
    5. Verifies run.py exits 0
  - Use `tmp_path` for ALL files (no real file system pollution)

  **Must NOT do**:
  - Do NOT run real tools during test if their dependencies (template, source data) are missing
  - Generate all fixtures programmatically within the test
  - Keep the test to 1 verifiable flow (not 10 edge case variations)

  **QA**:
  ```
  Scenario: Full pipeline runs end-to-end
    Tool: Bash
    Steps: cd project-root && python -m pytest tests/test_pipeline_e2e.py -v --timeout=60
    Expected: 1 passed, 0 failed. run.py exit 0. All stage outputs verified.
  ```

  **Commit**: `test(e2e): add full pipeline integration test`

> 4 review agents run in PARALLEL. ALL must APPROVE.

- [x] F1. **Plan Compliance Audit** — `oracle`
- [x] F2. **Test Quality Review** — `unspecified-high`
- [x] F3. **Real Manual QA** — `unspecified-high`
- [x] F4. **Scope Fidelity Check** — `deep`

---

## Commit Strategy

| # | Commit Message | Files |
|---|---------------|-------|
| 1 | `chore: remove dead code, refactor main() for testability` | extractor.py, naming.py, edit.py, generate.py, extract_pngs.py, insert.py |
| 2 | `test(template-generator): add unit + integration tests` | tests/test_generate.py |
| 3 | `test(cell-editor): expand test coverage 5→12` | tests/test_editor.py |
| 4 | `test(png-extractor): add XML drawing parsing unit tests` | tests/test_drawing.py |
| 5 | `test(column-copier): add cleanup action tests` | tests/test_cleanup.py |
| 6 | `test(run): add pipeline orchestrator tests` | tests/test_run.py |
| 7 | `test(e2e): add full pipeline integration test` | tests/test_pipeline_e2e.py |

---

## Success Criteria

```bash
# All test suites pass (per tool)
cd 1-png-extractor && python -m pytest tests/ -v          # 24+ tests pass
cd 2-template-generator && python -m pytest tests/ -v     # 10+ tests pass
cd 3-column-copier && python -m pytest tests/ -v          # 24+ tests pass
cd 4-cell-editor && python -m pytest tests/ -v            # 12+ tests pass
cd 5-png-inserter && python -m pytest tests/ -v           # 45+ tests pass

# run.py + E2E tests (from project root)
python -m pytest tests/test_run.py -v                      # 4+ tests pass
python -m pytest tests/test_pipeline_e2e.py -v             # 1+ tests pass
```
