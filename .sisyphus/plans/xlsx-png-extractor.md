# XLSX PNG Extractor with Smart Naming

## TL;DR

> **Quick Summary**: Python CLI tool that extracts PNG images from all .xlsx files in a configured folder, names each output using `{XLSXstem}_{SheetName}_{LabelFromRowAbove}.png`, with configurable input/output paths via JSON config.
>
> **Deliverables**:
> - `extract_pngs.py` — main CLI script
> - `config.json` — input/output folder paths
> - `test_extract_pngs.py` — pytest test suite
> - Test fixture: `test_fixture.xlsx` — multi-sheet XLSX with PNGs and labels
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6

---

## Context

### Original Request
User wants to extract PNG images from XLSX files. Each output PNG should be named using the source XLSX filename, the sheet name it came from, and the text label found in the row directly above the image's anchor position. Multiple XLSX files in a folder should be batch-processed, with input and output folders configurable via JSON.

### Interview Summary
**Key Discussions**:
- **Language**: Python using openpyxl for cell reading + zipfile for image extraction (avoids private API fragility)
- **Interface**: CLI script with `--config` flag pointing to a JSON config file
- **Config**: Minimal JSON — `input_folder` (XLSX source), `output_folder` (PNG destination)
- **Naming**: `{XLSXstem}_{SheetName}_{Label}.png` (includes XLSX filename to prevent cross-file collisions)
- **Fallback**: `{XLSXstem}_{SheetName}_row{N}_col{L}.png` when row above has no text
- **Batch mode**: Process all .xlsx in input folder (flat only, no subfolders)
- **Tests**: pytest — basic naming logic and extraction tests
- **Image scope**: PNG only; skip non-PNG with warning

**Research Findings**:
- XLSX internal structure: `xl/media/` contains raw image files, `xl/drawings/drawingN.xml` maps images to positions, `xl/worksheets/_rels/sheetN.xml.rels` links sheets to drawings
- openpyxl's `sheet._images` is a private API — fragile across versions
- openpyxl can read cell values for label lookup; zipfile can extract images directly
- Anchor is `TwoCellAnchor` with `_from.row` and `_from.col` (0-indexed)
- When `_from.row == 0`, no row exists above → immediate fallback needed
- Book1.xlsx in workspace has 2 PNGs and zero cell values — perfect fallback test fixture

### Metis Review
**Identified Gaps** (addressed with defaults):
- **Config discovery**: `--config` CLI arg required, validates schema, exits with code 1 if missing/invalid
- **Cross-file collisions**: Include XLSX stem in filename (`{stem}_{Sheet}_{Label}.png`)
- **Edge at row 0**: Immediate fallback naming when `_from.row == 0`
- **Duplicate names**: Append `_{N}` counter when file exists
- **Non-PNG images**: Skip with warning, don't crash
- **Private API fragility**: Use `zipfile` for extraction, openpyxl only for cell reading
- **Corrupt/protected XLSX**: Catch exceptions, log error to stderr, continue processing
- **Hidden temp files**: Skip `~$*.xlsx` (Excel lock files)
- **Exit codes**: 0=success, 1=config error, 2=I/O error
- **Output folder**: Auto-create if doesn't exist
- **Duplicate sheet names**: Not possible via Excel UI; handled gracefully

---

## Work Objectives

### Core Objective
Build a Python CLI tool that batch-extracts PNG images from XLSX files and names them intelligently using the source filename, sheet name, and the label text above each image.

### Concrete Deliverables
- `extract_pngs.py` — CLI entry point with argparse (`--config` flag)
- `config.json` — Schema: `{ "input_folder": "path", "output_folder": "path" }`
- `test_extract_pngs.py` — pytest tests for naming, sanitization, fallback, edge cases
- `test_fixture.xlsx` — Multi-sheet XLSX with PNGs at known positions + labels above them

