#!/usr/bin/env python3
"""
Test script to understand and verify the control point locking behavior.

This test demonstrates:
1. Creating a strand and attached strand
2. Manually moving the center control point of the attached strand
3. Then dragging an endpoint of the attached strand
4. Checking if the center stays in place
"""

import sys
import logging
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import the classes we need
from strand import Strand
from attached_strand import AttachedStrand

def test_control_point_locking():
    """Test the control point locking behavior step by step."""
    
    print("=== Control Point Locking Test ===\n")
    
    # Step 1: Create a parent strand
    print("1. Creating parent strand...")
    parent_strand = Strand(
        start=QPointF(100, 100),
        end=QPointF(200, 100),
        width=20,
        color=QColor(255, 0, 0),  # Red
        stroke_color=QColor(0, 0, 0),  # Black
        stroke_width=2
    )
    print(f"   Parent strand: start={parent_strand.start}, end={parent_strand.end}")
    
    # Step 2: Create an attached strand
    print("\n2. Creating attached strand...")
    attached_strand = AttachedStrand(
        parent=parent_strand,
        start_point=QPointF(150, 100),  # Midpoint of parent
        attachment_side='top'
    )
    
    # Give it some length to work with
    attached_strand.end = QPointF(150, 50)  # Point upward
    attached_strand.update_end()
    attached_strand.update_control_points()
    
    print(f"   Attached strand: start={attached_strand.start}, end={attached_strand.end}")
    print(f"   Initial center_locked: {attached_strand.control_point_center_locked}")
    print(f"   Initial center position: {attached_strand.control_point_center}")
    
    # Step 3: Manually move the center control point (simulating user drag)
    print("\n3. Manually moving center control point...")
    original_center = QPointF(attached_strand.control_point_center)
    new_center_position = QPointF(170, 75)  # Move it to the right and down
    
    # This simulates what happens in move_mode.py when dragging the center control point
    attached_strand.control_point_center = new_center_position
    attached_strand.control_point_center_locked = True  # This should lock it
    
    print(f"   Center moved from {original_center} to {new_center_position}")
    print(f"   Center locked: {attached_strand.control_point_center_locked}")
    
    # Step 4: Now drag an endpoint (simulating user dragging endpoint)
    print("\n4. Dragging endpoint to simulate the problematic scenario...")
    original_end = QPointF(attached_strand.end)
    new_end_position = QPointF(150, 30)  # Move end point further up
    
    # Store the locked center position to verify it stays put
    locked_center_position = QPointF(attached_strand.control_point_center)
    
    # This simulates what happens when dragging an endpoint
    attached_strand.end = new_end_position
    attached_strand.update_end()
    
    # The key question: does update_control_points preserve the locked center?
    print(f"   End moved from {original_end} to {new_end_position}")
    print(f"   Center position before update_control_points: {locked_center_position}")
    
    # This is where the problem might occur
    attached_strand.update_control_points()
    
    print(f"   Center position after update_control_points: {attached_strand.control_point_center}")
    print(f"   Center still locked: {attached_strand.control_point_center_locked}")
    
    # Step 5: Analyze the results
    print("\n5. Analysis:")
    center_preserved = (attached_strand.control_point_center == locked_center_position)
    print(f"   Center position preserved: {center_preserved}")
    
    if center_preserved:
        print("   ✓ SUCCESS: Center control point stayed in place after endpoint drag")
    else:
        print("   ✗ PROBLEM: Center control point moved when it should have stayed locked")
        print(f"     Expected: {locked_center_position}")
        print(f"     Actual:   {attached_strand.control_point_center}")
    
    return center_preserved

def compare_strand_vs_attached_strand():
    """Compare the behavior between Strand and AttachedStrand classes."""
    
    print("\n=== Comparing Strand vs AttachedStrand ===\n")
    
    # Test regular Strand
    print("Testing regular Strand:")
    strand = Strand(
        start=QPointF(100, 100),
        end=QPointF(200, 100),
        width=20
    )
    strand.update_control_points()
    
    # Manually position and lock center
    strand.control_point_center = QPointF(170, 80)
    strand.control_point_center_locked = True
    locked_center = QPointF(strand.control_point_center)
    
    # Move endpoint and update
    strand.end = QPointF(250, 100)
    strand.update_control_points()
    
    strand_preserved = (strand.control_point_center == locked_center)
    print(f"   Center preserved: {strand_preserved}")
    
    # Test AttachedStrand
    print("\nTesting AttachedStrand:")
    parent = Strand(QPointF(0, 0), QPointF(100, 0), 20)
    attached = AttachedStrand(parent, QPointF(50, 0), 'top')
    attached.end = QPointF(50, -50)
    attached.update_control_points()
    
    # Manually position and lock center
    attached.control_point_center = QPointF(70, -25)
    attached.control_point_center_locked = True
    locked_center_attached = QPointF(attached.control_point_center)
    
    # Move endpoint and update
    attached.end = QPointF(50, -80)
    attached.update_control_points()
    
    attached_preserved = (attached.control_point_center == locked_center_attached)
    print(f"   Center preserved: {attached_preserved}")
    
    print(f"\nComparison:")
    print(f"   Strand preserves locked center: {strand_preserved}")
    print(f"   AttachedStrand preserves locked center: {attached_preserved}")
    
    if strand_preserved and not attached_preserved:
        print("   ✗ ISSUE: AttachedStrand doesn't preserve locked center like Strand does")
    elif strand_preserved and attached_preserved:
        print("   ✓ Both classes preserve locked center correctly")
    else:
        print("   ✗ Neither class preserves locked center (unexpected)")

if __name__ == "__main__":
    # Run the main test
    success = test_control_point_locking()
    
    # Run the comparison test
    compare_strand_vs_attached_strand()
    
    print(f"\n=== Test Summary ===")
    print(f"Main test {'PASSED' if success else 'FAILED'}")
    
    if not success:
        print("\nThis confirms the issue: AttachedStrand is not preserving the locked center control point")
        print("when endpoints are dragged, even though it should behave like the regular Strand class.")