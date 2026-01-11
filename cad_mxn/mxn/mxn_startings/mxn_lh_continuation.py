"""
MxN LH Continuation Generator

Generates LH stretch patterns with continuation strands (_4, _5).
The continuation is based on emoji pairing logic where:
- _4 start = _2 end (attached to it)
- _4 end = paired position (same emoji on opposite side)
- _5 start = _3 end (attached to it)
- _5 end = paired position (same emoji on opposite side)

Usage:
    from mxn_lh_continuation import generate_json
    json_content = generate_json(m=2, n=2, k=0, direction="cw")
"""

import json
import os
import sys
import random
import colorsys

# Emoji names matching the order in mxn_emoji_renderer.get_animal_pool()
EMOJI_NAMES = [
    "dog", "cat", "mouse", "rabbit", "hedgehog",      # 0-4
    "fox", "bear", "panda", "koala", "tiger",         # 5-9
    "lion", "cow", "pig", "frog", "monkey",           # 10-14
    "chicken", "penguin", "bird", "chick", "duck",    # 15-19
    "owl", "bat", "wolf", "boar", "horse",            # 20-24
    "unicorn", "bee", "bug", "butterfly", "snail",    # 25-29
    "ladybug", "turtle", "snake", "lizard", "t-rex",  # 30-34
    "sauropod", "octopus", "squid", "shrimp", "lobster",  # 35-39
    "crab", "blowfish", "tropical_fish", "fish", "dolphin",  # 40-44
    "whale", "crocodile", "zebra", "giraffe", "bison"  # 45-49
]

def get_emoji_name(index):
    """Get emoji name by index, with fallback for out-of-range indices."""
    if 0 <= index < len(EMOJI_NAMES):
        return EMOJI_NAMES[index]
    return f"emoji_{index}"


__all__ = [
    "generate_json",
    # Backwards/alternate public entrypoints
    "mxn_lh_continue",
    "mxn_lh_continute",
    # Parallel alignment functions
    "align_horizontal_strands_parallel",
    "align_vertical_strands_parallel",
    "apply_parallel_alignment",
    "print_alignment_debug",
]


def mxn_lh_continue(m, n, k=0, direction="cw"):
    """Alias for `generate_json` (LH continuation)."""
    return generate_json(m=m, n=n, k=k, direction=direction)


def mxn_lh_continute(m, n, k=0, direction="cw"):
    """Typo-compatible alias for `mxn_lh_continue`."""
    return mxn_lh_continue(m=m, n=n, k=k, direction=direction)


def generate_json(m, n, k=0, direction="cw"):
    """
    Generate LH stretch pattern WITH continuation (_4, _5 strands).

    Args:
        m: Number of vertical strands
        n: Number of horizontal strands
        k: Emoji rotation value (determines pairing)
        direction: "cw" or "ccw" (rotation direction)

    Returns:
        JSON string with base + continuation strands
    """
    # Constants and parameters (same as mxn_lh_strech.py)
    grid_unit = 42.0
    gap = grid_unit * (2.0 / 3.0)  # 28.0
    stride = 4.0 * gap  # 112.0
    length = stride
    center_x = 1274.0 - grid_unit
    center_y = 434.0 - grid_unit
    tail_offset = grid_unit + grid_unit / 3  # 56.0

    # Colors
    fixed_colors = {
        1: {"r": 255, "g": 255, "b": 255, "a": 255},
        2: {"r": 85, "g": 170, "b": 0, "a": 255},
    }

    index_counter = [0]  # Use list to allow modification in nested function

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
            "index": index_counter[0],
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

        if strand_type == "MaskedStrand":
            strand["deletion_rectangles"] = []

        index_counter[0] += 1
        return strand

    # =========================================================================
    # STEP 1: Generate base strands (_1, _2, _3) - same as mxn_lh_strech.py
    # =========================================================================
    strands_1 = []  # Main strands (_1)
    strands_2 = []  # Attached strands (_2)
    strands_3 = []  # Attached strands (_3)

    # Verticals (Sets n+1 ... n+m)
    for i in range(m):
        cx = center_x + (i - (m - 1) / 2) * stride
        v_set_num = n + 1 + i

        h_top_cy = center_y - (n - 1) / 2.0 * stride
        h_bottom_cy = center_y + (n - 1) / 2.0 * stride

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
        att_3_end = {"x": end_pt["x"], "y": start_pt["y"] + tail_offset}
        strand_2_3 = create_strand_base(
            end_pt, att_3_end, color, f"{v_set_num}_3", v_set_num,
            "AttachedStrand", main_layer, 1,
        )
        strands_3.append(strand_2_3)

        # Attached Strand (_2) - Bottom (Start)
        att_2_end = {"x": start_pt["x"], "y": end_pt["y"] - tail_offset}
        strand_2_2 = create_strand_base(
            start_pt, att_2_end, color, f"{v_set_num}_2", v_set_num,
            "AttachedStrand", main_layer, 0,
        )
        strands_2.append(strand_2_2)

    # Horizontals (Sets 1 ... n)
    for i in range(n):
        cy = center_y + (i - (n - 1) / 2) * stride
        h_set_num = 1 + i

        base_half_w = ((m - 1) * stride + length) / 2

        start_pt = {"x": center_x - base_half_w, "y": cy + gap}
        end_pt = {"x": center_x + base_half_w, "y": cy - gap}
        main_layer = f"{h_set_num}_1"
        color = get_color(h_set_num)

        # Main Strand (_1)
        main_strand = create_strand_base(start_pt, end_pt, color, main_layer, h_set_num, "Strand")
        strands_1.append(main_strand)

        # Attached Strand (_2) - Right (End)
        att_2_end = {"x": start_pt["x"] - tail_offset, "y": end_pt["y"]}
        strand_1_2 = create_strand_base(
            end_pt, att_2_end, color, f"{h_set_num}_2", h_set_num,
            "AttachedStrand", main_layer, 1,
        )
        strands_2.append(strand_1_2)

        # Attached Strand (_3) - Left (Start)
        att_3_end = {"x": end_pt["x"] + tail_offset, "y": start_pt["y"]}
        strand_1_3 = create_strand_base(
            start_pt, att_3_end, color, f"{h_set_num}_3", h_set_num,
            "AttachedStrand", main_layer, 0,
        )
        strands_3.append(strand_1_3)

    # Combine base strands
    base_strands = strands_1 + strands_2 + strands_3

    # =========================================================================
    # STEP 2: Generate base masked strands (_2 x _3 crossings)
    # =========================================================================
    base_masked = []
    v_tails = [s for s in base_strands if s["set_number"] > n and s["type"] == "AttachedStrand"]
    h_tails = [s for s in base_strands if s["set_number"] <= n and s["type"] == "AttachedStrand"]

    print(f"\n=== STEP 2: Generating _2 x _3 base masks (LH) ===")
    for v in v_tails:
        for h in h_tails:
            is_match = False
            if v["layer_name"].endswith("_2") and h["layer_name"].endswith("_3"):
                is_match = True
            elif v["layer_name"].endswith("_3") and h["layer_name"].endswith("_2"):
                is_match = True

            if is_match:
                masked_strand = create_strand_base(
                    v["start"], v["end"], v["color"],
                    f"{v['layer_name']}_{h['layer_name']}",
                    int(f"{v['set_number']}{h['set_number']}"),
                    "MaskedStrand"
                )
                masked_strand["first_selected_strand"] = v["layer_name"]
                masked_strand["second_selected_strand"] = h["layer_name"]
                base_masked.append(masked_strand)
                print(f"  Base mask: {v['layer_name']} x {h['layer_name']}")

    print(f"Total _2/_3 base masks: {len(base_masked)}")
    print(f"Base mask layer names: {[m['layer_name'] for m in base_masked]}")

    # =========================================================================
    # STEP 3: Compute emoji pairings based on k and direction
    # =========================================================================

    pairings = compute_emoji_pairings(base_strands, m, n, k, direction)

    # =========================================================================
    # STEP 4: Generate continuation strands (_4, _5)
    #
    # Per the docstring:
    # - _4 attaches to _2's end and extends to the paired position (same emoji)
    # - _5 attaches to _3's end and extends to the paired position (same emoji)
    #
    # The end position is determined by the emoji pairing (which depends on k).
    # The ends are extended further outward (by tail_offset) to reach near the emoji positions.
    # =========================================================================
    strands_4 = []
    strands_5 = []

    import math

    def extend_endpoint(start_x, start_y, end_x, end_y, extension):
        """Extend the endpoint further in the same direction by the given amount."""
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.001:
            return end_x, end_y
        # Normalize and extend
        nx = dx / length
        ny = dy / length
        return end_x + nx * extension, end_y + ny * extension

    print(f"\n=== STEP 4: Generating _4 and _5 strands ===")
    print(f"Using emoji pairings to determine end positions (k={k}, {direction})")
    print(f"Pairings: {pairings}")

    for strand in base_strands:
        if strand["type"] != "AttachedStrand":
            continue

        layer_name = strand["layer_name"]
        set_num = strand["set_number"]
        color = strand["color"]

        if layer_name.endswith("_2"):
            # _4 attaches to _2's end and goes to the paired position
            start_x = strand["end"]["x"]
            start_y = strand["end"]["y"]

            # Get paired position from emoji pairing
            pairing_key = f"{layer_name}_end"
            if pairing_key in pairings:
                paired_pos = pairings[pairing_key]
                base_end_x = paired_pos["x"]
                base_end_y = paired_pos["y"]
            else:
                # Fallback: shouldn't happen if pairings are computed correctly
                print(f"  WARNING: No pairing found for {pairing_key}, using start position")
                base_end_x = start_x
                base_end_y = start_y

            # Extend the end further outward (near emoji position)
            end_x, end_y = extend_endpoint(start_x, start_y, base_end_x, base_end_y, tail_offset)

            strand_4 = create_strand_base(
                {"x": start_x, "y": start_y},
                {"x": end_x, "y": end_y},
                color,
                f"{set_num}_4",
                set_num,
                "AttachedStrand",
                layer_name,
                1,
            )
            strands_4.append(strand_4)
            print(f"  Created {set_num}_4 (from _2): start=({start_x}, {start_y}), end=({end_x:.1f}, {end_y:.1f})")

        elif layer_name.endswith("_3"):
            # _5 attaches to _3's end and goes to the paired position
            start_x = strand["end"]["x"]
            start_y = strand["end"]["y"]

            # Get paired position from emoji pairing
            pairing_key = f"{layer_name}_end"
            if pairing_key in pairings:
                paired_pos = pairings[pairing_key]
                base_end_x = paired_pos["x"]
                base_end_y = paired_pos["y"]
            else:
                # Fallback: shouldn't happen if pairings are computed correctly
                print(f"  WARNING: No pairing found for {pairing_key}, using start position")
                base_end_x = start_x
                base_end_y = start_y

            # Extend the end further outward (near emoji position)
            end_x, end_y = extend_endpoint(start_x, start_y, base_end_x, base_end_y, tail_offset)

            strand_5 = create_strand_base(
                {"x": start_x, "y": start_y},
                {"x": end_x, "y": end_y},
                color,
                f"{set_num}_5",
                set_num,
                "AttachedStrand",
                layer_name,
                1,
            )
            strands_5.append(strand_5)
            print(f"  Created {set_num}_5 (from _3): start=({start_x}, {start_y}), end=({end_x:.1f}, {end_y:.1f})")

    # Order continuation strands based on get_vertical_order_k then get_horizontal_order_k
    # Convert _2 -> _4 and _3 -> _5 for the ordering
    vertical_order_k = get_vertical_order_k(m, n, k, direction)
    horizontal_order_k = get_horizontal_order_k(m, n, k, direction)

    # Convert vertical order (_2/_3) to continuation order (_4/_5)
    vertical_continuation_order = []
    for layer in vertical_order_k:
        # e.g., "3_2" -> "3_4", "3_3" -> "3_5"
        parts = layer.split("_")
        new_suffix = "4" if parts[1] == "2" else "5"
        vertical_continuation_order.append(f"{parts[0]}_{new_suffix}")

    # Convert horizontal order (_2/_3) to continuation order (_4/_5)
    horizontal_continuation_order = []
    for layer in horizontal_order_k:
        # e.g., "1_2" -> "1_4", "1_3" -> "1_5"
        parts = layer.split("_")
        new_suffix = "4" if parts[1] == "2" else "5"
        horizontal_continuation_order.append(f"{parts[0]}_{new_suffix}")

    # Combined order: vertical first, then horizontal
    continuation_order = vertical_continuation_order + horizontal_continuation_order

    print(f"\nVertical order (k={k}, {direction}): {vertical_order_k} -> {vertical_continuation_order}")
    print(f"Horizontal order (k={k}, {direction}): {horizontal_order_k} -> {horizontal_continuation_order}")

    # Build lookup and sort continuation strands by the computed order
    all_continuation = strands_4 + strands_5
    strand_lookup = {s["layer_name"]: s for s in all_continuation}

    continuation_strands = []
    for layer_name in continuation_order:
        if layer_name in strand_lookup:
            continuation_strands.append(strand_lookup[layer_name])

    print(f"\nTotal: {len(strands_4)} _4 strands: {[s['layer_name'] for s in strands_4]}")
    print(f"Total: {len(strands_5)} _5 strands: {[s['layer_name'] for s in strands_5]}")
    print(f"Continuation order: {[s['layer_name'] for s in continuation_strands]}")

    # =========================================================================
    # STEP 5: Generate _4/_5 masks using get_mask_order_k
    # =========================================================================
    print(f"\n=== STEP 5: Generating _4/_5 continuation masks ===")

    masks_info = compute_4_5_masks(base_strands, continuation_strands, m, n, k, direction)

    continuation_masked = []
    for mask_info in masks_info:
        v_strand = mask_info["v_strand"]
        h_strand = mask_info["h_strand"]

        # Create MaskedStrand using vertical strand's geometry
        masked_strand = create_strand_base(
            v_strand["start"], v_strand["end"], v_strand["color"],
            mask_info["layer_name"],
            mask_info["set_number"],
            "MaskedStrand"
        )
        masked_strand["first_selected_strand"] = mask_info["first_strand"]
        masked_strand["second_selected_strand"] = mask_info["second_strand"]
        continuation_masked.append(masked_strand)
        print(f"  Created _4/_5 mask: {mask_info['layer_name']}")

    print(f"Total _4/_5 masks created: {len(continuation_masked)}")

    # =========================================================================
    # STEP 6: Combine all strands and build JSON
    # =========================================================================
    all_strands = base_strands + base_masked + continuation_strands + continuation_masked

    print(f"\n=== STEP 6: Final strand counts ===")
    print(f"Base strands: {len(base_strands)}")
    print(f"Base masked: {len(base_masked)}")
    print(f"Continuation strands (_4 + _5): {len(continuation_strands)}")
    print(f"Continuation masked: {len(continuation_masked)}")
    print(f"TOTAL strands: {len(all_strands)}")

    # Re-index all strands
    for idx, s in enumerate(all_strands):
        s["index"] = idx

    # Build history JSON
    history = {
        "type": "OpenStrandStudioHistory",
        "version": 1,
        "current_step": 2,
        "max_step": 2,
        "states": [],
    }

    for step in range(1, 3):
        state_data = {
            "strands": all_strands,
            "groups": {},
            "selected_strand_name": None,
            "locked_layers": [],
            "lock_mode": False,
            "shadow_enabled": False,
            "show_control_points": step == 1,
            "shadow_overrides": {},
        }
        history["states"].append({"step": step, "data": state_data})

    return json.dumps(history, indent=2)


