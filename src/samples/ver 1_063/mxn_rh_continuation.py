import json
import os
import random
import colorsys

def generate_json(m, n, horizontal_gap=-26, vertical_gap=-26):
    strands = []
    index = 0
    base_x, base_y = 104, 156.0
    
    def get_color():
        h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
        return {"r": r, "g": g, "b": b, "a": 255}
    
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
            "has_circles": [True, True],
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

    colors = {i+1: get_color() for i in range(m+n)}
    
    # Generate vertical strands
    for i in range(m):
        start_x = base_x + i * 104.0
        start_y = base_y - (n-1) * 4 * vertical_gap
        main_strand = add_strand(
            {"x": start_x, "y": start_y},
            {"x": start_x + 52, "y": start_y + 104},
            colors[i+1], f"{i+1}_1", i+1
        )
        # Add attached strands for the main vertical strand
        add_strand(main_strand["end"], 
                   {"x": main_strand["end"]["x"], "y": main_strand["start"]["y"]},
                   colors[i+1], f"{i+1}_2", i+1, "AttachedStrand")
        add_strand(main_strand["start"], 
                   {"x": main_strand["start"]["x"], "y": main_strand["end"]["y"]},
                   colors[i+1], f"{i+1}_3", i+1, "AttachedStrand")
        add_strand(main_strand["start"], 
                   {"x": main_strand["start"]["x"], "y": main_strand["start"]["y"] - 52},
                   colors[i+1], f"{i+1}_4", i+1, "AttachedStrand")
        add_strand(main_strand["end"], 
                   {"x": main_strand["end"]["x"], "y": main_strand["end"]["y"] + 52},
                   colors[i+1], f"{i+1}_5", i+1, "AttachedStrand")

    # Generate horizontal strands
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap
        start_y = base_y + i * 104.0
        main_strand = add_strand(
            {"x": start_x, "y": start_y},
            {"x": start_x - 104, "y": start_y + 52},
            colors[m+i+1], f"{m+i+1}_1", m+i+1
        )
        # Add attached strands for the main horizontal strand
        add_strand(main_strand["end"], 
                   {"x": main_strand["end"]["x"] + 104, "y": main_strand["end"]["y"]},
                   colors[m+i+1], f"{m+i+1}_2", m+i+1, "AttachedStrand")
        add_strand(main_strand["start"], 
                   {"x": main_strand["start"]["x"] - 104, "y": main_strand["start"]["y"]},
                   colors[m+i+1], f"{m+i+1}_3", m+i+1, "AttachedStrand")
        add_strand(main_strand["start"], 
                   {"x": main_strand["start"]["x"] + 52, "y": main_strand["start"]["y"]},
                   colors[m+i+1], f"{m+i+1}_4", m+i+1, "AttachedStrand")
        add_strand(main_strand["end"], 
                   {"x": main_strand["end"]["x"] - 52, "y": main_strand["end"]["y"]},
                   colors[m+i+1], f"{m+i+1}_5", m+i+1, "AttachedStrand")

    # Generate masked strands
    vertical_strands = [s for s in strands if s["type"] == "AttachedStrand" and s["set_number"] <= m]
    horizontal_strands = [s for s in strands if s["type"] == "AttachedStrand" and s["set_number"] > m]

    for v_strand in vertical_strands:
        for h_strand in horizontal_strands:
            if (v_strand["layer_name"].endswith("_2") and h_strand["layer_name"].endswith("_2")) or \
               (v_strand["layer_name"].endswith("_3") and h_strand["layer_name"].endswith("_3")):
                masked_strand = {
                    "type": "MaskedStrand",
                    "index": index,
                    "start": v_strand["start"],
                    "end": v_strand["end"],
                    "width": v_strand["width"],
                    "color": v_strand["color"],
                    "stroke_color": v_strand["stroke_color"],
                    "stroke_width": v_strand["stroke_width"],
                    "has_circles": [True, True],
                    "layer_name": f"{v_strand['layer_name']}_{h_strand['layer_name']}",
                    "set_number": int(f"{v_strand['set_number']}{h_strand['set_number']}"),
                    "is_first_strand": False,
                    "is_start_side": True,
                    "first_selected_strand": v_strand["layer_name"],
                    "second_selected_strand": h_strand["layer_name"]
                }
                strands.append(masked_strand)
                index += 1

    data = {
        "strands": strands,
        "groups": {}
    }

    return json.dumps(data, indent=2)

def main():
    output_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_063\continuing_mxn_rh"
    os.makedirs(output_dir, exist_ok=True)

    for m in range(1, 5):
        for n in range(1, 5):
            json_content = generate_json(m, n)
            file_name = f"mxn_rh_{m}x{n}.json"
            with open(os.path.join(output_dir, file_name), 'w') as file:
                file.write(json_content)
            print(f"Generated {file_name}")

if __name__ == "__main__":
    main()