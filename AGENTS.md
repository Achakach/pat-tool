# PAT Tool — Agent Guide

## Architecture

4 pipeline tools, each in a numbered folder. Run in order. Each tool is self-contained: `src/` for library code, `tests/` for pytest, `config.json` for settings.

| # | Folder | Entry | Purpose |
|---|--------|-------|---------|
| 1 | 1-png-extractor/ | extract_pngs.py | Extract PNGs from XLSX. Names them PW {planwork}_{exist/new} {site}_{label}.png. Only sheets with exist/new prefix and a PW sheet present are processed. |
| 2 | 2-template-generator/ | generate.py | Copy template XLSX to one per unique filename from matching.xlsx. |
| 3 | 3-cell-editor/ | edit.py | Find cells by prefix then replace the cell to the RIGHT. Handles merged cells. match_mode: first or all. |
| 4 | 4-png-inserter/ | insert.py | Match PNGs to XLSX sheets, purge template rows, insert PNGs with labeled site rows. |

## Shared State

- matching.xlsx (root) — used by tools 2 and 4. Row 1 = headers (Site, PW Number), data from row 2. Blank Site cells inherit from above.
- requirements.txt — only dependency is openpyxl>=3.0,<4.0.
- test_fixture.xlsx — test fixture file (kept by .gitignore negate rule).

## Commands

```bash
pip install -r requirements.txt

cd 1-png-extractor && python extract_pngs.py
cd 2-template-generator && python generate.py
cd 3-cell-editor && python edit.py
cd 4-png-inserter && python insert.py

python -m pytest tests/ -v
```

## Key Quirks

- No CLI flags: all tools hardcode config.json next to the entry script.
- Relative paths in config: paths relative to the tool folder (e.g., ./input, ../matching.xlsx).
- .gitignore blocks *.xlsx except !test_fixture.xlsx.
- PNG naming format: PW {planwork}_{prefix} {site}_{label}.png. _ separates sections. Collision handling appends _1, _2. Inserter strips trailing _\d+ from labels.
- Sheet matching: sheet names like "2.1. Bayface_Before" are cleaned (strip number prefixes, underscores to spaces, parentheticals) for comparison only.
- Cell editor: replaces the cell to the RIGHT of the matched cell. Skips past merged ranges.
- PNG inserter: purges rows from purge_from_row ONCE per matched sheet. Label rows merge A to label_merge_to_col. insert_gap_rows applies before and after each image. Row spacing calculated from actual PNG pixel height.

## Test Conventions

- Each tool has tests/ folder with pytest.
- conftest.py adds tool root to sys.path so from src.xxx imports work.
- Fixtures use tmp_path (auto-cleaned by pytest).
