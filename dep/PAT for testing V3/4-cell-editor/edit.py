#!/usr/bin/env python3
"""CLI for XLSX cell text editor — prefix-match and replace cell values."""

import sys
import json
from pathlib import Path
from src.editor import process_workbook

def main(config=None):
    # Load config
    if config is None:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        input_folder = (Path(__file__).parent / config["input_folder"]).resolve()
        output_folder = (Path(__file__).parent / config["output_folder"]).resolve()
    else:
        input_folder = Path(config["input_folder"]).resolve()
        output_folder = Path(config["output_folder"]).resolve()

    replacements = config["replacements"]
    match_mode = config.get("match_mode", "first")
    
    if not replacements:
        print("No replacements configured in config.json", file=sys.stderr)
        sys.exit(1)
    
    if not input_folder.is_dir():
        print(f"Input folder not found: {input_folder}", file=sys.stderr)
        sys.exit(2)
    
    output_folder.mkdir(parents=True, exist_ok=True)
    
    total_changed = 0
    total_files = 0
    
    for xlsx_path in sorted(input_folder.glob("*.xlsx")):
        if xlsx_path.name.startswith("~$"):
            continue
        
        print(f"Processing: {xlsx_path.name}")
        total_files += 1
        
        output_path = output_folder / xlsx_path.name
        
        try:
            changed = process_workbook(xlsx_path, output_path, replacements, match_mode)
            total_changed += changed
            print(f"  Changed {changed} cell(s)")
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
    
    print(f"\nDone. Changed {total_changed} cell(s) in {total_files} file(s).")

if __name__ == "__main__":
    main()
