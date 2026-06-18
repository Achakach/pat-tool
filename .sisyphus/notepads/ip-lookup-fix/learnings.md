# learnings.md

## 2026-06-17: IP regex replace for noisy strings

- Replaced `text.split("_", 1)` with `re.search(r'([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)` in `build_ip_column`
- Regex naturally handles:
  - Clean format `CR10SDA_10.10.10.10` → NE_NO=`CR10SDA`, IP=`10.10.10.10`
  - Wrapped format `new_100_10.0.0.1(MXaxxxx)` → NE_NO=`100`, IP=`10.0.0.1`
    (leading `new_` is skipped because `([^_]+)` starts matching from the first non-underscore char before the IP)
- `import re` was already present at line 1
- All 33 tests pass after the change

## 2026-06-17: Added test_lookup_wrapped_formats

- Added `@pytest.mark.parametrize` test with 4 wrapped/noisy formats to `TestIpColumn`
- Tests verify regex `([^_]+)_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})` extracts NE_NO + IP from noisy values like `new_100_10.0.0.1(MXaxxxx)`
- All 5 TestIpColumn tests pass (1 existing + 4 parametrized)
- Key insight: regex `re.search` finds NE_NO_IP pattern anywhere in string, so wrapping text before/after is fine
