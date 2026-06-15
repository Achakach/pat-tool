# PAT Tool — Session Handout

## Pipeline (5 tools)

```
1-png-extractor → 2-template-generator → 3-column-copier → 4-cell-editor → 5-png-inserter
```

Run: `python run.py`

## Current State

| Tool | Status | Tests |
|------|--------|-------|
| 1-png-extractor | ✅ Ready | 39/39 |
| 2-template-generator | ✅ Ready | — |
| 3-column-copier | ✅ Ready | 8/8 |
| 4-cell-editor | ✅ Ready | 5/5 |
| 5-png-inserter | ✅ Mostly | 14/14 |

## Key Quirks

- No CLI flags — each tool reads `config.json` in its own folder
- Shared `matching.xlsx` at root — `Site` (filename), `PW Number` (planwork)
- PNG naming: `PW {planwork}_{exist/new} {site}_{label}.png`
- oneCellAnchor images now extracted (bug fixed)
- 3-column-copier: `paste_mode: "append"` stacks data from multiple sources

## 5-png-inserter Config

```json
{
  "matching_file": "../matching.xlsx",
  "xlsx_folder": "./xlsx",
  "png_folder": "./input",
  "output_folder": "./output",
  "purge_from_row": 10,
  "label_merge_to_col": "K",
  "insert_gap_rows": 1,
  "image_insert_col": "C",
  "image_display_width": 200
}
```

## Removed (simplified)

- `a4_page_rows` — page boundary snap removed
- `print_title_rows` — header repeat removed
- `label_offset` — removed
- All page boundary logic stripped

## Open Issue

Images can split across printed pages. No page boundary protection active. User needs to:
- Adjust `image_display_width` for smaller images
- Adjust `insert_gap_rows` for spacing
- Use Excel Print Preview to check page breaks manually

## What Works

- Labels + images correctly placed together
- Site grouping (same site = one label, images stacked)
- One site per sheet layout
- A4 paper + fit-to-width printing
- Merged label cells, bold, gray background

## Files to Place

Before running:
- `1-png-extractor/input/` — source XLSX with images
- `3-column-copier/source/` — same source XLSX for column copying
- `2-template-generator/template.xlsx` — template for target files
- `matching.xlsx` — planwork-to-filename mappings
