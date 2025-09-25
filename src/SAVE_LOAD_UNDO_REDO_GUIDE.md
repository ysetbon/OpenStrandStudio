# Save/Load and Undo/Redo Implementation Guide

This guide explains how to implement save/load and undo/redo functionality for strand properties in OpenStrandStudio.

## System Overview

The save/load and undo/redo system consists of three main components:

1. **SaveLoadManager** (`save_load_manager.py`) - Handles serialization/deserialization to/from JSON files
2. **UndoRedoManager** (`undo_redo_manager.py`) - Manages state history for undo/redo operations
3. **Property Toggles** (various UI components) - Trigger state saves when properties change

## How to Add a New Property with Save/Load and Undo/Redo Support

### Step 1: Initialize the Property

Add the property initialization in the strand class constructor:

```python
# In strand.py or attached_strand.py
class Strand:
    def __init__(self, ...):
        # ... existing initialization ...
        self.my_new_property = False  # Default value
```

### Step 2: Add Property to Save Serialization

In `save_load_manager.py`, add the property to the `serialize_strand` function:

```python
def serialize_strand(strand, canvas, index=None):
    # ... existing code ...
    data = {
        # ... existing properties ...
        "my_new_property": getattr(strand, 'my_new_property', False),
    }
```

### Step 3: Add Property to Load Deserialization

In `save_load_manager.py`, add the property restoration in `deserialize_strand` function:

```python
def deserialize_strand(data, canvas, strand_dict=None, parent_strand=None):
    # ... after strand creation ...
    strand.my_new_property = data.get("my_new_property", False)
```

For AttachedStrand, also add it in the load_strands function around line 650:

```python
# In load_strands function, when processing AttachedStrand
strand.my_new_property = strand_data.get("my_new_property", False)
```

### Step 4: Create a Toggle Function with Undo/Redo Support

When creating a UI toggle function, ensure it saves the state after modification:

```python
def toggle_my_property(self, strand, layer_panel):
    """Toggles my new property for a strand."""
    if hasattr(strand, 'my_new_property'):
        current_value = getattr(strand, 'my_new_property')
        setattr(strand, 'my_new_property', not current_value)

        # Update the canvas display
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()

            # Save state for undo/redo
            if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                # Force save by resetting the last save time
                layer_panel.canvas.undo_redo_manager._last_save_time = 0
                layer_panel.canvas.undo_redo_manager.save_state()
```

## Example: Full Arrow Implementation

The `full_arrow_visible` property is a complete example of this pattern:

### 1. Initialization
- `strand.py` line 86: `self.full_arrow_visible = False`
- `attached_strand.py` line 99: `self.full_arrow_visible = False`

### 2. Serialization
- `save_load_manager.py` line 127: Added to data dictionary
- `save_load_manager.py` line 428: Restored from data

### 3. AttachedStrand Loading
- `save_load_manager.py` line 655: Restored for AttachedStrand

### 4. Toggle with Undo/Redo
- `numbered_layer_button.py` line 2270-2282: `toggle_strand_full_arrow_visibility` function

## Key Implementation Details

### Save/Load Manager

The SaveLoadManager uses JSON serialization with custom encoders to handle PyQt objects:
- QPointF objects are converted to `{"x": x_value, "y": y_value}`
- QColor objects are converted to `{"r": red, "g": green, "b": blue, "a": alpha}`
- Complex objects like strands are serialized with their type information

### Undo/Redo Manager

The UndoRedoManager:
- Saves complete states to temporary JSON files
- Each state is identified by a session ID and step number
- Manages current_step and max_step for navigation
- Prevents duplicate saves within 500ms using `_last_save_time`
- Checks for identical states before saving to avoid duplicates

### State Saving Triggers

State is automatically saved when:
- User releases mouse in move/rotate modes
- Properties are toggled through UI
- Layers are added/removed
- Groups are created/modified

### Important Considerations

1. **Always use getattr with defaults** when reading properties to handle older save files:
   ```python
   property_value = getattr(strand, 'property_name', default_value)
   ```

2. **Force state save** after property changes by resetting `_last_save_time`:
   ```python
   undo_redo_manager._last_save_time = 0
   ```

3. **Update canvas** after property changes to reflect visual changes:
   ```python
   layer_panel.canvas.update()
   ```

4. **Handle all strand types** (Strand, AttachedStrand, MaskedStrand) when adding properties

## Testing Checklist

When adding a new property:
- [ ] Property initializes with correct default value
- [ ] Property saves correctly to JSON file
- [ ] Property loads correctly from JSON file
- [ ] Property loads correctly from older files without the property
- [ ] Undo restores previous property value
- [ ] Redo restores changed property value
- [ ] Property persists across application restart
- [ ] Property works for all strand types (regular, attached, masked)

## Existing Properties with Save/Load Support

Current properties that follow this pattern:
- `has_circles` - Circle visibility at strand ends
- `is_hidden` - Strand visibility
- `shadow_only` - Shadow-only rendering mode
- `start_extension_visible` - Start extension line visibility
- `end_extension_visible` - End extension line visibility
- `start_arrow_visible` - Start arrow visibility
- `end_arrow_visible` - End arrow visibility
- `full_arrow_visible` - Full arrow visibility
- `arrow_color` - Custom arrow color
- `arrow_head_visible` - Arrow head visibility
- `arrow_casts_shadow` - Arrow shadow casting
- `manual_circle_visibility` - Manual override for circle visibility