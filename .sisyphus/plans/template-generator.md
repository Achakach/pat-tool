# Template XLSX Generator

## TL;DR

> **Quick Summary**: Read matching file → get unique filenames → copy template XLSX for each.
>
> **Estimated Effort**: Trivial (1 file)

---

## How It Works

```
matching.xlsx:
  one     siteA
  one     siteB   ← same file, skip
  two     siteC

template.xlsx (user provides)

      ↓

output/
├── one.xlsx     ← copy of template
└── two.xlsx     ← copy of template
```

---

## Tool Structure

```
template-generator/
├── generate.py
├── config.json
├── template.xlsx
└── output/
```

## config.json
```json
{
  "matching_file": "../png-inserter/matching.xlsx",
  "matching_sheet": "Sheet1",
  "filename_col": "filename",
  "planwork_col": "planwork",
  "template": "./template.xlsx",
  "output_folder": "./output"
}
```

Reuses the same matching.xlsx as png-inserter.

---

## TODOs

- [x] 1. Create template-generator/ folder + config
- [x] 2. CLI — read matching, get unique filenames, copy template
- [x] 3. Verify
