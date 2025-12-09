# MXN Starting Patterns - JSON Generation Documentation

This document explains how the `mxn_lh.py` (Left-Hand) and `mxn_rh.py` (Right-Hand) scripts generate OpenStrandStudio JSON files for MxN crossing patterns.

## Overview

The MXN pattern represents a grid of interwoven strands:
- **M** = number of vertical strands
- **N** = number of horizontal strands
- **LH** = Left-Hand variant (gap = +42)
- **RH** = Right-Hand variant (gap = -42)

## Visual Representation

### 1x1 Pattern (Simplest Case)

```
        LH (Left-Hand)                           RH (Right-Hand)
        gap = +42                                gap = -42
        (V slants \)                             (V slants /)

            2_2                                      2_2
             O                                        O
             |                                        |
    1_3 O----+----O 1_2                     1_3 O----+----O 1_2
             |                                        |
             O                                        O
            2_3                                      2_3

    At crossing:                             At crossing:
    - Vertical (2_2) goes OVER H             - Vertical (2_2) goes OVER H
    - Vertical slants \ (Top-Left)           - Vertical slants / (Top-Right)
```

### Detailed 1x1 ASCII Diagram

```
    LH Pattern (gap=+42)                    RH Pattern (gap=-42)

          2_3 (up)                               2_2 (up)
            O                                      O
            ║                                      ║
            ║                                      ║
   1_3 O════╬════O 1_2                    1_3 O════╬════O 1_2
            ║    (H over V)                        ║    (H over V)
            ║                                      ║
            O                                      O
          2_2 (down)                             2_3 (down)

    In LH: Upper vertical tail (2_3)
           Lower vertical tail (2_2)

    In RH: Upper vertical tail (2_2)
           Lower vertical tail (2_3)

    Legend:
    O = rounded end (circle)
    ═ = horizontal strand segment (ON TOP at crossing)
    ║ = vertical strand segment (BEHIND at crossing)
    ╬ = crossing point

    Strand naming:
    2_1 = Vertical main strand (set 2, strand 1) - the central crossing area
    2_2 = Vertical attached strand going UP (Attached at Top)
    2_3 = Vertical attached strand going DOWN (Attached at Bottom)
    1_1 = Horizontal main strand (set 1, strand 1) - the central crossing area
    1_2 = Horizontal attached strand going LEFT (Attached at Right, Circle at Right)
    1_3 = Horizontal attached strand going RIGHT (Attached at Left, Circle at Left)
```

## Strand Types

### 1. Main Strand (`_1`)
```
    type: "Strand"
    has_circles: [true, true]  (circles at both ends)

         O------------------O
       start               end
       (circle)          (circle)
```

### 2. Attached Strand (`_2` and `_3`)
```
    type: "AttachedStrand"
    has_circles: [true, false]  (circle only at attachment point)

         O------------------x
       start               end
    (attachment)        (no circle)
```

### 3. Masked Strand (Crossings)
```
    type: "MaskedStrand"
    has_circles: [false, false]  (no circles)

    Created when vertical tail crosses horizontal tail
    Examples: "2_2_1_3" (vertical 2_2 masked by horizontal 1_3)
    
    The MaskedStrand is created from the VERTICAL strand properties,
    placing the Vertical strand ON TOP of the Horizontal strand.
```

## Grid Layout Algorithm

### Coordinate System
```
    center_x = 1274.0
    center_y = 434.0
    stride = 168.0 (spacing between parallel strands)
    gap = +/-42 (offset for over/under crossing)
    grid_unit = 42.0
```

### 2x1 Pattern Layout (2 vertical, 1 horizontal)
```
    LH Pattern:

        V1 (set 2)      V2 (set 3)
           O               O
           ║               ║
           ║               ║
    O══════╬═══════════════╬══════O    H1 (set 1, white)
           ║               ║
           ║               ║
           O               O

    - 2 vertical strands (green shades)
    - 1 horizontal strand (white)
    - Each vertical crosses the horizontal
```

### 1x2 Pattern Layout (1 vertical, 2 horizontal)
```
    LH Pattern:

                O
                ║
        O═══════╬═══════O    H1 (set 1, white)
                ║
        O═══════╬═══════O    H2 (set 2, green)
                ║
                O
           V1 (set 3, blue)

    - 1 vertical strand
    - 2 horizontal strands
    - The vertical weaves through both horizontals
```