### Definition of Done
- [x] `python extract_pngs.py --config config.json` processes all .xlsx in input folder
- [x] Each PNG saved to output folder with name `{XLSXstem}_{Sheet}_{Label}.png`
- [x] Fallback naming when row above is empty: `{XLSXstem}_{Sheet}_row{N}_col{L}.png`
- [x] `pytest test_extract_pngs.py` → all tests pass
- [x] Exit codes: 0 on success, 1 on config error, 2 on I/O error
- [x] Stderr for errors, stdout for progress per file/image

### Must Have
- Config via `--config <path>` CLI argument
- Batch processing of all .xlsx in input folder (flat, no recursion)
- PNG files saved to configured output folder
- Extract via `zipfile` (stable), read labels via openpyxl
- Skip non-PNG images with warning
- Sanitize filenames: replace `/\:*?"<>|` with `_`
- Handle corrupt/protected XLSX gracefully (log + skip)
- Auto-create output folder if missing
- Skip Excel temp files (`~$*.xlsx`)

### Must NOT Have (Guardrails)
- **NO modifying source XLSX files** — read-only operation
- **NO subfolder recursion** — flat input folder only
- **NO non-PNG extraction** — skip JPEG/GIF/EMF/WMF with warning
- **NO GUI or web interface** — CLI only
- **NO progress bars or logging frameworks** — stdout/stderr only
- **NO parallel/multithreaded processing** — sequential, one file at a time
- **NO over-engineered config** — two string fields, that's it
- **NO openpyxl `_images` private API** — use zipfile for extraction
- **NO overwriting existing output without explicit policy** — always overwrite (idempotent)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (new project)
- **Automated tests**: YES — basic pytest tests
- **Framework**: pytest
- **Test approach**: Tests-after (tests written alongside implementation)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/Backend**: Use Bash (PowerShell) — Run script, assert exit codes, stdout, stderr, output files
- **Tests**: Use Bash — `pytest test_extract_pngs.py -v`

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation):
├── Task 1: Project setup — requirements.txt, config.json template [quick]
├── Task 2: Config module — load + validate config.json [quick]

Wave 2 (After Wave 1 — core modules, MAX PARALLEL):
├── Task 3: Image extractor — zipfile-based PNG extraction from XLSX [quick]
├── Task 4: Naming engine — label lookup + sanitization + fallback [quick]
├── Task 5: Test fixture — create multi-sheet XLSX with PNGs and labels [unspecified-high]

Wave 3 (After Wave 2 — integration + CLI):
├── Task 6: CLI + orchestration — argparse, main loop, error handling [quick]
├── Task 7: Test suite — pytest tests for naming, extraction, edge cases [deep]

Wave FINAL (After ALL tasks):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
├── Task F4: Scope fidelity check (deep)
-> Present results → Get explicit user okay

Critical Path: Task 1 → Task 2 → Task 3 + Task 4 + Task 5 → Task 6 → Task 7 → F1-F4
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 3 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 2, 3, 4, 5 |
| 2 | 1 | 3, 4, 6 |
| 3 | 1, 2 | 6 |
| 4 | 1, 2 | 6 |
| 5 | 1 | 7 |
| 6 | 1, 2, 3, 4 | 7 |
| 7 | 5, 6 | F1-F4 |

### Agent Dispatch Summary

| Wave | Tasks | Agents |
|------|-------|--------|
| 1 | T1-T2 | `quick` × 2 |
| 2 | T3-T4 | `quick` × 2, T5 → `unspecified-high` |
| 3 | T6 | `quick`, T7 → `deep` |
| FINAL | F1-F4 | `oracle`, `unspecified-high` × 2, `deep` |

---

## TODOs

