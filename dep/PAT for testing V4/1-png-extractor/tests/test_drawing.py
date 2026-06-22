"""Unit tests for XML/drawing parsing functions in extract_pngs.py.

Tests cover:
- _local_find / _local_findall: namespace-agnostic XML traversal
- _find_drawing_path: locating drawing XML in XLSX archives
- _parse_drawing_image_map: parsing anchor positions + image paths
"""

from __future__ import annotations

import io
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import openpyxl
from openpyxl.drawing.image import Image as XlImage

from extract_pngs import (
    _local_find,
    _local_findall,
    _find_drawing_path,
    _parse_drawing_image_map,
)

# ── Constants ──────────────────────────────────────────────────────────────

# Minimal valid 1×1 pixel PNG (valid PNG header + IHDR + IDAT + IEND chunks)
_PNG_DATA = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

# OpenXML namespace URIs
_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# ── Helpers ────────────────────────────────────────────────────────────────


def _create_xlsx_with_image(path: Path, anchor: str = "A1") -> None:
    """Write a minimal .xlsx with one embedded image to *path*."""
    wb = openpyxl.Workbook()
    ws = wb.active
    img = XlImage(io.BytesIO(_PNG_DATA))
    img.anchor = anchor
    ws.add_image(img)
    wb.save(str(path))
    wb.close()


def _copy_zip_with_modified_drawing(
    src: Path, dst: Path, old_tag: str, new_tag: str
) -> None:
    """Copy zip from *src* to *dst*, replacing *old_tag*→*new_tag* in drawing XML."""
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if "drawing" in item.filename and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    text = text.replace(old_tag, new_tag)
                    data = text.encode("utf-8")
                zout.writestr(item, data)


# ── Tests: _local_find / _local_findall ────────────────────────────────────


class TestLocalFind:
    """Namespace-agnostic XML child-element finders."""

    def test_local_find(self):
        """_local_find returns first matching descendant by local tag."""
        root = ET.fromstring("<root><a><b>target</b></a></root>")
        result = _local_find(root, "b")
        assert result is not None
        assert result.text == "target"

    def test_local_findall(self):
        """_local_findall returns all matching descendants."""
        root = ET.fromstring(
            "<root><a><x>1</x><x>2</x></a><x>3</x></root>"
        )
        result = _local_findall(root, "x")
        assert len(result) == 3
        assert [e.text for e in result] == ["1", "2", "3"]


# ── Tests: _find_drawing_path ──────────────────────────────────────────────


class TestFindDrawingPath:
    """Locate the drawing XML within an XLSX archive."""

    def test_has_drawing(self, tmp_path: Path):
        """Sheet with embedded image → drawing path is found."""
        xlsx = tmp_path / "has_drawing.xlsx"
        _create_xlsx_with_image(xlsx, anchor="A1")

        with zipfile.ZipFile(xlsx, "r") as zf:
            path = _find_drawing_path(zf, 1)

        assert path is not None, "Expected a drawing path for sheet with image"
        assert "drawing" in path.lower()
        assert path.endswith(".xml")

    def test_no_drawing(self, tmp_path: Path):
        """Sheet without any images → _find_drawing_path returns None."""
        xlsx = tmp_path / "no_drawing.xlsx"
        wb = openpyxl.Workbook()
        wb.save(str(xlsx))
        wb.close()

        with zipfile.ZipFile(xlsx, "r") as zf:
            path = _find_drawing_path(zf, 1)

        assert path is None


# ── Tests: _parse_drawing_image_map ────────────────────────────────────────


class TestParseDrawingImageMap:
    """Parse drawing XML to map anchor positions → image paths."""

    def test_two_cell_anchor(self, tmp_path: Path):
        """Image anchored via twoCellAnchor → correct (row, col) key returned."""
        # 1. Create normal XLSX via openpyxl (produces oneCellAnchor)
        src = tmp_path / "original.xlsx"
        _create_xlsx_with_image(src, anchor="B3")  # row=2, col=1 (0-indexed)

        # 2. Copy zip, changing oneCellAnchor → twoCellAnchor in drawing XML
        dst = tmp_path / "two_cell.xlsx"
        _copy_zip_with_modified_drawing(
            src, dst,
            old_tag="oneCellAnchor",
            new_tag="twoCellAnchor",
        )

        # 3. Parse
        with zipfile.ZipFile(dst, "r") as zf:
            drawing_path = _find_drawing_path(zf, 1)
            assert drawing_path is not None
            result = _parse_drawing_image_map(zf, drawing_path)

        assert isinstance(result, dict)
        assert len(result) == 1
        (row, col), img_path = next(iter(result.items()))
        assert row == 2, f"Expected row=2, got {row}"
        assert col == 1, f"Expected col=1, got {col}"
        assert "image" in img_path.lower() or "png" in img_path.lower()

    def test_one_cell_anchor(self, tmp_path: Path):
        """Image anchored via oneCellAnchor (ws.add_image) → correct dict."""
        xlsx = tmp_path / "one_cell.xlsx"
        _create_xlsx_with_image(xlsx, anchor="C4")  # row=3, col=2 (0-indexed)

        with zipfile.ZipFile(xlsx, "r") as zf:
            drawing_path = _find_drawing_path(zf, 1)
            assert drawing_path is not None
            result = _parse_drawing_image_map(zf, drawing_path)

        assert isinstance(result, dict)
        assert len(result) == 1
        (row, col), img_path = next(iter(result.items()))
        assert row == 3, f"Expected row=3, got {row}"
        assert col == 2, f"Expected col=2, got {col}"
        assert "image" in img_path.lower() or "png" in img_path.lower()

    def test_no_drawing(self, tmp_path: Path):
        """Empty drawing XML (no anchors) → returns empty dict."""
        xlsx = tmp_path / "empty_drawing.xlsx"
        with zipfile.ZipFile(xlsx, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "xl/drawings/drawing1.xml",
                '<xdr:wsDr xmlns:xdr="{}"/>'.format(_XDR),
            )
            zf.writestr(
                "xl/drawings/_rels/drawing1.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="{}"/>'.format(_PKG_REL),
            )

        with zipfile.ZipFile(xlsx, "r") as zf:
            result = _parse_drawing_image_map(zf, "xl/drawings/drawing1.xml")

        assert result == {}
