#!/usr/bin/env python3
"""Master pipeline — run all 5 tools in order, copy files between stages."""

import json
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    config = json.loads((ROOT / "pipeline.json").read_text(encoding="utf-8"))

    for step_name, step in config["pipeline"].items():
        print(f"\n{'=' * 50}")
        print(f"  {step_name}")
        print(f"{'=' * 50}")

        # Run the tool
        cmd = step["command"]
        print(f"  Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=str(ROOT))
        if result.returncode != 0:
            print(f"  FAILED (exit {result.returncode})")
            sys.exit(result.returncode)

        # Copy output files to next stage
        for copy_rule in step.get("copy", []):
            src_pattern = copy_rule["from"]
            dst_dir = ROOT / copy_rule["to"]
            copied = 0
            for src in sorted(ROOT.glob(src_pattern)):
                dst = dst_dir / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied += 1
            print(f"  Copied {copied} file(s): {src_pattern} -> {copy_rule['to']}")

    print(f"\n{'=' * 50}")
    print("  PIPELINE COMPLETE")
    print(f"{'=' * 50}")
    print(f"  Output: 5-png-inserter/output/")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
