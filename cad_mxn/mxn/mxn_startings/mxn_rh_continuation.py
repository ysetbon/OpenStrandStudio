"""
MxN RH Continuation Generator

Generates RH stretch patterns with continuation strands (_4, _5).
The continuation is based on emoji pairing logic where:
- _4 start = _2 end (attached to it)
- _4 end = paired position (same emoji on opposite side)
- _5 start = _3 end (attached to it)
- _5 end = paired position (same emoji on opposite side)

RH differs from LH in:
- Negative gap value (-28.0 vs +28.0)
- Vertical strands: _2 is TOP, _3 is BOTTOM (swapped from LH)

Usage:
    from mxn_rh_continuation import generate_json
    json_content = generate_json(m=2, n=2, k=0, direction="cw")
"""

import json
import os
import sys
import random
import colorsys


__all__ = [
    "generate_json",
    # Backwards/alternate public entrypoints
    "mxn_rh_continue",
    "mxn_rh_continute",
]


def mxn_rh_continue(m, n, k=0, direction="cw"):
    """Alias for `generate_json` (RH continuation)."""
    return generate_json(m=m, n=n, k=k, direction=direction)


def mxn_rh_continute(m, n, k=0, direction="cw"):
    """Typo-compatible alias for `mxn_rh_continue`."""
    return mxn_rh_continue(m=m, n=n, k=k, direction=direction)


def generate_json(m, n, k=0, direction="cw"):
    """
    Generate RH stretch pattern WITH continuation (_4, _5 strands).

    Args:
        m: Number of vertical strands
        n: Number of horizontal strands
        k: Emoji rotation value (determines pairing)
        direction: "cw" or "ccw" (rotation direction)

    Returns:
        JSON string with base + continuation strands
    """
    # Constants and parameters (RH STRETCH geometry - negative gap)
    grid_unit = 42.0
    gap = -(grid_unit * (2.0 / 3.0))  # -28.0 (RH is negative)
    stride = 4.0 * abs(gap)  # 112.0
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
    # STEP 1: Generate base strands (_1, _2, _3) - RH pattern
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

        # RH vertical tails (SWAPPED from LH):
        # _2 is the TOP tail (attached at End), extends downward
        att_2_end = {"x": end_pt["x"], "y": start_pt["y"] + tail_offset}
        strand_2_2 = create_strand_base(
            end_pt, att_2_end, color, f"{v_set_num}_2", v_set_num,
            "AttachedStrand", main_layer, 1,
        )
        strands_2.append(strand_2_2)

        # _3 is the BOTTOM tail (attached at Start), extends upward
        att_3_end = {"x": start_pt["x"], "y": end_pt["y"] - tail_offset}
        strand_2_3 = create_strand_base(
            start_pt, att_3_end, color, f"{v_set_num}_3", v_set_num,
            "AttachedStrand", main_layer, 0,
        )
        strands_3.append(strand_2_3)

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

        # Attached Strand (_2) - Right (End), extends left
        att_2_end = {"x": start_pt["x"] - tail_offset, "y": end_pt["y"]}
        strand_1_2 = create_strand_base(
            end_pt, att_2_end, color, f"{h_set_num}_2", h_set_num,
            "AttachedStrand", main_layer, 1,
        )
        strands_2.append(strand_1_2)

        # Attached Strand (_3) - Left (Start), extends right
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

    print(f"\n=== STEP 2: Generating _2 x _3 base masks (RH) ===")
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

    print(f"\n=== STEP 4: Generating _4 and _5 strands (RH) ===")
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

    print(f"\n=== STEP 6: Final strand counts (RH) ===")
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
    print(f"\n=== Emoji Pairing Debug RH (k={k}, {direction}) ===")
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

    shift = k % n
    if shift < 0:
        shift += n

    if direction == "ccw":
        shift = (n - shift) % n

    out = [None] * n
    for i in range(n):
        out[(i + shift) % n] = labels[i]

    return out


