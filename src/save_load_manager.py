import json
import logging
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor
from strand import Strand, AttachedStrand, MaskedStrand



def deserialize_point(data):
    if data is None:
        return None
    return QPointF(data["x"], data["y"])

def serialize_color(color):
    if isinstance(color, QColor):
        return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}
    elif isinstance(color, int):  # Handle Qt.GlobalColor enums
        qcolor = QColor(color)
        return {"r": qcolor.red(), "g": qcolor.green(), "b": qcolor.blue(), "a": qcolor.alpha()}
    else:
        # Default to black color
        return {"r": 0, "g": 0, "b": 0, "a": 255}

def deserialize_color(data):
    return QColor(data["r"], data["g"], data["b"], data["a"])

def serialize_point(point):
    """Serialize a point to a dictionary format."""
    # If point is already a dictionary with x,y keys, return it as is
    if isinstance(point, dict) and 'x' in point and 'y' in point:
        return point
    # Otherwise assume it's a QPointF and convert it
    return {"x": point.x(), "y": point.y()}

def serialize_strand(strand, index=None):
    data = {
        "type": type(strand).__name__,
        "index": index,
        "start": serialize_point(strand.start),
        "end": serialize_point(strand.end),
        "width": strand.width,
        "color": serialize_color(strand.color),
        "stroke_color": serialize_color(strand.stroke_color),
        "stroke_width": strand.stroke_width,
        "has_circles": strand.has_circles,
        "layer_name": strand.layer_name,
        "set_number": strand.set_number,
        "is_first_strand": getattr(strand, 'is_first_strand', False),
        "is_start_side": getattr(strand, 'is_start_side', True),
    }

    # Add control points if they exist
    if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
        data["control_points"] = [
            serialize_point(strand.control_point1),
            serialize_point(strand.control_point2)
        ]

    # Handle MaskedStrand specific data
    if isinstance(strand, MaskedStrand):
        data.update({
            "first_selected_strand": strand.first_selected_strand.layer_name if strand.first_selected_strand else None,
            "second_selected_strand": strand.second_selected_strand.layer_name if strand.second_selected_strand else None,
            "deletion_rectangles": getattr(strand, 'deletion_rectangles', [])
        })
        logging.info(f"Serialized {len(data['deletion_rectangles'])} deletion rectangles for masked strand {strand.layer_name}")

    return data

