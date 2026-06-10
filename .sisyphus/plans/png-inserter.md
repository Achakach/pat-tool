# PNG Inserter Tool

## TL;DR

> **Quick Summary**: Match XLSX files to PNG folders using a configurable matching XLSX. Insert all PNGs from the matching folder into the XLSX. Position logic comes later.
>
> **Deliverables**:
> - `png-inserter/insert.py` — CLI entry
> - `png-inserter/config.json` — matching config
> - `png-inserter/src/matcher.py` — matching logic
> - `png-inserter/tests/` — pytest
>
> **Estimated Effort**: Medium

---

## Config

```json
{
  "matching_file": "./matching.xlsx",
  "matching_sheet": "Sheet1",
  "filename_col": "A",
  "planwork_col": "B",
  "xlsx_folder": "./xlsx",
  "png_folder": "./pngs",
  "output_folder": "./output"
}
```

## Matching File (user provides)

`matching.xlsx`, Sheet1:
```
A (filename_col)      B (planwork_col)
one.xlsx               siteA
(blank = same file)    siteB
two.xlsx               siteC
```

Blank filename → inherits from the row above. So `one.xlsx` gets both `siteA` and `siteB`.

## PNG Folder Structure

Flat — no subfolders:
```
pngs/
├── PW xxx_exist siteA_Bayface Before.png
├── PW xxx_exist siteA_Bayface After.png
├── PW xxx_new siteB_Bayface Before.png
├── PW xxx_new siteB_Bayface After.png
└── PW yyy_exist siteC_Bayface Before.png
```

## Flow

1. Read `matching.xlsx` → build `{filename: [planwork, planwork, ...]}` list
   - Blank filename cells inherit from the last non-blank row above
2. List all `.xlsx` in `xlsx_folder`
3. For each XLSX: get its list of planworks from the map
4. Scan flat `pngs/` folder — match PNGs whose filename **contains** any of the planworks
5. Copy XLSX to output, insert all matched PNGs (position TBD)
6. Report: which XLSX matched how many PNGs

## TODOs

- [x] 1. Create `png-inserter/` folder structure
- [x] 2. Config module — load + validate config.json
- [x] 3. Matcher module — read matching.xlsx, build filename→planwork map
- [x] 4. CLI — main loop, matching, copy XLSX, placeholder for insertion
- [x] 5. Tests — pytest for matching logic
- [x] 6. Verify — end-to-end

---

## Verification

```bash
cd png-inserter
python insert.py
# Expected: matches XLSX to PNG folders, copies to output
pytest tests/ -v
```
