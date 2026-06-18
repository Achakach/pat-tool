## 1-png-extractor CLI tests

- Copy approach: `_setup(tmp_path)` copies `extract_pngs.py` + `src/` into temp dir `tool1/`. No backup/restore of real config.json needed.
- `noise_threshold: 0` critical — default 5000 filters out test PNGs (~160 bytes, 1x1 pixel).
- PW sheet naming: must match `^PW\s+(.+)` regex, e.g. "PW XX001" → planwork="XX001".
- Sheet naming: `parse_prefix` requires `exist|new` followed by whitespace + site name, e.g. "exist TestSite".
- Image anchor: `img.anchor = "B3"` → XML anchor row=2, col=1 (0-indexed). Label in B2 (one cell above) so `get_label_with_row` finds it.
- openpyxl `ws.add_image()` produces `oneCellAnchor` in drawing XML. Script parses both `oneCellAnchor` and `twoCellAnchor`.
- Exit codes: config missing/invalid → 1 (from `load_config`), input folder missing → 2 (from `main`).
- Subprocess `cwd=str(d)` makes config paths relative to script dir work.
- All 3 tests pass, all 35 existing tests unaffected (38 total, 3.09s).

## 2-template-generator CLI tests

- Nested directory structure critical: config uses `../matching.xlsx` resolved relative to `Path(__file__).parent` (the script dir). So matching.xlsx goes at tmp_path level, tool2/ holds generate.py + config.json + template.xlsx.
- `_setup` helper copies generate.py via shutil.copy2; config.json written via json.dumps.
- Subprocess uses cwd=str(d) so relative paths in config resolve correctly.
- Missing config.json → open() raises FileNotFoundError → Python prints traceback to stderr, exit != 0 (not exactly 1).
- Missing template → explicit `sys.exit(1)`, stderr has "Template file not found".
- All 3 tests pass in 1.71s (subprocess overhead).

## 4-cell-editor CLI tests

- Tool 4 simplest: no matching.xlsx dependency, only input/output folders + replacements dict.
- `_setup` pattern same as other tools: copy edit.py + src/ into tmp_path, write config.json. `cwd=str(d)` for subprocess.
- edit.py `main()` with `config=None` (subprocess path) resolves `input_folder`/`output_folder` relative to `Path(__file__).parent`, so config uses `"./input"`, `"./output"`.
- `match_mode` key required in config (tool reads `config.get("match_mode", "first")`).
- Exit codes: empty replacements → 1, missing input folder → 2. Missing config.json → unhandled FileNotFoundError → Python traceback → exit != 0 (not exactly 1).
- test_happy_path: verify stdout has "Done" + "Changed 1 cell", output XLSX has A1 untouched, B1 replaced.
- test_missing_config: no config_dict → subprocess exits non-zero.
- test_missing_input_folder: valid config but input/ dir not created → exit 2, stderr "Input folder not found".
- All 3 CLI tests pass, all 12 existing tests unaffected (15 total, 1.84s).

## 3-column-copier CLI tests

- `_setup` helper copies `copier.py` + `src/` into `tmp_path/tool3/`. Config uses relative paths (`../matching.xlsx`, `./source`, `./target`, `./output`).
- **Tool 3 unique**: returns exit 0 on almost everything — silently skips. Must validate via stdout content, not just exit code.
- Subprocess: `[sys.executable, str(d / "copier.py")]` with `cwd=str(d)`. Captures stdout+stderr.
- Source XLSX: needs `PW {planwork}` sheet for planwork extraction + data sheet with non-empty rows.
- `find_matching_sheet()`: exact comparison after `clean_sheet_name()`. "IP" in config matches sheet named "IP" (NOT "IP & Port Assignment").
- Planwork column: `build_pw_column` writes to `build_at` col (Q), paste loop reads same col and writes to `paste_to` (J).
- `source_folder.glob("*.xlsx")`: empty generator when dir doesn't exist — no crash, exit 0.
- `output_folder.mkdir(parents=True, exist_ok=True)`: runs BEFORE file loop; creates output dir even with empty source.
- `test_missing_source_folder`: exit 0, stdout has no "Processing". `print("\nDone.")` still prints (from after loop), but "Processing" assertion is de facto proxy for "no files found".
- All 3 CLI tests pass, all 28 existing tests unaffected (31 total, 2.31s).

## 5-png-inserter CLI tests

- Nested structure: tool5/ holds insert.py + src/ + config.json. matching.xlsx at tmp_path level (`../matching.xlsx`). Output folder is `./out` (NOT `./output` unlike other tools).
- PNG naming: `PW {planwork}_{prefix} {site}_{label}.png`. `extract_label` uses last `_` segment. `find_matching_sheet` does fuzzy match (strip number prefixes, underscores→spaces, parentheticals).
- Must disable page breaks: `page_break_before_label: false`, `print_title_rows: null`, `a4_page_rows: null` — otherwise openpyxl autoPageBreaks crash with programmatic fixtures.
- XLSX needs 12+ rows because `purge_from_row: 10` deletes rows 10+ during purge step. After purge, label inserted at row 10 works fine (openpyxl handles row beyond max_row).
- Exit codes: matching file missing → 1, xlsx folder missing → 2. Missing config.json → FileNotFoundError traceback → exit != 0.
- test_missing_xlsx_folder requires matching.xlsx to exist (checked BEFORE xlsx folder guard in main()).
- `_CFG_BASE` constant avoids duplicating config dict across tests.
- All 3 CLI tests pass, all 46 existing tests unaffected (49 total, 2.70s).