- [x] 1. Project Setup — requirements.txt and config.json template

  **What to do**:
  - Create `requirements.txt` with `openpyxl>=3.0,<4.0` as the only dependency
  - Create `config.json` template with empty placeholders:
    ```json
    {
      "input_folder": "./input",
      "output_folder": "./output"
    }
    ```
  - Create `.sisyphus/evidence/` directory for QA evidence storage

  **Must NOT do**:
  - Do NOT add pytest to requirements.txt (separate dev dependency)
  - Do NOT create any Python files yet — config module is Task 2

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file creation, no logic involved
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2 can be parallel if using same pattern)
  - **Blocks**: Tasks 2, 3, 4, 5
  - **Blocked By**: None (can start immediately)

  **References**:
  - No existing code patterns to follow — this is a new project root

  **Acceptance Criteria**:
  - [ ] `requirements.txt` exists with `openpyxl>=3.0,<4.0`
  - [ ] `config.json` exists with valid JSON containing `input_folder` and `output_folder` strings
  - [ ] `.sisyphus/evidence/` directory exists

  **QA Scenarios**:

  ```
  Scenario: Files exist with correct content
    Tool: Bash (PowerShell)
    Steps:
      1. Test-Path "requirements.txt" → should return True
      2. Get-Content "requirements.txt" → should contain "openpyxl"
      3. Test-Path "config.json" → should return True
      4. python -c "import json; c=json.load(open('config.json')); assert 'input_folder' in c; assert 'output_folder' in c; print('OK')"
    Expected Result: All assertions pass, "OK" printed
    Evidence: .sisyphus/evidence/task-1-setup.txt
  ```

  **Commit**: YES
  - Message: `chore: project setup — requirements.txt and config.json template`
  - Files: `requirements.txt`, `config.json`

- [x] 2. Config Module — load and validate config.json

  **What to do**:
  - Create `config.py` with:
    - `load_config(path: str) -> dict` — loads JSON, validates schema, returns dict
    - Schema validation: must have `input_folder` (str) and `output_folder` (str)
    - On missing file: print "Config file not found: {path}" to stderr, `sys.exit(1)`
    - On invalid schema: print "Invalid config: missing 'input_folder' or 'output_folder'" to stderr, `sys.exit(1)`
    - On valid: return `{"input_folder": path, "output_folder": path}`
  - Use only `json` and `sys` from stdlib

  **Must NOT do**:
  - Do NOT add any other config fields (no over-engineering)
  - Do NOT auto-create folders — that's the orchestrator's job (Task 6)
  - Do NOT add logging/progress (stderr only for errors)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file, ~40 lines, straightforward validation logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (can run in parallel with Task 1 if executor handles dependency)
  - **Blocks**: Tasks 3, 4, 6
  - **Blocked By**: Task 1 (needs `config.json` to exist for testing)

  **References**:
  - `config.json` (created in Task 1) — the schema to validate against

  **Acceptance Criteria**:
  - [ ] `config.py` exists with `load_config()` function
  - [ ] `python -c "from config import load_config; load_config('config.json')"` → returns dict with input_folder and output_folder
  - [ ] `python -c "from config import load_config; load_config('nonexistent.json')"` → exit code 1, stderr contains error
  - [ ] Invalid config with wrong schema → exit code 1

  **QA Scenarios**:

  ```
  Scenario: Valid config loads successfully
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from config import load_config; c=load_config('config.json'); print(c['input_folder']); print(c['output_folder'])"
    Expected Result: Prints both folder paths, exit code 0
    Evidence: .sisyphus/evidence/task-2-valid-config.txt

  Scenario: Missing config file exits with error
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from config import load_config; load_config('nonexistent.json')" 2>&1; echo "EXIT:$LASTEXITCODE"
    Expected Result: EXIT:1, stderr contains "Config file not found"
    Evidence: .sisyphus/evidence/task-2-missing-config.txt

  Scenario: Invalid config schema exits with error
    Tool: Bash (PowerShell)
    Preconditions: Create {"bad": "schema"} in a temp config file
    Steps:
      1. echo '{"bad": "schema"}' > test_invalid.json
      2. python -c "from config import load_config; load_config('test_invalid.json')" 2>&1; echo "EXIT:$LASTEXITCODE"
    Expected Result: EXIT:1, stderr contains "Invalid config"
    Evidence: .sisyphus/evidence/task-2-invalid-config.txt
  ```

  **Commit**: YES
  - Message: `feat: config module — load and validate config.json`
  - Files: `config.py`

