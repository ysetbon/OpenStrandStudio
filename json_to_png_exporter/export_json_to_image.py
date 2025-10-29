#!/usr/bin/env python
"""
Export OpenStrand Studio JSON files to PNG images using the actual MainWindow and canvas
Based on the proper approach that uses the real application rendering
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

# Add src directory to path (go up one level from json_to_png_exporter)
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import QSize, Qt
from PIL import Image

# Import the actual application modules
from main_window import MainWindow
from save_load_manager import load_strands, apply_loaded_strands

def suppress_qt_warnings():
    """Suppress Qt and logging warnings"""
    os.environ["QT_LOGGING_RULES"] = "*=false"
    os.environ['PYTHONWARNINGS'] = 'ignore'
    warnings.filterwarnings('ignore')
    
    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger('PyQt5').setLevel(logging.CRITICAL)
    logging.getLogger('LayerStateManager').setLevel(logging.CRITICAL)

def calculate_bounds(canvas):
    """Calculate the bounding box of all strands including stroke width and circles"""
    if not canvas.strands:
        return 0, 0, 800, 600
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for strand in canvas.strands:
        # Get the strand's full bounding rect if available
        if hasattr(strand, 'boundingRect'):
            rect = strand.boundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())
        
        # Also include all control points and endpoints with stroke width
        stroke_padding = getattr(strand, 'stroke_width', 5) * 2
        width_padding = getattr(strand, 'width', 46) / 2 + stroke_padding
        
        points = []
        if hasattr(strand, 'start'):
            points.append(strand.start)
        if hasattr(strand, 'end'):
            points.append(strand.end)
        if hasattr(strand, 'control_point1') and strand.control_point1:
            points.append(strand.control_point1)
        if hasattr(strand, 'control_point2') and strand.control_point2:
            points.append(strand.control_point2)
        if hasattr(strand, 'control_point_center') and strand.control_point_center:
            points.append(strand.control_point_center)
        
        for point in points:
            # Include padding for stroke width and circles
            min_x = min(min_x, point.x() - width_padding)
            min_y = min(min_y, point.y() - width_padding)
            max_x = max(max_x, point.x() + width_padding)
            max_y = max(max_y, point.y() + width_padding)
    
    # Ensure we have valid bounds
    if min_x == float('inf'):
        return 0, 0, 800, 600
    
    return min_x, min_y, max_x, max_y

def create_image(canvas, min_x, min_y, max_x, max_y):
    """Create an image from the canvas content without cropping"""
    # Add generous padding to ensure nothing is cut off
    padding = 200
    
    # Calculate the actual content size
    content_width = max_x - min_x
    content_height = max_y - min_y
    
    # Create an image large enough to fit everything with padding
    image_width = int(content_width + 2 * padding)
    image_height = int(content_height + 2 * padding)
    
    # Don't make it square - keep the actual aspect ratio to avoid unnecessary whitespace
    # But ensure minimum size
    image_width = max(image_width, 800)
    image_height = max(image_height, 600)
    
    # Create image with white background (transparent can be changed if needed)
    image = QImage(QSize(image_width, image_height), QImage.Format_RGBA8888)
    image.fill(QColor(255, 255, 255, 255))  # White background
    
    # Create a painter with high-quality settings
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
    
    # Set color-preserving composition mode
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    
    # Calculate translation to position content with padding
    # This positions the content starting at (padding, padding)
    x_offset = padding - min_x
    y_offset = padding - min_y
    
    # Translate the painter to position the content
    painter.translate(x_offset, y_offset)
    
    # Set the canvas size to match the image
    canvas.setFixedSize(image_width, image_height)
    canvas.setStyleSheet("background-color: white;")
    
    # Reset zoom and pan to ensure everything is at 1:1 scale
    canvas.zoom_factor = 1.0
    canvas.pan_offset_x = 0
    canvas.pan_offset_y = 0
    
    # Render the canvas onto the image
    canvas.render(painter)
    painter.end()
    
    return image

def save_image(image, output_path):
    """Save the image without aggressive cropping"""
    # Create the directory path if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Convert QImage to PIL Image
    buffer = image.bits().asstring(image.width() * image.height() * 4)
    img = Image.frombytes('RGBA', (image.width(), image.height()), buffer)
    
    # Find the bounds of non-transparent/non-white content
    # Convert to RGB to check for white background
    img_rgb = img.convert('RGB')
    # Get bounding box of non-white pixels
    bbox = None
    width, height = img.size
    
    # Find actual content bounds (non-white pixels)
    left, top, right, bottom = width, height, 0, 0
    pixels = img_rgb.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # Check if pixel is not white (with some tolerance)
            if not (r > 250 and g > 250 and b > 250):
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    
    if right > left and bottom > top:
        # Add small padding around content
        padding = 30
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(width, right + padding)
        bottom = min(height, bottom + padding)
        
        # Crop to content with padding
        img = img.crop((left, top, right, bottom))
    
    # Save as PNG
    img.save(output_path, 'PNG')
    print(f"  Saved: {output_path}")
    print(f"  Final size: {img.size}")

def process_json_file(json_path, output_path):
    """Process a single JSON file and export as PNG"""
    
    # Set QT_QPA_PLATFORM to offscreen to prevent window from showing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    
    # Create or get QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create MainWindow
    main_window = MainWindow()
    canvas = main_window.canvas
    
    # Hide all windows
    main_window.hide()
    canvas.hide()
    
    # Ensure we're in select mode (not attach mode or any other mode)
    # This prevents attach mode visual indicators from appearing
    if hasattr(canvas, 'select_mode'):
        canvas.current_mode = canvas.select_mode
    elif hasattr(main_window, 'set_select_mode'):
        main_window.set_select_mode()
    
    try:
        print(f"\nLoading: {json_path}")
        
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
                return False
        else:
            # Regular JSON file
            strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points, shadow_overrides = load_strands(json_path, canvas)

        # Apply loaded strands to canvas
        apply_loaded_strands(canvas, strands, groups, shadow_overrides)
        
        # Check if any strand has a control_point_center and enable third control point if so
        has_third_control_point = False
        for strand in canvas.strands:
            if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                has_third_control_point = True
                break
        
        # Enable third control point if needed
        if has_third_control_point:
            canvas.enable_third_control_point = True
            print(f"  Third control point: Enabled")
        
        # Configure canvas display settings
        canvas.show_grid = False
        canvas.show_control_points = show_control_points  # Use loaded setting
        canvas.shadow_enabled = shadow_enabled  # Use loaded setting
        
        # Ensure attach mode is not active
        if hasattr(canvas, 'attach_mode') and canvas.current_mode == canvas.attach_mode:
            # Switch to select mode
            if hasattr(canvas, 'select_mode'):
                canvas.current_mode = canvas.select_mode
        
        # Disable any attach mode visual indicators
        if hasattr(canvas, 'is_attaching'):
            canvas.is_attaching = False
        if hasattr(canvas, 'attach_preview_strand'):
            canvas.attach_preview_strand = None
        
        # Update all strands
        for strand in canvas.strands:
            strand.should_draw_shadow = shadow_enabled
        
        print(f"  Loaded {len(canvas.strands)} strands")
        print(f"  Control points: {show_control_points}")
        print(f"  Shadow enabled: {shadow_enabled}")
        
        # Calculate bounds and create image
        min_x, min_y, max_x, max_y = calculate_bounds(canvas)
        print(f"  Content bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
        
        image = create_image(canvas, min_x, min_y, max_x, max_y)
        save_image(image, output_path)
        
        return True
        
    except Exception as e:
        print(f"\nError processing {os.path.basename(json_path)}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to export JSON files"""
    suppress_qt_warnings()
    
    # Test files to process
    test_files = [
        ('test_shapes/v_shape.json', 'output/v_shape_export.png'),
        ('test_shapes/another_s_shape.json', 'output/s_shape_export.png'),
        ('test_shapes/test_s_shape.json', 'output/test_s_shape_export.png'),
    ]
    
    print("OpenStrand Studio JSON to PNG Export")
    print("=" * 50)
    
    for json_file, output_file in test_files:
        json_path = os.path.join(os.path.dirname(__file__), json_file)
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        
        if not os.path.exists(json_path):
            print(f"\nSkipping {json_file} - file not found")
            continue
        
        process_json_file(json_path, output_path)
    
    print("\n" + "=" * 50)
    print("Export complete!")

if __name__ == "__main__":
    main()