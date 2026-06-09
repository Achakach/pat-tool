# Hardcode config.json Path

## TL;DR

> **Quick Summary**: Remove `--config` CLI argument. Always load `config.json` from the same directory as the script.
>
> **Estimated Effort**: Trivial (1 file, 5 lines changed)

---

## What Changes

### extract_pngs.py

**Remove** the `--config` argparse argument. **Hardcode** the path:

```python
# Before:
parser.add_argument("--config", required=True, ...)
config = load_config(args.config)

# After:
config = load_config(str(Path(__file__).parent / "config.json"))
```

This means `config.json` must live in the same folder as `extract_pngs.py`.

---

## TODOs

- [x] 1. Remove `--config` from argparse, hardcode path to `config.json` next to script
- [x] 2. Run `python extract_pngs.py` (no --config) — verify it works
- [x] 3. Update integration tests that passed `--config` — now just run script with no args

---

## Verification

```bash
python extract_pngs.py
# Expected: processes input folder from config.json without --config flag
```
