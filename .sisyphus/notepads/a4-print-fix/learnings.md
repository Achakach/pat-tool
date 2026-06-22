
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

## Task 3: Update rows_needed Test Assertions for RED Phase (2026-06-18)

### Changes Made
- test_single_image_taller_than_page: Updated comments (rows_needed 26→25, img_end 34→33, return 40→39). Assertions unchanged (label@11, next_row>6)
- test_overflow_with_headers_pushes: Updated comment (rows_needed 6→5). Changed assertion from 'next_row > 10' to 'next_row == 17'
- test_overflow_no_headers_unchanged: Added comment (rows_needed = ceil(75/15) = 5). Changed assertion from 'next_row > 10' to 'next_row == 17'

### RED Phase Result
- 2 tests FAIL (return 18 != expected 17): confirms old 'int()+1' formula still in use
- 1 test PASS (loose assertion '> 6' tolerant to both 40 and 39)
- Debug output confirms: 'rows_needed=6' from 'max(1, int(display_h * 0.75 / 15) + 1)'

### Key Insight
- For tests where snap+overflow keeps label at same row regardless of rows_needed, only next_row differs (40→39, 18→17)
- To ensure RED phase failure, had to change assertions from loose inequalities to exact values
