"""
MxN Emoji Renderer Module

This module handles all emoji-related functionality for the MxN CAD Generator.
It provides endpoint labeling with animal emojis that can be rotated around
the perimeter of the strand pattern for easy identification of strand pairs.

The emoji system works by:
1. Assigning a unique animal emoji to each strand (based on layer name)
2. Drawing the same emoji at both endpoints of each strand
3. Allowing rotation (CW/CCW) of all labels around the perimeter
4. This helps users identify which endpoints belong to the same strand

Usage:
    from mxn_emoji_renderer import EmojiRenderer

    renderer = EmojiRenderer()
    renderer.draw_endpoint_emojis(painter, canvas, bounds, m, n, settings)
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPen, QBrush, QPainterPath


class EmojiRenderer:
    """
    Handles rendering of emoji markers at strand endpoints.

    The renderer assigns animal emojis to strands and draws them at their
    endpoints. Labels can be rotated around the perimeter to help identify
    strand pairs in different configurations.

    Attributes:
        BOUNDS_PADDING: Padding around the content area for emoji placement
        _emoji_base_labels: Cached list of base emoji labels for current grid
        _emoji_base_key: Cache key (m, n, strand_ids) to detect when regeneration is needed
    """

    BOUNDS_PADDING = 100

    def __init__(self):
        """Initialize the emoji renderer with empty cache."""
        # Cache for stable emoji assignments across re-renders
        # This ensures the same strands get the same emojis until grid size changes
        self._emoji_base_labels = None
        self._emoji_base_key = None

    def clear_cache(self):
        """
        Clear the cached emoji labels.

        Call this when the grid size changes or when you want to
        regenerate the emoji assignments from scratch.
        """
        self._emoji_base_labels = None
        self._emoji_base_key = None

    def get_animal_pool(self):
        """
        Get the pool of animal emojis used for endpoint markers.

        Returns:
            list: A list of 50 animal emoji characters. If there are more
                  strands than emojis, numeric suffixes will be added
                  (e.g., "dog2", "dog3") to ensure uniqueness.

        The emojis are chosen to be visually distinct and commonly
        supported across platforms (Windows, macOS, Linux).
        """
        return [
            # Common pets and farm animals
            "\U0001F436", "\U0001F431", "\U0001F42D", "\U0001F439", "\U0001F430",  # dog, cat, mouse, hamster, rabbit
            # Wild animals
            "\U0001F98A", "\U0001F43B", "\U0001F43C", "\U0001F428", "\U0001F42F",  # fox, bear, panda, koala, tiger
            "\U0001F981", "\U0001F42E", "\U0001F437", "\U0001F438", "\U0001F435",  # lion, cow, pig, frog, monkey
            # Birds
            "\U0001F414", "\U0001F427", "\U0001F426", "\U0001F424", "\U0001F986",  # chicken, penguin, bird, chick, duck
            "\U0001F989", "\U0001F987", "\U0001F43A", "\U0001F417", "\U0001F434",  # owl, bat, wolf, boar, horse
            # Magical and insects
            "\U0001F984", "\U0001F41D", "\U0001F41B", "\U0001F98B", "\U0001F40C",  # unicorn, bee, bug, butterfly, snail
            "\U0001F41E", "\U0001F422", "\U0001F40D", "\U0001F98E", "\U0001F996",  # ladybug, turtle, snake, lizard, t-rex
            # Prehistoric and sea creatures
            "\U0001F995", "\U0001F419", "\U0001F991", "\U0001F990", "\U0001F99E",  # sauropod, octopus, squid, shrimp, lobster
            "\U0001F980", "\U0001F421", "\U0001F420", "\U0001F41F", "\U0001F42C",  # crab, blowfish, tropical fish, fish, dolphin
            # More animals
            "\U0001F433", "\U0001F40A", "\U0001F993", "\U0001F992", "\U0001F9AC"   # whale, crocodile, zebra, giraffe, bison
        ]

    def make_labels(self, count, base=None):
        """
        Create a list of unique emoji labels for the given count.

        Args:
            count: Number of unique labels needed (typically number of strands)
            base: Optional custom list of base emojis. If None, uses animal_pool.

        Returns:
            list: A list of `count` unique label strings. If count exceeds
                  the base pool size, labels will have numeric suffixes
                  (e.g., ["dog", "cat", ..., "dog2", "cat2", ...])

        Example:
            >>> renderer = EmojiRenderer()
            >>> labels = renderer.make_labels(3)
            >>> print(labels)  # ["dog", "cat", "mouse"]
            >>> labels = renderer.make_labels(55)  # More than pool size
            >>> print(labels[50])  # "dog2" (wraps around with suffix)
        """
        if base is None:
            base = self.get_animal_pool()

        labels = []
        if count <= 0:
            return labels

        base_len = max(1, len(base))

        for i in range(count):
            # Get the base emoji (cycles through the pool)
            emoji = base[i % base_len]
            # Calculate which "round" we're on (for suffix)
            k = i // base_len
            # First round: no suffix. Subsequent rounds: add number suffix
            labels.append(emoji if k == 0 else f"{emoji}{k + 1}")

        return labels

    def rotate_labels(self, labels, k, direction):
        """
        Rotate labels by k positions around the perimeter.

        This function shifts all labels in the list, simulating rotation
        around the strand pattern's perimeter. This helps users identify
        strand pairs when the pattern is viewed from different angles.

        Args:
            labels: List of emoji labels to rotate
            k: Number of positions to rotate (can be negative)
            direction: "cw" for clockwise, "ccw" for counter-clockwise

        Returns:
            list: A new list with labels rotated by k positions

        How it works:
            - CW rotation: labels shift "forward" around the perimeter
            - CCW rotation: labels shift "backward" around the perimeter
            - The visual effect is that all endpoint labels rotate together,
              maintaining their relative positions to each other

        Example:
            >>> labels = ["A", "B", "C", "D"]
            >>> rotate_labels(labels, 1, "cw")   # ["D", "A", "B", "C"]
            >>> rotate_labels(labels, 1, "ccw")  # ["B", "C", "D", "A"]
        """
        n = len(labels)
        if n == 0:
            return labels

        # Normalize shift to be within [0, n)
        shift = k % n
        if shift < 0:
            shift += n

        # CCW is the opposite direction of CW
        if direction == "ccw":
            shift = (n - shift) % n

        # Create rotated output: each label moves to position (i + shift) % n
        out = [None] * n
        for i in range(n):
            out[(i + shift) % n] = labels[i]

        return out

    def compute_slots_from_rect(self, rect, m, n):
        """
        Compute endpoint slot positions using a rectangular grid layout.

        This is a fallback method when actual strand endpoints can't be
        determined. It creates evenly-spaced slot positions around the
        rectangle's perimeter.

        Args:
            rect: QRectF defining the content area
            m: Number of vertical strands (columns)
            n: Number of horizontal strands (rows)

        Returns:
            list: Slot dictionaries with position and normal vector info:
                  {
                      "id": int,           # Unique slot index
                      "side": str,         # "top", "right", "bottom", or "left"
                      "side_index": int,   # Index along that side
                      "x": float,          # X coordinate
                      "y": float,          # Y coordinate
                      "nx": float,         # Normal X (outward direction)
                      "ny": float          # Normal Y (outward direction)
                  }

        Perimeter order (clockwise from top-left):
            1. Top edge: left to right (m slots for vertical strands)
            2. Right edge: top to bottom (n slots for horizontal strands)
            3. Bottom edge: right to left (m slots, reversed)
            4. Left edge: bottom to top (n slots, reversed)
        """
        if m < 1 or n < 1:
            return []

        # Build side lists in geometric order:
        # - top/bottom: vertical strand endpoints (index i = 0..m-1)
        # - left/right: horizontal strand endpoints (index j = 0..n-1)
        top_slots = []
        right_slots = []
        bottom_slots = []
        left_slots = []

        # Vertical strands have endpoints on top and bottom
        for i in range(m):
            x = rect.left() + (i + 0.5) * (rect.width() / m)
            top_slots.append({
                "side": "top",
                "side_index": i,
                "x": x,
                "y": rect.top(),
                "nx": 0.0,   # Normal points up (out of content)
                "ny": -1.0
            })
            bottom_slots.append({
                "side": "bottom",
                "side_index": i,
                "x": x,
                "y": rect.bottom(),
                "nx": 0.0,   # Normal points down (out of content)
                "ny": 1.0
            })

        # Horizontal strands have endpoints on left and right
        for j in range(n):
            y = rect.top() + (j + 0.5) * (rect.height() / n)
            right_slots.append({
                "side": "right",
                "side_index": j,
                "x": rect.right(),
                "y": y,
                "nx": 1.0,   # Normal points right (out of content)
                "ny": 0.0
            })
            left_slots.append({
                "side": "left",
                "side_index": j,
                "x": rect.left(),
                "y": y,
                "nx": -1.0,  # Normal points left (out of content)
                "ny": 0.0
            })

        # Combine in clockwise perimeter order (starting at top-left corner):
        # top (L->R), right (T->B), bottom (R->L = reversed), left (B->T = reversed)
        slots = top_slots + right_slots + list(reversed(bottom_slots)) + list(reversed(left_slots))

        # Assign unique IDs based on perimeter position
        for idx, s in enumerate(slots):
            s["id"] = idx

        return slots

    def compute_slots_from_strands(self, canvas, bounds, m, n):
        """
        Compute endpoint slots from actual strand positions.

        This method analyzes the canvas strands to find their actual
        endpoint positions, then organizes them into perimeter order.
        Falls back to rectangular distribution if strand data is incomplete.

        Args:
            canvas: The canvas object containing strand data
            bounds: QRectF of the rendered area (including padding)
            m: Number of vertical strands
            n: Number of horizontal strands

        Returns:
            list: Slot dictionaries (same format as compute_slots_from_rect)

        Algorithm:
            1. Calculate content area (bounds minus padding)
            2. Collect all strand endpoints from canvas
            3. Classify each endpoint by which edge it's nearest to
            4. Verify we have the expected number on each edge
            5. If valid, sort and return in perimeter order
            6. If invalid, fall back to rectangular layout
        """
        padding = self.BOUNDS_PADDING
        content = QRectF(
            bounds.x() + padding,
            bounds.y() + padding,
            max(1.0, bounds.width() - 2 * padding),
            max(1.0, bounds.height() - 2 * padding)
        )

        # Collect all endpoints from strands
        endpoints = []
        for strand in getattr(canvas, "strands", []) or []:
            if hasattr(strand, "start") and strand.start:
                endpoints.append(strand.start)
            if hasattr(strand, "end") and strand.end:
                endpoints.append(strand.end)

        # Tolerance for edge detection (points within this distance
        # of an edge are considered on that edge)
        tol = 8.0

        # Classify points by edge
        top_pts, right_pts, bottom_pts, left_pts = [], [], [], []
        for p in endpoints:
            x = float(p.x())
            y = float(p.y())

            if abs(y - content.top()) <= tol:
                top_pts.append((x, y))
            elif abs(x - content.right()) <= tol:
                right_pts.append((x, y))
            elif abs(y - content.bottom()) <= tol:
                bottom_pts.append((x, y))
            elif abs(x - content.left()) <= tol:
                left_pts.append((x, y))

        # Validate: we expect m points on top/bottom, n on left/right
        expected_valid = (
            len(top_pts) == m and
            len(bottom_pts) == m and
            len(left_pts) == n and
            len(right_pts) == n
        )

        if not expected_valid:
            # Fall back to rectangular distribution
            return self.compute_slots_from_rect(content, m, n)

        # Sort endpoints in geometric order (not perimeter order yet):
        # - top/bottom: left to right (x coordinate)
        # - left/right: top to bottom (y coordinate)
        top_sorted = sorted(top_pts, key=lambda t: t[0])
        right_sorted = sorted(right_pts, key=lambda t: t[1])
        bottom_sorted = sorted(bottom_pts, key=lambda t: t[0])
        left_sorted = sorted(left_pts, key=lambda t: t[1])

        # Create slot dictionaries with normal vectors
        top_slots = [
            {"side": "top", "side_index": i, "x": x, "y": y, "nx": 0.0, "ny": -1.0}
            for i, (x, y) in enumerate(top_sorted)
        ]
        right_slots = [
            {"side": "right", "side_index": j, "x": x, "y": y, "nx": 1.0, "ny": 0.0}
            for j, (x, y) in enumerate(right_sorted)
        ]
        bottom_slots = [
            {"side": "bottom", "side_index": i, "x": x, "y": y, "nx": 0.0, "ny": 1.0}
            for i, (x, y) in enumerate(bottom_sorted)
        ]
        left_slots = [
            {"side": "left", "side_index": j, "x": x, "y": y, "nx": -1.0, "ny": 0.0}
            for j, (x, y) in enumerate(left_sorted)
        ]

        # Combine in clockwise perimeter order
        slots = top_slots + right_slots + list(reversed(bottom_slots)) + list(reversed(left_slots))

        for idx, s in enumerate(slots):
            s["id"] = idx

        return slots

    def draw_endpoint_emojis(self, painter, canvas, bounds, m, n, settings):
        """
        Draw rotated animal emoji labels near each strand endpoint.

        This is the main entry point for emoji rendering. It:
        1. Identifies which strands should be labeled (skips "_1" suffix strands)
        2. Assigns emojis to *perimeter endpoint slots* in clockwise order
        3. Applies rotation based on user settings
        4. Draws emojis at calculated positions outside the strand endpoints

        Args:
            painter: QPainter to draw with (already positioned for content)
            canvas: Canvas object containing strand data
            bounds: QRectF of the full rendered area
            m: Number of vertical strands
            n: Number of horizontal strands
            settings: Dict with emoji settings:
                {
                    "show": bool,       # Whether to show emojis at all
                    "k": int,           # Rotation amount
                    "direction": str    # "cw" or "ccw"
                }

        Label Assignment Logic:
            - Only strands with "_2" or "_3" suffix are labeled (skip "_1")
            - Each unique perimeter endpoint position gets its own emoji
            - Emojis are assigned based on clockwise perimeter order of endpoints

        Drawing Details:
            - Emojis are drawn with a shadow for visibility
            - Position is offset outward from the strand endpoint
            - Offset distance accounts for strand width and font size
        """
        # Check if emojis should be shown
        if not settings.get("show", True):
            return

        padding = self.BOUNDS_PADDING
        content = QRectF(
            bounds.x() + padding,
            bounds.y() + padding,
            max(1.0, bounds.width() - 2 * padding),
            max(1.0, bounds.height() - 2 * padding)
        )

        # Helper: Calculate perimeter position (scalar) for sorting
        # This maps any point to its clockwise distance from top-left corner
        def perimeter_t(side, x, y):
            """
            Convert a point to a scalar perimeter position.

            The perimeter is measured clockwise from the top-left corner:
            - Top edge: 0 to width
            - Right edge: width to (width + height)
            - Bottom edge: (width + height) to (2*width + height)
            - Left edge: (2*width + height) to (2*width + 2*height)
            """
            w = content.width()
            h = content.height()

            if side == "top":
                return (x - content.left())
            if side == "right":
                return w + (y - content.top())
            if side == "bottom":
                return w + h + (content.right() - x)
            # left
            return 2 * w + h + (content.bottom() - y)

        # Collect unique endpoint positions from eligible strands.
        #
        # IMPORTANT:
        # We label *endpoints* (slots) around the perimeter, NOT whole strands.
        # This is required so that `_2 start` and `_2 end` (and `_3`) can have
        # different emojis, and so that rotation `k` shifts the perimeter
        # assignment as users expect.
        strands = getattr(canvas, "strands", []) or []

        q = 0.5  # Snap tolerance in pixels for endpoint identity

        def ep_key(ep):
            """Generate a unique key for an endpoint based on its position."""
            return (
                ep.get("side", ""),
                int(round(float(ep["x"]) / q)),
                int(round(float(ep["y"]) / q)),
            )

        endpoint_map = {}  # key -> {"ep": ep, "t": float, "width": float}

        for si, strand in enumerate(strands):
            # Skip strands without valid endpoints
            if not (hasattr(strand, "start") and hasattr(strand, "end") and strand.start and strand.end):
                continue

            # Filter by layer name: only label "_2" and "_3" strands
            # This skips the middle "_1" strands which don't have perimeter endpoints
            layer_name = getattr(strand, "layer_name", "") or ""
            strand_name = getattr(strand, "name", "") or ""
            # Some projects store the suffix on `name` rather than `layer_name`
            suffix_source = layer_name or strand_name or ""

            if suffix_source:
                if suffix_source.endswith("_1"):
                    continue  # Skip middle strands
                if not (suffix_source.endswith("_2") or suffix_source.endswith("_3")):
                    continue  # Only process _2 and _3 strands
            else:
                # Fallback for strands without layer_name
                try:
                    set_num = int(getattr(strand, "set_number", -1))
                except Exception:
                    set_num = -1
                if set_num not in (2, 3):
                    continue

            # Get endpoint coordinates
            x1, y1 = float(strand.start.x()), float(strand.start.y())
            x2, y2 = float(strand.end.x()), float(strand.end.y())

            dx = x2 - x1
            dy = y2 - y1

            # Determine which sides the endpoints are on based on strand direction
            if abs(dx) >= abs(dy):
                # Horizontal strand: endpoints on left/right
                if x1 <= x2:
                    ep_a = {"x": x1, "y": y1, "side": "left", "nx": -1.0, "ny": 0.0}
                    ep_b = {"x": x2, "y": y2, "side": "right", "nx": 1.0, "ny": 0.0}
                else:
                    ep_a = {"x": x2, "y": y2, "side": "left", "nx": -1.0, "ny": 0.0}
                    ep_b = {"x": x1, "y": y1, "side": "right", "nx": 1.0, "ny": 0.0}
            else:
                # Vertical strand: endpoints on top/bottom
                if y1 <= y2:
                    ep_a = {"x": x1, "y": y1, "side": "top", "nx": 0.0, "ny": -1.0}
                    ep_b = {"x": x2, "y": y2, "side": "bottom", "nx": 0.0, "ny": 1.0}
                else:
                    ep_a = {"x": x2, "y": y2, "side": "top", "nx": 0.0, "ny": -1.0}
                    ep_b = {"x": x1, "y": y1, "side": "bottom", "nx": 0.0, "ny": 1.0}

            strand_width = float(getattr(strand, "width", getattr(canvas, "strand_width", 46)))

            for ep in (ep_a, ep_b):
                key = ep_key(ep)
                t = perimeter_t(ep["side"], ep["x"], ep["y"])
                if key not in endpoint_map:
                    endpoint_map[key] = {"ep": ep, "t": float(t), "width": strand_width}
                else:
                    # Use the widest strand width for outward offset calculation.
                    endpoint_map[key]["width"] = max(endpoint_map[key]["width"], strand_width)

        if not endpoint_map:
            return

        # Sort endpoints by perimeter position (clockwise from top-left).
        # Tie-break with the snapped key to make ordering deterministic.
        ordered_eps = sorted(
            endpoint_map.items(),
            key=lambda kv: (kv[1]["t"], str(kv[0]))
        )
        ordered_keys = [k for k, _ in ordered_eps]

        def build_mirrored_base_labels():
            """
            Build the *k=0* base labels so opposite sides mirror each other.

            Desired behavior (clockwise perimeter order):
              - top:    unique sequence
              - right:  unique sequence
              - bottom: reverse(top)
              - left:   reverse(right)

            This ensures we do NOT end up with a different emoji for every slot.
            """
            total = len(ordered_eps)
            if total == 0:
                return []

            # Indices per side in clockwise order (already sorted by perimeter_t)
            side_to_indices = {"top": [], "right": [], "bottom": [], "left": []}
            for idx, (_key, item) in enumerate(ordered_eps):
                side = (item.get("ep") or {}).get("side", "")
                if side in side_to_indices:
                    side_to_indices[side].append(idx)
                else:
                    # Unexpected side value; treat it as unique/unmirrored.
                    side_to_indices.setdefault(side, []).append(idx)

            top_idx = side_to_indices.get("top", [])
            right_idx = side_to_indices.get("right", [])
            bottom_idx = side_to_indices.get("bottom", [])
            left_idx = side_to_indices.get("left", [])

            top_count = len(top_idx)
            right_count = len(right_idx)
            bottom_count = len(bottom_idx)
            left_count = len(left_idx)

            # We only need unique labels for top+right; the other two sides mirror.
            unique_needed = top_count + right_count
            unique = self.make_labels(unique_needed)

            top_labels = unique[:top_count]
            right_labels = unique[top_count:top_count + right_count]

            # Mirror sequences for opposite sides (clockwise order for bottom/left
            # is already reversed geometrically, so we still explicitly reverse the
            # top/right sequences to match the user's desired pattern).
            bottom_labels = list(reversed(top_labels))
            left_labels = list(reversed(right_labels))

            out = [None] * total

            # Fill mirrored sides; if counts don't match (unexpected geometry),
            # fill what we can and then fall back to unique labels for leftovers.
            for dst_i, label in zip(top_idx, top_labels):
                out[dst_i] = label
            for dst_i, label in zip(right_idx, right_labels):
                out[dst_i] = label
            for dst_i, label in zip(bottom_idx, bottom_labels):
                out[dst_i] = label
            for dst_i, label in zip(left_idx, left_labels):
                out[dst_i] = label

            # Any remaining slots (due to mismatched counts or unknown sides)
            # get deterministic unique labels.
            if any(v is None for v in out):
                remaining = [i for i, v in enumerate(out) if v is None]
                extra = self.make_labels(len(remaining))
                for i, lab in zip(remaining, extra):
                    out[i] = lab

            return out

        # Generate or retrieve cached base labels
        base_key = (m, n, tuple(ordered_keys))
        if (self._emoji_base_key != base_key or
            not self._emoji_base_labels or
            len(self._emoji_base_labels) != len(ordered_keys)):
            self._emoji_base_key = base_key
            # Base assignment for k=0: mirrored labels (top<->bottom, right<->left)
            self._emoji_base_labels = build_mirrored_base_labels()

        # Apply rotation to labels
        direction = settings.get("direction", "cw")
        k = int(settings.get("k", 0))
        rotated = self.rotate_labels(self._emoji_base_labels, k, direction)

        # Setup font for drawing
        font = QFont("Segoe UI Emoji")
        font.setPointSize(20)
        painter.setFont(font)
        fm = painter.fontMetrics()

        # Assign a rotated label per perimeter endpoint slot
        draw_items = []
        for i, (key, item) in enumerate(ordered_eps):
            txt = rotated[i] if i < len(rotated) else None
            if not txt:
                continue
            draw_items.append({
                "ep": item["ep"],
                "txt": txt,
                "width": float(item.get("width", 0.0) or 0.0),
            })

        # Draw each emoji label
        painter.save()

        for item in draw_items:
            ep = item["ep"]
            txt = item["txt"]
            width = item["width"]

            # Calculate outward offset so emoji sits outside the strand
            outward = (width * 0.5) + (fm.height() * 0.65) + 10.0
            outward = min(outward, max(24.0, self.BOUNDS_PADDING * 0.8))

            # Project endpoint to exact border edge for alignment
            side = ep.get("side", "")
            base_x = float(ep["x"])
            base_y = float(ep["y"])

            if side == "left":
                base_x = float(content.left())
            elif side == "right":
                base_x = float(content.right())
            elif side == "top":
                base_y = float(content.top())
            elif side == "bottom":
                base_y = float(content.bottom())

            # Apply outward offset using normal vector
            x = base_x + float(ep["nx"]) * outward
            y = base_y + float(ep["ny"]) * outward

            # Calculate centered text rectangle
            br = fm.boundingRect(txt)
            w = max(1, br.width() + 6)
            h = max(1, br.height() + 6)
            rect = QRectF(x - w / 2.0, y - h / 2.0, w, h)

            # Draw shadow for better visibility
            painter.setPen(QColor(0, 0, 0, 190))
            painter.drawText(
                QRectF(rect.x() + 1, rect.y() + 1, rect.width(), rect.height()),
                Qt.AlignCenter,
                txt
            )

            # Draw main text
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(rect, Qt.AlignCenter, txt)

        painter.restore()

    def draw_rotation_indicator(self, painter, bounds, settings, scale_factor=1.0):
        """
        Draw a rotation indicator in the top-right corner of the image.

        This draws a large circular arrow (CW or CCW) with the k value
        displayed in the center of the circle.

        Design:
        - CCW (counter-clockwise): Nearly complete circle with gap at ~8 o'clock,
          solid triangle arrowhead at ~9 o'clock pointing counter-clockwise
        - CW (clockwise): Vertical mirror - gap at ~4 o'clock,
          solid triangle arrowhead at ~3 o'clock pointing clockwise

        Args:
            painter: QPainter to draw with
            bounds: QRectF of the rendered area
            settings: Dict with emoji settings:
                {
                    "show": bool,       # Whether emojis are shown
                    "k": int,           # Rotation amount
                    "direction": str    # "cw" or "ccw"
                }
            scale_factor: Current scale factor for sizing adjustments
        """
        import math

        # Only show indicator if emojis are enabled
        if not settings.get("show", True):
            return

        k = int(settings.get("k", 0))
        direction = settings.get("direction", "cw")
        is_cw = (direction == "cw")

        # Format the k value with sign
        if k >= 0:
            k_text = f"+{k}"
        else:
            k_text = str(k)

        painter.save()

        # Size of the circular arrow indicator
        size = 96  # diameter of the circle
        arrow_thickness = 8
        margin = 20

        # Position in top-right corner
        center_x = bounds.right() - margin - size / 2
        center_y = bounds.top() + margin + size / 2
        radius = size / 2 - arrow_thickness

        # Styling:
        # - Transparent BG: use a white outline so the badge reads on dark/colored canvases.
        # - Non-transparent (white) BG: use a black outline (no white halo).
        is_transparent_bg = bool(settings.get("transparent", True))
        outline_color = QColor(255, 255, 255, 255) if is_transparent_bg else QColor(0, 0, 0, 255)
        fill_color = QColor(0, 0, 0, 255)

        # Reference icon target (matches the user's provided arrow image):
        # - CCW: small gap around ~7:30-8 o'clock (bottom-left), arrowhead at ~10-11 o'clock (top-left)
        # - CW: vertical mirror of CCW (gap bottom-right, arrowhead top-right)
        #
        # Qt angle system (degrees, counter-clockwise from 3 o'clock):
        #   3 o'clock = 0°, 12 o'clock = 90°, 9 o'clock = 180°, 6 o'clock = 270°
        #
        # NOTE: We draw the near-full arc with the gap defined by arc endpoints,
        # and place the arrowhead independently along the arc so it matches the
        # visual reference (arrowhead is not at the arc endpoint).

        # Small gap placement (CCW bottom-left; CW mirrored bottom-right).
        gap_center_deg = 225 if not is_cw else 315
        gap_half = 18  # small gap like the reference icon
        arc_span = 360 - 2 * gap_half  # near-full arc

        # Draw arc so its *missing* portion is centered at gap_center_deg.
        # For CCW: start at (gap_center + gap_half) and draw CCW.
        # For CW:  start at (gap_center - gap_half) and draw CW.
        if not is_cw:
            start_angle = gap_center_deg + gap_half
            span_angle = arc_span  # positive = CCW in Qt
        else:
            start_angle = gap_center_deg - gap_half
            span_angle = -arc_span  # negative = CW in Qt

        # Draw the circular arc
        arc_rect = QRectF(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2
        )

        # Draw outline first (thicker), then fill (thinner) to simulate stroke
        outline_pen = QPen(outline_color, arrow_thickness + 4, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(outline_pen)
        painter.drawArc(arc_rect, int(start_angle * 16), int(span_angle * 16))

        fill_pen = QPen(fill_color, arrow_thickness, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(fill_pen)
        painter.drawArc(arc_rect, int(start_angle * 16), int(span_angle * 16))

        # Draw solid triangle arrowhead, attached to the arc endpoint.
        #
        # IMPORTANT (visual alignment):
        # `drawArc()` uses a pen with `Qt.RoundCap`, so the *visible* arc end extends
        # past the mathematical endpoint by ~pen_width/2 along the tangent direction.
        # To make the arrowhead meet the *visible* end exactly, we push the triangle
        # tip forward by half the outline stroke width.
        arrow_end_deg = start_angle + span_angle
        arrow_angle_rad = math.radians(arrow_end_deg)

        # Triangle arrowhead size
        head_len = 18
        head_width = 30

        # Calculate arrowhead direction (tangent to circle, pointing in rotation direction)
        if is_cw:
            # Clockwise arrow points in direction of decreasing angle (tangent)
            arrow_dir_angle = arrow_angle_rad - math.pi / 2
        else:
            # Counter-clockwise arrow points in direction of increasing angle (tangent)
            arrow_dir_angle = arrow_angle_rad + math.pi / 2

        # Tip starts at the mathematical arc endpoint...
        tip_x = center_x + radius * math.cos(arrow_angle_rad)
        tip_y = center_y - radius * math.sin(arrow_angle_rad)  # Qt Y is inverted

        # ...then advance to the *visible* end of the rounded cap.
        outline_stroke_w = float(arrow_thickness + 4)
        cap_advance = outline_stroke_w * 0.5
        tip_x = tip_x + cap_advance * math.cos(arrow_dir_angle)
        tip_y = tip_y - cap_advance * math.sin(arrow_dir_angle)  # Qt Y inverted

        # Calculate the base center (backward from tip along arrow direction)
        base_x = tip_x - head_len * math.cos(arrow_dir_angle)
        base_y = tip_y + head_len * math.sin(arrow_dir_angle)  # Qt Y inverted

        # Calculate the two back corners of the triangle
        # The base of the triangle is perpendicular to the arrow direction
        perp_angle = arrow_dir_angle + math.pi / 2

        # Two corners of the triangle base (centered on base_x, base_y)
        corner1_x = base_x + (head_width / 2) * math.cos(perp_angle)
        corner1_y = base_y - (head_width / 2) * math.sin(perp_angle)
        corner2_x = base_x - (head_width / 2) * math.cos(perp_angle)
        corner2_y = base_y + (head_width / 2) * math.sin(perp_angle)

        # Create solid triangle path
        triangle = QPainterPath()
        triangle.moveTo(tip_x, tip_y)
        triangle.lineTo(corner1_x, corner1_y)
        triangle.lineTo(corner2_x, corner2_y)
        triangle.closeSubpath()

        # Draw triangle with a visible white outline:
        # - Fill black first
        # - Then stroke white on top (so it stays visible)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(triangle)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(outline_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(triangle)

        # Draw the number in the center (true outline around glyphs).
        # Using font metrics + drawText often makes the "stroke" look offset
        # (because it's typically faked via a shadow). A QPainterPath outline
        # hugs the glyph shapes exactly.
        font = QFont("Segoe UI", 14)
        font.setBold(True)

        text_path = QPainterPath()
        text_path.addText(0, 0, font, k_text)  # (0,0) is baseline origin
        br = text_path.boundingRect()
        text_path.translate(center_x - br.center().x(), center_y - br.center().y())

        # Outline, then fill
        outline_number_font = 4 if is_transparent_bg else 2
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(outline_color, outline_number_font, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(text_path)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
        painter.drawPath(text_path)

        painter.restore()
