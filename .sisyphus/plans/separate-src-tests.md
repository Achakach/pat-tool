# Separate Source and Test Files into Folders

## TL;DR

> **Quick Summary**: Move core Python files into `src/`, test file into `tests/`. Update all imports and paths.
>
> **Estimated Effort**: Quick (move files + fix imports)

---

## New Structure

```
PAT tool/
├── extract_pngs.py          (stays at root — the file you run)
├── src/
│   ├── __init__.py          (empty)
│   ├── config.py
│   ├── naming.py
│   └── extractor.py
├── tests/
│   └── test_extract_pngs.py
├── config.json
├── requirements.txt
├── generate_fixture.py      (stays at root)
├── test_fixture.xlsx        (stays at root)
└── input/                   (stays as-is)
```

## What Changes

### Imports

- **extract_pngs.py** (root): `from config import` → `from src.config import`, same for `naming`
- **config.py** (src/): no changes
- **naming.py** (src/): no changes
- **extractor.py** (src/): no changes
- **test_extract_pngs.py** (tests/): `from naming import` → `from src.naming import`, `from config import` → `from src.config import`

### Config path (no change)

`extract_pngs.py` stays at root, so `Path(__file__).parent / "config.json"` still works unchanged.

### Test paths

- `FIXTURE`: `Path(__file__).parent.parent / "test_fixture.xlsx"`
- `EXTRACT_SCRIPT`: `Path(__file__).parent.parent / "extract_pngs.py"`

---

## TODOs

- [x] 1. Create `src/` (with `__init__.py`) and `tests/` folders
- [x] 2. Move files: config.py, naming.py, extractor.py → `src/`
- [x] 3. Move test_extract_pngs.py → `tests/`
- [x] 4. Update imports in extract_pngs.py and test_extract_pngs.py
- [x] 5. Verify: `python extract_pngs.py` + `pytest tests/test_extract_pngs.py -v` — all pass

---

## Verification

```bash
python extract_pngs.py
pytest tests/test_extract_pngs.py -v
```
