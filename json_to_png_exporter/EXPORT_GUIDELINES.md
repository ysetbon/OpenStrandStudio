# OpenStrand Studio Export Guidelines

## Overview
This document outlines the correct settings and conventions for exporting OpenStrand Studio JSON files to high-quality PNG images.

## Essential Export Settings

### 1. Canvas Display Settings
When exporting to images, ensure these canvas settings:
- **`show_control_points`**: Set based on design needs
  - `true` - Shows control points, control lines, and selection rectangles
  - `false` - Clean export showing only the strands
- **`shadow_enabled`**: Usually `true` for professional appearance
- **`show_grid`**: Always `false` for exports
- **Mode**: Must be in **Select Mode** (not Attach Mode) to avoid attachment indicators

### 2. Control Points Configuration

#### Number of Control Points
- **2 control points**: Standard curves (U-shapes, simple arcs)
  - Creates cubic Bézier curve: `B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃`
  - P₀ = start point, P₁ = control_points[0], P₂ = control_points[1], P₃ = end point

- **3 control points**: Complex curves (S-shapes, serpentine paths)
  - Creates two connected cubic Bézier segments
  - Middle control point (control_point_center) creates inflection point
  - Enabled when `control_point_center` is defined in strand data

#### Control Point Center
- **`control_point_center`**: Defines the third control point for complex curves
- **`control_point_center_locked`**: 
  - `true` - Maintains symmetry when adjusting control points
  - `false` - Allows independent control point manipulation

### 3. Color Conventions

#### Layer Naming and Strand Types
**CRITICAL RULES**: 
1. All strands in the same set must use the same color!
2. **STRAND TYPE CONVENTION**:
   - `x_1` (e.g., `1_1`, `2_1`, `3_1`) = Main Strand (type: "Strand")
   - `x_y` where y ≠ 1 (e.g., `1_2`, `1_3`, `2_2`) = AttachedStrand (type: "AttachedStrand")

