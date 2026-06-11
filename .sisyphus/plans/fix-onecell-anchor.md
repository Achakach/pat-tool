# Fix oneCellAnchor Bug in Extractor

## TL;DR

> Add `oneCellAnchor` handling to image position parser. Currently only `twoCellAnchor` parsed — images from `ws.add_image()` silently skipped.

## What Changes

### 1-png-extractor/extract_pngs.py — `_parse_drawing_image_map`

After the `twoCellAnchor` loop, add identical loop for `oneCellAnchor`:

```python
# Also handle oneCellAnchor (from ws.add_image or direct Excel insert)
for anchor in _local_findall(dr_xml.getroot(), "oneCellAnchor"):
    blip = _local_find(anchor, "blip")
    from_el = _local_find(anchor, "from")
    if blip is None or from_el is None:
        continue
    r_id = blip.get(f"{{{_DOC_REL}}}embed") or blip.get(f"{{{_DOC_REL}}}link")
    if r_id is None:
        continue
    image_path = rId_to_image.get(r_id)
    if image_path is None:
        continue
    row_el = _local_find(from_el, "row")
    col_el = _local_find(from_el, "col")
    if row_el is None or col_el is None:
        continue
    row = int(row_el.text)
    col = int(col_el.text)
    # Skip if same position already captured from twoCellAnchor
    if (row, col) not in anchors:
        anchors[(row, col)] = image_path
```

## TODOs

- [x] 1. Add oneCellAnchor loop to _parse_drawing_image_map in extract_pngs.py
- [x] 2. Add test: XLSX with oneCellAnchor image → extracted correctly
- [x] 3. Test with e2e_source.xlsx — should extract both images
- [x] 4. Run full pytest — all must pass
- [x] 5. Restore noise_threshold to 5000
