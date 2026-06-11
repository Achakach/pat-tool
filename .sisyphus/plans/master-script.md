# Master Pipeline Script

## TL;DR

> `python run.py` at root → runs all 5 tools in order. Handles file copying between stages.
>
> **Estimated Effort**: Medium

---

## How It Works

```
python run.py

  1-png-extractor       PNGs out ──────────────────────────┐
  2-template-generator  blank targets ──→ copier target/    │
  3-column-copier       source + target → output            │
                        copy → editor input/                │
  4-cell-editor         edited output                       │
                        copy → inserter xlsx/               │
  5-png-inserter        edited xlsx + PNGs → FINAL ────────┘
  6-cleanup             delete temp columns from source
```

## Prerequisites (manual)

1. Source XLSX placed in:
   - `1-png-extractor/input/` (for extraction)
   - `3-column-copier/source/` (for column copying)
2. `matching.xlsx` populated with planwork→filename mappings
3. Each tool's `config.json` configured

## Root Config

```json
{
  "pipeline": {
    "1-png-extractor": {
      "command": "cd 1-png-extractor && python extract_pngs.py",
      "copy": [
        { "from": "1-png-extractor/output/*.png", "to": "5-png-inserter/input/" }
      ]
    },
    "2-template-generator": {
      "command": "cd 2-template-generator && python generate.py",
      "copy": [
        { "from": "2-template-generator/output/*.xlsx", "to": "5-png-inserter/xlsx/" },
        { "from": "2-template-generator/output/*.xlsx", "to": "3-column-copier/target/" }
      ]
    },
    "3-column-copier": {
      "command": "cd 3-column-copier && python copier.py",
      "copy": [
        { "from": "3-column-copier/output/*.xlsx", "to": "4-cell-editor/input/" }
      ]
    },
    "4-cell-editor": {
      "command": "cd 4-cell-editor && python edit.py",
      "copy": [
        { "from": "4-cell-editor/output/*.xlsx", "to": "5-png-inserter/xlsx/" }
      ]
    },
    "5-png-inserter": {
      "command": "cd 5-png-inserter && python insert.py"
    }
  }
}
```

## run.py

```python
import json, subprocess, sys, shutil
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    config = json.load(open(ROOT / "pipeline.json"))
    
    for step_name, step in config["pipeline"].items():
        print(f"\n{'='*50}")
        print(f"  {step_name}")
        print(f"{'='*50}")
        
        # Run the tool
        result = subprocess.run(step["command"], shell=True, cwd=str(ROOT))
        if result.returncode != 0:
            print(f"  FAILED (exit {result.returncode})")
            if step.get("required", True):
                sys.exit(1)
        
        # Copy output files
        for copy in step.get("copy", []):
            for src in ROOT.glob(copy["from"]):
                dst = ROOT / copy["to"] / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            print(f"  Copied: {copy['from']} -> {copy['to']}")
    
    print(f"\n{'='*50}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
```

---

## TODOs

- [x] 1. Create pipeline.json at root
- [x] 2. Create run.py at root
- [x] 3. Test full pipeline end-to-end