**IMPORTANT FOR AttachedStrands**:
- MUST have `type: "AttachedStrand"`
- MUST have `attached_to` field (parent strand layer_name)
- MUST have `attachment_side` (0=start of parent, 1=end of parent)
- MUST have `angle` (degrees from parent's end)
- MUST have `length` (length of the attached strand)
- **STILL MUST HAVE `start` and `end` coordinates** (calculated from parent position + angle + length)
- Can be chained: 1_3 can attach to 1_2, which attaches to 1_1

Examples:
- `1_1` → Main Strand (blue) with start/end coordinates
- `1_2` → AttachedStrand to `1_1` (same blue) with start/end AND attachment info
- `1_3` → AttachedStrand to `1_2` (same blue) forming a chain
- `2_1` → Main Strand (red)
- `2_2` → AttachedStrand to `2_1` (same red)

```json
// Correct structure with AttachedStrand - COMPLETE EXAMPLE
"strands": [
  {
    "type": "Strand",  // Main strand
    "layer_name": "1_1",
    "color": {"r": 100, "g": 150, "b": 255, "a": 255},  // Blue
    "start": {"x": 100.0, "y": 100.0},
    "end": {"x": 200.0, "y": 200.0},
    "width": 46.0,
    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
    "stroke_width": 4.5,
    "control_points": [{"x": 150.0, "y": 120.0}, {"x": 180.0, "y": 180.0}],
    ...
  },
  {
    "type": "AttachedStrand",  // MUST be AttachedStrand for x_2, x_3, etc.
    "layer_name": "1_2", 
    "color": {"r": 100, "g": 150, "b": 255, "a": 255},  // MUST be same blue
    "attached_to": "1_1",  // Parent strand layer_name
    "attachment_side": 1,  // 0=start of parent, 1=end of parent
    "angle": 45.0,  // Angle in degrees from parent's end
    "length": 100.0,  // Length of this attached strand
    "start": {"x": 200.0, "y": 200.0},  // REQUIRED: Calculated from parent's end
    "end": {"x": 270.7, "y": 270.7},    // REQUIRED: Calculated using angle & length
    "width": 46.0,
    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
    "stroke_width": 4.5,
    ...
  }
]
```

### 4. Strand Properties

#### Essential Properties
- **`width`**: Strand thickness (typically 46.0)
- **`stroke_width`**: Outline thickness (typically 4.5)
- **`stroke_color`**: Usually black `{"r": 0, "g": 0, "b": 0, "a": 255}`
- **`has_circles`**: `[start_circle, end_circle]` - Shows circles at endpoints
- **`shadow_only`**: Must be `false` for normal strands

#### Line Visibility Settings for Clean Export
- **`start_line_visible`**: Set to `true` (shows side line at start)
- **`end_line_visible`**: Set to `true` (shows side line at end)
- **`start_extension_visible`**: Set to `false` (NO extension dashes at start)
- **`end_extension_visible`**: Set to `false` (NO extension dashes at end)
- **`start_arrow_visible`**: Set to `false` (no arrow at start)
- **`end_arrow_visible`**: Set to `false` (no arrow at end)

#### Connections
- **`closed_connections`**: `[start_closed, end_closed]` - Indicates if endpoints are connected
- **`knot_connections`**: Defines connections to other strands

### 5. Image Export Requirements

#### Canvas Bounds Calculation
- Include all strand endpoints and control points
- Add padding for stroke width: `strand.width/2 + stroke_width*2`
- Consider circles at endpoints if enabled
- Include shadow offset if shadows are enabled

#### Padding and Cropping
- **Content padding**: 200px minimum around all content
- **Final padding**: 30px after cropping to content
- **Never crop**: Control points, stroke outlines, or shadows
- **Preserve aspect ratio**: Don't force square unless required

#### Background
- Default: White background `(255, 255, 255, 255)`
- Optional: Transparent background for overlays

### 6. Export Process Checklist

1. **Load JSON file**
   - Handle both regular JSON and history format
   - Apply all strand properties correctly

2. **Configure canvas**
   - Set to Select Mode (not Attach Mode)
   - Apply show_control_points setting from JSON
   - Enable third control point if control_point_center exists
   - Reset zoom (1.0) and pan (0, 0)

3. **Validate strands**
   - Check color consistency within sets
   - Verify all connections are properly defined
   - Ensure control points are within reasonable bounds

4. **Calculate bounds**
   - Get bounding rect of all strands
   - Include stroke width and circles
   - Add generous padding (200px)

5. **Render image**
   - Use high-quality antialiasing
   - Render at 1:1 scale (zoom = 1.0)
   - Capture all visual elements

6. **Save image**
   - Crop conservatively to preserve all content
   - Add final padding (30px)
   - Save as PNG with full quality

## Common Issues and Solutions

### Issue: Control points not visible
**Solution**: Ensure `show_control_points: true` in JSON and `canvas.enable_third_control_point = True` if using 3 control points

### Issue: Strands in same set have different colors
**Solution**: Update all strands with same prefix (e.g., 1_x) to use identical color values

### Issue: Parts of image are cropped
**Solution**: Increase padding in bounds calculation and use conservative cropping

### Issue: Attach mode indicators visible
**Solution**: Explicitly set `canvas.current_mode = canvas.select_mode` before rendering

### Issue: S-shape not forming correctly
**Solution**: For S-shapes with 2 control points, place them on opposite sides of start/end points

## Example: Correct S-Shape Configuration

```json
{
  "strands": [{
    "type": "Strand",
    "layer_name": "1_1",
    "start": {"x": 800.0, "y": 100.0},
    "end": {"x": 500.0, "y": 600.0},
    "color": {"r": 100, "g": 150, "b": 255, "a": 255},
    "control_points": [
      {"x": 200.0, "y": 100.0},  // Left of start
      {"x": 1400.0, "y": 600.0}  // Right of end
    ],
    "control_point_center": {"x": 650.0, "y": 350.0},
    "control_point_center_locked": true
  }],
  "show_control_points": true,
  "shadow_enabled": true
}
```

## Python Export Script Usage

```python
# Use the export_json_properly.py script
python export_json_properly.py

# The script will:
# 1. Load JSON files from src/documentation/
# 2. Apply all correct settings automatically
# 3. Export high-quality PNG images
# 4. Report bounds and settings used
```

## Quality Assurance

Before finalizing exports, verify:
- [ ] All strands in same set have identical colors
- [ ] Control points visible if intended
- [ ] No cropping of strand elements
- [ ] Shadows rendered if enabled
- [ ] No attach mode indicators
- [ ] Proper connections at strand endpoints
- [ ] Clean white or transparent background
- [ ] Image properly centered with padding

---

*Last Updated: 2024*
*For OpenStrand Studio v1.0+*