def get_starting_order(m, n):
    """
    LH version: starting by the **top-right** and going **counterclockwise**.
    Perimeter order is: **top + left + bottom + right**.

    Matches the UI/emoji layout:
    - Top side uses `_2` (right → left)
    - Left side uses `_2` (top → bottom)
    - Bottom side uses `_3` (left → right)
    - Right side uses `_3` (bottom → top)

    Example (m=2, n=2):
    ["4_2", "3_2", "1_2", "2_2", "3_3", "4_3", "2_3", "1_3"]
    top: ["4_2", "3_2"]
    left: ["1_2", "2_2"]
    bottom: ["3_3", "4_3"]
    right: ["2_3", "1_3"]
    """
    top = [f"{i}_2" for i in reversed(range(n + 1, n + m + 1))]
    left = [f"{i}_2" for i in range(1, n  + 1)]
    bottom = [f"{i}_3" for i in range(n + 1, n + m + 1)]
    right = [f"{i}_3" for i in reversed(range(1, n  + 1))]
    
    return top + left + bottom + right

def get_starting_order_oposite_orientation(m, n):
    """
    starting by top left side and going clockwise. Top side + right side + bottom side + left side.

    Matches the UI/emoji layout:
    - Top side uses `_2` (left → right)
    - Right side uses `_3` (top → bottom)
    - Bottom side uses `_3` (right → left)
    - Left side uses `_2` (bottom → top)

    Example (m=2, n=2):
    ["3_2", "4_2", "1_3", "2_3", "4_3", "3_3", "2_2", "1_2"]
    top: ["3_2", "4_2"]
    right: ["1_3", "2_3"]
    bottom: ["4_3", "3_3"]
    left: ["2_2", "1_2"]
    """
 
    # Top: vertical sets (n+1..n+m), `_2`, left -> right
    top = [f"{i}_2" for i in range(n + 1, n + m + 1)]
    # Right: horizontal sets (1..n), `_3`, top -> bottom
    right = [f"{i}_3" for i in range(1, n + 1)]
    # Bottom: vertical sets (n+1..n+m), `_3`, right -> left
    bottom = [f"{i}_3" for i in reversed(range(n + 1, n + m + 1))]
    # Left: horizontal sets (1..n), `_2`, bottom -> top
    left = [f"{i}_2" for i in reversed(range(1, n + 1))]
    return top + right + bottom + left

def get_horizontal_order_k(m, n, k, direction):
    """
    This code works properly!
    if k is even - full order is top + left + bottom + right of get_starting_order. horizontal order when k = 0 we have pointer 1 to be pointing at first element of left side (1_2), pointer 2 pointing at last element of right side (1_3), pointer 3 pointing at second element of left side (2_2), pointer 4 pointing at one before last element of right side (2_3), etc. if k is even and not 0 we shift the pointers to the left by k/2 positions of the array of the total get_starting_order (see examples for k=2 and k=4).

    if k is odd - full order is top + right + bottom + left of get_starting_order_oposite_orientation. horizontal order when k = 1 we have pointer 1 to be pointing at first element of right side (1_3), pointer 2 pointing at last element of left side (1_2), pointer 3 pointing at second element of right side (2_3), pointer 4 pointing at one before last element of left side (2_2), etc. if k is odd and not 1 we shift the pointers to the right by (k-1)/2 positions of the array of the total get_starting_order_oposite_orientation.

    if k is negative, it is equals to 4*(m+n) + k.

    example for 2x2 with k = 0 cw, total order is (top:[4_2, 3_2] left:[1_2, 2_2] bottom:[3_3, 4_3] right:[2_3, 1_3]) ["4_2", "3_2", "1_2", "2_2", "3_3", "4_3", "2_3", "1_3"]
    so pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3, horizontal order is 1_2 1_3 2_2 2_3.

    example for 2x2 with k = 1 cw, get_starting_order_oposite_orientation (top: [3_2, 4_2] right[1_3, 2_3] bottom[4_3, 3_3] left[2_2, 1_2]) ["3_2", "4_2", "1_3", "2_3", "4_3", "3_3", "2_2", "1_2"] so pointers: 1->1_3, 2->1_2, 3->2_3, 4->2_2, horizontal order is 1_3 1_2 2_3 2_2.

    example for 2x2 with k = 2 cw, initial pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3 (for k = 0) , and the total order is (top:[4_2, 3_2] left:[1_2, 2_2] bottom:[3_3, 4_3] right:[2_3, 1_3]) ["4_2", "3_2", "1_2", "2_2", "3_3", "4_3", "2_3", "1_3"], we shift the pointers by k/2 = 1 positions, so the new pointers are (shifting to the left by 1 position): 1->3_2, 2->2_3, 3->1_2, 4->4_3, horizontal order is 3_2 2_3 1_2 4_3.

    example for 2x2 with k = 3 cw, initial pointers: 1->1_3, 2->1_2, 3->2_3, 4->2_2 (for k = 1) , and the get_starting_order_oposite_orientation (top: [3_2, 4_2] right[1_3, 2_3] bottom[4_3, 3_3] left[2_2, 1_2]) ["3_2", "4_2", "1_3", "2_3", "4_3", "3_3", "2_2", "1_2"], we shift the pointers by (k-1)/2 = 1 position, so the new pointers are (shifting to the right by 1 position): 1->2_3, 2->3_2, 3->4_3, 4->1_2, horizontal order is 2_3 3_2 4_3 1_2.

    example for 2x2 with k = 4 cw, initial pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3 (for k = 0) , and the total order is (top:[4_2, 3_2] left:[1_2, 2_2] bottom:[3_3, 4_3] right:[2_3, 1_3]) ["4_2", "3_2", "1_2", "2_2", "3_3", "4_3", "2_3", "1_3"], we shift the pointers by k/2 = 2 positions, so the new pointers are (shifting to the left by 2 positions): 
    4_2 4_3 3_2 3_3
    

    example for 2x2 with k = -1 cw, its eqals 4*(m+n) + k = 4*(2+2) + (-1) = 15, initial pointers: 1->1_3, 2->1_2, 3->2_3, 4->2_2 (for k = 1) , and the get_starting_order_oposite_orientation (top: [3_2, 4_2] right[1_3, 2_3] bottom[4_3, 3_3] left[2_2, 1_2]) ["3_2", "4_2", "1_3", "2_3", "4_3", "3_3", "2_2", "1_2"], we shift the pointers by (k-1)/2 = (15-1)/2 = 7 positions, so the new pointers are (shifting to the right by 7 positions): 1->4_2, 2->2_2, 3->1_3, 4->3_3, horizontal order is 4_2 2_2 1_3 3_3.

    we shift the pointers by (k-1)/2 = (15-1)/2 = 7 positions, so the new pointers are (shifting to the right by 7 positions): 1->4_2, 2->2_2, 3->1_3, 4->3_3, horizontal order is 4_2 2_2 1_3 3_3.


    When direction is ccw, just change the k value to -k.
    """

    if direction == "ccw":
        k = -k

    total_len = 2 * (m + n)
    full_order = get_starting_order(m, n)
    full_order_oposite_orientation = get_starting_order_oposite_orientation(m, n)
    # k=0 pointers for horizontal order pointer = ["1_2", "1_3", "2_2", "2_3", ...]
    pointer_k0 = []
    for i in range(n):
        pointer_k0.append(f"{i+1}_2")
        pointer_k0.append(f"{i+1}_3")
    pointer_k1 = []
    for i in range(n):
        pointer_k1.append(f"{i+1}_3")
        pointer_k1.append(f"{i+1}_2")
    if k == 0:
        return pointer_k0
    if k == 1:
        return pointer_k1

    # Normalize negative k to the positive equivalent (per examples in the docstring)
    if k < 0:
        k = 4 * (m + n) + k

    if k % 2 == 0:
        # Even k: shift LEFT by (k/2) on get_starting_order (see docstring examples for k=2,4)
        shift_steps = k // 2
        pointer_k = list(pointer_k0)
        for i in range(len(pointer_k)):
            strand = pointer_k[i]
            shift_position = full_order.index(strand)
            pointer_k[i] = full_order[(shift_position - shift_steps) % total_len]
    else:
        # Odd k: shift RIGHT by (k-1)/2 on get_starting_order_oposite_orientation
        shift_steps = (k-1)//2
        pointer_k = list(pointer_k1)
        for i in range(len(pointer_k)):
            strand = pointer_k[i]
            shift_position = full_order_oposite_orientation.index(strand)
            pointer_k[i] = full_order_oposite_orientation[(shift_position + shift_steps) % total_len]
    for i in range(len(pointer_k)):
        print(f"horizontal_order_k[{i}]: {pointer_k[i]}")
    return pointer_k

