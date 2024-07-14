# File: square_diagram_nxm.py

import matplotlib.pyplot as plt
import random
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe

def create_stroked_polygon(ax, x1, y1, x2, y2, width, stroke_width, fill_color, stroke_color):
    dx, dy = x2 - x1, y2 - y1
    angle = np.arctan2(dy, dx)
    x_shift = np.sin(angle) * width / 2
    y_shift = np.cos(angle) * width / 2

    coords = np.array([
        [x1 + x_shift, y1 - y_shift],
        [x1 - x_shift, y1 + y_shift],
        [x2 - x_shift, y2 + y_shift],
        [x2 + x_shift, y2 - y_shift]
    ])

    polygon = Polygon(coords, closed=True, facecolor=fill_color, edgecolor=stroke_color, lw=stroke_width)
    polygon.set_path_effects([pe.Stroke(linewidth=stroke_width, foreground=stroke_color), pe.Normal()])
    ax.add_patch(polygon)

def draw_square(ax, square_size, string_width, string_length, m, n, stroke_width, orientation='left', offset_x=0, offset_y=0):
    """
    Draw a square with strands on a given axis based on specified parameters and orientation.

    Parameters:
    - ax: The axis to draw the square on.
    - square_size: The size of each small square.
    - string_width: The width of the strands as a fraction of the square size.
    - string_length: The length of the strands as a fraction of the square size.
    - m: Number of columns.
    - n: Number of rows.
    - stroke_width: The width of the stroke (border) for the strands.
    - orientation: Orientation of strands, can be 'left' or 'right'.
    - offset_x: X-axis offset for centering the diagram.
    - offset_y: Y-axis offset for centering the diagram.
    """
    
    # Generate unique colors for each side of the square
    all_colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(4 * n + 4 * m)]
    bottom_colors = all_colors[:2 * m]
    left_colors = all_colors[2 * m:2 * m + 2 * n]
    top_colors = all_colors[2 * m + 2 * n:4 * m + 2 * n]
    right_colors = all_colors[4 * m + 2 * n:]

    # Draw small squares within the main square
    for i in range(2 * m):
        for j in range(2 * n):
            small_square = plt.Rectangle(
                (i * square_size + offset_x, j * square_size + offset_y), 
                square_size, square_size, facecolor='none', edgecolor='black', 
                linewidth=stroke_width, zorder=4
            )
            ax.add_patch(small_square)

    # Create a list of coordinates for the dots
    coordinates = []

    # Top coordinates
    for i in range(2 * m):
        dot_x = (i * square_size) + (square_size / 2) + offset_x
        coordinates.append((dot_x, offset_y))

    # Right coordinates
    for j in range(2 * n):
        dot_y = (j * square_size) + (square_size / 2) + offset_y
        coordinates.append((2 * m * square_size + offset_x, dot_y))

    # Bottom coordinates
    for i in range(2 * m, 0, -1):
        dot_x = (i * square_size) - (square_size / 2) + offset_x
        coordinates.append((dot_x, 2 * n * square_size + offset_y))

    # Left coordinates
    for j in range(2 * n, 0, -1):
        dot_y = (j * square_size) - (square_size / 2) + offset_y
        coordinates.append((offset_x, dot_y))

    # Draw strands for left-handed orientation
    if orientation == 'left':
        for index, (x, y) in enumerate(coordinates):
            if index % 2 == 0:
                color = all_colors[index]
                # Bottom colors
                if y == offset_y:
                    create_stroked_polygon(ax, x, y, x, y - string_length * 2 * square_size, string_width * square_size, stroke_width, color, 'black')
                # Right colors
                elif x == 2 * m * square_size + offset_x:
                    create_stroked_polygon(ax, x, y, x + string_length * 2 * square_size, y, string_width * square_size, stroke_width, color, 'black')
                # Left colors
                elif y == 2 * n * square_size + offset_y:
                    create_stroked_polygon(ax, x, y, x, y + string_length * 2 * square_size, string_width * square_size, stroke_width, color, 'black')
                # Top colors
                elif x == offset_x:
                    create_stroked_polygon(ax, x, y, x - string_length * 2 * square_size, y, string_width * square_size, stroke_width, color, 'black')

    # Draw strands for right-handed orientation
    elif orientation == 'right':
        for index, (x, y) in enumerate(coordinates):
            if index % 2 == 1:
                color = all_colors[index]
                # Bottom colors
                if y == offset_y:
                    create_stroked_polygon(ax, x, y, x, y - string_length * 2 * square_size, string_width * square_size, stroke_width, color, 'black')
                # Right colors
                elif x == 2 * m * square_size + offset_x:
                    create_stroked_polygon(ax, x, y, x + string_length * 2 * square_size, y, string_width * square_size, stroke_width, color, 'black')
                # Left colors
                elif y == 2 * n * square_size + offset_y:
                    create_stroked_polygon(ax, x, y, x, y + string_length * 2 * square_size, string_width * square_size, stroke_width, color, 'black')
                # Top colors
                elif x == offset_x:
                    create_stroked_polygon(ax, x, y, x - string_length * 2 * square_size, y, string_width * square_size, stroke_width, color, 'black')

    return top_colors, right_colors, bottom_colors, left_colors

