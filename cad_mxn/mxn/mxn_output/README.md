# MxN Output Folder Structure

## Goal

Generate a complete library of all MxN strand patterns (from 1x1 to 10x10) with all valid k rotation values. Each pattern is exported in multiple formats:
- Base preview images with animal markers for visual reference
- Continuation patterns (_4, _5 strands) showing extended weaving
- Clean versions without markers for production use
- JSON data for programmatic loading into OpenStrandStudio

This provides a comprehensive reference set covering all possible LH (Left-Hand) and RH (Right-Hand) weaving configurations.

## File Naming Convention

Short format: `{type}_{m}x{n}_{k}_{dir}[_suffix].{ext}`

Examples:
- `lh_2x2_7_cw.png` - LH 2x2, k=7, clockwise, base preview
- `lh_2x2_-1_cw_45.png` - continuation with markers
- `lh_2x2_-1_cw_45_nm.png` - continuation no markers
- `lh_2x2_-1_cw_45.json` - continuation JSON

## K-Value Ranges

### Square Grids (m = n): 2m values from -(m-1) to m
| Grid | K Range | Count |
|------|---------|-------|
| 1x1 | 0 to 1 | 2 |
| 2x2 | -1 to 2 | 4 |
| 3x3 | -2 to 3 | 6 |
| 10x10 | -9 to 10 | 20 |

### Non-Square Grids (m != n): 2(m+n) values from -(m+n-1) to (m+n)
| Grid | K Range | Count |
|------|---------|-------|
| 1x2 | -2 to 3 | 6 |
| 2x3 | -4 to 5 | 10 |

## Pattern Rules
- **LH + m=n**: Direction = CW (clockwise)
- **RH + m=n**: Direction = CCW (counter-clockwise)
- **m != n**: Both LH and RH with both CW and CCW

## Files Per K Value
1. `{base}.png` - Preview with animal markers, white background
2. `{base}_45.png` - Continuation (_4,_5) with markers
3. `{base}_45_nm.png` - Continuation without markers
4. `{base}_45.json` - Continuation JSON data