def get_vertical_order_k(m, n, k, direction):
    """
    Get the *vertical* endpoint order for an m×n continuation, at rotation `k` and `direction`.

    This follows the same conventions as `get_horizontal_order_k()` in this file:

    - **Direction handling**: for LH, when `direction == "ccw"`, we flip `k` (so the examples
      below are written for **cw**, matching the docstrings in this file).
    - **Negative k**: if `k < 0`, it is normalized using `k = 4*(m+n) + k`
      (kept consistent with `get_horizontal_order_k`'s implementation).
    - **Parity**:
      - even `k`: base pointers come from the `k=0` pattern and are shifted in
        `get_starting_order(m, n)` by `-(k/2)` (left by `k/2`).
      - odd `k`: base pointers come from the `k=1` pattern and are shifted in
        `get_starting_order_oposite_orientation(m, n)` by `+((k-1)/2)` (right by `(k-1)/2`).

    The returned list has length `2*m` and contains labels like `"3_2"` / `"3_3"`.

    CW examples for **m=2, n=2** (vertical sets are 3 and 4):
    - k = 0 (cw) -> ["3_2", "3_3", "4_2", "4_3"]
    - k = 1 (cw) -> ["3_3", "3_2", "4_3", "4_2"]
    """

    # Match LH horizontal convention: flip k for "ccw"
    if direction == "ccw":
        k = -k

    total_len = 2 * (m + n)
    full_order = get_starting_order(m, n)
    full_order_oposite_orientation = get_starting_order_oposite_orientation(m, n)

    # k=0 pointers for vertical order: ["(n+1)_2", "(n+1)_3", "(n+2)_2", "(n+2)_3", ...]
    pointer_k0 = []
    for i in range(m):
        pointer_k0.append(f"{n + 1 + i}_2")
        pointer_k0.append(f"{n + 1 + i}_3")

    # k=1 pointers for vertical order: ["(n+1)_3", "(n+1)_2", "(n+2)_3", "(n+2)_2", ...]
    pointer_k1 = []
    for i in range(m):
        pointer_k1.append(f"{n + 1 + i}_3")
        pointer_k1.append(f"{n + 1 + i}_2")

    if k == 0:
        return pointer_k0
    if k == 1:
        return pointer_k1

    # Normalize negative k to the positive equivalent (kept consistent with horizontal impl)
    if k < 0:
        k = 4 * (m + n) + k

    if k % 2 == 0:
        # Even k: shift LEFT by (k/2) on get_starting_order (see horizontal docstring examples)
        shift_steps = k // 2
        out = list(pointer_k0)
        for i in range(len(out)):
            # search the strand in the full_order (same break logic style as RH horizontal)
            for strand in full_order:
                if out[i] == strand:
                    shift_position = full_order.index(strand)
                    out[i] = full_order[(shift_position - shift_steps) % total_len]
                    break
        
    else:
        # Odd k: shift RIGHT by (k-1)/2 on get_starting_order_oposite_orientation
        shift_steps = (k - 1) // 2
        out = list(pointer_k1)
        for i in range(len(out)):
            # search the strand in the full_order_oposite_orientation (same break logic style as RH horizontal)
            for strand in full_order_oposite_orientation:
                if out[i] == strand:
                    shift_position = full_order_oposite_orientation.index(strand)
                    out[i] = full_order_oposite_orientation[(shift_position + shift_steps) % total_len]
                    break
    for i in range(len(out)):
        print(f"vertical_order_k[{i}]: {out[i]}")

    return out

def get_mask_order_k(m, n, k, direction):
    """
    From get_horizontal_order_k and get_vertical_order_k, get the mask order for a given k and direction.

    For even values of k, we pair odd indexes of get_vertical_order_k with even indexes of get_horizontal_order_k, and vice versa. 
    Example for 2x2 with k=0 cw, horizontal order is 1_2 1_3 2_2 2_3 and vertical order is 3_2 3_3 4_2 4_3, 
    so the mask order is 3_2_1_3 3_2_2_3 3_3_1_2 3_3_2_2 4_2_1_3 4_2_2_3 4_3_1_2 4_3_2_2.

    For odd values of k, we pair odd indexes of get_vertical_order_k with odd indexes of get_horizontal_order_k, and vice versa. Example for 2x2 with k=1 cw, horizontal order is 2_3 1_2 1_3 2_2 and vertical order is 4_3 3_2 3_3 4_2, so the mask order is 4_3_2_3 4_3_1_2 4_2_2_3 4_2_1_2 3_2_2_3 3_2_1_2 3_3_2_3 3_3_1_2.
    """
    horizontal_order_k = get_horizontal_order_k(m, n, k, direction)
    vertical_order_k = get_vertical_order_k(m, n, k, direction)

    if not horizontal_order_k or not vertical_order_k:
        return []

    #h_even is the even indexes of horizontal_order
    #h_odd is the odd indexes of horizontal_order
    h_even = [h for idx, h in enumerate(horizontal_order_k) if idx % 2 == 0]
    h_odd = [h for idx, h in enumerate(horizontal_order_k) if idx % 2 == 1]
    
    mask_order = []
    
    if k % 2 == 1:
        for idx, v in enumerate(vertical_order_k):
            # If v index is even, pair with h_odd; if v index is odd, pair with h_even
            target_h = h_odd if idx % 2 == 0 else h_even
            for h in target_h:
                mask_order.append(f"{v}_{h}")
    else:
        for idx, v in enumerate(vertical_order_k):
            # If v index is even, pair with h_even; if v index is odd, pair with h_odd
            target_h = h_even if idx % 2 == 0 else h_odd
            for h in target_h:
                mask_order.append(f"{v}_{h}")

    return mask_order


def compute_4_5_masks(base_strands, continuation_strands, m, n, k, direction):
    """
    Compute the masks for the _4 and _5 strands using get_mask_order_k.

    The mask order from get_mask_order_k gives pairings like "3_2_1_3"
    which means vertical strand 3_2 crosses horizontal strand 1_3.

    For _4/_5 strands:
    - _4 strands attach to _2 ends, so 3_2 → 3_4
    - _5 strands attach to _3 ends, so 1_3 → 1_5

    This creates masks like "3_4_1_5" for the continuation crossings.

    Returns:
        list: List of mask dictionaries with keys:
            - first_strand: layer name of first strand (vertical _4 or _5)
            - second_strand: layer name of second strand (horizontal _4 or _5)
            - layer_name: combined mask name
    """
    mask_order = get_mask_order_k(m, n, k, direction)

    print(f"\n=== Computing _4/_5 masks ===")
    print(f"Base mask order from get_mask_order_k: {mask_order}")

    # Build lookup for continuation strands by layer name
    strand_lookup = {s["layer_name"]: s for s in continuation_strands}

    masks_info = []

    for mask_entry in mask_order:
        # Parse the mask entry: "3_2_1_3" → vertical="3_2", horizontal="1_3"
        parts = mask_entry.split("_")
        if len(parts) != 4:
            print(f"  Warning: Invalid mask entry format: {mask_entry}")
            continue

        v_set = parts[0]
        v_suffix = parts[1]  # "2" or "3"
        h_set = parts[2]
        h_suffix = parts[3]  # "2" or "3"

        # Convert to _4 and _5
        # _2 → _4, _3 → _5
        v_new_suffix = "4" if v_suffix == "2" else "5"
        h_new_suffix = "4" if h_suffix == "2" else "5"

        v_layer = f"{v_set}_{v_new_suffix}"  # e.g., "3_4"
        h_layer = f"{h_set}_{h_new_suffix}"  # e.g., "1_5"

        # Check if strands exist
        v_strand = strand_lookup.get(v_layer)
        h_strand = strand_lookup.get(h_layer)

        if not v_strand or not h_strand:
            print(f"  Warning: Could not find strands {v_layer} and/or {h_layer}")
            continue

        mask_info = {
            "first_strand": v_layer,
            "second_strand": h_layer,
            "layer_name": f"{v_layer}_{h_layer}",
            "v_strand": v_strand,
            "h_strand": h_strand,
            "set_number": int(f"{v_set}{h_set}"),
        }
        masks_info.append(mask_info)
        print(f"  Mask: {mask_entry} -> {v_layer}_{h_layer}")

    print(f"Total _4/_5 mask pairs: {len(masks_info)}")
    return masks_info





def compute_emoji_pairings(strands, m, n, k, direction):
    """
    Compute which endpoints pair together based on emoji rotation.

    This must match EXACTLY how mxn_emoji_renderer assigns emojis:
    - The renderer considers BOTH start AND end of each _2/_3 strand
    - Endpoints are classified by strand DIRECTION (horizontal vs vertical)
    - Endpoints are sorted by perimeter position (clockwise from top-left)
    - Top/Right get unique labels, Bottom/Left mirror them
    - Rotation k shifts all labels around the perimeter
    - Each endpoint pairs with the OTHER endpoint that has the same emoji

    Returns:
        dict: {"{layer_name}_end": {"x": x, "y": y}, ...}
    """
    # Collect BOTH start and end of each _2/_3 strand (matching emoji renderer)
    all_endpoints = []

    for strand in strands:
        if strand["type"] != "AttachedStrand":
            continue

        layer_name = strand["layer_name"]
        if not (layer_name.endswith("_2") or layer_name.endswith("_3")):
            continue

        # Get both start and end positions
        start_x = strand["start"]["x"]
        start_y = strand["start"]["y"]
        end_x = strand["end"]["x"]
        end_y = strand["end"]["y"]

        dx = end_x - start_x
        dy = end_y - start_y

        # Classify endpoints by strand DIRECTION (same as emoji renderer)
        if abs(dx) >= abs(dy):
            # Horizontal strand
            if start_x <= end_x:
                start_side = "left"
                end_side = "right"
            else:
                start_side = "right"
                end_side = "left"
        else:
            # Vertical strand
            if start_y <= end_y:
                start_side = "top"
                end_side = "bottom"
            else:
                start_side = "bottom"
                end_side = "top"

        # Add START endpoint
        all_endpoints.append({
            "layer_name": layer_name,
            "endpoint_type": "start",
            "x": start_x,
            "y": start_y,
            "side": start_side,
            "set_number": strand["set_number"],
        })

        # Add END endpoint
        all_endpoints.append({
            "layer_name": layer_name,
            "endpoint_type": "end",
            "x": end_x,
            "y": end_y,
            "side": end_side,
            "set_number": strand["set_number"],
        })

    if not all_endpoints:
        return {}

    # Group endpoints by side
    top_eps = [ep for ep in all_endpoints if ep["side"] == "top"]
    right_eps = [ep for ep in all_endpoints if ep["side"] == "right"]
    bottom_eps = [ep for ep in all_endpoints if ep["side"] == "bottom"]
    left_eps = [ep for ep in all_endpoints if ep["side"] == "left"]

    # Sort by position (same as emoji renderer):
    # Top/Bottom: sort by X (left to right)
    # Left/Right: sort by Y (top to bottom)
    top_eps.sort(key=lambda ep: ep["x"])
    bottom_eps.sort(key=lambda ep: ep["x"])
    left_eps.sort(key=lambda ep: ep["y"])
    right_eps.sort(key=lambda ep: ep["y"])

    # Build perimeter order (clockwise from top-left):
    # top (L->R), right (T->B), bottom (R->L reversed), left (B->T reversed)
    perimeter_order = (
        top_eps +
        right_eps +
        list(reversed(bottom_eps)) +
        list(reversed(left_eps))
    )

    total = len(perimeter_order)
    if total == 0:
        return {}

    # Assign perimeter indices
    for idx, ep in enumerate(perimeter_order):
        ep["perimeter_index"] = idx

    # Build base labels with mirroring at k=0 (SAME AS EMOJI RENDERER)
    # Top and Right get unique labels
    # Bottom mirrors Top, Left mirrors Right
    top_count = len(top_eps)
    right_count = len(right_eps)
    bottom_count = len(bottom_eps)
    left_count = len(left_eps)

    # Unique labels for top and right
    top_labels = list(range(top_count))
    right_labels = list(range(top_count, top_count + right_count))

    # Mirror for bottom and left
    bottom_labels = list(reversed(top_labels[:bottom_count]))
    left_labels = list(reversed(right_labels[:left_count]))

    # Combine in perimeter order
    base_labels = top_labels + right_labels + bottom_labels + left_labels

    # Apply rotation k
    rotated_labels = rotate_labels(base_labels, k, direction)

    # Assign rotated labels to endpoints
    for idx, ep in enumerate(perimeter_order):
        ep["emoji_index"] = rotated_labels[idx]

    # Build pairing map: for each END endpoint, find where the matching emoji is
    # The _4 strand attaches to _2's END and goes to where the same emoji appears
    # The _5 strand attaches to _3's END and goes to where the same emoji appears
    pairings = {}
    for ep in perimeter_order:
        # Only build pairings for END endpoints (since _4/_5 attach to ends)
        if ep.get("endpoint_type") != "end":
            continue

        target_emoji = ep["emoji_index"]

        # Find the OTHER endpoint with the same emoji (any endpoint except this one)
        for other_ep in perimeter_order:
            # Skip self (same layer AND same endpoint type)
            if other_ep["layer_name"] == ep["layer_name"] and other_ep.get("endpoint_type") == ep.get("endpoint_type"):
                continue
            if other_ep["emoji_index"] == target_emoji:
                pairings[f"{ep['layer_name']}_end"] = {
                    "x": other_ep["x"],
                    "y": other_ep["y"],
                }
                break

    # Debug output
    print(f"\n=== Emoji Pairing Debug (k={k}, {direction}) ===")
    print(f"Top ({len(top_eps)}): {[(ep['layer_name'], ep.get('endpoint_type','?'), ep['emoji_index']) for ep in top_eps]}")
    print(f"Right ({len(right_eps)}): {[(ep['layer_name'], ep.get('endpoint_type','?'), ep['emoji_index']) for ep in right_eps]}")
    print(f"Bottom ({len(bottom_eps)}): {[(ep['layer_name'], ep.get('endpoint_type','?'), ep['emoji_index']) for ep in bottom_eps]}")
    print(f"Left ({len(left_eps)}): {[(ep['layer_name'], ep.get('endpoint_type','?'), ep['emoji_index']) for ep in left_eps]}")
    print(f"Pairings: {pairings}")
    print("=" * 50)

    return pairings


