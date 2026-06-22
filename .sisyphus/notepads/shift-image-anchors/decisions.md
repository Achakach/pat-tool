# Decisions — shift-image-anchors
## Architecture
- Extract to src/images.py (follows src/columns.py pattern)
- Function: shift_image_anchors(ws, insert_at_row, num_rows) → None
- 0-based conversion inside function: insert_row_0 = insert_at_row - 1
- Both call sites follow same pattern: shift_image_anchors(tws, row, n)

## TDD
- RED phase: write 10 failing tests first
- GREEN phase: implement shift_image_anchors()
- INTEGRATE: add 2 call sites in copier.py

## Scope
- IN: tool 3 only, OneCellAnchor + TwoCellAnchor, both insert_rows calls
- OUT: AbsoluteAnchor (warn), column shifting, other tools, delete_rows
