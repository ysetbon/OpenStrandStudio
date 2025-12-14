# Feature Request: MxN CAD "Continuing" Mode

## Overview

Add a new variant option called **"Continuing"** to `mxn_cad_ui.py` that extends the existing `mxn_lh_stretch` and `mxn_rh_stretch` patterns by creating additional strands (`_4` and `_5`) that connect endpoints based on **emoji pairing**.

---

## Current Architecture

The existing stretch generators (`mxn_lh_strech.py`, `mxn_rh_stretch.py`) create three strand types per set:
- **`_1` (Main strand)**: The primary diagonal strand
- **`_2` (Attached strand)**: Extends from one end of `_1`
- **`_3` (Attached strand)**: Extends from the opposite end of `_1`

Each strand has a **start point** and an **end point**. The CAD UI displays emoji markers at strand endpoints around the perimeter (controlled by rotation `k` and direction CW/CCW).

---

## New "Continuing" Behavior

### Strand `_4`
1. **Starting point**: The **ending point** of strand `_2`
2. **Ending point**: Determined by **emoji matching**:
   - Look at which emoji appears at `_4`'s starting point
   - Find the **other occurrence** of that same emoji elsewhere on the perimeter
   - That matching emoji's position becomes `_4`'s ending point

### Strand `_5`
1. **Starting point**: The **ending point** of strand `_3`
2. **Ending point**: Same emoji-matching logic as `_4`:
   - Look at the emoji at `_5`'s starting point
   - Find its matching pair on the perimeter
   - That position becomes `_5`'s ending point

---

## 1x1 Pattern Structure (Detailed Example)

For **1x1** (M=1, N=1):
- **Set 1** (Horizontal): `1_1`, `1_2`, `1_3`
- **Set 2** (Vertical): `2_1`, `2_2`, `2_3`

Each `_2` and `_3` strand has:
- **Start point**: Where it attaches to the main `_1` strand (inner)
- **End point**: Where it extends outward to the perimeter (outer)

---

## Geometry Diagram (1x1)

```
                         TOP EDGE
            +-------------------------------------+
            |                                     |
            |    2_3 start o-----------o 2_2 end  |
            |              \           /          |
            |               \         /           |
            |                \       /            |
   LEFT     |    1_2 end o----\-----/----o 1_2 start   RIGHT
   EDGE     |                  \   /              |    EDGE
            |                   \ /               |
            |                    X                |
            |                   / \               |
            |    1_3 start o--/-----\----o 1_3 end    |
            |                /       \            |
            |               /         \           |
            |              /           \          |
            |    2_2 start o-----------o 2_3 end  |
            |                                     |
            +-------------------------------------+
                        BOTTOM EDGE
```

### 8 Emoji Positions (2 per edge):

| Edge | Position 1 | Position 2 |
|------|------------|------------|
| **TOP** | `2_3` start (inner) | `2_2` end (outer) |
| **RIGHT** | `1_2` start (inner) | `1_3` end (outer) |
| **BOTTOM** | `2_2` start (inner) | `2_3` end (outer) |
| **LEFT** | `1_3` start (inner) | `1_2` end (outer) |

---

## Perimeter Order (Clockwise from Top-Left)

With 8 positions and **paired emojis** (each appears twice), we need **4 unique emojis**:

| Index | Location | Strand Endpoint |
|-------|----------|-----------------|
| 0 | Top-Left | `2_3` start |
| 1 | Top-Right | `2_2` end |
| 2 | Right-Top | `1_2` start |
| 3 | Right-Bottom | `1_3` end |
| 4 | Bottom-Right | `2_2` start |
| 5 | Bottom-Left | `2_3` end |
| 6 | Left-Bottom | `1_3` start |
| 7 | Left-Top | `1_2` end |

---

## Example 1: k=0 (No Rotation)

### Base Emoji Assignment

| Index | Position | Emoji |
|-------|----------|-------|
| 0 | Top-Left (`2_3` start) | Dog |
| 1 | Top-Right (`2_2` end) | Cat |
| 2 | Right-Top (`1_2` start) | Mouse |
| 3 | Right-Bottom (`1_3` end) | Hamster |
| 4 | Bottom-Right (`2_2` start) | Dog |
| 5 | Bottom-Left (`2_3` end) | Cat |
| 6 | Left-Bottom (`1_3` start) | Mouse |
| 7 | Left-Top (`1_2` end) | Hamster |

### Visual Diagram (k=0)

```
                            TOP EDGE
               +------------------------------------+
               |                                    |
               |      Dog             Cat           |
               |    (2_3 start)   (2_2 end)         |
               |         \           /              |
               |          \         /               |
               |           \       /                |
    LEFT       |  Hamster   \     /      Mouse      |  RIGHT
    EDGE       | (1_2 end)   \   /    (1_2 start)   |  EDGE
               |              \ /                   |
               |               X                    |
               |              / \                   |
               |  Mouse      /   \      Hamster     |
               | (1_3 start)/     \   (1_3 end)     |
               |           /       \                |
               |          /         \               |
               |      Dog             Cat           |
               |    (2_2 start)   (2_3 end)         |
               |                                    |
               +------------------------------------+
                          BOTTOM EDGE
```

