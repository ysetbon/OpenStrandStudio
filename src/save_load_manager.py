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
    # Handle None case
    if point is None:
        return None
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

    # Add control points if they exist and are not None
    if (hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2') and 
        strand.control_point1 is not None and strand.control_point2 is not None):
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
    # Exact point deserialization
    start = QPointF(data["start"]["x"], data["start"]["y"])
    end = QPointF(data["end"]["x"], data["end"]["y"])
    width = data["width"]
    color = deserialize_color(data["color"])
    stroke_color = deserialize_color(data["stroke_color"])
    stroke_width = data["stroke_width"]
    set_number = data.get("set_number")
    layer_name = data.get("layer_name", "")
    strand_type = data.get("type", "Strand")

    # Create the appropriate type of strand based on the type field
    if strand_type == "Strand":
        strand = Strand(start, end, width, color, stroke_color, stroke_width, set_number, layer_name)
        # Explicitly set has_circles from saved data
        strand.has_circles = data.get("has_circles", [False, False])
        strand.both_ends_attached = all(strand.has_circles)
        
    elif strand_type == "AttachedStrand" and parent_strand:
        strand = AttachedStrand(parent_strand, end)
        # Explicitly set all properties to match saved data exactly
        strand.start = start
        strand.end = end
        strand.width = width
        strand.color = color
        strand.stroke_color = stroke_color
        strand.stroke_width = stroke_width
        strand.set_number = set_number
        strand.layer_name = layer_name
        
        # Explicitly set has_circles from saved data
        strand.has_circles = data.get("has_circles", [False, False])
        # Update both_ends_attached based on has_circles
        strand.both_ends_attached = all(strand.has_circles)
        
    elif strand_type == "MaskedStrand" and strand_dict:
        first_strand = strand_dict.get(data.get("first_selected_strand"))
        second_strand = strand_dict.get(data.get("second_selected_strand"))
        
        if first_strand and second_strand:
            strand = MaskedStrand(first_strand, second_strand)
            # Explicitly set all properties to match saved data exactly
            strand.start = start
            strand.end = end
            strand.width = width
            strand.color = color
            strand.stroke_color = stroke_color
            strand.stroke_width = stroke_width
            strand.set_number = set_number
            strand.layer_name = layer_name
            strand.has_circles = data.get("has_circles", [False, False])
            strand.both_ends_attached = all(strand.has_circles)
            strand.deletion_rectangles = data.get("deletion_rectangles", [])
        else:
            logging.error(f"Could not create MaskedStrand: missing reference strands")
            return None
    else:
        logging.error(f"Unknown strand type: {strand_type}")
        return None

    # Set common properties exactly as in saved data
    strand.has_circles = data.get("has_circles", [False, False])
    strand.both_ends_attached = all(strand.has_circles)
    strand.is_first_strand = data.get("is_first_strand", False)
    strand.is_start_side = data.get("is_start_side", True)

    # Set control points exactly as in saved data
    if "control_points" in data and len(data["control_points"]) == 2:
        strand.control_point1 = QPointF(
            data["control_points"][0]["x"],
            data["control_points"][0]["y"]
        )
        strand.control_point2 = QPointF(
            data["control_points"][1]["x"],
            data["control_points"][1]["y"]
        )
    else:
        # If no control points in data, initialize them based on geometry
        strand.update_control_points_from_geometry()

    # Force updates after setting all properties
    if hasattr(strand, 'update_shape'):
        strand.update_shape()
    if hasattr(strand, 'update_side_line'):
        strand.update_side_line()

    logging.info(f"Deserialized {strand_type} '{layer_name}' with has_circles={strand.has_circles}")
    return strand
def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

    logging.info(f"Starting to load strands from {filename}")

    # Initialize collections
    strands = []
    strand_dict = {}
    
    # Process all strands in exact JSON order
    for strand_data in data["strands"]:
        if strand_data["type"] == "Strand":
            strand = deserialize_strand(strand_data)
            if strand:
                strands.append(strand)
                strand_dict[strand.layer_name] = strand
                logging.info(f"Created basic strand: {strand.layer_name}")
                
        elif strand_data["type"] == "AttachedStrand":
            base_name = strand_data["layer_name"].split('_')[0]
            parent_name = f"{base_name}_1"
            parent_strand = strand_dict.get(parent_name)
            
            if parent_strand:
                strand = deserialize_strand(strand_data, parent_strand=parent_strand)
                if strand:
                    strands.append(strand)
                    strand_dict[strand.layer_name] = strand
                    parent_strand.attached_strands.append(strand)
                    logging.info(f"Created attached strand: {strand.layer_name} -> {parent_name}")
            else:
                logging.error(f"Parent strand {parent_name} not found for {strand_data['layer_name']}")
                
        elif strand_data["type"] == "MaskedStrand":
            first_strand_name = strand_data["first_selected_strand"]
            second_strand_name = strand_data["second_selected_strand"]
            
            first_strand = strand_dict.get(first_strand_name)
            second_strand = strand_dict.get(second_strand_name)
            
            if first_strand and second_strand:
                strand = MaskedStrand(first_strand, second_strand)
                # Copy properties from saved data
                strand.layer_name = strand_data["layer_name"]
                strand.set_number = strand_data["set_number"]
                strand.width = strand_data["width"]
                strand.color = deserialize_color(strand_data["color"])
                strand.stroke_color = deserialize_color(strand_data["stroke_color"])
                strand.stroke_width = strand_data["stroke_width"]
                strand.has_circles = strand_data["has_circles"]
                strand.deletion_rectangles = strand_data.get("deletion_rectangles", [])
                
                strands.append(strand)
                strand_dict[strand.layer_name] = strand
                logging.info(f"Created masked strand: {strand.layer_name}")
            else:
                logging.error(f"Missing reference strands for masked strand {strand_data['layer_name']}")

    # Apply loaded strands to canvas
    canvas.strands = strands
    
    # Update UI
    if hasattr(canvas, 'layer_panel'):
        canvas.layer_panel.refresh()

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
                    "control_point1": serialize_point(points.get("control_point1")),
                    "control_point2": serialize_point(points.get("control_point2"))
                } for layer_name, points in group_data.get("control_points", {}).items()
                if points.get("control_point1") is not None or points.get("control_point2") is not None
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




