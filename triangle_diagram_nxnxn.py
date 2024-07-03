import numpy as np
import colorsys
import random
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe

def generate_distinct_colors(num_colors):
    colors = []
    golden_ratio_conjugate = 0.618033988749895
    
    for i in range(num_colors):
        h = random.random()
        h += golden_ratio_conjugate
        h %= 1
        lightness = ((0.6 + random.uniform(-0.2, 0.2))*random.uniform(num_colors/2,num_colors))/num_colors
        saturation = ((0.95 + random.uniform(-0.05, 0.05))*random.uniform(i,num_colors))/num_colors
        color = colorsys.hls_to_rgb(h, lightness, saturation)
        colors.append('#%02x%02x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255)))

    return colors

def plot_triangle(side_length, show_lines, line_width, line_length, stroke, ax, polygon_size,canvas_width,canvas_height):
    # Scale the basic triangle size
    scaled_side_length = (polygon_size)*(np.log1p((side_length)))+(polygon_size*np.log1p((1/side_length)))
    line_length = line_length *10
    # Calculate the height of the triangle
    height = scaled_side_length * np.sqrt(3) / 2
    print(scaled_side_length)
    # Calculate the vertices of the triangle
    A = np.array([0, height * 2/3])
    B = np.array([-scaled_side_length/2, -height * 1/3])
    C = np.array([scaled_side_length/2, -height * 1/3])
    print(f'A: {A}')
    print(f'B: {B}')
    print(f'C: {C}')
    # Centroid is always at (0, 0)
    centroid = np.array([0, 0])
    print(f'centroid: {centroid}')
    # Calculate the midpoints of each side
    M_AB = (A + B) / 2
    M_BC = (B + C) / 2
    M_CA = (C + A) / 2

    # Calculate the fixed bounding box (independent of scale_factor)
    fixed_side_length = side_length  # Use the original side length
    fixed_height = fixed_side_length * np.sqrt(3) / 2
    bounding_box = max(2*fixed_side_length, 2*fixed_height)

    # Set fixed axis limits using the bounding box
    ax.set_xlim(-canvas_width/2, canvas_width/2)
    ax.set_ylim(-canvas_height/2, canvas_height/2)

    
    
    def draw_line_from_centroid(centroid, midpoint, color, linewidth):
        ax.plot([centroid[0], midpoint[0]], [centroid[1], midpoint[1]], color, linewidth=linewidth, zorder=5)

    def draw_perpendicular_line_to_segment(pointa, pointb, color, stroke):
        ax.plot([pointa[0], pointb[0]], [pointa[1], pointb[1]], color, stroke, zorder=5)

    def draw_perpendicular_line(M_points,point, direction, length, color, line_width, stroke):
        direction = direction / np.linalg.norm(direction)
        perpendicular_direction = np.array([-direction[1], direction[0]])
        distance = (np.linalg.norm(M_points[0] - M_points[1])/2)*line_width
        print(f"Distance: {np.linalg.norm(M_points[0] - M_points[1])}")
        print(f"Perpendicular Direction: {perpendicular_direction}")
        print(f"Line width: {line_width}")

        # Calculate the starting point on the triangle's edge
        start_point = point 

        # Calculate the end point
        end_point = start_point + perpendicular_direction * length


        # Calculate the direction and perpendicular direction
        dx, dy = end_point[0] - start_point[0], end_point[1] - start_point[1]
        angle = np.arctan2(dy, dx)
        perpendicular_direction = np.array([np.sin(angle), np.cos(angle)])

        # Calculate the shifts for the rectangle
        x_shift = perpendicular_direction[0] * distance
        y_shift = perpendicular_direction[1] * distance 

        # Calculate the coordinates of the rectangle
        coords = np.array([
            [start_point[0] + x_shift, start_point[1] - y_shift],
            [start_point[0] - x_shift, start_point[1] + y_shift],
            [end_point[0] - x_shift, end_point[1] + y_shift],
            [end_point[0] + x_shift, end_point[1] - y_shift]
        ])

        polygon = Polygon(coords, closed=True, facecolor=color, edgecolor="BLACK", lw=stroke)
        polygon.set_path_effects([pe.Stroke(linewidth=stroke, foreground="BLACK"), pe.Normal()])
        ax.add_patch(polygon)
    def split_points(p1, p2, split):
        points = [p1]
        for i in range(1, split + 1):
            point = p1 + (p2 - p1) * i / (split + 1)
            points.append(point)
        points.append(p2)
        return np.array(points)

    split = split = int(side_length) - 1
  
    M_AB_centroid = split_points(centroid, M_AB, split)
    M_BC_centroid = split_points(centroid, M_BC, split) 
    M_CA_centroid = split_points(centroid, M_CA, split)
    
    A_M_CA = split_points(M_CA, A, split)
    B_M_BC = split_points(M_BC, B, split)
    B_M_AB = split_points(M_AB, B, split)
    C_M_CA = split_points(M_CA, C, split)
    A_M_AB = split_points(M_AB, A, split)
    C_M_BC = split_points(M_BC, C, split)

    def middle_points(points):
        return np.array([(points[i] + points[i+1])/2 for i in range(len(points)-1)])
      
    A_M_CA_middle = middle_points(A_M_CA)
    B_M_BC_middle = middle_points(B_M_BC)
    B_M_AB_middle = middle_points(B_M_AB)
    C_M_CA_middle = middle_points(C_M_CA)
    A_M_AB_middle = middle_points(A_M_AB)
    C_M_BC_middle = middle_points(C_M_BC)

    num_colors = len(A_M_CA_middle) + len(B_M_BC_middle) + len(B_M_AB_middle) + len(C_M_CA_middle) + len(A_M_AB_middle) + len(C_M_BC_middle)
    colors = generate_distinct_colors(num_colors)

    A_M_CA_middle_color = [colors[color_index] for color_index in range(len(A_M_CA_middle))]
    B_M_BC_middle_color = [colors[color_index + len(A_M_CA_middle)] for color_index in range(len(B_M_BC_middle))]
    B_M_AB_middle_color = [colors[color_index + len(A_M_CA_middle) + len(B_M_BC_middle)] for color_index in range(len(B_M_AB_middle))]
    C_M_CA_middle_color = [colors[color_index + len(A_M_CA_middle) + len(B_M_BC_middle) + len(B_M_AB_middle)] for color_index in range(len(C_M_CA_middle))]
    A_M_AB_middle_color = [colors[color_index + len(A_M_CA_middle) + len(B_M_BC_middle) + len(B_M_AB_middle) + len(C_M_CA_middle)] for color_index in range(len(A_M_AB_middle))]
    C_M_BC_middle_color = [colors[color_index + len(A_M_CA_middle) + len(B_M_BC_middle) + len(B_M_AB_middle) + len(C_M_CA_middle) + len(A_M_AB_middle)] for color_index in range(len(C_M_BC_middle))]
    
    def plot_main_triangle_and_lines():
        triangle = np.array([A, B, C, A])
        ax.plot(triangle[:, 0], triangle[:, 1], 'k-', linewidth=stroke, zorder=5)

        draw_line_from_centroid(centroid, M_AB, 'gray', 1)
        draw_line_from_centroid(centroid, M_BC, 'gray', 1)
        draw_line_from_centroid(centroid, M_CA, 'gray', 1)

        for i in range(len(M_AB_centroid)):
            draw_perpendicular_line_to_segment(M_AB_centroid[i], A_M_CA[i], 'black', stroke)
            draw_perpendicular_line_to_segment(M_AB_centroid[i], B_M_BC[i], 'black', stroke)
            draw_perpendicular_line_to_segment(M_BC_centroid[i], B_M_AB[i], 'black', stroke)
            draw_perpendicular_line_to_segment(M_BC_centroid[i], C_M_CA[i], 'black', stroke)
            draw_perpendicular_line_to_segment(M_CA_centroid[i], A_M_AB[i], 'black', stroke)
            draw_perpendicular_line_to_segment(M_CA_centroid[i], C_M_BC[i], 'black', stroke)

    def line_intersection(line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if np.all(div == 0):
            return None

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return np.array([x, y])
    def find_polygons_row_by_row_AB_CA(A_M_AB, A_M_CA, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color):
            polygons = []
            colors_polygons = []
            polygon_indices = []

            for i in range(len(M_CA_centroid) - 1):
                for j in range(len(M_AB_centroid) - 1):
                    intersection_point1 = line_intersection([M_CA_centroid[i], A_M_AB[i]], [M_AB_centroid[j], A_M_CA[j]])
                    intersection_point2 = line_intersection([M_CA_centroid[i], A_M_AB[i]], [M_AB_centroid[j + 1], A_M_CA[j + 1]])
                    intersection_point3 = line_intersection([M_CA_centroid[i + 1], A_M_AB[i + 1]], [M_AB_centroid[j + 1], A_M_CA[j + 1]])
                    intersection_point4 = line_intersection([M_CA_centroid[i + 1], A_M_AB[i + 1]], [M_AB_centroid[j], A_M_CA[j]])
                    polygon = [intersection_point1, intersection_point2, intersection_point3, intersection_point4, intersection_point1]
                    polygons.append(polygon)
                    polygon_indices.append((i, j))
            if show_lines == 'blue':
                if side_length % 2 == 0:
                    for i, j in polygon_indices:
                        if i % 2 == 0:
                            colors_polygons.append(A_M_AB_middle_color[i] if j % 2 == 0 else A_M_CA_middle_color[j])
                        else:
                            colors_polygons.append(B_M_BC_middle_color[j] if j % 2 == 0 else C_M_BC_middle_color[i])
                else:
                    for i, j in polygon_indices:
                        if i % 2 == 0:
                            colors_polygons.append(B_M_BC_middle_color[j] if j % 2 == 0 else A_M_AB_middle_color[i])
                        else:
                            colors_polygons.append(C_M_BC_middle_color[i] if j % 2 == 0 else A_M_CA_middle_color[j])
            elif show_lines == 'red':
                if side_length % 2 == 0:
                    for i, j in polygon_indices:
                        if i % 2 == 0:
                            colors_polygons.append(A_M_CA_middle_color[j] if j % 2 == 0 else C_M_BC_middle_color[i])
                        else:
                            colors_polygons.append(A_M_AB_middle_color[i] if j % 2 == 0 else B_M_BC_middle_color[j])
                else:
                    for i, j in polygon_indices:
                        if i % 2 == 0:
                            colors_polygons.append(C_M_BC_middle_color[i] if j % 2 == 0 else B_M_BC_middle_color[j])
                        else:
                            colors_polygons.append(A_M_CA_middle_color[j] if j % 2 == 0 else A_M_AB_middle_color[i])
            return polygons, colors_polygons

    def find_polygons_row_by_row_CA_BC(C_M_CA, C_M_BC, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color):
        polygons = []
        colors_polygons = []
        polygon_indices = []

        for i in range(len(M_CA_centroid) - 1):
            for j in range(len(M_BC_centroid) - 1):
                intersection_point1 = line_intersection([M_CA_centroid[i], C_M_BC[i]], [M_BC_centroid[j], C_M_CA[j]])
                intersection_point2 = line_intersection([M_CA_centroid[i], C_M_BC[i]], [M_BC_centroid[j + 1], C_M_CA[j + 1]])
                intersection_point3 = line_intersection([M_CA_centroid[i + 1], C_M_BC[i + 1]], [M_BC_centroid[j + 1], C_M_CA[j + 1]])
                intersection_point4 = line_intersection([M_CA_centroid[i + 1], C_M_BC[i + 1]], [M_BC_centroid[j], C_M_CA[j]])
                polygon = [intersection_point1, intersection_point2, intersection_point3, intersection_point4, intersection_point1]
                polygons.append(polygon)
                polygon_indices.append((i, j))

        if show_lines == 'blue':
            if side_length % 2 == 0:
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_CA_middle_color[j])
                        else:
                            colors_polygons.append(A_M_AB_middle_color[i])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_BC_middle_color[i])
                        else:
                            colors_polygons.append(B_M_AB_middle_color[j])
            else:  # side_length % 2 == 1
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(A_M_AB_middle_color[i])
                        else:
                            colors_polygons.append(B_M_AB_middle_color[j])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_CA_middle_color[j])
                        else:
                            colors_polygons.append(C_M_BC_middle_color[i])
        elif show_lines == 'red':
            if side_length % 2 == 0:
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_BC_middle_color[i])
                        else:
                            colors_polygons.append(C_M_CA_middle_color[j])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_AB_middle_color[j])
                        else:
                            colors_polygons.append(A_M_AB_middle_color[i])
            else:  # side_length % 2 == 1
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_AB_middle_color[j])
                        else:
                            colors_polygons.append(C_M_BC_middle_color[i])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(A_M_AB_middle_color[i])
                        else:
                            colors_polygons.append(C_M_CA_middle_color[j])

        return polygons, colors_polygons

    def find_polygons_row_by_row_AB_BC(B_M_AB, B_M_BC, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color):
        polygons = []
        colors_polygons = []
        polygon_indices = []
        for i in range(len(M_AB_centroid) - 1):
            for j in range(len(M_BC_centroid) - 1):
                intersection_point1 = line_intersection([M_AB_centroid[i], B_M_BC[i]], [M_BC_centroid[j], B_M_AB[j]])
                intersection_point2 = line_intersection([M_AB_centroid[i], B_M_BC[i]], [M_BC_centroid[j + 1], B_M_AB[j + 1]])
                intersection_point3 = line_intersection([M_AB_centroid[i + 1], B_M_BC[i + 1]], [M_BC_centroid[j + 1], B_M_AB[j + 1]])
                intersection_point4 = line_intersection([M_AB_centroid[i + 1], B_M_BC[i + 1]], [M_BC_centroid[j], B_M_AB[j]])
                polygon = [intersection_point1, intersection_point2, intersection_point3, intersection_point4, intersection_point1]
                polygons.append(polygon)
                polygon_indices.append((i, j))
        if show_lines == 'blue':
            if(side_length%2==0):
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_BC_middle_color[i])
                        else:
                            colors_polygons.append(B_M_AB_middle_color[j])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_CA_middle_color[j])
                        else:
                            colors_polygons.append(A_M_CA_middle_color[i])
                return polygons, colors_polygons
                
            if(side_length%2==1):
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(C_M_CA_middle_color[j])
                        else:
                            colors_polygons.append(B_M_BC_middle_color[i])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(A_M_CA_middle_color[i])
                        else:
                            colors_polygons.append(B_M_AB_middle_color[j])
        if show_lines == 'red':
            if side_length % 2 == 0:
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_AB_middle_color[j])
                        else:
                            colors_polygons.append(A_M_CA_middle_color[i])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_BC_middle_color[i])
                        else:
                            colors_polygons.append(C_M_CA_middle_color[j])
            if side_length % 2 == 1: # side_length % 2 == 1
                for i, j in polygon_indices:
                    if i % 2 == 0:
                        if j % 2 == 0:
                            colors_polygons.append(A_M_CA_middle_color[i])
                        else:
                            colors_polygons.append(C_M_CA_middle_color[j])
                    else:
                        if j % 2 == 0:
                            colors_polygons.append(B_M_AB_middle_color[j])
                        else:
                            colors_polygons.append(B_M_BC_middle_color[i])

        return polygons, colors_polygons

    # Draw perpendicular lines
    for i in range(len(A_M_CA_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 0:
            draw_perpendicular_line(A_M_CA,A_M_CA_middle[i], A_M_CA_middle[i] - A, line_length, A_M_CA_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 1:
            draw_perpendicular_line(A_M_CA,A_M_CA_middle[i], A_M_CA_middle[i] - A, line_length, A_M_CA_middle_color[i], line_width, stroke)

    for i in range(len(B_M_BC_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 1:
            draw_perpendicular_line(B_M_BC,B_M_BC_middle[i], -B_M_BC_middle[i] + B, line_length, B_M_BC_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 0:
            draw_perpendicular_line(B_M_BC,B_M_BC_middle[i], -B_M_BC_middle[i] + B, line_length, B_M_BC_middle_color[i], line_width, stroke)

    for i in range(len(B_M_AB_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 0:
            draw_perpendicular_line(B_M_AB,B_M_AB_middle[i], B_M_AB_middle[i] - B, line_length, B_M_AB_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 1:
            draw_perpendicular_line(B_M_AB,B_M_AB_middle[i], B_M_AB_middle[i] - B, line_length, B_M_AB_middle_color[i], line_width, stroke)

    for i in range(len(C_M_CA_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 1:
            draw_perpendicular_line(C_M_CA,C_M_CA_middle[i], -C_M_CA_middle[i] + C, line_length, C_M_CA_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 0:
            draw_perpendicular_line(C_M_CA,C_M_CA_middle[i], -C_M_CA_middle[i] + C, line_length, C_M_CA_middle_color[i], line_width, stroke)

    for i in range(len(A_M_AB_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 1:
            draw_perpendicular_line(A_M_AB,A_M_AB_middle[i], -A_M_AB_middle[i] + A, line_length, A_M_AB_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 0:
            draw_perpendicular_line(A_M_AB,A_M_AB_middle[i], -A_M_AB_middle[i] + A, line_length, A_M_AB_middle_color[i], line_width, stroke)

    for i in range(len(C_M_BC_middle)):
        if (show_lines in ['both', 'red']) and i % 2 == 0:
            draw_perpendicular_line(C_M_BC,C_M_BC_middle[i], C_M_BC_middle[i] - C, line_length, C_M_BC_middle_color[i], line_width, stroke)
        if (show_lines in ['both', 'blue']) and i % 2 == 1:
            draw_perpendicular_line(C_M_BC,C_M_BC_middle[i], C_M_BC_middle[i] - C, line_length, C_M_BC_middle_color[i], line_width, stroke)

    # Draw polygons
    polygons_AB_CA, polygon_colors_AB_CA = find_polygons_row_by_row_AB_CA(A_M_AB, A_M_CA, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color)
    polygons_CA_BC, polygon_colors_CA_BC = find_polygons_row_by_row_CA_BC(C_M_CA, C_M_BC, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color)
    polygons_AB_BC, polygon_colors_AB_BC = find_polygons_row_by_row_AB_BC(B_M_AB, B_M_BC, M_AB_centroid, M_CA_centroid, B_M_BC_middle_color, C_M_BC_middle_color, A_M_AB_middle_color, A_M_CA_middle_color, C_M_CA_middle_color, B_M_AB_middle_color)

    for polygon, color in zip(polygons_AB_CA + polygons_CA_BC + polygons_AB_BC, 
                              polygon_colors_AB_CA + polygon_colors_CA_BC + polygon_colors_AB_BC):
        xs, ys = zip(*polygon)
        ax.fill(xs, ys, color=color, alpha=1, zorder=3)
        ax.plot(xs + (xs[0],), ys + (ys[0],), 'k-', linewidth=stroke, zorder=4)

    # Finally, plot the main triangle and internal lines
    plot_main_triangle_and_lines()

    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')



    return A_M_CA_middle_color, B_M_BC_middle_color, B_M_AB_middle_color, C_M_CA_middle_color, A_M_AB_middle_color, C_M_BC_middle_color