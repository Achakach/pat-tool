# Multi-Source Append Fix - Learnings

## Bug
When multiple source files map to the same target XLSX in `3-column-copier/copier.py`, each source loads the clean template from `target_folder/`, overwriting previous output. Only the last source's data survives.

## Root Cause
Line 144 (`load_workbook(str(target_path))`) always used `target_path = target_folder / target_file`, pointing to the pristine template. Even after saving to `output_folder/`, subsequent sources would re-load the template, not the accumulated output.

## Fix
Added output existence check at lines 143-147 (after target-not-found guard, before workbook load):

```python
out_path = output_folder / target_file
if out_path.exists():
    target_path = out_path
    print(f"  APPEND: Using existing output as base ({target_file})")
```

- First source: no output yet → loads template (unchanged)
- Subsequent sources: output exists → loads accumulated output

## Verification
All 38 existing tests pass with no modifications to test code.
