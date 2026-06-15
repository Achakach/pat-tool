# Compact Visual Layout

## Problem

Labels correctly positioned (row 55, 109, 163) but visual spacing feels loose. Image heights create large gaps.

## Fix

Tighter config:

```json
"image_display_width": 200,
"insert_gap_rows": 0
```

Smaller images + no gaps = denser pages. Labels stay at same position.

## Result

```
Page 1: SITE03 label + image (compact)
Page 2: SITE04 label + image (compact)
Page 3: SITE05 label + image (compact)
```

## TODOs

- [ ] 1. Set image_display_width to 200
- [ ] 2. Set insert_gap_rows to 0
- [ ] 3. Test + Print Preview
