# Draft: PNG to XLSX Insertion Tool

## Requirements (confirmed)
- Configurable matching via an XLSX file
- User provides: XLSX with filename + planwork columns
- Match only for now — position logic later
- Separate tool in its own folder (like png-extractor, cell-editor)

## How it works (my understanding)

**matching.xlsx** (user provides):
```
Column A            Column B
report_001.xlsx     bkk007
other_002.xlsx      bkk101
```

**PNG folders** (from extractor):
```
input/
├── bkk007/
│   ├── PW planwork100_exist BKK01_Bayface Before.png
│   └── PW planwork100_exist BKK01_Bayface After.png
├── bkk101/
│   └── ...
```

**Flow**:
1. Read matching.xlsx → map filenames to planwork codes
2. For each XLSX in the xlsx folder, look up its planwork
3. Find the PNG subfolder matching that planwork
4. Insert all PNGs into the XLSX (position TBD)

## Open Questions
- Config format: separate JSON or all in matching.xlsx?
- Is this understanding correct?
