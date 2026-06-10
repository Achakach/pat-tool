# Extract PNGs into Site Subfolders

## TL;DR

> **Quick Summary**: Add folder creation to png-extractor. Sheet names starting with `exist` or `new` → extract site name → create subfolder for that site → save PNGs inside.
>
> **Estimated Effort**: Quick (1 file, ~10 lines)

---

## How It Works

### Sheet name → folder mapping
```
Sheet: "exist bkk007"  →  site: "bkk007"  →  output/bkk007/exist bkk007_Bayface.png
Sheet: "new bkk101"    →  site: "bkk101"  →  output/bkk101/new bkk101_Bayface.png
Sheet: "Summary"       →  no prefix       →  output/Summary_row2_colA.png (flat)
```

### Extraction logic
Extract `exist` or `new` (case insensitive) from the beginning of the sheet name. Everything after is the site name. Strip whitespace.

```
"exist bkk007"    →  prefix="exist", site="bkk007"
"New BKK101"      →  prefix="new",  site="BKK101"
"EXIST   abc"     →  prefix="exist", site="abc"
"random sheet"    →  no match → flat output
```

---

## What Changes

### png-extractor/extract_pngs.py
In the extraction loop where `out_path` is built (around line 230), add folder logic:

```python
# Check if sheet name has exist/new prefix → create subfolder
import re
site_match = re.match(r'(exist|new)\s+(.+)', sheet_name, re.IGNORECASE)
if site_match:
    site = site_match.group(2).strip()
    site_folder = output_folder / site
    site_folder.mkdir(parents=True, exist_ok=True)
    out_path = site_folder / filename
else:
    out_path = output_folder / filename
```

## TODOs

- [ ] 1. Add `import re` and site-folder logic to extract_pngs.py
- [ ] 2. Update tests to verify folder creation
- [ ] 3. Run tool against real XLSX + pytest

---

## Verification

```bash
cd png-extractor
python extract_pngs.py
# Expected: PNGs from "exist bkk007" in output/bkk007/
# Expected: PNGs from "new bkk101" in output/bkk101/
# Expected: other sheets in output/ (flat)

pytest tests/test_extract_pngs.py -v
```
