import json
import os
import random
import colorsys
import math

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26, base_spacing=114, 
                 x4_vertical_angle=0, x5_vertical_angle=0,
                 x4_horizontal_angle=0, x5_horizontal_angle=0,
                 x4_length_extension=0, x5_length_extension=0):
    
    strands = []
    index = 0
    vertical_sets = {i+1: {} for i in range(m)}
    horizontal_sets = {m+i+1: {} for i in range(n)}
    
    base_x, base_y = base_spacing, 168.0
    
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
        
    def add_strand(start, end, color, layer_name, set_number, strand_type="Strand"):
        nonlocal index
        
        strand = {
            "type": strand_type,
            "index": index,
            "start": start,
            "end": end,
            "width": 46,
            "color": color,
            "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "stroke_width": 4,
            "has_circles": [True, True] if strand_type == "Strand" else [True, False],
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
        return {"x": round(x, 2), "y": round(y, 2)}

    def create_masked_strand(strand1, strand2):
        intersection = calculate_precise_intersection(strand1, strand2)
        if not intersection:
            return None

        masked_strand = {
            "type": "MaskedStrand",
            "index": index,
            "start": strand1["start"].copy(),
            "end": strand1["end"].copy(),
            "width": 46,
            "color": strand1["color"].copy(),
            "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "stroke_width": 4,
            "has_circles": [False, False],
            "layer_name": f"{strand1['layer_name']}_{strand2['layer_name']}",
            "set_number": strand1["set_number"],
            "control_points": calculate_control_points(strand1["start"], strand1["end"]),
            "first_selected_strand": strand1["layer_name"],
            "second_selected_strand": strand2["layer_name"],
            "deletion_rectangles": []
        }
        return masked_strand

    colors = {i+1: get_color() for i in range(m+n)}
    
    # Generate vertical strands (x_1)
    for i in range(m):
        start_x = base_x + i * base_x - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        main_strand = add_strand(
            {"x": start_x + vertical_gap, "y": start_y - 114.0 + (n-1) * 4 * vertical_gap},
            {"x": start_x - vertical_gap, "y": start_y},
            colors[i+1], f"{i+1}_1", i+1
        )
        vertical_sets[i+1]['main'] = main_strand

    # Generate horizontal strands (x_1)
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * base_x
        main_strand = add_strand(
            {"x": start_x + 114.0 - (m-1) * 4 * vertical_gap, "y": start_y + horizontal_gap},
            {"x": start_x, "y": start_y - horizontal_gap},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        horizontal_sets[m+i+1]['main'] = main_strand

    # Generate x_2 and x_3 strands
    for i in range(m):
        main_strand = vertical_sets[i+1]['main']
        strand2 = add_strand(main_strand["end"], 
                    {"x": main_strand["start"]["x"] - 2*vertical_gap, "y": main_strand["start"]["y"] + 2*vertical_gap},
                    colors[i+1], f"{i+1}_2", i+1, "AttachedStrand")
        strand3 = add_strand(main_strand["start"], 
                    {"x": main_strand["end"]["x"] + 2*vertical_gap, "y": main_strand["end"]["y"] - 2*vertical_gap},
                    colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
        vertical_sets[i+1].update({'2': strand2, '3': strand3})

    for i in range(n):
        main_strand = horizontal_sets[m+i+1]['main']
        strand2 = add_strand(main_strand["end"], 
                    {"x": main_strand["start"]["x"] - 2*horizontal_gap, "y": main_strand["start"]["y"] - 2*horizontal_gap},
                    colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand")
        strand3 = add_strand(main_strand["start"], 
                    {"x": main_strand["end"]["x"] + 2*horizontal_gap, "y": main_strand["end"]["y"] + 2*horizontal_gap},
                    colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
        horizontal_sets[m+i+1].update({'2': strand2, '3': strand3})

    # Generate masks for x_2 and x_3
    for v_set in vertical_sets.values():
        for h_set in horizontal_sets.values():
            mask = create_masked_strand(v_set['2'], h_set['3'])
            if mask:
                strands.append(mask)
            mask = create_masked_strand(v_set['3'], h_set['2'])
            if mask:
                strands.append(mask)

    # Generate x_4 and x_5 strands
    for i in range(m):
        strand2 = vertical_sets[i+1]['2']
        strand3 = vertical_sets[i+1]['3']
        
        # Use exact end points from strand2 and strand3 as starting points
        x4_length = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
        x4_end = calculate_endpoint_with_angle(strand2["end"], x4_length, x4_vertical_angle)
        strand4 = add_strand(strand2["end"], x4_end, colors[i+1], f"{i+1}_4", i+1, "AttachedStrand")
        
        x5_length = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
        x5_end = calculate_endpoint_with_angle(strand3["end"], x5_length, x5_vertical_angle)
        strand5 = add_strand(strand3["end"], x5_end, colors[i+1], f"{i+1}_5", i+1, "AttachedStrand")
        
        vertical_sets[i+1].update({'4': strand4, '5': strand5})

    for i in range(n):
        strand2 = horizontal_sets[m+i+1]['2']
        strand3 = horizontal_sets[m+i+1]['3']
        
        # Use exact end points from strand2 and strand3 as starting points
        x4_length = calculate_strand_length(strand2["start"], strand2["end"]) + x4_length_extension
        x4_end = calculate_endpoint_with_angle(strand2["end"], x4_length, x4_horizontal_angle)
        strand4 = add_strand(strand2["end"], x4_end, colors[m+i+1], f"{m+i+1}_4", m+i+1, "AttachedStrand")
        
        x5_length = calculate_strand_length(strand3["start"], strand3["end"]) + x5_length_extension
        x5_end = calculate_endpoint_with_angle(strand3["end"], x5_length, x5_horizontal_angle)
        strand5 = add_strand(strand3["end"], x5_end, colors[m+i+1], f"{m+i+1}_5", m+i+1, "AttachedStrand")
        
        horizontal_sets[m+i+1].update({'4': strand4, '5': strand5})

    # Generate masks for x_4 and x_5
    for v_set in vertical_sets.values():
        for h_set in horizontal_sets.values():
            mask = create_masked_strand(v_set['4'], h_set['5'])
            if mask:
                strands.append(mask)
            mask = create_masked_strand(v_set['5'], h_set['4'])
            if mask:
                strands.append(mask)

    data = {
        "strands": strands,
        "groups": {}
    }
    
    return json.dumps(data, indent=2)

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\continuing_mxn_lh"
    os.makedirs(output_dir, exist_ok=True)

    x4_vertical_angle = 0
    x5_vertical_angle = 180
    x4_horizontal_angle = 270
    x5_horizontal_angle = 90
    x4_length_extension = 55
    x5_length_extension = 55

    for m in range(1, 11):
        for n in range(1, 11):
            horizontal_gap = -28
            vertical_gap = -28
            base_spacing = 112
            
            json_content = generate_json(m, n, horizontal_gap, vertical_gap, base_spacing,
                                      x4_vertical_angle, x5_vertical_angle,
                                      x4_horizontal_angle, x5_horizontal_angle,
                                      x4_length_extension, x5_length_extension)
            file_name = f"mxn_lh_{m}x{n}.json"
            with open(os.path.join(output_dir, file_name), 'w') as file:
                file.write(json_content)
            print(f"Generated {file_name}")

if __name__ == "__main__":
    main()