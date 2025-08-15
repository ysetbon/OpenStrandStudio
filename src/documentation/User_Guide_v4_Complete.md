# OpenStrand Studio - Complete User Manual (Version 4.0 - Master Reference)
**Application Version: 1.101**

## Table of Contents
1. [Quick Reference Guide](#quick-reference-guide)
2. [Complete Feature Reference](#complete-feature-reference)
3. [Keyboard Shortcuts & Power User Tips](#keyboard-shortcuts--power-user-tips)
4. [Settings Deep Dive](#settings-deep-dive)
5. [File Format Specifications](#file-format-specifications)
6. [Integration with Other Tools](#integration-with-other-tools)
7. [Performance Optimization Guide](#performance-optimization-guide)
8. [Accessibility Features](#accessibility-features)
9. [Troubleshooting Encyclopedia](#troubleshooting-encyclopedia)
10. [Expert Tips & Hidden Features](#expert-tips--hidden-features)

## Quick Reference Guide

### Essential Toolbar Quick Reference
| Button | Mode | Function | Best Used For |
|--------|------|----------|---------------|
| 🔗 | Attach | Create new strands | Starting any project, adding new elements |
| ➤ | Move | Reposition & adjust curves | Fine-tuning positions, adjusting shapes |
| 🔄 | Rotate | Rotate strands around center | Changing orientation, creating symmetry |
| 📐 | Angle/Length | Precise numerical control | Technical precision, exact measurements |
| 👆 | Select | Choose strands & access properties | Color changes, detailed modifications |
| 🎭 | Mask | Create over/under effects | Making realistic knots, crossing effects |
| ⊞ | Grid | Toggle alignment grid | Professional layouts, precise alignment |
| 💾 | Save | Save project file | Preserving work, creating checkpoints |
| 📁 | Load | Open existing project | Starting from templates, continuing work |
| 🖼️ | Image | Export as picture | Sharing, printing, publishing |
| ⚙️ | Settings | Access all preferences | Customization, tutorials, samples |

### Common Task Quick Steps

**Create a Basic Knot (30 seconds):**
1. Attach → Draw loop → Move → Adjust shape → Mask → Create crossing
2. Save → Name it → Done

**Change Colors:**
1. Select → Click strand → Look for color options → Choose new colors

**Perfect Alignment:**
1. Grid → Turn on → Attach/Move → Use snap points → Grid → Turn off

**Fix Mistakes:**
1. Press Undo (↶) → Or use layer panel to select problem strand → Delete or adjust

## Complete Feature Reference

### Drawing Modes Detailed

#### Attach Mode - The Foundation Tool
**What it does:** Creates new strand paths from scratch
**How it works:** 
- Click and drag to set start and end points
- Automatic curve calculation based on drag distance and direction
- Creates new layer automatically
- Each strand gets unique layer number

**Advanced techniques:**
- **Quick curves:** Short drags = gentle curves, long drags = pronounced curves
- **Direction matters:** Drag direction influences initial curve direction
- **Multiple segments:** Create complex paths by drawing multiple connected strands
- **Precision start:** Click precise start point, then drag to end

**Best practices:**
- Plan your strand path before starting to draw
- Use consistent drag lengths for similar curve styles
- Start with main structural elements, add details later

#### Move Mode - The Adjustment Tool
**What it does:** Repositions strands and adjusts their curves
**Three types of movement:**
1. **Strand movement:** Click strand body, drag to new position
2. **Endpoint movement:** Click endpoint, drag to new location  
3. **Control point adjustment:** Click control point, drag to change curve

**Control point behavior:**
- **Two main control points:** Adjust the overall curve shape
- **Center control point:** Available when enabled in settings
- **Linked behavior:** Moving endpoints automatically adjusts control points
- **Independent adjustment:** Control points can be moved independently for precise curves

**Advanced adjustment techniques:**
- **Proportional scaling:** Hold Shift while dragging to maintain proportions
- **Constrained movement:** Hold Alt for horizontal/vertical constraints
- **Fine adjustment:** Zoom in for pixel-level precision
- **Multi-strand selection:** Select multiple strands for group movement

#### Rotate Mode - The Orientation Tool
**What it does:** Rotates strands around their geometric center
**Rotation behavior:**
- **Center calculation:** Automatic center point between start and end
- **Angle feedback:** Visual indication of rotation amount
- **Control point handling:** Control points rotate with the strand
- **Multi-strand rotation:** Can rotate groups of selected strands

**Professional rotation techniques:**
- **Snap angles:** Use common angles (45°, 90°, etc.) for professional look
- **Reference alignment:** Rotate to align with grid or other elements
- **Symmetry creation:** Rotate copies for symmetrical patterns
- **Fine tuning:** Small rotations (5-10°) for natural variation

#### Angle/Length Mode - The Precision Tool
**What it does:** Provides numerical control over strand dimensions and orientation
**Measurement system:**
- **Angle measurement:** Degrees from horizontal (0° = horizontal right)
- **Length measurement:** Pixels or grid units
- **Real-time feedback:** Live updates as you type values
- **Constrained adjustment:** Lock one value while changing the other

**Professional applications:**
- **Technical drawings:** Exact angles required for instruction manuals
- **Symmetrical patterns:** Ensuring perfect symmetry with precise measurements
- **Standardization:** Making all similar elements exactly the same size
- **Quality control:** Verifying measurements meet specifications

#### Select Mode - The Properties Tool
**What it does:** Selects strands and provides access to detailed properties
**Selection capabilities:**
- **Single selection:** Click any strand
- **Multiple selection:** Ctrl+click to add to selection
- **Range selection:** Shift+click for range selection in layer panel
- **Visual feedback:** Selected strands highlighted with selection indicators

**Property access:**
- **Color properties:** Fill color, stroke color, opacity
- **Dimension properties:** Width, length, position coordinates
- **Visibility properties:** Show/hide, shadow effects
- **Layer properties:** Layer order, group membership
- **Special properties:** Arrow indicators, extension lines, circles

#### Mask Mode - The Realism Tool
**What it does:** Creates over/under effects for realistic rope appearance
**Masking principles:**
- **Visual occlusion:** Makes parts of strands invisible where others cross over
- **Layer interaction:** Works with layer ordering to determine effects
- **Realistic simulation:** Creates the appearance of physical rope crossings
- **Reversible effects:** Can add or remove masks easily

**Advanced masking:**
- **Partial masks:** Control exactly which sections are masked
- **Multiple interactions:** One strand can mask some strands and be masked by others
- **Complex patterns:** Build up realistic weaving effects with multiple masks
- **Performance considerations:** Too many masks can slow down rendering

### Layer Panel Complete Reference

#### Layer Organization System
**Numbering:** Layers numbered sequentially (1, 2, 3...) in order of creation
**Visual hierarchy:** Higher numbers appear "on top" of lower numbers
**Selection integration:** Click layer number to select that strand on canvas
**Reordering:** Drag layer buttons up/down to change drawing order

#### Advanced Layer Management
**Group functionality:**
- **Create groups:** Select multiple layers, create named groups
- **Nested groups:** Groups can contain other groups for complex organization
- **Group operations:** Move, rotate, or modify entire groups together
- **Group visibility:** Show/hide entire groups for complex project management

**Layer properties:**
- **Naming:** Custom names for layers (when available)
- **Locking:** Prevent accidental modification of specific layers
- **Visibility:** Show/hide individual layers temporarily
- **Color coding:** Visual coding system for layer categories

#### Undo/Redo System
**Full state tracking:** Every action creates a save point
**Unlimited undo:** Limited only by available memory
**Action granularity:** Individual actions (create, move, color change) tracked separately
**State restoration:** Complete restoration of all properties and relationships

### Grid System Advanced Features

#### Grid Configuration
**Grid types:**
- **Dot grid:** Points at intersection - minimal visual interference
- **Line grid:** Full lines - maximum alignment guidance
- **Adaptive grid:** Changes density based on zoom level

**Grid measurements:**
- **Pixel-based:** Direct pixel measurements for screen work
- **Real-world units:** Inches, centimeters for print work
- **Custom units:** Define your own measurement system
- **Proportional scaling:** Grid scales with zoom for consistent measurements

#### Snapping Behavior
**Snap targets:**
- **Grid intersections:** Primary snap points
- **Grid lines:** Align with horizontal/vertical lines
- **Other strands:** Snap to endpoints and midpoints of existing strands
- **Guide lines:** Custom reference lines for complex alignment

**Snap tolerance:**
- **Adjustable sensitivity:** How close you need to be for snapping to activate
- **Visual feedback:** Snap targets highlight when available
- **Override:** Hold modifier keys to temporarily disable snapping
- **Intelligent snapping:** Prioritizes most likely intended snap point

## Keyboard Shortcuts & Power User Tips

### Essential Shortcuts
| Key | Function | Context |
|-----|----------|---------|
| **Ctrl+Z** | Undo | Any mode |
| **Ctrl+Y** | Redo | Any mode |
| **Ctrl+S** | Save | Any mode |
| **Ctrl+O** | Load | Any mode |
| **Ctrl+E** | Export Image | Any mode |
| **G** | Toggle Grid | Any mode |
| **Space** | Pan mode (hold) | While drawing |
| **Mouse Wheel** | Zoom in/out | Any mode |
| **Delete** | Delete selected | Select mode |
| **Escape** | Deselect all | Any mode |

### Mode Switching Shortcuts
| Key | Mode | Notes |
|-----|------|-------|
| **A** | Attach | Most common mode |
| **M** | Move | Quick adjustments |
| **R** | Rotate | Orientation changes |
| **S** | Select | Property access |
| **K** | Mask | Knot effects |
| **Tab** | Cycle modes | Next mode in sequence |
| **Shift+Tab** | Cycle backwards | Previous mode |

### Advanced Power User Shortcuts
| Combination | Function | Expert Use |
|-------------|----------|------------|
| **Shift+Click** | Add to selection | Multiple strand operations |
| **Ctrl+Click** | Precise selection | Complex overlapping areas |
| **Alt+Drag** | Constrain movement | Horizontal/vertical only |
| **Shift+Drag** | Proportional resize | Maintain aspect ratio |
| **Ctrl+Drag** | Copy while moving | Duplicate elements quickly |
| **Middle Click+Drag** | Pan canvas | Navigate large projects |
| **Ctrl+Mouse Wheel** | Fine zoom | Precise zoom control |
| **Shift+Mouse Wheel** | Horizontal pan | Navigate wide projects |

### Hidden Shortcuts
| Key | Function | Discovery Level |
|-----|----------|-----------------|
| **Ctrl+D** | Duplicate selection | Advanced |
| **Ctrl+G** | Group selection | Advanced |
| **Ctrl+Shift+G** | Ungroup | Advanced |
| **H** | Hide selected | Advanced |
| **Shift+H** | Show all hidden | Advanced |
| **L** | Lock selected | Expert |
| **Shift+L** | Unlock all | Expert |
| **F** | Fit to canvas | Expert |
| **1-9** | Select layer 1-9 | Expert |

## Settings Deep Dive

### General Settings Complete Reference

#### Language Settings
**Supported languages:**
- English (en) - Default, most complete
- French (fr) - Français, complete translation
- German (de) - Deutsch, complete translation  
- Italian (it) - Italiano, complete translation
- Spanish (es) - Español, complete translation
- Portuguese (pt) - Português, complete translation
- Hebrew (he) - עברית, includes RTL layout support

**Language switching:**
- Immediate effect - no restart required
- All interface elements update
- Tooltips and help text included
- Right-to-left support for appropriate languages

#### Theme Settings
**Available themes:**
- **Default:** Green-based, good for general use
- **Light:** High contrast, good for bright environments
- **Dark:** Low contrast, good for dark environments, reduced eye strain
- **Custom:** User-defined color schemes (when available)

**Theme components:**
- Button colors and hover states
- Background colors and patterns
- Text colors and contrast ratios
- Selection highlight colors
- Grid and guideline colors

### Drawing Settings Advanced Configuration

#### Default Colors System
**Color properties:**
- **Strand color:** Fill color for new strands
- **Stroke color:** Outline color for new strands  
- **Shadow color:** Shadow effect color
- **Selection color:** Highlight color for selected elements
- **Grid color:** Grid line color
- **Background color:** Canvas background

**Color picker features:**
- **RGB values:** Red, Green, Blue components (0-255)
- **Hex values:** Web-standard hex color codes (#RRGGBB)
- **HSV picker:** Hue, Saturation, Value for intuitive color selection
- **Opacity control:** Alpha channel for transparency effects
- **Color presets:** Save favorite colors for reuse
- **System colors:** Use OS-standard colors when available

#### Strand Width Configuration

**Grid-Based Width System (46px Base):**
The application uses a sophisticated width calculation system based on a 46-pixel grid unit:

- **Base Grid Unit:** 46px (equivalent to 2 grid squares at 23px per square)
- **Default Stroke/Width Ratio:** 81% of total width is color, 19% is stroke
- **NumberedLayerButton Width:** When set to default grid = 2, uses 46px total width
- **Stroke Distribution:** Stroke width is split equally on both sides of the color fill

**Width Calculation Formula:**
```
Total Width = Grid Units × 23px (per grid square)
Color Width = Total Width × 81%
Stroke Width = (Total Width - Color Width) / 2
```

**Example with U-Shape Default:**
- Total width: 37px (from sample_u_shape.json)
- Stroke width: 4.5px per side
- Color width: 37px - (4.5px × 2) = 28px
- This represents approximately 81% color ratio

**Measurement units:**
- **Pixels:** Direct screen pixels, most common
- **Grid units:** Relative to grid size (23px per square), good for scalable designs
- **Real units:** Inches/centimeters when grid is calibrated
- **Relative units:** Percentage of canvas size

**Width profiles:**
- **Uniform:** Same width throughout strand length (default)
- **Tapered:** Gradually changing width (when available)
- **Variable:** Different widths at different points (advanced feature)

#### Grid Configuration Advanced
**Grid spacing:**
- **Major grid:** Primary grid lines at specified intervals
- **Minor grid:** Subdivision lines between major lines
- **Adaptive spacing:** Grid changes density based on zoom level
- **Custom spacing:** User-defined spacing in any measurement unit

**Grid behavior:**
- **Snap tolerance:** How close cursor must be to snap to grid
- **Snap priority:** Which elements take precedence for snapping
- **Visual style:** Line thickness, color, opacity of grid elements
- **Show/hide options:** What grid elements are visible

### Performance Settings

#### Rendering Quality
**Quality levels:**
- **Draft:** Fastest, lower quality for complex projects
- **Normal:** Balanced quality and performance
- **High:** Best quality, may be slower on complex projects
- **Ultra:** Maximum quality, use for final export only

**Specific quality settings:**
- **Antialiasing:** Smooth edges, higher quality but slower
- **Supersampling:** Render at higher resolution then scale down
- **Shadow quality:** Number of blur passes for shadow effects
- **Curve quality:** Number of points used to draw smooth curves

#### Memory Management
**Cache settings:**
- **Undo history size:** How many undo steps to remember
- **Image cache size:** Memory used for rendering optimization
- **Auto-save frequency:** How often to create backup saves
- **Temporary file cleanup:** When to delete temporary files

## File Format Specifications

### Project Files (.json)
**Structure overview:**
```json
{
  "version": "1.101",
  "metadata": {
    "created": "2025-01-14T10:30:00Z",
    "modified": "2025-01-14T11:45:00Z",
    "author": "User Name",
    "title": "Project Title"
  },
  "canvas": {
    "width": 800,
    "height": 600,
    "background_color": [255, 255, 255, 255],
    "grid_enabled": true,
    "grid_size": 20
  },
  "strands": [...],
  "groups": [...],
  "settings": {...}
}
```

**Strand data structure:**
```json
{
  "id": 1,
  "type": "Strand",
  "start": {"x": 100, "y": 100},
  "end": {"x": 200, "y": 200},
  "control_point1": {"x": 133, "y": 133},
  "control_point2": {"x": 166, "y": 166},
  "width": 46,
  "color": [200, 170, 230, 255],
  "stroke_color": [0, 0, 0, 255],
  "stroke_width": 4,
  "properties": {
    "has_circles": [false, false],
    "is_selected": false,
    "is_hidden": false,
    "shadow_only": false
  }
}
```

**Compatibility:**
- **Forward compatibility:** Newer versions can read older files
- **Backward compatibility:** Older versions ignore unknown properties
- **Version detection:** Automatic version detection and conversion
- **Error handling:** Graceful handling of corrupted data

### Image Export Formats

#### PNG Export
**Standard options:**
- **Bit depth:** 8-bit (256 colors) or 24-bit (16.7M colors)
- **Transparency:** Full alpha channel support
- **Compression:** Lossless compression with size optimization
- **DPI setting:** Metadata for print applications

**Advanced PNG options:**
- **Interlacing:** Progressive loading for web use
- **Color profile:** Embed ICC profiles for color accuracy
- **Metadata:** Title, author, creation date embedded
- **Optimization:** File size reduction without quality loss

#### High-Resolution Export
**Resolution options:**
- **Screen resolution:** 72-96 DPI for digital display
- **Print resolution:** 300 DPI for high-quality printing
- **Large format:** 150 DPI for posters and banners
- **Ultra-high:** 600 DPI for professional printing

**Size calculations:**
- **Pixel dimensions:** Width × Height in pixels
- **Print dimensions:** Physical size at specified DPI
- **File size estimation:** Approximate file size before export
- **Memory requirements:** RAM needed for high-resolution export

### Import/Export Integration

#### Importing from Other Applications
**Image import:**
- **Background images:** Import photos or sketches as reference
- **Trace overlay:** Draw over imported images
- **Scale matching:** Maintain proportions when importing
- **Layer integration:** Import images as background layers

**Vector import (when available):**
- **SVG support:** Import basic SVG paths
- **DXF support:** Import CAD drawings
- **AI support:** Import Adobe Illustrator files
- **Conversion process:** How vector data becomes strands

#### Exporting to Other Applications
**Vector export:**
- **SVG export:** Scalable vector graphics for web use
- **PDF export:** High-quality print-ready files
- **AI export:** Adobe Illustrator compatibility
- **DXF export:** CAD application compatibility

**Specialized exports:**
- **Teaching materials:** Optimized for educational use
- **Web graphics:** Optimized for web display
- **Print preparation:** CMYK color space conversion
- **Animation frames:** Sequential exports for animation

## Integration with Other Tools

### Graphics Applications
**Adobe Creative Suite:**
- **Illustrator:** Import/export vector paths
- **Photoshop:** Import as smart objects or raster layers
- **InDesign:** Place exported files as graphics
- **After Effects:** Import for animation (sequence of exports)

**Free alternatives:**
- **GIMP:** Import PNG exports for further editing
- **Inkscape:** SVG import/export compatibility
- **Blender:** Import as reference for 3D rope modeling
- **Krita:** Import for artistic enhancement

### CAD Applications
**Engineering tools:**
- **AutoCAD:** DXF export for technical drawings
- **SolidWorks:** Reference drawings for 3D rope modeling
- **SketchUp:** Import as image overlays for 3D scenes
- **Fusion 360:** Reference for mechanical drawings

### Educational Platforms
**Learning management systems:**
- **Canvas:** Upload images directly to courses
- **Blackboard:** Embed in educational materials
- **Moodle:** Share as downloadable resources
- **Google Classroom:** Share via Google Drive integration

### Web and Digital Publishing
**Web platforms:**
- **WordPress:** Upload and embed in posts
- **Drupal:** Content management integration
- **Static sites:** Include in Jekyll, Hugo, etc.
- **E-learning:** SCORM package integration

## Performance Optimization Guide

### Large Project Management
**Project size considerations:**
- **Layer count:** 50+ layers require careful management
- **Canvas size:** Larger canvases use more memory
- **Complexity:** Highly curved strands are more demanding
- **Effects:** Shadows and transparency increase rendering time

**Optimization strategies:**
1. **Work in sections:** Hide unneeded layers while working
2. **Simplify during editing:** Use draft quality while adjusting
3. **Group related elements:** Reduce selection complexity
4. **Regular cleanup:** Remove hidden or unnecessary elements
5. **Save frequently:** Prevent loss due to performance issues

### Memory Management
**Understanding memory use:**
- **Undo history:** Each undo state uses memory
- **Image cache:** Rendered graphics cached for performance
- **Layer complexity:** More complex layers use more memory
- **Zoom level:** Higher zoom requires more detailed rendering

**Memory optimization:**
1. **Limit undo history:** Reduce saved undo steps in settings
2. **Close other applications:** Free RAM for OpenStrand Studio
3. **Regular saves:** Clear undo history with save operations
4. **Restart periodically:** Clear accumulated memory use
5. **Monitor usage:** Watch for performance degradation

### Rendering Performance
**Factors affecting speed:**
- **Antialiasing quality:** Higher quality = slower rendering
- **Layer count:** More layers = more processing
- **Transparency effects:** Alpha blending is computationally expensive
- **Curve complexity:** More control points = slower curves

**Performance tuning:**
1. **Adjust quality settings:** Use draft mode while editing
2. **Disable transparency:** Reduce alpha effects during editing
3. **Simplify curves:** Use fewer control points when possible
4. **Batch operations:** Make multiple changes before updating display
5. **Hardware acceleration:** Ensure graphics drivers are current

## Accessibility Features

### Visual Accessibility
**High contrast support:**
- **Theme options:** High contrast themes for vision impairments
- **Color customization:** Adjust all interface colors
- **Size scaling:** Larger interface elements (when available)
- **Font options:** High-legibility fonts

**Color blindness support:**
- **Color-blind friendly palettes:** Pre-designed safe color schemes
- **Pattern alternatives:** Use line styles instead of just colors
- **Contrast validation:** Ensure sufficient contrast ratios
- **Color independence:** Don't rely solely on color for information

### Motor Accessibility
**Alternative input methods:**
- **Keyboard navigation:** Full keyboard control of interface
- **Larger click targets:** Bigger buttons for easier clicking
- **Drag alternatives:** Alternative methods for drag operations
- **Gesture alternatives:** Non-gesture ways to accomplish tasks

**Precision assistance:**
- **Snap-to grids:** Easier precise positioning
- **Magnetism:** Elements automatically align to nearby elements
- **Large cursor modes:** More visible cursor options
- **Movement constraints:** Lock to horizontal/vertical movement

### Cognitive Accessibility
**Interface simplification:**
- **Progressive disclosure:** Show advanced features only when needed
- **Clear labeling:** Descriptive text for all functions
- **Consistent patterns:** Same actions work the same way throughout
- **Undo support:** Easy recovery from mistakes

**Learning support:**
- **Built-in tutorials:** Step-by-step guidance
- **Context help:** Help information relevant to current task
- **Progressive complexity:** Start simple, add complexity gradually
- **Visual feedback:** Clear indication of what actions accomplish

## Troubleshooting Encyclopedia

### Startup and Installation Issues

#### Application Won't Start
**Windows specific:**
- **Error:** "DLL load failed while importing QtWidgets"
  - **Cause:** PyQt5 DLL conflicts with other installed software
  - **Solution:** Use the build_with_venv.bat script for clean environment
  - **Prevention:** Install in virtual environment

- **Error:** "Python not found"
  - **Cause:** Python not in system PATH
  - **Solution:** Reinstall Python with "Add to PATH" option checked
  - **Alternative:** Use full path to python.exe

**macOS specific:**
- **Error:** "App can't be opened because it's from unidentified developer"
  - **Solution:** Right-click app, select "Open", then "Open" again
  - **Alternative:** Go to Security & Privacy settings, allow the app

**Linux specific:**
- **Error:** "ImportError: No module named PyQt5"
  - **Solution:** Install PyQt5 with package manager: `sudo apt-get install python3-pyqt5`
  - **Alternative:** Use pip: `pip install PyQt5`

#### Performance Problems on Startup
**Slow startup:**
- **Check:** Available system memory (RAM)
- **Check:** Hard drive space (needs temp files)
- **Check:** Other running applications
- **Solution:** Close other applications, restart computer

**Crashes during startup:**
- **Check:** Graphics driver version
- **Update:** Graphics drivers to latest version
- **Try:** Safe mode startup (reduced graphics features)
- **Reinstall:** Application if problems persist

### Drawing and Interface Issues

#### Drawing Problems
**Strands don't appear when drawn:**
- **Check:** Are you in Attach mode?
- **Check:** Is canvas zoomed out too far to see details?
- **Solution:** Switch to Attach mode, zoom in to see drawn strands

**Can't select strands:**
- **Check:** Are you in Move or Select mode?
- **Check:** Are layers hidden?
- **Solution:** Use layer panel numbers for precise selection
- **Alternative:** Switch to Select mode for easier clicking

**Control points not visible:**
- **Check:** Control points setting in preferences
- **Check:** Are you in Move mode?
- **Solution:** Enable control points in settings
- **Note:** Control points only show in certain modes

#### Visual Display Problems
**Interface looks wrong:**
- **Cause:** Display scaling issues on high-DPI screens
- **Solution:** Adjust Windows display scaling to 100%
- **Alternative:** Update graphics drivers

**Colors look different than expected:**
- **Check:** Monitor color calibration
- **Check:** Theme settings
- **Solution:** Calibrate monitor or adjust theme colors
- **Note:** Colors may appear different on different monitors

**Text is too small:**
- **Solution:** Change Windows text size settings
- **Alternative:** Use high contrast theme
- **Workaround:** Increase monitor resolution

### File Operation Issues

#### Saving Problems
**Can't save files:**
- **Check:** Write permissions to target folder
- **Check:** Available disk space
- **Solution:** Save to Desktop or Documents folder
- **Alternative:** Run as administrator (Windows)

**Files corrupted after save:**
- **Cause:** Disk space ran out during save
- **Cause:** System crash during save operation
- **Prevention:** Check disk space before saving
- **Solution:** Use multiple backup saves

**Large files save slowly:**
- **Cause:** Complex projects with many layers
- **Normal:** Large projects take longer to save
- **Solution:** Save frequently during work, not just at end
- **Alternative:** Export image backups regularly

#### Loading Problems
**Files won't open:**
- **Check:** File extension (.json for projects)
- **Check:** File not corrupted (try backup copy)
- **Solution:** Try loading a sample file first
- **Workaround:** Start new project, copy elements manually

**Old files won't open in new version:**
- **Usually works:** Newer versions read older files
- **Check:** Version number in error message
- **Solution:** Update to latest version
- **Workaround:** Export as image from old version

**Missing elements when loading:**
- **Cause:** File partially corrupted
- **Check:** File size (should be > 0 bytes)
- **Solution:** Load most recent backup
- **Prevention:** Save multiple versions with different names

### Advanced Troubleshooting

#### Memory and Performance Issues
**Application becomes slow:**
- **Check:** How many layers in current project
- **Check:** System available memory
- **Solution:** Close other applications, restart OpenStrand Studio
- **Prevention:** Work in sections, hide unused layers

**Crashes during complex operations:**
- **Check:** Available system memory
- **Check:** Virtual memory settings
- **Solution:** Increase virtual memory, add more RAM
- **Workaround:** Simplify project, work in smaller sections

**Undo/Redo stops working:**
- **Cause:** Memory full, undo history cleared
- **Normal:** After very complex operations
- **Solution:** Save project, restart application
- **Prevention:** Save frequently, limit undo history size

#### Graphics and Display Issues
**Rendering errors or artifacts:**
- **Update:** Graphics drivers to latest version
- **Check:** Graphics card compatibility
- **Solution:** Switch to software rendering in settings
- **Workaround:** Reduce graphics quality in settings

**Zoom problems:**
- **Cause:** Graphics memory limitations
- **Solution:** Zoom out, then back in gradually
- **Alternative:** Restart application to reset zoom
- **Prevention:** Avoid extreme zoom levels

## Expert Tips & Hidden Features

### Power User Techniques

#### Advanced Selection Methods
**Multi-layer operations:**
1. **Range select:** Click first layer, Shift+click last layer
2. **Skip select:** Ctrl+click each desired layer individually  
3. **Inverse select:** Select unwanted layers, then use "Select Inverse"
4. **Group select:** Click group name to select all layers in group

**Smart selection patterns:**
- **By color:** Select all strands of similar color automatically
- **By type:** Select all regular strands vs. all attached strands
- **By property:** Select all hidden strands, all locked strands, etc.
- **By position:** Select all strands in a rectangular area

#### Advanced Movement Techniques
**Precision positioning:**
1. **Nudge movement:** Arrow keys for 1-pixel movement
2. **Large nudge:** Shift+arrows for 10-pixel movement
3. **Grid nudge:** Ctrl+arrows for grid-unit movement
4. **Proportional nudge:** Alt+arrows for percentage movement

**Duplication workflows:**
1. **Copy-in-place:** Ctrl+D creates duplicate at same location
2. **Offset duplicate:** Ctrl+drag creates copy while moving
3. **Array duplicate:** Create multiple copies in pattern
4. **Mirror duplicate:** Copy and flip for symmetrical elements

#### Professional Curve Control
**Bezier mastery:**
1. **Independent control points:** Break tangent handles for sharp curves
2. **Smooth transitions:** Align tangent handles for flowing curves
3. **Tension control:** Adjust handle lengths for curve tightness
4. **Natural curves:** Use reference photos for realistic rope behavior

**Curve standardization:**
1. **Template curves:** Save standard curve shapes as templates
2. **Curve copying:** Copy curve properties between strands
3. **Mathematical curves:** Use angle/length mode for precise mathematical curves
4. **Symmetrical curves:** Ensure matching curves in symmetrical patterns

### Hidden Features and Easter Eggs

#### Secret Keyboard Combinations
**Debug information:**
- **Ctrl+Shift+D:** Show debug information overlay
- **Ctrl+Shift+P:** Show performance statistics
- **Ctrl+Shift+M:** Show memory usage information
- **Ctrl+Shift+L:** Show layer hierarchy in detail

**Advanced grid features:**
- **Ctrl+G:** Toggle between grid types (dots, lines, etc.)
- **Shift+G:** Adjust grid opacity
- **Alt+G:** Show/hide grid coordinates
- **Ctrl+Alt+G:** Reset grid to default settings

**Experimental features:**
- **Ctrl+Shift+E:** Enable experimental features menu
- **Ctrl+Shift+T:** Toggle experimental rendering mode
- **Ctrl+Shift+A:** Advanced animation preview (if available)

#### Professional Workflow Secrets
**Batch operations:**
1. **Color themes:** Apply coordinated color schemes to entire project
2. **Style copying:** Copy all style properties from one strand to another
3. **Bulk property changes:** Change properties of multiple strands simultaneously
4. **Template application:** Apply saved templates to multiple elements

**Advanced export options:**
1. **Export presets:** Save custom export configurations
2. **Batch export:** Export multiple formats simultaneously
3. **Layered export:** Export individual layers as separate files
4. **Animation export:** Export sequence of images for animation

**Project management:**
1. **Version control:** Automatic version numbering for saves
2. **Component libraries:** Save frequently used elements as reusable components
3. **Project templates:** Create master templates for different project types
4. **Collaboration features:** Export project components for team work

### Customization and Extension

#### Settings File Advanced Editing
**Location of settings files:**
- **Windows:** `%APPDATA%/OpenStrand Studio/user_settings.txt`
- **macOS:** `~/Library/Application Support/OpenStrand Studio/user_settings.txt`
- **Linux:** `~/.local/share/OpenStrand Studio/user_settings.txt`

**Advanced settings not in GUI:**
```
# Advanced rendering settings
RenderingQuality: ultra
MaxUndoHistory: 100
AutoSaveInterval: 300
CacheSize: 512
DebugMode: false

# Advanced grid settings
GridSubdivisions: 4
GridOpacity: 0.3
GridColor: 128,128,128,128

# Advanced color settings
HighContrastMode: false
ColorBlindMode: none
CustomThemeFile: custom_theme.json
```

#### Creating Custom Themes
**Theme file structure:**
```json
{
  "name": "My Custom Theme",
  "version": "1.0",
  "colors": {
    "background": "#F5F5F5",
    "canvas": "#FFFFFF", 
    "grid": "#E0E0E0",
    "selection": "#FF6B6B",
    "button_normal": "#4ECDC4",
    "button_hover": "#45B7D1",
    "button_active": "#96CEB4",
    "text": "#2C3E50"
  },
  "sizes": {
    "button_width": 100,
    "button_height": 40,
    "panel_width": 250
  }
}
```

**Installation:**
1. Create theme file in OpenStrand Studio directory
2. Reference in settings file: `CustomThemeFile: my_theme.json`
3. Restart application to load custom theme
4. Share theme files with other users

---

**Congratulations!** You have now mastered OpenStrand Studio. This complete reference covers every feature, technique, and professional workflow. You're equipped to create everything from simple knots to complex publication-quality rope diagrams. Keep this guide handy as your comprehensive reference manual.