# Issues — xlsx-png-extractor

## Session: ses_168b57026ffedH6d5AiS6ldaLx

### F2 Code Quality Review — 2026-06-08

**1. generate_fixture.py:45 — Hardcoded absolute path**
`out_path = r"C:\Users\kacha\OneDrive\Desktop\PAT tool\test_fixture.xlsx"`
Breaks portability. Should use `__file__`-relative path or accept output dir as argument.

**2. extract_pngs.py:232-240 — Duplicate filename counter silent overwrite**
When all 100 possible names exist (`file.png` through `file_99.png`), the `while counter < 100` loop exhausts without finding a free slot. Code falls through and writes to the original `out_path`, silently overwriting `file.png`. Should add overflow handling (warning, error, or dynamic counter beyond 99).

**3. config.py:23 — Misleading error message for JSON parse failure**
`json.JSONDecodeError` handler prints "Invalid config: missing 'input_folder' or 'output_folder'" but the real problem is malformed JSON, not missing fields. Correct message should indicate invalid JSON format.
