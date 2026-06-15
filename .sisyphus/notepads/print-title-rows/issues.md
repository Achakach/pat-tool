# Issues — print-title-rows

> All issues encountered across page-break-fix and print-title-rows sessions. Compiled 2026-06-15.

---

## #1: Wrong margins on first page calculation

**Session**: previous (page-break-fix)
**Severity**: critical
**Status**: fixed

**Symptom**: First page's row count was calculated using default Excel margins (0.75" top/bottom) instead of the 0.5" margins set by `_setup_a4_print()`. This produced a page that was slightly too short, causing a one-row misalignment on page 1 only.

**Root Cause**: `_calc_page_rows()` was called BEFORE `_setup_a4_print()` on the first invocation. It read the worksheet's default margin settings, which were still the Excel defaults at that point. `_setup_a4_print()` hadn't run yet, so the 0.5" margins weren't applied.

**Fix**: Moved the `_calc_page_rows()` call to AFTER `_setup_a4_print()` in the execution order. This ensures margins are set before the page row calculation reads them.

**Prevention**: When a function (A) modifies state that another function (B) reads, enforce a call-order invariant. Use a comment or assert at the call site. In test setup, call both functions in the same order the production code uses.

---

## #2: Excel ignoring manual page breaks

**Session**: previous (page-break-fix)
**Severity**: critical
**Status**: fixed

**Symptom**: Manual `Break` objects inserted via `ws.page_breaks.append(Break(row=N))` were silently ignored. Excel paginated as if the breaks didn't exist.

**Root Cause**: The worksheet had `fitToPage=True` enabled (via `ws.page_setup.fitToWidth = 1` and `ws.page_setup.fitToHeight = 1`). Excel's scaling engine ignores manual break positions when fit-to-page is active — it overrides them with its own calculated breaks.

**Fix**: Removed `fitToWidth` and `fitToHeight` settings entirely. Page breaks now rely solely on manual breaks or (later) `autoPageBreaks=True`.

**Prevention**: `fitToPage` and manual `Break` objects are mutually exclusive in Excel's rendering engine. If you insert manual breaks, verify `fitToPage` is off. Document this in any future code that manipulates page breaks.

---

## #3: Page count off by one (truncation vs ceiling)

**Session**: previous (page-break-fix)
**Severity**: high
**Status**: fixed

**Symptom**: Page boundary calculations were consistently one row off. The last row of each page ended up on the next page.

**Root Cause**: `int(769.89 / 15)` truncates 51.326 to 51. Excel uses ceiling semantics (51.326 → 52 rows per page). This caused the code to undercount rows by one, shifting all page boundaries.

**Fix**: Replaced `int(769.89 / 15)` with `math.ceil(769.89 / 15)`. Now uses `page_rows = math.ceil(a4_content_height_px / default_row_height_px)`.

**Prevention**: Any time you calculate a count from a ratio where the remainder must occupy its own slot, use `math.ceil` not `int()` / truncation. This is a recurring pattern — grep for `int(.*/.*)` in page-break-related code to audit.

---

## #4: Manual break conflict with auto-break engine

**Session**: previous (page-break-fix)
**Severity**: high
**Status**: fixed

**Symptom**: Inserting manual breaks at rows 53, 105, 157 produced actual page breaks at 54, 106, 158 — each break was shifted down by one row.

**Root Cause**: When `autoPageBreaks=True` and manual `Break` objects are both present, Excel's auto-break engine adjusts manual breaks to its own calculated positions. The auto-break engine expected breaks at 54, 106, 158 (its own calculation), so it reinterpreted the manual breaks as being one row off.

**Fix**: Removed all manual `Break` object insertion entirely. Set `autoPageBreaks=True` and let Excel's native engine handle all page break placement. This also simplified the code.

**Prevention**: `autoPageBreaks=True` is the simpler and more reliable approach. Only use manual `Break` objects when you need exact control that the auto engine cannot provide — and when you do, be aware that Excel may shift them.

---

## #5: Duplicate TestPrintTitleRows class

**Session**: current (print-title-rows)
**Severity**: critical
**Status**: fixed

**Symptom**: Running `pytest tests/test_page_breaks.py -v` showed 0 tests under `TestPrintTitleRows`, even though both Task 1 and Task 2 subagents had written tests to that class.

**Root Cause**: Two parallel subagents independently created `class TestPrintTitleRows:` in the same file (`test_page_breaks.py`). Python does not error on duplicate class definitions — the second definition silently overwrites the first. Task 2's tests never appeared because their class was the one that survived (last definition wins), but all Task 1's tests were lost. Neither subagent was aware of the other.

**Fix**: Renamed Task 2's class to `TestSetupA4PrintTitleRows` and verified all tests appeared in `pytest --collect-only`.

**Prevention**: When spawning parallel subagents that modify the same file, use a shared class registry or a pre-agreed naming convention. Alternatively, have each subagent write to a separate file and merge afterward. Do not assume subagents know about each other's work.

---

