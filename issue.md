# Known Issues — PAT Tool

Source: `.sisyphus/handover.md` + diff of current repo vs `dep/PAT for testing V7`.

## Issues reintroduced by reverting tool code to V7

| # | Issue | Original fix | V7 behavior | Impact |
|---|-------|--------------|-------------|--------|
| 1 | Tool 5 hard-coded 15 pt row height | `_detect_row_height(ws)` + `pixels_to_points()` | `int(display_h * 0.75 / 15) + 1` | Images may split across A4 page boundaries on templates with non-15 pt row heights. |
| 2 | Tool 3 image anchors not shifted after `insert_rows()` | Added `src/images.py` + `shift_image_anchors()` after both `insert_rows` calls | No anchor shifting | Existing images in target sheet stay fixed while rows push down, causing overlap. |
| 3 | Inconsistent matching.xlsx error handling | Unified all tools to `ValueError` | Tool 2 `SystemExit(1)`, Tool 3 silent `{}`, Tool 5 `ValueError` | Harder to debug missing-column config mistakes; behavior differs per tool. |

## Issues still open from handover (present in both V7 and current)

| # | Issue | Detail |
|---|-------|--------|
| 4 | Duplicate matching.xlsx parsers | 3 separate implementations across tools 2/3/5 with different return types. |
| 5 | Config injection path resolution differs | All tools accept `main(config=None)` but resolve relative paths differently. |
| 6 | `_parse_print_title_rows` duplicated | Same logic in tools 3 and 5; tool 5 has a global guard that suppresses debug prints. |
| 7 | Tool 3 `src/print_setup.py` hardcoded `/15` | Should use `_detect_row_height()` like tool 5. |

## Notes

- V7 lacks `pipeline.json` and root orchestrator tests; this repo keeps them for usability.
- V7 `2-template-generator/config.json` includes unused `planwork_col`; current config lacks it.
