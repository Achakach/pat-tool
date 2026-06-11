# Fix Image Splitting — Page Break Per Image

## Problem

Images split across pages. Row breaks at labels don't prevent image splitting mid-render.

## Root Cause

Excel renders images at pixel size. If image is taller than remaining page space → splits.

## Fix

Page break before every image row. Label + image always on same page.

### src/inserter.py — both insert functions

After `ws.add_image(img, ...)`, add:
```python
    ws.row_breaks.append(Break(id=img_row))
```

## Result

```
Page 1: BKK01 label + image 1
Page 2: image 2 (no label, same site)
Page 3: image 3
Page 4: BKK02 label + image 1
```

First image per site = label on same page. No splitting.

## TODOs

- [ ] 1. Add page break before image row in insert_png + insert_png_no_label
- [ ] 2. Remove label-level page break (redundant — image break covers it)
- [ ] 3. Test — verify no splitting in Print Preview
