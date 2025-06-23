# Shadow Only Feature Implementation

## How "Shadow Only" Works

When you set a strand to "Shadow Only":

1. **The strand itself becomes invisible** - you don't see the actual strand body, lines, arrows, or any visual elements
2. **The strand still casts shadows** on strands below it in the layer order - this is the key feature
3. **Other strands can still cast shadows onto the shadow-only strand** (but since it's invisible, you won't see those shadows)
4. **The result**: You see realistic shadow patterns on visible strands as if the invisible strand was still there casting shadows

**Important**: The shadow-only strand must continue to participate in the shadow calculation system to cast shadows on other strands below it.

## Visual Example

**Before Shadow Only:**
```
[Strand A] ←visible
[Strand B] ←visible (with shadow from A)
```

**After setting Strand A to Shadow Only:**
```
[        ] ←invisible (Strand A)
[Strand B] ←visible (still has shadow from invisible Strand A)
```

## Persistence Across All Operations

This "Shadow Only" behavior is **guaranteed to persist** during:

- **Zooming in** - Shadow-only strands remain invisible but continue casting shadows
- **Zooming out** - Shadow-only strands remain invisible but continue casting shadows  
- **Panning** - Shadow-only strands remain invisible but continue casting shadows
- **View transformations** - Shadow-only strands remain invisible but continue casting shadows
- **Canvas updates** - Shadow-only strands remain invisible but continue casting shadows

## Implementation Details

The system ensures consistency by:

1. **Preserving the `shadow_only` property** - The property is never reset during zoom/pan operations
2. **Strand rendering**: Shadow-only strands skip their own drawing in `draw()` methods
3. **Shadow casting**: Shadow-only strands continue to cast shadows through the shadow system
4. **State persistence**: The `shadow_only` state is maintained across all canvas operations and transformations

## Technical Implementation

### 1. Core Strand Property (`strand.py`)
- Added `self.shadow_only = False` property to Strand.__init__() (line 33)
- Modified draw() method to skip visual rendering while preserving shadow calculations:
  - Shadow calculation code (lines 1130-1160) executes normally
  - Strand body drawing (lines 1270-1300) wrapped in `if not shadow_only` checks
  - Arrow, extension, and other visual elements also wrapped in shadow-only checks

### 2. UI Integration (`numbered_layer_button.py`)
- Right-click menu already implemented with "Shadow Only" option
- Button styling with dashed border for shadow-only mode
- Checkmark indicator in context menu when enabled

### 3. Layer Panel Toggle (`layer_panel.py`)
- `toggle_layer_shadow_only(strand_index)` method (lines 931-964)
- Updates strand.shadow_only property
- Updates button appearance via `button.set_shadow_only()`
- Triggers canvas update and state saving

### 4. Undo/Redo Support (`layer_panel.py` + `undo_redo_manager.py`)
- Calls `layer_state_manager.save_current_state()` 
- Calls `undo_redo_manager.save_state()` with timing bypass
- Added visual difference detection for shadow_only property (lines 1070-1081, 1503-1514)
- Ensures shadow-only changes are treated as distinct states and not skipped as "visually identical"

#### **Critical Undo/Redo Implementation Pattern for ALL Strand Types**

To properly implement shadow-only support for AttachedStrand and MaskedStrand, follow this **exact pattern**:

**Step 1: Add to Serialization** (`save_load_manager.py`)
```python
# In serialize_strand function around line 125
"shadow_only": getattr(strand, 'shadow_only', False),
```

**Step 2: Add to Deserialization** (`save_load_manager.py`) 
```python
# In deserialize_strand function(s) 
strand.shadow_only = data.get("shadow_only", False)
```

