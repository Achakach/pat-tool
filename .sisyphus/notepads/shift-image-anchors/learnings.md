# Learnings — shift-image-anchors
## 2026-06-19T08:18 Session Start
- Plan: shift-image-anchors — 4 implementation tasks, TDD workflow
- Key: AnchorMarker.row is 0-BASED (row 0 = Excel row 1)
- Two insert_rows calls: line 216 (primary) + line 260 (snap)
- OneCellAnchor: only _from, no to attribute
- TwoCellAnchor: both _from and to
- AbsoluteAnchor: skip with stderr warning
- Guard: hasattr(ws, '_images'), num_rows <= 0, insert_at_row < 1

## 2026-06-19 Task 1 (RED phase) Complete
- Created `3-column-copier/tests/test_images.py` — 10 TDD test methods in `TestShiftImageAnchors`
- ALL tests fail (ModuleNotFoundError) — expected since `src/images.py` doesn't exist yet
- Import fix: XDRPoint2D/XDRPositiveSize2D from `openpyxl.drawing.xdr` not `openpyxl.drawing.geometry`
- AbsoluteAnchor: `pos` is `XDRPoint2D`, `ext` is `XDRPositiveSize2D` (both from `openpyxl.drawing.xdr`)
- TwoCellAnchor creation: `AnchorMarker(col=N, row=N)`, assign to `TwoCellAnchor(_from=marker)`
- Test structure follows `test_columns.py:TestAppendInsertRows` pattern — class-based, inline Workbook
- Evidence saved: `.sisyphus/evidence/task-1-red-phase.txt`
