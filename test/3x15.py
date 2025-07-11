import json

def generate_masked_strands():
    """Generate masked strands for OpenStrandStudio based on the intersection pattern."""
    
    # Define the horizontal strands that need masking (1-14)
    horizontal_strands = [
        {"index": 1, "y_2": 1092.0, "y_3": 1176.0},
        {"index": 2, "y_2": 924.0, "y_3": 1008.0},
        {"index": 3, "y_2": 756.0, "y_3": 840.0},
        {"index": 4, "y_2": 588.0, "y_3": 672.0},
        {"index": 5, "y_2": 420.0, "y_3": 504.0},
        {"index": 6, "y_2": 252.0, "y_3": 336.0},
        {"index": 7, "y_2": 84.0, "y_3": 168.0},
        {"index": 8, "y_2": -84.0, "y_3": 0.0},
        {"index": 9, "y_2": -252.0, "y_3": -168.0},
        {"index": 10, "y_2": -420.0, "y_3": -336.0},
        {"index": 11, "y_2": -588.0, "y_3": -504.0},
        {"index": 12, "y_2": 1260.0, "y_3": 1344.0},
        {"index": 13, "y_2": 1428.0, "y_3": 1512.0},
        {"index": 14, "y_2": 1596.0, "y_3": 1680.0},
    ]
    
    # Define the vertical strands (16, 17, 18) with their x positions
    vertical_strands = [
        {"index": 16, "x_2": 784.0, "x_3": 700.0},
        {"index": 17, "x_2": 952.0, "x_3": 868.0},
        {"index": 18, "x_2": 1120.0, "x_3": 1036.0},
    ]
    
    masked_strands = []
    strand_index = 54  # Starting index based on your example
    
    # Generate masked strands for each intersection
    for h_strand in horizontal_strands:
        h_idx = h_strand["index"]
        
        # For each vertical strand
        for v_strand in vertical_strands:
            v_idx = v_strand["index"]
            
            # Create masked strand for _2 part of horizontal strand with _3 part of vertical strand
            masked_strands.append({
                "type": "MaskedStrand",
                "index": strand_index,
                "start": {
                    "x": 644.0,
                    "y": h_strand["y_2"]
                },
                "end": {
                    "x": 1204.0,
                    "y": h_strand["y_2"]
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
                "layer_name": f"{h_idx}_2_{v_idx}_3",
                "set_number": int(f"{h_idx}{v_idx}"),
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
                    "x": v_strand["x_3"],
                    "y": h_strand["y_2"]
                },
                "control_point_center_locked": False,
                "deletion_rectangles": []
            })
            strand_index += 1
            
            # Create masked strand for _3 part of horizontal strand with _2 part of vertical strand
            masked_strands.append({
                "type": "MaskedStrand",
                "index": strand_index,
                "start": {
                    "x": 1176.0,
                    "y": h_strand["y_3"]
                },
                "end": {
                    "x": 616.0,
                    "y": h_strand["y_3"]
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
                "layer_name": f"{h_idx}_3_{v_idx}_2",
                "set_number": int(f"{h_idx}{v_idx}"),
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
                    "x": v_strand["x_2"],
                    "y": h_strand["y_3"]
                },
                "control_point_center_locked": False,
                "deletion_rectangles": []
            })
            strand_index += 1
    
    # We already have masked strands for strand 15, so let's skip those
    # The script starts from strand_index 54, which matches your example
    
    return masked_strands

def export_masked_strands(output_file="masked_strands.json"):
    """Export the generated masked strands to a JSON file."""
    masked_strands = generate_masked_strands()
    
    # Create a wrapper object similar to your artifact structure
    output_data = {
        "additional_strands": masked_strands
    }
    
    # Write to file with proper formatting
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Generated {len(masked_strands)} masked strands")
    print(f"Exported to {output_file}")
    
    # Also print a summary
    print("\nSummary of generated strands:")
    for i in range(0, len(masked_strands), 6):  # 6 strands per horizontal strand
        strand = masked_strands[i]
        h_strand_num = strand["layer_name"].split("_")[0]
        print(f"  Horizontal strand {h_strand_num}: indices {strand['index']} to {strand['index']+5}")

def merge_with_existing_data(existing_file, output_file="complete_strands.json"):
    """Merge the generated masked strands with existing strand data."""
    # Read existing data
    with open(existing_file, 'r') as f:
        existing_data = json.load(f)
    
    # Generate new masked strands
    masked_strands = generate_masked_strands()
    
    # Add the masked strands to the existing strands array
    if "states" in existing_data and len(existing_data["states"]) > 0:
        existing_strands = existing_data["states"][0]["data"]["strands"]
        
        # Remove any existing masked strands with indices >= 54 to avoid duplicates
        existing_strands = [s for s in existing_strands if s.get("index", 0) < 54]
        
        # Add the new masked strands
        existing_strands.extend(masked_strands)
        existing_data["states"][0]["data"]["strands"] = existing_strands
        
        print(f"Total strands after merge: {len(existing_strands)}")
    
    # Write the complete data
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"Complete data exported to {output_file}")

if __name__ == "__main__":
    # Export just the masked strands
    export_masked_strands()
    
    # If you have the original file, you can merge them
    # Uncomment the line below and provide the path to your original file
    # merge_with_existing_data("paste.txt", "complete_strands.json")