def get_starting_order(m, n):
    """
    RH version: starting by top LEFT side and going CLOCKWISE. Top side + right side + bottom side + left side.
    This is the OPPOSITE of LH's get_starting_order.
    """
    top = [f"{i}_3" for i in range(n + 1, n + m + 1)]
    right = [f"{i}_3" for i in range(1, n + 1)]
    bottom = [f"{i}_2" for i in reversed(range(n + 1, n + m + 1))]
    left = [f"{i}_2" for i in reversed(range(1, n + 1))]
    return top + right + bottom + left


def get_starting_order_oposite_orientation(m, n):
    """
    RH version: starting by top RIGHT side and going COUNTERCLOCKWISE. Top side + left side + bottom side + right side.
    This is the OPPOSITE of LH's get_starting_order_oposite_orientation.
    """
    top = [f"{i}_3" for i in reversed(range(n + 1, n + m + 1))]
    left = [f"{i}_2" for i in range(1, n + 1)]
    bottom = [f"{i}_2" for i in range(n + 1, n + m + 1)]
    right = [f"{i}_3" for i in reversed(range(1, n + 1))]
    return top + left + bottom + right


def get_horizontal_order_k(m, n, k, direction):
    f"""
    This code works properly!
    if k is even - full order is top + right + bottom + left of get_starting_order. horizontal order when k = 0 we have pointer 1 to be pointing at first element of right side (1_3), pointer 2 pointing at last element of left side (1_2), pointer 3 pointing at second element of right side (2_3), pointer 4 pointing at second element of one before last left side (2_2), etc. if k is even we shift the pointers to the right or left by k-1 positions (shifting to the left if k is positive, shifting to the right if k is negative) of the array of the total get_starting_order.

    if k is odd - full order is top + left + bottom + right of get_starting_order_oposite_orientation. horizontal order when k = 1 we have pointer 1 to be pointing at last element of left side (1_2), pointer 2 pointing at first element of right side (1_3), pointer 3 pointing at second element of left side (2_2), pointer 4 pointing at second element of one before last right side (2_3), etc. if k is odd and not 1 we shift the pointers base on the pointer of k = 1 and shifter by k - 2 positions of the array of the total get_starting_order_oposite_orientation.

    if k is negative, it is equals to 4*(m+n) + k.

    example for 2x2 with k = 0 ccw, total order is (top:[3_3, 4_3] right:[1_3, 2_3] bottom:[4_2, 3_2] left:[2_2, 1_2]) ["3_3", "4_3", "1_3", "2_3", "4_2", "3_2", "2_2", "1_2"]
    so pointers: 1->1_3, 2->1_2, 3->2_3, 4->2_2, horizontal order is 1_3 1_2 2_3 2_2.

    example for 2x2 with k = 1 ccw, get_starting_order_oposite_orientation (top: [4_3, 3_3] left[1_2, 2_2] bottom[3_2, 4_2] right[2_3, 1_3]) ["4_3", "3_3", "1_2", "2_2", "3_2", "4_2", "2_3", "1_3"] so pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3, horizontal order is 1_2 1_3 2_2 2_3.

    example for 2x2 with k = 2 ccw, initial pointers: 1->1_3, 2->1_2, 3->2_3, 4->2_2 (for k = 0) , and the total order is (top:["3_3", "4_3"] right: ["1_3", "2_3"] bottom: ["4_2", "3_2"] left: ["2_2", "1_2"]) ["3_3", "4_3", "1_3", "2_3", "4_2", "3_2", "2_2", "1_2"], we shift the pointers by k - 1 = 1 positions, so the new pointers are (shifting to the left by 1 position): 1->4_3, 2->2_2, 3->1_3, 4->3_2, horizontal order is 4_3 2_2 1_3 3_2.

    example for 2x2 with k = 3 ccw, initial pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3 (for k = 1) , and the get_starting_order_oposite_orientation (top: [4_3, 3_3] left[1_2, 2_2] bottom[3_2, 4_2] right[2_3, 1_3]) ["4_3", "3_3", "1_2", "2_2", "3_2", "4_2", "2_3", "1_3"], we shift the pointers by k - 2 = 1 positions, so the new pointers are (shifting to the right by 1 positions): 1->2_2, 2->4_3, 3->3_2, 4->1_3, horizontal order is 2_2 4_3 3_2 1_3.

    example for 2x2 with k = -1 ccw, its eqals 4*(m+n) + k = 4*(2+2) - (-1) = 17, initial pointers: 1->1_2, 2->1_3, 3->2_2, 4->2_3 (for k = 1) , and the get_starting_order_oposite_orientation (top: [4_3, 3_3] left[1_2, 2_2] bottom[3_2, 4_2] right[2_3, 1_3]) ["4_3", "3_3", "1_2", "2_2", "3_2", "4_2", "2_3", "1_3"], we shift the pointers by k-2 =17-2 positions, so the new pointers are (shifting to the right by 15 positions): 1->3_3, 2->2_3, 3->1_2, 4->4_2, horizontal order is 3_3 2_3 1_2 4_2.

    When direction is ccw, just change the k value to -k.
    """

    if direction == "cw":
        k = -k

    total_len = 2 * (m + n)
    full_order = get_starting_order(m, n)
    full_order_oposite_orientation = get_starting_order_oposite_orientation(m, n)
    # RH is opposite of LH, so k=0 pointers start with _3 (swapped from LH)
    # k=0 pointers for horizontal order pointer = ["1_3", "1_2", "2_3", "2_2", ...]
    pointer_k0 = []
    for i in range(n):
        pointer_k0.append(f"{i+1}_3")
        pointer_k0.append(f"{i+1}_2")
    # k=1 pointers for horizontal order pointer = ["1_2", "1_3", "2_2", "2_3", ...]
    pointer_k1 = []
    for i in range(n):
        pointer_k1.append(f"{i+1}_2")
        pointer_k1.append(f"{i+1}_3")
    if k == 0:
        return pointer_k0
    elif k == 1:
        return pointer_k1
    if k < 0:
        k = 4*(m+n) - k
    
    if k % 2 == 0:
        pointer_k = pointer_k0
        for i in range(len(pointer_k)):
            #search the strand in the full_order
            for strand in full_order:
                #find the strand in pointer_k[i]
                if pointer_k[i] == strand:
                    #get the shift position of the strand in the full_order
                    shift_position = full_order.index(strand)
                    #shift to the left by k-1 positions
                    pointer_k[i] = full_order[(shift_position - k + 1) % total_len]
                    break
    else:
        pointer_k = pointer_k1
        for i in range(len(pointer_k)):
            #search the strand in the full_order
            for strand in full_order_oposite_orientation:
                #find the strand in pointer_k[i]
                if pointer_k[i] == strand:
                    #get the shift position of the strand in the full_order
                    shift_position = full_order_oposite_orientation.index(strand)
                    #shift to the right by k-2 positions
                    pointer_k[i] = full_order_oposite_orientation[(shift_position + k - 2) % total_len]
                    break
    return pointer_k



