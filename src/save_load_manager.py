import json
import logging
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor
from strand import Strand, AttachedStrand, MaskedStrand

def serialize_point(point):
    return {"x": point.x(), "y": point.y()}

def deserialize_point(data):
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
        # Save control points for all strand types that have them
        "control_points": [
            serialize_point(strand.control_point1),
            serialize_point(strand.control_point2)
        ] if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2') else []
    }

    if isinstance(strand, AttachedStrand):
        data["parent_layer_name"] = strand.parent.layer_name if strand.parent else None
    elif isinstance(strand, MaskedStrand):
        data["first_selected_strand"] = strand.first_selected_strand.layer_name if strand.first_selected_strand else None
        data["second_selected_strand"] = strand.second_selected_strand.layer_name if strand.second_selected_strand else None

    logging.debug(f"Serialized strand '{strand.layer_name}' of type '{type(strand).__name__}'")
    return data

def save_strands(strands, groups, filename):
    data = {
        "strands": [serialize_strand(strand, i) for i, strand in enumerate(strands)],
        "groups": serialize_groups(groups),
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Saved strands and groups to {filename}")

def deserialize_strand(data, parent_strand=None, first_strand=None, second_strand=None):
    strand_type = data.get("type", "Strand")
    start = deserialize_point(data["start"])
    end = deserialize_point(data["end"])
    width = data["width"]
    color = deserialize_color(data["color"])
    stroke_color = deserialize_color(data["stroke_color"])
    stroke_width = data["stroke_width"]
    has_circles = data["has_circles"]
    layer_name = data["layer_name"]
    set_number = data["set_number"]
    is_first_strand = data.get("is_first_strand", False)
    is_start_side = data.get("is_start_side", True)

    if strand_type == "Strand":
        strand = Strand(start, end, width)
    elif strand_type == "AttachedStrand":
        if not parent_strand:
            logging.warning(f"Parent strand not found for attached strand '{layer_name}'")
            return None
        strand = AttachedStrand(parent_strand, start)
    elif strand_type == "MaskedStrand":
        if not (first_strand and second_strand):
            logging.warning(f"Selected strands not found for masked strand '{layer_name}'")
            return None
        strand = MaskedStrand(first_strand, second_strand)
    else:
        logging.warning(f"Unknown strand type: {strand_type}")
        return None

    strand.end = end
    strand.color = color
    strand.stroke_color = stroke_color
    strand.stroke_width = stroke_width
    strand.has_circles = has_circles
    strand.layer_name = layer_name
    strand.set_number = set_number
    strand.is_first_strand = is_first_strand
    strand.is_start_side = is_start_side

    # Set control points for any strand type that has them
    if len(data.get("control_points", [])) == 2:
        control_points = [deserialize_point(point) for point in data["control_points"]]
        if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
            strand.control_point1 = control_points[0]
            strand.control_point2 = control_points[1]
    
    strand.update_shape()
    strand.update_side_line()

    logging.debug(f"Deserialized strand '{strand.layer_name}' of type '{strand_type}'")

    return strand
def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

    logging.debug(f"Loaded data from {filename}: {data}")

    # Check if the data contains the expected keys
    if "strands" not in data or "groups" not in data:
        logging.error("Input data is missing 'strands' or 'groups' key.")
        return [], {}

    strands = []
    strand_dict = {}
    
    data_strands = data["strands"]
    strands_remaining = data_strands.copy()
    processed_indices = set()
    
    while strands_remaining:
        progress_made = False
        strands_to_remove = []

        for strand_data in strands_remaining:
            strand_type = strand_data.get("type", "Strand")
            index = strand_data.get("index")
            logging.debug(f"Attempting to deserialize strand at index {index} with type '{strand_type}'")
            try:
                if strand_type == "Strand":
                    strand = deserialize_strand(strand_data)
                elif strand_type == "AttachedStrand":
                    parent_layer_name = strand_data.get("parent_layer_name")
                    parent_strand = strand_dict.get(parent_layer_name)
                    if not parent_strand:
                        raise ValueError(f"Parent strand '{parent_layer_name}' not yet loaded for AttachedStrand at index {index}")
                    strand = deserialize_strand(strand_data, parent_strand=parent_strand)
                elif strand_type == "MaskedStrand":
                    first_layer_name = strand_data.get("first_selected_strand")
                    second_layer_name = strand_data.get("second_selected_strand")
                    first_strand = strand_dict.get(first_layer_name)
                    second_strand = strand_dict.get(second_layer_name)
                    if not (first_strand and second_strand):
                        raise ValueError(f"Selected strands '{first_layer_name}' and/or '{second_layer_name}' not yet loaded for MaskedStrand at index {index}")
                    strand = deserialize_strand(strand_data, first_strand=first_strand, second_strand=second_strand)
                else:
                    logging.warning(f"Unknown strand type: {strand_type} at index {index}")
                    strands_to_remove.append(strand_data)
                    continue

                if strand:
                    strands.append(strand)
                    strand_dict[strand.layer_name] = strand
                    processed_indices.add(index)
                    
                    # If it's an AttachedStrand, add to the parent's attached_strands
                    if strand_type == "AttachedStrand" and parent_strand:
                        parent_strand.attached_strands.append(strand)
                        
                    strands_to_remove.append(strand_data)
                    progress_made = True
                else:
                    logging.warning(f"Failed to deserialize strand at index {index}")
            except ValueError as e:
                logging.debug(str(e))
                continue  # Dependencies not yet met; will retry in next iteration

        if not progress_made:
            logging.error("Could not make progress in loading strands. Check for missing dependencies or cyclic references.")
            break

        for strand_data in strands_to_remove:
            strands_remaining.remove(strand_data)

    logging.debug("Strand dictionary contents after deserialization:")
    for layer_name, strand in strand_dict.items():
        logging.debug(f"Layer: {layer_name}, Strand: {strand}, Type: {type(strand).__name__}")

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

        # Debug: Log the strands being serialized
        logging.debug(f"Strands for group '{group_name}': {strands_list}")

        serialized_groups[group_name] = {
            "layers": group_data.get("layers", []),
            "main_strands": list(group_data.get("main_strands", [])),
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
