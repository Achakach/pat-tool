# Configurable Noise Threshold

## TL;DR

> **Quick Summary**: Add `noise_threshold` to config.json, default 5000 bytes. Skip images below this size.
>
> **Estimated Effort**: Trivial (2 files)

---

## What Changes

### png-extractor/config.json
```json
{
  "input_folder": "./input",
  "output_folder": "./output",
  "noise_threshold": 5000
}
```

### png-extractor/extract_pngs.py
Read threshold from config and use it:
```python
noise_threshold = config.get("noise_threshold", 5000)
# Then in extraction: if len(data) < noise_threshold: continue
```

Also update `png-extractor/src/extractor.py` if it has the same hardcoded threshold.

---

## TODOs

- [x] 1. Add noise_threshold to config.json (default 5000)
- [x] 2. Update extract_pngs.py to read from config
- [x] 3. Update extractor.py if needed
- [x] 4. Verify — 3000B images filtered, >5000B kept
