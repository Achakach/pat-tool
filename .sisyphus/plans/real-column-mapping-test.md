# Real Column Mapping — E2E Verification with `build_at` Architecture

## TL;DR

> **Quick Summary**: Verify the production column mapping (8 columns: C→D, D→F, E→C, G→G, H→I, IP1→E, IP2→H, PW→J) works correctly with the `build_at` architecture and page break protection using a Python-generated test dataset.
>
> **Deliverables**:
> - `3-column-copier/tests/generate_test_data.py` — Python script creating source + target `.xlsx` files
> - `3-column-copier/tests/test_real_mapping.py` — pytest integration test verifying all 8 columns + page break
> - Verified: copier runs with `page_break_enabled: true`, all columns paste correctly, source stays unmodified
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO — sequential (generate data → run test → verify)
> **Critical Path**: Task 1 → Task 2 → Task 3
> **Prerequisite**: `build-at-config-split` plan must be complete first

---

## Context

### Architecture Change (build-at-config-split)

The `build_at` config key separates temp column location from target paste column. The `copy_column` function is removed — paste reads directly from source to target. Source file is never modified.

### Production Column Mapping

```
SOURCE (cutsheet)              TARGET (IP & Port Assignment)
──────────────────              ─────────────────────────────
C = NE_NO        ──direct──→   D = Exist L1 OLT
D = PORT_NO      ──direct──→   F = Existing Port
E = L1 name      ──direct──→   C = L1 Name
G = NE_NO2       ──direct──→   G = New L1 OLT
H = PORT_NO2     ──direct──→   I = New Port
Q = PW temp      ──direct──→   J = PW Number
R = IP1 temp     ──direct──→   E = Existing IP
S = IP2 temp     ──direct──→   H = New IP
```

No columns overwritten. Source file stays pristine. Column order in config does **not** matter — `build_at` eliminates all ordering dependencies.

### Config Used for Test

```json
"columns": {
  "PW":      { "type": "planwork",  "build_at": "Q", "paste_to": "J" },
  "IP1":     { "type": "ip_lookup", "lookup_col": "C", "log_sheet": "Get Log Before&After", "build_at": "R", "paste_to": "E" },
  "IP2":     { "type": "ip_lookup", "lookup_col": "G", "log_sheet": "Get Log Before&After", "build_at": "S", "paste_to": "H" },
  "NE_NO1":  { "type": "copy",      "source_col": "C", "paste_to": "D" },
  "PORT_NO1": { "type": "copy",      "source_col": "D", "paste_to": "F" },
  "L1":      { "type": "copy",      "source_col": "E", "paste_to": "C" },
  "NE_NO2":  { "type": "copy",      "source_col": "G", "paste_to": "G" },
  "PORT_NO2": { "type": "copy",      "source_col": "H", "paste_to": "I" }
}
```

### Corrected Page Break Math

| Step | What happens | Row |
|------|-------------|-----|
| Content before any insert | `EXISTING_DATA_30` at row 30 | 30 |
| `insert_rows(3, 20)` | Pushes content down by 20 | **50** |
| Paste 20 rows (3-22) | `paste_end` = 23 | — |
| `snap_gap_rows(23, tws, 52)` | Finds content at 50, next_clean=53, gap=3 | — |
| `insert_rows(23, 3)` | Pushes content from 50 | **53** |

**Expected**: `EXISTING_DATA_30` at row **53** (NOT 157 as the old plan claimed).

### Metis Review

