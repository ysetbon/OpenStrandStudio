import json
import os

def create_base_strands():
    """Create the base strand data needed for mask generation with exact coordinates"""
    base_strands = []
    
    # Exact coordinates from the original JSON
    # Note: Set 15 already has masks in the original file, so we start from set 14
    strand_data = [
        # Set 1
        {"layer_name": "1_4", "start": {"x": 504.0, "y": 1176.0}, "end": {"x": 1422.0, "y": 1008.0}},
        {"layer_name": "1_5", "start": {"x": 1316.0, "y": 1092.0}, "end": {"x": 392.0, "y": 1296.0}},
        # Set 2
        {"layer_name": "2_4", "start": {"x": 504.0, "y": 1008.0}, "end": {"x": 1436.0, "y": 820.0}},
        {"layer_name": "2_5", "start": {"x": 1316.0, "y": 924.0}, "end": {"x": 372.0, "y": 1141.0}},
        # Set 3
        {"layer_name": "3_4", "start": {"x": 504.0, "y": 840.0}, "end": {"x": 1456.0, "y": 631.0}},
        {"layer_name": "3_5", "start": {"x": 1316.0, "y": 756.0}, "end": {"x": 367.0, "y": 965.0}},
        # Set 4
        {"layer_name": "4_4", "start": {"x": 504.0, "y": 672.0}, "end": {"x": 1462.0, "y": 458.0}},
        {"layer_name": "4_5", "start": {"x": 1316.0, "y": 588.0}, "end": {"x": 361.0, "y": 786.0}},
        # Set 5
        {"layer_name": "5_4", "start": {"x": 504.0, "y": 504.0}, "end": {"x": 1484.0, "y": 280.0}},
        {"layer_name": "5_5", "start": {"x": 1316.0, "y": 420.0}, "end": {"x": 364.0, "y": 621.0}},
        # Set 6
        {"layer_name": "6_4", "start": {"x": 504.0, "y": 336.0}, "end": {"x": 1475.0, "y": 120.0}},
        {"layer_name": "6_5", "start": {"x": 1316.0, "y": 252.0}, "end": {"x": 362.0, "y": 438.0}},
        # Set 7
        {"layer_name": "7_4", "start": {"x": 504.0, "y": 168.0}, "end": {"x": 1467.0, "y": -45.0}},
        {"layer_name": "7_5", "start": {"x": 1316.0, "y": 84.0}, "end": {"x": 341.0, "y": 273.0}},
        # Set 8
        {"layer_name": "8_4", "start": {"x": 504.0, "y": 0.0}, "end": {"x": 1461.0, "y": -208.0}},
        {"layer_name": "8_5", "start": {"x": 1316.0, "y": -84.0}, "end": {"x": 369.0, "y": 97.0}},
        # Set 9
        {"layer_name": "9_4", "start": {"x": 504.0, "y": -168.0}, "end": {"x": 1456.0, "y": -364.0}},
        {"layer_name": "9_5", "start": {"x": 1316.0, "y": -252.0}, "end": {"x": 367.0, "y": -64.0}},
        # Set 10
        {"layer_name": "10_4", "start": {"x": 504.0, "y": -336.0}, "end": {"x": 1445.0, "y": -550.0}},
        {"layer_name": "10_5", "start": {"x": 1316.0, "y": -420.0}, "end": {"x": 373.0, "y": -247.0}},
        # Set 11
        {"layer_name": "11_4", "start": {"x": 504.0, "y": -504.0}, "end": {"x": 1456.0, "y": -721.0}},
        {"layer_name": "11_5", "start": {"x": 1316.0, "y": -588.0}, "end": {"x": 358.0, "y": -404.0}},
        # Set 12
        {"layer_name": "12_4", "start": {"x": 504.0, "y": 1344.0}, "end": {"x": 1396.0, "y": 1174.0}},
        {"layer_name": "12_5", "start": {"x": 1316.0, "y": 1260.0}, "end": {"x": 396.0, "y": 1460.0}},
        # Set 13
        {"layer_name": "13_4", "start": {"x": 504.0, "y": 1512.0}, "end": {"x": 1418.0, "y": 1338.0}},
        {"layer_name": "13_5", "start": {"x": 1316.0, "y": 1428.0}, "end": {"x": 386.0, "y": 1614.0}},
        # Set 14
        {"layer_name": "14_4", "start": {"x": 504.0, "y": 1680.0}, "end": {"x": 1448.0, "y": 1473.0}},
        {"layer_name": "14_5", "start": {"x": 1316.0, "y": 1596.0}, "end": {"x": 493.0, "y": 1790.0}},
        # Set 16
        {"layer_name": "16_4", "start": {"x": 700.0, "y": -868.0}, "end": {"x": 868.0, "y": 1932.0}},
        {"layer_name": "16_5", "start": {"x": 784.0, "y": 1848.0}, "end": {"x": 560.0, "y": -868.0}},
        # Set 17
        {"layer_name": "17_4", "start": {"x": 868.0, "y": -896.0}, "end": {"x": 1036.0, "y": 1876.0}},
        {"layer_name": "17_5", "start": {"x": 952.0, "y": 1820.0}, "end": {"x": 784.0, "y": -896.0}},
        # Set 18
        {"layer_name": "18_4", "start": {"x": 1036.0, "y": -924.0}, "end": {"x": 1232.0, "y": 1876.0}},
        {"layer_name": "18_5", "start": {"x": 1120.0, "y": 1764.0}, "end": {"x": 952.0, "y": -924.0}}
    ]
    
    return strand_data

