# Wider Label Search — Same Column → Whole Row → Anchor Cell → Upward

## TL;DR

> **Quick Summary**: Expand `get_label()` to search wider when the cell directly above is empty. New search order: (1) same column above, (2) any cell in the row above, (3) the anchor cell itself, (4) scan upward in same column.
>
> **Estimated Effort**: Quick (1 file, ~20 lines changed)

---

## What Changes

### naming.py — `get_label()`

**Current behavior**: Scans upward in the same column only.

**New behavior** — search order for each anchor position:

```
For each candidate row (starting from row above anchor, going up):
  1. Check same column → if text found, return it
  2. Check ALL columns in that row (left to right) → return first text found
  3. If row == anchor_row: also check the anchor cell itself
  4. If nothing in this row, move up one row and repeat
  5. If all rows exhausted → return None (fallback)
```

Example with image at C5 (anchor_row=4, anchor_col=2):

```
Row 4: A4=""  B4=""  C4="Chart"  D4=""  → step 2 finds "Chart" at C4 (different column, same row above)
Row 3: A3=""  B3=""  C3=""  D3=""  → nothing, continue up
Row 2: A2="Title" B2="" ... → step 2 finds "Title" at A2 (row further above)
→ returns "Chart" (first match at row 4)
```

If the anchor cell itself has text:
```
Row 5: C5="Embedded label"  → step 3 (check anchor cell) finds it
```

---

## Implementation

Replace the current get_label loop:

```python
# Current:
for row in range(anchor_row, 0, -1):
    value = ws.cell(row=row, column=anchor_col + 1).value
    if value and str(value).strip():
        return str(value).strip()
```

With the new wider search:

```python
from openpyxl.utils import get_column_letter

def get_label(ws, anchor_row: int, anchor_col: int) -> str | None:
    if anchor_row == 0:
        return None
    
    max_col = ws.max_column or 26  # fallback if sheet empty
    
    for row in range(anchor_row, 0, -1):
        # Step 1: same column
        value = ws.cell(row=row, column=anchor_col + 1).value
        if value and str(value).strip():
            return str(value).strip()
        
        # Step 2: any cell in this row (left to right)
        for col in range(1, max_col + 1):
            if col == anchor_col + 1:
                continue  # already checked
            value = ws.cell(row=row, column=col).value
            if value and str(value).strip():
                return str(value).strip()
        
        # Step 3: if this is the anchor row, check the anchor cell
        if row == anchor_row + 0:  # anchor_row is 0-indexed, openpyxl row = anchor_row (since we loop from anchor_row down)
            # Actually the anchor cell check should happen once, not in the loop
            pass
    
    return None
```

Wait — the anchor cell check doesn't fit naturally in the upward loop. Better structure:

```python
def get_label(ws, anchor_row: int, anchor_col: int) -> str | None:
    max_col = ws.max_column or 26
    
    # Search rows above anchor (anchor_row down to 1)
    for row in range(anchor_row, 0, -1):
        # Step 1: same column
        value = ws.cell(row=row, column=anchor_col + 1).value
        if value and str(value).strip():
            return str(value).strip()
        
        # Step 2: scan entire row left-to-right
        for col in range(1, max_col + 1):
            if col == anchor_col + 1:
                continue
            value = ws.cell(row=row, column=col).value
            if value and str(value).strip():
                return str(value).strip()
    
    # Step 3: check the anchor cell itself (after all rows above exhausted)
    value = ws.cell(row=anchor_row + 1, column=anchor_col + 1).value
    if value and str(value).strip():
        return str(value).strip()
    
    return None
```

Wait — when anchor_row == 0, we can't check the cell at row=1 because that's the anchor cell. Let me reconsider. The anchor cell at row=anchor_row+1 (openpyxl 1-indexed). If anchor_row=0, the anchor cell IS row 1 (no row above). So for anchor_row==0, we should check the anchor cell itself, and also scan other columns in row 1.

Actually, let me simplify. The user's order is: Cell above → any cell in row above → anchor cell → scan upward.

So for each step upward:
1. Check same column cell at that row
2. Check all other columns in that row
3. When we've checked all rows above, check anchor cell

For row-0 edge case: no rows above. Just check the anchor cell (step 3 only).

Let me finalize:

```python
def get_label(ws, anchor_row: int, anchor_col: int) -> str | None:
    max_col = ws.max_column or 26
    
    if anchor_row > 0:
        # Search rows above anchor
        for row in range(anchor_row, 0, -1):
            # Step 1: same column
            value = ws.cell(row=row, column=anchor_col + 1).value
            if value and str(value).strip():
                return str(value).strip()
            
            # Step 2: scan entire row (skip already-checked column)
            for col in range(1, max_col + 1):
                if col == anchor_col + 1:
                    continue
                value = ws.cell(row=row, column=col).value
                if value and str(value).strip():
                    return str(value).strip()
    
    # Step 3: check the anchor cell itself
    anchor_value = ws.cell(row=anchor_row + 1, column=anchor_col + 1).value
    if anchor_value and str(anchor_value).strip():
        return str(anchor_value).strip()
    
    return None
```

This is clean. For anchor_row > 0, scans upward row by row (same col first, then full row scan), then falls through to check anchor cell. For anchor_row == 0, skips the loop and checks only the anchor cell.

---

## TODOs

- [x] 1. Update naming.py `get_label()` — new search order: same col → full row → anchor cell → upward
- [x] 2. Update tests — add `test_get_label_adjacent_column` (label in different column, same row above)
- [x] 3. Update tests — add `test_get_label_anchor_cell` (label in anchor cell itself)
- [x] 4. Run pytest — all tests pass

---

## Verification

```bash
pytest test_extract_pngs.py -v
# Expected: all pass (29 + 2 new = 31)
```
