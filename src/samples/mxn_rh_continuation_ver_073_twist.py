import json
import os
import random
import colorsys
import math

def calculate_point_to_line_distance(point, line_start, line_end):
    """Calculate perpendicular distance from a point to a line segment"""
    # Vector from line start to point
    px = point["x"] - line_start["x"]
    py = point["y"] - line_start["y"]
    
    # Vector from line start to line end
    lx = line_end["x"] - line_start["x"]
    ly = line_end["y"] - line_start["y"]
    
    # Line length squared
    l2 = lx*lx + ly*ly
    
    # If line is a point, return distance to that point
    if l2 == 0:
        return math.sqrt(px*px + py*py)
    
    # Project point onto line
    t = max(0, min(1, (px*lx + py*ly) / l2))
    
    # Calculate projection point
    projection_x = line_start["x"] + t * lx
    projection_y = line_start["y"] + t * ly
    
    # Calculate distance
    dx = point["x"] - projection_x
    dy = point["y"] - projection_y
    return math.sqrt(dx*dx + dy*dy)

def get_midpoint(strand):
    """Get midpoint of a strand"""
    return {
        "x": (strand["start"]["x"] + strand["end"]["x"]) / 2,
        "y": (strand["start"]["y"] + strand["end"]["y"]) / 2
    }

