import json
import logging
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand



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
    elif isinstance(color, dict) and all(k in color for k in ['r','g','b','a']):
        return color
    else:
        # Default to black color
        return {"r": 0, "g": 0, "b": 0, "a": 255}

def deserialize_color(data):
    """Deserialize a color from saved data."""
    if not isinstance(data, dict) or not all(k in data for k in ['r','g','b','a']):
        logging.warning(f"Invalid color data format: {data}")
        return QColor(0, 0, 0, 255)
    
    color = QColor(data["r"], data["g"], data["b"], data["a"])
    logging.info(f"Deserialized color from {data} to QColor({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})")
    return color

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

def serialize_strand(strand, canvas, index=None):
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
        "start_line_visible": getattr(strand, 'start_line_visible', True),
        "end_line_visible": getattr(strand, 'end_line_visible', True),
        "is_hidden": getattr(strand, 'is_hidden', False),
        # NEW: Extension & Arrow visibility flags
        "start_extension_visible": getattr(strand, 'start_extension_visible', False),
        "end_extension_visible": getattr(strand, 'end_extension_visible', False),
        "start_arrow_visible": getattr(strand, 'start_arrow_visible', False),
        "end_arrow_visible": getattr(strand, 'end_arrow_visible', False),
    }

    # Only save circle_stroke_color if it exists
    if hasattr(strand, 'circle_stroke_color'):
        data["circle_stroke_color"] = serialize_color(strand.circle_stroke_color)
    else:
        data["circle_stroke_color"] = None

    # Add attached_to information for AttachedStrands
    if isinstance(strand, AttachedStrand):
        # Get the connections from LayerStateManager
        layer_name = strand.layer_name
        # Find the parent by looking at who this strand is connected to
        connected_to = None
        if hasattr(canvas, 'layer_state_manager'):
            for potential_parent, connections in canvas.layer_state_manager.getConnections().items():
                if layer_name in connections:
                    connected_to = potential_parent
                    break
        
        data["attached_to"] = connected_to
        logging.info(f"Serializing AttachedStrand {strand.layer_name} attached to {connected_to}")

        # Add attachment_side for AttachedStrands
        if hasattr(strand, 'attachment_side'):
            data["attachment_side"] = strand.attachment_side
            logging.info(f"Serializing attachment_side: {strand.attachment_side} for {strand.layer_name}")
        else:
            # Fallback or default if attribute doesn't exist (should exist based on constructor)
            data["attachment_side"] = 0 # Default to start side if missing, though this indicates an issue
            logging.warning(f"attachment_side attribute missing for AttachedStrand {strand.layer_name}, defaulting to 0")

    if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
        data["control_points"] = [
            serialize_point(strand.control_point1),
            serialize_point(strand.control_point2)
        ]
        # Add control_point_center if it exists
        if hasattr(strand, 'control_point_center'):
            data["control_point_center"] = serialize_point(strand.control_point_center)
            data["control_point_center_locked"] = getattr(strand, 'control_point_center_locked', False)

    if isinstance(strand, MaskedStrand):
        data["deletion_rectangles"] = getattr(strand, 'deletion_rectangles', [])

    # --- NEW: Save manual circle visibility overrides ---
    if hasattr(strand, 'manual_circle_visibility'):
        data["manual_circle_visibility"] = strand.manual_circle_visibility

    return data

