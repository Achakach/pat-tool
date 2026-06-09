# Move PNG Extractor into png-extractor/ Subfolder

## TL;DR

> **Quick Summary**: Move PNG extractor into `png-extractor/` folder (like cell-editor). Same structure, self-contained.
>
> **Estimated Effort**: Quick (move files + update paths)

---

## New Structure

```
PAT tool/
├── png-extractor/
│   ├── extract_pngs.py      ← cd png-extractor && python extract_pngs.py
│   ├── config.json          ← "./input", "./output"
│   ├── input/               ← put XLSX files here
│   ├── output/              ← PNGs land here
│   ├── conftest.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── naming.py
│   │   └── extractor.py
│   └── tests/
│       └── test_extract_pngs.py
│
├── cell-editor/
│   ├── edit.py
│   ├── config.json          ← "./input", "./output-edited"
│   ├── input/               ← put XLSX files here
│   ├── output-edited/       ← edited copies land here
│   └── ...
│
├── generate_fixture.py      ← stays root (utility)
├── test_fixture.xlsx        ← stays root (shared fixture)
└── requirements.txt         ← stays root (shared dep)
```

## What Changes

### Move files
- `src/` → `png-extractor/src/`
- `tests/test_extract_pngs.py` → `png-extractor/tests/test_extract_pngs.py`
- `extract_pngs.py` → `png-extractor/extract_pngs.py`
- `config.json` → `png-extractor/config.json`
- `conftest.py` → `png-extractor/conftest.py`

### Update config.json
```json
{
  "input_folder": "./input",
  "output_folder": "./output"
}
```

### Also update cell-editor config.json
```json
{
  "input_folder": "./input",
  "output_folder": "./output-edited",
  "replacements": { ... }
}
```

### Create input/output folders
- `png-extractor/input/`
- `png-extractor/output/`
- `cell-editor/input/`
- `cell-editor/output-edited/`

### Clean up root
- Remove old `input/` and `output/` at root level (no longer needed)

### Update test paths
- `FIXTURE = Path(__file__).parent.parent.parent / "test_fixture.xlsx"`
- `EXTRACT_SCRIPT = Path(__file__).parent.parent / "extract_pngs.py"`

---

## TODOs

- [x] 1. Create `png-extractor/` folder structure with own input/output
- [x] 2. Move all extractor files into `png-extractor/`
- [x] 3. Update config.json paths (both tools), create input/output dirs
- [x] 4. Update cell-editor config to use own input folder
- [x] 5. Verify both tools work independently

---

## Verification

```bash
cd png-extractor
python extract_pngs.py
pytest tests/test_extract_pngs.py -v

cd ../cell-editor
python edit.py
pytest tests/test_editor.py -v
```
