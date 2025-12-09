#!/usr/bin/env python
"""
Batch export MXN starting patterns to PNG images
Uses the OpenStrandStudio export functionality to convert all JSON files to images
Properly centers strands and uses the main window's save image logic
"""

import os
import sys
import logging
import warnings
import json

# Set up logging configuration before any other imports
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('LayerStateManager').disabled = True
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
os.environ["QT_LOGGING_RULES"] = "*=false"

# Add src directory to path
# Go up 3 levels: mxn_startings -> mxn -> cad_mxn -> OpenStrandStudio
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 3 levels: mxn_startings -> mxn -> cad_mxn -> OpenStrandStudio
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
src_dir = os.path.join(root_dir, 'src')
sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import QSize, Qt, QPointF

# Import the actual application modules
from main_window import MainWindow
from save_load_manager import load_strands, apply_loaded_strands
from render_utils import RenderUtils


def suppress_qt_warnings():
    """Suppress Qt and logging warnings"""
    os.environ["QT_LOGGING_RULES"] = "*=false"
    os.environ['PYTHONWARNINGS'] = 'ignore'
    warnings.filterwarnings('ignore')

    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger('PyQt5').setLevel(logging.CRITICAL)
    logging.getLogger('LayerStateManager').setLevel(logging.CRITICAL)