def generate_masked_strands(strands):
    """Generate masked strands for sets 14 down to 1, combining with strands 16, 17, and 18
    Creates _5 with _5 and _4 with _4 combinations"""
    masked_strands = []
    current_index = 186  # Starting from the next available index
    
    # For each set from 14 down to 1
    for set_num in range(14, 0, -1):
        # Find the _4 and _5 strands for this set
        strand4 = None
        strand5 = None
        
        for strand in strands:
            if strand.get('layer_name') == f"{set_num}_4":
                strand4 = strand
            elif strand.get('layer_name') == f"{set_num}_5":
                strand5 = strand
        
        if not strand4 or not strand5:
            print(f"Warning: Strands {set_num}_4 or {set_num}_5 not found")
            continue
        
        # For each combining strand set (16, 17, 18)
        for combining_set in [16, 17, 18]:
            # Find the corresponding _4 and _5 strands
            comb_strand4 = None
            comb_strand5 = None
            
            for strand in strands:
                if strand.get('layer_name') == f"{combining_set}_4":
                    comb_strand4 = strand
                elif strand.get('layer_name') == f"{combining_set}_5":
                    comb_strand5 = strand
            
            if not comb_strand4 or not comb_strand5:
                print(f"Warning: Strands {combining_set}_4 or {combining_set}_5 not found")
                continue
            
            # Create masked strand for _5 with _5
            masked_strands.append({
                "type": "MaskedStrand",
                "index": current_index,
                "start": {
                    "x": strand5["start"]["x"],
                    "y": strand5["start"]["y"]
                },
                "end": {
                    "x": comb_strand5["end"]["x"],
                    "y": comb_strand5["end"]["y"]
                },
                "width": 46,
                "color": {
                    "r": 231,
                    "g": 238,
                    "b": 101,
                    "a": 255
                },
                "stroke_color": {
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "a": 255
                },
                "stroke_width": 4,
                "has_circles": [False, False],
                "layer_name": f"{combining_set}_5_{set_num}_5",
                "set_number": int(f"{combining_set}{set_num}"),
                "is_first_strand": False,
                "is_start_side": True,
                "start_line_visible": True,
                "end_line_visible": True,
                "is_hidden": False,
                "start_extension_visible": False,
                "end_extension_visible": False,
                "start_arrow_visible": False,
                "end_arrow_visible": False,
                "full_arrow_visible": False,
                "shadow_only": False,
                "circle_stroke_color": {
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "a": 255
                },
                "control_points": [None, None],
                "control_point_center": {
                    "x": (strand5["start"]["x"] + comb_strand5["end"]["x"]) / 2,
                    "y": (strand5["start"]["y"] + comb_strand5["end"]["y"]) / 2
                },
                "control_point_center_locked": False,
                "deletion_rectangles": []
            })
            current_index += 1
            
            # Create masked strand for _4 with _4
            masked_strands.append({
                "type": "MaskedStrand",
                "index": current_index,
                "start": {
                    "x": strand4["start"]["x"],
                    "y": strand4["start"]["y"]
                },
                "end": {
                    "x": comb_strand4["end"]["x"],
                    "y": comb_strand4["end"]["y"]
                },
                "width": 46,
                "color": {
                    "r": 231,
                    "g": 238,
                    "b": 101,
                    "a": 255
                },
                "stroke_color": {
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "a": 255
                },
                "stroke_width": 4,
                "has_circles": [False, False],
                "layer_name": f"{combining_set}_4_{set_num}_4",
                "set_number": int(f"{combining_set}{set_num}"),
                "is_first_strand": False,
                "is_start_side": True,
                "start_line_visible": True,
                "end_line_visible": True,
                "is_hidden": False,
                "start_extension_visible": False,
                "end_extension_visible": False,
                "start_arrow_visible": False,
                "end_arrow_visible": False,
                "full_arrow_visible": False,
                "shadow_only": False,
                "circle_stroke_color": {
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "a": 255
                },
                "control_points": [None, None],
                "control_point_center": {
                    "x": (strand4["start"]["x"] + comb_strand4["end"]["x"]) / 2,
                    "y": (strand4["start"]["y"] + comb_strand4["end"]["y"]) / 2
                },
                "control_point_center_locked": False,
                "deletion_rectangles": []
            })
            current_index += 1
    
    return masked_strands

def main():
    # Set output directory to Downloads
    output_dir = r"C:\Users\YonatanSetbon\Downloads"
    
    print("Generating masked strands...")
    
    # Create base strands
    base_strands = create_base_strands()
    
    # Generate masked strands
    masked_strands = generate_masked_strands(base_strands)
    
    print(f"Generated {len(masked_strands)} masked strands")
    
    # Save the masked strands
    output_filename = "rest_of_mask_strands.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        json.dump(masked_strands, f, indent=2)
    
    print(f"Masked strands saved to: {output_path}")
    print("Done!")

if __name__ == "__main__":
    main()