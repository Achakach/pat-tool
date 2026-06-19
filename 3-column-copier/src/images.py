"""Image anchor utilities for shifting after insert_rows.

openpyxl's Worksheet.insert_rows() shifts cell content and merged ranges
but does NOT adjust image anchors. This module provides shift_image_anchors()
to manually shift AnchorMarker.row for images on the target worksheet.

AnchorMarker.row is 0-BASED: row 0 = Excel row 1.
The insert_at_row parameter is 1-based (matching Excel row numbers).
"""

import sys
from openpyxl.drawing.spreadsheet_drawing import (
    OneCellAnchor, TwoCellAnchor, AbsoluteAnchor,
)


def shift_image_anchors(ws, insert_at_row, num_rows):
    """Shift image anchors down after insert_rows().

    Args:
        ws: openpyxl Worksheet object (the target worksheet).
        insert_at_row: 1-based row number where rows were inserted.
        num_rows: Number of rows inserted.

    Handles:
        - OneCellAnchor: shifts _from.row if >= insertion point
        - TwoCellAnchor: shifts _from.row and to.row based on position
          (spanning images: only to.row shifts if _from is above insert)
        - AbsoluteAnchor: skipped with stderr warning
        - Unknown types: skipped with stderr warning

    No return value. Modifies ws._images in place.
    """
    # Guard: no-op if nothing to shift
    if num_rows <= 0:
        return

    # Guard: no images on sheet
    if not hasattr(ws, '_images'):
        return

    insert_row_0 = insert_at_row - 1  # convert to 0-based for comparison

    for img in ws._images:
        anchor = img.anchor

        if isinstance(anchor, OneCellAnchor):
            if anchor._from.row >= insert_row_0:
                anchor._from.row += num_rows

        elif isinstance(anchor, TwoCellAnchor):
            # Shift _from if entirely below insertion
            if anchor._from.row >= insert_row_0:
                anchor._from.row += num_rows
            # Shift to if it extends below insertion (spanning case)
            if anchor.to.row >= insert_row_0:
                anchor.to.row += num_rows

        elif isinstance(anchor, AbsoluteAnchor):
            print(
                f"[WARNING] Skipping AbsoluteAnchor at pos x={anchor.pos.x}, "
                f"y={anchor.pos.y} — manual repositioning required",
                file=sys.stderr,
            )
        else:
            print(
                f"[WARNING] Unknown anchor type: {type(anchor).__name__} — skipping",
                file=sys.stderr,
            )
