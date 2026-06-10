# Use Label Text Instead of Row Number in Filename

## TL;DR

> **Quick Summary**: Change naming from `PW planwork100_exist BKK01_row1.png` to `PW planwork100_exist BKK01_Bayface Before.png`.
>
> **Estimated Effort**: Trivial (1 function signature + 1 call site)

---

## What Changes

### png-extractor/src/naming.py — `build_pw_filename()`
```python
# Before:
def build_pw_filename(planwork, prefix, site, label_row):
    return f"PW {planwork}_{prefix} {site}_row{label_row}.png"

# After:
def build_pw_filename(planwork, prefix, site, label_text):
    from src.naming import sanitize
    return f"PW {planwork}_{prefix} {site}_{sanitize(label_text)}.png"
```

### png-extractor/extract_pngs.py — call site
```python
# Before:
filename = build_pw_filename(planwork, prefix, site, label_row)

# After:
filename = build_pw_filename(planwork, prefix, site, label_text)
```

### Tests — update expectations
```python
# Before:
assert result == "PW bkk007_exist bkk101_row3.png"

# After:
assert result == "PW bkk007_exist bkk101_My Label.png"
```

---

## TODOs

- [x] 1. Update build_pw_filename in naming.py — use label_text, sanitize it
- [x] 2. Update extract_pngs.py call site
- [x] 3. Update tests
- [x] 4. Verify with real XLSX + pytest
