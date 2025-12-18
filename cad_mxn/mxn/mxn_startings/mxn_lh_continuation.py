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


__all__ = [
    "generate_json",
    # Backwards/alternate public entrypoints
    "mxn_lh_continue",
    "mxn_lh_continute",
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

    # Order: vertical strands first (set > n), then horizontal (set <= n)
    # Within each group: by set_number, then _4 before _5
    # Result for 1x2: 3_4, 3_5, 1_4, 1_5, 2_4, 2_5
    all_continuation = strands_4 + strands_5
    all_continuation.sort(key=lambda s: (
        0 if s["set_number"] > n else 1,  # Vertical first (set > n)
        s["set_number"],                   # Then by set number
        s["layer_name"].endswith("_5")     # _4 before _5
    ))
    continuation_strands = all_continuation

    print(f"\nTotal: {len(strands_4)} _4 strands: {[s['layer_name'] for s in strands_4]}")
    print(f"Total: {len(strands_5)} _5 strands: {[s['layer_name'] for s in strands_5]}")
    print(f"Continuation order: {[s['layer_name'] for s in continuation_strands]}")

    # =========================================================================
    # STEP 5: Generate masked strands for _4/_5 crossings
    #
    # The masking pattern depends on k (even/odd):
    # - k even (0, 2, 4...): vertical _4 crosses horizontal _5, vertical _5 crosses horizontal _4
    # - k odd (1, 3, 5...): vertical _4 crosses horizontal _4, vertical _5 crosses horizontal _5
    # =========================================================================
    continuation_masked = []

    # Separate vertical and horizontal continuation strands
    v_strands_4 = [s for s in strands_4 if s["set_number"] > n]  # Vertical sets
    v_strands_5 = [s for s in strands_5 if s["set_number"] > n]
    h_strands_4 = [s for s in strands_4 if s["set_number"] <= n]  # Horizontal sets
    h_strands_5 = [s for s in strands_5 if s["set_number"] <= n]

    print(f"\n=== STEP 5: Generating masked strands ===")
    print(f"v_strands_4: {[s['layer_name'] for s in v_strands_4]}")
    print(f"v_strands_5: {[s['layer_name'] for s in v_strands_5]}")
    print(f"h_strands_4: {[s['layer_name'] for s in h_strands_4]}")
    print(f"h_strands_5: {[s['layer_name'] for s in h_strands_5]}")

    k_is_even = (k % 2 == 0)

    # Masking rule:
    # Base masks pair OPPOSITE suffixes: v_2 x h_3, v_3 x h_2
    # Continuation masks should be the OPPOSITE of base pattern:
    # k even (0, 2, 4...): SAME suffixes (v_4 with h_4, v_5 with h_5) - opposite of base
    # k odd (1, 3, 5...): OPPOSITE suffixes (v_4 with h_5, v_5 with h_4) - same as base
    if k_is_even:
        # k even: same suffixes (OPPOSITE of base _2 x _3 pattern)
        crossing_pairs = [
            (v_strands_4, h_strands_4),  # vertical _4 with horizontal _4
            (v_strands_5, h_strands_5),  # vertical _5 with horizontal _5
        ]
        print(f"k={k} is EVEN: using same suffixes (v_4 with h_4, v_5 with h_5) - opposite of base")
    else:
        # k odd: opposite suffixes (same as base pattern)
        crossing_pairs = [
            (v_strands_4, h_strands_5),  # vertical _4 with horizontal _5
            (v_strands_5, h_strands_4),  # vertical _5 with horizontal _4
        ]
        print(f"k={k} is ODD: using opposite suffixes (v_4 with h_5, v_5 with h_4) - same as base")

    for v_list, h_list in crossing_pairs:
        for v_strand in v_list:
            for h_strand in h_list:
                v_set = v_strand["set_number"]
                h_set = h_strand["set_number"]

                layer_name = f"{v_strand['layer_name']}_{h_strand['layer_name']}"
                set_number = int(f"{v_set}{h_set}") if v_set < 10 and h_set < 10 else v_set * 10 + h_set

                # Create masked strand for vertical crossing horizontal
                masked = create_strand_base(
                    v_strand["start"], v_strand["end"], v_strand["color"],
                    layer_name,
                    set_number,
                    "MaskedStrand"
                )
                masked["first_selected_strand"] = v_strand["layer_name"]
                masked["second_selected_strand"] = h_strand["layer_name"]
                continuation_masked.append(masked)
                print(f"  Created mask: {layer_name} (set_number={set_number})")

    print(f"\nTotal: {len(continuation_masked)} continuation masks")
    print(f"Continuation mask layer names: {[m['layer_name'] for m in continuation_masked]}")

    # Summary comparison of base vs continuation masks
    print(f"\n=== MASK COMPARISON (k={k}) ===")
    print(f"BASE _2/_3 masks (never changes with k):")
    for m in base_masked:
        print(f"  {m['first_selected_strand']} x {m['second_selected_strand']}")
    print(f"CONTINUATION _4/_5 masks (changes with k):")
    for m in continuation_masked:
        print(f"  {m['first_selected_strand']} x {m['second_selected_strand']}")
    print("=" * 50)

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


def main():
    """Test the generator."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "mxn_lh_continuation")
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
            file_name = f"mxn_lh_continuation_{m}x{n}_k{k}_{direction}.json"
            with open(os.path.join(output_dir, file_name), "w") as file:
                file.write(json_content)
            print(f"Generated {file_name}")
        except Exception as e:
            print(f"Error {m}x{n} k={k} {direction}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Running LH Continuation generator...")
    main()
    print("Finished.")
