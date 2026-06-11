# E2E Pipeline Test Plan

## Setup — Create Mock Data

Source XLSX (test1.xlsx) with:
- Sheet "PW TEST01"
- Sheet "exist SITE01": A1="Bayface Front", image at A2 (noisy 100×100)
- Sheet "new SITE02": B4="Bayface Back", image at B5 (noisy 100×100)
- Sheet "cutsheet": header row 2 (C=NE_NO, D=PORT_NO, E=L1, G=NE_NO2, H=PORT_NO2), data rows 3-4
- Sheet "Get Log Before&After": row 1 cells (CR10SDA_10.10.10.10, CR11SDA_10.10.11.11)

Template XLSX with sheets: "2.1. Bayface_Front", "2.2. Bayface_Back", "2.3. IP & Port Assignment(P.4)"

matching.xlsx: "test1_target" → TEST01

## Expected Results

### 1-png-extractor
Output: PW TEST01_exist SITE01_Bayface Front.png (30KB+)
        PW TEST01_new SITE02_Bayface Back.png (30KB+)

### 5-png-inserter  
Sheet "2.1. Bayface_Front": SITE01 label at row 10, 1 image
Sheet "2.2. Bayface_Back": SITE02 label at row 10, 1 image
print_title_rows: $1:$6, a4_page_rows: 60, paperSize: 9, fitToWidth: 1

### Cleanup
3-column-copier cleanup mode: PW+IP columns deleted from source

### 1-png-extractor
- [ ] PNGs extracted with correct `PW {planwork}_{prefix} {site}_{label}.png` naming
- [ ] Only sheets with exist/new prefix processed
- [ ] oneCellAnchor images extracted
- [ ] Noise threshold respected

### 2-template-generator
- [ ] Template copied for each unique filename in matching.xlsx
- [ ] Output in correct folder

### 3-column-copier
- [ ] PW column filled from sheet name
- [ ] IP columns filled from log sheet lookup
- [ ] Copy columns copied correctly
- [ ] Append mode stacks data (no overwrites)
- [ ] Target matched via planwork

### 4-cell-editor
- [ ] Prefix match finds cells
- [ ] Replaces cell to the RIGHT
- [ ] Merged cells handled
- [ ] match_mode "first" respected

### 5-png-inserter
- [ ] PNGs matched to correct XLSX via planwork
- [ ] PNGs matched to correct sheet via label
- [ ] Purge once per sheet
- [ ] Site labels (bold, gray) at correct positions
- [ ] One site per page (page boundary snap)
- [ ] Images scaled to image_display_width
- [ ] A4 print setup: paperSize=9, fitToWidth=1, narrow margins
- [ ] print_title_rows set
- [ ] Row breaks per site label
- [ ] Gap rows applied

## Edge Cases
- [ ] Empty source folder (no XLSX)
- [ ] No PW sheet in source
- [ ] No matching entry in matching.xlsx
- [ ] Target file missing
- [ ] Duplicate planwork names
- [ ] oneCellAnchor + twoCellAnchor mixed
- [ ] Multiple sources → same target (append)
- [ ] Very tall images (page boundary push)

## TODOs
- [x] 1. Create mock data for all 5 tools
- [x] 2. Run pipeline steps
- [x] 3. Verify each tool's output
- [x] 4. Report bugs found
