# Fix Image Splitting — One Page Per Site

## Problem

Images split across pages. `fitToHeight=0` doesn't contain them.

## Root Cause

`fitToHeight=0` → content flows freely. Tall image near page bottom → splits.

## Fix

`fitToHeight=1` + page breaks per site. Each site's content auto-scaled to one page.

```python
ws.page_setup.fitToHeight = 1  # was 0
```

## Result

| Before | After |
|--------|-------|
| Images spill across pages | Each site = 1 page |
| Manual row-counting needed | Excel auto-scales |

Page breaks per site already work. Only config change needed.

## TODOs

- [ ] 1. Change fitToHeight from 0 to 1 in _setup_a4_print
- [ ] 2. Test — each site on own page, no image splits
- [ ] 3. Verify in Print Preview

## Risk

Sites with many images → images scale smaller to fit. User can balance via `image_display_width`.
