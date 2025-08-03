# Move Mode Highlighting Issue

## Your Goal

You want to fix the highlighting behavior in move mode when the "draw only affected strand" toggle is **OFF**. Specifically:

- When you click on the connection between strands 1_1 and 1_2 with the toggle OFF
- Both strand 1_1 (parent) and strand 1_2 (attached) should be highlighted
- Currently, only strand 1_2 is being highlighted, but strand 1_1 is not

## The Issue

The problem is that the **optimized paint handler is not being set up** when strands are marked as selected during mouse press. Here's what's happening:

1. ✅ **Selection Logic Works**: Both strands are correctly marked with `is_selected=True`
   ```
   DEBUG: Set is_selected=True for moving strand: 1_1
   DEBUG: Set is_selected=True for moving strand: 1_2
   ```

2. ❌ **Paint Handler Setup Missing**: The optimized paint handler that should draw both highlighted strands is not being triggered
   - Only the normal `paintEvent` is running (multiple `[ATTACHED_STRAND_DRAW_START] 1_2` calls)
   - No logs from optimized paint handler setup or execution
   - Strand 1_1 is never drawn, only strand 1_2

3. **Root Cause**: The optimized paint handler setup code I added isn't being executed, even though it's in the right location after the strand selection

## Expected Behavior vs Current Behavior

**When toggle is ON (working correctly)**: Both strands highlighted during movement
**When toggle is OFF (broken)**: Only directly selected strand highlighted, connected strand ignored

## Files to Provide to Another Model

Give these files to the other model:

1. **`src/move_mode.py`** - Main file containing the movement and highlighting logic
2. **`src/strand_drawing_canvas.py`** - Contains the canvas painting logic and normal paintEvent
3. **Sample logs** - Show the model the logs you provided to demonstrate the issue

## Key Code Locations to Focus On

In `move_mode.py`:

1. **Line ~2267**: Where strands are marked with `is_selected=True` 
2. **Line ~2269-2281**: Where optimized paint handler should be set up (this code isn't executing)
3. **Line ~420-440**: The optimized paint handler entry condition logic
4. **Line ~760-780**: The strand drawing logic that should handle both toggle states

## Summary for the Other Model

"The optimized paint handler setup code exists but isn't being executed after strand selection. The goal is to ensure that when toggle is OFF, both connected strands (1_1 and 1_2) are highlighted immediately when clicked, using the optimized paint handler instead of the normal paintEvent. The LayerStateManager correctly identifies the connections, and the selection logic works, but the drawing system isn't using the optimized path."