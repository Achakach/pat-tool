## [2026-06-15] QA Verification Results

### Files Analyzed (7 total):
1. e2e_target.xlsx — 2 sheets, 1 PNG each
2. e2e_v2_target.xlsx — 2 sheets, 1 PNG each
3. test1_target.xlsx — 2 sheets, 1 PNG each
4. test2_target.xlsx — 1 sheet, 4 PNGs (3 page breaks)
5. test_fixture.xlsx — 2 content sheets + 2 misc sheets
6. test_fixture2.xlsx — 2 content sheets + 2 misc sheets

### SUMMARY: 7/18 sheets PASS, 11/18 sheets FAIL

### FAIL CATEGORIES:

**1. First label always at row 10 (ALL sheets)** — position 10 on page 1
   - Root cause: purge_from_row=10, first site has no page break inserted (start_row <= purge_from check in insert_png)
   - Label is at row 10, page starts at row 1, so position = 10 > 3 → FAIL

**2. test_fixture.xlsx / test_fixture2.xlsx — breaks misaligned**
   - test_fixture.xlsx '2.1. Bayface_Before': breaks at 93, 139, 185, 231 (expected 52, 103, 154, 205)
   - test_fixture.xlsx '2.2. Bayface_After': breaks at 139, 185, 231, 277 (expected 52, 103, 154, 205)
   - (93-1)%51=41≠0, (139-1)%51=36≠0 — all breaks fail alignment
   - These files were likely generated with different page_rows config or have pre-existing content

### PASS:
- test2_target.xlsx '2.1. Bayface_Front': All 3 breaks aligned (52, 103, 154)
- Subsequent labels after breaks always at position 1 (correct page top)
