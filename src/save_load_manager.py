import json
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
    elif isinstance(color, Qt.GlobalColor):
        # Convert Qt.GlobalColor to QColor
        qcolor = QColor(color)
        return {"r": qcolor.red(), "g": qcolor.green(), "b": qcolor.blue(), "a": qcolor.alpha()}
    else:
        # If it's neither QColor nor Qt.GlobalColor, return a default color (e.g., black)
        return {"r": 0, "g": 0, "b": 0, "a": 255}

def deserialize_color(data):
    return QColor(data["r"], data["g"], data["b"], data["a"])

def serialize_strand(strand, index):
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
    
    if isinstance(strand, AttachedStrand):
        data["parent_index"] = strand.parent.layer_name
    elif isinstance(strand, MaskedStrand):
        data["first_selected_strand"] = strand.first_selected_strand.layer_name
        data["second_selected_strand"] = strand.second_selected_strand.layer_name
    
    return data

def save_strands(strands, filename):
    data = [serialize_strand(strand, i) for i, strand in enumerate(strands)]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)
    
    strands = []
    strand_dict = {}
    
    # First pass: create all strands
    for strand_data in data:
        if strand_data["type"] == "Strand":
            strand = Strand(
                deserialize_point(strand_data["start"]),
                deserialize_point(strand_data["end"]),
                strand_data["width"]
            )
        elif strand_data["type"] == "AttachedStrand":
            # Create a temporary parent strand
            temp_parent = Strand(QPointF(0, 0), QPointF(1, 1), strand_data["width"])
            temp_parent.color = deserialize_color(strand_data["color"])
            temp_parent.stroke_color = deserialize_color(strand_data["stroke_color"])
            temp_parent.stroke_width = strand_data["stroke_width"]
            strand = AttachedStrand(temp_parent, deserialize_point(strand_data["start"]))
        elif strand_data["type"] == "MaskedStrand":
            # Create MaskedStrand with None for strands and pass the set_number
            strand = MaskedStrand(None, None, set_number=strand_data["set_number"])
        else:
            continue
        
        strand.end = deserialize_point(strand_data["end"])
        strand.color = deserialize_color(strand_data["color"])
        strand.stroke_color = deserialize_color(strand_data["stroke_color"])
        strand.stroke_width = strand_data["stroke_width"]
        strand.has_circles = strand_data["has_circles"]
        strand.layer_name = strand_data["layer_name"]
        if strand_data["type"] != "MaskedStrand":  # We've already set this for MaskedStrand
            strand.set_number = strand_data["set_number"]
        strand.is_first_strand = strand_data["is_first_strand"]
        strand.is_start_side = strand_data["is_start_side"]
        
        strand.update_shape()
        strand.update_side_line()
        
        strands.append(strand)
        strand_dict[strand.layer_name] = strand
    
    # Second pass: set up relationships
    for strand_data, strand in zip(data, strands):
        if strand_data["type"] == "AttachedStrand":
            parent = strand_dict.get(strand_data["parent_index"])
            if parent:
                strand.parent = parent
                parent.attached_strands.append(strand)
                # Update strand properties to match the actual parent
                strand.width = parent.width
                strand.color = parent.color
                strand.stroke_color = parent.stroke_color
                strand.stroke_width = parent.stroke_width
                strand.update_shape()
                strand.update_side_line()
        elif strand_data["type"] == "MaskedStrand":
            first = strand_dict.get(strand_data["first_selected_strand"])
            second = strand_dict.get(strand_data["second_selected_strand"])
            if first and second:
                strand.first_selected_strand = first
                strand.second_selected_strand = second
                strand.start = first.start
                strand.end = first.end
                strand.width = first.width
                strand.update_shape()
                strand.update_side_line()
    
    return strands
def apply_loaded_strands(canvas, strands):
    canvas.strands = strands
    if strands:  # Check if strands list is not empty
        canvas.update_color_for_set(strands[0].set_number, strands[0].color)
        canvas.newest_strand = strands[-1]
    canvas.is_first_strand = False
    canvas.update()
    
    if canvas.layer_panel:
        canvas.layer_panel.refresh()