"""Tests for page break logic in png-inserter — Tasks 4, 5, 6."""
import struct
import zlib
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.pagebreak import Break

from src.inserter import (
    _calc_page_rows,
    _clear_page_breaks,
    _setup_a4_print,
    insert_png,
    insert_png_no_label,
)


def _make_test_png(path, width=10, height=10):
    """Create a minimal valid PNG for testing."""
    def _chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''
    for _ in range(height):
        raw += b'\x00'  # filter byte
        for _ in range(width):
            raw += b'\xff\x00\x00'  # RGB red pixels
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(_chunk(b'IHDR', ihdr))
        f.write(_chunk(b'IDAT', zlib.compress(raw)))
        f.write(_chunk(b'IEND', b''))


def _make_test_xlsx(tmp_path, name="test.xlsx"):
    """Create an xlsx with Sheet as active sheet and some data rows."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet"
    for i in range(1, 20):
        ws.cell(row=i, column=1).value = f"row{i}"
    path = tmp_path / name
    wb.save(str(path))
    wb.close()
    return path


# ============================================================
# Task 4 — Config / Setup Tests (7 tests)
# ============================================================

class TestPageBreakConfig:
    """Tests for page break feature toggle and A4 setup helpers."""

    def test_page_break_before_label_true_enables_feature(self, tmp_path):
        """_calc_page_rows returns non-None int when feature conceptually enabled."""
        wb = Workbook()
        ws = wb.active
        _setup_a4_print(ws)
        result = _calc_page_rows(ws)
        # Feature enabled: page_rows is an integer (not None)
        assert result is not None
        assert isinstance(result, int)
        assert result > 0
        wb.close()

    def test_page_break_before_label_false_disables_feature(self, tmp_path):
        """page_rows=None passed to insert_png → no breaks inserted."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)

        insert_png(output, "Sheet", png, "Site1", 5, page_rows=None, purge_from=1, gap_rows=1)

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        assert len(ws.row_breaks.brk) == 0
        wb.close()

    def test_page_break_before_label_missing_defaults_false(self, tmp_path):
        """page_rows not passed (default None) → no breaks (backward compat)."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)

        insert_png(output, "Sheet", png, "Site1", 5, purge_from=1, gap_rows=1)

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        assert len(ws.row_breaks.brk) == 0
        wb.close()

    def test_a4_page_rows_override(self, tmp_path):
        """Config a4_page_rows=40 → _calc_page_rows returns 40."""
        wb = Workbook()
        ws = wb.active
        result = _calc_page_rows(ws, config_override=40)
        assert result == 40
        wb.close()

    def test_a4_page_rows_absent_autocalc(self, tmp_path):
        """No a4_page_rows → _calc_page_rows returns ~51 (auto-calc)."""
        wb = Workbook()
        ws = wb.active
        _setup_a4_print(ws)
        result = _calc_page_rows(ws)
        # A4 auto-calc with 0.5" top+bottom margins → (841.89 - 72) / 15 ≈ 51
        assert 49 <= result <= 53
        wb.close()

    def test_auto_page_breaks_disabled(self, tmp_path):
        """_setup_a4_print → autoPageBreaks is False."""
        wb = Workbook()
        ws = wb.active
        _setup_a4_print(ws)
        assert ws.page_setup.autoPageBreaks is False
        wb.close()

    def test_clear_page_breaks_empties_brk(self, tmp_path):
        """_clear_page_breaks clears all existing manual breaks."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        ws.row_breaks.append(Break(id=10))
        ws.row_breaks.append(Break(id=25))
        assert len(ws.row_breaks.brk) == 2

        _clear_page_breaks(ws)
        assert len(ws.row_breaks.brk) == 0
        wb.close()


# ============================================================
# Task 5 — Break Insertion Logic Tests (6 tests)
# ============================================================

