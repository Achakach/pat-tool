# End-to-End Test Plan — Full Pipeline

## Mock Scenario

One construction site report. Source XLSX has 2 images + PW sheet + config data. Target gets columns filled, labels fixed, PNGs inserted, temp columns cleaned.

## Step 1: Create Mock Source XLSX

```
source.xlsx
├── "PW PLANCK01"
├── "exist BKK101"     (image at A2, label "Bayface Before" at A1)
├── "new BKK102"       (image at B5, label "Bayface After" at B4)
├── "cutsheet"          (data: NE_NO in col C+D, etc.)
└── "Get Log Before&After" (row 1: CR10SDA_10.10.10.10, CR11SDA_10.10.11.11)
```

## Step 2: Run 1-png-extractor

```
cd 1-png-extractor
python extract_pngs.py
```

Output: `PW PLANCK01_exist BKK101_Bayface Before.png`
        `PW PLANCK01_new BKK102_Bayface After.png`

Copy PNGs to `4-png-inserter/input/`.

## Step 3: Run 5-column-copier

```
cd 5-column-copier
python copier.py
```

Source cutsheet → add PW col Q + IP col R + IP col S.
Copy all to target via matching.xlsx.

## Step 4: Run 2-template-generator (if target doesn't exist)

```
cd 2-template-generator
python generate.py
```

## Step 5: Run 3-cell-editor on target

Fix labels in target (e.g., "name:" → "name: kacha").

## Step 6: Run 4-png-inserter

```
cd 4-png-inserter
python insert.py
```

Match PNGs → insert into target with labels, A4 formatting.

## Step 7: Cleanup

```
cd 5-column-copier
# Set action: "cleanup" in config, run:
python copier.py
```

Delete PW + IP temp columns from source.

---

## Expected Results

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 2 | extractor | source.xlsx | 2 PNGs with PW naming |
| 3 | copier | source.xlsx | target with PW/IP/NE_NO columns |
| 5 | cell-editor | target (edited) | labels fixed |
| 6 | inserter | target + PNGs | labeled PNGs inserted, A4 print |
| 7 | copier | source.xlsx | temp columns deleted |

---

## TODOs

- [ ] 1. Create mock source XLSX with all sheets/data
- [ ] 2. Create matching.xlsx entries
- [ ] 3. Run extractor → verify PNG names
- [ ] 4. Run copier (copy) → verify target columns
- [ ] 5. Run cell-editor → verify label changes
- [ ] 6. Run inserter → verify PNG placement
- [ ] 7. Run copier (cleanup) → verify temp columns gone

---

## Test Assertions

```python
# After step 2
assert output/ contains "PW PLANCK01_exist BKK101_Bayface Before.png"
assert output/ contains "PW PLANCK01_new BKK102_Bayface After.png"

# After step 3
assert target.Q1 == "PW"
assert target.R1 == "IP_Exist"

# After step 6
assert target sheet has 2 images
assert target page_setup.paperSize == 9  # A4

# After step 7
assert source no longer has Q, R, S columns
```
