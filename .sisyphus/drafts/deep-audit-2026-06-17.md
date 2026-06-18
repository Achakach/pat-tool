# Draft: Deep Audit — PAT Tool Codebase (2026-06-17)

## Audit Scope
5 parallel audits covering: code annotations, test coverage, error handling, config consistency, code duplication.

---

## 🔴 CRITICAL: Issues That Will Crash or Produce Wrong Output

### 1. MergedCell Crash (14 locations, 0 guards)
- **copier.py:219** — known bug, plan ready at `.sisyphus/plans/merged-cell-fix.md`
- **naming.py:67,73,76** — same pattern (read, not write, but still crashes)
- **columns.py:25,55** — writes to cells without MergedCell guard
- **No tool imports or checks for `MergedCell` anywhere in the project**

### 2. _parse_print_title_rows Wrong Return (Tool 5)
- **insert.py:48**: returns `end` instead of `end - start + 1`
- Tool 3's version already fixed this (FIX #8)
- Missing content_rows < 1 guard (FIX #9 also missing in tool 5)

### 3. Duplicate Filename Silent Overwrite (Tool 1)
- **extract_pngs.py:274**: when counter hits 100, silently overwrites original file

---

## 🟡 HIGH: Maintenance & Quality

### 4. A4 Print Code Diverged
- Tool 3 has 3 fixes (#8, #9, #10) applied
- Tool 5 has NONE of them — still has global _a4_print_setup_done guard
- _parse_print_title_rows, _setup_a4_print, _calc_page_rows all duplicated

### 5. Three Different matching.xlsx Parsers
- Tool 2: returns `list[str]` (filenames)
- Tool 3: returns `dict[str, str]` (planwork→filename)
- Tool 5: returns `dict[str, list[str]]` (filename→[planworks])
- Three different error handling strategies

### 6. Error Handling Gaps
- Tools 3 and 5 have NO try/except in main processing loops
- One corrupt file crashes entire tool run
- run.py ignores stderr entirely

### 7. Config Inconsistencies
- Tool 5 uses ./out vs ./output (all others)
- Tool 2 has dead planwork_col config field
- Tool 2 missing src/ package structure

### 8. AGENTS.md Stale
- Lists 4 tools, actual is 5
- Missing 3-column-copier entirely
- Wrong tool numbers

---

## 🟠 MEDIUM

### 9. Test Coverage Minor Gaps
- extract_planwork() — no direct test
- progress_bar() — no direct test
- No tests with no assertions (good)

### 10. Magic Numbers
- inserter.py: 0.75 pixels→points ratio undocumented
- inserter.py: 15 default row height duplicated

### 11. Config Path Handling
- Tool 5 uses is_absolute() check; tools 1-4 always resolve relative
- Minor inconsistency, both work

### 12. Stale Prototype Directories
- PAT for testing/ and PAT for testing V2/ contain full tool copies

---

## Priority Action Plan

1. 🔴 Fix MergedCell crash (copier.py:219 + 13 other locations)
2. 🔴 Fix _parse_print_title_rows in tool 5 (align with tool 3's FIX #8, #9)
3. 🔴 Fix duplicate filename overflow in extract_pngs.py
4. 🟡 Unify A4 print code between tools 3 and 5
5. 🟡 Add try/except to tool 3 and tool 5 main loops
6. 🟡 Unify matching.xlsx parsers
7. 🟡 Update AGENTS.md
8. 🟠 Clean up stale prototype directories
9. 🟠 Standardize output folder naming (./out → ./output)
10. 🟠 Remove dead planwork_col from tool 2 config