def get_vertical_order_k(m, n, k, direction):
    """
    Get the *vertical* endpoint order for an m×n continuation, at rotation `k` and `direction`.

    This is the RH analogue of `mxn_lh_continuation.get_vertical_order_k`, following the
    exact same conventions already used by RH `get_horizontal_order_k`:

    - **Direction handling**: RH flips `k` when `direction == "cw"` (so the examples below
      are written for **ccw**, matching `get_horizontal_order_k` in this file).
    - **Negative k**: if `k < 0`, it is normalized using `k = 4*(m+n) - k` (same as RH horizontal).
    - **Parity**:
      - even `k`: base pointers come from the `k=0` pattern and are shifted in
        `get_starting_order(m, n)` by `-(k-1)` (left by `k-1`).
      - odd `k`: base pointers come from the `k=1` pattern and are shifted in
        `get_starting_order_oposite_orientation(m, n)` by `+(k-2)` (right by `k-2`).

    The returned list has length `2*m` and contains labels like `"3_2"` / `"3_3"`.

    CCW examples for **m=2, n=2** (vertical sets are 3 and 4):

    - k = 0 (ccw)  -> ["3_3", "3_2", "4_3", "4_2"]
    - k = 1 (ccw)  -> ["3_2", "3_3", "4_2", "4_3"]
    - k = 2 (ccw)  -> ["1_2", "4_2", "3_3", "2_3"]
    - k = 3 (ccw)  -> ["4_2", "1_2", "2_3", "3_3"]
    - k = -1 (ccw) -> ["2_2", "4_3", "3_2", "1_3"]
    """

    # Match RH horizontal convention: flip k for "cw"
    if direction == "cw":
        k = -k

    total_len = 2 * (m + n)
    full_order = get_starting_order(m, n)
    full_order_oposite_orientation = get_starting_order_oposite_orientation(m, n)

    # RH is opposite of LH, so the base pointers swap the _2/_3 ordering vs LH.
    # k=0 pointers for vertical order: ["(n+1)_3", "(n+1)_2", "(n+2)_3", "(n+2)_2", ...]
    pointer_k0 = []
    for i in range(m):
        pointer_k0.append(f"{n+1+i}_3")
        pointer_k0.append(f"{n+1+i}_2")

    # k=1 pointers for vertical order: ["(n+1)_2", "(n+1)_3", "(n+2)_2", "(n+2)_3", ...]
    pointer_k1 = []
    for i in range(m):
        pointer_k1.append(f"{n+1+i}_2")
        pointer_k1.append(f"{n+1+i}_3")

    if k == 0:
        return pointer_k0
    if k == 1:
        return pointer_k1

    if k < 0:
        k = 4 * (m + n) - k

    # Precompute indices for O(1) shifts
    full_index = {s: idx for idx, s in enumerate(full_order)}
    opp_index = {s: idx for idx, s in enumerate(full_order_oposite_orientation)}

    if k % 2 == 0:
        # Shift left by (k-1) in the full RH starting order
        out = list(pointer_k0)
        for i, label in enumerate(out):
            shift_position = full_index[label]
            out[i] = full_order[(shift_position - k + 1) % total_len]
        return out

    # Odd k: shift right by (k-2) in the opposite-orientation perimeter
    out = list(pointer_k1)
    for i, label in enumerate(out):
        shift_position = opp_index[label]
        out[i] = full_order_oposite_orientation[(shift_position + k - 2) % total_len]
    return out