### 2x2 Pattern Layout
```
    LH Pattern:

        V1 (set 3)      V2 (set 4)
           O               O
           ║               ║
    O══════╬═══════════════╬══════O    H1 (set 1, white)
           ║               ║
    O══════╬═══════════════╬══════O    H2 (set 2, green)
           ║               ║
           O               O

    Weave pattern:
    - Verticals go OVER Horizontals at intersections.
    
    Set numbers:
    - Horizontals: 1 to n (sets 1, 2)
    - Verticals: n+1 to n+m (sets 3, 4)
```

### 3x3 Pattern Layout
```
    LH Pattern:

      V1 (set 4)    V2 (set 5)    V3 (set 6)
         O             O             O
         ║             ║             ║
    O════╬═════════════╬═════════════╬════O    H1 (set 1)
         ║             ║             ║
    O════╬═════════════╬═════════════╬════O    H2 (set 2)
         ║             ║             ║
    O════╬═════════════╬═════════════╬════O    H3 (set 3)
         ║             ║             ║
         O             O             O

    Set numbers:
    - Horizontals: 1 to n (sets 1, 2, 3)
    - Verticals: n+1 to n+m (sets 4, 5, 6)
```

## JSON Generation Flow

```
                    +------------------+
                    |  Input: m x n    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
    +---------v----------+       +----------v---------+
    |  Create Verticals  |       |  Create Horizontals |
    |  (Sets n+1...n+m)  |       |  (Sets 1...n)       |
    +--------+-----------+       +----------+----------+
              |                             |
              |   For each vertical:        |   For each horizontal:
              |   - Main strand (_1)        |   - Main strand (_1)
              |   - Attached up (_2)        |   - Attached left (_3) (Circle Left)
              |   - Attached down (_3)      |   - Attached right (_2) (Circle Right)
              |                             |
              +--------------+--------------+
                             |
                    +--------v---------+
                    | Combine strands  |
                    | strands_1 + _2   |
                    |   + strands_3    |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Re-index all    |
                    |  strand indices  |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Generate Masked |
                    |  Strands for     |
                    |  crossings       |
                    | (V over H)       |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Add Shadow      |
                    |  Overrides       |
                    |  (1x1 only)      |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Create History  |
                    |  with 3 states   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Output JSON     |
                    +------------------+
```

## Masking Logic

The natural drawing order (from list order) is **Horizontal Over Vertical** (since Horizontals are added to the list after Verticals).

Masking creates specific **Vertical Over Horizontal** crossings by creating a `MaskedStrand` (a copy of the Vertical strand) that is placed at the end of the list, drawing it on top.

### LH (Left-Hand) - Positive Gap
```
    Vertical Orientation:
    - _3 is Top (starts at Top)
    - _2 is Bottom (starts at Bottom)
    
    Horizontal Orientation:
    - _3 is Left
    - _2 is Right

    Masked when (V tail overlaps H tail):
    - Vertical _2 (Bottom) crosses Horizontal _3 (Left)
    - Vertical _3 (Top) crosses Horizontal _2 (Right)

    Result: V is forced OVER H at these diagonal opposites (Bottom-Left, Top-Right).
```

### RH (Right-Hand) - Negative Gap
```
    Vertical Orientation:
    - _2 is Top
    - _3 is Bottom

    Horizontal Orientation:
    - _3 is Left
    - _2 is Right

    Masked when:
    - Vertical _2 (Top) crosses Horizontal _3 (Left)
    - Vertical _3 (Bottom) crosses Horizontal _2 (Right)

    Result: V is forced OVER H at these diagonal opposites (Top-Left, Bottom-Right).
```

## Strand Coordinate Calculation

### Vertical Strands
```python
    # Center X position (distributed across m columns)
    cx = center_x + (i - (m-1)/2) * stride

    # Start point (bottom)
    start_pt = {"x": cx + gap, "y": start_y}

    # End point (top)
    end_pt = {"x": cx - gap, "y": end_y}

    # The gap creates the diagonal slant:
    #   LH (gap=+42):  start.x (Right) > end.x (Left) -> Slants Top-Left (\)
    #   RH (gap=-42):  start.x (Left) < end.x (Right) -> Slants Top-Right (/)
```

