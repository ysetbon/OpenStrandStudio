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
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen, QBrush, QPainterPath


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
        # Cache for visual (pixel-tight) emoji extents to place strand names based on what
        # is actually rendered, not on font-metric bounding boxes.
        self._emoji_visual_extents_cache = {}
        # Cache for rendered emoji glyph images (used to avoid Windows ClearType fringing
        # on transparent backgrounds and to speed up repeated renders).
        self._emoji_glyph_cache = {}
        # Store original endpoint order before parallel alignment
        # Maps strand_name -> emoji label (preserves assignment across position changes)
        self._strand_emoji_map = None
        self._strand_emoji_map_key = None

    def clear_cache(self):
        """
        Clear the cached emoji labels.

        Call this when the grid size changes or when you want to
        regenerate the emoji assignments from scratch.
        """
        self._emoji_base_labels = None
        self._emoji_base_key = None
        self._strand_emoji_map = None
        self._strand_emoji_map_key = None
        self.clear_render_cache()

    def clear_render_cache(self):
        """Clear only render-related caches (keeps emoji assignments stable)."""
        self._emoji_visual_extents_cache = {}
        self._emoji_glyph_cache = {}

    def _font_cache_key(self, font: QFont):
        # QFont is not reliably hashable across PyQt versions; use a stable tuple key.
        try:
            style_strategy = int(font.styleStrategy())
        except Exception:
            style_strategy = 0
        return (
            font.family(),
            float(font.pointSizeF()),
            int(font.pixelSize()),
            bool(font.bold()),
            bool(font.italic()),
            int(font.weight()),
            font.styleName(),
            style_strategy,
        )

    def _compute_alpha_bounds(self, alpha8: QImage, threshold: int = 8):
        """
        Return (min_x, min_y, max_x, max_y) bounds of non-transparent pixels, or None.

        Note: `alpha8` must be `QImage.Format_Alpha8`.
        """
        w = int(alpha8.width())
        h = int(alpha8.height())
        if w <= 0 or h <= 0:
            return None

        ptr = alpha8.bits()
        ptr.setsize(alpha8.byteCount())
        data = bytes(ptr)  # small (few 100KB); cache avoids repeated work
        bpl = int(alpha8.bytesPerLine())

        min_x, min_y = w, h
        max_x, max_y = -1, -1

        for y in range(h):
            row = data[y * bpl : y * bpl + w]
            any_hit = False
            for x, a in enumerate(row):
                if a > threshold:
                    any_hit = True
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
            if any_hit:
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

        if max_x < 0 or max_y < 0:
            return None
        return (min_x, min_y, max_x, max_y)

    def _get_visual_text_extents(self, txt: str, font: QFont):
        """
        Measure pixel-tight extents of rendered text around a known center.

        Returns a dict of directional extents (logical units):
            { "left": dL, "right": dR, "top": dT, "bottom": dB }
        where d* are distances from the drawn center to the tight pixel edge.
        """
        if not txt:
            return {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0}

        key = (txt, self._font_cache_key(font))
        cached = self._emoji_visual_extents_cache.get(key)
        if cached is not None:
            return cached

        # Supersample to reduce the effect of hinting/antialiasing on bounds.
        ss = 4  # supersample factor
        logical_size = 128.0
        img_w = int(logical_size * ss)
        img_h = int(logical_size * ss)

        img = QImage(img_w, img_h, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.scale(ss, ss)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 255))
        p.drawText(QRectF(0.0, 0.0, logical_size, logical_size), Qt.AlignCenter, txt)
        p.end()

        alpha = img.convertToFormat(QImage.Format_Alpha8)
        bounds = self._compute_alpha_bounds(alpha, threshold=8)

        # Fallback: if we fail to detect pixels (e.g. font engine edge-cases),
        # use font-metric tight bounds, which are still better than boundingRect().
        if bounds is None:
            # We deliberately avoid importing QFontMetrics at module scope.
            # The metrics object needs a paint device anyway, so reuse `alpha`.
            p2 = QPainter(alpha)
            p2.setFont(font)
            fm = p2.fontMetrics()
            tbr = fm.tightBoundingRect(txt)
            p2.end()
            # tightBoundingRect is in device pixels; treat as centered.
            cached = {
                "left": float(tbr.width()) * 0.5,
                "right": float(tbr.width()) * 0.5,
                "top": float(tbr.height()) * 0.5,
                "bottom": float(tbr.height()) * 0.5,
            }
            self._emoji_visual_extents_cache[key] = cached
            return cached

        min_x, min_y, max_x, max_y = bounds
        cx = (img_w - 1) * 0.5
        cy = (img_h - 1) * 0.5

        cached = {
            "left": float(cx - min_x) / ss,
            "right": float(max_x - cx) / ss,
            "top": float(cy - min_y) / ss,
            "bottom": float(max_y - cy) / ss,
        }
        self._emoji_visual_extents_cache[key] = cached
        return cached

    def _get_emoji_glyph_image(self, txt: str, font: QFont, logical_w: int, logical_h: int, ss: int = 3):
        """
        Render an emoji into a cached, supersampled offscreen image.

        Why: On Windows, drawing color emoji text directly onto a transparent target can
        produce colored halos (lime/magenta/black) due to LCD/subpixel AA assumptions.
        Rendering into an offscreen buffer and then scaling down removes the fringe.
        """
        if not txt:
            return None

        lw = max(1, int(logical_w))
        lh = max(1, int(logical_h))
        key = ("emoji_glyph", txt, self._font_cache_key(font), lw, lh, int(ss))
        cached = self._emoji_glyph_cache.get(key)
        if cached is not None:
            return cached

        img_w = max(1, int(lw * ss))
        img_h = max(1, int(lh * ss))

        # Render into straight-alpha first. Some Windows emoji rendering paths can
        # produce edge colors that look like a "stroke" when drawn directly into a
        # premultiplied surface. Converting after render helps normalize.
        img_straight = QImage(img_w, img_h, QImage.Format_ARGB32)
        img_straight.fill(Qt.transparent)

        p = QPainter(img_straight)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.scale(ss, ss)
        p.setFont(font)
        # Pen color is irrelevant for color emoji glyphs, but use transparent to
        # avoid black stroke artifacts around the emojis.
        p.setPen(QColor(0, 0, 0, 0))
        p.setBrush(Qt.NoBrush)
        p.drawText(QRectF(0.0, 0.0, float(lw), float(lh)), Qt.AlignCenter, txt)
        p.end()

        # Convert to premultiplied (our target images are premultiplied).
        img = img_straight.convertToFormat(QImage.Format_ARGB32_Premultiplied)

        # Clean fully/near-transparent pixels to transparent black to avoid colored
        # fringing when compositing (common with emoji edges on Windows).
        # This is cheap (glyph images are small) and cached.
        # Using a higher cutoff (50) to aggressively remove semi-transparent fringe
        # pixels that can appear as colored strokes around emojis due to LCD/ClearType
        # subpixel antialiasing.
        alpha_cutoff = 50  # 0..255
        for y in range(img.height()):
            for x in range(img.width()):
                a = QColor.fromRgba(img.pixel(x, y)).alpha()
                if a <= alpha_cutoff:
                    img.setPixel(x, y, 0)

        self._emoji_glyph_cache[key] = img
        return img

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
            "\U0001F436", "\U0001F431", "\U0001F42D", "\U0001F430", "\U0001F994",  # dog, cat, mouse, rabbit, hedgehog 

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

        endpoint_map = {}  # key -> {"ep": ep, "t": float, "width": float, "strand_name": str, "ep_type": str}

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
                    ep_a_type = "start"
                    ep_b_type = "end"
                else:
                    ep_a = {"x": x2, "y": y2, "side": "left", "nx": -1.0, "ny": 0.0}
                    ep_b = {"x": x1, "y": y1, "side": "right", "nx": 1.0, "ny": 0.0}
                    ep_a_type = "end"
                    ep_b_type = "start"
            else:
                # Vertical strand: endpoints on top/bottom
                if y1 <= y2:
                    ep_a = {"x": x1, "y": y1, "side": "top", "nx": 0.0, "ny": -1.0}
                    ep_b = {"x": x2, "y": y2, "side": "bottom", "nx": 0.0, "ny": 1.0}
                    ep_a_type = "start"
                    ep_b_type = "end"
                else:
                    ep_a = {"x": x2, "y": y2, "side": "top", "nx": 0.0, "ny": -1.0}
                    ep_b = {"x": x1, "y": y1, "side": "bottom", "nx": 0.0, "ny": 1.0}
                    ep_a_type = "end"
                    ep_b_type = "start"

            strand_width = float(getattr(strand, "width", getattr(canvas, "strand_width", 46)))

            for ep, ep_type in [(ep_a, ep_a_type), (ep_b, ep_b_type)]:
                key = ep_key(ep)
                t = perimeter_t(ep["side"], ep["x"], ep["y"])
                if key not in endpoint_map:
                    endpoint_map[key] = {
                        "ep": ep,
                        "t": float(t),
                        "width": strand_width,
                        # Only store strand_name for END points (free ends at perimeter)
                        "strand_name": suffix_source if ep_type == "end" else "",
                        "ep_type": ep_type
                    }
                else:
                    # Use the widest strand width for outward offset calculation.
                    endpoint_map[key]["width"] = max(endpoint_map[key]["width"], strand_width)
                    # If this is an END point and we don't have a name yet, use it
                    if ep_type == "end" and not endpoint_map[key].get("strand_name"):
                        endpoint_map[key]["strand_name"] = suffix_source
                        endpoint_map[key]["ep_type"] = ep_type

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
        # Use a position-independent key (m, n, total_count) so that emoji assignments
        # stay stable when strand positions change (e.g., after parallel alignment)
        base_key = (m, n, len(ordered_keys))
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
        #
        # IMPORTANT (Windows/Qt):
        # Some emoji glyphs can show colored "fringing" (often green/magenta) due to
        # ClearType/subpixel antialiasing, especially on light/transparent backgrounds.
        # Disabling subpixel AA makes the edges consistent and removes the lime halo.
        font = QFont("Segoe UI Emoji")
        font.setPointSize(20)
        try:
            font.setStyleStrategy(QFont.PreferAntialias | QFont.NoSubpixelAntialias)
        except Exception:
            # Some Qt/PyQt builds may not expose all style strategy flags; safe to ignore.
            pass
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
                "strand_name": item.get("strand_name", ""),
                "ep_type": item.get("ep_type", ""),
            })

        # Check if strand names should be shown
        show_strand_names = settings.get("show_strand_names", False)

        # Draw each emoji label
        painter.save()

        # IMPORTANT: Reset painter state to prevent strand colors bleeding into emoji rendering
        # (The strand.draw() calls may leave the brush set to a strand color)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(Qt.NoPen)

        # Setup font for strand names (much smaller than emoji)
        name_font = QFont("Segoe UI")
        name_font.setPointSize(7)
        name_font.setBold(True)
        try:
            name_font.setStyleStrategy(QFont.PreferAntialias | QFont.NoSubpixelAntialias)
        except Exception:
            pass
        # name_fm is computed on-demand after setting the font (see below).

        for item in draw_items:
            ep = item["ep"]
            txt = item["txt"]
            width = item["width"]
            strand_name = item.get("strand_name", "")
            ep_type = item.get("ep_type", "")

            # Calculate outward offset so emoji sits outside the strand
            outward = (width * 0.5) + (fm.height() * 0.65) + 10.0
            outward = min(outward, max(24.0, self.BOUNDS_PADDING * 0.8))

            # Project endpoint to exact border edge for alignment (keep emoji positions stable).
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

            nx = float(ep.get("nx", 0.0) or 0.0)
            ny = float(ep.get("ny", 0.0) or 0.0)

            # Apply outward offset using normal vector
            x = base_x + nx * outward
            y = base_y + ny * outward

            # Calculate centered text rectangle
            br = fm.boundingRect(txt)
            w = max(1, br.width() + 6)
            h = max(1, br.height() + 6)
            rect = QRectF(x - w / 2.0, y - h / 2.0, w, h)

            # Draw emoji in a way that avoids Windows ClearType/subpixel fringing on alpha.
            # Render into a cached supersampled buffer, then scale down into `rect`.
            painter.setBrush(Qt.NoBrush)
            painter.setPen(Qt.NoPen)
            # Render at the *same* logical size we used before (based on font metrics),
            # so the emoji appears the same size as the direct drawText() version.
            glyph_img = self._get_emoji_glyph_image(txt, font, int(w), int(h), ss=3)
            if glyph_img is not None:
                painter.drawImage(rect, glyph_img)
            else:
                # Fallback: direct text draw (should rarely happen)
                painter.setPen(QColor(0, 0, 0, 255))
                painter.drawText(rect, Qt.AlignCenter, txt)

            # Draw strand name if enabled (only for END points of _2/_3 strands)
            if show_strand_names and strand_name:
                # Format: just the strand name like "3_2" or "1_3"
                name_txt = strand_name

                painter.setFont(name_font)
                name_fm = painter.fontMetrics()
                name_br = name_fm.boundingRect(name_txt)
                name_w = max(1, name_br.width() + 4)
                name_h = max(1, name_br.height() + 2)

                # Place the name at the true midpoint between:
                # - the endpoint (distance 0 from the endpoint), and
                # - the emoji's *visual* inner edge (measured from actual rendered pixels).
                ext = self._get_visual_text_extents(txt, font)
                if abs(nx) > 0.5:
                    inward_extent = ext["right"] if nx < 0.0 else ext["left"]
                else:
                    inward_extent = ext["bottom"] if ny < 0.0 else ext["top"]

                emoji_inner_edge_off = max(1.0, outward - float(inward_extent))
                mid_dist = emoji_inner_edge_off * 0.5

                name_x = base_x + nx * mid_dist
                name_y = base_y + ny * mid_dist

                name_rect = QRectF(name_x - name_w / 2.0, name_y - name_h / 2.0, name_w, name_h)

                # Draw background for readability (subtle)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 150))
                painter.drawRoundedRect(name_rect.adjusted(-1, -1, 1, 1), 2, 2)

                # Draw strand name text
                painter.setPen(QColor(255, 255, 255, 255))
                painter.drawText(name_rect, Qt.AlignCenter, name_txt)

                # Reset font to emoji font
                painter.setFont(font)

        painter.restore()

    def draw_rotation_indicator(self, painter, bounds, settings, scale_factor=1.0):
        """
        Draw a rotation indicator in the top-right corner of the image.

        This draws a large circular arrow (CW or CCW) with the k value
        displayed in the center of the circle.

        Design matches the reference SVG:
        - Arc with stroke-linecap="butt" (flat ends)
        - Thick stroke relative to radius (~42% ratio)
        - Isosceles triangle arrowhead with base midpoint at arc endpoint
        - Arrowhead rotated to match arc tangent + offset angle

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

        # Size of the circular arrow indicator.
        # We will render the *exact* reference SVG geometry in a 604x604
        # viewbox, then scale it into this `size` box.
        size = 96  # diameter of the outer icon box
        margin = 20

        # Position in top-right corner
        center_x = bounds.right() - margin - size / 2
        center_y = bounds.top() + margin + size / 2
        # Styling: match the provided SVG (solid black fill), but add a stroke
        # around the arrow for legibility (same approach as the number).
        fill_color = QColor(0, 0, 0, 255)

        is_transparent_bg = bool(settings.get("transparent", True))
        outline_color = QColor(255, 255, 255, 255) if is_transparent_bg else QColor(0, 0, 0, 0)
        outline_number_font = 4 if is_transparent_bg else 2
        # These widths are in the SVG coordinate space (604x604) and get scaled down with `s`.
        # (Border thickness in device pixels ~= arrow_outline_extra * s)
        arrow_outline_extra = 8.0 if is_transparent_bg else 5.0
        # For a filled shape outlined then filled: visible border ~= pen_width/2.
        # Match the triangle border to the shaft border (which is `arrow_outline_extra`).
        arrowhead_outline_width = 2.0 * arrow_outline_extra

        # Nudge the icon inward so the outline isn't clipped at the top/right edges.
        # (This replaces the previous SquareCap trick, which made the end "side line" too thick.)
        margin += 3 if is_transparent_bg else 2

        # --- Render the SVG geometry exactly, then scale into `size` ---
        # Reference SVG:
        # - viewBox: 0 0 604 604
        # - Arc path: M 497 211 A 215 215 0 1 1 393 107
        # - stroke-width: 90, stroke-linecap: butt
        # - Arrowhead polygon: points="0,-95 0,95 190,0"
        #   transform="translate(393 107) rotate(25.1)"
        #
        # In Qt we draw the same circle arc via drawArc with:
        # - circle center: (302,302)
        # - radius: 215
        # - start angle: 25°
        # - end angle: 65°
        # - long CW span: -320°  (because 65° - 25° = 40° small arc; we want the large arc)
        svg_size = 604.0
        s = float(size) / svg_size

        # Target rect in device coords
        icon_left = center_x - size / 2.0
        icon_top = center_y - size / 2.0

        painter.save()
        painter.translate(icon_left, icon_top)
        painter.scale(s, s)

        # Mirror for CCW so the icon is the exact mirrored version of the SVG.
        # This keeps the arrowhead *identical* in shape and relative placement.
        if not is_cw:
            painter.translate(svg_size, 0.0)
            painter.scale(-1.0, 1.0)

        # Arc (exact proportions)
        # Outline, then fill
        arc_outline_pen = QPen(outline_color, 80.0 + (2.0 * arrow_outline_extra), Qt.SolidLine, Qt.FlatCap)
        painter.setPen(arc_outline_pen)
        painter.setBrush(Qt.NoBrush)

        arc_rect = QRectF(87.0, 87.0, 430.0, 430.0)  # (302-215, 302-215, 2*215, 2*215)
        start_angle_deg = 15.0
        span_angle_deg = -320.0

        fill_cap_deg = 8.0 if is_transparent_bg else 6.0
        # Shift start along arc direction so end stays the same.
        shift = fill_cap_deg if span_angle_deg > 0.0 else -fill_cap_deg
        fill_start_deg = start_angle_deg + shift
        fill_span_deg = span_angle_deg - shift

        # Draw the outline arc starting at the fill start (flush with fill)
        # We will add a manual tangential cap to create the "side line" extension
        # perpendicular to the shaft gradient.
        painter.drawArc(arc_rect, int(fill_start_deg * 16), int(fill_span_deg * 16))

        # ====================================================================
        # START OF "SIDE LINE" STROKE - Manual cap (rectangular extension)
        # ====================================================================
        # This creates a "butt end" that is exactly 90 degrees to the shaft start gradient
        cx, cy = 302.0, 302.0
        r = 215.0
        w_out = 80.0 + (2.0 * arrow_outline_extra)
        
        # Geometry for the cap
        theta = math.radians(fill_start_deg)
        nx = math.cos(theta)
        ny = -math.sin(theta)  # Y is down, positive angle is CCW
        tx = -math.sin(theta)
        ty = -math.cos(theta)
        
        # Extension direction: Backwards from shift direction
        ext_dir = -1.0 if shift > 0 else 1.0
        ext_len = r * math.radians(abs(shift))
        
        r_in = r - w_out / 2.0
        r_out = r + w_out / 2.0
        
        p_in = (cx + r_in * nx, cy + r_in * ny)
        p_out = (cx + r_out * nx, cy + r_out * ny)
        
        dx = tx * ext_dir * ext_len*0.3
        dy = ty * ext_dir * ext_len*0.3
        
        p_in_ext = (p_in[0] + dx, p_in[1] + dy)
        p_out_ext = (p_out[0] + dx, p_out[1] + dy)
        
        cap_path = QPainterPath()
        cap_path.moveTo(*p_in)
        cap_path.lineTo(*p_out)
        cap_path.lineTo(*p_out_ext)
        cap_path.lineTo(*p_in_ext)
        cap_path.closeSubpath()
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(outline_color)
        painter.drawPath(cap_path)
        # ====================================================================
        # END OF "SIDE LINE" STROKE
        # ====================================================================

        arc_pen = QPen(fill_color, 80.0, Qt.SolidLine, Qt.FlatCap)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(arc_rect, int(fill_start_deg * 16), int(fill_span_deg * 16))

        # Arrowhead polygon (exact transform)
        theta = math.radians(25.1)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        base_mid_x = 393.0
        base_mid_y = 107.0

        pts = [(0.0, -95.0), (0.0, 95.0), (190.0, 0.0)]
        tri = QPainterPath()
        for i, (x, y) in enumerate(pts):
            xr = (x * cos_t) - (y * sin_t)
            yr = (x * sin_t) + (y * cos_t)
            px = base_mid_x + xr
            py = base_mid_y + yr
            if i == 0:
                tri.moveTo(px, py)
            else:
                tri.lineTo(px, py)
        tri.closeSubpath()

        # Outline, then fill (matches the number outline style)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(outline_color, arrowhead_outline_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(tri)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(tri)
        painter.restore()

        # Draw the number in the center (true outline around glyphs).
        font = QFont("Segoe UI", 14)
        font.setBold(True)

        text_path = QPainterPath()
        text_path.addText(0, 0, font, k_text)  # (0,0) is baseline origin
        br = text_path.boundingRect()
        text_path.translate(center_x - br.center().x(), center_y - br.center().y())

        # Outline, then fill
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(outline_color, outline_number_font, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(text_path)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
        painter.drawPath(text_path)

        painter.restore()
