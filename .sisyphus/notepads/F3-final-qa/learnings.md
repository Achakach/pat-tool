# F3: Real Manual QA — Learnings

## Test Results (2026-06-19)
- 53/53 tests passed across 6 test files
- Integration test: shift_image_anchors anchor shift verified (9 → 14)
- Edge cases: empty _images, zero rows, negative rows — all handled

## Key Finding: openpyxl 3.1.5 anchor behavior
- `ws.add_image(img, 'A10')` stores anchor as **string** ('A10'), NOT as AnchorMarker
- The plan's integration snippet used `._images[0].anchor._from.row` which fails on string anchors
- Fixed by using explicit `OneCellAnchor()` + `AnchorMarker()` creation (matching test patterns)
- `shift_image_anchors()` correctly handles string anchors via isinstance checks — unknown types get warning and skip

## Evidence Saved
- `.sisyphus/evidence/final-qa/full_test_suite.txt` — 53 passed
- `.sisyphus/evidence/final-qa/integration_test.txt` — anchor shift PASS
- `.sisyphus/evidence/final-qa/edge_cases.txt` — 3/3 edge cases PASS
- `.sisyphus/evidence/final-qa/VERDICT.txt` — APPROVE