def fill_small_squares(ax, square_size, m, n, color_array, orientation, offset_x=0, offset_y=0):
    if color_array is None:
        return  # Exit the function if color_array is None

    if orientation == 'left':
        # Fill the small squares based on the top_colors array
        for j in range(2, 2 * m + 1, 2):
            color = color_array['top'][2 * m - j]  # Get the color from the top row in the color array
            for i in range(0, 2 * n, 2):
                small_square = plt.Rectangle(((j - 1) * square_size + offset_x, i * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the bottom_colors array
        for j in range(1, 2 * m, 2):
            color = color_array['bottom'][j - 1]  # Get the color from the bottom row in the color array
            for i in range(0, 2 * n, 2):
                small_square = plt.Rectangle(((j - 1) * square_size + offset_x, (i + 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the left_colors array
        for j in range(1, 2 * n + 1, 2):
            color = color_array['left'][j - 1]  # Get the color from the left column in the color array
            for i in range(0, 2 * m, 2):
                small_square = plt.Rectangle((i * square_size + offset_x, (j - 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the right_colors array
        for j in range(2, 2 * n + 1, 2):
            color = color_array['right'][2 * n - j]  # Get the color from the right column in the color array
            for i in range(0, 2 * m, 2):
                small_square = plt.Rectangle(((2 * m - i - 1) * square_size + offset_x, (j - 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

    else:  # right-hand stitch
        # Fill the small squares based on the top_colors array
        for j in range(1, 2 * m, 2):
            color = color_array['top'][2 * m - j]  # Get the color from the top row in the color array
            for i in range(0, 2 * n, 2):
                small_square = plt.Rectangle(((j - 1) * square_size + offset_x, i * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the bottom_colors array
        for j in range(2, 2 * m + 1, 2):
            color = color_array['bottom'][j - 1]  # Get the color from the bottom row in the color array
            for i in range(0, 2 * n, 2):
                small_square = plt.Rectangle(((j - 1) * square_size + offset_x, (2 * n - i - 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the left_colors array
        for j in range(2, 2 * n + 1, 2):
            color = color_array['left'][j - 1]  # Get the color from the left column in the color array
            for i in range(0, 2 * m, 2):
                small_square = plt.Rectangle((i * square_size + offset_x, (j - 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

        # Fill the small squares based on the right_colors array
        for j in range(1, 2 * n, 2):
            color = color_array['right'][2 * n - j]  # Get the color from the right column in the color array
            for i in range(0, 2 * m, 2):
                small_square = plt.Rectangle(((2 * m - i - 1) * square_size + offset_x, (j - 1) * square_size + offset_y), square_size, square_size, facecolor=color, edgecolor='none', zorder=3)
                ax.add_patch(small_square)

    # Draw the outer square with a colored border
    outer_square = plt.Rectangle((offset_x, offset_y), 2 * m * square_size, 2 * n * square_size, facecolor='none', edgecolor='black', zorder=4, linewidth=0.5)
    ax.add_patch(outer_square)

# The display_colors function remains unchanged as it doesn't deal with positioning
def display_colors(ax, square_size, m, n, top_colors, left_colors, bottom_colors, right_colors):
    if any(colors is None for colors in [top_colors, left_colors, bottom_colors, right_colors]):
        # Regenerate all colors if any color list is None
        all_colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(4 * n + 4 * m)]
        top_colors = all_colors[:2 * m]
        right_colors = all_colors[2 * m:2 * m + 2 * n]
        bottom_colors = all_colors[2 * m + 2 * n:4 * m + 2 * n]
        left_colors = all_colors[4 * m + 2 * n:]

    all_colors = [top_colors[::-1], right_colors[::-1], bottom_colors, left_colors]
    all_labels = ['Top', 'Right', 'Bottom', 'Left']
    num_colors = max([len(colors) for colors in all_colors])
    cellText = [[''] * 4 for _ in range(num_colors)]
    for i, colors in enumerate(all_colors):
        for j, color in enumerate(colors):
            cellText[j][i] = str(color) if color else 'white'  # Ensure no empty color values

    table = ax.table(cellText=cellText, cellLoc='center', loc='center', colLabels=all_labels, colWidths=[0.15] * 4, rowLabels=['Color ' + str(i + 1) for i in range(num_colors)], rowLoc='center')
    for i in range(num_colors):
        for j in range(4):
            cell = table.get_celld()[(i + 1, j)]
            if cellText[i][j] == '':
                cellText[i][j] = 'white'  # Set default color if empty
            cell.set_facecolor(mcolors.to_rgba(cellText[i][j]))
            cell.set_edgecolor('black')
            cell.set_linewidth(1)
            cell.set_text_props(weight='bold', size=14)

    table.scale(1, 1)  # Scale the table to fit the axis
    ax.axis('off')
    return {'top': top_colors, 'right': right_colors, 'bottom': bottom_colors, 'left': left_colors}
