# Insert Mode — Left Aligned vs Centered

## TL;DR

> **Quick Summary**: Add `insert_mode` config: `"left"` or `"center"`. When centered, calculate starting column so image sits in the middle of A4.
>
> **Estimated Effort**: Quick (1 function + config)

---

## How It Works

**Mode `"left"`** (current): Image at `image_insert_col` (default A).
```
A      B      C      D
[BKK01]
       [PNG starts here]
```

**Mode `"center"`**: Image at centered column.
```
A      B      C      D      E      F
              [BKK01]
                     [PNG starts here]
```

Center column = `(A4_width_px - image_width_px) / 2 / 64` (column width ~64px).

A 500px image on 720px A4 → center at (720-500)/2/64 ≈ 1.7 → column B with 45px offset.

## Implementation

### src/inserter.py — add center column calculation

```python
def _inserter_center_col(image_width: int, a4_width: int = 720, col_width: int = 64) -> int:
    """Return 1-indexed column number to center image on A4 page."""
    center_px = (a4_width - image_width) / 2
    return max(1, round(center_px / col_width) + 1)
```

In both insert functions, add `insert_mode="left"` param. After reading `w, h`:
```python
if insert_mode == "center":
    center_col_idx = _inserter_center_col(w)
    col = chr(ord('A') + center_col_idx - 1)
```

### config.json
```json
"insert_mode": "left"
```

---

## TODOs

- [x] 1. Add `_inserter_center_col` function
- [x] 2. Add `insert_mode` param to both insert functions
- [x] 3. Add config + wire through insert.py
- [x] 4. Test