## #6: test_fixture.xlsx accidentally modified

**Session**: current (print-title-rows)
**Severity**: high
**Status**: fixed

**Symptom**: Running tests modified `5-png-inserter/out/test_fixture.xlsx` (a binary test fixture), causing it to show up in `git diff` as a changed file. This polluted the working tree with unintended modifications.

**Root Cause**: Tests call `insert_png()` which internally calls `wb.save('out/test_fixture.xlsx')`. The output path points to the same directory as the fixture file, so the test mutated the fixture in-place.

**Fix**: Restored the file via `git checkout -- 5-png-inserter/out/test_fixture.xlsx`.

**Prevention**: Test fixtures should be read-only. Either (a) copy the fixture to a temp directory before testing, (b) use `tmp_path` fixtures that pytest auto-cleans, or (c) ensure `wb.save()` writes to a separate test output directory, not the source fixture location.

---

## #7: `_parse_print_title_rows` unused `start` variable

**Session**: current (print-title-rows)
**Severity**: low
**Status**: not fixed

**Symptom**: The function parses both `start` and `end` from the config string (e.g. `"1:6"` -> start=1, end=6) but only uses `end` to compute `header_count`. The `start` variable is assigned but never read.

**Root Cause**: For `"1:N"` ranges, `header_count = end` is equivalent to `header_count = end - start + 1` because start=1. The developer chose the simpler formula without removing the unused `start` parse.

**Impact**: For `"1:6"` this returns 6 — correct. For `"3:8"` it would return 8 instead of 6 (off by 3). Currently cosmetic because all realistic configs use `"1:N"`, but fragile.

**Fix**: None applied. The proper fix is `header_count = end - start + 1` and removing the unused variable. Low priority.

**Prevention**: Linter rules (e.g., `pylint W0612` / `pyflakes F841`) catch unused variables. Enable them in CI. The linter would have flagged `start` as unused immediately.

---

## #8: Missing safety guard for `header_count >= page_rows`

**Session**: current (print-title-rows)
**Severity**: low
**Status**: not fixed

**Symptom**: If a user sets `"print_title_rows": "1:52"` or higher (where header_count >= page_rows of 52), the formula `content_rows = page_rows - header_count` would compute 0 or negative. This would cause either a crash or incorrect behavior in snap/overflow calculations.

**Root Cause**: The plan specified a guard that would disable the feature if `header_count >= page_rows` (preventing division by zero in content row calculations), but it was not implemented during the session.

**Impact**: Low in practice — realistic header counts are 1–10 rows, far below 52. But a careless config value would silently break.

**Fix**: None applied. The guard should check `if header_count >= page_rows: header_count = 0; logger.warning(...)`.

**Prevention**: Plan items should be checked against the final diff during code review. The guard was clearly specified in the plan but dropped during implementation.

---

## #9: Config default `null` confused user

**Session**: current (print-title-rows)
**Severity**: medium
**Status**: workaround

**Symptom**: The config default is `"print_title_rows": null` (feature disabled). The user ran the first test without changing it and saw no header rows repeating. This was expected behavior but not obvious.

**Root Cause**: `null` means disabled. The user did not know they had to explicitly set `"1:6"` to enable the feature.

**Fix**: No code change. Resolution was documentation: `null = disabled, user must explicitly set a range`.

**Prevention**: Document defaults clearly in config.json comments and README. Consider printing a one-line log statement at startup: `print_title_rows: null (feature disabled)`. This makes the state visible.

---

## #10: `_setup_a4_print` debug print mismatch

**Session**: current (print-title-rows)
**Severity**: low
**Status**: not fixed

**Symptom**: The debug message logs `autoPageBreaks=False` but the code on the next line sets `ws.page_setup.autoPageBreaks = True`. The log string contradicts the actual behavior.

**Root Cause**: Copy-paste error from a previous refactor. The debug string was not updated when the setting changed from False to True.

**Impact**: Cosmetic. Developers reading debug output would see the wrong value, but no functional impact.

**Fix**: None applied. The debug string should read `autoPageBreaks=True`.

**Prevention**: Review debug/log messages when changing the associated setting. Automated: a test that checks `ws.page_setup.autoPageBreaks` against a known expected value would catch this.

---

## Summary

| # | Title | Severity | Status |
|---|-------|----------|--------|
| 1 | Wrong margins on first page calculation | critical | fixed |
| 2 | Excel ignoring manual page breaks | critical | fixed |
| 3 | Page count off by one (truncation vs ceiling) | high | fixed |
| 4 | Manual break conflict with auto-break engine | high | fixed |
| 5 | Duplicate TestPrintTitleRows class | critical | fixed |
| 6 | test_fixture.xlsx accidentally modified | high | fixed |
| 7 | `_parse_print_title_rows` unused `start` variable | low | not fixed |
| 8 | Missing safety guard for `header_count >= page_rows` | low | not fixed |
| 9 | Config default `null` confused user | medium | workaround |
| 10 | `_setup_a4_print` debug print mismatch | low | not fixed |
