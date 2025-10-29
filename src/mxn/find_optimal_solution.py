import os
import sys
import json
import shutil
import warnings
from pathlib import Path

# Add the src directory to Python path
src_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src"
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Now we can import the local modules
from main_window import MainWindow
from save_load_manager import load_strands, apply_loaded_strands

# Suppress all warnings and logging
warnings.filterwarnings('ignore')
os.environ["QT_LOGGING_RULES"] = "*=false"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, Qt
from PIL import Image

def get_max_extension(strands):
    max_extension = 0
    for strand in strands:
        if '_4' in strand['layer_name'] or '_5' in strand['layer_name']:
            extension = abs(strand['end']['x'] - strand['start']['x']) if strand['end']['x'] != strand['start']['x'] else abs(strand['end']['y'] - strand['start']['y'])
            max_extension = max(max_extension, extension)
    return max_extension

def find_optimal_solution(base_dir, m, n):
    min_extension = float('inf')
    optimal_file = None
    input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
    
    for file in os.listdir(input_dir):
        if file.endswith('_extended.json'):
            file_path = os.path.join(input_dir, file)
            with open(file_path, 'r') as f:
                data = json.load(f)
            max_extension = get_max_extension(data['strands'])
            if max_extension < min_extension:
                min_extension = max_extension
                optimal_file = file_path
    
    return optimal_file, min_extension

def process_optimal_solution_image(json_path, output_path):
    app = QApplication(sys.argv)
    main_window = MainWindow()
    canvas = main_window.canvas

    # Hide all windows
    main_window.hide()
    canvas.hide()

    try:
        strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points, shadow_overrides = load_strands(json_path, canvas)
        apply_loaded_strands(canvas, strands, groups, shadow_overrides)

        canvas.show_grid = False
        canvas.show_control_points = False

        # Calculate bounds
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for strand in canvas.strands:
            points = [strand.start, strand.end]
            if hasattr(strand, 'control_point1') and strand.control_point1:
                points.append(strand.control_point1)
            if hasattr(strand, 'control_point2') and strand.control_point2:
                points.append(strand.control_point2)

            for point in points:
                min_x = min(min_x, point.x())
                min_y = min(min_y, point.y())
                max_x = max(max_x, point.x())
                max_y = max(max_y, point.y())

        # Create and save image
        padding = 1000
        width = int(max_x - min_x + 2 * padding)
        height = int(max_y - min_y + 2 * padding)
        size = max(width, height)

        image = QImage(QSize(size, size), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        x_offset = (size - width) / 2 + padding - min_x
        y_offset = (size - height) / 2 + padding - min_y
        painter.translate(x_offset, y_offset)

        canvas.setFixedSize(size, size)
        canvas.setStyleSheet("background-color: transparent;")
        canvas.render(painter)
        painter.end()

        # Convert and save image
        buffer = image.bits().asstring(image.width() * image.height() * 4)
        img = Image.frombytes('RGBA', (image.width(), image.height()), buffer)

        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
            padding = 50
            width, height = img.size
            max_dim = max(width, height) + (padding * 2)

            new_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
            paste_x = (max_dim - width) // 2
            paste_y = (max_dim - height) // 2
            new_img.paste(img, (paste_x, paste_y), img)
            new_img.save(output_path)

        return True

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()

def summarize_results(directory):
    summary = []
    for file in os.listdir(directory):
        if file.endswith('.json'):
            file_path = os.path.join(directory, file)
            with open(file_path, 'r') as f:
                data = json.load(f)
            max_extension = get_max_extension(data['strands'])
            summary.append({
                'file': file,
                'max_extension': max_extension
            })
    return summary

def main():
    # Use the exact path provided
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    print(f"Using base directory: {base_dir}")
    
    n_values = [1,2,3,4]
    m_values = [1]
    
    # Create a directory for all optimal solutions
    all_optimal_solutions_dir = os.path.join(base_dir, "all_optimal_solutions")
    os.makedirs(all_optimal_solutions_dir, exist_ok=True)
    
    for m in m_values:
        for n in n_values:
            print(f"\nProcessing configuration m={m}, n={n}:")
            
            # Find optimal solution
            optimal_file, min_extension = find_optimal_solution(base_dir, m, n)
            
            if optimal_file:
                output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation", "optimal_solution")
                os.makedirs(output_dir, exist_ok=True)
                
                # Save optimal JSON file
                output_json = os.path.join(output_dir, os.path.basename(optimal_file))
                shutil.copy2(optimal_file, output_json)
                print(f"Optimal solution saved: {os.path.basename(optimal_file)}")
                print(f"Maximum extension: {min_extension}")
                
                # Create and save image
                output_image = output_json.replace('.json', '.png')
                if process_optimal_solution_image(output_json, output_image):
                    print(f"Image created successfully: {os.path.basename(output_image)}")
                else:
                    print("Failed to create image")
                
                # Copy JSON and PNG to all_optimal_solutions directory
                shutil.copy2(output_json, all_optimal_solutions_dir)
                shutil.copy2(output_image, all_optimal_solutions_dir)
            else:
                print("No optimal solution found")

    # Summarize results
    summary = summarize_results(all_optimal_solutions_dir)
    for result in summary:
        print(f"File: {result['file']}, Max Extension: {result['max_extension']}")

if __name__ == "__main__":
    main()