# Decisions — xlsx-png-extractor

## Architecture
- `config.py` — JSON config loading + validation (stdlib only)
- `extractor.py` — zipfile-based PNG extraction (stdlib only)
- `naming.py` — label lookups + filename building (uses openpyxl for cell reading)
- `extract_pngs.py` — CLI orchestrator (argparse, combines all modules)
- `test_fixture.xlsx` — multi-sheet test data
- `test_extract_pngs.py` — pytest tests

## Key Decisions
- zipfile for extraction (avoids openpyxl `_images` private API)
- openpyxl only for cell value reading (stable public API)
- Include XLSX stem in filename to prevent cross-file collisions
- Row-0 edge case: immediate fallback (no row above)
- Duplicate names: append `_{N}` counter