**Step 3: Add Visual Difference Detection** (`undo_redo_manager.py`)
```python
# Add this EXACT block in BOTH undo() and redo() functions
# After the is_hidden check, before extension visibility check:

# --- NEW: Check shadow-only mode ---
if hasattr(new_strand, 'shadow_only') and hasattr(original_strand, 'shadow_only'):
    if new_strand.shadow_only != original_strand.shadow_only:
        logging.info(f"Undo check: Strand {new_strand.layer_name} shadow_only differs.")
        has_visual_difference = True
        break
elif hasattr(new_strand, 'shadow_only') != hasattr(original_strand, 'shadow_only'):
    logging.info(f"Undo check: Strand {new_strand.layer_name} shadow_only attribute presence differs.")
    has_visual_difference = True
    break
# --- END NEW ---
```

**Step 4: Add to Drawing Logic** (in strand class `draw()` method)
```python
# Wrap ALL visual rendering (not shadow calculations) with:
if not getattr(self, 'shadow_only', False):
    # Visual rendering code here (stroke drawing, fill drawing, etc.)
    # But KEEP shadow calculation code outside this check
```

**⚠️ CRITICAL**: Without ALL 4 steps, undo/redo will skip shadow-only states as "visually identical".

#### **Implementation Locations for AttachedStrand and MaskedStrand**

**For AttachedStrand:**
- **Step 1 & 2**: Serialization is already handled by the base `serialize_strand` function
- **Step 3**: Visual comparison is already handled (works for all strand types)  
- **Step 4**: Add shadow-only check to `attached_strand.py` `draw()` method
- **Additional**: Add `self.shadow_only = False` to `AttachedStrand.__init__()`

**For MaskedStrand:**
- **Step 1 & 2**: Serialization is already handled by the base `serialize_strand` function
- **Step 3**: Visual comparison is already handled (works for all strand types)
- **Step 4**: Add shadow-only check to `masked_strand.py` `draw()` method  
- **Additional**: Add `self.shadow_only = False` to `MaskedStrand.__init__()`

**Example for AttachedStrand/MaskedStrand `draw()` method:**
```python
def draw(self, painter, canvas):
    # Shadow calculations and other logic that should always run
    # ... existing shadow code ...
    
    # --- START: Skip visual rendering in shadow-only mode ---
    if getattr(self, 'shadow_only', False):
        # In shadow-only mode, skip all visual drawing but preserve shadows
        painter.restore()  # Clean up painter state
        return
    # --- END: Skip visual rendering in shadow-only mode ---
    
    # All visual rendering code (strokes, fills, etc.)
    # ... existing visual drawing code ...
```

**Why this pattern works universally:**
1. The serialization system uses the base `serialize_strand` function for all types
2. The visual comparison logic checks all strand types uniformly
3. Only the drawing logic needs type-specific implementation
4. The shadow_only property is inherited by all strand subclasses

### 5. Save/Load Functionality (`save_load_manager.py`)
- Added `shadow_only` property to serialization (line 125) and deserialization in multiple locations:
  - Line 125: serialize_strand function - saves shadow_only property
  - Line 353: Main deserialize_strand function
  - Line 504: Alternative strand loading path  
  - Line 583: Masked strand loading path
- Button state restoration in `update_layer_button_states()` (layer_panel.py:2484-2485)

### 6. Button State Management (`numbered_layer_button.py`)
- `set_shadow_only(shadow_only)` method updates button appearance
- `update_style()` method handles dashed border styling for shadow-only mode
- State restoration during refresh operations

## Key Code Locations

| Feature | File | Lines | Description |
|---------|------|-------|-------------|
| Core Property | strand.py | 33 | shadow_only initialization |
| Drawing Logic | strand.py | 1270-1300 | Skip visual rendering |
| Shadow Casting | strand.py | 1130-1160 | Preserve shadow calculations |
| UI Toggle | layer_panel.py | 931-964 | toggle_layer_shadow_only method |
| Undo/Redo | layer_panel.py | 953-960 | State saving |
| Undo/Redo Visual Check | undo_redo_manager.py | 1070-1081, 1503-1514 | Shadow-only comparison logic |
| Save/Load | save_load_manager.py | 125, 353, 504, 583 | Property serialization |
| Button States | layer_panel.py | 2484-2485 | State restoration |

This creates a robust system where shadow-only strands provide realistic lighting effects while remaining completely invisible to the user, regardless of any navigation or view changes in the application.