- [x] 3. Image Extractor — zipfile-based PNG extraction from XLSX

  **What to do**:
  - Create `extractor.py` with:
    - `extract_images(xlsx_path: Path, output_dir: Path) -> int` — extracts all PNGs from a single XLSX
    - Opens XLSX as ZIP via `zipfile.ZipFile`
    - Lists `/xl/media/` members, filters to `.png` extension only
    - For each PNG found, extracts to output_dir with a temporary name `_raw_{stem}_{n}.png`
    - Returns count of extracted PNGs
    - Skip non-PNG media files (JPEG, GIF, etc.) — print warning to stderr
    - Catch `BadZipFile` / `KeyError`: print error to stderr, return 0
    - Catch `PermissionError`: print error to stderr, return 0
  - Function signature returns raw image count; naming happens in Task 4+6

  **Must NOT do**:
  - Do NOT rename files with final names here — naming is Task 4's job
  - Do NOT use openpyxl for extraction — zipfile only
  - Do NOT crash on corrupt/protected XLSX — catch and continue
  - Do NOT extract non-PNG image types

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward zipfile extraction, ~60 lines
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 6
  - **Blocked By**: Tasks 1, 2

  **References**:
  - Python `zipfile` docs: `ZipFile.namelist()`, `ZipFile.extract()` — standard library API
  - `Book1.xlsx` in workspace — test against this real file

  **Acceptance Criteria**:
  - [ ] `extractor.py` exists with `extract_images()` function
  - [ ] Running against Book1.xlsx → extracts 2 PNGs to output dir
  - [ ] Running against a corrupt ZIP → returns 0, prints error to stderr
  - [ ] Non-PNG media in XLSX → skipped with warning, PNGs still extracted

  **QA Scenarios**:

  ```
  Scenario: Extract PNGs from Book1.xlsx
    Tool: Bash (PowerShell)
    Preconditions: Book1.xlsx in current dir, output_dir exists
    Steps:
      1. python -c "from extractor import extract_images; from pathlib import Path; n = extract_images(Path('Book1.xlsx'), Path('test_out')); print(f'Extracted: {n}')"
      2. Get-ChildItem test_out -Filter "*.png" | Measure-Object | Select-Object -ExpandProperty Count
    Expected Result: "Extracted: 2", Count = 2
    Evidence: .sisyphus/evidence/task-3-extract-book1.txt

  Scenario: No images in XLSX (text-only sheet)
    Tool: Bash (PowerShell)
    Preconditions: Placeholder for a text-only XLSX (or use any xlsx without images)
    Steps:
      1. python -c "from extractor import extract_images; from pathlib import Path; n = extract_images(Path('text_only.xlsx'), Path('test_out')); print(f'Extracted: {n}')"
    Expected Result: "Extracted: 0", no files in test_out
    Evidence: .sisyphus/evidence/task-3-no-images.txt
  ```

  **Commit**: YES
  - Message: `feat: image extractor — zipfile-based PNG extraction`
  - Files: `extractor.py`

