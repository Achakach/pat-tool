# PAT Tool — Agent Guide

## Architecture

5 pipeline tools in numbered folders. Run in order. Each tool is self-contained: `src/` for library code, `tests/` for pytest, `config.json` for settings.

| # | Folder | Entry | Purpose |
|---|--------|-------|---------|
| 1 | 1-png-extractor/ | extract_pngs.py | Extract PNGs from XLSX. Names them `PW {planwork}_{exist/new} {site}_{label}.png`. Only sheets with a `PW` sheet plus `exist`/`new` prefix sheets are processed. |
| 2 | 2-template-generator/ | generate.py | Copy template XLSX to one per unique filename from `matching.xlsx`. |
| 3 | 3-column-copier/ | copier.py | Build temp planwork/IP columns, copy configured columns to the target sheet, then clean temp columns from source. |
| 4 | 4-cell-editor/ | edit.py | Find cells by prefix and replace the cell to the RIGHT. Handles merged cells. `match_mode`: `first` or `all`. |
| 5 | 5-png-inserter/ | insert.py | Match PNGs to XLSX sheets, purge template rows once per sheet, insert PNGs with labeled site rows. |

`run.py` at the repo root orchestrates all 5 stages via `pipeline.json` and copies outputs between stages automatically.

## Shared State

- `matching.xlsx` (root) — used by tools 2, 3, and 5. Row 1 = headers (`Site`, `PW Number`), data from row 2. Blank `Site` cells inherit from the row above.
- `requirements.txt` — `openpyxl>=3.0,<4.0`, `Pillow>=9.0`, `pytest>=7.0`.
- `generate_fixture.py` — recreates `test_fixture.xlsx`.
- `dep/` — legacy/archive versions. Do not modify, import from, or run tests here.
- `issue.md` — known issues and technical debt inherited from `.sisyphus/handover.md` plus the V7 baseline.

## Commands

```bash
pip install -r requirements.txt

# Full pipeline (recommended)
python run.py

# Individual tools
python extract_pngs.py
python generate.py
python copier.py
python edit.py
python insert.py

# Regenerate test fixture
python generate_fixture.py
```

Run per-tool from inside its own folder; each loads `config.json` from that folder. No CLI flags are supported.

## Tests

Each tool has its own `tests/` with a `conftest.py` that adds the tool root to `sys.path`.

```bash
cd 1-png-extractor && python -m pytest tests/ -v
cd 2-template-generator && python -m pytest tests/ -v
cd 3-column-copier && python -m pytest tests/ -v
cd 4-cell-editor && python -m pytest tests/ -v
cd 5-png-inserter && python -m pytest tests/ -v

# Root-level pipeline orchestrator tests only
python -m pytest tests/ -v
```

Run tool tests from inside the tool folder. Running pytest from the repo root collects duplicate `tests` packages and old `dep/` versions, which causes import collisions.

## Key Quirks

- **No CLI flags.** Each tool reads `config.json` next to its entry script. `main()` accepts a config dict only for tests.
- **Relative paths in config** are relative to the tool folder (e.g. `./input`, `../matching.xlsx`).
- **Extractor filters:** requires a sheet named `PW {planwork}`; only processes sheets matching `exist|new {site}`; skips images smaller than `noise_threshold`; labels are found by scanning upward from the image anchor.
- **PNG filename format:** `PW {planwork}_{prefix} {site}_{label}.png`. `_` separates sections. Collision handling appends `_1`, `_2`. The inserter strips trailing `_\d+` from labels when matching sheets.
- **Sheet matching:** sheet names like `2.1. Bayface_Before` are cleaned (strip number prefixes, underscores to spaces, parentheticals, lowercase) for comparison only.
- **Column copier:** `action: "copy"` builds temp `planwork`/`ip_lookup` columns at `build_at`, copies configured source columns to the target, then deletes the temp columns from the source. `action: "cleanup"` just deletes the temp columns. Does NOT shift existing image anchors when rows are inserted.
- **Cell editor:** prefix-match → replace the cell to the right. Skips past merged ranges.
- **PNG inserter:** purges rows from `purge_from_row` once per matched sheet; label rows merge `A` to `label_merge_to_col`; `insert_gap_rows` apply before and after each image; A4 row-height math uses a hard-coded 15 pt default. A4 page snapping is controlled by `page_break_before_label` and `print_title_rows`.
