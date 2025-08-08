# Add these two lines at the very top of the file, before any other imports
import matplotlib
matplotlib.use('TkAgg')  # Use interactive backend

# Then your existing imports
import json
import os
import random
import colorsys
import math
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count, Manager, Process
import itertools
import time
import matplotlib.pyplot as plt

def init_worker(global_min_diffs_, global_strands_data_):
    """Initialize global variables in child processes."""
    global global_min_diffs
    global global_strands_data
    global_min_diffs = global_min_diffs_
    global_strands_data = global_strands_data_

def calculate_point_to_line_distance_vectorized(point, line_start, line_end):
    """Vectorized version of point-to-line distance calculation"""
    points = np.array([[point['x'], point['y']]])
    line_starts = np.array([[line_start['x'], line_start['y']]])
    line_ends = np.array([[line_end['x'], line_end['y']]])
    
    px = points[:, 0] - line_starts[:, 0]
    py = points[:, 1] - line_starts[:, 1]
    
    lx = line_ends[:, 0] - line_starts[:, 0]
    ly = line_ends[:, 1] - line_starts[:, 1]
    
    l2 = lx*lx + ly*ly
    
    # Handle case where line is a point
    point_mask = l2 == 0
    point_distances = np.sqrt(px[point_mask]**2 + py[point_mask]**2)
    
    # Project points onto lines
    t = np.clip((px*lx + py*ly) / l2, 0, 1)
    
    projection_x = line_starts[:, 0] + t * lx
    projection_y = line_starts[:, 1] + t * ly
    
    dx = points[:, 0] - projection_x
    dy = points[:, 1] - projection_y
    distances = np.sqrt(dx*dx + dy*dy)
    
    # Combine results
    distances[point_mask] = point_distances
    
    # Return scalar if single point
    return float(distances[0])

def get_midpoint(strand):
    """Get midpoint of a strand"""
    return {
        "x": (strand["start"]["x"] + strand["end"]["x"]) / 2,
        "y": (strand["start"]["y"] + strand["end"]["y"]) / 2
    }

def normalize_vector(vector):
    """Normalize a vector to unit length"""
    magnitude = math.hypot(vector["x"], vector["y"])
    if magnitude == 0:
        return {"x": 0, "y": 0}
    return {"x": vector["x"]/magnitude, "y": vector["y"]/magnitude}

def dot_product(v1, v2):
    """Calculate dot product of two vectors"""
    return v1["x"] * v2["x"] + v1["y"] * v2["y"]

def params_generator(m, n, vertical_angles, horizontal_angles, possible_offsets, 
                    horizontal_gap, vertical_gap, base_spacing,
                    x4_length_extension, x5_length_extension):
    """Generate parameters for processing with different offsets for each pair"""
    # Generate all possible combinations of offsets for each pair
    vertical_offset_combinations = itertools.product(possible_offsets, repeat=m)
    horizontal_offset_combinations = itertools.product(possible_offsets, repeat=n)
    
    for i_angle, j_angle, v_offsets, h_offsets in itertools.product(
        vertical_angles,    # i_angle
        horizontal_angles,  # j_angle
        vertical_offset_combinations,   # Different offset for each vertical pair
        horizontal_offset_combinations  # Different offset for each horizontal pair
    ):
        x5_v_angle = (i_angle + 180) % 360
        x4_v_angle = i_angle
        x5_h_angle = (j_angle + 90) % 360
        x4_h_angle = (j_angle + 270) % 360

        vertical_offsets = np.array(v_offsets)    # Array of different offsets for vertical pairs
        horizontal_offsets = np.array(h_offsets)  # Array of different offsets for horizontal pairs
        
        params = (
            m, n,
            horizontal_gap, vertical_gap, base_spacing,
            x4_v_angle, x5_v_angle,
            x4_h_angle, x5_h_angle,
            x4_length_extension, x5_length_extension,
            vertical_offsets, horizontal_offsets,
            i_angle, x5_v_angle, j_angle, x5_h_angle,
            tuple(v_offsets), tuple(h_offsets)  # Store as tuples for filename generation
        )
        yield params

