"""
Batch generator for all MxN patterns (1x1 to 10x10)
Generates preview images, continuation images (with/without markers), and JSON files.
"""

import os
import sys
import json
import tempfile

# Suppress warnings and logging
import warnings
import logging
logging.basicConfig(level=logging.CRITICAL)
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ["QT_LOGGING_RULES"] = "*=false"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, QRectF

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
src_dir = os.path.join(root_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import generators
from mxn_lh_strech import generate_json as generate_lh_stretch_json
from mxn_rh_stretch import generate_json as generate_rh_stretch_json
from mxn_lh_continuation import generate_json as generate_lh_continuation_json
from mxn_rh_continuation import generate_json as generate_rh_continuation_json
from mxn_emoji_renderer import EmojiRenderer

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(script_dir), "mxn_output")
BOUNDS_PADDING = 100
SCALE_FACTOR = 4.0


class BatchGenerator:
    def __init__(self):
        self._main_window = None
        self._emoji_renderer = EmojiRenderer()

    def _get_main_window(self):
        """Get or create MainWindow instance."""
        if self._main_window is None:
            from main_window import MainWindow
            self._main_window = MainWindow()
            self._main_window.hide()
            self._main_window.canvas.hide()
        return self._main_window

    def _calculate_bounds(self, canvas):
        """Calculate bounding box of all strands."""
        if not canvas.strands:
            return QRectF(0, 0, 1200, 900)

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
                max_x = max(max_x, point.x())
                min_y = min(min_y, point.y())
                max_y = max(max_y, point.y())

        return QRectF(min_x - BOUNDS_PADDING, min_y - BOUNDS_PADDING,
                      max_x - min_x + 2*BOUNDS_PADDING, max_y - min_y + 2*BOUNDS_PADDING)

    def _load_json_to_canvas(self, json_content):
        """Load JSON content into canvas."""
        from save_load_manager import load_strands, apply_loaded_strands

        main_window = self._get_main_window()
        canvas = main_window.canvas

        # Clear canvas
        canvas.strands = []
        canvas.strand_colors = {}
        canvas.selected_strand = None
        canvas.current_strand = None

        # Parse JSON
        data = json.loads(json_content)

        if data.get('type') == 'OpenStrandStudioHistory':
            current_step = data.get('current_step', 1)
            states = data.get('states', [])
            current_data = None
            for state in states:
                if state['step'] == current_step:
                    current_data = state['data']
                    break
            if not current_data:
                return None
        else:
            current_data = data

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(current_data, tmp)
            temp_path = tmp.name

        try:
            strands, groups, _, _, _, _, _, shadow_overrides = load_strands(temp_path, canvas)
        finally:
            os.unlink(temp_path)

        apply_loaded_strands(canvas, strands, groups, shadow_overrides)

        # Configure canvas
        canvas.show_grid = False
        canvas.show_control_points = False
        canvas.shadow_enabled = False
        canvas.should_draw_names = False

        for strand in canvas.strands:
            strand.should_draw_shadow = False

        return self._calculate_bounds(canvas)

    def _render_image(self, bounds, m, n, emoji_settings):
        """Render image from current canvas state."""
        from render_utils import RenderUtils

        main_window = self._get_main_window()
        canvas = main_window.canvas

        image_width = int(bounds.width() * SCALE_FACTOR)
        image_height = int(bounds.height() * SCALE_FACTOR)
        image = QImage(image_width, image_height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)  # Non-transparent background

        painter = QPainter(image)
        RenderUtils.setup_painter(painter, enable_high_quality=True)
        painter.scale(SCALE_FACTOR, SCALE_FACTOR)
        painter.translate(-bounds.x(), -bounds.y())

        for strand in canvas.strands:
            strand.draw(painter, skip_painter_setup=True)

        if canvas.current_strand:
            canvas.current_strand.draw(painter, skip_painter_setup=True)

        # Draw emojis if enabled
        self._emoji_renderer.draw_endpoint_emojis(painter, canvas, bounds, m, n, emoji_settings)
        self._emoji_renderer.draw_rotation_indicator(painter, bounds, emoji_settings, SCALE_FACTOR)

        painter.end()
        return image

    def generate_pattern(self, m, n, k, direction, pattern_type, output_folder):
        """Generate all outputs for a single pattern configuration."""
        print(f"  Generating {pattern_type}_{m}x{n}_k{k}_{direction}...")

        base_name = f"{pattern_type}_{m}x{n}_{k}_{direction}"

        # Create subfolder for this pattern
        pattern_folder = os.path.join(output_folder, base_name)
        os.makedirs(pattern_folder, exist_ok=True)

        try:
            # 1. Generate base/preview (stretch pattern)
            if pattern_type == "lh":
                base_json = generate_lh_stretch_json(m, n)
            else:
                base_json = generate_rh_stretch_json(m, n)

            bounds = self._load_json_to_canvas(base_json)
            if bounds is None:
                print(f"    ERROR: Failed to load base pattern")
                return False

            emoji_settings = {
                "show": True,
                "show_strand_names": False,
                "k": k,
                "direction": direction,
                "transparent": False,
            }

            # Export preview image with markers
            image = self._render_image(bounds, m, n, emoji_settings)
            preview_path = os.path.join(pattern_folder, f"{base_name}_starting_position.png")
            image.save(preview_path)

            # 2. Generate continuation pattern (_4, _5)
            if pattern_type == "lh":
                cont_json = generate_lh_continuation_json(m, n, k, direction)
            else:
                cont_json = generate_rh_continuation_json(m, n, k, direction)

            bounds = self._load_json_to_canvas(cont_json)
            if bounds is None:
                print(f"    ERROR: Failed to load continuation pattern")
                return False

            # Export continuation with markers
            image = self._render_image(bounds, m, n, emoji_settings)
            cont_path = os.path.join(pattern_folder, f"{base_name}_continuation_emojis.png")
            image.save(cont_path)

            # Export continuation without markers
            emoji_settings["show"] = False
            image = self._render_image(bounds, m, n, emoji_settings)
            cont_nm_path = os.path.join(pattern_folder, f"{base_name}_continuation_no_emojis.png")
            image.save(cont_nm_path)

            # Export JSON
            json_path = os.path.join(pattern_folder, f"{base_name}_continuation.json")
            with open(json_path, 'w') as f:
                f.write(cont_json)

            return True

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_k_values(self, m, n):
        """Get list of k values for given m, n."""
        if m == n:
            # Square: 2m values from -(m-1) to m
            return list(range(-(m-1), m+1))
        else:
            # Non-square: 2(m+n) values from -(m+n-1) to (m+n)
            return list(range(-(m+n-1), (m+n)+1))

    def run(self, m_range=range(1, 11), n_range=range(1, 11)):
        """Run batch generation for all patterns."""
        total_generated = 0
        total_errors = 0

        for m in m_range:
            for n in n_range:
                folder = os.path.join(OUTPUT_DIR, f"{m}x{n}")
                os.makedirs(folder, exist_ok=True)

                k_values = self.get_k_values(m, n)
                print(f"\n=== {m}x{n} ({len(k_values)} k values: {k_values[0]} to {k_values[-1]}) ===")

                if m == n:
                    # Square grid: LH with CW, RH with CCW
                    for k in k_values:
                        if self.generate_pattern(m, n, k, "cw", "lh", folder):
                            total_generated += 1
                        else:
                            total_errors += 1

                        if self.generate_pattern(m, n, k, "ccw", "rh", folder):
                            total_generated += 1
                        else:
                            total_errors += 1
                else:
                    # Non-square: both LH and RH with both CW and CCW
                    for k in k_values:
                        for pattern_type in ["lh", "rh"]:
                            for direction in ["cw", "ccw"]:
                                if self.generate_pattern(m, n, k, direction, pattern_type, folder):
                                    total_generated += 1
                                else:
                                    total_errors += 1

        print(f"\n=== COMPLETE ===")
        print(f"Generated: {total_generated}")
        print(f"Errors: {total_errors}")
        return total_generated, total_errors


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    generator = BatchGenerator()

    # Run for all 1x1 to 10x10
    generator.run()


if __name__ == "__main__":
    main()