### Emoji Pairs (k=0)

| Emoji | Appears At | Pair Connection |
|-------|------------|-----------------|
| Dog | Top-Left (`2_3` start) <-> Bottom-Right (`2_2` start) | Diagonal |
| Cat | Top-Right (`2_2` end) <-> Bottom-Left (`2_3` end) | Diagonal |
| Mouse | Right-Top (`1_2` start) <-> Left-Bottom (`1_3` start) | Diagonal |
| Hamster | Right-Bottom (`1_3` end) <-> Left-Top (`1_2` end) | Diagonal |

### Creating `_4` and `_5` Strands (k=0)

**`_4` strands** (start at `_2` end):

| Strand | Starts At | Emoji | Matching Emoji At | Ends At |
|--------|-----------|-------|-------------------|---------|
| `1_4` | `1_2` end (Left-Top) | Hamster | Right-Bottom (`1_3` end) | Right-Bottom |
| `2_4` | `2_2` end (Top-Right) | Cat | Bottom-Left (`2_3` end) | Bottom-Left |

**`_5` strands** (start at `_3` end):

| Strand | Starts At | Emoji | Matching Emoji At | Ends At |
|--------|-----------|-------|-------------------|---------|
| `1_5` | `1_3` end (Right-Bottom) | Hamster | Left-Top (`1_2` end) | Left-Top |
| `2_5` | `2_3` end (Bottom-Left) | Cat | Top-Right (`2_2` end) | Top-Right |

### Result Connections (k=0)

```
        1_4: Left-Top (Hamster) -----------------> Right-Bottom (Hamster)
        1_5: Right-Bottom (Hamster) <------------- Left-Top (Hamster)

        2_4: Top-Right (Cat) -----------------> Bottom-Left (Cat)
        2_5: Bottom-Left (Cat) <------------- Top-Right (Cat)
```

---

## Example 2: k=1 (Rotate 1 Position CW)

### Rotated Emoji Assignment

Each emoji shifts **1 position clockwise**:

| Index | Position | Original (k=0) | After k=1 |
|-------|----------|----------------|-----------|
| 0 | Top-Left (`2_3` start) | Dog | **Hamster** *(from index 7)* |
| 1 | Top-Right (`2_2` end) | Cat | **Dog** *(from index 0)* |
| 2 | Right-Top (`1_2` start) | Mouse | **Cat** *(from index 1)* |
| 3 | Right-Bottom (`1_3` end) | Hamster | **Mouse** *(from index 2)* |
| 4 | Bottom-Right (`2_2` start) | Dog | **Hamster** *(from index 3)* |
| 5 | Bottom-Left (`2_3` end) | Cat | **Dog** *(from index 4)* |
| 6 | Left-Bottom (`1_3` start) | Mouse | **Cat** *(from index 5)* |
| 7 | Left-Top (`1_2` end) | Hamster | **Mouse** *(from index 6)* |

### Visual Diagram (k=1)

```
                            TOP EDGE
               +------------------------------------+
               |                                    |
               |      Hamster         Dog           |
               |    (2_3 start)   (2_2 end)         |
               |         \           /              |
               |          \         /               |
               |           \       /                |
    LEFT       |  Mouse     \     /        Cat      |  RIGHT
    EDGE       | (1_2 end)   \   /    (1_2 start)   |  EDGE
               |              \ /                   |
               |               X                    |
               |              / \                   |
               |  Cat        /   \        Mouse     |
               | (1_3 start)/     \   (1_3 end)     |
               |           /       \                |
               |          /         \               |
               |      Hamster         Dog           |
               |    (2_2 start)   (2_3 end)         |
               |                                    |
               +------------------------------------+
                          BOTTOM EDGE
```

### Emoji Pairs (k=1) - DIFFERENT from k=0!

| Emoji | Appears At | Pair Connection |
|-------|------------|-----------------|
| Hamster | Top-Left (`2_3` start) <-> Bottom-Right (`2_2` start) | Diagonal |
| Dog | Top-Right (`2_2` end) <-> Bottom-Left (`2_3` end) | Diagonal |
| Cat | Right-Top (`1_2` start) <-> Left-Bottom (`1_3` start) | Diagonal |
| Mouse | Right-Bottom (`1_3` end) <-> Left-Top (`1_2` end) | Diagonal |

### Creating `_4` and `_5` Strands (k=1)

**`_4` strands** (start at `_2` end):

| Strand | Starts At | Emoji | Matching Emoji At | Ends At |
|--------|-----------|-------|-------------------|---------|
| `1_4` | `1_2` end (Left-Top) | Mouse | Right-Bottom (`1_3` end) | Right-Bottom |
| `2_4` | `2_2` end (Top-Right) | Dog | Bottom-Left (`2_3` end) | Bottom-Left |

**`_5` strands** (start at `_3` end):

| Strand | Starts At | Emoji | Matching Emoji At | Ends At |
|--------|-----------|-------|-------------------|---------|
| `1_5` | `1_3` end (Right-Bottom) | Mouse | Left-Top (`1_2` end) | Left-Top |
| `2_5` | `2_3` end (Bottom-Left) | Dog | Top-Right (`2_2` end) | Top-Right |

