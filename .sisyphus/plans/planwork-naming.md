# New Naming: PW + Prefix + Site + Row

## TL;DR

> **Quick Summary**: Only extract PNGs from "exist"/"new" sheets. Name format: `PW {planwork}_{prefix} {site}_row{label_row}.png`. Other sheets skipped entirely.
>
> **Estimated Effort**: Medium (2 files, logic overhaul)

---

## How It Works

```
XLSX sheets:
  "PW bkk007"           → planwork = "bkk007"
  "exist bkk101"         → prefix = "exist", site = "bkk101"  ✓ extract
  "new bkk999"           → prefix = "new",   site = "bkk999"   ✓ extract
  "Summary"              → skip (no exist/new)
  "Sheet1"               → skip

Image in "exist bkk101", label found at row 3:
  → PW bkk007_exist bkk101_row3.png
```

---

## What Changes

### png-extractor/src/naming.py

**New: `parse_prefix(sheet_name: str) -> tuple[str, str] | None`**
```python
def parse_prefix(sheet_name):
    """Extract (prefix, site) from 'exist bkk101' or 'new bkk999'. None if no match."""
    m = re.match(r'(exist|new)\s+(.+)', sheet_name, re.IGNORECASE)
    if m:
        return (m.group(1).lower(), m.group(2).strip())
    return None
```

**New: `get_label_with_row(ws, anchor_row, anchor_col) -> tuple[str, int] | None`**
Like `get_label()` but returns `(text, row)` where row is the 1-indexed openpyxl row where text was found. Returns `None` if nothing found.

**New: `build_filename(planwork, prefix, site, label_row) -> str`**
```python
def build_filename(planwork, prefix, site, label_row):
    return f"PW {planwork}_{prefix} {site}_row{label_row}.png"
```

### png-extractor/extract_pngs.py

- After opening workbook: scan sheets for `PW xxx` → extract planwork
- In extraction loop: skip sheets without exist/new prefix
- Pass parsed prefix/site + label row to new build_filename

---

## TODOs

- [x] 1. Update naming.py — parse_prefix, get_label_with_row, build_filename
- [x] 2. Update extract_pngs.py — scan PW sheet, filter exist/new only, new naming
- [x] 3. Update tests — new naming format, skip logic
- [x] 4. Verify with real XLSX + pytest

---

## Verification

```bash
cd png-extractor
python extract_pngs.py

# Expected for XLSX with "PW bkk007" and "exist bkk101":
#   PW bkk007_exist bkk101_row3.png
# Only exist/new sheets extracted
```