def save_canvas_as_image_to_file(main_window, filename):
    """
    Save the canvas as a PNG image - mirrors the main_window.save_canvas_as_image logic
    but saves directly to a file without dialog.
    """
    canvas = main_window.canvas

    # Ensure the filename ends with .png
    if not filename.lower().endswith('.png'):
        filename += '.png'

    # Get the size of the canvas
    canvas_size = canvas.size()

    # Create image 4x larger for maximum quality/crispness
    scale_factor = 4.0
    high_res_size = canvas_size * scale_factor

    # Create a transparent image at 4x resolution
    image = QImage(high_res_size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    # Create a painter for the image
    painter = QPainter(image)

    # Use the same high-quality settings as the canvas display
    RenderUtils.setup_painter(painter, enable_high_quality=True)

    # Scale everything up by 4x for high-resolution rendering
    painter.scale(scale_factor, scale_factor)

    # Apply zoom and pan transformation to match current canvas view
    canvas_center = QPointF(canvas_size.width() / 2, canvas_size.height() / 2)
    painter.translate(canvas_center)

    # Apply pan offset if it exists
    if hasattr(canvas, 'pan_offset_x') and hasattr(canvas, 'pan_offset_y'):
        painter.translate(canvas.pan_offset_x, canvas.pan_offset_y)

    # Apply zoom if it's not 1.0
    if hasattr(canvas, 'zoom_factor') and canvas.zoom_factor != 1.0:
        painter.scale(canvas.zoom_factor, canvas.zoom_factor)

    painter.translate(-canvas_center)

    # Draw all strands in their current order
    for strand in canvas.strands:
        if strand == canvas.selected_strand:
            canvas.draw_highlighted_strand(painter, strand)
        else:
            strand.draw(painter, skip_painter_setup=True)

    # Draw the current strand if it exists
    if canvas.current_strand:
        canvas.current_strand.draw(painter, skip_painter_setup=True)

    # End painting
    painter.end()

    # Create output directory if needed
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

    # Save the image
    image.save(filename)

    return image.size()


def process_json_file(json_path, output_path, main_window):
    """Process a single JSON file and export as PNG"""
    canvas = main_window.canvas

    # Clear existing strands
    canvas.strands = []
    canvas.strand_colors = {}
    canvas.selected_strand = None
    canvas.current_strand = None

    try:
        # Check if it's a history file or regular JSON
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Handle history format
        if data.get('type') == 'OpenStrandStudioHistory':
            # Get the current state from history
            current_step = data.get('current_step', 1)
            states = data.get('states', [])

            # Find the state with the current step
            current_data = None
            for state in states:
                if state['step'] == current_step:
                    current_data = state['data']
                    break

            if current_data:
                # Save to temp file for loading
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(current_data, tmp)
                    temp_path = tmp.name

                # Load from temp file
                strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points, shadow_overrides = load_strands(temp_path, canvas)

                # Clean up temp file
                os.unlink(temp_path)
            else:
                print(f"  Warning: Could not find step {current_step} in history")
                return False, 0, (0, 0)
        else:
            # Regular JSON file
            strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points, shadow_overrides = load_strands(json_path, canvas)

        # Apply loaded strands to canvas
        apply_loaded_strands(canvas, strands, groups, shadow_overrides)

        # Configure canvas display settings
        canvas.show_grid = False
        canvas.show_control_points = False  # Hide control points for cleaner export
        canvas.shadow_enabled = False  # Disable shadows for cleaner export
        canvas.should_draw_names = False  # Don't draw strand names

        # Disable any attach mode visual indicators
        if hasattr(canvas, 'is_attaching'):
            canvas.is_attaching = False
        if hasattr(canvas, 'attach_preview_strand'):
            canvas.attach_preview_strand = None

        # Update all strands shadow setting
        for strand in canvas.strands:
            strand.should_draw_shadow = False

        # Set canvas to a reasonable size
        canvas.setFixedSize(1200, 900)

        # Reset zoom to 1.0
        canvas.zoom_factor = 1.0

        # CENTER ALL STRANDS - This is the key step!
        canvas.center_all_strands()

        # Update the canvas
        canvas.update()

        # Process events to ensure canvas is fully updated
        QApplication.processEvents()

        # Save using the main window's save logic
        image_size = save_canvas_as_image_to_file(main_window, output_path)

        return True, len(canvas.strands), (image_size.width(), image_size.height())

    except Exception as e:
        print(f"\nError processing {os.path.basename(json_path)}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0, (0, 0)


def main():
    """Main function to export all MXN JSON files"""
    suppress_qt_warnings()

    # Set QT_QPA_PLATFORM to offscreen to prevent window from showing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create MainWindow
    main_window = MainWindow()
    main_window.hide()
    main_window.canvas.hide()

    print("=" * 60)
    print("  MXN Starting Patterns - Batch Export to PNG")
    print("=" * 60)

    # Define input/output directories
    base_dir = os.path.dirname(os.path.abspath(__file__))

    patterns = [
        ('mxn_lh', 'Left-Hand (LH)'),
        ('mxn_rh', 'Right-Hand (RH)')
    ]

    total_exported = 0

    for pattern_dir, pattern_name in patterns:
        input_dir = os.path.join(base_dir, pattern_dir)
        output_dir = os.path.join(input_dir, 'images')

        if not os.path.exists(input_dir):
            print(f"\n  Skipping {pattern_name} - directory not found: {input_dir}")
            continue

        os.makedirs(output_dir, exist_ok=True)

        print(f"\n  {pattern_name} Patterns")
        print("  " + "-" * 40)

        # Find all JSON files in the directory
        json_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.json')])

        for json_file in json_files:
            json_path = os.path.join(input_dir, json_file)
            output_file = json_file.replace('.json', '.png')
            output_path = os.path.join(output_dir, output_file)

            result = process_json_file(json_path, output_path, main_window)

            if result[0]:
                strands, size = result[1], result[2]
                print(f"    {json_file:20s} -> {output_file:20s} ({strands} strands, {size[0]}x{size[1]})")
                total_exported += 1
            else:
                print(f"    {json_file:20s} -> FAILED")

    print("\n" + "=" * 60)
    print(f"  Export complete! {total_exported} images generated.")
    print("=" * 60)

    # Print output locations
    for pattern_dir, pattern_name in patterns:
        output_dir = os.path.join(base_dir, pattern_dir, 'images')
        if os.path.exists(output_dir):
            print(f"\n  {pattern_name} images: {output_dir}")


if __name__ == "__main__":
    main()
