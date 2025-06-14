# Temporary Window Issues During Attach Operations

## Identified Issues

### 1. QApplication.processEvents() in partial_update()
- **Location**: attach_mode.py, line 92
- **Issue**: Calling `processEvents()` during mouse movement can cause pending UI events to be processed, potentially creating temporary windows
- **Context**: Called frequently during strand dragging in partial_update method

### 2. Layer Panel Refresh Methods
- **Location**: layer_panel.py, lines 1996-2025, 2058-2059
- **Issue**: The refresh methods disable/enable updates on the main window which can cause window flashing
- **Methods affected**:
  - `refresh_layers()` - lines 1970-2034
  - `refresh()` - lines 2035+
  - Both methods call `main_window.setUpdatesEnabled(False/True)`

### 3. Synchronous Repaint When Zoomed
- **Location**: attach_mode.py, line 81
- **Issue**: Using `repaint()` instead of `update()` forces immediate synchronous painting
- **Context**: Called when zoom_factor != 1.0

### 4. Potential UI Update Batching Issues
- **Multiple update calls**: The code has several places where UI updates might not be properly batched
- **Background cache invalidation**: Frequent cache invalidation might cause unnecessary redraws

## Recommendations

1. **Remove or defer processEvents()**: Consider removing the `processEvents()` call or moving it to less critical paths
2. **Batch UI updates**: Ensure all UI updates during attach operations are properly batched
3. **Avoid disabling main window updates**: Use more targeted update disabling instead of disabling the entire main window
4. **Use update() instead of repaint()**: Replace synchronous repaint() calls with asynchronous update() calls where possible