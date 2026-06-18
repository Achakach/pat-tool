# Shift Image Anchors on Insert

## TL;DR

> **Quick Summary**: After `insert_rows`, manually shift all image anchors below the paste row down by the same number of rows.
>
> **Deliverables**: `copier.py` — ~5 lines after `insert_rows()` call
>
> **Estimated Effort**: Quick
> **Critical Path**: Single task

---

## Context

openpyxl's `insert_rows()` shifts cell content and merged ranges but does NOT adjust image anchors. Images stay frozen while cells move, causing overlap. Fix: manually shift anchors.

## The Fix

After `tws.insert_rows(paste_row, src_data_rows)` (line ~186), add:

```python
# Shift image anchors below paste row down
paste_row_0 = paste_row - 1  # 0-indexed
for img in tws._images:
    if hasattr(img.anchor, '_from') and img.anchor._from.row >= paste_row_0:
        img.anchor._from.row += src_data_rows
        if hasattr(img.anchor, 'to') and img.anchor.to:
            img.anchor.to.row += src_data_rows
```

---

## TODOs

- [ ] 1. Add anchor-shifting loop to `copier.py` after `insert_rows()` call
- [ ] 2. Run full test suite — 41 tests pass

---

## Final Verification Wave

- [ ] F1. Full test suite passes
- [ ] F2. Image anchor shifts verified manually

---

## Success Criteria

```bash
cd 3-column-copier && python -m pytest tests/ -v
# Expected: all 41 pass
```