class TestPageBreakInsertion:
    """Tests for page break insertion during insert_png and insert_png_no_label."""

    def test_break_before_second_site(self, tmp_path):
        """Two sites on same sheet → break inserted before second site's label row."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)  # rows_needed = 1

        # First site at purge_from (5): no break
        r1 = insert_png(output, "Sheet", png, "Site1", 5, page_rows=10, purge_from=5, gap_rows=1)
        # start_row=5, start_row > purge_from? No → no break, no snap
        # label=5, img=7, rows_needed=1 → returns 7+1+1 = 9

        # Second site at row 9: should snap to page boundary and get break
        r2 = insert_png(output, "Sheet", png, "Site2", r1, page_rows=10, purge_from=5, gap_rows=1)
        # start_row=9 > 5 → snap: ((9-2)//10+1)*10+1 = (0+1)*10+1 = 11
        # Break(id=11), label at 11, img at 13, returns 15

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        breaks = ws.row_breaks.brk
        assert len(breaks) == 1
        assert breaks[0].id == 11  # break before row 11 (page boundary)
        assert ws.cell(row=11, column=1).value == "Site2"
        wb.close()

    def test_no_break_before_first_site(self, tmp_path):
        """First site at purge_from row → no page break inserted."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)

        insert_png(output, "Sheet", png, "Site1", 5, page_rows=10, purge_from=5, gap_rows=1)
        # start_row=5, purge_from=5 → start_row > purge_from? No → skip break

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        assert len(ws.row_breaks.brk) == 0
        assert ws.cell(row=5, column=1).value == "Site1"
        wb.close()

    def test_overflow_guard_pushes_image(self, tmp_path):
        """Image near page boundary → insert_png_no_label pushes to next page."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "tall.png"
        _make_test_png(png, 10, 100)  # rows_needed = max(1, int(75/15)+1) = 6

        # start_row=4, page_rows=5, gap_rows=1
        # img_end = 4+1+6 = 11, page_end = ((4-1)//5+1)*5 = 5
        # 11 > 5 → pushed to page_end+1 = 6
        next_row = insert_png_no_label(output, "Sheet", png, start_row=4, gap_rows=1, page_rows=5)
        # img_row = 6+1 = 7, return = 7+6+1 = 14
        assert next_row > 5  # image pushed past page boundary
        assert next_row >= 12

    def test_image_fits_no_push(self, tmp_path):
        """Image fits within page boundary → stays at original start_row."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "small.png"
        _make_test_png(png, 10, 10)  # rows_needed = 1

        # start_row=4, page_rows=10, gap_rows=1
        # img_end = 4+1+1 = 6, page_end = ((4-1)//10+1)*10 = 10
        # 6 <= 10 → no push, stays at row 4
        next_row = insert_png_no_label(output, "Sheet", png, start_row=4, gap_rows=1, page_rows=10)
        # img_row = 4+1 = 5, return = 5+1+1 = 7
        assert next_row == 7  # no push, image at row 5

    def test_multiple_small_images_fill_page(self, tmp_path):
        """Third of three images overflows page → pushed to next page."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "med.png"
        _make_test_png(png, 10, 60)  # rows_needed = max(1, int(45/15)+1) = 4

        # page_rows=15, gap_rows=1
        r1 = insert_png_no_label(output, "Sheet", png, start_row=1, gap_rows=1, page_rows=15)
        # img_end = 1+1+4=6, page_end=15 → stays. img_row=2, return=2+4+1=7
        r2 = insert_png_no_label(output, "Sheet", png, start_row=r1, gap_rows=1, page_rows=15)
        # img_end = 7+1+4=12, page_end=15 → stays. img_row=8, return=8+4+1=13
        r3 = insert_png_no_label(output, "Sheet", png, start_row=r2, gap_rows=1, page_rows=15)
        # img_end = 13+1+4=18, page_end=15. 18>15 → pushed to 16
        # img_row=16+1=17, return=17+4+1=22
        assert r1 == 7
        assert r2 == 13
        assert r3 == 22  # pushed past page boundary at row 15

    def test_break_ids_correct_convention(self, tmp_path):
        """Break(id=X) means break BEFORE row X — (id-1) is multiple of page_rows."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)

        insert_png(output, "Sheet", png, "Site1", 5, page_rows=10, purge_from=1, gap_rows=1)
        insert_png(output, "Sheet", png, "Site2", 15, page_rows=10, purge_from=1, gap_rows=1)

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        breaks = ws.row_breaks.brk
        assert len(breaks) >= 1
        # Break BEFORE row N means N is first row of a page → (N-1) % page_rows == 0
        for brk in breaks:
            assert (brk.id - 1) % 10 == 0
        wb.close()


