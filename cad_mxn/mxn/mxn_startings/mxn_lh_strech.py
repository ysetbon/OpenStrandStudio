import json
import os
import sys
import random
import colorsys


def generate_json(m, n):
    """
    LH "stretch" variant:
    Replace the hard-coded tail offsets with a computed amount (based on grid geometry)
    so attached strands extend consistently and align (as in your 1x2 temp example).
    """
    # Constants and parameters (STRECH geometry)
    #
    # This generator uses a "tighter" diagonal slant than the baseline LH:
    # - grid_unit stays 42
    # - gap becomes 28 (= 2/3 * grid_unit)
    # - stride becomes 4 * gap (= 112)
    # - main strand length becomes stride (keeps proportions consistent)
    #
    # This matches the proportions in your `mxn_lh_strech_1x2_temp.json`.
    grid_unit = 42.0  # Grid unit size in pixels
    gap = grid_unit * (2.0 / 3.0)  # 28.0 (LH is positive)
    stride = 4.0 * gap  # 112.0
    length = stride
    # Shift the whole construction by one grid unit up-left (matches the temp layout)
    center_x = 1274.0 - grid_unit
    center_y = 434.0 - grid_unit
    extension_length = 280.0

    # Colors
    fixed_colors = {
        1: {"r": 255, "g": 255, "b": 255, "a": 255},
        2: {"r": 85, "g": 170, "b": 0, "a": 255},
    }

    # Lists to hold strands by phase
    strands_1 = []  # Main strands (_1)
    strands_2 = []  # Attached strands (_2)
    strands_3 = []  # Attached strands (_3)

    index = 0

    def get_color(set_num):
        if set_num in fixed_colors:
            return fixed_colors[set_num]
        h, s, l = random.random(), random.uniform(0.2, 0.9), random.uniform(0.1, 0.9)
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
        return {"r": r, "g": g, "b": b, "a": 255}

    def create_strand_base(
        start,
        end,
        color,
        layer_name,
        set_number,
        strand_type="Strand",
        attached_to=None,
        attachment_side=None,
    ):
        nonlocal index
        if strand_type == "Strand":
            has_circles = [True, True]
        elif strand_type == "AttachedStrand":
            has_circles = [True, False]
        else:  # MaskedStrand
            has_circles = [False, False]

        cp_center = {
            "x": (start["x"] + end["x"]) / 2,
            "y": (start["y"] + end["y"]) / 2,
        }

        if strand_type == "MaskedStrand":
            control_points = [None, None]
        else:
            control_points = [
                {"x": start["x"], "y": start["y"]},
                {"x": end["x"], "y": end["y"]},
            ]

        strand = {
            "type": strand_type,
            "index": index,
            "start": start,
            "end": end,
            "width": 46,
            "color": color,
            "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "stroke_width": 4,
            "has_circles": has_circles,
            "layer_name": layer_name,
            "set_number": set_number,
            "is_first_strand": strand_type == "Strand",
            "is_start_side": strand_type == "Strand" or strand_type == "MaskedStrand",
            "start_line_visible": True,
            "end_line_visible": True,
            "is_hidden": False,
            "start_extension_visible": False,
            "end_extension_visible": False,
            "start_arrow_visible": False,
            "end_arrow_visible": False,
            "full_arrow_visible": False,
            "shadow_only": False,
            "closed_connections": [False, False],
            "arrow_color": None,
            "arrow_transparency": 100,
            "arrow_texture": "none",
            "arrow_shaft_style": "solid",
            "arrow_head_visible": True,
            "arrow_casts_shadow": False,
            "knot_connections": {},
            "circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "start_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "end_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
            "control_points": control_points,
            "control_point_center": cp_center,
            "control_point_center_locked": False,
            "bias_control": {
                "triangle_bias": 0.5,
                "circle_bias": 0.5,
                "triangle_position": None,
                "circle_position": None,
            },
            "triangle_has_moved": False,
            "control_point2_shown": False,
            "control_point2_activated": False,
        }

        if attached_to:
            strand["attached_to"] = attached_to
            strand["attachment_side"] = attachment_side
            strand["angle"] = 0
            strand["length"] = 0
            strand["is_start_side"] = False

        index += 1
        return strand

    def midpoint(a, b):
        return {"x": (a["x"] + b["x"]) / 2, "y": (a["y"] + b["y"]) / 2}

    tail_offset = grid_unit + grid_unit / 3  # 56.0

    # Verticals (Sets n+1 ... n+m)
    for i in range(m):
        cx = center_x + (i - (m - 1) / 2) * stride
        v_set_num = n + 1 + i

        # Calculate Vertical Start/End based on 4 grid units spacing from first/last horizontal
        h_top_cy = center_y - (n - 1) / 2.0 * stride
        h_bottom_cy = center_y + (n - 1) / 2.0 * stride

        # Vertical extent for STRECH:
        # Extend exactly half a stride beyond the outermost horizontal centerlines.
        # For n=2, this matches the temp file:
        #   h_top_cy=center_y-56 -> end_y=h_top_cy-56
        #   h_bottom_cy=center_y+56 -> start_y=h_bottom_cy+56
        end_y = h_top_cy - stride / 2.0
        start_y = h_bottom_cy + stride / 2.0

        start_pt = {"x": cx + gap, "y": start_y}
        end_pt = {"x": cx - gap, "y": end_y}

        main_layer = f"{v_set_num}_1"
        color = get_color(v_set_num)

        # Main Strand (_1)
        main_strand = create_strand_base(start_pt, end_pt, color, main_layer, v_set_num, "Strand")
        strands_1.append(main_strand)

        # Attached Strand (_3) - Top (End)
        # Attaches to End point. Goes down toward the bottom extent, with computed offset.
        att_3_end = {"x": end_pt["x"], "y": start_pt["y"] + tail_offset}
        strand_2_3 = create_strand_base(
            end_pt,
            att_3_end,
            color,
            f"{v_set_num}_3",
            v_set_num,
            "AttachedStrand",
            main_layer,
            1,
        )
        strands_3.append(strand_2_3)

        # Attached Strand (_2) - Bottom (Start)
        # Attaches to Start point. Goes up toward the top extent, with computed offset.
        att_2_end = {"x": start_pt["x"], "y": end_pt["y"] - tail_offset}
        strand_2_2 = create_strand_base(
            start_pt,
            att_2_end,
            color,
            f"{v_set_num}_2",
            v_set_num,
            "AttachedStrand",
            main_layer,
            0,
        )
        strands_2.append(strand_2_2)

    # Horizontals (Sets 1 ... n)
    for i in range(n):
        cy = center_y + (i - (n - 1) / 2) * stride
        h_set_num = 1 + i

        # Scaling horizontal length as well for consistency with grid size m
        base_half_w = ((m - 1) * stride + length) / 2

        start_pt = {"x": center_x - base_half_w, "y": cy + gap}
        end_pt = {"x": center_x + base_half_w, "y": cy - gap}
        main_layer = f"{h_set_num}_1"
        color = get_color(h_set_num)

        # Main Strand (_1)
        main_strand = create_strand_base(start_pt, end_pt, color, main_layer, h_set_num, "Strand")
        strands_1.append(main_strand)

        # Attached Strand (_2) - Right (End)
        # Attaches to End point. Extends left with computed offset.
        att_2_end = {"x": start_pt["x"] - tail_offset, "y": end_pt["y"]}
        strand_1_2 = create_strand_base(
            end_pt,
            att_2_end,
            color,
            f"{h_set_num}_2",
            h_set_num,
            "AttachedStrand",
            main_layer,
            1,
        )
        strands_2.append(strand_1_2)

        # Attached Strand (_3) - Left (Start)
        # Attaches to Start point. Extends right with computed offset.
        att_3_end = {"x": end_pt["x"] + tail_offset, "y": start_pt["y"]}
        strand_1_3 = create_strand_base(
            start_pt,
            att_3_end,
            color,
            f"{h_set_num}_3",
            h_set_num,
            "AttachedStrand",
            main_layer,
            0,
        )
        strands_3.append(strand_1_3)

    # Combine lists in order: Main(_1), Attached(_2), Attached(_3)
    final_strands_list = strands_1 + strands_2 + strands_3

    # Re-index
    for idx, s in enumerate(final_strands_list):
        s["index"] = idx

    # Generate masked strands
    v_tails = [s for s in final_strands_list if s["set_number"] > n and s["type"] == "AttachedStrand"]
    h_tails = [s for s in final_strands_list if s["set_number"] <= n and s["type"] == "AttachedStrand"]

    for v in v_tails:
        for h in h_tails:
            is_match = False
            # LH masking logic: Match 2 with 3, and 3 with 2 (Mixed pairs, opposite masks)
            if v["layer_name"].endswith("_2") and h["layer_name"].endswith("_3"):
                is_match = True
            elif v["layer_name"].endswith("_3") and h["layer_name"].endswith("_2"):
                is_match = True

            if is_match:
                masked_strand = {
                    "type": "MaskedStrand",
                    "index": len(final_strands_list),
                    "start": v["start"],
                    "end": v["end"],
                    "width": v["width"],
                    "color": v["color"],
                    "stroke_color": v["stroke_color"],
                    "stroke_width": v["stroke_width"],
                    "has_circles": [False, False],
                    "layer_name": f"{v['layer_name']}_{h['layer_name']}",
                    "set_number": int(f"{v['set_number']}{h['set_number']}"),
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
                    "closed_connections": [False, False],
                    "arrow_color": None,
                    "arrow_transparency": 100,
                    "arrow_texture": "none",
                    "arrow_shaft_style": "solid",
                    "arrow_head_visible": True,
                    "arrow_casts_shadow": False,
                    "knot_connections": {},
                    "circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "start_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "end_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "control_points": [None, None],
                    "control_point_center": {
                        "x": (v["start"]["x"] + v["end"]["x"]) / 2,  # Approx center
                        "y": (v["start"]["y"] + v["end"]["y"]) / 2,
                    },
                    "control_point_center_locked": False,
                    "bias_control": {
                        "triangle_bias": 0.5,
                        "circle_bias": 0.5,
                        "triangle_position": None,
                        "circle_position": None,
                    },
                    "triangle_has_moved": False,
                    "control_point2_shown": False,
                    "control_point2_activated": False,
                    "deletion_rectangles": [],
                    "first_selected_strand": v["layer_name"],
                    "second_selected_strand": h["layer_name"],
                }
                final_strands_list.append(masked_strand)

    shadow_overrides = {}
    if m == 1 and n == 1:
        # Same overrides as LH baseline
        shadow_overrides = {
            "1_3": {  # H Right
                "1_1": {"visibility": True, "allow_full_shadow": True, "subtracted_layers": ["2_3", "2_2"]},
                "2_1": {"visibility": True, "allow_full_shadow": True, "subtracted_layers": []},
                "2_3": {"visibility": False, "allow_full_shadow": False},
                "1_2": {"visibility": False, "allow_full_shadow": False},
                "2_2": {"visibility": True, "allow_full_shadow": False},
            },
            "2_2": {  # V Left in LH is 2_2
                "2_1": {"visibility": True, "subtracted_layers": [], "allow_full_shadow": True},
                "2_3": {"visibility": True, "allow_full_shadow": False},
                "1_2": {"visibility": True, "allow_full_shadow": False},
                "1_1": {"visibility": True, "subtracted_layers": ["1_2"], "allow_full_shadow": True},
            },
            "1_2": {  # H Left
                "1_1": {"visibility": True, "allow_full_shadow": True, "subtracted_layers": ["2_3", "2_2"]},
                "2_1": {"visibility": True, "allow_full_shadow": False},
                "2_3": {"visibility": True, "allow_full_shadow": True, "subtracted_layers": []},
            },
            "2_3": {  # V Right in LH is 2_3
                "1_1": {"visibility": True, "subtracted_layers": [], "allow_full_shadow": True},
                "2_1": {"visibility": True, "allow_full_shadow": True, "subtracted_layers": []},
            },
        }

    history = {
        "type": "OpenStrandStudioHistory",
        "version": 1,
        "current_step": 3,
        "max_step": 3,
        "states": [],
    }

    for step in range(1, 4):
        show_cp = step == 1
        state_data = {
            "strands": final_strands_list,
            "groups": {},
            "selected_strand_name": None,
            "locked_layers": [],
            "lock_mode": False,
            "shadow_enabled": False,
            "show_control_points": show_cp,
            "shadow_overrides": shadow_overrides,
        }
        history["states"].append({"step": step, "data": state_data})

    return json.dumps(history, indent=2)


def main():
    # Setup path to import from src if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 3 levels: mxn_startings -> mxn -> cad_mxn -> OpenStrandStudio
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    src_dir = os.path.join(root_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    output_dir = os.path.join(script_dir, "mxn_lh_strech")
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "debug.txt"), "w") as f:
        f.write("Started LH STRECH\n")

    for m in range(1, 4):  # 1 to 3
        for n in range(1, 4):  # 1 to 3
            try:
                json_content = generate_json(m, n)
                file_name = f"mxn_lh_strech_{m}x{n}.json"
                with open(os.path.join(output_dir, file_name), "w") as file:
                    file.write(json_content)
                with open(os.path.join(output_dir, "debug.txt"), "a") as f:
                    f.write(f"Generated {file_name}\n")
            except Exception as e:
                with open(os.path.join(output_dir, "debug.txt"), "a") as f:
                    f.write(f"Error {m}x{n}: {e}\n")


if __name__ == "__main__":
    print("Running main LH STRECH...")
    main()
    print("Finished main LH STRECH.")