def rotate_labels(labels, k, direction):
    """
    Rotate labels by k positions.

    Args:
        labels: List of label indices
        k: Rotation amount
        direction: "cw" or "ccw"

    Returns:
        New list with rotated labels
    """
    n = len(labels)
    if n == 0:
        return labels

    # Normalize shift
    shift = k % n
    if shift < 0:
        shift += n

    # CCW is opposite of CW
    if direction == "ccw":
        shift = (n - shift) % n

    # Rotate: each label moves to position (i + shift) % n
    out = [None] * n
    for i in range(n):
        out[(i + shift) % n] = labels[i]

    return out


# =============================================================================
# PARALLEL ALIGNMENT FUNCTIONS
# =============================================================================

import math

def get_parallel_alignment_preview(all_strands, n, m):
    """
    Get preview information for parallel alignment angle ranges.
    Returns first/last strand positions and default angle ranges for both H and V.

    Returns:
        dict with:
            - horizontal: {first, last, initial_angle, angle_min, angle_max}
            - vertical: {first, last, initial_angle, angle_min, angle_max}
    """
    result = {"horizontal": None, "vertical": None}

    # Collect horizontal _4/_5 strands (set_number <= n)
    h_strands = []
    for strand in all_strands:
        if strand["type"] != "AttachedStrand":
            continue
        layer_name = strand["layer_name"]
        set_num = strand["set_number"]
        if set_num > n:
            continue
        if layer_name.endswith("_4") or layer_name.endswith("_5"):
            # Find the _2 or _3 strand this attaches to
            suffix = "_2" if layer_name.endswith("_4") else "_3"
            base_name = layer_name.rsplit("_", 1)[0] + suffix
            s2_3 = next((s for s in all_strands if s["layer_name"] == base_name), None)
            if s2_3:
                h_strands.append({
                    "strand": strand,
                    "strand_2_3": s2_3,
                    "set_number": set_num,
                    "start": {"x": strand["start"]["x"], "y": strand["start"]["y"]},
                    "target": {"x": strand["end"]["x"], "y": strand["end"]["y"]},
                })

    if len(h_strands) >= 2:
        # Sort by set_number, then by layer_name (_4 before _5 within each set)
        h_strands.sort(key=lambda h: (h["set_number"], h["strand"]["layer_name"]))

        first_h = h_strands[0]
        last_h = h_strands[-1]

        # Calculate initial angle of first strand
        dx = first_h["target"]["x"] - first_h["start"]["x"]
        dy = first_h["target"]["y"] - first_h["start"]["y"]
        initial_angle = math.degrees(math.atan2(dy, dx))

        # Get full strand order
        strand_order = [h["strand"]["layer_name"] for h in h_strands]

        result["horizontal"] = {
            "first_start": first_h["start"],
            "first_target": first_h["target"],
            "last_start": last_h["start"],
            "last_target": last_h["target"],
            "initial_angle": initial_angle,
            "angle_min": initial_angle - 20,
            "angle_max": initial_angle + 20,
            "first_name": first_h["strand"]["layer_name"],
            "last_name": last_h["strand"]["layer_name"],
            "strand_order": strand_order,
        }

    # Collect vertical _4/_5 strands (set_number > n)
    v_strands = []
    for strand in all_strands:
        if strand["type"] != "AttachedStrand":
            continue
        layer_name = strand["layer_name"]
        set_num = strand["set_number"]
        if set_num <= n:
            continue
        if layer_name.endswith("_4") or layer_name.endswith("_5"):
            suffix = "_2" if layer_name.endswith("_4") else "_3"
            base_name = layer_name.rsplit("_", 1)[0] + suffix
            s2_3 = next((s for s in all_strands if s["layer_name"] == base_name), None)
            if s2_3:
                v_strands.append({
                    "strand": strand,
                    "strand_2_3": s2_3,
                    "set_number": set_num,
                    "start": {"x": strand["start"]["x"], "y": strand["start"]["y"]},
                    "target": {"x": strand["end"]["x"], "y": strand["end"]["y"]},
                })

    if len(v_strands) >= 2:
        # Sort by set_number, then by layer_name (_4 before _5 within each set)
        v_strands.sort(key=lambda v: (v["set_number"], v["strand"]["layer_name"]))

        first_v = v_strands[0]
        last_v = v_strands[-1]

        # Calculate initial angle of first strand
        dx = first_v["target"]["x"] - first_v["start"]["x"]
        dy = first_v["target"]["y"] - first_v["start"]["y"]
        initial_angle = math.degrees(math.atan2(dy, dx))

        # Get full strand order
        strand_order = [v["strand"]["layer_name"] for v in v_strands]

        result["vertical"] = {
            "first_start": first_v["start"],
            "first_target": first_v["target"],
            "last_start": last_v["start"],
            "last_target": last_v["target"],
            "initial_angle": initial_angle,
            "angle_min": initial_angle - 20,
            "angle_max": initial_angle + 20,
            "first_name": first_v["strand"]["layer_name"],
            "last_name": last_v["strand"]["layer_name"],
            "strand_order": strand_order,
        }

    return result


