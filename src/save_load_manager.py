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
        # Add any additional properties needed
    }

    if isinstance(strand, AttachedStrand):
        data["parent_layer_name"] = strand.parent.layer_name if strand.parent else None
    elif isinstance(strand, MaskedStrand):
        data["first_selected_strand"] = strand.first_selected_strand.layer_name if strand.first_selected_strand else None
        data["second_selected_strand"] = strand.second_selected_strand.layer_name if strand.second_selected_strand else None

    return data

def serialize_groups(groups):
    serialized_groups = {}
    for group_name, group_data in groups.items():
        serialized_groups[group_name] = {
            "layers": group_data["layers"],
            "main_strands": list(group_data.get("main_strands", [])),
            # Use the already serialized strands directly
            "strands": group_data["strands"],
        }
    return serialized_groups

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

    strand.update_shape()
    strand.update_side_line()

    return strand

def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

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

    # Apply loaded strands to canvas
    apply_loaded_strands(canvas, strands, data.get("groups", {}))

    return strands, data.get("groups", {})

def apply_loaded_strands(canvas, strands, groups):
    canvas.strands = strands
    canvas.strand_colors = {}  # Reset the strand colors dictionary

    for strand in strands:
        # Update the strand colors
        canvas.strand_colors[strand.set_number] = strand.color
        canvas.update_color_for_set(strand.set_number, strand.color)

    if strands:
        canvas.newest_strand = strands[-1]
    canvas.is_first_strand = False
    canvas.update()

    if canvas.layer_panel:
        canvas.layer_panel.refresh()

    # **Removed the call to apply_group_data to prevent duplicate group loading**
    # if canvas.group_layer_manager:
    #     canvas.group_layer_manager.apply_group_data(groups)

    logging.info("Loaded strands into the canvas.")