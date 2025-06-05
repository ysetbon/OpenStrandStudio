"""
Debug script to test strand movement and identify jump issues
"""

import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath

def test_selection_area_issue():
    """Test the issue with selection area center vs click position"""
    
    # Simulate a strand at position (100, 100)
    strand_pos = QPointF(100, 100)
    
    # Create a 120x120 selection area centered on the strand
    selection_size = 120
    half_size = selection_size / 2
    selection_rect = QRectF(
        strand_pos.x() - half_size,
        strand_pos.y() - half_size,
        selection_size,
        selection_size
    )
    
    # Simulate clicking near the edge of the selection area
    # When zoomed out, this is a common scenario
    click_pos = QPointF(strand_pos.x() + 40, strand_pos.y() + 40)  # 40 pixels away from strand
    
    # Old method: using selection area center
    area_center = selection_rect.center()
    old_offset = QPointF(strand_pos.x() - area_center.x(), 
                        strand_pos.y() - area_center.y())
    
    # New method: using actual click position
    new_offset = QPointF(strand_pos.x() - click_pos.x(), 
                        strand_pos.y() - click_pos.y())
    
    print("=== Selection Area Issue Test ===")
    print(f"Strand position: {strand_pos}")
    print(f"Selection area: {selection_rect}")
    print(f"Area center: {area_center}")
    print(f"Click position: {click_pos}")
    print(f"Old offset (using area center): {old_offset}")
    print(f"New offset (using click pos): {new_offset}")
    print(f"Distance from click to strand: {((click_pos.x() - strand_pos.x())**2 + (click_pos.y() - strand_pos.y())**2)**0.5:.2f}")
    
    # Simulate first mouse move
    first_move_pos = QPointF(click_pos.x() + 5, click_pos.y() + 5)  # Small movement
    
    # Calculate adjusted positions
    old_adjusted = QPointF(first_move_pos.x() + old_offset.x(), 
                          first_move_pos.y() + old_offset.y())
    new_adjusted = QPointF(first_move_pos.x() + new_offset.x(), 
                          first_move_pos.y() + new_offset.y())
    
    print("\n=== First Mouse Move ===")
    print(f"Mouse moved to: {first_move_pos}")
    print(f"Old adjusted position: {old_adjusted}")
    print(f"New adjusted position: {new_adjusted}")
    print(f"Jump with old method: {((old_adjusted.x() - strand_pos.x())**2 + (old_adjusted.y() - strand_pos.y())**2)**0.5:.2f}")
    print(f"Jump with new method: {((new_adjusted.x() - strand_pos.x())**2 + (new_adjusted.y() - strand_pos.y())**2)**0.5:.2f}")

def test_zoom_factor_issue(zoom_factor=0.5):
    """Test how zoom affects the selection areas and movement"""
    
    # Simulate a strand at position (200, 200)
    strand_pos = QPointF(200, 200)
    
    # Base selection size
    base_size = 120
    
    # Old method: fixed size
    old_size = base_size
    old_rect = QRectF(
        strand_pos.x() - old_size / 2,
        strand_pos.y() - old_size / 2,
        old_size,
        old_size
    )
    
    # New method: scaled by zoom
    new_size = base_size / zoom_factor
    new_rect = QRectF(
        strand_pos.x() - new_size / 2,
        strand_pos.y() - new_size / 2,
        new_size,
        new_size
    )
    
    print(f"\n=== Zoom Factor Test (zoom={zoom_factor}) ===")
    print(f"Strand position: {strand_pos}")
    print(f"Old selection size: {old_size}x{old_size}")
    print(f"New selection size: {new_size}x{new_size}")
    print(f"Old selection rect: {old_rect}")
    print(f"New selection rect: {new_rect}")
    
    # Test clicking at the same visual distance when zoomed out
    visual_distance = 30  # pixels on screen
    canvas_distance_old = visual_distance  # Old method doesn't account for zoom
    canvas_distance_new = visual_distance / zoom_factor  # New method scales with zoom
    
    click_pos_old = QPointF(strand_pos.x() + canvas_distance_old, 
                           strand_pos.y() + canvas_distance_old)
    click_pos_new = QPointF(strand_pos.x() + canvas_distance_new, 
                           strand_pos.y() + canvas_distance_new)
    
    print(f"\nClicking {visual_distance} screen pixels away from strand:")
    print(f"Old method would miss at: {click_pos_old} (in selection: {old_rect.contains(click_pos_old)})")
    print(f"New method would hit at: {click_pos_new} (in selection: {new_rect.contains(click_pos_new)})")

if __name__ == "__main__":
    test_selection_area_issue()
    test_zoom_factor_issue(0.5)
    test_zoom_factor_issue(0.3)
    test_zoom_factor_issue(2.0)