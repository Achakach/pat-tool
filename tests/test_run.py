"""Tests for run.py — the master pipeline orchestrator.

All tests run run.py as a subprocess in a tmp_path to isolate from real
project files. Pipeline configs use no-op echo commands (no real PAT tools).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RUN_PY = ROOT / "run.py"


def run_pipeline(tmp_path, pipeline_config):
    """Write pipeline.json, copy run.py to tmp_path, and execute it."""
    pipeline_path = tmp_path / "pipeline.json"
    pipeline_path.write_text(json.dumps(pipeline_config), encoding="utf-8")
    shutil.copy2(RUN_PY, tmp_path / "run.py")
    result = subprocess.run(
        [sys.executable, "run.py"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result


class TestRunPy:
    """Integration tests for the run.py orchestrator."""

    # ── Test 1: all stages run successfully ─────────────────────────────

    def test_runs_all_stages(self, tmp_path):
        config = {
            "pipeline": {
                "Stage 1": {"command": "echo Stage 1 done"},
                "Stage 2": {"command": "echo Stage 2 done"},
                "Stage 3": {"command": "echo Stage 3 done"},
            }
        }
        result = run_pipeline(tmp_path, config)

        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        assert "Stage 1" in result.stdout
        assert "Stage 2" in result.stdout
        assert "Stage 3" in result.stdout
        assert "PIPELINE COMPLETE" in result.stdout

    # ── Test 2: pipeline stops on failure ──────────────────────────────

    def test_stops_on_failure(self, tmp_path):
        config = {
            "pipeline": {
                "Stage 1": {"command": "echo Stage 1 done"},
                "Stage 2": {"command": "exit 1"},
                "Stage 3": {"command": "echo Stage 3 done"},
            }
        }
        result = run_pipeline(tmp_path, config)

        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        assert "Stage 1" in result.stdout
        assert "Stage 2" in result.stdout
        assert "Stage 3" not in result.stdout, (
            "Stage 3 should not have run after Stage 2 failure"
        )
        assert "PIPELINE COMPLETE" not in result.stdout

    # ── Test 3: files copied between stages ─────────────────────────────

    def test_copies_files_between_stages(self, tmp_path):
        config = {
            "pipeline": {
                "Stage 1": {
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "p = Path('stage1_out'); "
                        "p.mkdir(exist_ok=True); "
                        "(p / 'file.txt').write_text('hello from stage1')\""
                    ),
                    "copy": [{"from": "stage1_out/*.txt", "to": "stage2_in/"}],
                },
                "Stage 2": {"command": "echo Stage 2 done"},
            }
        }
        result = run_pipeline(tmp_path, config)

        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        assert "Copied 1 file(s)" in result.stdout

        copied_file = tmp_path / "stage2_in" / "file.txt"
        assert copied_file.exists(), f"Expected file at {copied_file}"
        assert copied_file.read_text() == "hello from stage1"

    # ── Test 4: empty stage with no matching copy files ─────────────────

    def test_handles_empty_stage(self, tmp_path):
        config = {
            "pipeline": {
                "Stage 1": {
                    "command": "echo nothing produced",
                    "copy": [{"from": "nonexistent_dir/*.txt", "to": "output/"}],
                }
            }
        }
        result = run_pipeline(tmp_path, config)

        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        assert "Copied 0 file(s)" in result.stdout
        assert "PIPELINE COMPLETE" in result.stdout

    # ── Test 5: missing pipeline.json causes non-zero exit ──────────────

    def test_missing_pipeline_json(self, tmp_path):
        # Copy run.py but do NOT create pipeline.json
        shutil.copy2(RUN_PY, tmp_path / "run.py")
        result = subprocess.run(
            [sys.executable, "run.py"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode != 0, (
            f"Expected non-zero exit for missing pipeline.json, "
            f"got {result.returncode}"
        )