---

## Key Difference Between k=0 and k=1

| | k=0 | k=1 |
|---|-----|-----|
| `1_4` connects via | Hamster to Hamster | Mouse to Mouse |
| `2_4` connects via | Cat to Cat | Dog to Dog |
| **Geometric result** | Same diagonal paths | Same diagonal paths |

**Important insight**: For 1x1, the **geometric connections remain the same** (diagonal paths), but the **emoji labels that define those connections change**. This matters when the user wants to track which specific emoji pair is being connected.

In larger grids (2x2, 3x3), changing `k` would create **different geometric paths** because there are more endpoints and more possible pairings.

---

## Implementation Requirements

### 1. JSON Generator Logic

The "continuing" JSON creator must:

```
For each set (horizontal 1..n and vertical n+1..n+m):

    # Get existing _2 and _3 strand endpoints
    strand_2_end = get_endpoint("_2", "end")
    strand_3_end = get_endpoint("_3", "end")

    # Create _4 strand
    _4_start = strand_2_end
    _4_end = find_matching_emoji_point(_4_start, emoji_map, rotation_k)
    create_strand(_4_start, _4_end, set_number, "_4")

    # Create _5 strand
    _5_start = strand_3_end
    _5_end = find_matching_emoji_point(_5_start, emoji_map, rotation_k)
    create_strand(_5_start, _5_end, set_number, "_5")
```

### 2. Emoji Mapping Integration

The generator needs access to:
- **Current grid size** (MxN)
- **Emoji rotation value** (`k`) from the UI spinner
- **Direction** (CW/CCW) from the UI radio buttons

The emoji assignment follows a **perimeter ordering** (clockwise from top-left):
```
Top edge (left->right) -> Right edge (top->bottom) ->
Bottom edge (right->left) -> Left edge (bottom->top)
```

Each unique endpoint position gets an emoji. **Paired emojis** (same animal appearing twice) indicate connection points for the continuing strands.

### 3. Finding the Matching Emoji Point

```python
def find_matching_emoji_point(start_point, emoji_assignments, rotation_k):
    """
    Given a starting point, find where the matching emoji is located.

    1. Get the emoji assigned to start_point (after rotation k applied)
    2. Search all other endpoints for the same emoji
    3. Return that endpoint's coordinates
    """
    my_emoji = get_emoji_at_point(start_point, emoji_assignments)

    for point, emoji in emoji_assignments.items():
        if emoji == my_emoji and point != start_point:
            return point

    return None  # No match found
```

---

## UI Changes in `mxn_cad_ui.py`

### Variant Section Update

Add a "Continuing" checkbox or radio option under the Variant section:

```python
# In _setup_variant_section():
self.continuing_checkbox = QCheckBox("Continuing")
self.continuing_checkbox.stateChanged.connect(self._on_grid_size_changed)
layout.addWidget(self.continuing_checkbox)
```

### Generator Selection

```python
# In generate_and_preview():
if is_continuing:
    if is_lh:
        json_content = generate_lh_continuing_json(m, n, emoji_k, emoji_direction)
    else:
        json_content = generate_rh_continuing_json(m, n, emoji_k, emoji_direction)
```

---

## Data Flow Diagram

```
+------------------------------------------------------------------+
|                        CAD UI Settings                            |
|  MxN grid  |  LH/RH  |  Stretch  |  Continuing  |  Emoji k  |  CW/CCW |
+------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------+
|                   Continuing JSON Generator                       |
|                                                                   |
|  1. Generate base stretch pattern (_1, _2, _3 strands)           |
|  2. Compute perimeter emoji assignments (using k, direction)      |
|  3. For each _2 endpoint -> find matching emoji -> create _4      |
|  4. For each _3 endpoint -> find matching emoji -> create _5      |
+------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------+
|                      Output JSON Structure                        |
|                                                                   |
|  strands: [                                                       |
|    { layer_name: "1_1", ... },  // Main                          |
|    { layer_name: "1_2", ... },  // Attached                      |
|    { layer_name: "1_3", ... },  // Attached                      |
|    { layer_name: "1_4", ... },  // Continuing (NEW)              |
|    { layer_name: "1_5", ... },  // Continuing (NEW)              |
|    ...                                                            |
|  ]                                                                |
+------------------------------------------------------------------+
```

---

## Files to Create/Modify

1. **New files:**
   - `mxn_lh_continuing.py` - LH continuing generator
   - `mxn_rh_continuing.py` - RH continuing generator

2. **Modify:**
   - `mxn_cad_ui.py` - Add "Continuing" option and wire up new generators

---

## Key Considerations

1. **Emoji rotation must be consistent** - The same `k` value and direction used for display must be used in the generator to determine endpoint matching

2. **Handle edge cases** - What if no matching emoji is found? (Fall back to not creating `_4`/`_5` for that strand)

3. **Maintain strand ordering** - New `_4` and `_5` strands should be added after `_3` strands in the final list for proper layering

4. **MaskedStrand generation** - The continuing strands may need additional masked strand logic where they cross existing strands
