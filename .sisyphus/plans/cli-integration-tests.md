# CLI Integration Tests — Run All 5 Tools Like a User Would

## TL;DR

> **Quick Summary**: Add CLI-level tests for all 5 tools — each runs its entry script via `subprocess` with real `config.json` files in isolated `tmp_path`, simulating exactly what a user types at the command line.
>
> **Deliverables**:
> - 5 new `tests/test_cli.py` files (one per tool)
> - ~15 tests total: 1 happy path + 2 error cases per tool
> - All fixtures created programmatically via openpyxl (no committed .xlsx/.png)
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 5 parallel tasks (one per tool)
> **Critical Path**: None — all independent

---

## Context

### Original Request
User wants CLI-level tests that simulate real user behavior — running each tool's entry script via subprocess with real config.json files, rather than calling `main(config=...)` in-process.

### Current Gap
All 139 existing tests use in-process `main(config=...)` injection. No test runs the actual entry script via `python extract_pngs.py` etc. from a command line.

### Metis Review Key Findings
1. **Directory structure**: Tools 2, 3, 5 reference `../matching.xlsx` — must nest them in subdirectories of tmp_path with matching.xlsx at root
2. **autoPageBreaks crash risk**: Creating all fixtures via openpyxl.Workbook() avoids the openpyxl `_parent is None` bug
3. **Tool 3 is an outlier**: Returns exit 0 even on errors — must verify stderr content, not exit code
4. **noise_threshold**: Tool 1's default 5000 filters out small test PNGs — must set to 0 in test config
5. **Tool 5 output folder**: Uses `./out` (not `./output` like other tools)
6. **Exit code conventions differ**: Tools 1&4 use exit 2 for missing input, exit 1 for config errors; Tool 2 uses exit 1 for everything; Tool 3 uses exit 0 with stderr warnings

---

## Work Objectives

### Core Objective
Add CLI-level subprocess tests for all 5 pipeline tools, verifying each tool's entry script runs correctly from the command line with real config.json files.

### Concrete Deliverables
- `1-png-extractor/tests/test_cli.py` — 3 tests
- `2-template-generator/tests/test_cli.py` — 3 tests
- `3-column-copier/tests/test_cli.py` — 3 tests
- `4-cell-editor/tests/test_cli.py` — 3 tests
- `5-png-inserter/tests/test_cli.py` — 3 tests

### Definition of Done
- [ ] All 5 `test_cli.py` files created with 3 tests each
- [ ] Happy path per tool: exit 0, output files exist, stdout contains expected text
- [ ] Error case 1: config.json missing → correct exit code + stderr message
- [ ] Error case 2: input folder missing → correct exit code + stderr message
- [ ] All existing 139 tests still pass
- [ ] Each CLI test runs in <10 seconds

### Must Have
- Subprocess execution of entry scripts (e.g., `python extract_pngs.py`)
- All fixtures created in tmp_path (no committed fixture files)
- Nested directory structure for tools referencing `../matching.xlsx`
- Correct exit code verification per tool's convention
- stdout AND stderr content verification
- Output file existence and validity verification

### Must NOT Have (Guardrails)
- No modification to real config.json files (all test configs in tmp_path)
- No copying real Excel files from the repo (all fixtures via openpyxl.Workbook())
- No testing Tool 3's `cleanup` action (destructive, needs separate isolation)
- No cross-tool pipeline testing (already covered by test_pipeline_e2e.py)
- No run.py CLI tests (already covered by test_run.py)
- No modification to production code

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES — pytest + tmp_path + subprocess
- **Automated tests**: Test-first (write tests, verify they pass)
- **Framework**: pytest + subprocess + openpyxl