def check_valid_distances(vertical_strands, horizontal_strands, m, n):
    """Check if distances between x4 and x5 are valid"""
    strand_width = strand_width  # Width of a strand
    min_distance = strand_width
    max_distance = strand_width*2
    
    # Check vertical strands
    for i in range(m):
        if '4' in vertical_strands[i+1] and '5' in vertical_strands[i+1]:
            x4_strand = vertical_strands[i+1]['4']
            x5_strand = vertical_strands[i+1]['5']
            
            # Get midpoint of x4
            midpoint = get_midpoint(x4_strand)
            
            # Calculate distance from midpoint to x5 line
            distance = calculate_point_to_line_distance(
                midpoint,
                x5_strand["start"],
                x5_strand["end"]
            )
            
            if not (min_distance <= distance <= max_distance):
                return False
    
    # Check horizontal strands
    for i in range(n):
        set_num = m + i + 1
        if '4' in horizontal_strands[set_num] and '5' in horizontal_strands[set_num]:
            x4_strand = horizontal_strands[set_num]['4']
            x5_strand = horizontal_strands[set_num]['5']
            
            # Get midpoint of x4
            midpoint = get_midpoint(x4_strand)
            
            # Calculate distance from midpoint to x5 line
            distance = calculate_point_to_line_distance(
                midpoint,
                x5_strand["start"],
                x5_strand["end"]
            )
            
            if not (min_distance <= distance <= max_distance):
                return False
    
    return True

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26, base_spacing=114,
                 x4_vertical_angle=0, x5_vertical_angle=0,
                 x4_horizontal_angle=0, x5_horizontal_angle=0,
                 x4_length_extension=0, x5_length_extension=0,
                 vertical_x2_offset=0, vertical_x3_offset=0,
                 horizontal_x2_offset=0, horizontal_x3_offset=0):
    all_strands = []  # Single list to maintain exact order
    index = 0
    base_x, base_y = base_spacing, 168.0
    
    # [Helper functions remain the same]
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
        return math.sqrt((end["x"] - start["x"])**2 + (end["y"] - start["y"])**2)

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
            
            # Add connection information for x_4 and x_5
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
    
    # Dictionary to store strands for masking
    vertical_strands = {i: {} for i in range(1, m+1)}  # Organized by set number
    horizontal_strands = {i: {} for i in range(m+1, m+n+1)}  # Organized by set number

    # Generate main strands (x_1) first
    for i in range(m):
        start_x = base_x + i * base_x - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        
        main_strand = create_strand(
            {"x": start_x + vertical_gap, "y": start_y},
            {"x": start_x - vertical_gap, "y": start_y - base_x + (n-1) * 4 * vertical_gap},
            colors[i+1], f"{i+1}_1", i+1
        )
        all_strands.append(main_strand)
        vertical_strands[i+1]['main'] = main_strand

    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * base_x
        
        main_strand = create_strand(
            {"x": start_x, "y": start_y + horizontal_gap},
            {"x": start_x + base_x - (m-1) * 4 * vertical_gap, "y": start_y - horizontal_gap},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        all_strands.append(main_strand)
        horizontal_strands[m+i+1]['main'] = main_strand

    # Generate x_2 and x_3 strands with immediate masking
    for i in range(m):
        main_strand = vertical_strands[i+1]['main']
        
        # Create x_2 with vertical offset
        strand2 = create_strand(main_strand["start"], 
            {"x": main_strand["end"]["x"] + 2*vertical_gap, "y": main_strand["end"]["y"] + 2*vertical_gap- vertical_x2_offset},
            colors[i+1], f"{i+1}_2", i+1, "AttachedStrand")
        all_strands.append(strand2)
        vertical_strands[i+1]['2'] = strand2

        # Check for masks with existing horizontal strands
        for h_set in horizontal_strands.values():
            if '3' in h_set:  # If horizontal strand has x_3
                mask = create_masked_strand(strand2, h_set['3'])
                if mask:
                    all_strands.append(mask)

        # Create x_3 with vertical offset
        strand3 = create_strand(main_strand["end"], 
            {"x": main_strand["start"]["x"] - 2*vertical_gap, "y": main_strand["start"]["y"] - 2*vertical_gap+vertical_x3_offset},
            colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
        all_strands.append(strand3)
        vertical_strands[i+1]['3'] = strand3

        # Check for masks with existing horizontal strands
        for h_set in horizontal_strands.values():
            if '2' in h_set:  # If horizontal strand has x_2
                mask = create_masked_strand(strand3, h_set['2'])
                if mask:
                    all_strands.append(mask)

    for i in range(n):
        main_strand = horizontal_strands[m+i+1]['main']
        
        # Create x_2 with horizontal offset
        strand2 = create_strand(main_strand["start"], 
            {"x": main_strand["end"]["x"] - 2*horizontal_gap+horizontal_x2_offset, "y": main_strand["end"]["y"] + 2*horizontal_gap},
            colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand")
        all_strands.append(strand2)
        horizontal_strands[m+i+1]['2'] = strand2

        # Check for masks with existing vertical strands
        for v_set in vertical_strands.values():
            if '3' in v_set:  # If vertical strand has x_3
                mask = create_masked_strand(v_set['3'], strand2)
                if mask:
                    all_strands.append(mask)

        # Create x_3 with horizontal offset
        strand3 = create_strand(main_strand["end"], 
            {"x": main_strand["start"]["x"] + 2*horizontal_gap-horizontal_x3_offset, "y": main_strand["start"]["y"] - 2*horizontal_gap},
            colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
        all_strands.append(strand3)
        horizontal_strands[m+i+1]['3'] = strand3

        # Check for masks with existing vertical strands
        for v_set in vertical_strands.values():
            if '2' in v_set:  # If vertical strand has x_2
                mask = create_masked_strand(v_set['2'], strand3)
                if mask:
                    all_strands.append(mask)

    # Generate x_4 and x_5 strands
    for i in range(m):
        strand2 = vertical_strands[i+1]['2']
        strand3 = vertical_strands[i+1]['3']
        
        # Create x_4
        length4 = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
        x4_end = calculate_endpoint_with_angle(strand2["end"], length4, x4_vertical_angle)
        strand4 = create_strand(strand2["end"], x4_end, colors[i+1], f"{i+1}_4", i+1, "AttachedStrand")
        all_strands.append(strand4)
        vertical_strands[i+1]['4'] = strand4
        
        # Create x_5
        length5 = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
        x5_end = calculate_endpoint_with_angle(strand3["end"], length5, x5_vertical_angle)
        strand5 = create_strand(strand3["end"], x5_end, colors[i+1], f"{i+1}_5", i+1, "AttachedStrand")
        all_strands.append(strand5)
        vertical_strands[i+1]['5'] = strand5

    for i in range(n):
        strand2 = horizontal_strands[m+i+1]['2']
        strand3 = horizontal_strands[m+i+1]['3']
        
        # Create x_4
        length4 = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
        x4_end = calculate_endpoint_with_angle(strand2["end"], length4, x4_horizontal_angle)
        strand4 = create_strand(strand2["end"], x4_end, colors[m+i+1], f"{m+i+1}_4", m+i+1, "AttachedStrand")
        all_strands.append(strand4)
        horizontal_strands[m+i+1]['4'] = strand4
        
        # Create x_5
        length5 = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
        x5_end = calculate_endpoint_with_angle(strand3["end"], length5, x5_horizontal_angle)
        strand5 = create_strand(strand3["end"], x5_end, colors[m+i+1], f"{m+i+1}_5", m+i+1, "AttachedStrand")
        all_strands.append(strand5)
        horizontal_strands[m+i+1]['5'] = strand5

        # Generate masks for x_4 and x_5 immediately
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
    
    return json.dumps(data, indent=2)

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\all possible rh continulation twist"
    os.makedirs(output_dir, exist_ok=True)
    
    x4_length_extension = 55
    x5_length_extension = 55
    horizontal_gap = -28
    vertical_gap = -28
    base_spacing = 112

    max_offset = abs(2 * vertical_gap)
    offset_step = 5

    # Loop through all possible angles and offsets
    for i in range(0, 50, 5):  # vertical angles
        for j in range(0, 50, 5):  # horizontal angles
            for v_x2_offset in range(0, max_offset, offset_step):
                for v_x3_offset in range(0, max_offset, offset_step):
                    for h_x2_offset in range(0, max_offset, offset_step):
                        for h_x3_offset in range(0, max_offset, offset_step):
                            x4_vertical_angle = i
                            x5_vertical_angle = (i + 180) % 360
                            x4_horizontal_angle = (j + 270) % 360
                            x5_horizontal_angle = (j + 90) % 360

                            for m in range(1, 2):
                                for n in range(1, 2):
                                    json_content = generate_json(
                                        m, n, horizontal_gap, vertical_gap, base_spacing,
                                        x4_vertical_angle, x5_vertical_angle,
                                        x4_horizontal_angle, x5_horizontal_angle,
                                        x4_length_extension, x5_length_extension,
                                        v_x2_offset, v_x3_offset,
                                        h_x2_offset, h_x3_offset
                                    )
                                    
                                    # Only write file if json_content is valid
                                    if json_content is not None:
                                        file_name = f"mxn_rh_{m}x{n}_v{i}_h{j}_vx2_{v_x2_offset}_vx3_{v_x3_offset}_hx2_{h_x2_offset}_hx3_{h_x3_offset}.json"
                                        file_path = os.path.join(output_dir, file_name)
                                        with open(file_path, 'w') as file:
                                            file.write(json_content)
                                        print(f"Generated {file_name}")
                                    else:
                                        print(f"Skipped invalid configuration: v{i}_h{j}_vx2_{v_x2_offset}_vx3_{v_x3_offset}_hx2_{h_x2_offset}_hx3_{h_x3_offset}")

if __name__ == "__main__":
    main()