def align_horizontal_strands_parallel(all_strands, n,
                                       angle_step_degrees=0.5,
                                       max_extension=100.0, strand_width=46,
                                       custom_angle_min=None, custom_angle_max=None,
                                       on_config_callback=None):
    """
    Parallel alignment of horizontal _4/_5 strands using first-last pair approach.

    Algorithm:
    1. Calculate angle range: first strand's initial angle ±20° (or use custom range)
    2. LAST strand should use angle + 180° (opposite direction)
    3. For each angle in range, check if first and last can reach their targets
    4. Then check if MIDDLE strands can adapt (with extensions if needed)
    5. Validate gaps are within strand_width to strand_width*1.5

    Args:
        all_strands: List of all strand dictionaries
        n: Number of horizontal strand sets (horizontal sets are 1..n)
        angle_step_degrees: Step size for angle search (default 0.5°)
        max_extension: Maximum allowed extension for _2/_3 strands
        strand_width: Width of strands for gap calculation (default 46)
        custom_angle_min: Optional custom minimum angle (degrees)
        custom_angle_max: Optional custom maximum angle (degrees)
        on_config_callback: Optional callback(angle_deg, extension, result) called for each config

    Returns:
        dict with success, angle, configurations, gaps, etc.
    """

    # Separate strands by type
    strands_2 = []  # Horizontal _2 strands
    strands_3 = []  # Horizontal _3 strands
    strands_4 = []  # Horizontal _4 strands
    strands_5 = []  # Horizontal _5 strands

    for strand in all_strands:
        if strand["type"] != "AttachedStrand":
            continue

        layer_name = strand["layer_name"]
        set_num = strand["set_number"]

        # Only process horizontal strands (set_number <= n)
        if set_num > n:
            continue

        if layer_name.endswith("_2"):
            strands_2.append(strand)
        elif layer_name.endswith("_3"):
            strands_3.append(strand)
        elif layer_name.endswith("_4"):
            strands_4.append(strand)
        elif layer_name.endswith("_5"):
            strands_5.append(strand)

    if not strands_4 and not strands_5:
        return {
            "success": False,
            "message": "No horizontal _4/_5 strands found"
        }


    # Collect all horizontal _4/_5 strands with their target positions
    horizontal_strands = []

    for s4 in strands_4:
        set_num = s4["set_number"]
        s2 = next((s for s in strands_2 if s["set_number"] == set_num), None)
        if s2:
            horizontal_strands.append({
                "strand_4_5": s4,
                "strand_2_3": s2,
                "type": "_4",
                "set_number": set_num,
                "original_start": {"x": s4["start"]["x"], "y": s4["start"]["y"]},
                "target_position": {"x": s4["end"]["x"], "y": s4["end"]["y"]},
            })

    for s5 in strands_5:
        set_num = s5["set_number"]
        s3 = next((s for s in strands_3 if s["set_number"] == set_num), None)
        if s3:
            horizontal_strands.append({
                "strand_4_5": s5,
                "strand_2_3": s3,
                "type": "_5",
                "set_number": set_num,
                "original_start": {"x": s5["start"]["x"], "y": s5["start"]["y"]},
                "target_position": {"x": s5["end"]["x"], "y": s5["end"]["y"]},
            })

    # Sort by set_number, then by type (_4 before _5 within each set)
    horizontal_strands.sort(key=lambda h: (h["set_number"], h["type"]))

    num_strands = len(horizontal_strands)
    if num_strands < 2:
        return {
            "success": False,
            "message": "Need at least 2 horizontal strands for parallel alignment"
        }

    # Get FIRST and LAST strands
    first_strand = horizontal_strands[0]
    last_strand = horizontal_strands[-1]

    # Get _2/_3 extension directions for first and last strands
    first_s23 = first_strand["strand_2_3"]
    first_s23_dx = first_s23["end"]["x"] - first_s23["start"]["x"]
    first_s23_dy = first_s23["end"]["y"] - first_s23["start"]["y"]
    first_s23_len = math.sqrt(first_s23_dx**2 + first_s23_dy**2)
    first_s23_nx = first_s23_dx / first_s23_len if first_s23_len > 0.001 else 0
    first_s23_ny = first_s23_dy / first_s23_len if first_s23_len > 0.001 else 0

    last_s23 = last_strand["strand_2_3"]
    last_s23_dx = last_s23["end"]["x"] - last_s23["start"]["x"]
    last_s23_dy = last_s23["end"]["y"] - last_s23["start"]["y"]
    last_s23_len = math.sqrt(last_s23_dx**2 + last_s23_dy**2)
    last_s23_nx = last_s23_dx / last_s23_len if last_s23_len > 0.001 else 0
    last_s23_ny = last_s23_dy / last_s23_len if last_s23_len > 0.001 else 0

    # Store original start positions
    first_original_start = {"x": first_strand["original_start"]["x"], "y": first_strand["original_start"]["y"]}
    last_original_start = {"x": last_strand["original_start"]["x"], "y": last_strand["original_start"]["y"]}

    print(f"\n=== Horizontal Parallel Alignment (First-Last Pair Approach) ===")
    print(f"Found {num_strands} horizontal _4/_5 strands")
    print(f"Max extension: {max_extension}")
    print(f"Strand width: {strand_width}")
    print(f"First-Last pair extension: 0 to 200 px (step 5)")

    # Debug: Print details of each strand
    print(f"\n--- Strand Details ---")
    for i, h in enumerate(horizontal_strands):
        dx = h['target_position']['x'] - h['original_start']['x']
        dy = h['target_position']['y'] - h['original_start']['y']
        angle = math.degrees(math.atan2(dy, dx))
        label = ""
        if i == 0:
            label = " [FIRST]"
        elif i == num_strands - 1:
            label = " [LAST]"
        print(f"  {i+1}. {h['strand_4_5']['layer_name']}{label} angle={angle:.1f}°")

    # Calculate the initial angle of the FIRST strand (from start to target)
    first_dx = first_strand["target_position"]["x"] - first_strand["original_start"]["x"]
    first_dy = first_strand["target_position"]["y"] - first_strand["original_start"]["y"]
    first_initial_angle = math.degrees(math.atan2(first_dy, first_dx))

    # Use custom angle range if provided, otherwise use ±20° from initial angle
    use_custom_h = custom_angle_min is not None and custom_angle_max is not None
    if use_custom_h:
        base_angle_min = custom_angle_min
        base_angle_max = custom_angle_max
        print(f"\n--- Using CUSTOM Horizontal Angle Range ---")
        print(f"    Custom range: {base_angle_min:.2f}° to {base_angle_max:.2f}°")
    else:
        base_angle_min = first_initial_angle - 20
        base_angle_max = first_initial_angle + 20
        print(f"\n--- Angle Range: First strand initial angle ±20° ---")
        print(f"    First strand initial angle: {first_initial_angle:.2f}°")
        print(f"    Angle range: {base_angle_min:.2f}° to {base_angle_max:.2f}°")

    # Outer loop: extend first-last pair starting points (0 to 200 px, step 5)
    best_result = None
    best_pair_extension = 0

    # Track best fallback candidate (max-min optimization: maximize the worst gap)
    best_fallback = None
    best_fallback_worst_gap = -float('inf')
    best_fallback_extension = 0
    best_fallback_angle = 0

    for pair_extension in range(0, 210, 10):  # Step 10px instead of 5px
        # Extend first and last strand starting positions
        first_strand["original_start"]["x"] = first_original_start["x"] + pair_extension * first_s23_nx
        first_strand["original_start"]["y"] = first_original_start["y"] + pair_extension * first_s23_ny
        last_strand["original_start"]["x"] = last_original_start["x"] + pair_extension * last_s23_nx
        last_strand["original_start"]["y"] = last_original_start["y"] + pair_extension * last_s23_ny

        # Recalculate the first strand's angle after extension (for auto mode)
        first_dx_ext = first_strand["target_position"]["x"] - first_strand["original_start"]["x"]
        first_dy_ext = first_strand["target_position"]["y"] - first_strand["original_start"]["y"]
        first_angle_ext = math.degrees(math.atan2(first_dy_ext, first_dx_ext))

        # Use custom angles directly, or recalculate based on extension
        if use_custom_h:
            angle_min_deg = base_angle_min
            angle_max_deg = base_angle_max
        else:
            angle_min_deg = first_angle_ext - 10
            angle_max_deg = first_angle_ext + 10

        if pair_extension % 40 == 0:  # Log every 40px
            print(f"\n--- Pair Extension: {pair_extension}px ---")
            print(f"    First strand angle (extended): {first_angle_ext:.2f}°")
            print(f"    Angle range: {angle_min_deg:.2f}° to {angle_max_deg:.2f}°")

        # Search within the angle range
        angle_start = int(angle_min_deg * 100)
        angle_end = int(angle_max_deg * 100)
        step = max(1, int(angle_step_degrees * 100))

        best_gap_variance = float('inf')
        angles_tested = 0
        valid_count = 0
        fail_reasons = {}

        for angle_hundredth in range(angle_start, angle_end + 1, step):
            angle_deg = angle_hundredth / 100.0
            angle_rad = math.radians(angle_deg)
            angles_tested += 1

            result = try_angle_configuration_first_last(
                horizontal_strands,
                angle_rad,
                max_extension,
                strand_width,
                verbose=False
            )

            # Call callback for each configuration tried
            if on_config_callback:
                on_config_callback(angle_deg, pair_extension, result, "horizontal")

            if result["valid"]:
                valid_count += 1
                gap_variance = result["gap_variance"]

                if gap_variance < best_gap_variance:
                    best_gap_variance = gap_variance
                    best_result = result
                    best_result["angle_degrees"] = angle_deg
                    best_result["pair_extension"] = pair_extension
                    best_pair_extension = pair_extension

                    if gap_variance < 0.01:
                        break
            else:
                # Track failure reason
                reason = result.get("reason", "unknown")
                fail_reasons[reason] = fail_reasons.get(reason, 0) + 1

                # Track fallback: only consider if directions are valid (no crossing)
                fallback = result.get("fallback")
                if fallback and result.get("directions_valid", False):
                    worst_gap = fallback.get("worst_gap", 0)
                    if worst_gap > best_fallback_worst_gap:
                        best_fallback_worst_gap = worst_gap
                        best_fallback = fallback
                        best_fallback_extension = pair_extension
                        best_fallback_angle = angle_deg

        # Log summary for this extension
        if pair_extension % 20 == 0 or valid_count > 0:
            print(f"\n  Extension {pair_extension}px: tested {angles_tested} angles, {valid_count} valid")
            if fail_reasons:
                top_reasons = sorted(fail_reasons.items(), key=lambda x: -x[1])[:3]
                for reason, count in top_reasons:
                    print(f"    - {reason}: {count} times")

        if best_result and best_result.get("pair_extension") == pair_extension:
            print(f"\n  >>> SUCCESS at extension {pair_extension}px, angle {best_result['angle_degrees']:.2f}°")
            print(f"      Gap variance: {best_result['gap_variance']:.4f}, Avg gap: {best_result['average_gap']:.2f}px")
            break  # Found a valid configuration, stop extending

    # Restore original positions (they will be updated by apply_parallel_alignment)
    first_strand["original_start"]["x"] = first_original_start["x"]
    first_strand["original_start"]["y"] = first_original_start["y"]
    last_strand["original_start"]["x"] = last_original_start["x"]
    last_strand["original_start"]["y"] = last_original_start["y"]

    if best_result:
        print(f"\n=== Best Solution Found ===")
        print(f"Pair extension: {best_pair_extension}px")
        print(f"Angle: {best_result['angle_degrees']:.2f}°")
        print(f"Gap variance: {best_result['gap_variance']:.4f}")
        print(f"Average gap: {best_result['average_gap']:.2f}")

        return {
            "success": True,
            "angle": best_result["angle"],
            "angle_degrees": best_result["angle_degrees"],
            "configurations": best_result["configurations"],
            "average_gap": best_result["average_gap"],
            "gap_variance": best_result["gap_variance"],
            "pair_extension": best_pair_extension,
            "min_gap": best_result.get("min_gap", strand_width),
            "max_gap": best_result.get("max_gap", strand_width * 1.5),
            "message": f"Found parallel configuration at {best_result['angle_degrees']:.2f}° (pair ext: {best_pair_extension}px)"
        }
    elif best_fallback:
        # Return best fallback candidate (max-min: the one with maximum worst gap)
        print(f"\n=== Best Fallback Candidate (no valid solution) ===")
        print(f"Pair extension: {best_fallback_extension}px")
        print(f"Angle: {best_fallback_angle:.2f}°")
        print(f"Worst gap (min): {best_fallback_worst_gap:.2f}px")
        print(f"Average gap: {best_fallback['average_gap']:.2f}px")
        print(f"All gaps: {[f'{g:.1f}' for g in best_fallback['gaps']]}")

        return {
            "success": False,
            "is_fallback": True,
            "angle": best_fallback["angle"],
            "angle_degrees": best_fallback_angle,
            "configurations": best_fallback["configurations"],
            "average_gap": best_fallback["average_gap"],
            "gap_variance": best_fallback["gap_variance"],
            "worst_gap": best_fallback_worst_gap,
            "gaps": best_fallback["gaps"],
            "pair_extension": best_fallback_extension,
            "min_gap": best_fallback.get("min_gap", strand_width),
            "max_gap": best_fallback.get("max_gap", strand_width * 1.5),
            "message": f"Fallback: best candidate at {best_fallback_angle:.2f}° (worst gap: {best_fallback_worst_gap:.1f}px)"
        }
    else:
        print(f"\n=== No Solution Found ===")
        print(f"Tried pair extensions from 0 to 200px")
        return {
            "success": False,
            "message": "Could not find any valid configuration or fallback (tried pair extensions 0-200px)"
        }


