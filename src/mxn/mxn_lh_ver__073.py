import json
import os
import random
import colorsys
import math

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26, base_spacing=114):
    """
    Generate strand pattern with adjustable spacings while maintaining original logic
    
    Args:
        m (int): Number of vertical sets
        n (int): Number of horizontal sets
        horizontal_gap (float): Horizontal spacing parameter (default: -26)
        vertical_gap (float): Vertical spacing parameter (default: -26)
        base_spacing (float): Base spacing between elements (default: 114)
    """
    strands = []
    index = 0
    base_x, base_y = base_spacing, 168.0
    
    def get_color():
        h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
        return {"r": r, "g": g, "b": b, "a": 255}

    def calculate_control_points(start, end):
        dx = float(end["x"] - start["x"])
        dy = float(end["y"] - start["y"])
        print(float(start["x"] + dx / 3))

        return [
            {"x": start["x"], "y": start["y"]},
            {"x": start["x"], "y": start["y"]}
        ]
        
    def add_strand(start, end, color, layer_name, set_number, strand_type="Strand"):
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
            strand["attached_to"] = f"{set_number}_1"
        
        strands.append(strand)
        index += 1
        return strand
    def calculate_bounding_rectangle_3(strand):
        x1, y1 = strand["start"]["x"], strand["start"]["y"]
        x2, y2 = strand["end"]["x"], strand["end"]["y"]
        width = strand["width"]
        width = width+5
        half_width = width / 2.0

        # Calculate the strand vector and its length
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0: # Handle zero-length strands
            # Return a square centered at the point
            return {
                'top_left': [x1 - half_width, y1 - half_width],
                'top_right': [x1 + half_width, y1 - half_width],
                'bottom_left': [x1 - half_width, y1 + half_width],
                'bottom_right': [x1 + half_width, y1 + half_width]
            }

        # Normalized perpendicular vector
        perp_dx = -dy / length
        perp_dy = dx / length

        # Calculate the four corner points of the oriented rectangle
        p1 = {"x": x1 + perp_dx * half_width, "y": y1 + perp_dy * half_width} # Start, positive offset
        p2 = {"x": x1 - perp_dx * half_width, "y": y1 - perp_dy * half_width} # Start, negative offset
        p3 = {"x": x2 + perp_dx * half_width, "y": y2 + perp_dy * half_width} # End, positive offset
        p4 = {"x": x2 - perp_dx * half_width, "y": y2 - perp_dy * half_width} # End, negative offset

        # Return the four corner points with the expected keys
        # The loading code uses these to derive an axis-aligned bounding box
        return {
            'top_left': [p1['x'], p1['y']],
            'top_right': [p3['x'], p3['y']],
            'bottom_left': [p2['x'], p2['y']],
            'bottom_right': [p4['x'], p4['y']]
        }    

    def calculate_bounding_rectangle_2(strand):
        x1, y1 = strand["start"]["x"], strand["start"]["y"]
        x2, y2 = strand["end"]["x"], strand["end"]["y"]
        width = strand["width"]
        width = width+10
        half_width = width / 2.0

        # Calculate the strand vector and its length
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0: # Handle zero-length strands
            # Return a square centered at the point
            return {
                'top_left': [x1 - half_width, y1 - half_width],
                'top_right': [x1 + half_width, y1 - half_width],
                'bottom_left': [x1 - half_width, y1 + half_width],
                'bottom_right': [x1 + half_width, y1 + half_width]
            }

        # Normalized perpendicular vector
        perp_dx = -dy / length
        perp_dy = dx / length

        # Calculate the four corner points of the oriented rectangle
        p1 = {"x": x1 + perp_dx * half_width, "y": y1 + perp_dy * half_width} # Start, positive offset
        p2 = {"x": x1 - perp_dx * half_width, "y": y1 - perp_dy * half_width} # Start, negative offset
        p3 = {"x": x2 + perp_dx * half_width, "y": y2 + perp_dy * half_width} # End, positive offset
        p4 = {"x": x2 - perp_dx * half_width, "y": y2 - perp_dy * half_width} # End, negative offset

        # Return the four corner points with the expected keys
        # The loading code uses these to derive an axis-aligned bounding box
        return {
            'top_left': [p1['x'], p1['y']],
            'top_right': [p3['x'], p3['y']],
            'bottom_left': [p2['x'], p2['y']],
            'bottom_right': [p4['x'], p4['y']]
        }
    def calculate_bounding_rectangle(strand):
        x1, y1 = strand["start"]["x"], strand["start"]["y"]
        x2, y2 = strand["end"]["x"], strand["end"]["y"]
        width = strand["width"]
        width = width-2
        half_width = width / 2.0

        # Calculate the strand vector and its length
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0: # Handle zero-length strands
            # Return a square centered at the point
            return {
                'top_left': [x1 - half_width, y1 - half_width],
                'top_right': [x1 + half_width, y1 - half_width],
                'bottom_left': [x1 - half_width, y1 + half_width],
                'bottom_right': [x1 + half_width, y1 + half_width]
            }

        # Normalized perpendicular vector
        perp_dx = -dy / length
        perp_dy = dx / length

        # Calculate the four corner points of the oriented rectangle
        p1 = {"x": x1 + perp_dx * half_width, "y": y1 + perp_dy * half_width} # Start, positive offset
        p2 = {"x": x1 - perp_dx * half_width, "y": y1 - perp_dy * half_width} # Start, negative offset
        p3 = {"x": x2 + perp_dx * half_width, "y": y2 + perp_dy * half_width} # End, positive offset
        p4 = {"x": x2 - perp_dx * half_width, "y": y2 - perp_dy * half_width} # End, negative offset

        # Return the four corner points with the expected keys
        # The loading code uses these to derive an axis-aligned bounding box
        return {
            'top_left': [p1['x'], p1['y']],
            'top_right': [p3['x'], p3['y']],
            'bottom_left': [p2['x'], p2['y']],
            'bottom_right': [p4['x'], p4['y']]
        }
        
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
    
    # Generate vertical strands
    vertical_strands = []
    for i in range(m):
        start_x = base_x + i * base_x - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        main_strand = add_strand(
            {"x": start_x + vertical_gap, "y": start_y - 114.0 + (n-1) * 4 * vertical_gap},
            {"x": start_x - vertical_gap, "y": start_y},
            colors[i+1], f"{i+1}_1", i+1
        )
        vertical_strands.extend([
            add_strand(main_strand["end"], 
                      {"x": main_strand["start"]["x"] - 2*vertical_gap, "y": main_strand["start"]["y"] + 2*vertical_gap},
                      colors[i+1], f"{i+1}_2", i+1, "AttachedStrand"),
            add_strand(main_strand["start"], 
                      {"x": main_strand["end"]["x"] + 2*vertical_gap, "y": main_strand["end"]["y"] - 2*vertical_gap},
                      colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
        ])

    # Generate horizontal strands
    horizontal_strands = []
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * base_x
        main_strand = add_strand(
            {"x": start_x + 114.0 - (m-1) * 4 * vertical_gap, "y": start_y + horizontal_gap},
            {"x": start_x, "y": start_y - horizontal_gap},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        horizontal_strands.extend([
            add_strand(main_strand["end"], 
                      {"x": main_strand["start"]["x"] - 2*horizontal_gap, "y": main_strand["start"]["y"] - 2*horizontal_gap},
                      colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand"),
            add_strand(main_strand["start"], 
                      {"x": main_strand["end"]["x"] + 2*horizontal_gap, "y": main_strand["end"]["y"] + 2*horizontal_gap},
                      colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
        ])

    # Generate masked strands
    # Type A
    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            is_v2 = v_strand["layer_name"].endswith("_2")
            is_h2 = h_strand["layer_name"].endswith("_2")
            is_v3 = v_strand["layer_name"].endswith("_3")
            is_h3 = h_strand["layer_name"].endswith("_3")

            if (is_v2 and is_h2) or (is_v3 and is_h3):
                intersection = calculate_precise_intersection(v_strand, h_strand)
                if intersection is None:
                    continue

                # Create deletion rectangles for other vertical strands (assuming V is primary)
                deletion_rect = []

                # Add bounding rectangles for all other vertical strands
                for other_h_strand in horizontal_strands:
                    if other_h_strand["index"] != h_strand["index"]:
                        h_rect = calculate_bounding_rectangle(other_h_strand)
                        if h_rect:
                            deletion_rect.append(h_rect)

                if not deletion_rect:
                    print(f"Warning: No other vertical strands found to create deletion mask for intersection involving {v_strand['layer_name']}")

                masked_strand = {
                    "type": "MaskedStrand",
                    "index": index,
                    "start": intersection.copy(),
                    "end": intersection.copy(),
                    "width": 46,
                    "color": v_strand["color"].copy(),
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [False, False],
                    "layer_name": f"{v_strand['layer_name']}_{h_strand['layer_name']}",
                    "set_number": v_strand["set_number"],
                    "first_selected_strand": v_strand["layer_name"],
                    "second_selected_strand": h_strand["layer_name"],
                    "deletion_rectangles": deletion_rect,
                    "custom_mask_path": None,
                    "base_center_point": intersection,
                    "edited_center_point": intersection.copy(),
                    "is_first_strand": False,
                    "is_start_side": False
                }
                strands.append(masked_strand)
                index += 1

    # Type B - V2/H3
    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            is_v2 = v_strand["layer_name"].endswith("_2")
            is_h3 = h_strand["layer_name"].endswith("_3")

            if is_v2 and is_h3:
                intersection = calculate_precise_intersection(v_strand, h_strand)
                if intersection is not None:
                    # Create deletion rectangles based on the current horizontal and other vertical strands
                    deletion_rect = []
                    for over_h_strand in horizontal_strands:
                        if over_h_strand["index"] == h_strand["index"]:
                            h_rect = calculate_bounding_rectangle_3(over_h_strand)
                            if h_rect:
                                deletion_rect.append(h_rect)

                    for over_v_strand in vertical_strands:
                        if over_v_strand["index"] != v_strand["index"]:
                            v_rect = calculate_bounding_rectangle(over_v_strand)
                            if v_rect:
                                deletion_rect.append(v_rect)

                    if not deletion_rect:
                         print(f"Warning: No strands found to create deletion mask for Type B (V2/H3) intersection involving {h_strand['layer_name']} and {v_strand['layer_name']}")

                    masked_strand_b_v2h3 = {
                        "type": "MaskedStrand",
                        "index": index,
                        "start": intersection.copy(),
                        "end": intersection.copy(),
                        "width": 46, # Using 46 for consistency.
                        "color": h_strand["color"].copy(), # Use horizontal strand color
                        "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                        "stroke_width": 4,
                        "has_circles": [False, False],
                        "layer_name": f"{h_strand['layer_name']}_{v_strand['layer_name']}", # Indicate H primary, V2/H3 Type B
                        "set_number": h_strand["set_number"], # Use horizontal strand set number
                        "first_selected_strand": h_strand["layer_name"],
                        "second_selected_strand": v_strand["layer_name"],
                        "deletion_rectangles": deletion_rect,
                        "custom_mask_path": None,
                        "base_center_point": intersection,
                        "edited_center_point": intersection.copy(),
                        "is_first_strand": False,
                        "is_start_side": False
                    }
                    strands.append(masked_strand_b_v2h3)
                    index += 1

    # Type B - V3/H2
    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            is_v3 = v_strand["layer_name"].endswith("_3")
            is_h2 = h_strand["layer_name"].endswith("_2")

            if is_v3 and is_h2:
                intersection = calculate_precise_intersection(v_strand, h_strand)
                if intersection is not None:
                     # Create deletion rectangles based on the current horizontal and other vertical strands
                    deletion_rect = []
                    for over_h_strand in horizontal_strands:
                        if over_h_strand["index"] == h_strand["index"]:
                            h_rect = calculate_bounding_rectangle_3(over_h_strand)
                            if h_rect:
                                deletion_rect.append(h_rect)

                    for over_v_strand in vertical_strands:
                        if over_v_strand["index"] != v_strand["index"]:
                            v_rect = calculate_bounding_rectangle(over_v_strand)
                            if v_rect:
                                deletion_rect.append(v_rect)

                    if not deletion_rect:
                         print(f"Warning: No strands found to create deletion mask for Type B (V3/H2) intersection involving {h_strand['layer_name']} and {v_strand['layer_name']}")

                    masked_strand_b_v3h2 = {
                        "type": "MaskedStrand",
                        "index": index,
                        "start": intersection.copy(),
                        "end": intersection.copy(),
                        "width": 46, # Using 46 for consistency.
                        "color": h_strand["color"].copy(), # Use horizontal strand color
                        "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                        "stroke_width": 4,
                        "has_circles": [False, False],
                        "layer_name": f"{h_strand['layer_name']}_{v_strand['layer_name']}", 
                        "set_number": h_strand["set_number"], # Use horizontal strand set number
                        "first_selected_strand": h_strand["layer_name"],
                        "second_selected_strand": v_strand["layer_name"],
                        "deletion_rectangles": deletion_rect,
                        "custom_mask_path": None,
                        "base_center_point": intersection,
                        "edited_center_point": intersection.copy(),
                        "is_first_strand": False,
                        "is_start_side": False
                    }
                    strands.append(masked_strand_b_v3h2)
                    index += 1

    data = {
        "strands": strands,
        "groups": {}
    }
    
    return json.dumps(data, indent=2)

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\ver_1_73_mxn_lh"
    os.makedirs(output_dir, exist_ok=True)

    # Example with different spacings
    for m in range(1, 11):
        for n in range(1, 11):
            # You can adjust these values to change the spacing
            horizontal_gap = -28  # Adjust this to change horizontal spacing
            vertical_gap = -28    # Adjust this to change vertical spacing
            base_spacing = 112    # Adjust this to change overall spacing
            
            json_content = generate_json(m, n, horizontal_gap, vertical_gap, base_spacing)
            file_name = f"mxn_lh_{m}x{n}.json"
            with open(os.path.join(output_dir, file_name), 'w') as file:
                file.write(json_content)
            print(f"Generated {file_name}")

if __name__ == "__main__":
    main()