def get_mask_order_k(m, n, k, direction):
    """
    From get_horizontal_order_k and get_vertical_order_k, get the mask order for a given k and direction.

    For even values of k, we pair odd indexes of get_vertical_order_k with even indexes of get_horizontal_order_k, and vice versa.

    For odd values of k, we pair odd indexes of get_vertical_order_k with odd indexes of get_horizontal_order_k, and vice versa.
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

    print(f"\n=== Computing _4/_5 masks (RH) ===")
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


def main():
    """Test the generator."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "mxn_rh_continuation")
    os.makedirs(output_dir, exist_ok=True)

    # Test cases
    test_cases = [
        (1, 2, 0, "cw"),
        (1, 2, 1, "cw"),
        (2, 2, 0, "cw"),
        (2, 2, 1, "ccw"),
    ]

    for m, n, k, direction in test_cases:
        try:
            json_content = generate_json(m, n, k, direction)
            file_name = f"mxn_rh_continuation_{m}x{n}_k{k}_{direction}.json"
            with open(os.path.join(output_dir, file_name), "w") as file:
                file.write(json_content)
            print(f"Generated {file_name}")
        except Exception as e:
            print(f"Error {m}x{n} k={k} {direction}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Running RH Continuation generator...")
    main()
    print("Finished.")
