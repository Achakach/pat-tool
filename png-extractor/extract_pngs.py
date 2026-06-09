#!/usr/bin/env python3
"""CLI entry point for PAT tool — extract PNGs from XLSX with smart naming.

Usage::

    python extract_pngs.py --config config.json

Orchestrates image extraction by:
1. Reading config for input/output folders.
2. Iterating over each ``.xlsx`` in the input folder.
3. Parsing the internal drawing XML to map images to their sheet + cell.
4. Using ``naming.py`` to build descriptive output filenames.
5. Saving extracted PNGs to the output folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

import openpyxl

from src.config import load_config
from src.naming import get_label, build_filename

# ── OpenXML namespaces ──────────────────────────────────────────────────
# These are well-known, stable URIs within the OOXML spec.

_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


# ── XML helpers (namespace-agnostic) ────────────────────────────────────


def _local_find(el, local_tag):
    """Return the first descendant of *el* whose local (namespace-free) tag
    equals *local_tag*, or ``None``."""
    for child in el.iter():
        tag = child.tag.split("}")[1] if "}" in child.tag else child.tag
        if tag == local_tag:
            return child
    return None


def _local_findall(el, local_tag):
    """Return a list of all descendants whose local tag equals *local_tag*."""
    return [
        child
        for child in el.iter()
        if (child.tag.split("}")[1] if "}" in child.tag else child.tag) == local_tag
    ]


# ── Drawing-XML parsers ─────────────────────────────────────────────────


def _find_drawing_path(zf, sheet_idx):
    """Return the zip-internal path of the drawing XML for the 1‑based
    *sheet_idx*, or ``None`` if the sheet has no drawing relationship."""
    rels_path = f"xl/worksheets/_rels/sheet{sheet_idx}.xml.rels"
    if rels_path not in zf.namelist():
        return None

    with zf.open(rels_path) as f:
        rels = ET.parse(f)

    for rel in rels.findall(f"{{{_PKG_REL}}}Relationship"):
        if "drawing" in rel.get("Type", ""):
            raw_target = rel.get("Target", "")
            # Absolute paths (starts with /) are already rooted in the zip.
            # Relative paths are relative to xl/worksheets/.
            if raw_target.startswith("/"):
                resolved = raw_target.lstrip("/")
            else:
                resolved = os.path.normpath(
                    os.path.join("xl/worksheets", raw_target)
                ).replace("\\", "/")
            return resolved
    return None


def _parse_drawing_image_map(zf, drawing_path):
    """Parse *drawing_path* and its companion ``.rels`` file to build a
    mapping of ``(anchor_row, anchor_col) → zip_image_path``.

    Parameters
    ----------
    zf : zipfile.ZipFile
        Opened XLSX archive.
    drawing_path : str
        Zip-internal path (e.g. ``xl/drawings/drawing1.xml``).

    Returns
    -------
    dict[tuple[int, int], str]
        Keys are 0‑indexed (row, col) anchor positions; values are full
        zip-internal paths to PNG files (e.g. ``xl/media/image1.png``).
    """
    dr = Path(drawing_path)
    rels_path = str(dr.parent / "_rels" / (dr.stem + ".xml.rels")).replace(
        "\\", "/"
    )

    # ── rId → zip image path ─────────────────────────────────────────
    rId_to_image: dict[str, str] = {}
    if rels_path in zf.namelist():
        with zf.open(rels_path) as f:
            dr_rels = ET.parse(f)
        for rel in dr_rels.findall(f"{{{_PKG_REL}}}Relationship"):
                if "image" in rel.get("Type", ""):
                    raw_target = rel.get("Target", "")
                    # Absolute path → already rooted in zip; relative → join
                    if raw_target.startswith("/"):
                        resolved = raw_target.lstrip("/")
                    else:
                        resolved = os.path.normpath(
                            os.path.join("xl/drawings", raw_target)
                        ).replace("\\", "/")
                    rId_to_image[rel.get("Id")] = resolved

    # ── Parse anchor elements for positions ──────────────────────────
    with zf.open(drawing_path) as f:
        dr_xml = ET.parse(f)

    anchors: dict[tuple[int, int], str] = {}
    for anchor in _local_findall(dr_xml.getroot(), "twoCellAnchor"):
        blip = _local_find(anchor, "blip")
        from_el = _local_find(anchor, "from")
        if blip is None or from_el is None:
            continue

        r_id = blip.get(f"{{{_DOC_REL}}}embed")
        if r_id is None:
            r_id = blip.get(f"{{{_DOC_REL}}}link")
        if r_id is None:
            continue

        image_path = rId_to_image.get(r_id)
        if image_path is None:
            continue

        row_el = _local_find(from_el, "row")
        col_el = _local_find(from_el, "col")
        if row_el is None or col_el is None:
            continue

        row = int(row_el.text)
        col = int(col_el.text)
        anchors[(row, col)] = image_path

    return anchors


# ── Main CLI ────────────────────────────────────────────────────────────


def main():
    # ── Load config ──────────────────────────────────────────────────
    config_path = Path(__file__).parent / "config.json"
    config = load_config(str(config_path))
    input_folder = Path(config["input_folder"])
    output_folder = Path(config["output_folder"])

    # ── Validate input folder ────────────────────────────────────────
    if not input_folder.is_dir():
        print(f"Input folder not found: {input_folder}", file=sys.stderr)
        sys.exit(2)

    # ── Create output folder ─────────────────────────────────────────
    output_folder.mkdir(parents=True, exist_ok=True)

    # ── Process each .xlsx ───────────────────────────────────────────
    total_images = 0
    total_files = 0

    for xlsx_path in sorted(input_folder.glob("*.xlsx")):
        # Skip Excel temporary files (prefixed with ~$)
        if xlsx_path.name.startswith("~$"):
            continue

        print(f"Processing: {xlsx_path.name}")
        total_files += 1

        # Open the workbook for sheet/cell metadata
        try:
            wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        except Exception as exc:
            print(f"  ERROR: Cannot open workbook — {exc}", file=sys.stderr)
            continue

        try:
            with zipfile.ZipFile(xlsx_path, "r") as zf:
                for sheet_idx, ws in enumerate(wb.worksheets, start=1):
                    sheet_name = ws.title

                    drawing_path = _find_drawing_path(zf, sheet_idx)
                    if drawing_path is None or drawing_path not in zf.namelist():
                        continue

                    image_map = _parse_drawing_image_map(zf, drawing_path)
                    if not image_map:
                        continue

                    for (anchor_row, anchor_col), zip_path in image_map.items():
                        label = get_label(ws, anchor_row, anchor_col)
                        filename = build_filename(
                            sheet_name,
                            label,
                            anchor_row,
                            anchor_col,
                        )

                        # Handle duplicate filenames by appending _1, _2, …
                        out_path = output_folder / filename
                        if out_path.exists():
                            counter = 1
                            while counter < 100:
                                candidate = output_folder / (
                                    out_path.stem + f"_{counter}" + out_path.suffix
                                )
                                if not candidate.exists():
                                    out_path = candidate
                                    break
                                counter += 1

                        try:
                            with zf.open(zip_path) as src:
                                data = src.read()
                            if len(data) < 500:
                                continue  # skip noise/spacer images
                            with open(out_path, "wb") as dst:
                                dst.write(data)
                            total_images += 1
                            print(f"  Extracted: {out_path.name}")
                        except KeyError:
                            print(
                                f"  ERROR: Image not found in zip: {zip_path}",
                                file=sys.stderr,
                            )

        except PermissionError:
            print(
                f"  ERROR: Permission denied — '{xlsx_path.name}'",
                file=sys.stderr,
            )
        except zipfile.BadZipFile:
            print(
                f"  ERROR: '{xlsx_path.name}' is not a valid ZIP/XLSX file",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
        finally:
            wb.close()

    print(f"\nDone. Extracted {total_images} images from {total_files} files.")


if __name__ == "__main__":
    main()