### Horizontal Strands
```python
    # Center Y position (distributed across n rows)
    cy = center_y + (i - (n-1)/2) * stride

    # Start point (left)
    start_pt = {"x": center_x - base_half_w, "y": cy + gap}

    # End point (right)
    end_pt = {"x": center_x + base_half_w, "y": cy - gap}

    # The gap creates the diagonal slant:
    #   LH (gap=+42):  start.y (Low/Big) > end.y (High/Small) -> Slants Up (/)
    #   RH (gap=-42):  start.y (High/Small) < end.y (Low/Big) -> Slants Down (\)
```

## Visual: LH vs RH Crossing Direction

```
    LH (gap = +42)                      RH (gap = -42)

         ║                                   ║
         ║  V goes                           ║  V goes
         ║  OVER H                           ║  OVER H
    ═════╬═════                         ═════╬═════
         ║                                   ║
         ║                                   ║

    In both cases, Vertical is in front (MaskedStrand from V).
    
    Slant Difference:
    LH: V = \ , H = /
    RH: V = / , H = \
```

### Complete 1x1 Weave Visualization

```
    LH Pattern (+42)                        RH Pattern (-42)
    V Slant: \                              V Slant: /
    H Slant: /                              H Slant: \

         2_3 (Top-Left)                          2_2 (Top-Right)
          O                                       O
           \                                     /
            \  (H is Over)                      /  (H is Over)
             \                                 /
   1_3 O------╳------O 1_2             1_3 O------╳------O 1_2
  (Low-Left) /      (High-Right)      (High-Left) \      (Low-Right)
            /                                      \
           /                                        \
          O                                          O
        2_2 (Bottom-Right)                         2_3 (Bottom-Left)

    Legend:
    ╳ = crossing point (Horizontal strand is ON TOP at center)
    \ / = Strand segments
```

## File Output Structure

```
mxn_startings/
├── mxn_lh.py                 # Left-hand generator
├── mxn_rh.py                 # Right-hand generator
├── mxn_lh/                   # LH output folder
│   ├── mxn_lh_1x1.json
│   ├── mxn_lh_1x2.json
│   ├── mxn_lh_1x3.json
│   ├── mxn_lh_2x1.json
│   ├── mxn_lh_2x2.json
│   ├── mxn_lh_2x3.json
│   ├── mxn_lh_3x1.json
│   ├── mxn_lh_3x2.json
│   └── mxn_lh_3x3.json
└── mxn_rh/                   # RH output folder
    ├── mxn_rh_1x1.json
    ├── mxn_rh_1x2.json
    ├── mxn_rh_1x3.json
    ├── mxn_rh_2x1.json
    ├── mxn_rh_2x2.json
    ├── mxn_rh_2x3.json
    ├── mxn_rh_3x1.json
    ├── mxn_rh_3x2.json
    └── mxn_rh_3x3.json
```

## JSON Structure Overview

```json
{
  "type": "OpenStrandStudioHistory",
  "version": 1,
  "current_step": 3,
  "max_step": 3,
  "states": [
    {
      "step": 1,
      "data": {
        "strands": [...],           // Array of strand objects
        "groups": {},
        "selected_strand_name": null,
        "locked_layers": [],
        "lock_mode": false,
        "shadow_enabled": false,
        "show_control_points": true,  // Step 1 shows control points
        "shadow_overrides": {...}
      }
    },
    { "step": 2, "data": {...} },    // show_control_points: false
    { "step": 3, "data": {...} }     // show_control_points: false
  ]
}
```

## Strand Object Structure

```json
{
  "type": "Strand|AttachedStrand|MaskedStrand",
  "index": 0,
  "start": {"x": 1316.0, "y": 532.0},
  "end": {"x": 1232.0, "y": 336.0},
  "width": 46,
  "color": {"r": 85, "g": 170, "b": 0, "a": 255},
  "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
  "stroke_width": 4,
  "has_circles": [true, true],
  "layer_name": "2_1",
  "set_number": 2,
  "is_first_strand": true,
  "attached_to": null,           // For AttachedStrand: parent layer
  "attachment_side": null        // 0=start, 1=end of parent
}
```

## Color Scheme

```
Set 1 (First horizontal):  White   RGB(255, 255, 255)
Set 2 (First vertical):    Green   RGB(85, 170, 0)
Set 3+ (Others):           Random  HSL-based random colors
```

## Usage

```bash
# Generate LH patterns
python mxn_lh.py

# Generate RH patterns
python mxn_rh.py
```

Both scripts generate 9 JSON files (1x1 through 3x3) in their respective output folders.