def save_strands(strands, groups, filename, canvas):
    selected_strand_name = canvas.selected_strand.layer_name if canvas.selected_strand else None
    logging.info(f"Saving state with selected strand: {selected_strand_name}")
    data = {
        "strands": [serialize_strand(strand, canvas, i) for i, strand in enumerate(strands)],
        "groups": serialize_groups(groups),
        "selected_strand_name": selected_strand_name,  # Add selected strand name
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Saved strands and groups to {filename}")

def deserialize_strand(data, canvas, strand_dict=None, parent_strand=None):
    """Deserialize a strand from saved data."""
    try:
        start = deserialize_point(data["start"])
        end = deserialize_point(data["end"])
        width = data["width"]
        color = deserialize_color(data["color"])
        stroke_color = deserialize_color(data["stroke_color"])
        stroke_width = data["stroke_width"]
        set_number = data.get("set_number")
        layer_name = data.get("layer_name", "")
        strand_type = data.get("type", "Strand")

        strand = None

        if strand_type == "Strand":
            strand = Strand(start, end, width, color, stroke_color, stroke_width, set_number, layer_name)
        
        elif strand_type == "AttachedStrand":
            parent_layer_name = data.get("attached_to")
            if strand_dict is None:
                strand_dict = {}
            parent_strand = strand_dict.get(parent_layer_name)
            
            if parent_strand:
                # Retrieve attachment_side
                attachment_side = data.get("attachment_side", 0) # Default to 0 if missing
                logging.info(f"Deserializing {data['layer_name']} with attachment_side: {attachment_side}")
                strand = AttachedStrand(parent_strand, end, attachment_side)
                
                # Set properties for the attached strand
                strand.end = end
                strand.width = width
                strand.color = color
                strand.stroke_color = stroke_color
                strand.stroke_width = stroke_width
                strand.set_number = set_number
                strand.layer_name = layer_name
                
                # Connect layers in the canvas
                if hasattr(canvas, 'layer_state_manager'):
                    canvas.layer_state_manager.connect_layers(parent_layer_name, layer_name)
                
                # Update the parent strand's connections
                if not hasattr(parent_strand, 'connections'):
                    parent_strand.connections = []
                parent_strand.connections.append(layer_name)
                
                # Update the parent strand's position if needed
                update_parent_strand_position(parent_strand, strand)

                # Explicitly apply any circle_stroke_color from JSON so alpha=0 isn't lost:
                if "circle_stroke_color" in data and data["circle_stroke_color"] is not None:
                    raw_color = data["circle_stroke_color"]
                    loaded_color = deserialize_color(raw_color)
                    strand.circle_stroke_color = loaded_color
                    logging.info(f"Loaded circle_stroke_color for {strand.layer_name}: "
                                f"rgba({loaded_color.red()}, {loaded_color.green()}, "
                                f"{loaded_color.blue()}, {loaded_color.alpha()})")
            else:
                logging.error(f"Parent strand {parent_layer_name} not found for AttachedStrand {layer_name}")
                return None
        
        elif strand_type == "MaskedStrand":
            parts = layer_name.split('_')
            if len(parts) >= 4:
                first_layer = f"{parts[0]}_{parts[1]}"
                second_layer = f"{parts[2]}_{parts[3]}"
                
                if strand_dict:
                    first_strand = strand_dict.get(first_layer)
                    second_strand = strand_dict.get(second_layer)
                    
                    if first_strand and second_strand:
                        strand = MaskedStrand(first_strand, second_strand)
                        strand.width = width
                        strand.color = color
                        strand.stroke_color = stroke_color
                        strand.stroke_width = stroke_width
                        strand.layer_name = layer_name
                        strand.set_number = set_number
                        
                        # Initialize MaskedStrand-specific properties
                        strand._has_circles = [False, False]
                        strand.is_selected = False
                        strand.custom_mask_path = None
                        strand.deletion_rectangles = []
                        strand.base_center_point = None
                        strand.edited_center_point = None
                        strand._attached_strands = []
                        
                        # Update the mask path
                        if hasattr(strand, 'update_mask_path'):
                            strand.update_mask_path()
                        
                        logging.info(f"Successfully created MaskedStrand {layer_name}")
                    else:
                        logging.error(f"Could not find both strands for masked strand {layer_name}")
                        return None
            else:
                logging.error(f"Invalid layer name format for masked strand: {layer_name}")
                return None

        if strand is None:
            logging.error(f"Failed to create strand of type {strand_type}")
            return None

        # Set common properties
        strand.has_circles = data.get("has_circles", [False, False])
        strand.is_first_strand = data.get("is_first_strand", False)
        strand.is_start_side = data.get("is_start_side", True)
        strand.start_line_visible = data.get("start_line_visible", True)
        strand.end_line_visible = data.get("end_line_visible", True)
        strand.is_hidden = data.get("is_hidden", False)

        # NEW: Extension & Arrow visibility flags
        strand.start_extension_visible = data.get("start_extension_visible", False)
        strand.end_extension_visible = data.get("end_extension_visible", False)
        strand.start_arrow_visible = data.get("start_arrow_visible", False)
        strand.end_arrow_visible = data.get("end_arrow_visible", False)

        # Now handle control_points if present
        if "control_points" in data:
            control_points = data["control_points"]
            if control_points[0]:
                strand.control_point1 = deserialize_point(control_points[0])
            if control_points[1]:
                strand.control_point2 = deserialize_point(control_points[1])
            strand.update_control_points(reset_control_points=False)
        
        # Handle control_point_center if present
        if "control_point_center" in data:
            strand.control_point_center = deserialize_point(data["control_point_center"])
            # Also set the locked state if available
            if "control_point_center_locked" in data:
                strand.control_point_center_locked = data["control_point_center_locked"]
            logging.info(f"Loaded control_point_center for {strand.layer_name}")

        # NEW: Circle stroke color logic similar to control_points
        if "circle_stroke_color" in data and data["circle_stroke_color"] is not None:
            raw_color = data["circle_stroke_color"]
            logging.info(f"Raw circle_stroke_color from JSON for {data.get('layer_name', 'unknown')}: {raw_color}")
            loaded_color = deserialize_color(raw_color)

            # Only actually set the property if we have something non-null
            strand.circle_stroke_color = loaded_color
            if loaded_color.alpha() == 0:
                logging.info(f"[DEBUG] {strand.layer_name} loaded with a transparent circle_stroke_color (alpha=0).")
            else:
                logging.info(f"[DEBUG] {strand.layer_name} circle stroke alpha after load: {loaded_color.alpha()}")

            logging.info(
                f"Loaded circle_stroke_color for {data.get('layer_name', 'unknown')}: "
                f"(r={loaded_color.red()}, g={loaded_color.green()}, "
                f"b={loaded_color.blue()}, a={loaded_color.alpha()})"
            )
        else:
            # If the JSON did not contain circle_stroke_color, we do NOT overwrite with black
            logging.info(f"No circle_stroke_color found for {strand.layer_name}, leaving as-is.")

        if strand_type == "MaskedStrand" and "deletion_rectangles" in data:
            # Set a flag to prevent automatic repositioning
            strand.skip_center_recalculation = True
            # Set a permanent flag that this strand uses absolute coordinates for deletion rectangles
            strand.using_absolute_coords = True
            
            # Directly assign the deletion rectangles from JSON
            strand.deletion_rectangles = data["deletion_rectangles"]
            
            # Set the control_point_center from JSON as the base_center_point to prevent transformations
            if "control_point_center" in data:
                strand.base_center_point = deserialize_point(data["control_point_center"])
                strand.edited_center_point = deserialize_point(data["control_point_center"])
            
            # DON'T call update_mask_path here, which would recalculate center points
            logging.info(f"Loaded deletion rectangles verbatim with absolute coordinates: {strand.deletion_rectangles}")

            # Now that deletion rectangles and center points are set, update the visual mask path
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()

        if hasattr(strand, 'update'):
            strand.update(None, False)

        # Add verification logging after strand creation
        if hasattr(strand, 'circle_stroke_color'):
            final_color = strand.circle_stroke_color
            logging.info(f"Final circle_stroke_color for {strand.layer_name}: "
                        f"(r={final_color.red()}, g={final_color.green()}, "
                        f"b={final_color.blue()}, a={final_color.alpha()})")

        # --- NEW: Load manual circle visibility overrides ---
        if "manual_circle_visibility" in data:
            strand.manual_circle_visibility = data["manual_circle_visibility"]

        return strand

    except Exception as e:
        logging.error(f"Error deserializing strand: {str(e)}")
        return None

def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

    logging.info(f"Starting to load strands from {filename}")
    selected_strand_name = data.get("selected_strand_name", None) # Get selected strand name
    logging.info(f"Loaded selected strand name from file: {selected_strand_name}")

    # Initialize collections
    strands = [None] * len(data["strands"])  # Pre-allocate list with correct size
    strand_dict = {}
    masked_strands_data = []
    
    # First pass: Create all basic strands
    for strand_data in data["strands"]:
        if strand_data["type"] == "Strand":
            strand = deserialize_strand(strand_data, canvas)
            if strand:
                index = strand_data["index"]
                strands[index] = strand
                strand_dict[strand.layer_name] = strand
                strand.attached_strands = []  # Initialize attached_strands list
        elif strand_data["type"] == "MaskedStrand":
            masked_strands_data.append(strand_data)

    # Collect all attached strand data first to process order-independently
    attached_strands_data = [sd for sd in data["strands"] if sd["type"] == "AttachedStrand"]

    # Process attached strands until no progress can be made
    unresolved_count_prev = -1
    while attached_strands_data and unresolved_count_prev != len(attached_strands_data):
        unresolved_count_prev = len(attached_strands_data)
        remaining = []
        for strand_data in attached_strands_data:
            parent_layer_name = strand_data["attached_to"]
            parent_strand = strand_dict.get(parent_layer_name)

            if parent_strand is None:
                # Parent not created yet – postpone
                remaining.append(strand_data)
                continue

            # Parent exists – we can create this attached strand
            start = deserialize_point(strand_data["start"])
            end = deserialize_point(strand_data["end"])
            # Retrieve attachment_side
            attachment_side = strand_data.get("attachment_side", 0) # Default to 0 if missing
            logging.info(f"Deserializing {strand_data['layer_name']} with attachment_side: {attachment_side}")
            strand = AttachedStrand(parent_strand, end, attachment_side)

            # Set all properties
            strand.start = start
            strand.end = end
            strand.width = strand_data["width"]
            strand.color = deserialize_color(strand_data["color"])
            strand.stroke_color = deserialize_color(strand_data["stroke_color"])
            strand.stroke_width = strand_data["stroke_width"]
            strand.layer_name = strand_data["layer_name"]
            strand.set_number = strand_data["set_number"]
            strand.has_circles = strand_data["has_circles"]
            strand.is_first_strand = strand_data["is_first_strand"]
            strand.is_start_side = strand_data["is_start_side"]
            strand.is_hidden = strand_data.get("is_hidden", False)

            # Visibility flags
            strand.start_line_visible = strand_data.get("start_line_visible", True)
            strand.end_line_visible = strand_data.get("end_line_visible", True)

            # NEW: Extension & Arrow visibility flags
            strand.start_extension_visible = strand_data.get("start_extension_visible", False)
            strand.end_extension_visible = strand_data.get("end_extension_visible", False)
            strand.start_arrow_visible = strand_data.get("start_arrow_visible", False)
            strand.end_arrow_visible = strand_data.get("end_arrow_visible", False)

            # Circle stroke color
            if "circle_stroke_color" in strand_data and strand_data["circle_stroke_color"] is not None:
                raw_color = strand_data["circle_stroke_color"]
                strand.circle_stroke_color = deserialize_color(raw_color)

            # --- NEW: Load manual circle visibility overrides ---
            if "manual_circle_visibility" in strand_data:
                strand.manual_circle_visibility = strand_data["manual_circle_visibility"]

            # Add to collections
            index = strand_data["index"]
            if index < len(strands):
                strands[index] = strand
            else:
                # Expand list if necessary (shouldn't usually happen)
                strands.extend([None] * (index - len(strands) + 1))
                strands[index] = strand

            strand_dict[strand.layer_name] = strand
            parent_strand.attached_strands.append(strand)

            # Control points
            if "control_points" in strand_data and all(cp is not None for cp in strand_data["control_points"]):
                strand.control_point1 = deserialize_point(strand_data["control_points"][0])
                strand.control_point2 = deserialize_point(strand_data["control_points"][1])
                strand.update_control_points(reset_control_points=False)

            if "control_point_center" in strand_data:
                strand.control_point_center = deserialize_point(strand_data["control_point_center"])
                if "control_point_center_locked" in strand_data:
                    strand.control_point_center_locked = strand_data["control_point_center_locked"]

            # Layer state manager connections
            if hasattr(canvas, 'layer_state_manager'):
                canvas.layer_state_manager.connect_layers(parent_layer_name, strand.layer_name)

        attached_strands_data = remaining

    if attached_strands_data:
        # Still unresolved attached strands – log warning
        unresolved_names = [sd["layer_name"] for sd in attached_strands_data]
        logging.warning(f"Could not resolve parent strands for AttachedStrands: {unresolved_names}")

    # Third pass: Create masked strands
    for masked_data in masked_strands_data:
        parts = masked_data["layer_name"].split('_')
        if len(parts) >= 4:
            first_layer = f"{parts[0]}_{parts[1]}"
            second_layer = f"{parts[2]}_{parts[3]}"
            
            first_strand = strand_dict.get(first_layer)
            second_strand = strand_dict.get(second_layer)
            
            if first_strand and second_strand:
                strand = MaskedStrand(first_strand, second_strand)
                # Set all properties exactly as in saved data
                strand.start = deserialize_point(masked_data["start"])
                strand.end = deserialize_point(masked_data["end"])
                strand.width = masked_data["width"]
                strand.color = deserialize_color(masked_data["color"])
                strand.stroke_color = deserialize_color(masked_data["stroke_color"])
                strand.stroke_width = masked_data["stroke_width"]
                strand.layer_name = masked_data["layer_name"]
                strand.set_number = masked_data["set_number"]
                strand.has_circles = masked_data["has_circles"]
                strand.is_first_strand = masked_data["is_first_strand"]
                strand.is_start_side = masked_data["is_start_side"]
                strand.is_hidden = masked_data.get("is_hidden", False)
                
                # Load visibility flags
                strand.start_line_visible = masked_data.get("start_line_visible", True)
                strand.end_line_visible = masked_data.get("end_line_visible", True)
                
                # NEW: Extension & Arrow visibility flags
                strand.start_extension_visible = masked_data.get("start_extension_visible", False)
                strand.end_extension_visible = masked_data.get("end_extension_visible", False)
                strand.start_arrow_visible = masked_data.get("start_arrow_visible", False)
                strand.end_arrow_visible = masked_data.get("end_arrow_visible", False)
                
                if "deletion_rectangles" in masked_data:
                    # Set a flag to prevent automatic repositioning
                    strand.skip_center_recalculation = True
                    # Set a permanent flag that this strand uses absolute coordinates for deletion rectangles
                    strand.using_absolute_coords = True
                    
                    # Directly assign the deletion rectangles from JSON
                    strand.deletion_rectangles = masked_data["deletion_rectangles"]
                    
                    # Set the control_point_center from JSON as the base_center_point to prevent transformations
                    if "control_point_center" in masked_data:
                        strand.base_center_point = deserialize_point(masked_data["control_point_center"])
                        strand.edited_center_point = deserialize_point(masked_data["control_point_center"])
                    
                    # DON'T call update_mask_path here, which would recalculate center points
                    logging.info(f"Loaded deletion rectangles verbatim with absolute coordinates: {strand.deletion_rectangles}")

                    # Now that deletion rectangles and center points are set, update the visual mask path
                    if hasattr(strand, 'update_mask_path'):
                        strand.update_mask_path()

                # --- NEW: Load manual circle visibility overrides ---
                if "manual_circle_visibility" in masked_data:
                    strand.manual_circle_visibility = masked_data["manual_circle_visibility"]

                index = masked_data["index"]
                strands[index] = strand
                strand_dict[strand.layer_name] = strand

    # Remove any None values (shouldn't be any if indexes are correct)
    strands = [s for s in strands if s is not None]
    
    # Fourth pass: Validate has_circles based on actual attached strands
    for strand in strands:
        if hasattr(strand, 'has_circles') and isinstance(strand.has_circles, list) and len(strand.has_circles) == 2:
            # Reset has_circles array
            start_has_attachment = False
            end_has_attachment = False
            
            # For each strand, check if there are actual attached strands at each end
            if hasattr(strand, 'attached_strands'):
                for attached in strand.attached_strands:
                    # Determine if attached to start or end
                    # Check attachment_side to be sure
                    if attached.start == strand.start and getattr(attached, 'attachment_side', 0) == 0:
                        start_has_attachment = True
                    elif attached.start == strand.end and getattr(attached, 'attachment_side', 0) == 1:
                        end_has_attachment = True
            
            # Update has_circles to reflect actual attached strands, *unless* manually overridden
            manual_override = getattr(strand, 'manual_circle_visibility', [None, None])
            if manual_override[0] is None: # No manual override for start circle
                strand.has_circles[0] = start_has_attachment
            else: # Manual override exists, respect it
                strand.has_circles[0] = manual_override[0]

            if manual_override[1] is None: # No manual override for end circle
                strand.has_circles[1] = end_has_attachment
            else: # Manual override exists, respect it
                strand.has_circles[1] = manual_override[1]
            
            # Call update_attachable to refresh the attachable property
            if hasattr(strand, 'update_attachable'):
                strand.update_attachable()
                
            logging.info(f"Validated has_circles for {strand.layer_name}: [{strand.has_circles[0]}, {strand.has_circles[1]}]")
    
    # Apply loaded strands to canvas
    canvas.strands = strands
    
    # Set the canvas property for each strand to ensure shadows work correctly
    for strand in strands:
        strand.canvas = canvas
        # Ensure shadow color is set
        if hasattr(canvas, 'default_shadow_color') and canvas.default_shadow_color:
            strand.shadow_color = QColor(canvas.default_shadow_color)
        # Explicitly enable shadow drawing for this strand
        strand.should_draw_shadow = True
        
        # Special handling for MaskedStrand shadows
        if isinstance(strand, MaskedStrand):
            # Ensure the mask path is updated
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()
            # Force complete update for masked strands
            if hasattr(strand, 'force_complete_update'):
                try:
                    strand.force_complete_update()
                    logging.info(f"Forced complete update for MaskedStrand {strand.layer_name}")
                except Exception as e:
                    logging.error(f"Error during complete update for MaskedStrand {strand.layer_name}: {e}")
            
        # For AttachedStrand, ensure parent-child shadow relationships
        elif isinstance(strand, AttachedStrand):
            # Make sure parent shadow properties are inherited
            if hasattr(strand, 'parent') and strand.parent:
                if hasattr(strand.parent, 'shadow_color'):
                    strand.shadow_color = QColor(strand.parent.shadow_color)
                logging.info(f"Inherited shadow properties from parent for AttachedStrand {strand.layer_name}")
            
        logging.info(f"Set canvas reference and shadow properties for strand {strand.layer_name}")
    
    # Update UI
    if hasattr(canvas, 'layer_panel'):
        canvas.layer_panel.refresh()
    
    # Ensure shadows are enabled
    if hasattr(canvas, 'shadow_enabled'):
        canvas.shadow_enabled = True
        logging.info("Shadows explicitly enabled on canvas")
    
    # Make sure layer ordering is properly set for shadow calculations
    if hasattr(canvas, 'layer_state_manager'):
        # Get all layer names
        layer_names = [strand.layer_name for strand in strands if hasattr(strand, 'layer_name')]
        # Update layer state order directly
        if hasattr(canvas.layer_state_manager, 'layer_state'):
            canvas.layer_state_manager.layer_state['order'] = layer_names
            logging.info(f"Updated layer state manager order with {len(layer_names)} layers")
    
    # Force a complete redraw of the canvas to ensure shadows are rendered
    canvas.update()
    # Also force a repaint which guarantees immediate visual update
    if hasattr(canvas, 'repaint'):
        canvas.repaint()
    logging.info("Canvas updated and repainted after loading strands - this should trigger shadow rendering")

    return strands, data.get("groups", {}), selected_strand_name # Return selected strand name


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
    
    # Set the canvas property for each strand to ensure shadows work correctly
    for strand in strands:
        strand.canvas = canvas
        # Ensure shadow color is set
        if hasattr(canvas, 'default_shadow_color') and canvas.default_shadow_color:
            strand.shadow_color = QColor(canvas.default_shadow_color)
        # Explicitly enable shadow drawing for this strand
        strand.should_draw_shadow = True
        
        # Special handling for MaskedStrand shadows
        if isinstance(strand, MaskedStrand):
            # Ensure the mask path is updated
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()
            # Force complete update for masked strands
            if hasattr(strand, 'force_complete_update'):
                try:
                    strand.force_complete_update()
                    logging.info(f"Forced complete update for MaskedStrand {strand.layer_name}")
                except Exception as e:
                    logging.error(f"Error during complete update for MaskedStrand {strand.layer_name}: {e}")
            
        # For AttachedStrand, ensure parent-child shadow relationships
        elif isinstance(strand, AttachedStrand):
            # Make sure parent shadow properties are inherited
            if hasattr(strand, 'parent') and strand.parent:
                if hasattr(strand.parent, 'shadow_color'):
                    strand.shadow_color = QColor(strand.parent.shadow_color)
                logging.info(f"Inherited shadow properties from parent for AttachedStrand {strand.layer_name}")
            
        logging.info(f"Set canvas reference and shadow properties for strand {strand.layer_name}")

    # Update the LayerPanel with the loaded strands
    if hasattr(canvas, 'layer_panel'):
        # Update set_counts and track highest set number
        set_counts = {}
        highest_set = 0
        
        # Filter out masked strands and get set numbers from layer names
        for strand in strands:
            if not isinstance(strand, MaskedStrand):
                try:
                    # Extract set number from layer_name (format: "set_count")
                    set_num = int(strand.layer_name.split('_')[0])
                    set_counts[set_num] = set_counts.get(set_num, 0) + 1
                    highest_set = max(highest_set, set_num)
                except (ValueError, IndexError, AttributeError):
                    logging.warning(f"Could not parse set number from layer name: {strand.layer_name}")
                    continue
        
        # Update layer panel's set_counts and current_set
        canvas.layer_panel.set_counts = set_counts
        canvas.layer_panel.current_set = highest_set + 1
        
        logging.info(f"Updated set numbering - Next set: {canvas.layer_panel.current_set}, "
                    f"Current set counts: {set_counts} (Based on layer names)")
        
        # Refresh the panel
        canvas.layer_panel.refresh()
        logging.info(f"LayerPanel refreshed with loaded strands. Set counts: {set_counts}")

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
    if hasattr(canvas, 'shadow_enabled'):
        canvas.shadow_enabled = True
        logging.info("Shadows explicitly enabled on canvas")
    
    # Make sure layer ordering is properly set for shadow calculations
    if hasattr(canvas, 'layer_state_manager'):
        # Get all layer names
        layer_names = [strand.layer_name for strand in strands if hasattr(strand, 'layer_name')]
        # Update layer state order directly
        if hasattr(canvas.layer_state_manager, 'layer_state'):
            canvas.layer_state_manager.layer_state['order'] = layer_names
            logging.info(f"Updated layer state manager order with {len(layer_names)} layers")
        
    if hasattr(canvas, 'update'):
        canvas.update()
        # Also force a repaint which guarantees immediate visual update
        if hasattr(canvas, 'repaint'):
            canvas.repaint()
        logging.info("Canvas updated and repainted after applying groups - this should trigger shadow rendering")

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
                    "control_point2": serialize_point(points.get("control_point2")),
                    "control_point_center": serialize_point(points.get("control_point_center")),
                    "control_point_center_locked": points.get("control_point_center_locked", False)
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
                    "control_point2": deserialize_point(points["control_point2"]),
                    "control_point_center": deserialize_point(points.get("control_point_center")),
                    "control_point_center_locked": points.get("control_point_center_locked", False)
                } for layer_name, points in group_data.get("control_points", {}).items()
            }
        }
        logging.info(f"Deserialized group '{group_name}' with {len(strands)} strands")
        # Debug: Print final group structure
        logging.debug(f"Final group structure for '{group_name}': {[s.layer_name for s in strands]}")
    
    logging.info("Completed deserialization of all groups.")
    return deserialized_groups

def update_parent_strand_position(parent_strand, attached_strand):
    """
    Update the position of the parent strand based on the attached strand's position.
    """
    if attached_strand.start == parent_strand.start:
        parent_strand.start = attached_strand.start
    elif attached_strand.start == parent_strand.end:
        parent_strand.end = attached_strand.start

    parent_strand.update_shape()
    parent_strand.update_side_line()

    # Propagate position changes to attached strands
    if hasattr(parent_strand, 'attached_strands'):
        for child_strand in parent_strand.attached_strands:
            update_attached_strand_position(parent_strand, child_strand)

def update_attached_strand_position(parent_strand, attached_strand):
    """
    Update the position of an attached strand based on the parent strand's position.
    """
    if attached_strand.is_start_side:
        attached_strand.start = parent_strand.start
    else:
        attached_strand.start = parent_strand.end

    attached_strand.update_shape()
    attached_strand.update_side_line()

    # Recursively update any strands attached to this strand
    if hasattr(attached_strand, 'attached_strands'):
        for child_strand in attached_strand.attached_strands:
            update_attached_strand_position(attached_strand, child_strand)




