# Issues

## From F2 Code Quality Review (2026-06-15)

### Minor (non-blocking)
1. **inserter.py:143,177** — Magic `0.75` (pixels→points: 72/96 DPI) undocumented
2. **inserter.py:90,142** — `15` (default row height) duplicated as local vars
3. **insert.py:193,198** — Magic `10` fallback for `purge_from` undocumented
4. **inserter.py:110-112 vs 163-165** — PNG dimension reading duplicated in two functions (minor DRY)