# ============================================================
# Task 6 — Edge Case Tests (4 tests)
# ============================================================

class TestPageBreakEdgeCases:
    """Edge case tests for page break behavior."""

    def test_single_image_taller_than_page(self, tmp_path):
        """Image taller than page_rows → still inserted without crash (warning in orchestrator)."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "huge.png"
        _make_test_png(png, 10, 500)  # rows_needed ≈ max(1, int(375/15)+1) = 26

        # page_rows=5, image spans ~26 rows → much taller than a page
        next_row = insert_png(output, "Sheet", png, "Site1", 3, page_rows=5, purge_from=1, gap_rows=1)
        # start_row=3 > 1 → snap: ((3-2)//5+1)*5+1 = 6, snap to row 6
        # label at 6, img at 8, rows_needed=26, return = 8+26+1 = 35
        assert next_row > 6  # image inserted past the page boundary

        wb = load_workbook(str(output))
        ws = wb["Sheet"]
        assert ws.cell(row=6, column=1).value == "Site1"  # label at snapped row
        wb.close()

    def test_multi_sheet_independence(self, tmp_path):
        """Page breaks on one sheet do not affect another — independent collections."""
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Sheet1"
        ws2 = wb.create_sheet("Sheet2")

        for i in range(1, 20):
            ws1.cell(row=i, column=1).value = f"s1_{i}"
            ws2.cell(row=i, column=1).value = f"s2_{i}"

        path = tmp_path / "test.xlsx"
        wb.save(str(path))
        wb.close()

        png = tmp_path / "test.png"
        _make_test_png(png, 10, 10)

        # Sheet1: insert with purge_from=1, start_row=10 → 10>1 triggers snap → Break at row 11
        insert_png(path, "Sheet1", png, "Site1", 10, page_rows=5, purge_from=1, gap_rows=1)

        # Sheet2: insert with purge_from=5, start_row=5 → 5>5 is False → no break (first site)
        insert_png(path, "Sheet2", png, "SiteA", 5, page_rows=5, purge_from=5, gap_rows=1)

        wb = load_workbook(str(path))
        breaks1 = wb["Sheet1"].row_breaks.brk
        breaks2 = wb["Sheet2"].row_breaks.brk

        assert len(breaks1) == 1  # Sheet1: break at row 11 (snapped from 10)
        assert breaks1[0].id == 11
        assert len(breaks2) == 0  # Sheet2: no break (first site at purge_from row)
        wb.close()

    def test_gap_rows_zero(self, tmp_path):
        """Gap_rows=0 does not break overflow math."""
        output = _make_test_xlsx(tmp_path, "test.xlsx")
        png = tmp_path / "med.png"
        _make_test_png(png, 10, 60)  # rows_needed = 4

        # page_rows=5, gap_rows=0, start_row=3
        # img_end = 3+0+4 = 7, page_end = ((3-1)//5+1)*5 = 5
        # 7 > 5 → pushed: start_row = 6
        # img_row = 6+0 = 6, return = 6+4+0 = 10
        next_row = insert_png_no_label(output, "Sheet", png, start_row=3, gap_rows=0, page_rows=5)
        assert next_row >= 9  # pushed past page boundary

        # Verify image was actually inserted (no crash)
        wb = load_workbook(str(output))
        images = wb["Sheet"]._images
        assert len(images) == 1
        wb.close()

    def test_existing_breaks_cleared_when_disabled(self, tmp_path):
        """_clear_page_breaks removes pre-existing manual page breaks."""
        wb = Workbook()
        ws = wb.active
        _setup_a4_print(ws)

        # Simulate pre-existing breaks from a previous run
        ws.row_breaks.append(Break(id=15))
        ws.row_breaks.append(Break(id=30))
        ws.row_breaks.append(Break(id=45))
        assert len(ws.row_breaks.brk) == 3

        _clear_page_breaks(ws)
        assert len(ws.row_breaks.brk) == 0
        wb.close()
