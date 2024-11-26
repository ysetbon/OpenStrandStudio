import matplotlib
matplotlib.use('TkAgg')  # Use interactive backend

import json
import os
import random
import colorsys
import math
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count, Process
import time
import matplotlib.pyplot as plt

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
    
    return float(distances[0])

def get_midpoint(strand):
    """Get midpoint of a strand"""
    return {
        "x": (strand["start"]["x"] + strand["end"]["x"]) / 2,
        "y": (strand["start"]["y"] + strand["end"]["y"]) / 2
    }

def calculate_x4_x5_positions(strand2, strand3, x4_angle, x5_angle, base_spacing):
    """
    Calculate x4 and x5 positions maintaining parallel lines and consistent spacing
    """
    # Calculate the base direction vectors when angle is 0
    x2_vector = {
        "x": strand2["end"]["x"] - strand2["start"]["x"],
        "y": strand2["end"]["y"] - strand2["start"]["y"]
    }
    x3_vector = {
        "x": strand3["end"]["x"] - strand3["start"]["x"],
        "y": strand3["end"]["y"] - strand3["start"]["y"]
    }
    
    # Normalize vectors
    x2_length = math.sqrt(x2_vector["x"]**2 + x2_vector["y"]**2)
    x3_length = math.sqrt(x3_vector["x"]**2 + x3_vector["y"]**2)
    
    x2_unit = {
        "x": x2_vector["x"] / x2_length,
        "y": x2_vector["y"] / x2_length
    }
    x3_unit = {
        "x": x3_vector["x"] / x3_length,
        "y": x3_vector["y"] / x3_length
    }
    
    # Normalize angles to -180 to 180 range
    x4_angle = ((x4_angle + 180) % 360) - 180
    x5_angle = ((x5_angle + 180) % 360) - 180
    
    x4_rad = math.radians(x4_angle)
    x5_rad = math.radians(x5_angle)
    
    # Rotate x2 direction to get x4 direction
    x4_unit = {
        "x": x2_unit["x"] * math.cos(x4_rad) - x2_unit["y"] * math.sin(x4_rad),
        "y": x2_unit["x"] * math.sin(x4_rad) + x2_unit["y"] * math.cos(x4_rad)
    }
    
    # Rotate x3 direction to get x5 direction
    x5_unit = {
        "x": x3_unit["x"] * math.cos(x5_rad) - x3_unit["y"] * math.sin(x5_rad),
        "y": x3_unit["x"] * math.sin(x5_rad) + x3_unit["y"] * math.cos(x5_rad)
    }
    
    # Calculate new end points for x2 and x3 (which become start points for x4 and x5)
    x4_start = {
        "x": strand2["start"]["x"] + x2_length * x2_unit["x"],
        "y": strand2["start"]["y"] + x2_length * x2_unit["y"]
    }
    
    x5_start = {
        "x": strand3["start"]["x"] + x3_length * x3_unit["x"],
        "y": strand3["start"]["y"] + x3_length * x3_unit["y"]
    }
    
    # Calculate end points for x4 and x5 maintaining the base spacing
    x4_end = {
        "x": x4_start["x"] + 400 * x4_unit["x"],
        "y": x4_start["y"] + 400 * x4_unit["y"]
    }
    
    x5_end = {
        "x": x5_start["x"] + 400 * x5_unit["x"],
        "y": x5_start["y"] + 400 * x5_unit["y"]
    }
    
    return {
        "x4": {"start": x4_start, "end": x4_end},
        "x5": {"start": x5_start, "end": x5_end}
    }

def calculate_control_points(start, end):
    """Calculate control points for a strand"""
    return [
        {"x": start["x"], "y": start["y"]},
        {"x": start["x"], "y": start["y"]}
    ]

