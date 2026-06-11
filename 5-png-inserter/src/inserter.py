"""PNG inserter — sheet manipulation utilities."""

import re
import struct
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XlImage
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.pagebreak import Break


def purge_sheet(xlsx_path: Path, sheet_name: str, from_row: int):
    """Delete all rows from *from_row* to end in the given sheet."""
    wb = load_workbook(str(xlsx_path))
    if sheet_name not in wb.sheetnames:
        wb.close()
        return
    ws = wb[sheet_name]
    if ws.max_row >= from_row:
        ws.delete_rows(from_row, ws.max_row - from_row + 1)
    wb.save(str(xlsx_path))
    wb.close()


def extract_label(filename: str) -> str:
    """Extract label from PNG filename.
    'PW planwork100_exist BKK01_Bayface Before.png' → 'Bayface Before'"""
    stem = Path(filename).stem
    stem = re.sub(r'_\d+$', '', stem)  # strip _1, _2 dedup suffix
    parts = stem.rsplit("_", 1)
    return parts[-1] if len(parts) > 1 else stem


def extract_site(filename: str) -> str:
    """Extract site name from PNG filename.
    'PW planwork100_exist BKK01_Bayface Before.png' → 'BKK01'"""
    stem = Path(filename).stem
    parts = stem.split("_", 2)  # ["PW planwork100", "exist BKK01", "Bayface Before"]
    if len(parts) >= 2:
        prefix_site = parts[1]  # "exist BKK01" or "new BKK09"
        site_parts = prefix_site.split(" ", 1)
        if len(site_parts) >= 2:
            return site_parts[1]  # "BKK01"
    return stem


def clean_sheet_name(name: str) -> str:
    """Clean sheet name for comparison.
    '2.1. Bayface_Before' → 'bayface before'"""
    name = re.sub(r'^\d+\.?\d*\.?\s*', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    name = name.replace("_", " ")
    return " ".join(name.split()).lower()


def find_matching_sheet(wb, label: str) -> str | None:
    """Find sheet whose cleaned name matches the label."""
    clean_label = clean_sheet_name(label)
    for sheet_name in wb.sheetnames:
        if clean_sheet_name(sheet_name) == clean_label:
            return sheet_name
    return None


def _setup_a4_print(ws, print_title_rows=None):
    """Configure sheet for A4 portrait printing with auto-height flow."""
    ws.page_setup.paperSize = 9
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0  # height auto-flows
    from openpyxl.worksheet.properties import PageSetupProperties
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5
    if print_title_rows:
        ws.print_title_rows = print_title_rows


def insert_png(xlsx_path: Path, sheet_name: str, png_path: Path,
               label: str, start_row: int, merge_to_col: str | None = None,
               gap_rows: int = 1, col: str = "A",
               display_width: int | None = None,
               page_rows: int | None = None, header_count: int = 0) -> int:
    """Insert label + PNG. Returns next available row."""
    wb = load_workbook(str(xlsx_path))
    ws = wb[sheet_name]

    # Read PNG dimensions
    with open(png_path, 'rb') as f:
        f.read(16)
        w, h = struct.unpack('>II', f.read(8))

    # Page boundary check — push to next page if image would overflow
    if page_rows:
        usable = page_rows - header_count if header_count else page_rows
        est_rows = max(1, int(h * 0.75 / 15) + 1)
        page_end = ((start_row - 1) // usable + 1) * usable
        if start_row + 1 + gap_rows + est_rows > page_end:
            start_row = page_end + 1

    # Label row
    label_cell = ws.cell(row=start_row, column=1)
    label_cell.value = label
    label_cell.font = Font(bold=True, size=12)
    label_cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    label_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Page break before label (skip first site — it's at purge_from=10)
    if start_row > 10:
        ws.row_breaks.append(Break(id=start_row))

    # Merge label row cells (if configured)
    if merge_to_col:
        ws.merge_cells(f"A{start_row}:{merge_to_col}{start_row}")

    # Scale image to display_width (if configured)
    img = XlImage(str(png_path))
    if display_width:
        scale = display_width / w
        img.width = display_width
        img.height = int(h * scale)
        display_h = img.height
    else:
        display_h = h

    # Count rows this image needs (pixels → points → rows)
    default_ht = 15
    rows_needed = max(1, int(display_h * 0.75 / default_ht) + 1)

    # Insert image (offset by gap)
    img_row = start_row + 1 + gap_rows  # label + gap + image
    ws.add_image(img, f"{col}{img_row}")

    wb.save(str(xlsx_path))
    wb.close()
    return img_row + rows_needed + gap_rows  # image + gap for next


def insert_png_no_label(xlsx_path: Path, sheet_name: str, png_path: Path,
                         start_row: int, gap_rows: int = 1, col: str = "A",
                         display_width: int | None = None,
                         page_rows: int | None = None, header_count: int = 0) -> int:
    """Insert PNG without label row. Returns next available row."""
    wb = load_workbook(str(xlsx_path))
    ws = wb[sheet_name]
    with open(png_path, 'rb') as f:
        f.read(16)
        w, h = struct.unpack('>II', f.read(8))

    # Page boundary check — push to next page if image would overflow
    if page_rows:
        usable = page_rows - header_count if header_count else page_rows
        est_rows = max(1, int(h * 0.75 / 15) + 1)
        page_end = ((start_row - 1) // usable + 1) * usable
        if start_row + 1 + gap_rows + est_rows > page_end:
            start_row = page_end + 1

    # Scale image to display_width (if configured)
    img = XlImage(str(png_path))
    if display_width:
        scale = display_width / w
        img.width = display_width
        img.height = int(h * scale)
        display_h = img.height
    else:
        display_h = h

    rows_needed = max(1, int(display_h * 0.75 / 15) + 1)

    img_row = start_row + gap_rows
    ws.add_image(img, f"{col}{img_row}")
    wb.save(str(xlsx_path))
    wb.close()
    return img_row + rows_needed + gap_rows
