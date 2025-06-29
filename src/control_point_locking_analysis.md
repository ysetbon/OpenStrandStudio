# Control Point Locking System Analysis

## Summary of the Issue

The control point locking system in this application has an **inconsistency between `Strand` and `AttachedStrand` classes** that causes the center control point to not be preserved properly in attached strands.

## How the System Should Work

1. **Initial State**: When you create an AttachedStrand, `control_point_center_locked = False`
2. **Manual Positioning**: When you manually drag the center control point, `control_point_center_locked = True` 
3. **Preservation**: After the center is locked, it should be preserved when dragging strand endpoints

## The Problem: Code Inconsistency

### Strand Class (Working Correctly)
```python
def update_control_points_from_geometry(self):
    # ... update control_point1 and control_point2 ...
    
    # Update the center control point ONLY if it's not locked
    if not self.control_point_center_locked:
        self.control_point_center = QPointF(
            (self.control_point1.x() + self.control_point2.x()) / 2,
            (self.control_point1.y() + self.control_point2.y()) / 2
        )
        # Don't change the lock status - preserve whatever it was
```

### AttachedStrand Class (Broken)
```python
def update_control_points_from_geometry(self):
    # ... update control_point1 and control_point2 ...
    
    # Update the center control point as the midpoint between control_point1 and control_point2
    # Reset the lock status since we're recalculating from geometry  <-- PROBLEM!
    self.control_point_center = QPointF(
        (self.control_point1.x() + self.control_point2.x()) / 2,
        (self.control_point1.y() + self.control_point2.y()) / 2
    )
```

## The Bug

**AttachedStrand is missing the crucial `if not self.control_point_center_locked:` check.**

This means:
- Even when the center control point has been manually positioned and locked
- The `update_control_points_from_geometry()` method **always** recalculates and overwrites the center position
- The locked center position is lost when endpoints are dragged

## Test Scenario to Reproduce

1. **Create** a strand and attached strand
2. **Manually move** the center control point of the attached strand (this sets `control_point_center_locked = True`)
3. **Drag an endpoint** of the attached strand
4. **Observe**: The center control point jumps back to the calculated midpoint, ignoring the manual positioning

## Expected vs Actual Behavior

### Expected (like Strand class):
- Center stays at manually positioned location
- `control_point_center_locked` remains `True`
- Strand shape preserves the custom center curve

### Actual (AttachedStrand bug):
- Center jumps back to calculated midpoint
- Manual positioning is lost
- Custom curve shape is reset

## Impact

This bug affects user workflow by:
- Making it impossible to create custom curved shapes with attached strands
- Forcing users to repeatedly reposition the center control point
- Creating inconsistent behavior between regular strands and attached strands

## Solution Required

The `AttachedStrand.update_control_points_from_geometry()` method needs to be updated to match the `Strand` class behavior by adding the locked center check.