# Learnings - MergedCell Guard

## Task 1: Guard paste against MergedCell

### Changes made to `3-column-copier/copier.py`
1. Added import: `from openpyxl.cell.cell import MergedCell` (line 10, after existing openpyxl import)
2. Guarded write at line 220-222: skip `cell.value = val` when target cell is a `MergedCell`

### Root cause
`AttributeError: 'MergedCell' object attribute 'value' is read-only` — writing to a merged cell's sub-cells is forbidden by openpyxl. The paste loop read from source correctly but crashed on unconditional write to target.

### Solution pattern
```python
cell = tws.cell(row=dst_row, column=dst_idx)
if not isinstance(cell, MergedCell):
    cell.value = val
```

### Key insight
- Only target sheet cells need guarding (source reads are fine)
- `isinstance` check is lighter than try/except and expresses intent clearly
- Existing `insert_rows` merged cell detection (lines 180-190) is a separate concern — it guards row insertion, not paste writes

### All 37 tests pass after change

## Task 2: Test merged cell paste behavior

### Changes made to `3-column-copier/tests/test_columns.py`
1. Added `test_paste_skips_merged_cells` method in `TestPasteDirect` class (after `test_paste_direct_source_to_target`)

### Test structure
- Source has data in column B (B1="source B1 val", B2="source B2 val")
- Target has merge A1:B1 with A1="merged header", B2="target B2"
- Guarded paste writes from source col B to target col B
- Asserts: B1 is MergedCell, write to B1 skipped (A1 value preserved), B1.value is None (sub-cell has no own value), B2 gets source value

### Learning: anchor cell vs sub-cell
- `merge_cells("A1:B1")` makes A1 the anchor (regular Cell) and B1 a MergedCell
- The `isinstance(cell, MergedCell)` guard correctly catches sub-cells but NOT the anchor
- Anchor cell writes are allowed and intentional — only sub-cell writes need skipping
- Test must use a column that's NOT the merge anchor to meaningfully test the guard

### All 38 tests pass after Task 2
