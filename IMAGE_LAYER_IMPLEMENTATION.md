# Image Layer Implementation - Complete Documentation

## Overview
Image layers are special layers that display imported images (PNG, JPG, etc.) in the canvas. They behave like regular strand layers in terms of ordering, selection, and visibility, but have unique properties and interactions.

## Core Components

### 1. ImageLayer Class (`image_layer.py`)
**Purpose**: Represents a single image layer with its properties and drawing logic.

**Key Properties**:
- `pixmap`: The loaded image data
- `filename`: Original file path
- `layer_number`: Numeric identifier (e.g., 1 for "1_img")
- `layer_name`: Full name in format "X_img" (e.g., "1_img", "2_img")
- `position`: QPointF for image placement in canvas
- `visible`: Boolean for show/hide state
- `selected`: Boolean for selection state
- `opacity`: Float value for transparency (default 1.0)
- `scale`: Float value for size adjustment (default 1.0)

**Key Methods**:
- `draw(painter, zoom_factor, is_selected)`: Renders the image on canvas with proper scaling and selection indication
- `contains_point(pos, zoom_factor)`: Hit detection for mouse interactions
- `get_bounding_rect(zoom_factor)`: Returns the image boundaries for collision detection

**Drawing Behavior**:
- Images are drawn with their top-left corner at `position`
- When selected, a purple border (3px) is drawn around the image
- Respects zoom factor for proper scaling
- Supports opacity for transparency effects

### 2. Layer Panel Integration (`layer_panel.py`)

**Button Creation**:
- Custom `ImageLayerButton` class extends `NumberedLayerButton`
- Always displays purple color (#BA55D3) as base
- Selected state: Darker purple with thick border (#8B008B, 3px)
- Unselected state: Lighter purple with thin border (#DDA0DD, 2px)
- Button text shows layer name (e.g., "1_img")

**Layer Management**:
- Image layers stored in `self.image_layers` list (separate from strands)
- Buttons marked with `is_image_button = True` flag for identification
- Layer numbering uses next available set number to avoid conflicts

**Selection Behavior**:
- Selecting an image layer performs complete "Deselect All" on strands
- Clears all strand highlighting and selection states
- Updates Move Mode to clear `highlighted_strand` and `affected_strand`
- Only one image layer can be selected at a time

**Context Menu**:
- Image layer buttons have custom context menu
- Only "Hide Layer" option available (no delete, mask, etc.)
- Toggle visibility updates the canvas immediately

### 3. Canvas Drawing (`strand_drawing_canvas.py`)

**Unified Drawing System**:
- Single drawing pass for all layers (images and strands)
- Order determined by actual QLayout widget positions, not list order
- Bottom-to-top drawing (last in layout = first drawn = behind)

**Drawing Order Logic**:
1. Iterate through `scroll_layout` from bottom (count-1) to top (0)
2. Identify each button as image or strand
3. Build unified draw order list
4. Draw each layer in sequence (images and strands intermixed)

**Selection Visual Feedback**:
- No strand highlighting when any image is selected
- `selected_image_exists` flag prevents all strand highlight drawing
- Image selection border drawn by ImageLayer.draw() method

### 4. Move Mode Behavior (`move_mode.py`)

**Exclusive Image Movement**:
- When image selected: ONLY that image can be moved
- All strand/control point interactions blocked
- Click detection checks image selection first
- Early return prevents any other processing

**Movement Mechanics**:
- `is_moving_image` flag tracks image drag state
- `moving_image_layer` stores reference to dragging image
- `image_drag_start` stores offset for smooth dragging
- Position updates directly modify `image_layer.position`

**Non-Selected Images**:
- Clicking on unselected images does nothing in move mode
- No selection change from move mode clicks
- Must select from layer panel first

### 5. Drag and Drop Support

**Button Mapping**:
- Separate maps for strands (`button_to_strand_map`) and images (`button_to_image_map`)
- Maps rebuilt before each drag operation
- Identifies buttons by `is_image_button` flag

**Order Management**:
- After drop, rebuilds both `canvas.strands` and `image_layers` lists
- Maintains relative positioning between all layer types
- Visual order in panel matches drawing order exactly

**Drop Validation**:
- Checks both maps for valid button references
- Falls back to refresh if mapping fails
- Preserves selection states through drag operation

### 6. Refresh and State Preservation

**Refresh Function Updates**:
1. Store original order from layout before clearing
2. Create all buttons in dictionary (not added to layout yet)
3. Re-add buttons following original order
4. New buttons added at top if not in original order

**State Preservation**:
- Image layer selection state maintained
- Position in stack preserved
- Visibility and other properties retained
- Works with undo/redo system

### 7. File Loading

**Load Image Dialog**:
- Standard file dialog for PNG/JPG selection
- Automatic layer naming (X_img format)
- Uses next available set number
- Prevents number conflicts with strands

**Initial State**:
- New images automatically selected
- Added at top of layer stack
- Visible by default
- Full opacity and scale

### 8. Special Behaviors and Rules

**Image Layers Are**:
- Never attachable (no green sides)
- Never deletable via Delete button
- Never maskable
- Never participate in strand connections
- Always purple-colored in panel

**Selection Rules**:
- Image selection clears ALL strand selections
- Acts like "Deselect All" + select image
- Move mode highlighting disabled when image selected
- Canvas shows no strand highlights with image selection

**Interaction Priorities**:
- In move mode with image selected: image movement only
- Click detection: selected images checked before strands
- Drag and drop: unified handling for both types

## Key Design Decisions

### Separation of Concerns
- Image layers kept separate from strands list
- Different storage (`image_layers` vs `strands`)
- Unified only at drawing and UI level

### Visual Consistency
- Purple color theme for all image UI elements
- Consistent with application's color coding
- Clear visual distinction from strands

### Movement Restrictions
- Images only movable when explicitly selected
- Prevents accidental image displacement
- Clear user intention required

### Layer Order Philosophy
- True unified stacking order
- Images can be anywhere in stack
- Visual order = drawing order = logical order

## Integration Points

### Main Systems Affected:
1. **Layer Panel**: Button creation, selection, drag-drop
2. **Canvas**: Drawing order, selection rendering
3. **Move Mode**: Exclusive movement logic
4. **Refresh System**: Order preservation
5. **Save/Load**: Would need serialization (not implemented)
6. **Undo/Redo**: State tracking for image operations

### Event Flow:
1. User loads image → Creates ImageLayer + Button
2. User clicks button → Triggers selection cascade
3. Selection → Clears strands, updates canvas, modifies move mode
4. Drag in move mode → Exclusive image movement
5. Drag in panel → Reorders unified layer stack
6. Refresh → Preserves order and states

This implementation treats image layers as first-class layers with special properties, fully integrated into the layer system while maintaining their unique characteristics and behaviors.