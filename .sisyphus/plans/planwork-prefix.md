# Add PlanWork Prefix to PNG Names

## TL;DR

> **Quick Summary**: If XLSX has a sheet named "PW {name}", all PNGs from that file get `{name}_` prefixed to their filenames.
>
> **Estimated Effort**: Quick (2 files, ~15 lines)

---

## How It Works

### Sheet scan
```
XLSX sheets: "before bkk007", "PW bkk007", "after bkk101", "Summary"
                                           ↓
                         planwork = "bkk007"
```

### Naming
```
Before: Sheet1_Bayface Before.png
After:  bkk007_Sheet1_Bayface Before.png  ← planwork prefix added
```

No "PW" sheet? No prefix — same as current behavior.

---

## What Changes

### png-extractor/src/naming.py — `build_filename()`
Add `planwork: str | None` parameter:
```python
def build_filename(sheet_name, label, anchor_row, anchor_col, planwork=None):
    ...
    # Build base name as before
    if label:
        base = f"{sheet}_{lbl}"
    else:
        base = f"{sheet}_row{row}_col{col}"
    
    # Add planwork prefix if present
    if planwork:
        return f"{planwork}_{base}.png"
    return f"{base}.png"
```

### png-extractor/extract_pngs.py
After opening the workbook, scan for a "PW" sheet:
```python
import re

planwork = None
for ws in wb.worksheets:
    m = re.match(r'^PW\s+(.+)', ws.title, re.IGNORECASE)
    if m:
        planwork = m.group(1).strip()
        break
```

Then pass `planwork` to `build_filename()`.

---

## TODOs

- [ ] 1. Update naming.py — add planwork parameter to build_filename
- [ ] 2. Update extract_pngs.py — scan for "PW" sheet, pass planwork
- [ ] 3. Update tests — add planwork prefix test
- [ ] 4. Verify with real XLSX + pytest

---

## Verification

```bash
cd png-extractor
python extract_pngs.py
# Expected: bkk007_Sheet1_Bayface Before.png (if PW sheet exists)

pytest tests/test_extract_pngs.py -v
```