- [x] 4. Naming Engine — label lookup, sanitization, fallback

  **What to do**:
  - Create `naming.py` with:
    - `build_filename(xlsx_stem: str, sheet_name: str, label: str | None, anchor_row: int, anchor_col: int) -> str`
      - Returns `{xlsx_stem}_{sheet_name}_{sanitized_label}.png` if label exists
      - Returns `{xlsx_stem}_{sheet_name}_row{anchor_row+1}_col{col_letter}.png` if label is None/empty
    - `sanitize(name: str) -> str` — replaces `/\:*?"<>|` with `_`, strips leading/trailing whitespace and dots
    - `get_label(ws, anchor_row: int, anchor_col: int) -> str | None`:
      - Uses openpyxl worksheet object
      - If `anchor_row == 0`: return None immediately (no row above)
      - Read `ws.cell(row=anchor_row, column=anchor_col + 1).value` (openpyxl is 1-indexed, anchor is 0-indexed)
      - Return `str(value).strip()` if truthy, else None
    - `col_letter(n: int) -> str` — 0-indexed column to letter (0→A, 1→B, ..., 25→Z, 26→AA)

  **Must NOT do**:
  - Do NOT use `sheet._images` at all (private API)
  - Do NOT truncate filenames at 200 chars (handle in Task 6 orchestrator)
  - Do NOT handle file I/O — this module is pure string manipulation

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure functions, string manipulation, ~60 lines
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 5)
  - **Blocks**: Task 6
  - **Blocked By**: Tasks 1, 2

  **References**:
  - openpyxl docs: `worksheet.cell(row, column)` for cell access
  - Excel column naming: A-Z, AA-ZZ pattern for col_letter()

  **Acceptance Criteria**:
  - [ ] `naming.py` exists with all four functions
  - [ ] `build_filename("report", "Sheet1", "Revenue", 3, 1)` → `"report_Sheet1_Revenue.png"`
  - [ ] `build_filename("report", "Sheet1", None, 3, 1)` → `"report_Sheet1_row4_colB.png"`
  - [ ] `build_filename("report", "Sheet1", "", 0, 0)` → `"report_Sheet1_row1_colA.png"` (row 0, immediate fallback)
  - [ ] `sanitize("Q1/2024: <Report>")` → `"Q1_2024_ _Report_"` (all bad chars replaced)
  - [ ] `col_letter(0)` → `"A"`, `col_letter(25)` → `"Z"`, `col_letter(26)` → `"AA"`

  **QA Scenarios**:

  ```
  Scenario: Label from row above generates correct filename
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from naming import build_filename; print(build_filename('book1', 'Sales', 'Q3 Revenue', 3, 2))"
    Expected Result: "book1_Sales_Q3 Revenue.png"
    Evidence: .sisyphus/evidence/task-4-label-name.txt

  Scenario: Empty label uses fallback naming
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from naming import build_filename; print(build_filename('book1', 'Sheet1', None, 14, 0))"
    Expected Result: "book1_Sheet1_row15_colA.png"
    Evidence: .sisyphus/evidence/task-4-fallback-name.txt

  Scenario: Bad characters sanitized in sheet name and label
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from naming import build_filename; print(build_filename('data', 'Q1/2024', 'Profit/Loss: <5%>', 1, 1))"
    Expected Result: "data_Q1_2024_Profit_Loss_ _5%_.png"
    Evidence: .sisyphus/evidence/task-4-sanitize.txt
  ```

  **Commit**: YES
  - Message: `feat: naming engine — label lookup, sanitization, fallback`
  - Files: `naming.py`