def process_params(params):
    """Wrapper function that includes the shared dictionary"""
    global global_min_diffs
    global global_strands_data
    result = generate_json(params)
    if result is not None:
        data, (m, n, v_offsets, h_offsets, i_angle, j_angle) = result
        valid_lengths_v = global_strands_data.get('valid_lengths_vertical')
        valid_lengths_h = global_strands_data.get('valid_lengths_horizontal')
        if valid_lengths_v is None or valid_lengths_h is None:
            return None
        return result, (valid_lengths_v, valid_lengths_h)
    else:
        # No need to print current minimal diffs; they are now plotted
        return None

def store_valid_lengths_vertical(min_length, max_length, strand_width):
    """Store valid lengths for vertical strands in global dictionary"""
    global global_strands_data
    global_strands_data['valid_lengths_vertical'] = {
            'min_length': min_length,
            'max_length': max_length,
            'strand_width': strand_width
        }

def store_valid_lengths_horizontal(min_length, max_length, strand_width):
    """Store valid lengths for horizontal strands in global dictionary"""
    global global_strands_data
    global_strands_data['valid_lengths_horizontal'] = {
            'min_length': min_length,
            'max_length': max_length,
            'strand_width': strand_width
        }

def check_strand_sequence_alignment(strands_dict, is_vertical, log_file=None):
    """Check sequence alignment for all consecutive pairs."""
    set_numbers = sorted(strands_dict.keys())
    num_vectors = 0

    if len(set_numbers) == 0:
        return True, [], None, None  # No strands to check

    vectors = []
    normalized_vectors = []
    dot_products = []
    strand_width = 26
    is_aligned = True

    # Compute vectors between connected strands
    for i in range(len(set_numbers)):
        current_set = set_numbers[i]

        if '5' in strands_dict[current_set] and '4' in strands_dict[current_set]:
            current_x5 = strands_dict[current_set]['5']
            current_x4 = strands_dict[current_set]['4']

            point1 = get_midpoint(current_x5)
            point2 = get_projection_point(point1, current_x4["start"], current_x4["end"])

            vector = {
                "x": point2["x"] - point1["x"],
                "y": point2["y"] - point1["y"]
            }
            vectors.append(vector)
            normalized_vectors.append(normalize_vector(vector))
            num_vectors += 1

        if i < len(set_numbers) - 1:
            next_set = set_numbers[i + 1]
            if '4' in strands_dict[current_set] and '5' in strands_dict[next_set]:
                current_x4 = strands_dict[current_set]['4']
                next_x5 = strands_dict[next_set]['5']

                point1 = get_midpoint(current_x4)
                point2 = get_projection_point(point1, next_x5["start"], next_x5["end"])

                vector = {
                    "x": point2["x"] - point1["x"],
                    "y": point2["y"] - point1["y"]
                }
                vectors.append(vector)
                normalized_vectors.append(normalize_vector(vector))
                num_vectors += 1

    min_alignment = 1.0  # Initialize min_alignment
    min_length = float('inf')  # Initialize min_length to infinity
    max_length = 0

    for i in range(len(vectors)):
        length = math.hypot(vectors[i]['x'], vectors[i]['y'])
        min_length = min(min_length, length)
        max_length = max(max_length, length)

        if i < len(vectors) - 1:
            alignment = dot_product(normalized_vectors[i], normalized_vectors[i+1])
            dot_products.append(alignment)
            min_alignment = min(min_alignment, alignment)  # Update min_alignment

    if num_vectors >= 1:
        if max_length - min_length > 4:
            is_aligned = False
            # Always store lengths
            if is_vertical:
                store_valid_lengths_vertical(min_length, max_length, strand_width)
            else:
                store_valid_lengths_horizontal(min_length, max_length, strand_width)
            return is_aligned, dot_products, min_length, max_length

    # Perform min_length checks only if min_length has been updated
    if min_length != float('inf'):
        min_length = abs(min_length)
        max_length = abs(max_length)
        
        if min_length - strand_width * 2 < 4:
            is_aligned = False
            # Store absolute values
            if is_vertical:
                store_valid_lengths_vertical(min_length, max_length, strand_width)
            else:
                store_valid_lengths_horizontal(min_length, max_length, strand_width)
            return is_aligned, dot_products, min_length, max_length

        if min_length - strand_width * 4 > 4:
            is_aligned = False
            # Store absolute values
            if is_vertical:
                store_valid_lengths_vertical(min_length, max_length, strand_width)
            else:
                store_valid_lengths_horizontal(min_length, max_length, strand_width)
            return is_aligned, dot_products, min_length, max_length

    # Alignment check
    if min_alignment <= 0.9 and num_vectors >= 1:
        is_aligned = False

    # Always store lengths
    if is_vertical:
        store_valid_lengths_vertical(min_length, max_length, strand_width)
    else:
        store_valid_lengths_horizontal(min_length, max_length, strand_width)

    return is_aligned, dot_products, min_length, max_length

