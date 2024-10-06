import json
import os
import random
import colorsys

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26):
    strands = []
    index = 0
    base_x, base_y = 104, 156.0
    
    def get_color():
        # Generate a random color using HSL color space
        h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
        return {"r": r, "g": g, "b": b, "a": 255}
    
    def add_strand(start, end, color, layer_name, set_number, strand_type="Strand"):
        # Helper function to create and add a strand to the strands list
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
            "is_start_side": strand_type == "Strand"
        }
        if strand_type != "Strand":
            strand["parent_layer_name"] = f"{set_number}_1"
        strands.append(strand)
        index += 1
        return strand

    # Generate colors for each set
    colors = {i+1: get_color() for i in range(m+n)}
    
    # Generate vertical strands
    for i in range(m):
        start_x = base_x + i * 104.0 - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        main_strand = add_strand(
            {"x": start_x + vertical_gap, "y": start_y},
            {"x": start_x - vertical_gap, "y": start_y - 104.0 + (n-1) * 4 * vertical_gap},
            colors[i+1], f"{i+1}_1", i+1
        )
        # Add attached strands for the main vertical strand
        add_strand(main_strand["start"], 
                   {"x": main_strand["end"]["x"] + 2*vertical_gap, "y": main_strand["end"]["y"] + 2*vertical_gap},
                   colors[i+1], f"{i+1}_2", i+1, "AttachedStrand")
        add_strand(main_strand["end"], 
                   {"x": main_strand["start"]["x"] - 2*vertical_gap, "y": main_strand["start"]["y"] - 2*vertical_gap},
                   colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")

    # Generate horizontal strands
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * 104.0
        main_strand = add_strand(
            {"x": start_x, "y": start_y + horizontal_gap},
            {"x": start_x + 104.0 - (m-1) * 4 * vertical_gap, "y": start_y - horizontal_gap},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        # Add attached strands for the main horizontal strand
        add_strand(main_strand["start"], 
                   {"x": main_strand["end"]["x"] - 2*horizontal_gap, "y": main_strand["end"]["y"] + 2*horizontal_gap},
                   colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand")
        add_strand(main_strand["end"], 
                   {"x": main_strand["start"]["x"] + 2*horizontal_gap, "y": main_strand["start"]["y"] - 2*horizontal_gap},
                   colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")

    # Generate masked strands
    vertical_strands = [s for s in strands if s["type"] == "AttachedStrand" and s["set_number"] <= m]
    horizontal_strands = [s for s in strands if s["type"] == "AttachedStrand" and s["set_number"] > m]

    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            if (v_strand["layer_name"].endswith("_2") and h_strand["layer_name"].endswith("_3")) or \
               (v_strand["layer_name"].endswith("_3") and h_strand["layer_name"].endswith("_2")):
                # Create masked strands at intersection points
                masked_strand = {
                    "type": "MaskedStrand",
                    "index": index,
                    "start": h_strand["start"],
                    "end": h_strand["end"],
                    "width": h_strand["width"],
                    "color": h_strand["color"],
                    "stroke_color": h_strand["stroke_color"],
                    "stroke_width": h_strand["stroke_width"],
                    "has_circles": [True, False],
                    "layer_name": f"{v_strand['layer_name']}_{h_strand['layer_name']}",
                    "set_number": int(f"{v_strand['set_number']}{h_strand['set_number']}"),
                    "is_first_strand": False,
                    "is_start_side": True,
                    "first_selected_strand": v_strand["layer_name"],
                    "second_selected_strand": h_strand["layer_name"]
                }
                strands.append(masked_strand)
                index += 1

    # Prepare the final data structure
    data = {
        "strands": strands,
        "groups": {}
    }

    print(f"Total strands: {len(strands)}")
    print(f"Masked strands: {len([s for s in strands if s['type'] == 'MaskedStrand'])}")

    return json.dumps(data, indent=2)

def main():
    # Set the output directory
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_063\ver_1_063_mxn_rh"
    os.makedirs(output_dir, exist_ok=True)

    # Generate JSON files for different m x n combinations
    for m in range(1, 11):
        for n in range(1, 11):
            json_content = generate_json(m, n)
            file_name = f"mxn_rh_{m}x{n}.json"
            with open(os.path.join(output_dir, file_name), 'w') as file:
                file.write(json_content)
            print(f"Generated {file_name}")

if __name__ == "__main__":
    main()