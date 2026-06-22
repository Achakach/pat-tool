"""print_setup module — A4 page setup and header parsing for column copier.

Functions copied from 5-png-inserter with 3 handover bugs fixed:
  #8 — _parse_print_title_rows returns header count (end-start+1), not end
  #9 — _parse_print_title_rows guards when headers fill entire page (content_rows < 1)
  #10 — _setup_a4_print: remove global flag, fix debug string, always print
"""

import math
import sys


# ── A4 print setup ────────────────────────────────────────────────────────

def _setup_a4_print(ws, print_title_rows=None):
    """Configure worksheet for A4 portrait printing.

    Args:
        ws: Worksheet to configure.
        print_title_rows: Optional str like '1:6' to set as print title rows
                          (repeat at top of every page).
    """
    ws.page_setup.paperSize = 9
    ws.page_setup.orientation = 'portrait'
    try:
        ws.page_setup.autoPageBreaks = True
    except AttributeError:
        print("[WARNING] Could not set autoPageBreaks: worksheet XML missing pageSetUpPr element", file=sys.stderr)
    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5
    if print_title_rows is not None:
        ws.print_title_rows = print_title_rows
    # FIX #10: removed global _a4_print_setup_done guard; print every call
    # FIX #10: debug string now says autoPageBreaks=True (was False)
    print(f"[DEBUG] _setup_a4_print: setting A4 portrait, margins L=0.25 R=0.25 T=0.5 B=0.5, autoPageBreaks=True, print_title_rows={print_title_rows}", file=sys.stderr)


# ── Page row calculation ───────────────────────────────────────────────────

def _calc_page_rows(ws, config_override=None):
    """Calculate max rows fitting on one A4 page based on margins.

    Paper height = 841.89 points (A4).
    Row height = 15 points (default Excel row height).
    Returns integer row count. Pass config_override to bypass auto-calc.
    """
    if config_override is not None:
        print(f"[DEBUG] _calc_page_rows: config_override={config_override}, returning early", file=sys.stderr)
        return config_override
    paper_height_pts = 841.89
    margins_pts = (float(ws.page_margins.top) + float(ws.page_margins.bottom)) * 72
    printable_pts = paper_height_pts - margins_pts
    rows = math.ceil(printable_pts / 15)
    print(f"[DEBUG] _calc_page_rows: margins top={ws.page_margins.top} bottom={ws.page_margins.bottom}, paper=841.89, margins_pts={margins_pts}, printable_pts={printable_pts}, rows={printable_pts}/15={rows} (ceil)", file=sys.stderr)
    return rows


# ── Print title rows parsing ───────────────────────────────────────────────

def _parse_print_title_rows(value, page_rows=None):
    """Parse print_title_rows config value.

    Returns (header_count, print_title_rows_str):
        header_count: int (0 if disabled, else end-start+1 rows)
        print_title_rows_str: str or None (None if disabled)
    """
    if value is None:
        return (0, None)

    if not isinstance(value, str) or ':' not in value:
        print(f"WARNING: Invalid print_title_rows '{value}' — must be 'start:end' format. Disabled.", file=sys.stderr)
        return (0, None)

    parts = value.split(':')
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        print(f"WARNING: Invalid print_title_rows '{value}' — non-numeric parts. Disabled.", file=sys.stderr)
        return (0, None)

    start, end = int(parts[0]), int(parts[1])

    if page_rows is not None:
        content_rows = page_rows - end
        # FIX #9: guard when headers consume entire page leaving 0 content rows
        if content_rows < 1:
            print(f"WARNING: print_title_rows '{value}' leaves 0 content rows (page_rows={page_rows}). Disabled.", file=sys.stderr)
            return (0, None)
        if content_rows < 2:
            w = max(0, content_rows)
            print(f"WARNING: print_title_rows '{value}' leaves only {w} content row(s) per page (page_rows={page_rows}).", file=sys.stderr)

    # FIX #8: header_count = end - start + 1 (was incorrectly just `end`)
    return (end - start + 1, value)


# ── Gap snapping ───────────────────────────────────────────────────────────

def snap_gap_rows(paste_end_row, tws, page_rows, header_count=0):
    """Return number of gap rows needed to push content below paste_end_row
    to the next clean page start. Returns 0 if no snap needed."""
    if page_rows is None:
        return 0

    content_rows = page_rows - header_count if header_count else page_rows

    # Find next non-empty row below paste area
    next_row = None
    for row in range(paste_end_row + 1, tws.max_row + 200):
        for c in range(1, tws.max_column + 1):
            if tws.cell(row=row, column=c).value is not None:
                next_row = row
                break
        if next_row is not None:
            break

    if next_row is None:
        return 0  # no content below

    # Check if already at a clean page start
    # Clean starts: row 1, row page_rows+1, row page_rows+content_rows+1, ...
    if next_row == 1:
        return 0

    k = (next_row - page_rows - 1) // content_rows
    clean_start = page_rows + k * content_rows + 1

    if next_row == clean_start:
        return 0  # already clean

    # Return gap to next clean start
    next_clean = page_rows + (k + 1) * content_rows + 1
    return next_clean - next_row
