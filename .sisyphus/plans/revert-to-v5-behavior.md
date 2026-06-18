# Revert to V5 Behavior (Keep Multi-Source + Insert Decouple)

## TL;DR

> **Quick Summary**: Restore blank scan, merged skip, and paste_mode config that were removed in `simplify-insert-logic`. Keep multi-source append and insert_mode decoupling.
>
> **Deliverables**:
> - `copier.py`: restore 4 code blocks, keep insert_mode OR condition + output check
> - `config.json`: restore `paste_mode` key
> - Test configs: restore `paste_mode`
>
> **Estimated Effort**: Quick (re-add removed code)
> **Critical Path**: copier.py → config → tests

---

## Context

`simplify-insert-logic` (commit `7f49970`) removed blank scan, merged skip, and paste_mode. User wants those back. BUT keep: insert_mode decoupling (commit `a45a295`) and multi-source append (commit `73cede2`).

## What Gets Restored vs Kept

| Feature | In V5 | Removed by simplify | RESTORE? | Keep from latest? |
|---------|-------|---------------------|----------|-------------------|
| `paste_mode` config read | ✅ | Yes | **RESTORE** | - |
| Blank row scan | ✅ | Yes | **RESTORE** | - |
| Merged cell check+skip | ✅ | Yes | **RESTORE** | - |
| `dst_row` conditional | ✅ | Yes | **RESTORE** | - |
| Multi-source append | ❌ | No | - | **KEEP** |
| `insert_mode` (OR gate) | ❌ | No | - | **KEEP** |
| Image anchor shift | ❌ | No | - | **KEEP** (TBD) |

## Final Behavior

```
1. paste_mode = config.get("paste_mode", "overwrite")
2. Blank scan: find first empty row → paste_row
3. Gate: paste_mode=="append" AND (page_break_enabled OR insert_mode)
4. Merged check: if overlap → WARNING + skip
5. dst_row = paste_row if paste_mode=="append" else min(start_row, paste_row)
6. Multi-source: check output folder, load existing if present
```

---

## TODOs

- [x] 1. Restore paste_mode + blank scan + merged skip + dst_row to copier.py
- [x] 2. Restore paste_mode to config.json
- [x] 3. Restore paste_mode to test configs
- [x] 4. Run full test suite — 41 pass

---

## Final Verification Wave

- [x] F1. Full test suite passes
- [x] F2. grep "paste_mode" copier.py → found
- [x] F3. grep "blank row" copier.py → found
- [x] F4. grep "has_merged" copier.py → found

---

## Commit Strategy

- **1**: `revert: restore V5 blank scan, merged skip, paste_mode`
  - Files: `copier.py`, `config.json`, test files