- [x] 5. Test Fixture — multi-sheet XLSX with PNGs and labels

  **What to do**:
  - Create `test_fixture.xlsx` using openpyxl (programmatic creation):
    - **Sheet "Sales"**:
      - Cell A1: "Revenue Chart" — Image anchored at A2 (col=0, row=1) — a simple colored rectangle PNG
      - Cell E1: "Growth Trend" — Image anchored at E2 (col=4, row=1)
    - **Sheet "Empty"**:
      - Image anchored at B5 (col=1, row=4) with NO label above → tests fallback naming
    - **Sheet "Edge"**:
      - Image anchored at A1 (col=0, row=0) → tests row-0 edge case (no row above)
      - Cell B10: "Deep Label" — Image anchored at B11 (col=1, row=10)
  - Generate simple PNG images programmatically (e.g., a 100×50 colored rectangle via Pillow if available, or embed the smallest valid PNG bytes directly)
  - Save to `test_fixture.xlsx`

  **Must NOT do**:
  - Do NOT manually create in Excel — must be reproducible via script
  - Do NOT use external image files — generate PNG bytes in code

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires openpyxl + image embedding knowledge, multi-sheet creation, edge case coverage
  - **Skills**: [`xlsx`]
    - `xlsx`: For openpyxl sheet manipulation and image embedding patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 4)
  - **Blocks**: Task 7
  - **Blocked By**: Task 1

  **References**:
  - openpyxl docs: `openpyxl.drawing.image.Image` for embedding images
  - Minimal valid PNG bytes: `\x89PNG\r\n\x1a\n...` (can hardcode a tiny PNG)
  - Workshop `Book1.xlsx` as reference for XLSX structure with images

  **Acceptance Criteria**:
  - [ ] `test_fixture.xlsx` exists with 3 sheets: "Sales", "Empty", "Edge"
  - [ ] "Sales" sheet has labels at A1 and E1 with images anchored below
  - [ ] "Empty" sheet has image with no label above → fallback scenario
  - [ ] "Edge" sheet has image at A1 → row-0 edge case
  - [ ] All embedded images are valid PNGs

  **QA Scenarios**:

  ```
  Scenario: Fixture file exists with correct structure
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from openpyxl import load_workbook; wb = load_workbook('test_fixture.xlsx'); print([s.title for s in wb.worksheets]); print(wb['Sales']['A1'].value); print(wb['Sales']['B1'].value)"
    Expected Result: ['Sales', 'Empty', 'Edge'], "Revenue Chart", "Growth Trend"
    Evidence: .sisyphus/evidence/task-5-fixture-structure.txt

  Scenario: Images are extractable from fixture
    Tool: Bash (PowerShell)
    Steps:
      1. python -c "from zipfile import ZipFile; z=ZipFile('test_fixture.xlsx'); print([n for n in z.namelist() if n.startswith('xl/media/')])"
    Expected Result: Lists at least 5 PNG entries (one per embedded image)
    Evidence: .sisyphus/evidence/task-5-fixture-images.txt
  ```

  **Commit**: YES
  - Message: `test: multi-sheet XLSX fixture with PNGs and labels`
  - Files: `test_fixture.xlsx`