### QA Policy
Every task includes Agent-Executed QA scenarios using Bash to run the CLI test and verify output.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (ALL 5 PARALLEL — independent):
├── Task 1: 1-png-extractor CLI tests
├── Task 2: 2-template-generator CLI tests
├── Task 3: 3-column-copier CLI tests
├── Task 4: 4-cell-editor CLI tests
└── Task 5: 5-png-inserter CLI tests
```

---

## TODOs

> EVERY task: 3 tests (happy path + 2 error cases), subprocess execution, tmp_path isolation.

- [x] 1. **1-png-extractor CLI tests** — `tests/test_cli.py`

  **What to do**:
  - Create `1-png-extractor/tests/test_cli.py`
  - Copy `extract_pngs.py` + `src/` into `tmp_path/tool1/`
  - Create `config.json` with `{"input_folder": "./input", "output_folder": "./output", "noise_threshold": 0}`
  - Tests:
    1. `test_happy_path` — Create XLSX in `input/` with embedded 1x1 PNG + "PW XX001" sheet + "exist TestSite" sheet with label. Run `python extract_pngs.py`. Verify exit 0, stdout contains "Done", output/*.png exists with correct naming.
    2. `test_missing_config` — No config.json in tool dir. Run script. Verify exit 1 (config.py raises SystemExit), stderr contains error.
    3. `test_missing_input_folder` — Valid config but `./input` doesn't exist. Verify exit 2, stderr contains "Input folder not found".

  **Must NOT do**: Do NOT backup/restore real config.json. Do NOT use real XLSX fixtures.

  **QA**:
  ```
  Scenario: All CLI tests pass
    Tool: Bash
    Steps: cd 1-png-extractor && python -m pytest tests/test_cli.py -v
    Expected: 3 passed, 0 failed
  ```

  **Commit**: `test(png-extractor): add CLI integration tests`

- [x] 2. **2-template-generator CLI tests** — `tests/test_cli.py`

  **What to do**:
  - Create `2-template-generator/tests/test_cli.py`
  - Directory structure: `tmp_path/matching.xlsx` + `tmp_path/tool2/` with `generate.py` + `config.json` + `template.xlsx`
  - Config: `{"matching_file": "../matching.xlsx", "matching_sheet": "match", "filename_col": "Site", "planwork_col": "PW Number", "template": "./template.xlsx", "output_folder": "./output"}`
  - Tests:
    1. `test_happy_path` — Create matching.xlsx with "TestSite"→"XX001", template.xlsx (Workbook with "Header" in A1). Run `python generate.py`. Verify exit 0, stdout contains "Done", output/TestSite.xlsx exists with "Header" content.
    2. `test_missing_config` — No config.json. Verify exit 1 (FileNotFoundError from json.load), stderr contains error traceback.
    3. `test_missing_template` — Valid config but template.xlsx doesn't exist. Verify exit 1, stderr contains "Template file not found".

  **QA**:
  ```
  Scenario: All CLI tests pass
    Tool: Bash
    Steps: cd 2-template-generator && python -m pytest tests/test_cli.py -v
    Expected: 3 passed, 0 failed
  ```

  **Commit**: `test(template-generator): add CLI integration tests`

- [x] 3. **3-column-copier CLI tests** — `tests/test_cli.py`

  **What to do**:
  - Create `3-column-copier/tests/test_cli.py`
  - Directory structure: `tmp_path/matching.xlsx` + `tmp_path/tool3/` with `copier.py` + `src/` + `config.json` + `source/` + `target/`
  - Config: `action: "copy"`, `paste_mode: "overwrite"`, minimal columns (1 planwork + 1 copy), `page_break_enabled: false`, `print_title_rows: null`
  - Tests:
    1. `test_happy_path` — Create source XLSX with "PW XX001" sheet + "Cutsheet" sheet (data rows), matching.xlsx with planwork→filename mapping, target XLSX in target/ matching the filename. Run `python copier.py`. Verify exit 0, stdout contains "Processing", output/ has XLSX.
    2. `test_missing_config` — No config.json. Verify non-zero exit (json.load FileNotFoundError).
    3. `test_missing_source_folder` — Valid config but source/ doesn't exist. Tool 3 returns exit 0 silently (no files to process). Verify exit 0, stdout shows no files processed.

  **Must NOT do**: Do NOT test cleanup action (destructive). Do NOT copy real matching.xlsx.

  **QA**:
  ```
  Scenario: All CLI tests pass
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/test_cli.py -v
    Expected: 3 passed, 0 failed
  ```

  **Commit**: `test(column-copier): add CLI integration tests`

- [x] 4. **4-cell-editor CLI tests** — `tests/test_cli.py`

  **What to do**:
  - Create `4-cell-editor/tests/test_cli.py`
  - Copy `edit.py` + `src/` into `tmp_path/tool4/` with config.json
  - Config: `{"input_folder": "./input", "output_folder": "./output", "match_mode": "first", "replacements": {"name:": "kacha"}}`
  - Tests:
    1. `test_happy_path` — Create XLSX in input/ with cell A1="name:", B1="old". Run `python edit.py`. Verify exit 0, stdout contains "Done", output XLSX has B1="kacha".
    2. `test_missing_config` — No config.json. Verify exit 1 (json.load FileNotFoundError).
    3. `test_missing_input_folder` — Valid config but input/ doesn't exist. Verify exit 2, stderr contains "Input folder not found".

  **QA**:
  ```
  Scenario: All CLI tests pass
    Tool: Bash
    Steps: cd 4-cell-editor && python -m pytest tests/test_cli.py -v
    Expected: 3 passed, 0 failed
  ```

  **Commit**: `test(cell-editor): add CLI integration tests`

- [x] 5. **5-png-inserter CLI tests** — `tests/test_cli.py`

  **What to do**:
  - Create `5-png-inserter/tests/test_cli.py`
  - Directory structure: `tmp_path/matching.xlsx` + `tmp_path/tool5/` with `insert.py` + `src/` + `config.json` + `xlsx/` + `input/`
  - Config: Use `./out` as output_folder (tool 5 convention), `print_title_rows: null`, `page_break_before_label: false`
  - Tests:
    1. `test_happy_path` — Create matching.xlsx ("TestSite"→"XX001"), PNG in input/ named "PW XX001_exist TestSite_label.png", XLSX in xlsx/ named "TestSite.xlsx" with sheet "label". Run `python insert.py`. Verify exit 0, stdout contains "Done", output XLSX has image inserted.
    2. `test_missing_config` — No config.json. Verify exit 1 (json.load FileNotFoundError).
    3. `test_missing_xlsx_folder` — Valid config but xlsx/ doesn't exist. Verify exit 2, stderr contains "XLSX folder not found".

  **Must NOT do**: Do NOT use the real `_test_png.png`. Create PNGs from raw bytes.

  **QA**:
  ```
  Scenario: All CLI tests pass
    Tool: Bash
    Steps: cd 5-png-inserter && python -m pytest tests/test_cli.py -v
    Expected: 3 passed, 0 failed
  ```

  **Commit**: `test(png-inserter): add CLI integration tests`

---

## Commit Strategy

| # | Commit Message | Files |
|---|---------------|-------|
| 1 | `test(png-extractor): add CLI integration tests` | 1-png-extractor/tests/test_cli.py |
| 2 | `test(template-generator): add CLI integration tests` | 2-template-generator/tests/test_cli.py |
| 3 | `test(column-copier): add CLI integration tests` | 3-column-copier/tests/test_cli.py |
| 4 | `test(cell-editor): add CLI integration tests` | 4-cell-editor/tests/test_cli.py |
| 5 | `test(png-inserter): add CLI integration tests` | 5-png-inserter/tests/test_cli.py |

---

## Success Criteria

```bash
# Per-tool CLI test suites
cd 1-png-extractor && python -m pytest tests/test_cli.py -v    # 3 passed
cd ../2-template-generator && python -m pytest tests/test_cli.py -v  # 3 passed
cd ../3-column-copier && python -m pytest tests/test_cli.py -v      # 3 passed
cd ../4-cell-editor && python -m pytest tests/test_cli.py -v        # 3 passed
cd ../5-png-inserter && python -m pytest tests/test_cli.py -v       # 3 passed

# All existing tests still pass
cd 1-png-extractor && python -m pytest tests/ -v          # 35 passed
cd ../2-template-generator && python -m pytest tests/ -v  # 12 passed
cd ../3-column-copier && python -m pytest tests/ -v       # 28 passed
cd ../4-cell-editor && python -m pytest tests/ -v         # 12 passed
cd ../5-png-inserter && python -m pytest tests/ -v        # 46 passed
python -m pytest tests/test_run.py tests/test_pipeline_e2e.py -v  # 6 passed
# Total: 154 tests pass (139 existing + 15 new CLI)
```
