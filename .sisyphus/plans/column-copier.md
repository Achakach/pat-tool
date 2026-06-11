# Column Copier Tool

## TL;DR

Create temp columns (PW, IP) + copy columns from source → target XLSX. Matching by PW value.

## Config

```json
{
  "matching_file": "../matching.xlsx",
  "matching_sheet": "match",
  "filename_col": "Site",
  "planwork_col": "PW Number",
  "data_sheet": "cutsheet",
  "target_sheet": "IP & Port Assignment",
  "source_start_row": 3,
  "paste_start_row": 3,
  "columns": {
    "PW": {
      "type": "planwork",
      "paste_to": "Q"
    },
    "IP1": {
      "type": "ip_lookup",
      "lookup_col": "C",
      "log_sheet": "Get Log Before&After",
      "paste_to": "R"
    },
    "IP2": {
      "type": "ip_lookup",
      "lookup_col": "D",
      "log_sheet": "Get Log Before&After",
      "paste_to": "S"
    },
    "NE_NO_1": {
      "type": "copy",
      "source_col": "C",
      "paste_to": "C"
    },
    "NE_NO_2": {
      "type": "copy",
      "source_col": "D",
      "paste_to": "D"
    }
  },
  "source_folder": "./source",
  "target_folder": "./target",
  "output_folder": "./output",
  "action": "copy"
}
```

## Flow (action: "copy")

1. Read matching.xlsx → `{PW Number → Site}` map
2. For each source XLSX in source_folder:
   - Find `PW {planwork}` sheet → extract planwork
   - Create PW column (planwork), fill every row
   - Create IP column (lookup from log sheet), fill every row
3. Read PW column value → lookup in matching map → get target filename
4. Open target XLSX in target_folder
5. Copy PW, IP, NE_NO_1, NE_NO_2, etc. to paste_to positions
6. Save to output_folder

## Flow (action: "cleanup")

1. Delete PW and IP columns from source files in output_folder
2. Target files untouched

## Column Types

| type | Does |
|------|------|
| `"planwork"` | PW sheet name → fill column |
| `"ip_lookup"` | Read lookup_col → find in log sheet row 1 → extract IP |
| `"copy"` | Direct copy source_col → paste_to |

## TODOs

- [x] 1. Create `5-column-copier/` folder structure
- [x] 2. Column builder module (PW + IP + copy)
- [x] 3. CLI + matching + cleanup
- [x] 4. Tests + verify
