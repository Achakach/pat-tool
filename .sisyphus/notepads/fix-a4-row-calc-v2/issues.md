# Issues — fix-a4-row-calc-v2

## F4 Scope Fidelity — 2026-06-18 — REJECT

### Blockers
1. **_setup_a4_print modified** (Must NOT) — try/except added around autoPageBreaks in Task 1 commit a028ed7. Also propagated to tool 3.
2. **Tool 3 contaminated** — `3-column-copier/src/print_setup.py` + tests modified despite explicit prohibition.
3. **9 files contaminated** across tools 1-4 — `main(config=None)` pattern, test additions, file deletion.
4. **extractor.py DELETED** — `1-png-extractor/src/extractor.py` removed without authorization.
5. **Plan file modified** — checkboxes marked [x] for T2-T8. Plan is read-only per Sisyphus protocol.

### Non-blocking issues
6. **Test mismatch**: `test_calc_page_rows_mixed_mode` uses mode=15 (result 52) but plan specified mode=24 (result 33). Doesn't validate the 24pt scenario.
7. **4 unplanned tests**: `test_no_crash_on_missing_page_setup_pr` + ~3 in `TestMainIntegration`.
8. **Task 8 unverified**: No evidence of full suite run.

### Remediation needed
- Revert `_setup_a4_print` changes in both tool 5 and tool 3
- Revert ALL tool 1-4 changes (9 files)
- Remove `test_no_crash_on_missing_page_setup_pr` and `TestMainIntegration`
- Restore deleted `extractor.py`
- Add proper 24pt-mode test per plan spec
- Restore plan file from git
