#!/usr/bin/env python3
"""
Test script for Curvature Bias Control feature
Run this to open a window with a test strand ready for experimentation
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

from strand_drawing_canvas import StrandDrawingCanvas
from attached_strand import AttachedStrand
from move_mode import MoveMode

def create_test_strand():
    """Create a test 1_1 strand with control points visible"""
    app = QApplication(sys.argv)
    
    # Create the main canvas
    canvas = StrandDrawingCanvas()
    
    # Enable the features we want to test
    canvas.show_control_points = True
    canvas.enable_third_control_point = True
    canvas.enable_curvature_bias_control = True
    
    # Set canvas properties
    canvas.setWindowTitle("Curvature Bias Control Test - Move the control points!")
    canvas.resize(800, 600)
    
    # Create a simple parent strand (dummy object for AttachedStrand)
    class DummyParent:
        def __init__(self):
            self.width = 46
            self.color = QColor(200, 170, 230, 255)  # Light purple
            self.stroke_color = QColor(0, 0, 0, 255)  # Black
            self.stroke_width = 4
            self.shadow_color = QColor(0, 0, 0, 150)
            self.set_number = 1
            self.layer_name = "Test_Strand_1"
            self.canvas = canvas
            self.control_point_base_fraction = 0.4
            self.distance_multiplier = 1.2
            self.curve_response_exponent = 1.5
    
    parent = DummyParent()
    
    # Create an attached strand (1_1 type strand)
    strand = AttachedStrand(
        parent=parent,
        start_point=QPointF(200, 300),
        attachment_side='right'
    )
    
    # Set up the strand
    strand.end = QPointF(600, 300)
    strand.length = 400
    
    # Position control points for a nice curve
    strand.control_point1 = QPointF(300, 200)  # Triangle - above
    strand.control_point2 = QPointF(500, 400)  # Circle - below
    
    # Position the center control point
    strand.control_point_center = QPointF(400, 300)
    strand.control_point_center_locked = True  # Lock it to enable bias controls
    
    # Make sure bias control is initialized
    from curvature_bias_control import CurvatureBiasControl
    if not hasattr(strand, 'bias_control') or strand.bias_control is None:
        strand.bias_control = CurvatureBiasControl(canvas)
    
    # Ensure the strand has proper update methods
    if not hasattr(strand, 'update_shape'):
        def update_shape():
            # Trigger path recalculation
            if hasattr(strand, '_create_path'):
                strand._create_path()
        strand.update_shape = update_shape
    
    if not hasattr(strand, 'update_side_line'):
        strand.update_side_line = lambda: None  # Stub for test
    
    # Add the strand to canvas
    canvas.strands.append(strand)
    canvas.selected_strand = strand
    strand.is_selected = True
    
    # Set up move mode for interaction
    move_mode = MoveMode(canvas)
    canvas.current_mode = move_mode
    canvas.setMouseTracking(True)
    
    # Override mousePressEvent to properly handle bias controls
    original_mouse_press = canvas.mousePressEvent
    def enhanced_mouse_press(event):
        # First check if we're clicking on bias controls
        if strand.bias_control:
            # Convert to canvas coordinates to match drawing space
            canvas_pos = canvas.screen_to_canvas(event.pos())
            new_event = type(event)(event.type(), canvas_pos, event.button(), event.buttons(), event.modifiers())
            triangle_pos, circle_pos = strand.bias_control.get_bias_control_positions(strand)
            if triangle_pos and circle_pos:
                triangle_rect = strand.bias_control.get_control_rect(triangle_pos)
                circle_rect = strand.bias_control.get_control_rect(circle_pos)
                # Debug prints removed for clean test
                
                if strand.bias_control.handle_mouse_press(new_event, strand):
                    # Start a MoveMode movement for the specific bias control to trigger yellow highlight
                    if hasattr(canvas, 'current_mode') and canvas.current_mode:
                        if triangle_rect.contains(canvas_pos):
                            canvas.current_mode.start_movement(strand, 'bias_triangle', triangle_rect, canvas_pos)
                        elif circle_rect.contains(canvas_pos):
                            canvas.current_mode.start_movement(strand, 'bias_circle', circle_rect, canvas_pos)
                        canvas.current_mode.is_moving_control_point = True
                        canvas.current_mode.is_moving_bias_control = True
                        canvas.current_mode.bias_control_strand = strand
                    canvas.is_moving_bias_control = True
                    canvas.bias_control_strand = strand
                    # Store initial bias values for tracking changes
                    canvas.initial_triangle_bias = strand.bias_control.triangle_bias
                    canvas.initial_circle_bias = strand.bias_control.circle_bias
                    # Debug positions
                    tp = strand.bias_control.triangle_position
                    cp = strand.bias_control.circle_position
                    # Initial positions stored
                    return
        # Otherwise use normal mouse press handling
        original_mouse_press(event)
    canvas.mousePressEvent = enhanced_mouse_press
    
    # Enable mouse tracking to receive move events
    canvas.setMouseTracking(True)
    
    # Create a flag to track bias dragging
    canvas.is_moving_bias_control = False
    
    # Override the actual widget mouseMoveEvent
    def mouseMoveEvent(self, event):
        # First check if we're dragging bias controls
        if self.is_moving_bias_control and hasattr(self, 'bias_control_strand'):
            if self.bias_control_strand and self.bias_control_strand.bias_control:
                # Convert to canvas coordinates and forward to MoveMode so it can draw yellow highlight
                canvas_pos = self.screen_to_canvas(event.pos())
                new_event = type(event)(event.type(), canvas_pos, event.button(), event.buttons(), event.modifiers())
                if hasattr(self, 'current_mode') and self.current_mode:
                    self.current_mode.mouseMoveEvent(new_event)
                else:
                    # Fallback
                    self.bias_control_strand.bias_control.handle_mouse_move(new_event, self.bias_control_strand)
                    self.bias_control_strand.update_shape()
                    self.bias_control_strand.update_side_line()
                    self.update()
                return
        
        # Call the original implementation
        type(self).mouseMoveEvent(self, event)
    
    # Bind the new mouseMoveEvent to the canvas instance
    import types
    canvas.mouseMoveEvent = types.MethodType(mouseMoveEvent, canvas)
    
    # Override mouseReleaseEvent to handle bias control release
    original_mouse_release = canvas.mouseReleaseEvent
    def enhanced_mouse_release(event):
        # Check if we're releasing bias controls
        if hasattr(canvas, 'is_moving_bias_control') and canvas.is_moving_bias_control:
            if hasattr(canvas, 'bias_control_strand') and canvas.bias_control_strand:
                # Convert to canvas coordinates for consistency
                canvas_pos = canvas.screen_to_canvas(event.pos())
                new_event = type(event)(event.type(), canvas_pos, event.button(), event.buttons(), event.modifiers())
                # Route to MoveMode so yellow->green flows identically to other controls
                if hasattr(canvas, 'current_mode') and canvas.current_mode:
                    canvas.current_mode.mouseReleaseEvent(new_event)
                else:
                    canvas.bias_control_strand.bias_control.handle_mouse_release(new_event)
            canvas.is_moving_bias_control = False
            canvas.bias_control_strand = None
            canvas.update()
            # Schedule an extra update to ensure paint pipeline flush
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, canvas.update)
            return
        # Otherwise use normal mouse release
        original_mouse_release(event)
    canvas.mouseReleaseEvent = enhanced_mouse_release
    
    # Add a timer to display bias values
    from PyQt5.QtCore import QTimer
    def show_bias_values():
        if strand.bias_control:
            triangle_bias = strand.bias_control.triangle_bias
            circle_bias = strand.bias_control.circle_bias
            triangle_weight, circle_weight = strand.bias_control.get_bias_weights()
            canvas.setWindowTitle(
                f"Bias Test | Triangle: {triangle_bias:.2f} ({triangle_weight:.2f}) | "
                f"Circle: {circle_bias:.2f} ({circle_weight:.2f})"
            )
    
    # Update title every 100ms
    bias_timer = QTimer()
    bias_timer.timeout.connect(show_bias_values)
    bias_timer.start(100)
    
    # Add keyboard shortcuts for testing
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QShortcut
    from PyQt5.QtGui import QKeySequence
    
    # Q/A keys for triangle bias
    def increase_triangle_bias():
        if strand.bias_control:
            strand.bias_control.triangle_bias = min(1.0, strand.bias_control.triangle_bias + 0.1)
            canvas.update()
    
    def decrease_triangle_bias():
        if strand.bias_control:
            strand.bias_control.triangle_bias = max(0.0, strand.bias_control.triangle_bias - 0.1)
            canvas.update()
    
    # W/S keys for circle bias
    def increase_circle_bias():
        if strand.bias_control:
            strand.bias_control.circle_bias = min(1.0, strand.bias_control.circle_bias + 0.1)
            canvas.update()
    
    def decrease_circle_bias():
        if strand.bias_control:
            strand.bias_control.circle_bias = max(0.0, strand.bias_control.circle_bias - 0.1)
            canvas.update()
    
    # R key to reset biases
    def reset_biases():
        if strand.bias_control:
            strand.bias_control.reset_biases()
            canvas.update()
    
    # Set up shortcuts
    QShortcut(QKeySequence("Q"), canvas, increase_triangle_bias)
    QShortcut(QKeySequence("A"), canvas, decrease_triangle_bias)
    QShortcut(QKeySequence("W"), canvas, increase_circle_bias)
    QShortcut(QKeySequence("S"), canvas, decrease_circle_bias)
    QShortcut(QKeySequence("R"), canvas, reset_biases)
    
    # Show instructions
    print("\n" + "="*60)
    print("CURVATURE BIAS CONTROL TEST")
    print("="*60)
    print("\nInstructions:")
    print("1. The strand has 3 control points visible:")
    print("   - Triangle (top) - control_point1")
    print("   - Circle (bottom) - control_point2")
    print("   - Square (center) - control_point_center")
    print("\n2. Move the center square to lock it (enables bias controls)")
    print("\n3. Once bias controls appear:")
    print("   - Small square with △ = Controls bias toward triangle point")
    print("   - Small square with ○ = Controls bias toward circle point")
    print("\n4. How to use bias controls:")
    print("   - Click and drag horizontally on the bias squares")
    print("   - Drag RIGHT = Increase bias (curve pulls more to that control)")
    print("   - Drag LEFT = Decrease bias (curve pulls less to that control)")
    print("   - Watch the window title for real-time bias values!")
    print("\n5. Effects on the curve:")
    print("   - High triangle bias = Tighter curve near triangle control point")
    print("   - High circle bias = Tighter curve near circle control point")
    print("   - Equal biases (0.5 each) = Symmetric curve")
    print("\nControls:")
    print("- Click and drag any control point to move it")
    print("- Click and drag bias control squares horizontally to adjust bias")
    print("\nKeyboard Shortcuts:")
    print("- Q/A = Increase/Decrease triangle bias")
    print("- W/S = Increase/Decrease circle bias")  
    print("- R = Reset biases to neutral (0.5 each)")
    print("="*60 + "\n")
    
    # Show the canvas
    canvas.show()
    
    # Force an update to draw everything
    canvas.update()
    
    return app, canvas

if __name__ == '__main__':
    app, canvas = create_test_strand()
    sys.exit(app.exec_())