
## F4 Scope Fidelity Check — REJECT

### Violation: 5-png-inserter/tests/test_matcher.py

**Problem 1 — Removed existing test (not allowed):**
- Old class TestInsertPng with 	est_insert_creates_label_and_image was REMOVED
- Replaced with class TestMainIntegration with 	est_main_with_config_dict
- Plan only allows ADDING integration tests, not replacing existing tests

**Problem 2 — Orphaned module-level code (lines 261-294):**
- Body of old test left behind at module level
- Executes on every import: creates PNGs, writes workbooks, calls insert_png()
- Includes orphaned docstring and assertions outside any test function

**Fix needed:**
1. Restore TestInsertPng.test_insert_creates_label_and_image
2. Append (not replace) TestMainIntegration below it
3. Delete orphaned module-level code at lines 261-294