def save_strands(strands, groups, filename):
    data = {
        "strands": [serialize_strand(strand, i) for i, strand in enumerate(strands)],
        "groups": serialize_groups(groups),
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Saved strands and groups to {filename}")

def deserialize_strand(data, strand_dict=None, parent_strand=None):
    """Deserialize a strand from saved data."""
    start = deserialize_point(data["start"])
    end = deserialize_point(data["end"])
    width = data["width"]
    color = deserialize_color(data["color"])
    stroke_color = deserialize_color(data["stroke_color"])
    stroke_width = data["stroke_width"]
    set_number = data.get("set_number")
    layer_name = data.get("layer_name", "")
    strand_type = data.get("type", "Strand")

    # Create the appropriate type of strand
    if strand_type == "MaskedStrand" and strand_dict:
        # Get the referenced strands from the strand dictionary
        first_strand = strand_dict.get(data.get("first_selected_strand"))
        second_strand = strand_dict.get(data.get("second_selected_strand"))
        
        if first_strand and second_strand:
            strand = MaskedStrand(first_strand, second_strand)
            strand.set_number = set_number
            strand.layer_name = layer_name
            
            # Restore deletion rectangles if they exist
            if "deletion_rectangles" in data:
                strand.deletion_rectangles = data["deletion_rectangles"]
                logging.info(f"Restored {len(data['deletion_rectangles'])} deletion rectangles for masked strand {layer_name}")
        else:
            logging.warning(f"Could not create MaskedStrand: missing reference strands")
            return None
    elif strand_type == "AttachedStrand" and parent_strand:
        strand = AttachedStrand(parent_strand, end)
        strand.start = start
    else:
        strand = Strand(start, end, width, color, stroke_color, stroke_width, set_number, layer_name)

    # Set basic properties
    strand.width = width
    strand.color = color
    strand.stroke_color = stroke_color
    strand.stroke_width = stroke_width
    strand.set_number = set_number
    strand.layer_name = layer_name
    strand.has_circles = data.get("has_circles", [False, False])
    strand.is_first_strand = data.get("is_first_strand", False)
    strand.is_start_side = data.get("is_start_side", True)

    # Set control points if they exist in the data
    if "control_points" in data and len(data["control_points"]) == 2:
        control_point1 = deserialize_point(data["control_points"][0])
        control_point2 = deserialize_point(data["control_points"][1])
        strand.control_point1 = control_point1
        strand.control_point2 = control_point2
        
        # Force path and side line updates
        if hasattr(strand, 'update_shape'):
            strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()

    return strand
def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

    logging.info(f"Starting to load strands from {filename}")
    logging.debug(f"Loaded data from {filename}: {data}")

    # Check if the data contains the expected keys
    if "strands" not in data or "groups" not in data:
        logging.error("Input data is missing 'strands' or 'groups' key.")
        return [], {}

    strands = []
    strand_dict = {}
    data_strands = data["strands"]
    
    # First pass: Load basic Strands
    logging.info("First pass: Loading basic Strands")
    for strand_data in data_strands:
        if strand_data.get("type") == "Strand":
            logging.debug(f"Processing Strand with index {strand_data.get('index')}")
            strand = deserialize_strand(strand_data)
            if strand:
                strands.append(strand)
                strand_dict[strand.layer_name] = strand
                logging.info(f"Successfully loaded basic Strand: {strand.layer_name}")

    # Second pass: Load AttachedStrands
    logging.info("Second pass: Loading AttachedStrands")
    for strand_data in data_strands:
        if strand_data.get("type") == "AttachedStrand":
            index = strand_data.get("index")
            layer_name = strand_data.get("layer_name")
            # Get the base number before the underscore for parent
            parent_layer_name = f"{layer_name.split('_')[0]}_1"  # e.g., "1_2" -> "1_1"
            logging.debug(f"Processing AttachedStrand {layer_name}, looking for parent {parent_layer_name}")
            
            parent_strand = strand_dict.get(parent_layer_name)
            if parent_strand:
                strand = deserialize_strand(strand_data, parent_strand=parent_strand)
                if strand:
                    strands.append(strand)
                    strand_dict[strand.layer_name] = strand
                    parent_strand.attached_strands.append(strand)
                    logging.info(f"Successfully loaded AttachedStrand: {layer_name} with parent {parent_layer_name}")
            else:
                logging.warning(f"Parent strand {parent_layer_name} not found for AttachedStrand {layer_name}")

    # Third pass: Load MaskedStrands
    logging.info("Third pass: Loading MaskedStrands")
    for strand_data in data_strands:
        if strand_data.get("type") == "MaskedStrand":
            index = strand_data.get("index")
            first_layer_name = strand_data.get("first_selected_strand")
            second_layer_name = strand_data.get("second_selected_strand")
            logging.debug(f"Processing MaskedStrand {strand_data.get('layer_name')} with strands {first_layer_name} and {second_layer_name}")

            first_strand = strand_dict.get(first_layer_name)
            second_strand = strand_dict.get(second_layer_name)

            if first_strand and second_strand:
                strand = deserialize_strand(strand_data, strand_dict=strand_dict)
                if strand:
                    strands.append(strand)
                    strand_dict[strand.layer_name] = strand
                    logging.info(f"Successfully loaded MaskedStrand: {strand.layer_name}")
            else:
                logging.warning(f"Missing reference strands for MaskedStrand {strand_data.get('layer_name')}. "
                              f"First strand ({first_layer_name}) found: {bool(first_strand)}, "
                              f"Second strand ({second_layer_name}) found: {bool(second_strand)}")

    # Log final results
    logging.info(f"Completed loading strands. Total loaded: {len(strands)}")
    logging.debug("Final strand dictionary contents:")
    for layer_name, strand in strand_dict.items():
        logging.debug(f"Layer: {layer_name}, Type: {type(strand).__name__}")

    # Check for missing strands
    original_count = len(data_strands)
    if len(strands) < original_count:
        logging.warning(f"Not all strands were loaded. Original count: {original_count}, Loaded count: {len(strands)}")
        loaded_indices = {s.layer_name for s in strands}
        original_indices = {s.get('layer_name') for s in data_strands}
        missing_indices = original_indices - loaded_indices
        logging.warning(f"Missing strands: {missing_indices}")

    # Apply loaded strands to canvas
    apply_loaded_strands(canvas, strands, data.get("groups", {}))

    return strands, data.get("groups", {})


def apply_loaded_strands(canvas, strands, groups):
    logging.info("Starting to apply loaded strands and groups to the canvas.")

    # Log the contents of strand_dict
    logging.debug("Contents of strand_dict before applying group data:")
    strand_dict = {strand.layer_name: strand for strand in strands}
    for layer_name, strand in strand_dict.items():
        logging.debug(f"Layer: {layer_name}, Strand ID: {id(strand)}")

    # Apply strands to the canvas
    canvas.strands = strands
    logging.info(f"Applied {len(strands)} strands to the canvas.")

    # Update the LayerPanel with the loaded strands
    if hasattr(canvas, 'layer_panel'):
        canvas.layer_panel.refresh()
        logging.info("LayerPanel refreshed with loaded strands.")

    for group_name, group_info in groups.items():
        logging.info(f"Deserializing group '{group_name}'")
        
        group_strands = []
        for layer_name in group_info["strands"]:
            logging.debug(f"Attempting to retrieve strand with layer_name '{layer_name}'")
            strand = strand_dict.get(layer_name)
            if strand:
                group_strands.append(strand)
                logging.info(f"Strand '{layer_name}' added to group '{group_name}'")
                logging.debug(f"Strand ID: {id(strand)}, Attributes: {dir(strand)}")
            else:
                logging.warning(f"Strand with layer_name '{layer_name}' not found in strand_dict")

        if group_strands:
            canvas.group_layer_manager.group_panel.create_group(group_name, group_strands)
            logging.info(f"Group '{group_name}' created in group panel with {len(group_strands)} strands")
            
            canvas.groups[group_name] = {
                "layers": group_info["layers"],
                "strands": group_strands,
                "main_strands": group_info.get("main_strands", set()),
                "control_points": group_info.get("control_points", {})
            }
            logging.info(f"Group '{group_name}' applied with {len(group_strands)} strands")
        else:
            logging.warning(f"Group '{group_name}' has no valid strands")

    # Update the canvas to reflect changes
    if hasattr(canvas, 'update'):
        canvas.update()
        logging.info("Canvas updated.")

    logging.info("Finished applying group data.")
def serialize_groups(groups):
    serialized_groups = {}
    logging.info(f"Starting serialization of groups. Total groups: {len(groups)}")

    for group_name, group_data in groups.items():
        logging.info(f"Serializing group '{group_name}'")
        
        # Handle regular strands list
        strands_list = []
        for strand in group_data.get("strands", []):
            # Handle both Strand objects and dictionaries
            if isinstance(strand, (Strand, AttachedStrand, MaskedStrand)):
                strands_list.append(strand.layer_name)
            elif isinstance(strand, dict) and "layer_name" in strand:
                strands_list.append(strand["layer_name"])
            elif isinstance(strand, str):  # Handle case where it's already a layer name
                strands_list.append(strand)
            else:
                logging.warning(f"Invalid strand object in group {group_name}")
                continue

        # Handle main strands list similarly
        main_strands_list = []
        for strand in group_data.get("main_strands", []):
            if isinstance(strand, (Strand, AttachedStrand, MaskedStrand)):
                main_strands_list.append(strand.layer_name)
            elif isinstance(strand, str):
                main_strands_list.append(strand)
            else:
                logging.warning(f"Invalid main strand object in group {group_name}")
                continue

        # Debug: Log the strands being serialized
        logging.debug(f"Strands for group '{group_name}': {strands_list}")
        logging.debug(f"Main strands for group '{group_name}': {main_strands_list}")

        serialized_groups[group_name] = {
            "layers": group_data.get("layers", []),
            "main_strands": main_strands_list,
            "strands": strands_list,
            "control_points": {
                layer_name: {
                    "control_point1": serialize_point(points["control_point1"]),
                    "control_point2": serialize_point(points["control_point2"])
                } for layer_name, points in group_data.get("control_points", {}).items()
            }
        }

        # Debug: Log the serialized group data
        logging.debug(f"Serialized data for group '{group_name}': {serialized_groups[group_name]}")

    logging.info("Finished serialization of groups.")
    return serialized_groups


def deserialize_groups(groups_data, strand_dict):
    logging.info(f"Starting deserialization of groups. Total groups: {len(groups_data)}")
    
    # Debug: Print all available strands in strand_dict
    logging.debug(f"Available strands in strand_dict: {list(strand_dict.keys())}")
    
    deserialized_groups = {}
    for group_name, group_data in groups_data.items():
        logging.info(f"Deserializing group '{group_name}'")
        logging.debug(f"Group data before processing: {group_data}")
        
        strands = []
        for layer_name in group_data["strands"]:
            logging.debug(f"Attempting to retrieve strand with layer_name '{layer_name}'")
            strand = strand_dict.get(layer_name)  # Use get to safely retrieve the strand
            if strand:
                strands.append(strand)
                logging.info(f"Strand '{layer_name}' added to group '{group_name}'")
                # Debug: Print strand properties
                logging.debug(f"Strand properties - Layer: {layer_name}, "
                            f"Type: {type(strand).__name__}, "
                            f"Color: {strand.color}, "
                            f"Valid: {hasattr(strand, 'layer_name')}")
            else:
                logging.warning(f"Strand '{layer_name}' not found in strand_dict for group '{group_name}'")
                # Debug: Check if the layer name is in the JSON data
                logging.debug(f"Checking JSON data for layer name '{layer_name}': "
                            f"{'Found' if layer_name in [s['layer_name'] for s in groups_data[group_name]['strands']] else 'Not Found'}")

        # Log the number of strands found for the group
        logging.info(f"Group '{group_name}' has {len(strands)} valid strands out of {len(group_data['strands'])} total strands")

        deserialized_groups[group_name] = {
            "layers": group_data["layers"],
            "main_strands": set(group_data.get("main_strands", [])),
            "strands": strands,
            "control_points": {
                layer_name: {
                    "control_point1": deserialize_point(points["control_point1"]),
                    "control_point2": deserialize_point(points["control_point2"])
                } for layer_name, points in group_data.get("control_points", {}).items()
            }
        }
        logging.info(f"Deserialized group '{group_name}' with {len(strands)} strands")
        # Debug: Print final group structure
        logging.debug(f"Final group structure for '{group_name}': {[s.layer_name for s in strands]}")
    
    logging.info("Completed deserialization of all groups.")
    return deserialized_groups




