# MxN sample stitches

Ready-to-open OpenStrandStudio documents (`.json`) and their pictures (`.png`) for the MxN stitch family. `m` counts vertical ribbons, `n` horizontal ones. Left hand (`lh`) and right hand (`rh`) each have their own folder, and every kind of sample has a `json/` and an `images/` folder of its own.

```
mxn_samples/
├── lh/
│   ├── starting/          every starting stitch, m and n from 1 to 8 (64)
│   ├── k1_start/          k = 1 starting stitch, before alignment (10)
│   ├── k1_continuation/   k = 1 aligned continuation (10)
│   └── k1_alignment/      k = 1 angles, gaps and extensions (json only, 10)
└── rh/                    same layout, mirrored hand
```

Each of `starting`, `k1_start`, `k1_continuation` holds `json/` and `images/`; `k1_alignment` holds `json/` only.

## Starting stitches (`starting/`)

`mxn_<hand>_<m>x<n>.json` for every `m` and `n` from 1 to 8, so both `2x3` and `3x2` are present. They come straight from the repo's generators (`mxn_lh.generate_json`, `mxn_rh.generate_json` in [ysetbon/mxn](https://github.com/ysetbon/mxn)), colours as generated.

## k = 1 set (`k1_*`)

The k = 1 twist stitches already published in mxn under `src/mxn_k1` (branch `cursor/k1-stitch-json-3cb7`), copied as they were, not regenerated. They cover `m ≤ n` with both from 1 to 4 (`2x1` is the same stitch as `1x2`), 10 sizes per hand.

- `k1_start/` — `mxn_<hand>_<m>x<n>_k1_start.json`, the starting stitch with its raw continuation, before alignment.
- `k1_continuation/` — `mxn_<hand>_<m>x<n>_k1_continuation.json`, the aligned continuation. The left-hand `1x4` also has `..._continuation_before_reaim`, the earlier straight 90° vertical arm, next to the re-aimed 103.5° one.
- `k1_alignment/` — `mxn_<hand>_<m>x<n>_k1_alignment.json`, the alignment result for that size.

## Images

PNGs are drawn from the JSON by the mxn repo's `src/oss_svg.py`, a port of OpenStrandStudio's strand, attached-strand and mask drawing, on a white background, one pixel per document unit. They use each file's own colours.