def get_projection_point(point, line_start, line_end):
    """Get the projection point of a point onto a line"""
    px = point["x"] - line_start["x"]
    py = point["y"] - line_start["y"]
    
    lx = line_end["x"] - line_start["x"]
    ly = line_end["y"] - line_start["y"]
    
    l2 = lx*lx + ly*ly
    t = max(0, min(1, (px*lx + py*ly) / l2))
    
    return {
        "x": line_start["x"] + t * lx,
        "y": line_start["y"] + t * ly
    }

def check_valid_distances(vertical_strands, horizontal_strands, m, n):
    """Check if distances between first x4 and last x5 are valid and sequence alignment is consistent"""
    # For vertical strands
    if m >= 1:  # Only check if there are vertical strands
        if '4' in vertical_strands[1] and '5' in vertical_strands[m]:
            x4_strand = vertical_strands[1]['4']
            x5_strand = vertical_strands[m]['5']
            midpoint = get_midpoint(x4_strand)
            distance = calculate_point_to_line_distance_vectorized(
                midpoint,
                x5_strand["start"],
                x5_strand["end"]
            )
            expected_distance = (2*n) * 26  # Assuming strand_width = 26
            if not ((expected_distance)/2  <= distance <= (expected_distance+2*n)*4):
                return False
    # For horizontal strands
    if n >= 1:  # Only check if there are horizontal strands
        if '4' in horizontal_strands[m+1] and '5' in horizontal_strands[m+n]:
            x4_strand = horizontal_strands[m+1]['4']
            x5_strand = horizontal_strands[m+n]['5']
            midpoint = get_midpoint(x4_strand)
            distance = calculate_point_to_line_distance_vectorized(
                midpoint,
                x5_strand["start"],
                x5_strand["end"]
            )
            expected_distance =  (2*m) * 26  # Assuming strand_width = 26
            if not ((expected_distance)/2  <= distance <= (expected_distance+2*m)*4):
                return False
    # Update sequence alignment validation calls
    v_aligned, _, _, _ = check_strand_sequence_alignment(vertical_strands, is_vertical=True, log_file=None)
    if not v_aligned:
        return False
        
    h_aligned, _, _, _ = check_strand_sequence_alignment(horizontal_strands, is_vertical=False, log_file=None)
    if not h_aligned:
        return False

    return True

