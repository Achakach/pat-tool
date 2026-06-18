# Copy Source Cell Alignment

## TL;DR

> **Summary**: When pasting cell values, also copy the alignment (horizontal, vertical, wrap_text) from source to target.
>
> **Effort**: Quick — 2 lines in copier.py

## The Fix

In `copier.py` paste loop (~line 243), after `cell.value = val`, add:

```python
from copy import copy  # at top of file

# In paste loop:
cell.alignment = copy(src_cell.alignment)
```

## TODOs

- [ ] 1. Add `from copy import copy` import to copier.py
- [ ] 2. Add `cell.alignment = copy(src_cell.alignment)` after `cell.value = val`
- [ ] 3. Run full test suite — 41 pass

## Final Verification

- [ ] F1. All tests pass
