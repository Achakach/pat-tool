# Draft: Verify Current PAT Tool Functionality

## Request (paraphrased)
Test that the current version of the codebase is functioning as intended.

## Context from handover.md
- 5-tool Python pipeline (1-png-extractor, 2-template-generator, 3-column-copier, 4-cell-editor, 5-png-inserter)
- run.py orchestrates via pipeline.json
- 184 tests across all tools + pipeline E2E (all passing at handover time)
- Latest completed work: image anchor shifting, A4 row-height fix, unified error handling, multi-source append
- 3 backlog items (medium priority, unplanned):
  1. Unify matching.xlsx parsers across tools 2/3/5
  2. Unify config injection across all 5 tools
  3. Fix _parse_print_title_rows duplication + stale /15 in tool 3 print_setup.py

## Updated Request
User wants mock data created for testing the PAT tool pipeline.

## Open Questions
- Should mock data be a generator script (reproducible) or static handcrafted fixtures?
- Should it be committed to the repo or generated into a temp directory?
- Which scenarios must the mock data cover? (happy path + edge cases)
- Should it exercise the full 5-tool pipeline or specific tools?
- What naming conventions and sample values to use? (sites, PW numbers, labels)

## Scope Boundaries (to confirm)
- INCLUDE: TBD
- EXCLUDE: TBD