def generate_json(params):
    try:
        # Unpack parameters
        (m, n, horizontal_gap, vertical_gap, base_spacing,
         x4_vertical_angle, x5_vertical_angle,
         x4_horizontal_angle, x5_horizontal_angle,
         x4_length_extension, x5_length_extension,
         vertical_offsets, horizontal_offsets,
         i_angle, x5_v_angle, j_angle, x5_h_angle,
         v_offsets, h_offsets) = params

        global global_min_diffs
        global global_strands_data

        all_strands = []  # Single list to maintain exact order
        index = 0
        base_x, base_y = 168.0*2, 168.0*2

        def get_color():
            h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
            r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
            return {"r": r, "g": g, "b": b, "a": 255}

        def calculate_control_points(start, end):
            return [
                {"x": start["x"], "y": start["y"]},
                {"x": start["x"], "y": start["y"]}
            ]

        def calculate_strand_length(start, end):
            return math.hypot(end["x"] - start["x"], end["y"] - start["y"])

        def calculate_endpoint_with_angle(start, length, angle_deg):
            angle_deg = angle_deg % 360
            angle_rad = math.radians(angle_deg)
            dx = length * math.sin(angle_rad)
            dy = length * math.cos(angle_rad)
            return {
                "x": round(start["x"] + dx, 2),
                "y": round(start["y"] + dy, 2)
            }

        def create_strand(start, end, color, layer_name, set_number, strand_type="Strand"):
            nonlocal index
            is_main_strand = layer_name.split('_')[1] == '1'
            
            strand = {
                "type": strand_type,
                "index": index,
                "start": start,
                "end": end,
                "width": 46,
                "color": color,
                "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                "stroke_width": 4,
                "has_circles": [True, True] if is_main_strand else [True, False],
                "layer_name": layer_name,
                "set_number": set_number,
                "is_first_strand": strand_type == "Strand",
                "is_start_side": True,
                "control_points": calculate_control_points(start, end)
            }
            
            if strand_type == "AttachedStrand":
                strand["parent_layer_name"] = f"{set_number}_1"
                strand_number = layer_name.split('_')[1]
                
                if strand_number == '4':
                    strand["parent_layer_name"] = f"{set_number}_2"
                elif strand_number == '5':
                    strand["parent_layer_name"] = f"{set_number}_3"
            
            index += 1
            return strand

        def create_masked_strand(v_strand, h_strand):
            nonlocal index
            intersection = calculate_precise_intersection(v_strand, h_strand)
            if intersection is None:
                return None

            masked_strand = {
                "type": "MaskedStrand",
                "index": index,
                "start": h_strand["start"].copy(),
                "end": h_strand["end"].copy(),
                "width": 46,
                "color": h_strand["color"].copy(),
                "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                "stroke_width": 4,
                "has_circles": [False, False],
                "layer_name": f"{v_strand['layer_name']}_{h_strand['layer_name']}",
                "set_number": h_strand["set_number"],
                "first_selected_strand": v_strand["layer_name"],
                "second_selected_strand": h_strand["layer_name"],
                "deletion_rectangles": [],
                "custom_mask_path": None,
                "base_center_point": intersection,
                "edited_center_point": intersection.copy(),
            }
            index += 1
            return masked_strand

        def calculate_precise_intersection(strand1, strand2):
            x1, y1 = strand1["start"]["x"], strand1["start"]["y"]
            x2, y2 = strand1["end"]["x"], strand1["end"]["y"]
            x3, y3 = strand2["start"]["x"], strand2["start"]["y"]
            x4, y4 = strand2["end"]["x"], strand2["end"]["y"]

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                return None

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            if not (0 <= t <= 1):
                return None

            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return {"x": x, "y": y}

        colors = {i+1: get_color() for i in range(m+n)}
        vertical_strands = {i: {} for i in range(1, m+1)}  # Organized by set number
        horizontal_strands = {i: {} for i in range(m+1, m+n+1)}  # Organized by set number

        # Generate main strands (x_1) first
        for i in range(m):
            start_x = base_x + i * base_spacing - 2 * horizontal_gap
            start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
            main_strand = create_strand(
                {"x": start_x + vertical_gap, "y": start_y},
                {"x": start_x - vertical_gap, "y": start_y - base_spacing + (n-1) * 4 * vertical_gap},
                colors[i+1], f"{i+1}_1", i+1
            )
            all_strands.append(main_strand)
            vertical_strands[i+1]['main'] = main_strand

        for i in range(n):
            start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
            start_y = base_y + i * base_spacing
            main_strand = create_strand(
                {"x": start_x, "y": start_y + horizontal_gap},
                {"x": start_x + base_spacing - (m-1) * 4 * vertical_gap, "y": start_y - horizontal_gap},
                colors[m+i+1], f"{m+i+1}_1", m+i+1
            )
            all_strands.append(main_strand)
            horizontal_strands[m+i+1]['main'] = main_strand

        # Generate x_2 and x_3 strands with immediate masking
        for i in range(m):
            main_strand = vertical_strands[i+1]['main']
            current_offset = vertical_offsets[i]
            reverse_index = m - 1 - i

            strand2 = create_strand(main_strand["start"], 
                {"x": main_strand["end"]["x"] + 2*vertical_gap, 
                 "y": main_strand["end"]["y"] + 0.5*vertical_gap - current_offset},
                colors[i+1], f"{i+1}_2", i+1, "AttachedStrand")
            all_strands.append(strand2)
            vertical_strands[i+1]['2'] = strand2

            paired_offset = vertical_offsets[reverse_index]
            strand3 = create_strand(main_strand["end"], 
                {"x": main_strand["start"]["x"] - 2*vertical_gap, 
                 "y": main_strand["start"]["y"] - 0.5*vertical_gap + paired_offset},
                colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
            all_strands.append(strand3)
            vertical_strands[i+1]['3'] = strand3

        for i in range(n):
            main_strand = horizontal_strands[m+i+1]['main']
            current_offset = horizontal_offsets[i]
            reverse_index = n - 1 - i

            strand2 = create_strand(main_strand["start"], 
                {"x": main_strand["end"]["x"] - 0.5*horizontal_gap + current_offset, 
                 "y": main_strand["end"]["y"] + 2*horizontal_gap},
                colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand")
            all_strands.append(strand2)
            horizontal_strands[m+i+1]['2'] = strand2

            paired_offset = horizontal_offsets[reverse_index]
            strand3 = create_strand(main_strand["end"], 
                {"x": main_strand["start"]["x"] + 0.5*horizontal_gap - paired_offset, 
                 "y": main_strand["start"]["y"] - 2*horizontal_gap},
                colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
            all_strands.append(strand3)
            horizontal_strands[m+i+1]['3'] = strand3

        # Generate masks for x_2 and x_3
        for v_set in vertical_strands.values():
            for h_set in horizontal_strands.values():
                if '2' in v_set and '2' in h_set:
                    mask = create_masked_strand(v_set['2'], h_set['3'])
                    if mask:
                        all_strands.append(mask)
                if '3' in v_set and '3' in h_set:
                    mask = create_masked_strand(v_set['3'], h_set['2'])
                    if mask:
                        all_strands.append(mask)

        # Generate x_4 and x_5 strands
        for i in range(m):
            strand2 = vertical_strands[i+1]['2']
            strand3 = vertical_strands[i+1]['3']
            length4 = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
            x4_end = calculate_endpoint_with_angle(strand2["end"], length4, x4_vertical_angle)
            strand4 = create_strand(strand2["end"], x4_end, colors[i+1], f"{i+1}_4", i+1, "AttachedStrand")
            all_strands.append(strand4)
            vertical_strands[i+1]['4'] = strand4
            
            length5 = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
            x5_end = calculate_endpoint_with_angle(strand3["end"], length5, x5_vertical_angle)
            strand5 = create_strand(strand3["end"], x5_end, colors[i+1], f"{i+1}_5", i+1, "AttachedStrand")
            all_strands.append(strand5)
            vertical_strands[i+1]['5'] = strand5

        for i in range(n):
            strand2 = horizontal_strands[m+i+1]['2']
            strand3 = horizontal_strands[m+i+1]['3']
            length4 = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
            x4_end = calculate_endpoint_with_angle(strand2["end"], length4, x4_horizontal_angle)
            strand4 = create_strand(strand2["end"], x4_end, colors[m+i+1], f"{m+i+1}_4", m+i+1, "AttachedStrand")
            all_strands.append(strand4)
            horizontal_strands[m+i+1]['4'] = strand4
            
            length5 = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
            x5_end = calculate_endpoint_with_angle(strand3["end"], length5, x5_horizontal_angle)
            strand5 = create_strand(strand3["end"], x5_end, colors[m+i+1], f"{m+i+1}_5", m+i+1, "AttachedStrand")
            all_strands.append(strand5)
            horizontal_strands[m+i+1]['5'] = strand5

            for v_set in vertical_strands.values():
                if '4' in v_set and '5' in horizontal_strands[m+i+1]:
                    mask = create_masked_strand(v_set['4'], strand5)
                    if mask:
                        all_strands.append(mask)
                if '5' in v_set and '4' in horizontal_strands[m+i+1]:
                    mask = create_masked_strand(v_set['5'], strand4)
                    if mask:
                        all_strands.append(mask)

        # After generating all strands, check distances
        if not check_valid_distances(vertical_strands, horizontal_strands, m, n):
            # Update minimal diffs
            valid_lengths_v = global_strands_data.get('valid_lengths_vertical')
            valid_lengths_h = global_strands_data.get('valid_lengths_horizontal')

            if valid_lengths_v is not None:
                min_length_v = abs(valid_lengths_v['min_length'])
                max_length_v = abs(valid_lengths_v['max_length'])
                strand_width_v = valid_lengths_v['strand_width']
                diff1_v = abs(min_length_v - strand_width_v * 2)  # Take absolute value here
                diff2_v = abs(max_length_v - min_length_v)  # Take absolute value here

                # Update global_min_diffs with absolute values
                if diff1_v < global_min_diffs.get('min_diff1_v', float('inf')):
                    global_min_diffs['min_diff1_v'] = diff1_v
                if diff2_v < global_min_diffs.get('min_diff2_v', float('inf')):
                    global_min_diffs['min_diff2_v'] = diff2_v

            if valid_lengths_h is not None:
                min_length_h = abs(valid_lengths_h['min_length'])
                max_length_h = abs(valid_lengths_h['max_length'])
                strand_width_h = valid_lengths_h['strand_width']
                diff1_h = abs(min_length_h - strand_width_h * 2)  # Take absolute value here
                diff2_h = abs(max_length_h - min_length_h)  # Take absolute value here

                # Update global_min_diffs with absolute values
                if diff1_h < global_min_diffs.get('min_diff1_h', float('inf')):
                    global_min_diffs['min_diff1_h'] = diff1_h
                if diff2_h < global_min_diffs.get('min_diff2_h', float('inf')):
                    global_min_diffs['min_diff2_h'] = diff2_h

            return None

        # Update indices to match the final order
        for i, strand in enumerate(all_strands):
            strand["index"] = i

        data = {
            "strands": all_strands,
            "groups": {}
        }

        # Return the data and parameters needed for naming
        return data, (m, n, v_offsets, h_offsets, i_angle, j_angle)

    except Exception as e:
        # Handle exceptions gracefully
        print(f"Error processing params {params}: {e}")
        return None

def calculate_total_combinations(m, n, vertical_angles, horizontal_angles, possible_offsets):
    """Calculate the total number of combinations."""
    return (
        len(vertical_angles) *
        len(horizontal_angles) *
        len(possible_offsets) ** m *  # m vertical pairs
        len(possible_offsets) ** n    # n horizontal pairs
    )

def data_processing(m_values, n_values, vertical_angles, horizontal_angles, possible_offsets,
                    horizontal_gap, vertical_gap, base_spacing,
                    x4_length_extension, x5_length_extension,
                    base_dir, global_min_diffs, global_strands_data, processing_complete):
    """Function to perform data processing in a separate process."""
    for m in m_values:
        for n in n_values:
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            os.makedirs(output_dir, exist_ok=True)

            print(f"Processing m={m}, n={n} configuration...")
            params_iter = params_generator(
                m, n, vertical_angles, horizontal_angles, possible_offsets,
                horizontal_gap, vertical_gap, base_spacing,
                x4_length_extension, x5_length_extension
            )

            total_combinations = calculate_total_combinations(m, n, vertical_angles, horizontal_angles, possible_offsets)

            # Limit the number of processes to cpu_count() - 1
            num_processes = max(cpu_count() - 1, 1)

            with Pool(
                processes=num_processes,
                initializer=init_worker,
                initargs=(global_min_diffs, global_strands_data)
            ) as pool:
                for processed_result in tqdm(
                    pool.imap_unordered(process_params, params_iter, chunksize=10),  # Use a smaller chunksize
                    total=total_combinations,
                    desc=f"m{m}xn{n}"
                ):
                    if processed_result is not None:
                        (data, params), (valid_lengths_v, valid_lengths_h) = processed_result
                        m, n, v_offsets, h_offsets, i_angle, j_angle = params

                        # Vertical lengths
                        min_length_v = abs(valid_lengths_v['min_length'])
                        max_length_v = abs(valid_lengths_v['max_length'])
                        strand_width_v = valid_lengths_v['strand_width']

                        # Horizontal lengths
                        min_length_h = abs(valid_lengths_h['min_length'])
                        max_length_h = abs(valid_lengths_h['max_length'])
                        strand_width_h = valid_lengths_h['strand_width']

                        diff1_v = abs(min_length_v - strand_width_v * 2)  # Take absolute value here
                        diff2_v = abs(max_length_v - min_length_v)  # Take absolute value here

                        diff1_h = abs(min_length_h - strand_width_h * 2)  # Take absolute value here
                        diff2_h = abs(max_length_h - min_length_h)  # Take absolute value here

                        # Create offset strings for filename
                        v_offset_str = '_'.join(f'v{v}' for v in v_offsets)
                        h_offset_str = '_'.join(f'h{h}' for h in h_offsets)

                        filename = (
                            f"m{m}_n{n}_{v_offset_str}_{h_offset_str}_"
                            f"va{i_angle}_ha{j_angle}_"
                            f"diff1_v_{diff1_v:.2f}_diff2_v_{diff2_v:.2f}_"
                            f"diff1_h_{diff1_h:.2f}_diff2_h_{diff2_h:.2f}.json"
                        )

                        filepath = os.path.join(output_dir, filename)

                        with open(filepath, 'w') as f:
                            json.dump(data, f, separators=(',', ':'))

                        global_strands_data.clear()
    # Signal that processing is complete
    processing_complete.set()

def main():
    start_time = time.time()
    last_update_time = time.time()
    update_interval = 1

    # Initialize data storage for plotting
    plot_data = {
        'time': [],
        'Vertical diff1': [],
        'Vertical diff2': [],
        'Horizontal diff1': [],
        'Horizontal diff2': []
    }

    # Initialize Manager and shared dictionaries inside main()
    manager = Manager()
    global global_strands_data
    global global_min_diffs
    global_strands_data = manager.dict()
    global_min_diffs = manager.dict()
    global_min_diffs['min_diff1_v'] = float('inf')
    global_min_diffs['min_diff2_v'] = float('inf')
    global_min_diffs['min_diff1_h'] = float('inf')
    global_min_diffs['min_diff2_h'] = float('inf')

    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"

    strand_width = 28
    x4_length_extension = 55
    x5_length_extension = 55
    horizontal_gap = -28
    vertical_gap = -28
    base_spacing = 112

    max_offset = abs(6 * vertical_gap)
    min_offset = 0
    offset_step = 10

    minimum_angle_h = 5 # For n
    maximum_angle_h = 21 # For n
    minimum_angle_v = 16 # For m
    maximum_angle_v = 27 # For m

    angle_step = 2

    vertical_angles = np.arange(minimum_angle_v, maximum_angle_v + 1, angle_step)
    horizontal_angles = np.arange(minimum_angle_h, maximum_angle_h + 1, angle_step)
    possible_offsets = np.arange(min_offset, max_offset + 1, offset_step)

    n_values = [4]
    m_values = [1]

    # Start the data processing in a separate process
    processing_complete = manager.Event()

    # Start the data processing in a separate process
    processing_process = Process(
        target=data_processing,
        args=(
            m_values, n_values, vertical_angles, horizontal_angles, possible_offsets,
            horizontal_gap, vertical_gap, base_spacing,
            x4_length_extension, x5_length_extension,
            base_dir, global_min_diffs, global_strands_data, processing_complete
        )
    )
    processing_process.start()

    # Create the figure and axes for plotting
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Difference Values')
    ax.set_title('Minimum Differences Over Time')
    ax.grid(True)
    
    lines = {}
    colors = {'Vertical diff1': 'blue', 'Vertical diff2': 'red',
              'Horizontal diff1': 'green', 'Horizontal diff2': 'purple'}

    # Monitor progress
    while not processing_complete.is_set():
        current_time = time.time()
        
        if current_time - last_update_time >= update_interval:
            elapsed_time = current_time - start_time
            
            # Get current minimum values
            current_values = {
                'Vertical diff1': global_min_diffs.get('min_diff1_v', float('inf')),
                'Vertical diff2': global_min_diffs.get('min_diff2_v', float('inf')),
                'Horizontal diff1': global_min_diffs.get('min_diff1_h', float('inf')),
                'Horizontal diff2': global_min_diffs.get('min_diff2_h', float('inf'))
            }

            # Update plot data
            plot_data['time'].append(elapsed_time)
            for key, value in current_values.items():
                if value != float('inf'):
                    plot_data[key].append(value)
                    if key not in lines:
                        # Create new line
                        lines[key], = ax.plot([], [], label=key, color=colors[key])
                    
                    # Update line data
                    if len(plot_data[key]) > 0:
                        lines[key].set_data(plot_data['time'][-len(plot_data[key]):], 
                                        plot_data[key])

            # Update plot limits if we have data
            if any(len(plot_data[key]) > 0 for key in current_values.keys()):
                ax.set_xlim(0, max(plot_data['time']) * 1.1)
                
                # Find min/max y values across all valid data
                all_values = [v for key in current_values.keys() 
                            for v in plot_data[key] if v != float('inf')]
                if all_values:
                    ymin = min(all_values)
                    ymax = max(all_values)
                    margin = (ymax - ymin) * 0.1 if ymax > ymin else 1
                    ax.set_ylim(ymin - margin, ymax + margin)

            # Update legend and refresh plot
            if lines:
                ax.legend()
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            last_update_time = current_time

        time.sleep(0.1)  # Reduced sleep time for more responsive updates

    # Final plot update
    plt.ioff()
    plt.show()

    print("\nProcessing complete!")
    print("Final minimum values:")
    print("-" * 50)
    final_values = {
        'Vertical diff1': abs(global_min_diffs.get('min_diff1_v', float('inf'))),
        'Vertical diff2': abs(global_min_diffs.get('min_diff2_v', float('inf'))),
        'Horizontal diff1': abs(global_min_diffs.get('min_diff1_h', float('inf'))),
        'Horizontal diff2': abs(global_min_diffs.get('min_diff2_h', float('inf')))
    }
    for key, value in final_values.items():
        if value != float('inf'):
            print(f"{key}: {value:.4f}")
    print("-" * 50)

if __name__ == "__main__":
    main()
