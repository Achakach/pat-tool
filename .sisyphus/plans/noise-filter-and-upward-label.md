# Filter Noise PNGs + Upward Label Search

## TL;DR

> **Quick Summary**: (1) Skip embedded images smaller than 500 bytes to eliminate Excel noise/spacer PNGs. (2) When searching for a label, scan upward from the image until finding the first non-empty cell — not just exactly one row above.
>
> **Estimated Effort**: Quick (2 files, ~15 lines changed)

---

## What Changes

### Change 1: Noise filter in `extract_pngs.py`

After extracting PNG bytes from the zip, check if the byte size is below a threshold (500 bytes). If so, skip it silently.

```python
# In the extraction loop, after reading image bytes:
if len(image_data) < 500:
    continue  # skip tiny noise/spacer images
```

This eliminates the 161-163 byte transparent spacer PNGs that Excel embeds internally.

### Change 2: Upward label search in `naming.py` — `get_label()`

**Current behavior**: Looks at EXACTLY the cell one row above the image anchor. If that cell is empty, falls back to position-based naming.

**New behavior**: Scans upward from the row above the anchor. If the immediate row above is empty, keeps going up until finding the first row with text in that column.

```
Example:
  Row 1: (empty)
  Row 2: (empty)  
  Row 3: "Bayface Before"  ← image anchored at row 4 (0-indexed)
  Row 4: [IMAGE]

Old: looks at row 3 → "Bayface Before" ✓ (works if label is exactly 1 row above)
New: looks at row 3 → "Bayface Before" ✓ (same result when label is adjacent)

Example with gap:
  Row 1: "Chart Title"
  Row 2: (empty)
  Row 3: (empty)
  Row 4: [IMAGE]

Old: looks at row 3 → empty → fallback "row4_colA.png"
New: looks at row 3 → empty → row 2 → empty → row 1 → "Chart Title" ✓
```

If no text is found in any row above (all the way to row 1), falls back to position naming as before.

---

## TODOs

- [x] 1. Update naming.py — `get_label()` to scan upward until finding first non-empty cell
- [x] 2. Update extract_pngs.py — skip images smaller than 500 bytes
- [x] 3. Update tests — add test for upward label search (gap scenario), add test for noise filter
- [x] 4. Run pytest — verify all tests pass

---

## Verification

```bash
# Run against user's XLSX — should get only 2 images, both with correct labels
python extract_pngs.py --config config.json
# Expected: Sheet1_Bayface Before.png, Sheet2_Bayface After.png
# NOT expected: Sheet1_row1_colA.png, Sheet1_row11_colB.png (noise filtered)

pytest test_extract_pngs.py -v
# Expected: all pass
```