def create_strand(start, end=None, length=None, angle_deg=None, color=None, 
                 layer_name="", set_number=0, strand_type="Strand"):
    """Create a strand with the given parameters"""
    is_main_strand = layer_name.split('_')[1] == '1'
    
    if end is None and length is not None and angle_deg is not None:
        # Calculate end point using length and angle
        angle_rad = math.radians(angle_deg)
        dx = length * math.cos(angle_rad)
        dy = length * math.sin(angle_rad)
        end = {
            "x": start["x"] + dx,
            "y": start["y"] + dy
        }
    
    strand = {
        "type": strand_type,
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
    
    return strand

def check_strand_sequence_alignment(strands_dict, is_vertical):
    """Check sequence alignment for all consecutive pairs."""
    set_numbers = sorted(strands_dict.keys())
    
    if len(set_numbers) == 0:
        return True, None, None  # No strands to check

    strand_width = 26
    min_length = float('inf')
    max_length = 0

    # Check distances between consecutive strands
    for i in range(len(set_numbers)):
        current_set = set_numbers[i]
        
        if '5' in strands_dict[current_set] and '4' in strands_dict[current_set]:
            current_x5 = strands_dict[current_set]['5']
            current_x4 = strands_dict[current_set]['4']
            
            # Calculate distance between x4 and x5
            midpoint_x4 = get_midpoint(current_x4)
            midpoint_x5 = get_midpoint(current_x5)
            distance = math.sqrt(
                (midpoint_x4["x"] - midpoint_x5["x"])**2 + 
                (midpoint_x4["y"] - midpoint_x5["y"])**2
            )
            
            min_length = min(min_length, distance)
            max_length = max(max_length, distance)

    if min_length != float('inf'):
        # Check if distances are within acceptable range
        if max_length - min_length > 4:
            return False, min_length, max_length

        if min_length < strand_width * 2:
            return False, min_length, max_length

    return True, min_length, max_length

def check_valid_distances(vertical_strands, horizontal_strands, m, n):
    """Check if distances between strands are valid"""
    # Check vertical strands
    v_aligned, v_min, v_max = check_strand_sequence_alignment(vertical_strands, True)
    if not v_aligned:
        return False

    # Check horizontal strands
    h_aligned, h_min, h_max = check_strand_sequence_alignment(horizontal_strands, False)
    if not h_aligned:
        return False

    return True

def generate_json(params):
    """Generate JSON data for the given parameters"""
    try:
        # Create local strands_data dictionary for this process
        strands_data = {
            'valid_lengths_vertical': {},
            'valid_lengths_horizontal': {}
        }
        mask_index = 0

        def create_masked_strand(v_strand, h_strand):
            nonlocal mask_index  # Access the outer index counter
            intersection = calculate_precise_intersection(v_strand, h_strand)
            if intersection is None:
                return None

            masked_strand = {
                "type": "MaskedStrand",
                "index": mask_index,  # Use the counter
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
            mask_index += 1  # Increment counter
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
        # Unpack parameters
        (m, n, horizontal_gap, vertical_gap, base_spacing,
         x4_vertical_angle, x5_vertical_angle,
         x4_horizontal_angle, x5_horizontal_angle,
         x4_length_extension, x5_length_extension,
         i_angle, j_angle) = params

        all_strands = []
        vertical_strands = {i: {} for i in range(1, m+1)}
        horizontal_strands = {i: {} for i in range(m+1, m+n+1)}

        def get_color():
            h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
            r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
            return {"r": r, "g": g, "b": b, "a": 255}

        colors = {i+1: get_color() for i in range(m+n)}
        base_x, base_y = 168.0*2, 168.0*2

        # Instead of adding strands directly to all_strands, we'll create separate lists
        main_strands_horizontal = []
        main_strands_vertical = []
        attached_strands_23_horizontal = []
        attached_strands_23_vertical = []
        attached_strands_45_horizontal = []
        attached_strands_45_vertical = []
        masks_strands_23 = []
        masks_strands_45 = []

        # Generate main strands (x_1) for vertical
        for i in range(m):
            start_x = base_x + i * base_spacing - 2 * horizontal_gap
            start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
            main_strand = create_strand(
                {"x": start_x + vertical_gap, "y": start_y},
                {"x": start_x - vertical_gap, "y": start_y - base_spacing + (n-1) * 4 * vertical_gap},
                color=colors[i+1], layer_name=f"{i+1}_1", set_number=i+1
            )
            main_strands_vertical.append(main_strand)
            vertical_strands[i+1]['main'] = main_strand

        # Generate main strands (x_1) for horizontal
        for i in range(n):
            start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
            start_y = base_y + i * base_spacing
            main_strand = create_strand(
                {"x": start_x, "y": start_y + horizontal_gap},
                {"x": start_x + base_spacing - (m-1) * 4 * vertical_gap, "y": start_y - horizontal_gap},
                color=colors[m+i+1], layer_name=f"{m+i+1}_1", set_number=m+i+1
            )
            main_strands_horizontal.append(main_strand)
            horizontal_strands[m+i+1]['main'] = main_strand

        # Generate x2 and x3 strands for horizontal and vertical
        for i in range(m):
            main_strand = vertical_strands[i+1]['main']
            
            strand2 = create_strand(
                main_strand["start"],
                {"x": main_strand["end"]["x"] + 2*vertical_gap,
                 "y": main_strand["end"]["y"] + 0.5*vertical_gap},
                color=colors[i+1], layer_name=f"{i+1}_2", set_number=i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_23_vertical.append(strand2)
            vertical_strands[i+1]['2'] = strand2

            strand3 = create_strand(
                main_strand["end"],
                {"x": main_strand["start"]["x"] - 2*vertical_gap,
                 "y": main_strand["start"]["y"] - 0.5*vertical_gap},
                color=colors[i+1], layer_name=f"{i+1}_3", set_number=i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_23_vertical.append(strand3)
            vertical_strands[i+1]['3'] = strand3

        # Generate x4 and x5 strands for horizontal and vertical
        for i in range(m):
            strand2 = vertical_strands[i+1]['2']
            strand3 = vertical_strands[i+1]['3']
            
            positions = calculate_x4_x5_positions(
                strand2, strand3,
                x4_vertical_angle, x5_vertical_angle,
                base_spacing
            )
            
            # Update x2 end point and create x4
            strand2["end"] = positions["x4"]["start"]
            strand2["control_points"] = calculate_control_points(strand2["start"], strand2["end"])
            
            strand4 = create_strand(
                positions["x4"]["start"],
                positions["x4"]["end"],
                color=colors[i+1],
                layer_name=f"{i+1}_4",
                set_number=i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_45_vertical.append(strand4)
            vertical_strands[i+1]['4'] = strand4
            
            # Update x3 end point and create x5
            strand3["end"] = positions["x5"]["start"]
            strand3["control_points"] = calculate_control_points(strand3["start"], strand3["end"])
            
            strand5 = create_strand(
                positions["x5"]["start"],
                positions["x5"]["end"],
                color=colors[i+1],
                layer_name=f"{i+1}_5",
                set_number=i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_45_vertical.append(strand5)
            vertical_strands[i+1]['5'] = strand5

        # Similar process for horizontal strands
        for i in range(n):
            main_strand = horizontal_strands[m+i+1]['main']
            
            strand2 = create_strand(
                main_strand["start"],
                {"x": main_strand["end"]["x"] - 0.5*horizontal_gap,
                 "y": main_strand["end"]["y"] + 2*horizontal_gap},
                color=colors[m+i+1],
                layer_name=f"{m+i+1}_2",
                set_number=m+i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_23_horizontal.append(strand2)
            horizontal_strands[m+i+1]['2'] = strand2

            strand3 = create_strand(
                main_strand["end"],
                {"x": main_strand["start"]["x"] + 0.5*horizontal_gap,
                 "y": main_strand["start"]["y"] - 2*horizontal_gap},
                color=colors[m+i+1],
                layer_name=f"{m+i+1}_3",
                set_number=m+i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_23_horizontal.append(strand3)
            horizontal_strands[m+i+1]['3'] = strand3

            positions = calculate_x4_x5_positions(
                strand2, strand3,
                x4_horizontal_angle, x5_horizontal_angle,
                base_spacing
            )
            
            # Update x2 end point and create x4
            strand2["end"] = positions["x4"]["start"]
            strand2["control_points"] = calculate_control_points(strand2["start"], strand2["end"])
            
            strand4 = create_strand(
                positions["x4"]["start"],
                positions["x4"]["end"],
                color=colors[m+i+1],
                layer_name=f"{m+i+1}_4",
                set_number=m+i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_45_horizontal.append(strand4)
            horizontal_strands[m+i+1]['4'] = strand4
            
            # Update x3 end point and create x5
            strand3["end"] = positions["x5"]["start"]
            strand3["control_points"] = calculate_control_points(strand3["start"], strand3["end"])
            
            strand5 = create_strand(
                positions["x5"]["start"],
                positions["x5"]["end"],
                color=colors[m+i+1],
                layer_name=f"{m+i+1}_5",
                set_number=m+i+1,
                strand_type="AttachedStrand"
            )
            attached_strands_45_horizontal.append(strand5)
            horizontal_strands[m+i+1]['5'] = strand5

            # Generate masks for x_2 and x_3
        for v_set in vertical_strands.values():
            for h_set in horizontal_strands.values():
                if '2' in v_set and '3' in h_set:
                    mask = create_masked_strand(v_set['2'], h_set['3'])
                    if mask:
                        masks_strands_23.append(mask)
                if '3' in v_set and '2' in h_set:
                    mask = create_masked_strand(v_set['3'], h_set['2'])
                    if mask:
                        masks_strands_23.append(mask)
        for v_set in vertical_strands.values():
            for h_set in horizontal_strands.values():
                if '4' in v_set and '5' in h_set:
                    mask = create_masked_strand(v_set['4'], h_set['5'])
                    if mask:
                        masks_strands_45.append(mask)
                if '5' in v_set and '4' in h_set:
                    mask = create_masked_strand(v_set['5'], h_set['4'])
                    if mask:
                        masks_strands_45.append(mask)

        print(len(masks_strands_45))
        # Combine all strands in the desired order
        all_strands_final = (
            main_strands_vertical +
            main_strands_horizontal +
            
            attached_strands_23_vertical +
            attached_strands_23_horizontal +
            masks_strands_23+
            attached_strands_45_vertical+
            attached_strands_45_horizontal +
            masks_strands_45
           
        )

        # Check if the generated configuration is valid
        if not check_valid_distances(vertical_strands, horizontal_strands, m, n):
            return None

        # Update indices
        for i, strand in enumerate(all_strands_final):
            strand["index"] = i

        data = {
            "strands": all_strands_final,
            "groups": {}
        }

        return data, (m, n, i_angle, j_angle)

    except Exception as e:
        print(f"Error processing params: {e}")
        return None

def calculate_x4_x5_pair_distances(strands_dict):
    """
    Calculate distances between x4-x5 pairs, starting from last x4 to first x5.
    Returns a list of minimum distances between paired strands.
    """
    set_numbers = sorted(strands_dict.keys())
    distances = []
    
    # Get all x4 and x5 strands
    x4_strands = []
    x5_strands = []
    for set_num in set_numbers:
        if '4' in strands_dict[set_num] and '5' in strands_dict[set_num]:
            x4_strands.append(strands_dict[set_num]['4'])
            x5_strands.append(strands_dict[set_num]['5'])
    
    # Reverse x4_strands to pair last x4 with first x5
    x4_strands.reverse()
    
    # Calculate distances for each pair
    for x4, x5 in zip(x4_strands, x5_strands):
        # Calculate distance from x4 start point to x5 line
        dist1 = calculate_point_to_line_distance_vectorized(
            x4['start'],
            x5['start'],
            x5['end']
        )
        
        # Calculate distance from x4 end point to x5 line
        dist2 = calculate_point_to_line_distance_vectorized(
            x4['end'],
            x5['start'],
            x5['end']
        )
        
        # Take the minimum distance
        min_distance = min(dist1, dist2)
        distances.append(min_distance)
    
    return distances

def main():
    start_time = time.time()
    
    # Remove the Manager and shared dictionaries since we're not using them anymore
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    os.makedirs(base_dir, exist_ok=True)

    # Configuration parameters
    strand_width = 28
    horizontal_gap = -28
    vertical_gap = -28
    base_spacing = 112
    x4_length_extension = 55
    x5_length_extension = 55

    # Angle ranges
    minimum_angle_h = 40  # For n
    maximum_angle_h = 42  # For n
    minimum_angle_v = 70  # For m
    maximum_angle_v = 70  # For m
    angle_step = 1

    vertical_angles = np.arange(minimum_angle_v, maximum_angle_v + 1, angle_step)
    horizontal_angles = np.arange(minimum_angle_h, maximum_angle_h + 1, angle_step)

    n_values = [3]
    m_values = [1]

    # Process configurations
    for m in m_values:
        for n in n_values:
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            os.makedirs(output_dir, exist_ok=True)

            print(f"Processing m={m}, n={n} configuration...")
            
            total_combinations = len(vertical_angles) * len(horizontal_angles)
            
            with Pool(processes=max(cpu_count() - 1, 1)) as pool:
                params_list = [
                    (m, n, horizontal_gap, vertical_gap, base_spacing,
                     i_angle+90, (i_angle+90 ) % 360,
                     j_angle+90, (j_angle+90 ) % 360,
                     x4_length_extension, x5_length_extension,
                     i_angle, j_angle)
                    for i_angle in vertical_angles
                    for j_angle in horizontal_angles
                ]
                
                for result in tqdm(pool.imap_unordered(generate_json, params_list),
                                 total=total_combinations,
                                 desc=f"m{m}xn{n}"):
                    if result is not None:
                        data, (m, n, i_angle, j_angle) = result
                        
                        filename = f"m{m}_n{n}_va{i_angle}_ha{j_angle}.json"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w') as f:
                            json.dump(data, f)

    print("\nProcessing complete!")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main() 