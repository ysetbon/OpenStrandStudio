import json
import os
import random
import colorsys
import math

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26, base_spacing=114):
    """
    Generate right-hand strand pattern with adjustable spacings
    
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
            strand["parent_layer_name"] = f"{set_number}_1"
        
        strands.append(strand)
        index += 1
        return strand

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
    
    # Generate vertical strands (right-hand pattern)
    vertical_strands = []
    for i in range(m):
        start_x = base_x + i * base_x - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        main_strand = add_strand(
            {"x": start_x + vertical_gap, "y": start_y},
            {"x": start_x - vertical_gap, "y": start_y - base_x + (n-1) * 4 * vertical_gap},
            colors[i+1], f"{i+1}_1", i+1
        )
        vertical_strands.extend([
            add_strand(main_strand["start"], 
                      {"x": main_strand["end"]["x"] + 2*vertical_gap, "y": main_strand["end"]["y"] + 2*vertical_gap},
                      colors[i+1], f"{i+1}_2", i+1, "AttachedStrand"),
            add_strand(main_strand["end"], 
                      {"x": main_strand["start"]["x"] - 2*vertical_gap, "y": main_strand["start"]["y"] - 2*vertical_gap},
                      colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
        ])

    # Generate horizontal strands (right-hand pattern)
    horizontal_strands = []
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * base_x
        main_strand = add_strand(
            {"x": start_x, "y": start_y + horizontal_gap},
            {"x": start_x + base_x - (m-1) * 4 * vertical_gap, "y": start_y - horizontal_gap},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        horizontal_strands.extend([
            add_strand(main_strand["start"], 
                      {"x": main_strand["end"]["x"] - 2*horizontal_gap, "y": main_strand["end"]["y"] + 2*horizontal_gap},
                      colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand"),
            add_strand(main_strand["end"], 
                      {"x": main_strand["start"]["x"] + 2*horizontal_gap, "y": main_strand["start"]["y"] - 2*horizontal_gap},
                      colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
        ])

    # Generate masked strands for right-hand pattern
    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            if ((v_strand["layer_name"].endswith("_2") and h_strand["layer_name"].endswith("_3")) or
                (v_strand["layer_name"].endswith("_3") and h_strand["layer_name"].endswith("_2"))):
                
                intersection = calculate_precise_intersection(v_strand, h_strand)
                if intersection is None:
                    continue

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
                strands.append(masked_strand)
                index += 1

    data = {
        "strands": strands,
        "groups": {}
    }
    
    return json.dumps(data, indent=2)

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\ver_1_73_mxn_rh"
    os.makedirs(output_dir, exist_ok=True)

    for m in range(1, 11):
        for n in range(1, 11):
            horizontal_gap = -28  # Adjusted for consistency with left-hand version
            vertical_gap = -28    # Adjusted for consistency with left-hand version
            base_spacing = 112    # Adjusted for consistency with left-hand version
            
            json_content = generate_json(m, n, horizontal_gap, vertical_gap, base_spacing)
            file_name = f"mxn_rh_{m}x{n}.json"
            with open(os.path.join(output_dir, file_name), 'w') as file:
                file.write(json_content)
            print(f"Generated {file_name}")

if __name__ == "__main__":
    main()