def align_vertical_strands_parallel(all_strands, n, m,
                                     angle_step_degrees=0.5,
                                     max_extension=100.0, strand_width=46,
                                     custom_angle_min=None, custom_angle_max=None,
                                     on_config_callback=None):
    """
    Parallel alignment of vertical _4/_5 strands using first-last pair approach.

    Algorithm:
    1. Calculate angle range: first strand's initial angle ±20° (or use custom range)
    2. LAST strand should use angle + 180° (opposite direction)
    3. For each angle in range, check if first and last can reach their targets
    4. Then check if MIDDLE strands can adapt (with extensions if needed)
    5. Validate gaps are within strand_width to strand_width*1.5

    Args:
        all_strands: List of all strand dictionaries
        n: Number of horizontal strand sets
        m: Number of vertical strand sets (vertical sets are n+1 to n+m)
        angle_step_degrees: Step size for angle search (default 0.5°)
        max_extension: Maximum allowed extension for _2/_3 strands
        strand_width: Width of strands for gap calculation (default 46)
        custom_angle_min: Optional custom minimum angle (degrees)
        custom_angle_max: Optional custom maximum angle (degrees)
        on_config_callback: Optional callback(angle_deg, extension, result) called for each config

    Returns:
        dict: {
            "success": bool,
            "angle": float (radians),
            "configurations": list of strand configurations,
            "average_gap": float,
            "gap_variance": float,
            "message": str
        }
    """

    # Separate strands by type - VERTICAL strands (set_number > n)
    strands_2 = []  # Vertical _2 strands
    strands_3 = []  # Vertical _3 strands
    strands_4 = []  # Vertical _4 strands
    strands_5 = []  # Vertical _5 strands

    for strand in all_strands:
        if strand["type"] != "AttachedStrand":
            continue

        layer_name = strand["layer_name"]
        set_num = strand["set_number"]

        # Only process vertical strands (set_number > n and <= n+m)
        if set_num <= n or set_num > n + m:
            continue

        if layer_name.endswith("_2"):
            strands_2.append(strand)
        elif layer_name.endswith("_3"):
            strands_3.append(strand)
        elif layer_name.endswith("_4"):
            strands_4.append(strand)
        elif layer_name.endswith("_5"):
            strands_5.append(strand)

    if not strands_4 and not strands_5:
        return {
            "success": False,
            "message": "No vertical _4/_5 strands found"
        }

    # Collect all vertical _4/_5 strands with their target positions
    vertical_strands = []

    for s4 in strands_4:
        set_num = s4["set_number"]
        # Find corresponding _2 strand
        s2 = next((s for s in strands_2 if s["set_number"] == set_num), None)
        if s2:
            vertical_strands.append({
                "strand_4_5": s4,
                "strand_2_3": s2,
                "type": "_4",
                "set_number": set_num,
                "original_start": {"x": s4["start"]["x"], "y": s4["start"]["y"]},
                "target_position": {"x": s4["end"]["x"], "y": s4["end"]["y"]},
            })

    for s5 in strands_5:
        set_num = s5["set_number"]
        # Find corresponding _3 strand
        s3 = next((s for s in strands_3 if s["set_number"] == set_num), None)
        if s3:
            vertical_strands.append({
                "strand_4_5": s5,
                "strand_2_3": s3,
                "type": "_5",
                "set_number": set_num,
                "original_start": {"x": s5["start"]["x"], "y": s5["start"]["y"]},
                "target_position": {"x": s5["end"]["x"], "y": s5["end"]["y"]},
            })

    # Sort by set_number, then by type (_4 before _5 within each set)
    vertical_strands.sort(key=lambda v: (v["set_number"], v["type"]))

    num_strands = len(vertical_strands)
    if num_strands < 2:
        return {
            "success": False,
            "message": "Need at least 2 vertical strands for parallel alignment"
        }

    # Get FIRST and LAST strands
    first_strand = vertical_strands[0]
    last_strand = vertical_strands[-1]

    # Get _2/_3 extension directions for first and last strands
    first_s23 = first_strand["strand_2_3"]
    first_s23_dx = first_s23["end"]["x"] - first_s23["start"]["x"]
    first_s23_dy = first_s23["end"]["y"] - first_s23["start"]["y"]
    first_s23_len = math.sqrt(first_s23_dx**2 + first_s23_dy**2)
    first_s23_nx = first_s23_dx / first_s23_len if first_s23_len > 0.001 else 0
    first_s23_ny = first_s23_dy / first_s23_len if first_s23_len > 0.001 else 0

    last_s23 = last_strand["strand_2_3"]
    last_s23_dx = last_s23["end"]["x"] - last_s23["start"]["x"]
    last_s23_dy = last_s23["end"]["y"] - last_s23["start"]["y"]
    last_s23_len = math.sqrt(last_s23_dx**2 + last_s23_dy**2)
    last_s23_nx = last_s23_dx / last_s23_len if last_s23_len > 0.001 else 0
    last_s23_ny = last_s23_dy / last_s23_len if last_s23_len > 0.001 else 0

    # Store original start positions
    first_original_start = {"x": first_strand["original_start"]["x"], "y": first_strand["original_start"]["y"]}
    last_original_start = {"x": last_strand["original_start"]["x"], "y": last_strand["original_start"]["y"]}

    print(f"\n=== Vertical Parallel Alignment (First-Last Pair Approach) ===")
    print(f"Found {num_strands} vertical _4/_5 strands")
    print(f"Max extension: {max_extension}")
    print(f"Strand width: {strand_width}")
    print(f"First-Last pair extension: 0 to 200 px (step 5)")

    # Debug: Print details of each strand
    print(f"\n--- Vertical Strand Details ---")
    for i, v in enumerate(vertical_strands):
        dx = v['target_position']['x'] - v['original_start']['x']
        dy = v['target_position']['y'] - v['original_start']['y']
        angle = math.degrees(math.atan2(dy, dx))
        label = ""
        if i == 0:
            label = " [FIRST]"
        elif i == num_strands - 1:
            label = " [LAST]"
        print(f"  {i+1}. {v['strand_4_5']['layer_name']}{label} angle={angle:.1f}°")

    # Calculate the initial angle of the FIRST strand (from start to target)
    first_dx = first_strand["target_position"]["x"] - first_strand["original_start"]["x"]
    first_dy = first_strand["target_position"]["y"] - first_strand["original_start"]["y"]
    first_initial_angle = math.degrees(math.atan2(first_dy, first_dx))

    # Use custom angle range if provided, otherwise use ±20° from initial angle
    use_custom_v = custom_angle_min is not None and custom_angle_max is not None
    if use_custom_v:
        base_angle_min = custom_angle_min
        base_angle_max = custom_angle_max
        print(f"\n--- Using CUSTOM Vertical Angle Range ---")
        print(f"    Custom range: {base_angle_min:.2f}° to {base_angle_max:.2f}°")
    else:
        base_angle_min = first_initial_angle - 20
        base_angle_max = first_initial_angle + 20
        print(f"\n--- Angle Range: First strand initial angle ±20° ---")
        print(f"    First strand initial angle: {first_initial_angle:.2f}°")
        print(f"    Angle range: {base_angle_min:.2f}° to {base_angle_max:.2f}°")

    # Outer loop: extend first-last pair starting points (0 to 200 px, step 5)
    best_result = None
    best_pair_extension = 0

    # Track best fallback candidate (max-min optimization: maximize the worst gap)
    best_fallback = None
    best_fallback_worst_gap = -float('inf')
    best_fallback_extension = 0
    best_fallback_angle = 0

    for pair_extension in range(0, 210, 10):  # Step 10px instead of 5px
        # Extend first and last strand starting positions
        first_strand["original_start"]["x"] = first_original_start["x"] + pair_extension * first_s23_nx
        first_strand["original_start"]["y"] = first_original_start["y"] + pair_extension * first_s23_ny
        last_strand["original_start"]["x"] = last_original_start["x"] + pair_extension * last_s23_nx
        last_strand["original_start"]["y"] = last_original_start["y"] + pair_extension * last_s23_ny

        # Recalculate the first strand's angle after extension (for auto mode)
        first_dx_ext = first_strand["target_position"]["x"] - first_strand["original_start"]["x"]
        first_dy_ext = first_strand["target_position"]["y"] - first_strand["original_start"]["y"]
        first_angle_ext = math.degrees(math.atan2(first_dy_ext, first_dx_ext))

        # Use custom angles directly, or recalculate based on extension
        if use_custom_v:
            angle_min_deg = base_angle_min
            angle_max_deg = base_angle_max
        else:
            angle_min_deg = first_angle_ext - 10
            angle_max_deg = first_angle_ext + 10

        if pair_extension % 40 == 0:  # Log every 40px
            print(f"\n--- Pair Extension: {pair_extension}px ---")
            print(f"    First strand angle (extended): {first_angle_ext:.2f}°")
            print(f"    Angle range: {angle_min_deg:.2f}° to {angle_max_deg:.2f}°")

        # Search within the angle range
        angle_start = int(angle_min_deg * 100)
        angle_end = int(angle_max_deg * 100)
        step = max(1, int(angle_step_degrees * 100))

        best_gap_variance = float('inf')
        angles_tested = 0
        valid_count = 0
        fail_reasons = {}

        for angle_hundredth in range(angle_start, angle_end + 1, step):
            angle_deg = angle_hundredth / 100.0
            angle_rad = math.radians(angle_deg)
            angles_tested += 1

            result = try_angle_configuration_first_last(
                vertical_strands,
                angle_rad,
                max_extension,
                strand_width,
                verbose=False
            )

            # Call callback for each configuration tried
            if on_config_callback:
                on_config_callback(angle_deg, pair_extension, result, "vertical")

            if result["valid"]:
                valid_count += 1
                gap_variance = result["gap_variance"]

                if gap_variance < best_gap_variance:
                    best_gap_variance = gap_variance
                    best_result = result
                    best_result["angle_degrees"] = angle_deg
                    best_result["pair_extension"] = pair_extension
                    best_pair_extension = pair_extension

                    if gap_variance < 0.01:
                        break
            else:
                # Track failure reason
                reason = result.get("reason", "unknown")
                fail_reasons[reason] = fail_reasons.get(reason, 0) + 1

                # Track fallback: only consider if directions are valid (no crossing)
                fallback = result.get("fallback")
                if fallback and result.get("directions_valid", False):
                    worst_gap = fallback.get("worst_gap", 0)
                    if worst_gap > best_fallback_worst_gap:
                        best_fallback_worst_gap = worst_gap
                        best_fallback = fallback
                        best_fallback_extension = pair_extension
                        best_fallback_angle = angle_deg

        # Log summary for this extension
        if pair_extension % 20 == 0 or valid_count > 0:
            print(f"\n  Extension {pair_extension}px: tested {angles_tested} angles, {valid_count} valid")
            if fail_reasons:
                top_reasons = sorted(fail_reasons.items(), key=lambda x: -x[1])[:3]
                for reason, count in top_reasons:
                    print(f"    - {reason}: {count} times")

        if best_result and best_result.get("pair_extension") == pair_extension:
            print(f"\n  >>> SUCCESS at extension {pair_extension}px, angle {best_result['angle_degrees']:.2f}°")
            print(f"      Gap variance: {best_result['gap_variance']:.4f}, Avg gap: {best_result['average_gap']:.2f}px")
            break  # Found a valid configuration, stop extending

    # Restore original positions (they will be updated by apply_parallel_alignment)
    first_strand["original_start"]["x"] = first_original_start["x"]
    first_strand["original_start"]["y"] = first_original_start["y"]
    last_strand["original_start"]["x"] = last_original_start["x"]
    last_strand["original_start"]["y"] = last_original_start["y"]

    if best_result:
        print(f"\n=== Best Vertical Solution Found ===")
        print(f"Pair extension: {best_pair_extension}px")
        print(f"Angle: {best_result['angle_degrees']:.2f}°")
        print(f"Gap variance: {best_result['gap_variance']:.4f}")
        print(f"Average gap: {best_result['average_gap']:.2f}")

        return {
            "success": True,
            "angle": best_result["angle"],
            "angle_degrees": best_result["angle_degrees"],
            "configurations": best_result["configurations"],
            "average_gap": best_result["average_gap"],
            "gap_variance": best_result["gap_variance"],
            "pair_extension": best_pair_extension,
            "min_gap": best_result.get("min_gap", strand_width),
            "max_gap": best_result.get("max_gap", strand_width * 1.5),
            "message": f"Found vertical parallel configuration at {best_result['angle_degrees']:.2f}° (pair ext: {best_pair_extension}px)"
        }
    elif best_fallback:
        # Return best fallback candidate (max-min: the one with maximum worst gap)
        print(f"\n=== Best Vertical Fallback Candidate (no valid solution) ===")
        print(f"Pair extension: {best_fallback_extension}px")
        print(f"Angle: {best_fallback_angle:.2f}°")
        print(f"Worst gap (min): {best_fallback_worst_gap:.2f}px")
        print(f"Average gap: {best_fallback['average_gap']:.2f}px")
        print(f"All gaps: {[f'{g:.1f}' for g in best_fallback['gaps']]}")

        return {
            "success": False,
            "is_fallback": True,
            "angle": best_fallback["angle"],
            "angle_degrees": best_fallback_angle,
            "configurations": best_fallback["configurations"],
            "average_gap": best_fallback["average_gap"],
            "gap_variance": best_fallback["gap_variance"],
            "worst_gap": best_fallback_worst_gap,
            "gaps": best_fallback["gaps"],
            "pair_extension": best_fallback_extension,
            "min_gap": best_fallback.get("min_gap", strand_width),
            "max_gap": best_fallback.get("max_gap", strand_width * 1.5),
            "message": f"Fallback: best candidate at {best_fallback_angle:.2f}° (worst gap: {best_fallback_worst_gap:.1f}px)"
        }
    else:
        print(f"\n=== No Solution Found ===")
        print(f"Tried pair extensions from 0 to 200px")
        return {
            "success": False,
            "message": "Could not find any valid configuration or fallback (tried pair extensions 0-200px)"
        }


