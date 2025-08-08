import json
import os
import random
import colorsys
import math
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import itertools

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

def check_strand_sequence_alignment(strands_dict, log_file=None):
    """Check sequence alignment for all consecutive pairs"""
    set_numbers = sorted(strands_dict.keys())
    if len(set_numbers) < 2:
        return True, []
    
    vectors = []
    normalized_vectors = []
    vector_pairs = []
    dot_products = []
    strand_width = 26
    is_aligned = True

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
            vector_pairs.append(f"Set {current_set}: x5 -> x4")
        
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
                vector_pairs.append(f"Set {current_set} -> Set {next_set}: x4 -> x5")

    min_alignment = 1.0  # Initialize min_alignment
    for i in range(len(vectors)-1):
        alignment = dot_product(normalized_vectors[i], normalized_vectors[i+1])
        dot_products.append(alignment)
        min_alignment = min(min_alignment, alignment)  # Update min_alignment

        length = math.hypot(vectors[i]['x'], vectors[i]['y'])
        next_length = math.hypot(vectors[i+1]['x'], vectors[i+1]['y'])
        
        if i == 0:
            min_length = min(length, next_length)
            max_length = max(length, next_length)
        else:
            min_length = min(min_length, length, next_length) 
            max_length = max(max_length, length, next_length)

        if max_length - min_length > 8:
            is_aligned = False
            if log_file:
                log_file.write(f"Failed length consistency check: max_length - min_length = {max_length - min_length:.3f} > 5\n")

        if min_length - strand_width*2 < 3:
            is_aligned = False
            if log_file:
                log_file.write(f"Failed minimum length check: min_length = {min_length:.3f} < 28\n")

    if min_alignment <= 0.9:
        is_aligned = False
        if log_file:
            log_file.write(f"Failed alignment check: minimum alignment = {min_alignment:.3f}\n")

    return is_aligned, dot_products

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
    strand_width = 26
    # For vertical strands: distance should be n * strand_width
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
            expected_distance = (2*n) * strand_width
            if not ((expected_distance)/2  <= distance <=(expected_distance+2*n)*4):
                return False
    # For horizontal strands: distance should be m * strand_width
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
            expected_distance =  (2*m) * strand_width
            if not ((expected_distance)/2  <= distance <= (expected_distance+2*m)*4):
                return False
    # Update sequence alignment validation calls
    v_aligned, _ = check_strand_sequence_alignment(vertical_strands, None)
    if not v_aligned:
        return False
        
    h_aligned, _ = check_strand_sequence_alignment(horizontal_strands, None)
    if not h_aligned:
        return False
    
    return True

def generate_json(params):
    # Unpack parameters
    (m, n, horizontal_gap, vertical_gap, base_spacing,
     x4_vertical_angle, x5_vertical_angle,
     x4_horizontal_angle, x5_horizontal_angle,
     x4_length_extension, x5_length_extension,
     vertical_offsets, horizontal_offsets, output_dir,
     i_angle, x5_v_angle, j_angle, x5_h_angle,
     v_offset, h_offset) = params

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
        return None

    # Update indices to match the final order
    for i, strand in enumerate(all_strands):
        strand["index"] = i

    data = {
        "strands": all_strands,
        "groups": {}
    }
    
    json_content = json.dumps(data, indent=2)
    if json_content is not None:
        filename = f"m{m}_n{n}_v{v_offset}_h{h_offset}_va{i_angle}_ha{j_angle}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(json_content)
        return filename
    else:
        return None  # Return None explicitly if json_content is None

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\all possible rh continulation twist offsets optimized numpy o1"  # Replace with your actual output directory
    os.makedirs(output_dir, exist_ok=True)

    strand_width = 28
    x4_length_extension = 55
    x5_length_extension = 55
    horizontal_gap = -28
    vertical_gap = -28
    base_spacing = 112

    max_offset = abs(6 * vertical_gap)
    min_offset = 0
    offset_step = 1  # Step size of 1 for offsets

    minimum_angle = 12
    maximum_angle = 45
    angle_step = 1  # Step size of 1 for angles

    vertical_angles = np.arange(minimum_angle, maximum_angle + 1, angle_step)
    horizontal_angles = np.arange(minimum_angle, maximum_angle + 1, angle_step)
    possible_offsets = np.arange(min_offset, max_offset + 1, offset_step)

    m_values = [2]
    n_values = [2]

    total_combinations = (
        len(vertical_angles) * 
        len(horizontal_angles) * 
        len(possible_offsets) * 
        len(possible_offsets)
    )

    # Use itertools.product to create an iterator over all combinations
    combinations = itertools.product(
        vertical_angles,    # i_angle
        horizontal_angles,  # j_angle
        possible_offsets,   # v_offset
        possible_offsets    # h_offset
    )

    # Generator function to yield parameters one at a time
    def params_generator():
        for i_angle, j_angle, v_offset, h_offset in combinations:
            x5_v_angle = (i_angle + 180) % 360
            x4_v_angle = i_angle
            x5_h_angle = (j_angle + 90) % 360
            x4_h_angle = (j_angle + 270) % 360

            vertical_offsets = np.full(m_values[0], v_offset)
            horizontal_offsets = np.full(n_values[0], h_offset)
            params = (
                m_values[0], n_values[0],
                horizontal_gap, vertical_gap, base_spacing,
                x4_v_angle, x5_v_angle,
                x4_h_angle, x5_h_angle,
                x4_length_extension, x5_length_extension,
                vertical_offsets, horizontal_offsets,
                output_dir, i_angle, x5_v_angle, j_angle, x5_h_angle,
                v_offset, h_offset
            )
            yield params

    with Pool(processes=cpu_count()) as pool:
        for _ in tqdm(pool.imap_unordered(generate_json, params_generator()), total=total_combinations):
            pass  # Progress bar updates automatically

if __name__ == "__main__":
    main()