- [x] 6. CLI + Orchestration — argparse, main loop, error handling

  **What to do**:
  - Create `extract_pngs.py` — the main CLI entry point:
    - `argparse`: single argument `--config` (required)
    - Calls `load_config()` from config.py
    - Validates output folder exists or creates it via `Path.mkdir(parents=True, exist_ok=True)`
    - Iterates all `*.xlsx` in input folder (flat), skipping `~$*.xlsx` temp files
    - For each XLSX:
      - Print "Processing: {filename}" to stdout
      - Open with openpyxl (`load_workbook(data_only=True, read_only=True)`)
      - Open as zipfile for image extraction
      - For each sheet: get images via zipfile listing, map to anchors via drawing XML parsing
      - Call `get_label()` from naming.py for each image's anchor
      - Call `build_filename()` for the output name
      - Handle filename collisions: if file exists, append `_{N}` counter (N=1,2,3... max 99)
      - Save PNG bytes to output folder
      - Print "  Extracted: {filename}" to stdout
    - Print final summary: "Done. Extracted {N} images from {M} files."
    - Exit code 0 on success
    - Catches openpyxl errors (corrupt, password-protected) → print ERROR to stderr, continue
    - Catches PermissionError → print ERROR to stderr, continue
    - Exit code 2 on I/O errors (input folder not found, output creation failed)

  **Must NOT do**:
  - Do NOT process subdirectories
  - Do NOT add progress bars or logging
  - Do NOT modify source files
  - Do NOT exit on a single file error — continue processing remaining files

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Orchestration glue — combines existing modules with error handling, ~100 lines
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential — depends on all Wave 2 modules)
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 1, 2, 3, 4

  **References**:
  - `config.py` → `load_config()`
  - `extractor.py` → `extract_images()`
  - `naming.py` → `build_filename()`, `get_label()`, `sanitize()`

  **Acceptance Criteria**:
  - [ ] `python extract_pngs.py --config config.json` processes Book1.xlsx
  - [ ] Two PNGs saved with names like `Book1_Sheet1_row2_colB.png` and `Book1_Sheet1_row15_colB.png`
  - [ ] `python extract_pngs.py --config nonexistent.json` → exit 1 with error
  - [ ] Input folder not found → exit 2 with error
  - [ ] `~$temp.xlsx` in input folder → skipped silently
  - [ ] Duplicate filename → `_1.png` suffix appended

  **QA Scenarios**:

  ```
  Scenario: Full run with Book1.xlsx
    Tool: Bash (PowerShell)
    Preconditions: config.json pointing to folder with Book1.xlsx, output folder exists
    Steps:
      1. python extract_pngs.py --config config.json; echo "EXIT:$LASTEXITCODE"
      2. Get-ChildItem output_folder -Filter "*.png" | Select-Object Name
    Expected Result: EXIT:0, stdout contains "Processing: Book1.xlsx", two "Extracted: ..." lines, "Done. Extracted 2 images from 1 file."
    Evidence: .sisyphus/evidence/task-6-full-run.txt

  Scenario: Missing config exits with code 1
    Tool: Bash (PowerShell)
    Steps:
      1. python extract_pngs.py --config nonexistent.json 2>&1; echo "EXIT:$LASTEXITCODE"
    Expected Result: EXIT:1, stderr contains "Config file not found"
    Evidence: .sisyphus/evidence/task-6-missing-config.txt

  Scenario: Non-existent input folder exits with code 2
    Tool: Bash (PowerShell)
    Preconditions: config with input_folder pointing to non-existent path
    Steps:
      1. echo '{"input_folder":"./nonexistent","output_folder":"./out"}' > bad_input_config.json
      2. python extract_pngs.py --config bad_input_config.json 2>&1; echo "EXIT:$LASTEXITCODE"
    Expected Result: EXIT:2, stderr contains error about folder not found
    Evidence: .sisyphus/evidence/task-6-bad-input.txt

  Scenario: Duplicate filename collision handled
    Tool: Bash (PowerShell)
    Preconditions: Pre-create a file in output folder matching what would be extracted
    Steps:
      1. python extract_pngs.py --config config.json 2>&1
      2. Check that duplicate gets _1 suffix instead of overwriting
    Expected Result: Existing file untouched, new file has _1 suffix
    Evidence: .sisyphus/evidence/task-6-collision.txt
  ```

  **Commit**: YES
  - Message: `feat: CLI + orchestration — argparse, main loop, error handling`
  - Files: `extract_pngs.py`