def try_angle_configuration_first_last(strands_list, angle_rad, max_extension, strand_width, verbose=False):
    """
    Try a specific angle using the FIRST-LAST pair approach.

    Algorithm:
    1. FIRST strand projects to target at angle θ (or θ+180° if going left)
    2. LAST strand projects at opposite angle
    3. For 2 strands: search extension combinations to find valid gap
    4. For 3+ strands: MIDDLE strands adapt with extensions
    5. Validate gaps are within [strand_width+10, strand_width*1.5]

    Returns:
        dict with "valid", "configurations", "gaps", "gap_variance", "average_gap"
    """
    min_gap = strand_width + 10     # 56 px for width 46
    max_gap = strand_width * 1.5    # 69 px

    if len(strands_list) < 2:
        return {"valid": False, "reason": "Need at least 2 strands"}

    angle_deg = math.degrees(angle_rad)

    # Helper function to compute strand config for a given extension
    def compute_strand_config(h_strand, extension):
        original_start = h_strand["original_start"]
        target_position = h_strand["target_position"]

        dx_to_target = target_position["x"] - original_start["x"]
        dy_to_target = target_position["y"] - original_start["y"]
        distance_to_target = math.sqrt(dx_to_target**2 + dy_to_target**2)

        if distance_to_target < 0.001:
            return None

        # Determine if strand is predominantly horizontal or vertical
        is_vertical = abs(dy_to_target) > abs(dx_to_target)

        if is_vertical:
            # For vertical strands, check if going down (positive y)
            goes_positive = dy_to_target >= 0
        else:
            # For horizontal strands, check if going right (positive x)
            goes_positive = dx_to_target >= 0

        strand_angle = angle_rad if goes_positive else angle_rad + math.pi
        cos_a = math.cos(strand_angle)
        sin_a = math.sin(strand_angle)

        s2_3 = h_strand["strand_2_3"]
        s2_3_dx = s2_3["end"]["x"] - s2_3["start"]["x"]
        s2_3_dy = s2_3["end"]["y"] - s2_3["start"]["y"]
        s2_3_len = math.sqrt(s2_3_dx**2 + s2_3_dy**2)

        if s2_3_len < 0.001:
            return None

        s2_3_nx = s2_3_dx / s2_3_len
        s2_3_ny = s2_3_dy / s2_3_len

        extended_start_x = original_start["x"] + extension * s2_3_nx
        extended_start_y = original_start["y"] + extension * s2_3_ny

        dx = target_position["x"] - extended_start_x
        dy = target_position["y"] - extended_start_y
        length = dx * cos_a + dy * sin_a

        if length <= 10:
            return None

        end_x = extended_start_x + length * cos_a
        end_y = extended_start_y + length * sin_a

        return {
            "strand": h_strand,
            "extended_start": {"x": extended_start_x, "y": extended_start_y},
            "end": {"x": end_x, "y": end_y},
            "length": length,
            "extension": extension,
            "angle": strand_angle,
            "goes_positive": goes_positive,
        }

    # Special case: exactly 2 strands - search for extension combo with valid gap
    if len(strands_list) == 2:
        first_strand = strands_list[0]
        last_strand = strands_list[1]

        best_config_pair = None
        best_gap_diff = float('inf')  # How close to ideal gap (center of range)
        ideal_gap = (min_gap + max_gap) / 2  # 57.5 px

        # Search extension combinations
        for ext1 in range(0, int(max_extension) + 1, 5):
            config1 = compute_strand_config(first_strand, ext1)
            if not config1:
                continue

            # Precompute line params for config1 (reused for all ext2 iterations)
            line_params1 = precompute_line_params(config1["extended_start"], config1["end"])

            for ext2 in range(0, int(max_extension) + 1, 5):
                config2 = compute_strand_config(last_strand, ext2)
                if not config2:
                    continue

                # Calculate gap using fast precomputed method
                px, py = config2["extended_start"]["x"], config2["extended_start"]["y"]
                gap = fast_perpendicular_distance(line_params1, px, py)
                abs_gap = abs(gap)

                # Check if gap is in valid range
                if min_gap <= abs_gap <= max_gap:
                    gap_diff = abs(abs_gap - ideal_gap)
                    if gap_diff < best_gap_diff:
                        best_gap_diff = gap_diff
                        best_config_pair = (config1, config2, abs_gap, gap)

        if best_config_pair:
            config1, config2, abs_gap, signed_gap = best_config_pair
            return {
                "valid": True,
                "configurations": [config1, config2],
                "gaps": [abs_gap],
                "signed_gaps": [signed_gap],
                "gap_variance": 0,
                "average_gap": abs_gap,
                "worst_gap": abs_gap,
                "angle": angle_rad,
                "min_gap": min_gap,
                "max_gap": max_gap,
            }
        else:
            # No valid gap found - return fallback info
            # Try to find best available gap
            config1 = compute_strand_config(first_strand, 0)
            config2 = compute_strand_config(last_strand, 0)
            if config1 and config2:
                line_params1 = precompute_line_params(config1["extended_start"], config1["end"])
                px, py = config2["extended_start"]["x"], config2["extended_start"]["y"]
                gap = fast_perpendicular_distance(line_params1, px, py)
                abs_gap = abs(gap)
                fallback_data = {
                    "configurations": [config1, config2],
                    "gaps": [abs_gap],
                    "signed_gaps": [gap],
                    "gap_variance": 0,
                    "average_gap": abs_gap,
                    "worst_gap": abs_gap,
                    "angle": angle_rad,
                    "min_gap": min_gap,
                    "max_gap": max_gap,
                }
                if abs_gap < min_gap:
                    return {"valid": False, "reason": f"Gap too small ({abs_gap:.1f} < {min_gap})", "fallback": fallback_data, "directions_valid": True}
                else:
                    return {"valid": False, "reason": f"Gap too large ({abs_gap:.1f} > {max_gap})", "fallback": fallback_data, "directions_valid": True}
            return {"valid": False, "reason": "Could not compute configs for 2-strand case"}

    # For 3+ strands: original logic
    configurations = []

    for idx, h_strand in enumerate(strands_list):
        best_config = None

        for extension in range(0, int(max_extension) + 1, 5):
            config = compute_strand_config(h_strand, extension)
            if config:
                best_config = config
                break

        if not best_config:
            if verbose:
                print(f"    FAILED: {h_strand['strand_4_5']['layer_name']} - no valid length at angle {angle_deg:.2f}°")
            return {"valid": False, "reason": f"Strand {h_strand['strand_4_5']['layer_name']} no valid length"}

        configurations.append(best_config)

    # Calculate gaps between consecutive strands using fast precomputed method
    gaps = []
    signed_gaps = []

    # Precompute all line parameters for speed
    line_params_list = [
        precompute_line_params(cfg["extended_start"], cfg["end"])
        for cfg in configurations
    ]

    for i in range(len(configurations) - 1):
        config2 = configurations[i + 1]
        px, py = config2["extended_start"]["x"], config2["extended_start"]["y"]
        signed_gap = fast_perpendicular_distance(line_params_list[i], px, py)

        # Flip sign for odd-indexed gaps (where LINE strand is _5, which has 180° opposite direction)
        if i % 2 == 1:
            signed_gap = -signed_gap

        signed_gaps.append(signed_gap)
        gaps.append(abs(signed_gap))

    if not gaps:
        return {"valid": True, "configurations": configurations, "gaps": [], "gap_variance": 0, "average_gap": 0, "min_gap": min_gap, "max_gap": max_gap}

    # Calculate statistics for fallback tracking
    gap_sum = sum(gaps)
    average_gap = gap_sum / len(gaps)
    gap_variance = sum((g - average_gap)**2 for g in gaps) / len(gaps)
    worst_gap = min(gaps)  # The smallest gap is the "worst" for max-min optimization

    # Build fallback data (always available even if invalid)
    fallback_data = {
        "configurations": configurations,
        "gaps": gaps,
        "signed_gaps": signed_gaps,
        "gap_variance": gap_variance,
        "average_gap": average_gap,
        "worst_gap": worst_gap,
        "angle": angle_rad,
        "min_gap": min_gap,
        "max_gap": max_gap,
    }

    # Validate gaps
    # 1. Determine expected direction from first-to-last (using first strand's line as reference)
    last_config = configurations[-1]
    px, py = last_config["extended_start"]["x"], last_config["extended_start"]["y"]
    first_to_last_signed = fast_perpendicular_distance(line_params_list[0], px, py)
    expected_sign = 1 if first_to_last_signed >= 0 else -1

    # 2. Check each gap - track if directions are all correct
    directions_valid = True
    for i, sg in enumerate(signed_gaps):
        abs_gap = abs(sg)

        # Check direction (no crossing)
        if expected_sign > 0 and sg <= 0:
            directions_valid = False
            if verbose:
                print(f"    Gap {i} wrong direction: {sg:.2f}")
            return {"valid": False, "reason": f"Gap {i} wrong direction ({sg:.2f})", "fallback": fallback_data, "directions_valid": False}
        elif expected_sign < 0 and sg >= 0:
            directions_valid = False
            if verbose:
                print(f"    Gap {i} wrong direction: {sg:.2f}")
            return {"valid": False, "reason": f"Gap {i} wrong direction ({sg:.2f})", "fallback": fallback_data, "directions_valid": False}

        # Check gap range [strand_width, strand_width*1.5]
        if abs_gap < min_gap:
            if verbose:
                print(f"    Gap {i} too small: {abs_gap:.2f} < {min_gap}")
            return {"valid": False, "reason": f"Gap {i} too small ({abs_gap:.2f} < {min_gap})", "fallback": fallback_data, "directions_valid": directions_valid}

        if abs_gap > max_gap:
            if verbose:
                print(f"    Gap {i} too large: {abs_gap:.2f} > {max_gap}")
            return {"valid": False, "reason": f"Gap {i} too large ({abs_gap:.2f} > {max_gap})", "fallback": fallback_data, "directions_valid": directions_valid}

    return {
        "valid": True,
        "configurations": configurations,
        "gaps": gaps,
        "signed_gaps": signed_gaps,
        "gap_variance": gap_variance,
        "average_gap": average_gap,
        "worst_gap": worst_gap,
        "angle": angle_rad,
        "min_gap": min_gap,
        "max_gap": max_gap,
    }


