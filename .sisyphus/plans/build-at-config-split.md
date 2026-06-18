# Split `paste_to` — Add `build_at` for Temp Column Safety

## TL;DR

> **Quick Summary**: Add `build_at` config key to separate temp column location (where data is built in source) from target column (where it's pasted). This prevents IP/PW temp columns from overwriting real source data when they share column letters with copy columns.
>
> **Deliverables**:
> - `copier.py`: build step uses `build_at`, paste step uses `build_at`→`paste_to` mapping
> - `config.json`: updated with `build_at` keys for PW/IP columns
> - Tests: verify backward compat (no `build_at` → uses `paste_to`) and new behavior
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO — single file change

---

## Context

### The Problem

Current config uses `paste_to` for two purposes — where to build the temp column in source AND where to paste in target:

```json
"IP1": {
    "type": "ip_lookup",
    "lookup_col": "C",
    "paste_to": "E"       ← builds at E (overwrites L1 data!)
}                          ← pastes E→E in target
```

When `paste_to` is E and source column E has L1 data, the IP lookup overwrites it before L1 can be copied.

### The Fix

Split into two keys:

```json
"IP1": {
    "type": "ip_lookup",
    "lookup_col": "C",
    "build_at": "R",      ← safe temp column in source (Q/R/S)
    "paste_to": "E"       ← target column
}
```

### Safe Column Layout

```
Source cutsheet (NEVER modified):    Target:
──────────────────────────────────    ──────────────────
C = NE_NO        ──direct──→         D = Exist L1 OLT
D = PORT_NO      ──direct──→         F = Existing Port
E = L1 name      ──direct──→         C = L1 Name
G = NE_NO2       ──direct──→         G = New L1 OLT
H = PORT_NO2     ──direct──→         I = New Port
Q = PW temp      ──direct──→         J = PW Number
R = IP1 temp     ──direct──→         E = Existing IP
S = IP2 temp     ──direct──→         H = New IP
```

No columns overwritten. Source file stays pristine. `copy_column` function removed entirely.

---

## Work Objectives

### Core Objective
Add `build_at` config key to allow temp columns to be built at safe locations (Q/R/S) while pasting to the correct target columns, preventing source data corruption.

### Concrete Deliverables
- `3-column-copier/copier.py` — two changes: build step reads `build_at`, paste step maps `build_at`→`paste_to`
- `3-column-copier/config.json` — add `build_at` to PW, IP1, IP2 columns
- `3-column-copier/tests/test_columns.py` — add 2 tests: backward compat + new behavior

### Definition of Done
- [ ] `build_at` respected in build step (planwork + ip_lookup)
- [ ] `build_at`→`paste_to` mapping correct in paste step
- [ ] Backward compat: missing `build_at` → falls back to `paste_to`
- [ ] All 21 existing tests still pass
- [ ] New test: `build_at` column contains temp data, `paste_to` column in target has correct data

### Must Have
- `build_at` optional — falls back to `paste_to` when absent
- Build step: use `col_cfg.get("build_at", col_cfg.get("paste_to"))`
- Paste step: read source from `build_at` col, write target to `paste_to` col
- Copy columns unaffected (they don't use `build_at`)

### Must NOT Have
- No changes to copy column behavior
- No new required config keys — `build_at` is optional
- No changes to other pipeline tools

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES — pytest, 21 tests
- **Automated tests**: TDD — RED → GREEN → REFACTOR
- **Framework**: pytest
- **Agent-Executed QA**: Run copier.py with real mapping, verify output columns

---

## TODOs

- [x] 1. **Add `build_at` + remove `copy_column` — paste directly source→target (TDD)**

  **What to do**:

  Currently the paste loop does two things: (1) `copy_column` modifies the source, then (2) pastes from source to target. This is unnecessary — we can read directly from the original source column and write to a different target column. The source file never gets touched.

  **RED**: Add 3 tests to `tests/test_columns.py`:
  1. `test_paste_direct_source_to_target` — config with `type: "copy", source_col: "C", paste_to: "D"` → reads C from source, writes D in target. No source modification.
  2. `test_build_at_maps_to_target` — config with `build_at: "R", paste_to: "E"` → reads R from source, writes E in target.
  3. `test_backward_compat_no_source_col` — config without `source_col` or `build_at` → falls back to `paste_to` for both read/write.

  **GREEN**: Modify `copier.py` in three places:

  **A. Build step (line 97-110)**: Use `build_at` for temp column placement:
  ```python
  build_at = col_cfg.get("build_at", col_cfg.get("paste_to"))
  ```
  Use in `build_pw_column()` and `build_ip_column()` calls.

  **B. REMOVE the `copy_column` call** (line 163). Delete:
  ```python
  if col_type == "copy":
      copy_column(sws, col_cfg["source_col"], col_cfg["paste_to"], start_row)
  ```

  **C. Paste step (lines 165-183)**: Determine source column from config, read from source, write to target:
  ```python
  # Determine source column based on type
  if col_type in ("planwork", "ip_lookup"):
      src_col = col_cfg.get("build_at", col_cfg.get("paste_to"))
  elif col_type == "copy":
      src_col = col_cfg.get("source_col", col_cfg.get("paste_to"))
  else:
      src_col = col_cfg.get("paste_to")
  
  dst_col = col_cfg.get("paste_to")
  src_idx = col_letter_to_index(src_col)
  dst_idx = col_letter_to_index(dst_col)
  ```

  **Result**: Source file is never modified during paste. All reads come from original source columns.

  **REFACTOR**: Verify all tests pass. Remove `copy_column` import from copier.py if no longer used.

  **QA**:
  ```
  Scenario: All tests pass, source stays pristine
    Tool: Bash
    Steps: cd 3-column-copier && python -m pytest tests/ -v
    Expected: 24+ passed, 0 failed
  ```

  **Commit**: `feat(copier): paste directly source→target, add build_at for temp columns`

- [x] 2. **Update config.json with build_at mapping**

  **What to do**:
  ```json
  "PW": {
      "type": "planwork",
      "build_at": "Q",
      "paste_to": "J"
  },
  "IP1": {
      "type": "ip_lookup",
      "lookup_col": "C",
      "log_sheet": "Get Log Before&After",
      "build_at": "R",
      "paste_to": "E"
  },
  "IP2": {
      "type": "ip_lookup",
      "lookup_col": "G",
      "log_sheet": "Get Log Before&After",
      "build_at": "S",
      "paste_to": "H"
  },
  "PORT_NO1": { "type": "copy", "source_col": "D", "paste_to": "F" },
  "NE_NO1": { "type": "copy", "source_col": "C", "paste_to": "D" },
  "L1": { "type": "copy", "source_col": "E", "paste_to": "C" },
  "NE_NO2": { "type": "copy", "source_col": "G", "paste_to": "G" },
  "PORT_NO2": { "type": "copy", "source_col": "H", "paste_to": "I" }
  ```

  **QA**:
  ```
  Scenario: Config loads valid JSON
    Tool: Bash
    Steps: cd 3-column-copier && python -c "import json; json.load(open('config.json')); print('OK')"
    Expected: OK
  ```

  **Commit**: `config(copier): add build_at keys for PW/IP safe temp columns`

- [x] 3. **E2E test with real column mapping + page break**

  **What to do**:
  - Create test data (from real-column-mapping-test plan):
    - Source: 20 rows with columns C, D, E, G, H populated
    - Target: content at row 30
  - Run: `python copier.py` with `page_break_enabled: true`
  - Verify output:
    - Col J = planwork number
    - Col E = IP addresses (from IP1 lookup, built at R)
    - Col H = IP addresses (from IP2 lookup, built at S)
    - Col D = NE_NO values (copied from C)
    - Col F = PORT_NO (copied from D)
    - Col C = L1 names (copied from E) ← NOT overwritten by IP1!
    - Col I = PORT_NO2 (copied from H)
    - Existing content pushed to clean page boundary

  **QA**:
  ```
  Scenario: Full pipeline with build_at — all columns correct
    Tool: Bash
    Steps: Run test script
    Expected: All 8 columns verify correctly, no data corruption
  ```

---

## Commit Strategy

| # | Commit Message | Files |
|---|---------------|-------|
| 1 | `feat(copier): add build_at config key for safe temp column placement` | `copier.py`, `tests/` |
| 2 | `config(copier): add build_at keys for PW/IP safe temp columns` | `config.json` |

---

## Success Criteria

```bash
cd 3-column-copier
python -m pytest tests/ -v         # Expected: 23+ passed
python copier.py                    # Expected: exit 0, all columns correct
```
