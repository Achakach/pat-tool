# Plan: Zip Essential Files for Distribution

## TL;DR
> Package the PAT tool into a portable zip that runs on any computer with just `pip install -r requirements.txt && python run.py`.

## What to Include

```
PAT-tool.zip
├── run.py                          # orchestrator
├── pipeline.json                   # stage definitions
├── requirements.txt                # pip dependencies
├── matching.xlsx                   # shared matching data
├── AGENTS.md                       # documentation
│
├── 1-png-extractor/
│   ├── extract_pngs.py             # entry script
│   ├── config.json
│   └── src/                        # library code
│       ├── config.py
│       └── naming.py
│
├── 2-template-generator/
│   ├── generate.py
│   ├── config.json
│   └── template.xlsx               # template fixture
│
├── 3-column-copier/
│   ├── copier.py
│   ├── config.json
│   └── src/
│       ├── columns.py
│       └── print_setup.py
│
├── 4-cell-editor/
│   ├── edit.py
│   ├── config.json
│   └── src/
│       └── editor.py
│
└── 5-png-inserter/
    ├── insert.py
    ├── config.json
    └── src/
        ├── matcher.py
        └── inserter.py
```

## What to EXCLUDE

| Excluded | Why |
|----------|-----|
| `tests/` | Test files — not needed to run |
| `.sisyphus/` | Internal planning files |
| `.git/` | Git history |
| `__pycache__/`, `*.pyc` | Python cache |
| `.pytest_cache/` | Test cache |
| `test_fixture.xlsx` | Test fixture |
| `generate_fixture.py` | Test helper |
| Mock data (`input/`, `output/`, `xlsx/` dirs) | User provides their own data |

## After Unzipping

```bash
pip install -r requirements.txt
# Place your .xlsx files in the input/source folders
# Place PNGs in 5-png-inserter/input/
python run.py
```