def try_angle_configuration(horizontal_strands, angle_rad, emoji_area_radius, max_extension, verbose=False, strand_width=46):
    """
    Try a specific angle and check if all strands can be made parallel.

    For parallel strands going in OPPOSITE directions (like _4 going right, _5 going left),
    we use angle for one direction and angle+180° for the opposite direction.
    This ensures they have the same SLOPE (parallel) even though they go opposite ways.

    Gap constraints:
    - All gaps between consecutive strands should be between strand_width+10 and strand_width*1.5
    - Strands should maintain their relative order (not cross)

    For each strand:
    1. Determine its natural direction (left or right based on emoji target)
    2. Use angle or angle+180° based on direction
    3. Check if end point falls within emoji area
    4. Calculate required extension for _2/_3 (if any)

    Returns:
        dict with "valid", "configurations", "gaps", "gap_variance", "average_gap"
    """
    # Gap constraints: strand_width+10 to strand_width * 1.5
    min_gap = strand_width + 10     # 56 px for width 46
    max_gap = strand_width * 1.5    # 69 px for width 46
    configurations = []
    angle_deg = math.degrees(angle_rad)

    for h_strand in horizontal_strands:
        original_start = h_strand["original_start"]
        target_position = h_strand["target_position"]

        # Calculate direction to emoji target
        dx_to_target = target_position["x"] - original_start["x"]
        dy_to_target = target_position["y"] - original_start["y"]
        distance_to_target = math.sqrt(dx_to_target**2 + dy_to_target**2)

        if distance_to_target < 0.001:
            return {"valid": False, "reason": "Target at start"}

        # Determine if strand is predominantly horizontal or vertical
        is_vertical = abs(dy_to_target) > abs(dx_to_target)

        if is_vertical:
            # For vertical strands, check if going down (positive y)
            goes_positive = dy_to_target >= 0
        else:
            # For horizontal strands, check if going right (positive x)
            goes_positive = dx_to_target >= 0

        # For parallel strands: use angle for positive-going, angle+180° for negative-going
        # This ensures same slope (parallel) regardless of direction
        if goes_positive:
            strand_angle = angle_rad
        else:
            strand_angle = angle_rad + math.pi  # Add 180°

        cos_a = math.cos(strand_angle)
        sin_a = math.sin(strand_angle)

        # Try different extensions and lengths to find one that lands in emoji area
        best_length = None
        best_end = None
        best_extension = 0
        best_extended_start = None

        for extension in range(0, int(max_extension) + 1, 2):  # Finer extension steps
            # Extended start point (move along _2/_3 direction)
            s2_3 = h_strand["strand_2_3"]
            s2_3_dx = s2_3["end"]["x"] - s2_3["start"]["x"]
            s2_3_dy = s2_3["end"]["y"] - s2_3["start"]["y"]
            s2_3_len = math.sqrt(s2_3_dx**2 + s2_3_dy**2)

            if s2_3_len < 0.001:
                continue

            # Normalize _2/_3 direction
            s2_3_nx = s2_3_dx / s2_3_len
            s2_3_ny = s2_3_dy / s2_3_len

            # Extended start = original start + extension along _2/_3 direction
            extended_start_x = original_start["x"] + extension * s2_3_nx
            extended_start_y = original_start["y"] + extension * s2_3_ny

            # Try different lengths at the strand's angle
            for length in range(10, 400, 2):  # Finer length steps, longer max
                end_x = extended_start_x + length * cos_a
                end_y = extended_start_y + length * sin_a

                # Check if end is within emoji area
                dist_to_emoji = math.sqrt(
                    (end_x - target_position["x"])**2 +
                    (end_y - target_position["y"])**2
                )

                if dist_to_emoji <= emoji_area_radius:
                    best_length = length
                    best_end = {"x": end_x, "y": end_y}
                    best_extension = extension
                    best_extended_start = {"x": extended_start_x, "y": extended_start_y}
                    break

            if best_length is not None:
                break

        if best_length is None:
            if verbose:
                print(f"    FAILED: {h_strand['strand_4_5']['layer_name']} - Could not reach emoji area")
                print(f"            Start: ({original_start['x']:.1f}, {original_start['y']:.1f})")
                print(f"            Target: ({target_position['x']:.1f}, {target_position['y']:.1f})")
                print(f"            Goes positive: {goes_positive}, Strand angle: {math.degrees(strand_angle):.1f}°")
            return {"valid": False, "reason": f"Strand {h_strand['strand_4_5']['layer_name']} cannot reach emoji area"}

        configurations.append({
            "strand": h_strand,
            "extended_start": best_extended_start,
            "end": best_end,
            "length": best_length,
            "extension": best_extension,
            "angle": strand_angle,
            "goes_positive": goes_positive,
        })

    # Calculate gaps between consecutive parallel strands using SIGNED distance
    # This ensures we can verify strands maintain correct order
    gaps = []
    signed_gaps = []

    for i in range(len(configurations) - 1):
        config1 = configurations[i]
        config2 = configurations[i + 1]

        # Calculate signed perpendicular distance
        signed_gap = calculate_signed_perpendicular_distance(
            config1["extended_start"],
            config1["end"],
            config2["extended_start"]
        )
        signed_gaps.append(signed_gap)
        gaps.append(abs(signed_gap))

    if not gaps:
        return {"valid": True, "configurations": configurations, "gaps": [], "gap_variance": 0, "average_gap": 0}

    # Determine expected direction from first-to-last relationship
    # All gaps should have the same sign (direction)
    if len(configurations) >= 2:
        # Calculate direction from first to last strand
        first_config = configurations[0]
        last_config = configurations[-1]

        first_to_last_signed = calculate_signed_perpendicular_distance(
            first_config["extended_start"],
            first_config["end"],
            last_config["extended_start"]
        )

        # Expected direction: if first_to_last is positive, all gaps should be positive
        # if first_to_last is negative, all gaps should be negative
        expected_sign = 1 if first_to_last_signed >= 0 else -1

        # Validate all gaps:
        # 1. Same direction (same sign)
        # 2. Within valid range: min_gap (strand_width) to max_gap (strand_width*1.5)
        for i, sg in enumerate(signed_gaps):
            abs_gap = abs(sg)

            # Check if gap has correct sign (strands maintain order, don't cross)
            if expected_sign > 0 and sg <= 0:
                if verbose:
                    print(f"    Gap {i} direction mismatch: expected positive, got {sg:.2f} (strands crossing)")
                return {"valid": False, "reason": f"Gap {i} wrong direction - strands crossing ({sg:.2f})"}
            elif expected_sign < 0 and sg >= 0:
                if verbose:
                    print(f"    Gap {i} direction mismatch: expected negative, got {sg:.2f} (strands crossing)")
                return {"valid": False, "reason": f"Gap {i} wrong direction - strands crossing ({sg:.2f})"}

            # Check if gap is within valid range [min_gap, max_gap]
            if abs_gap < min_gap:
                if verbose:
                    print(f"    Gap {i} too small: {abs_gap:.2f} < {min_gap}")
                return {"valid": False, "reason": f"Gap {i} too small ({abs_gap:.2f} < {min_gap})"}

            if abs_gap > max_gap:
                if verbose:
                    print(f"    Gap {i} too large: {abs_gap:.2f} > {max_gap:.2f}")
                return {"valid": False, "reason": f"Gap {i} too large ({abs_gap:.2f} > {max_gap:.2f})"}

    # Calculate variance of gaps (lower = more equal)
    average_gap = sum(gaps) / len(gaps)
    gap_variance = sum((g - average_gap)**2 for g in gaps) / len(gaps)

    return {
        "valid": True,
        "configurations": configurations,
        "gaps": gaps,
        "signed_gaps": signed_gaps,
        "gap_variance": gap_variance,
        "average_gap": average_gap,
        "angle": angle_rad,
        "min_gap": min_gap,
        "max_gap": max_gap,
    }


def calculate_perpendicular_distance(line_start, line_end, point):
    """
    Calculate perpendicular distance from a point to a line defined by two points.

    Uses the formula: |((y2-y1)*px - (x2-x1)*py + x2*y1 - y2*x1)| / sqrt((y2-y1)^2 + (x2-x1)^2)
    """
    x1, y1 = line_start["x"], line_start["y"]
    x2, y2 = line_end["x"], line_end["y"]
    px, py = point["x"], point["y"]

    numerator = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1)
    denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)

    if denominator < 0.001:
        return 0

    return numerator / denominator


def precompute_line_params(line_start, line_end):
    """
    Precompute line parameters for fast repeated distance calculations.

    Returns tuple: (dx, dy, c, inv_length) where:
    - dx, dy: direction vector components
    - c: constant term (x2*y1 - y2*x1)
    - inv_length: 1/line_length (precomputed to avoid repeated sqrt and division)
    """
    x1, y1 = line_start["x"], line_start["y"]
    x2, y2 = line_end["x"], line_end["y"]

    dx = x2 - x1
    dy = y2 - y1
    c = x2 * y1 - y2 * x1

    length_sq = dx * dx + dy * dy
    if length_sq < 0.000001:
        return (dx, dy, c, 0.0)

    inv_length = 1.0 / math.sqrt(length_sq)
    return (dy, -dx, c, inv_length)  # Note: (dy, -dx) for perpendicular


def fast_perpendicular_distance(line_params, px, py):
    """
    Fast perpendicular distance using precomputed line parameters.

    Args:
        line_params: tuple from precompute_line_params()
        px, py: point coordinates (raw floats, not dict)

    Returns:
        Signed perpendicular distance
    """
    a, b, c, inv_length = line_params
    if inv_length == 0.0:
        return 0.0
    return (a * px + b * py + c) * inv_length


def calculate_signed_perpendicular_distance(line_start, line_end, point):
    """
    Calculate SIGNED perpendicular distance from a point to a line.

    Positive = point is on one side of the line
    Negative = point is on the other side

    This helps determine if strands maintain their relative order.

    Note: For multiple calculations to the same line, use precompute_line_params()
    and fast_perpendicular_distance() instead for better performance.
    """
    x1, y1 = line_start["x"], line_start["y"]
    x2, y2 = line_end["x"], line_end["y"]
    px, py = point["x"], point["y"]

    # Cross product gives signed distance
    numerator = (y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1
    denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)

    if denominator < 0.001:
        return 0

    return numerator / denominator


def apply_parallel_alignment(all_strands, alignment_result):
    """
    Apply the parallel alignment result to modify the strands.

    This function:
    1. Updates _4/_5 strand positions (start and end)
    2. Updates _2/_3 strand end positions (if extended)

    Args:
        all_strands: List of all strand dictionaries
        alignment_result: Result from align_horizontal_strands_parallel()

    Returns:
        List of modified strands
    """
    if not alignment_result["success"]:
        print("Cannot apply alignment: no valid configuration found")
        return all_strands

    configurations = alignment_result["configurations"]

    # Build lookup for quick access
    strand_lookup = {s["layer_name"]: s for s in all_strands}

    for config in configurations:
        h_strand = config["strand"]
        strand_4_5 = h_strand["strand_4_5"]
        strand_2_3 = h_strand["strand_2_3"]

        # Update _4/_5 strand
        layer_name_4_5 = strand_4_5["layer_name"]
        if layer_name_4_5 in strand_lookup:
            strand_lookup[layer_name_4_5]["start"] = config["extended_start"].copy()
            strand_lookup[layer_name_4_5]["end"] = config["end"].copy()

            # Update control points
            strand_lookup[layer_name_4_5]["control_points"] = [
                config["extended_start"].copy(),
                config["end"].copy()
            ]
            strand_lookup[layer_name_4_5]["control_point_center"] = {
                "x": (config["extended_start"]["x"] + config["end"]["x"]) / 2,
                "y": (config["extended_start"]["y"] + config["end"]["y"]) / 2,
            }

        # Always update _2/_3 strand end to match _4/_5 start (ensures connection)
        layer_name_2_3 = strand_2_3["layer_name"]
        if layer_name_2_3 in strand_lookup:
            strand_lookup[layer_name_2_3]["end"] = config["extended_start"].copy()

            # Update control points
            if strand_lookup[layer_name_2_3].get("control_points") and len(strand_lookup[layer_name_2_3]["control_points"]) > 1:
                strand_lookup[layer_name_2_3]["control_points"][1] = config["extended_start"].copy()
            strand_lookup[layer_name_2_3]["control_point_center"] = {
                "x": (strand_lookup[layer_name_2_3]["start"]["x"] + config["extended_start"]["x"]) / 2,
                "y": (strand_lookup[layer_name_2_3]["start"]["y"] + config["extended_start"]["y"]) / 2,
            }

    print(f"\nApplied parallel alignment to {len(configurations)} strands")

    return list(strand_lookup.values())


def print_alignment_debug(alignment_result):
    """Print detailed debug information about the alignment result."""
    if not alignment_result["success"]:
        print(f"Alignment failed: {alignment_result['message']}")
        return

    print(f"\n{'='*60}")
    print(f"PARALLEL ALIGNMENT RESULT")
    print(f"{'='*60}")
    print(f"Angle: {alignment_result['angle_degrees']:.2f}° ({alignment_result['angle']:.4f} rad)")
    print(f"Average gap: {alignment_result['average_gap']:.2f} px")
    print(f"Gap variance: {alignment_result['gap_variance']:.4f}")

    # Print gap constraints
    min_gap = alignment_result.get("min_gap", 46)
    max_gap = alignment_result.get("max_gap", 69)
    print(f"Gap constraints: {min_gap:.1f} to {max_gap:.1f} px (strand_width to strand_width*1.5)")

    # Print gaps between strands
    gaps = alignment_result.get("gaps", [])
    signed_gaps = alignment_result.get("signed_gaps", [])
    if gaps:
        print(f"\nGaps between consecutive strands:")
        for i, (gap, sg) in enumerate(zip(gaps, signed_gaps)):
            in_range = "OK" if min_gap <= gap <= max_gap else "OUT OF RANGE"
            print(f"  Gap {i+1}-{i+2}: {gap:.2f} px (signed: {sg:+.2f}) [{in_range}]")

    print(f"\nStrand configurations:")

    for i, config in enumerate(alignment_result["configurations"]):
        h = config["strand"]
        print(f"\n  {i+1}. {h['strand_4_5']['layer_name']} (set {h['set_number']})")
        print(f"     Original start: ({h['original_start']['x']:.1f}, {h['original_start']['y']:.1f})")
        print(f"     Extended start: ({config['extended_start']['x']:.1f}, {config['extended_start']['y']:.1f})")
        print(f"     End:            ({config['end']['x']:.1f}, {config['end']['y']:.1f})")
        print(f"     Extension: {config['extension']:.1f} px")
        print(f"     Length: {config['length']:.1f} px")

    print(f"\n{'='*60}")


