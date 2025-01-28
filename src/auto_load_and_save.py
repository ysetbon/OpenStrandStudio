import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, Qt, QPoint, QRect
from PIL import Image
import cv2
import numpy as np

# Ensure the OpenStrand Studio source directory is in the Python path
sys.path.append(r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src")

# Import necessary classes from OpenStrand Studio
from main_window import MainWindow
from strand_drawing_canvas import StrandDrawingCanvas
from save_load_manager import load_strands, apply_loaded_strands

def load_json_and_save_png(json_file_path, output_png_path):
    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Create main window and canvas
    main_window = MainWindow()
    canvas = main_window.canvas

    try:
        # Load JSON data
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Load strands from data
        strands, groups = load_strands(json_file_path, canvas)
        apply_loaded_strands(canvas, strands, groups)

        # Turn off the grid and control points
        canvas.show_grid = False
        canvas.show_control_points = False

        # Calculate the bounding box of all strands
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for strand in canvas.strands:
            # Include control points in bounding box calculation
            points = [strand.start, strand.end]
            if strand.control_point1:
                points.append(strand.control_point1)
            if strand.control_point2:
                points.append(strand.control_point2)
            
            for point in points:
                min_x = min(min_x, point.x())
                min_y = min(min_y, point.y())
                max_x = max(max_x, point.x())
                max_y = max(max_y, point.y())

        # Add padding
        padding = 100
        width = int(max_x - min_x + 2 * padding)
        height = int(max_y - min_y + 2 * padding)

        # Make the image square by using the larger dimension
        size = max(width, height)
        
        # Create an image with transparent background (make it larger initially)
        image = QImage(QSize(size, size), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        # Create a painter to draw on the image
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate centering offsets
        x_offset = (size - width) / 2 + padding - min_x
        y_offset = (size - height) / 2 + padding - min_y
        
        # Translate the painter to center the content
        painter.translate(x_offset, y_offset)

        # Set the canvas size
        canvas.setFixedSize(size, size)
        canvas.setStyleSheet("background-color: transparent;")

        # Render the canvas
        canvas.render(painter)
        painter.end()

        # Crop transparent edges
        width = image.width()
        height = image.height()
        min_x = width
        min_y = height
        max_x = 0
        max_y = 0
        
        # Find the bounds of non-transparent pixels
        for y in range(height):
            for x in range(width):
                if image.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        # Add a small padding to the cropped image
        crop_padding = 50
        min_x = max(0, min_x - crop_padding)
        min_y = max(0, min_y - crop_padding)
        max_x = min(width, max_x + crop_padding)
        max_y = min(height, max_y + crop_padding)

        # Crop the image
        cropped_image = image.copy(QRect(min_x, min_y, max_x - min_x, max_y - min_y))

        # Save the cropped image
        cropped_image.save(output_png_path)
        print(f"Image saved to {output_png_path}")
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")

if __name__ == "__main__":
    # Directory containing JSON files
    json_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\all possible rh continulation twist offsets"
    
    # Output directory for PNG files
    output_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\all possible rh continulation twist images offsets"

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Create a list to store the PNG images
    png_images = []
    
    # Process all JSON files in the directory
    json_files = []
    for filename in os.listdir(json_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(json_directory, filename)
            # Get creation time and add to list as tuple
            creation_time = os.path.getctime(file_path)
            json_files.append((creation_time, file_path))
    
    # Sort files by creation time
    json_files.sort()  # This will sort based on creation_time
    
    # First pass: Export all images with padding
    temp_png_paths = []
    for _, json_path in json_files:
        filename = os.path.basename(json_path)
        png_path = os.path.join(output_directory, filename.replace(".json", ".png"))
        load_json_and_save_png(json_path, png_path)
        temp_png_paths.append(png_path)

    # Second pass: Find the content bounds for all images
    image_bounds = []
    max_content_width = 0
    max_content_height = 0

    for png_path in temp_png_paths:
        img = QImage(png_path)
        
        # Find content boundaries
        width = img.width()
        height = img.height()
        min_x = width
        min_y = height
        max_x = 0
        max_y = 0
        
        for y in range(height):
            for x in range(width):
                if img.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        max_content_width = max(max_content_width, content_width)
        max_content_height = max(max_content_height, content_height)
        
        image_bounds.append({
            'path': png_path,
            'bounds': (min_x, min_y, max_x, max_y),
            'center_x': min_x + content_width / 2,
            'center_y': min_y + content_height / 2
        })

    # Third pass: Create properly centered images
    padding = 100
    final_size = max(max_content_width, max_content_height) + (2 * padding)
    png_images = []

    for bounds_data in image_bounds:
        # Create new image with proper centering
        final_image = QImage(QSize(final_size, final_size), QImage.Format_ARGB32_Premultiplied)
        final_image.fill(Qt.transparent)
        
        # Load original image
        orig_image = QImage(bounds_data['path'])
        
        painter = QPainter(final_image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate offset to center this image's content
        x_offset = (final_size / 2) - bounds_data['center_x']
        y_offset = (final_size / 2) - bounds_data['center_y']
        
        # Draw the content centered
        painter.translate(x_offset, y_offset)
        min_x, min_y, max_x, max_y = bounds_data['bounds']
        source_rect = QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        painter.drawImage(source_rect, orig_image, source_rect)
        painter.end()
        
        # Save the centered image
        final_image.save(bounds_data['path'])
        
        # Convert to PIL Image with white background for GIF
        img = Image.open(bounds_data['path'])
        bg = Image.new('RGB', img.size, 'white')
        bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        png_images.append(bg)

    # Create GIF with existing duration settings
    if png_images:
        gif_path = os.path.join(output_directory, "animation.gif")
        durations = [1000] + [50] * (len(png_images) - 2) + [2000] if len(png_images) > 2 else [1000, 2000]
        
        png_images[0].save(
            gif_path,
            save_all=True,
            append_images=png_images[1:],
            duration=durations,
            loop=0,
            disposal=2
        )
        print(f"GIF created at {gif_path}")

    # Create MP4 from the PNG images
    if png_images:
        mp4_path = os.path.join(output_directory, "animation.mp4")
        
        # Get dimensions from first image
        first_frame = cv2.imread(temp_png_paths[0])
        height, width, _ = first_frame.shape
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(mp4_path, fourcc, 20.0, (width, height))
        
        # Write first frame for 1 second (20 frames at 20fps)
        for _ in range(20):
            out.write(first_frame)
            
        # Write middle frames
        for png_path in temp_png_paths[1:-1]:
            frame = cv2.imread(png_path)
            out.write(frame)
            
        # Write last frame for 2 seconds (40 frames at 20fps)
        last_frame = cv2.imread(temp_png_paths[-1])
        for _ in range(40):
            out.write(last_frame)
            
        out.release()
        print(f"MP4 created at {mp4_path}")

    print("All JSON files processed and images saved.")