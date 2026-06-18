
## Task 5: Remove E2E Monkey-Patch (2026-06-17)

### What Was Removed
- `_OPENPYXL_PATCH` variable (multiline string with monkey-patch code for autoPageBreaks)
- `patch_openpyxl` parameter from `_write_stage_script()` function signature
- Docstring referencing the parameter
- `if patch_openpyxl:` conditional block
- `patch_openpyxl=True` from both call sites (stages 3 and 5)

### Verification
- `python -m pytest tests/test_pipeline_e2e.py -v --tb=long` → **1 passed** (WITHOUT monkey-patch)
- `python -m pytest tests/test_run.py -v --tb=short` → **5 passed**
- E2E test validates the real fix works end-to-end — no patching needed

### Key Insight
The surgical try/except fixes in copier.py (gate moved inside `if page_break_enabled:`) and inserter.py (try/except on autoPageBreaks) plus print_setup.py (try/except on autoPageBreaks) are sufficient. The monkey-patch was redundant — confirming the targeted approach was correct.
