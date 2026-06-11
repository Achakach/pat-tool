# Append Mode for Column Copier

## TL;DR

> `paste_mode: "append"` → finds first blank row in target, pastes there. No overwrites.

## Config

```json
{
  "paste_mode": "append"
}
```

## Behavior

**`"overwrite"`** (current): paste at `paste_start_row`, overwrite whatever's there.

**`"append"`** (new): scan target column from `paste_start_row` downward, find first fully blank row, start pasting there.

## Implementation

### 3-column-copier/copier.py

After reading config, get mode:
```python
paste_mode = config.get("paste_mode", "overwrite")
```

When pasting to target, if `append` mode:
```python
if paste_mode == "append":
    paste_row = start_row
    max_row = tws.max_row + 100  # safety bound
    while paste_row < max_row:
        empty = True
        for c in range(1, tws.max_column + 1):
            if tws.cell(row=paste_row, column=c).value is not None:
                empty = False
                break
        if empty:
            break
        paste_row += 1
```

## TODOs

- [x] 1. Add paste_mode to config.json
- [x] 2. Add append logic to copier.py
- [x] 3. Test — multiple sources → same target, no overwrites
