# Sheet Matching for PNG Insertion

## TL;DR

> **Quick Summary**: Match PNG label text to XLSX sheet names. Strip noise from sheet names for comparison. Insert PNG, purge once per sheet.
>
> **Estimated Effort**: Medium

---

## How It Works

### Step 1 — Extract label from PNG name
```
PNG: "PW planwork100_exist BKK01_Bayface Before.png"
     → label = "Bayface Before" (last part after the site name)
```

Wait — the PNG naming format is: `PW {planwork}_{prefix} {site}_{label}.png`
So label = everything after `{prefix} {site}_`

From the extractor: `build_pw_filename(planwork, prefix, site, label_text)`
→ `PW planwork100_exist BKK01_Bayface Before.png`

So the label is in the filename between the site and `.png`. We need to extract it.

### Step 2 — Clean sheet name for comparison
```
Sheet: "2.1. Bayface_Before" → clean: "Bayface Before"
Sheet: "4.1 Alarm Before(7)" → clean: "Alarm Before"
```

Clean function: remove leading numbers/dots, replace underscores with spaces, strip parentheses content.

### Step 3 — Match
```
label "Bayface Before" → matches cleaned sheet "Bayface Before" → insert into "2.1. Bayface_Before"
```

---

## Implementation

### 4-png-inserter/src/inserter.py — add functions

```python
def extract_label_from_filename(filename: str) -> str:
    """Extract label text from PNG filename.
    'PW planwork100_exist BKK01_Bayface Before.png' → 'Bayface Before'"""
    stem = Path(filename).stem
    # Format: PW {planwork}_{prefix} {site}_{label}
    # Label is everything after the site part
    parts = stem.split("_")
    # Find where the site ends — after prefix_site pattern
    # Pattern: PW_planwork_prefix_site_label...
    # Skip PW, planwork, skip prefix_site, rest is label
    if len(parts) >= 3:
        # parts[0]="PW", parts[1]=planwork, parts[2]=prefix_site, rest=label
        label_parts = parts[3:]  # everything after prefix_site
        return " ".join(label_parts)
    return stem

def clean_sheet_name(name: str) -> str:
    """Clean sheet name for matching.
    '2.1. Bayface_Before' → 'bayface before'
    '4.1 Alarm Before(7)' → 'alarm before'"""
    import re
    # Remove leading numbers and dots (e.g., "2.1. ")
    name = re.sub(r'^\d+\.?\d*\.?\s*', '', name)
    # Remove parenthetical suffixes (e.g., "(7)")
    name = re.sub(r'\([^)]*\)', '', name)
    # Replace underscores with spaces
    name = name.replace("_", " ")
    # Normalize whitespace and lowercase
    return " ".join(name.split()).lower()

def find_matching_sheet(wb, label: str) -> str | None:
    """Find sheet whose cleaned name matches the label. Returns sheet name or None."""
    clean_label = clean_sheet_name(label)
    for sheet_name in wb.sheetnames:
        if clean_sheet_name(sheet_name) == clean_label:
            return sheet_name
    return None
```

### 4-png-inserter/insert.py — main loop update

In the PNG matching loop, for each matched PNG:
1. Extract label from filename
2. Find matching sheet
3. Purge sheet if not already purged
4. Insert PNG (TBD — placeholder for now)

---

## TODOs

- [x] 1. Add extract_label, clean_sheet_name, find_matching_sheet to inserter.py
- [x] 2. Wire sheet matching into insert.py main loop
- [x] 3. Wire purge into matched sheet
- [x] 4. Tests + verify