- [x] 7. Test Suite — pytest tests for naming, extraction, edge cases

  **What to do**:
  - Create `test_extract_pngs.py` with pytest:
    - **Test naming — `TestNaming` class**:
      - `test_build_filename_with_label` — verify format with label
      - `test_build_filename_fallback` — verify fallback format without label
      - `test_build_filename_row_zero` — verify fallback when anchor_row=0
      - `test_sanitize_bad_chars` — verify `/\\:*?"<>|` replaced with `_`
      - `test_sanitize_leading_trailing` — strip whitespace and dots from edges
      - `test_col_letter` — parametrize: (0→A, 1→B, 25→Z, 26→AA, 27→AB)
    - **Test config — `TestConfig` class**:
      - `test_load_valid_config` — uses temp valid config file
      - `test_load_missing_config` — `SystemExit` raised with code 1
      - `test_load_invalid_schema` — `SystemExit` raised with code 1
    - **Test extraction — `TestExtraction` class**:
      - `test_extract_images_from_fixture` — run extractor on test_fixture.xlsx, verify count
      - `test_no_images_in_sheet` — text-only sheet returns 0
    - **Test integration — `TestIntegration` class**:
      - Run extract_pngs.py against test_fixture.xlsx via subprocess, verify output files named correctly
      - Verify "Sales" sheet images have labels, "Empty" uses fallback, "Edge" row-0 uses fallback

  **Must NOT do**:
  - Do NOT test openpyxl internals — test our code only
  - Do NOT skip test fixture creation — use the fixture from Task 5

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Comprehensive test design, parametrized tests, integration testing, subprocess handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 5 and 6)
  - **Blocks**: Final verification
  - **Blocked By**: Tasks 5, 6

  **References**:
  - `naming.py` — functions to test
  - `config.py` — functions to test
  - `extractor.py` — functions to test
  - `extract_pngs.py` — integration target
  - `test_fixture.xlsx` — test data from Task 5

  **Acceptance Criteria**:
  - [ ] `test_extract_pngs.py` exists with all test classes
  - [ ] `pytest test_extract_pngs.py -v` → all tests pass
  - [ ] At least 12 individual test cases
  - [ ] Integration test verifies actual output filenames from test_fixture.xlsx

  **QA Scenarios**:

  ```
  Scenario: All pytest tests pass
    Tool: Bash (PowerShell)
    Steps:
      1. pytest test_extract_pngs.py -v 2>&1
    Expected Result: All tests PASS, exit code 0
    Evidence: .sisyphus/evidence/task-7-pytest-output.txt

  Scenario: Naming tests cover edge cases
    Tool: Bash (PowerShell)
    Steps:
      1. pytest test_extract_pngs.py::TestNaming -v 2>&1
    Expected Result: All naming tests pass including row-0, col_letter, sanitize
    Evidence: .sisyphus/evidence/task-7-naming-tests.txt
  ```

  **Commit**: YES
  - Message: `test: pytest suite — naming, config, extraction, integration`
  - Files: `test_extract_pngs.py`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Review all Python files for: bare excepts, `pass` in except, unused imports, undefined names. Verify openpyxl is only used for cell reading (not `_images`). Check filename sanitization logic. Verify error handling catches all specified cases.
  Output: `Lint [PASS/FAIL] | Patterns [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Run script with valid config → verify output. Run with missing config → verify exit code 1. Run with invalid config → verify exit code 1. Run with non-existent input folder → verify exit code 2. Verify Book1.xlsx produces correctly named PNGs. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec (no creep). Check "Must NOT do" compliance. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **T1**: `feat: add project setup — requirements.txt and config template` — `requirements.txt`, `config.json`
- **T2**: `feat: add config module — load and validate config.json`
- **T3**: `feat: add image extractor — zipfile-based PNG extraction from XLSX`
- **T4**: `feat: add naming engine — label lookup, sanitization, fallback`
- **T5**: `feat: add test fixture — multi-sheet XLSX with PNGs and labels`
- **T6**: `feat: add CLI + orchestration — argparse, main loop, error handling`
- **T7**: `test: add pytest suite — naming, extraction, edge cases`

---

## Success Criteria

### Verification Commands
```bash
# Run the tool
python extract_pngs.py --config config.json
# Expected: stdout lists each extracted file, exit code 0

# Run tests
pytest test_extract_pngs.py -v
# Expected: all tests pass

# Missing config
python extract_pngs.py --config nonexistent.json
# Expected: exit code 1, stderr has error message

# Invalid config
echo '{"bad": "schema"}' > bad_config.json && python extract_pngs.py --config bad_config.json
# Expected: exit code 1, stderr has error message
```

### Final Checklist
- [x] All "Must Have" implemented and verified
- [x] All "Must NOT Have" absent from codebase
- [x] All pytests pass
- [x] Book1.xlsx processing yields correctly named PNGs
- [x] Script handles all edge cases from Metis review gracefully