**Identified Gaps** (addressed):
- **Page break math corrected**: 157 → 53 (traced `snap_gap_rows` logic)
- **Cleanup action bug**: Documented in `build-at-config-split` scope (not this plan)
- **copy_column test**: Will be removed alongside function deletion in `build-at-config-split`
- **Config order mismatch**: Resolved (order doesn't matter with `build_at`, use consistent ordering)
- **E2E QA vagueness**: Replaced with concrete per-column assertions
- **Source modification check**: Added SHA256 verification before/after

---

## Work Objectives

### Core Objective
Create a repeatable E2E test that verifies the production column mapping works correctly with the `build_at` architecture and page break protection.

### Concrete Deliverables
- `3-column-copier/tests/generate_test_data.py` — script that creates source and target `.xlsx`
- `3-column-copier/tests/test_real_mapping.py` — pytest test exercising the full copier pipeline
- Verified output: all 8 columns map to correct target columns, source stays unmodified, existing content at clean page boundary

### Definition of Done
- [ ] `python tests/generate_test_data.py` — creates source + target files without error
- [ ] `python -m pytest tests/test_real_mapping.py -v` — 1 test, PASS
- [ ] Source `.xlsx` SHA256 unchanged after copier run
- [ ] Target output column D, row 3 = `"CR10SDA"` (NE_NO1)
- [ ] Target output column F, row 3 = `"1/1/1"` (PORT_NO1)
- [ ] Target output column C, row 3 = `"CR10-KM01"` (L1)
- [ ] Target output column G, row 3 = `"CR20SDA"` (NE_NO2)
- [ ] Target output column I, row 3 = `"2/1/1"` (PORT_NO2)
- [ ] Target output column J, row 3 = `"TEST001"` (PW)
- [ ] Target output column E, row 3 = `"10.10.10.10"` (IP1)
- [ ] Target output column H, row 3 = `"10.20.20.20"` (IP2)
- [ ] `EXISTING_DATA_30` at row **53** (clean page boundary)
- [ ] All 21+ existing tests still pass

### Must Have
- Python-generated test data (repeatable, reviewable, no binary blobs in repo)
- Per-column assertions with exact expected values
- Source file unmodified verification (SHA256 before/after)
- Page break verification at row 53 (corrected math)
- No merged cells in test data (would silently skip insert_rows)
- `print_title_rows: null` in test config (header_count=0 simplifies page math)

### Must NOT Have (Guardrails)
- No pre-committed `.xlsx` binary files
- No print_title_rows in test config
- No merged cell edge case testing (separate concern)
- No backward compat testing (covered by build-at-config-split Task 1)
- No cleanup action testing (covered by build-at-config-split Task 2)
- No vague "run and verify" assertions — every check is concrete + per-cell

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES — pytest with 21+ tests, tmp_path fixtures
- **Automated tests**: Tests-after — test written to verify implementation
- **Framework**: pytest + openpyxl
- **Agent-Executed QA**: Run pytest, verify output, capture evidence

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/real-mapping-{N}.{ext}`.

- **Test execution**: Bash (`python -m pytest`) — run tests, verify exit code + output
- **Cell verification**: Python one-liners via Bash — open output .xlsx, read specific cells, assert values
- **Source integrity**: Python one-liner via Bash — compute SHA256, compare before/after

---

## Execution Strategy

### Task Flow (sequential — each depends on prior)

```
Task 1: Create test data generator script
  └── Task 2: Create pytest integration test
       └── Task 3: Run E2E with page_break_enabled=true, verify all columns
```

### Agent Dispatch Summary
- **T1**: `quick` — Script generation, straightforward openpyxl code
- **T2**: `quick` — Pytest test writing, follows existing patterns
- **T3**: `quick` — Test execution + manual cell verification

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**

- [x] 1. **Create test data generator script**

  **What to do**:
  - Create `3-column-copier/tests/generate_test_data.py`:
    - Uses `openpyxl` to create two `.xlsx` files in `tests/tmp/`
    - **Source** (`tests/tmp/source_test.xlsx`):
      - Sheet `PW TEST001`: just exists (planwork identifier)
      - Sheet `cutsheet`: 20 data rows (rows 3-22):
        | Row | Col C (NE_NO) | Col D (PORT_NO) | Col E (L1) | Col G (NE_NO2) | Col H (PORT_NO2) |
        |-----|---------------|-----------------|------------|----------------|-------------------|
        | 3 | `CR10SDA` | `1/1/1` | `CR10-KM01` | `CR20SDA` | `2/1/1` |
        | 4 | `CR11SDA` | `1/1/2` | `CR11-KM01` | `CR21SDA` | `2/1/2` |
        | 5 | `CR12SDA` | `1/1/3` | `CR12-KM01` | `CR22SDA` | `2/1/3` |
        | ... | ... | ... | ... | ... | ... |
        | 22 | `CR29SDA` | `1/1/20` | `CR29-KM01` | `CR39SDA` | `2/1/20` |
      - Sheet `Get Log Before&After`: Row 1 with IP mappings:
        - `CR10SDA_10.10.10.10` through `CR29SDA_10.10.29.29` (for IP1 lookup on col C)
        - `CR20SDA_10.20.20.20` through `CR39SDA_10.20.39.39` (for IP2 lookup on col G)
    - **Target** (`tests/tmp/target_test.xlsx`):
      - Sheet `IP & Port Assignment`:
        - Row 1: header text `"Site Info"`
        - Row 30: `"EXISTING_DATA_30"` (col A)
        - Row 31: `"EXISTING_DATA_31"` (col A)
      - **NO merged cells** (merged cells cause insert_rows to skip)
    - Script takes optional `--tmp-dir` arg (default: `tests/tmp/`)
    - Prints filenames created and row counts on success
    - **Self-verifies**: after writing, re-opens files and asserts data is correct

  **Must NOT do**:
  - Do NOT commit the generated `.xlsx` files (add to `.gitignore` if needed)
  - Do NOT use merged cells in test data
  - Do NOT populate columns Q, R, S in source (they'll be built by copier)
  - Do NOT use `print_title_rows` in target (leave null for clean math)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward script — openpyxl Workbook creation, loops, assertions
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl-based .xlsx creation with proper sheet/column handling

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential — Task 1 only
  - **Blocks**: Task 2, Task 3
  - **Blocked By**: None (can start immediately)

  **References**:
  - `3-column-copier/tests/test_columns.py:12-45` — Existing test patterns using openpyxl Workbook + assertions
  - `3-column-copier/tests/test_columns.py:75-113` — tempfile + openpyxl save/load patterns
  - `3-column-copier/config.json` — Target config structure to match (build_at keys for PW/IP1/IP2)
  - `3-column-copier/copier.py:42-51` — How config paths are resolved (relative to copier.py)

  **Acceptance Criteria**:

  - [ ] `python tests/generate_test_data.py` — exit 0, prints file paths
  - [ ] `tests/tmp/source_test.xlsx` exists with sheets: `PW TEST001`, `cutsheet`, `Get Log Before&After`
  - [ ] Source row 3, col C = `"CR10SDA"`, row 3 col E = `"CR10-KM01"`
  - [ ] Source log sheet has `CR10SDA_10.10.10.10` at row 1
  - [ ] `tests/tmp/target_test.xlsx` exists with sheet `IP & Port Assignment`
  - [ ] Target row 30, col A = `"EXISTING_DATA_30"`, row 31 col A = `"EXISTING_DATA_31"`
  - [ ] Target has 0 merged cells

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Generator creates valid test files with correct data
    Tool: Bash
    Preconditions: Clean tests/tmp/ directory
    Steps:
      1. cd 3-column-copier && python tests/generate_test_data.py
      2. python -c "
         from openpyxl import load_workbook
         s = load_workbook('tests/tmp/source_test.xlsx')
         assert 'PW TEST001' in s.sheetnames
         assert 'cutsheet' in s.sheetnames
         assert 'Get Log Before&After' in s.sheetnames
         cs = s['cutsheet']
         assert cs.cell(row=3, column=3).value == 'CR10SDA'
         assert cs.cell(row=3, column=5).value == 'CR10-KM01'
         assert cs.cell(row=22, column=8).value == '2/1/20'
         log = s['Get Log Before&After']
         assert log.cell(row=1, column=1).value == 'CR10SDA_10.10.10.10'
         s.close()
         t = load_workbook('tests/tmp/target_test.xlsx')
         assert 'IP & Port Assignment' in t.sheetnames
         ts = t['IP & Port Assignment']
         assert ts.cell(row=30, column=1).value == 'EXISTING_DATA_30'
         assert ts.cell(row=31, column=1).value == 'EXISTING_DATA_31'
         assert len(ts.merged_cells.ranges) == 0
         t.close()
         print('ALL OK')
         "
    Expected Result: ALL OK
    Failure Indicators: AssertionError on any check, missing sheet, wrong cell value
    Evidence: .sisyphus/evidence/real-mapping-1-generator.txt
  ```

  **Evidence to Capture**:
  - [ ] `.sisyphus/evidence/real-mapping-1-generator.txt` — script output + verification

  **Commit**: YES
  - Message: `test(copier): add test data generator for real column mapping`
  - Files: `tests/generate_test_data.py`

- [x] 2. **Create pytest integration test**

  **What to do**:
  - Create `3-column-copier/tests/test_real_mapping.py`:
    - Uses `tmp_path` fixture (auto-cleaned by pytest)
    - Before test: run `generate_test_data.py --tmp-dir {tmp_path}` to create source + target
    - Compute SHA256 of source file (before copier)
    - Patch `config.json` values programmatically (or use a test config dict):
      - `source_folder`: tmp_path / "source"
      - `target_folder`: tmp_path / "target"
      - `output_folder`: tmp_path / "output"
      - `page_break_enabled`: True
      - `a4_page_rows`: 52
      - `paste_mode`: append
      - `print_title_rows`: null
      - Columns: production mapping (8 columns with `build_at` as shown above)
    - Set up `matching.xlsx` in tmp: "TEST001" → "target_test.xlsx"
    - Run `copier.main()` with test config (call main logic, not subprocess)
    - Assert source SHA256 unchanged (source file never modified)
    - Open output file and verify **every cell**:
      | Assertion | Cell | Expected |
      |-----------|------|----------|
      | NE_NO1 → D | `tws.cell(row=3, column=4)` | `"CR10SDA"` |
      | PORT_NO1 → F | `tws.cell(row=3, column=6)` | `"1/1/1"` |
      | L1 → C | `tws.cell(row=3, column=3)` | `"CR10-KM01"` |
      | NE_NO2 → G | `tws.cell(row=3, column=7)` | `"CR20SDA"` |
      | PORT_NO2 → I | `tws.cell(row=3, column=9)` | `"2/1/1"` |
      | PW → J | `tws.cell(row=3, column=10)` | `"TEST001"` |
      | IP1 → E | `tws.cell(row=3, column=5)` | `"10.10.10.10"` |
      | IP2 → H | `tws.cell(row=3, column=8)` | `"10.20.20.20"` |
    - Assert last data row: `tws.cell(row=22, column=3)` = `"CR29-KM01"` (20th row)
    - Assert page break: `tws.cell(row=53, column=1)` = `"EXISTING_DATA_30"`
    - Assert `tws.cell(row=54, column=1)` = `"EXISTING_DATA_31"`

  **Must NOT do**:
  - Do NOT call `copier.py` as subprocess — use in-process main() call with monkeypatched config
  - Do NOT hardcode absolute paths — use tmp_path fixture
  - Do NOT leave test files behind — tmp_path auto-cleans
  - Do NOT test backward compat (no build_at) — that's build-at-config-split scope

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pytest test writing following existing patterns in test_columns.py
  - **Skills**: [`xlsx`]
    - `xlsx`: openpyxl cell reading + assertions

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential — Task 2 only
  - **Blocks**: Task 3
  - **Blocked By**: Task 1 (needs generator script + build-at-config-split complete)

  **References**:
  - `3-column-copier/tests/test_columns.py:161-200` — Integration test pattern with tmp_path + openpyxl
  - `3-column-copier/conftest.py` — sys.path setup pattern
  - `3-column-copier/copier.py:42-51` — Config loading (paths resolved relative to copier.py)
  - `3-column-copier/copier.py:54-57` — read_matching signature
  - `3-column-copier/copier.py:136-140` — _setup_a4_print + _calc_page_rows call pattern

  **Acceptance Criteria**:

  - [ ] `python -m pytest tests/test_real_mapping.py -v` — 1 test, PASS
  - [ ] Source SHA256 unchanged after test (asserted in test body)
  - [ ] All 8 column assertions pass (row 3)
  - [ ] Last row assertion passes (row 22)
  - [ ] Page break assertion passes (row 53)
  - [ ] All 21+ existing tests still pass: `python -m pytest tests/ -v`

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Integration test passes — all columns correct, source unmodified, page break at 53
    Tool: Bash
    Preconditions: Task 1 complete (generator script exists), build-at-config-split complete
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_real_mapping.py -v
      3. python -m pytest tests/ -v
    Expected Result: test_real_mapping.py PASSED (1 test), all other tests PASS (21+)
    Failure Indicators: Any FAILED test, AssertionError for wrong cell value, SHA256 mismatch
    Evidence: .sisyphus/evidence/real-mapping-2-pytest.txt

  Scenario: Test verifies source file is unmodified
    Tool: Bash
    Preconditions: Test ran and passed
    Steps:
      1. cd 3-column-copier
      2. python -m pytest tests/test_real_mapping.py -v -k "test_real" --tb=long
    Expected Result: Test output includes SHA256 assertion pass (no "source was modified" error)
    Failure Indicators: SHA256 mismatch error in test output
    Evidence: .sisyphus/evidence/real-mapping-2-source-checksum.txt
  ```

  **Evidence to Capture**:
  - [ ] `.sisyphus/evidence/real-mapping-2-pytest.txt` — full pytest output
  - [ ] `.sisyphus/evidence/real-mapping-2-source-checksum.txt` — SHA256 assertion detail

  **Commit**: YES
  - Message: `test(copier): add integration test for real column mapping with build_at`
  - Files: `tests/test_real_mapping.py`

- [x] 3. **Run E2E verification and collect evidence**

  **What to do**:
  - Run the full test suite and capture evidence:
    1. `cd 3-column-copier && python tests/generate_test_data.py`
    2. `cd 3-column-copier && python -m pytest tests/test_real_mapping.py -v --tb=long`
    3. `cd 3-column-copier && python -m pytest tests/ -v`
  - If test passes, do spot-check verification by opening output file directly:
    ```python
    from openpyxl import load_workbook
    wb = load_workbook('tests/tmp/output/target_test.xlsx')
    ws = wb['IP & Port Assignment']
    print(f"D3={ws.cell(3,4).value}  F3={ws.cell(3,6).value}  C3={ws.cell(3,3).value}")
    print(f"G3={ws.cell(3,7).value}  I3={ws.cell(3,9).value}  J3={ws.cell(3,10).value}")
    print(f"E3={ws.cell(3,5).value}  H3={ws.cell(3,8).value}")
    print(f"row53={ws.cell(53,1).value}  row54={ws.cell(54,1).value}")
    wb.close()
    ```
  - Save all output to evidence files

  **Must NOT do**:
  - Do NOT mark task complete if any assertion fails
  - Do NOT skip the spot-check — verify actual cell values beyond what pytest asserts
  - Do NOT leave generated .xlsx files in the repo

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test execution + evidence collection, no code changes
  - **Skills**: []
    - No skills needed — just bash commands

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential — Task 3 only
  - **Blocks**: Final Verification Wave
  - **Blocked By**: Task 1, Task 2, build-at-config-split

  **References**:
  - `3-column-copier/tests/test_real_mapping.py` — The test created in Task 2
  - `3-column-copier/tests/generate_test_data.py` — The generator created in Task 1

  **Acceptance Criteria**:

  - [ ] All tests pass (21+ existing + 1 new)
  - [ ] Source file SHA256 unchanged
  - [ ] All 8 column cells verified at row 3
  - [ ] Last data row (22) verified
  - [ ] Page break at row 53 verified

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Full E2E — generate, run, verify all cells
    Tool: Bash
    Preconditions: Tasks 1-2 complete, build-at-config-split complete
    Steps:
      1. cd 3-column-copier
      2. python tests/generate_test_data.py
      3. python -m pytest tests/test_real_mapping.py -v --tb=long
      4. python -m pytest tests/ -v
      5. python -c "
         from openpyxl import load_workbook
         wb = load_workbook('tests/tmp/output/target_test.xlsx')
         ws = wb['IP & Port Assignment']
         checks = [
           ('D3 NE_NO1', ws.cell(3,4).value, 'CR10SDA'),
           ('F3 PORT1', ws.cell(3,6).value, '1/1/1'),
           ('C3 L1', ws.cell(3,3).value, 'CR10-KM01'),
           ('G3 NE_NO2', ws.cell(3,7).value, 'CR20SDA'),
           ('I3 PORT2', ws.cell(3,9).value, '2/1/1'),
           ('J3 PW', ws.cell(3,10).value, 'TEST001'),
           ('E3 IP1', ws.cell(3,5).value, '10.10.10.10'),
           ('H3 IP2', ws.cell(3,8).value, '10.20.20.20'),
           ('C22 last L1', ws.cell(22,3).value, 'CR29-KM01'),
           ('row53', ws.cell(53,1).value, 'EXISTING_DATA_30'),
           ('row54', ws.cell(54,1).value, 'EXISTING_DATA_31'),
         ]
         all_ok = True
         for label, actual, expected in checks:
             ok = actual == expected
             print(f'[{'OK' if ok else 'FAIL'}] {label}: {actual} (expected {expected})')
             if not ok: all_ok = False
         wb.close()
         print('\\nALL PASS' if all_ok else '\\nSOME FAILED')
         "
    Expected Result: ALL PASS on all 11 checks, all pytest suites PASS
    Failure Indicators: Any FAIL check, any pytest failure, missing output file
    Evidence: .sisyphus/evidence/real-mapping-3-e2e.txt

  Scenario: Source file integrity check
    Tool: Bash
    Preconditions: E2E test ran
    Steps:
      1. cd 3-column-copier
      2. python -c "
         import hashlib
         before = hashlib.sha256(open('tests/tmp/source_test.xlsx','rb').read()).hexdigest()
         # Run copier via test (test already did this, just verify file still exists unmodified)
         after = hashlib.sha256(open('tests/tmp/source_test.xlsx','rb').read()).hexdigest()
         print(f'Before: {before}')
         print(f'After:  {after}')
         print('SOURCE UNCHANGED' if before == after else 'SOURCE WAS MODIFIED!')
         "
    Expected Result: SOURCE UNCHANGED
    Failure Indicators: SOURCE WAS MODIFIED! message
    Evidence: .sisyphus/evidence/real-mapping-3-source-integrity.txt
  ```

  **Evidence to Capture**:
  - [ ] `.sisyphus/evidence/real-mapping-3-e2e.txt` — all 11 cell checks + pytest output
  - [ ] `.sisyphus/evidence/real-mapping-3-source-integrity.txt` — SHA256 before/after

  **Commit**: NO (evidence only, no code changes)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Test Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Verify all tests pass. Review test for: clear assertions, no `assert True` placeholders, proper teardown (tmp_path), side-effect isolation (no shared state between tests). Check test data generator for repeatability.
  Output: `Tests [N pass/N fail] | Assertions [N valid/N weak] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Run `python tests/generate_test_data.py` → `python copier.py` → verify EVERY expected cell value from Definition of Done. Verify source file SHA256 unchanged. Verify EXISTING_DATA_30 at row 53. Save evidence to `.sisyphus/evidence/real-mapping/`.
  Output: `Cells [N/N correct] | Source [CLEAN/MODIFIED] | Page Break [row 53/OTHER] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec. Check "Must NOT do" compliance. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| # | Commit Message | Files |
|---|---------------|-------|
| 1 | `test(copier): add real column mapping E2E with build_at` | `tests/generate_test_data.py`, `tests/test_real_mapping.py` |

---

## Success Criteria

```bash
cd 3-column-copier
python tests/generate_test_data.py          # Expected: exit 0, creates source + target .xlsx
python -m pytest tests/ -v                   # Expected: 22+ passed (21 existing + 1 new)
python -m pytest tests/test_real_mapping.py -v  # Expected: 1 passed
```
