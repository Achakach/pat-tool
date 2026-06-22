"""CLI subprocess tests for extract_pngs.py — simulate real user invocation.

Each test copies extract_pngs.py + src/ into a temp directory so the
subprocess runs in complete isolation without touching the real config.json.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest
from openpyxl.drawing.image import Image as XlImage

# ── Paths ───────────────────────────────────────────────────────────────────

SCRIPT = Path(__file__).parent.parent / "extract_pngs.py"
SRC = Path(__file__).parent.parent / "src"

# Minimal valid 1×1 pixel PNG (valid PNG header + IHDR + IDAT + IEND chunks)
_PNG_DATA = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _setup(tmp_path: Path, config_dict: dict | None = None) -> Path:
    """Copy extract_pngs.py + src/ into tmp_path/tool1/, optionally write config.json.

    Returns the tool directory path where the script lives.
    """
    d = tmp_path / "tool1"
    d.mkdir()
    shutil.copy2(SCRIPT, d / "extract_pngs.py")
    shutil.copytree(SRC, d / "src")
    if config_dict is not None:
        (d / "config.json").write_text(json.dumps(config_dict), encoding="utf-8")
    return d


# ── Tests ───────────────────────────────────────────────────────────────────


class TestCLI:
    """Subprocess integration tests for the extract_pngs.py CLI."""

    def test_happy_path(self, tmp_path: Path):
        """Full pipeline: create XLSX with image → run CLI → verify PNG output."""
        d = _setup(
            tmp_path,
            config_dict={
                "input_folder": "./input",
                "output_folder": "./output",
                "noise_threshold": 0,
            },
        )

        # Create input directory and XLSX
        in_dir = d / "input"
        in_dir.mkdir()

        xlsx_path = in_dir / "test.xlsx"
        wb = openpyxl.Workbook()

        # Sheet 1: PW sheet (planwork identifier)
        ws_pw = wb.active
        ws_pw.title = "PW XX001"

        # Sheet 2: exist sheet with embedded image
        ws_exist = wb.create_sheet("exist TestSite")
        # Label in B2 — get_label_with_row searches above the image anchor
        ws_exist["B2"] = "label"
        # Embed 1×1 PNG at B3 (XML anchor row=2, col=1 in 0-indexed)
        img = XlImage(io.BytesIO(_PNG_DATA))
        img.anchor = "B3"
        ws_exist.add_image(img)

        wb.save(str(xlsx_path))
        wb.close()

        # Run the CLI
        result = subprocess.run(
            [sys.executable, "extract_pngs.py"],
            cwd=str(d),
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Verify success
        assert result.returncode == 0, (
            f"CLI exit code {result.returncode}\n"
            f"STDERR: {result.stderr}\n"
            f"STDOUT: {result.stdout}"
        )
        assert "Done" in result.stdout, (
            f"Expected 'Done' in stdout, got:\n{result.stdout}"
        )

        # Verify output
        out_dir = d / "output"
        png_files = list(out_dir.glob("*.png"))
        assert len(png_files) >= 1, (
            f"Expected at least 1 PNG, got {len(png_files)}: "
            f"{[f.name for f in png_files]}"
        )

        png_name = png_files[0].name
        assert "PW_XX001" in png_name or "PW XX001" in png_name, (
            f"Filename missing PW reference: {png_name}"
        )
        assert png_files[0].stat().st_size > 0, "Output PNG is empty"

    def test_missing_config(self, tmp_path: Path):
        """No config.json → script should exit with code 1."""
        d = _setup(tmp_path, config_dict=None)  # no config.json created

        result = subprocess.run(
            [sys.executable, "extract_pngs.py"],
            cwd=str(d),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}\n"
            f"STDERR: {result.stderr}\n"
            f"STDOUT: {result.stdout}"
        )
        assert "not found" in result.stderr.lower() or "config" in result.stderr.lower(), (
            f"Expected error message in stderr, got:\n{result.stderr}"
        )

    def test_missing_input_folder(self, tmp_path: Path):
        """Valid config but missing input/ → script should exit with code 2."""
        d = _setup(
            tmp_path,
            config_dict={
                "input_folder": "./input",
                "output_folder": "./output",
                "noise_threshold": 0,
            },
        )
        # Do NOT create input/ directory

        result = subprocess.run(
            [sys.executable, "extract_pngs.py"],
            cwd=str(d),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2, (
            f"Expected exit code 2, got {result.returncode}\n"
            f"STDERR: {result.stderr}\n"
            f"STDOUT: {result.stdout}"
        )
        assert "input folder not found" in result.stderr.lower(), (
            f"Expected 'Input folder not found' in stderr, got:\n{result.stderr}"
        )
