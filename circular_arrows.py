"""
Generate SVG circular arrows - clockwise and counter-clockwise (mirror reflection)
Matching the reference image style with thick arc and triangular arrowhead
"""
import math

def generate_circular_arrow_svg(filename="circular_arrows.svg"):
    """Generate SVG with clockwise and counter-clockwise circular arrows"""

    # SVG dimensions
    width = 800
    height = 400

    # Arrow parameters
    cx1, cy = 200, 200  # Center for clockwise arrow
    cx2 = 600           # Center for counter-clockwise arrow
    radius = 100        # Radius of the arc
    stroke_width = 25   # Thickness of the arc

    # The arc covers about 300 degrees, leaving a gap for the arrowhead
    # Gap is at the right side (3 o'clock position) where the arrow points

    # CLOCKWISE ARROW
    # Arc goes from about 30 degrees (gap start) to 330 degrees (gap end)
    # Arrow points clockwise at the gap

    gap_start_cw = 30   # degrees - where arrowhead points TO
    gap_end_cw = 330    # degrees - where arc ends

    gap_start_rad_cw = math.radians(gap_start_cw)
    gap_end_rad_cw = math.radians(gap_end_cw)

    # Arc endpoints
    arc_start_x_cw = cx1 + radius * math.cos(gap_end_rad_cw)
    arc_start_y_cw = cy + radius * math.sin(gap_end_rad_cw)
    arc_end_x_cw = cx1 + radius * math.cos(gap_start_rad_cw)
    arc_end_y_cw = cy + radius * math.sin(gap_start_rad_cw)

    # Arc path (clockwise, large arc)
    # sweep-flag=1 for clockwise
    arc_path_cw = f"M {arc_start_x_cw},{arc_start_y_cw} A {radius},{radius} 0 1 1 {arc_end_x_cw},{arc_end_y_cw}"

    # Arrowhead - triangle pointing in clockwise direction
    arrow_length = 50
    arrow_width = 40

    # Tip of arrow is ahead of arc end in the direction of motion (clockwise)
    # At gap_start, moving clockwise means tangent points "down and right"
    tangent_angle_cw = gap_start_rad_cw + math.pi / 2

    # Arrowhead tip
    tip_x_cw = arc_end_x_cw + (arrow_length * 0.6) * math.cos(tangent_angle_cw)
    tip_y_cw = arc_end_y_cw + (arrow_length * 0.6) * math.sin(tangent_angle_cw)

    # Base of arrowhead (perpendicular to tangent)
    perp_angle_cw = tangent_angle_cw - math.pi / 2
    base1_x_cw = arc_end_x_cw + (arrow_width / 2) * math.cos(perp_angle_cw) - (arrow_length * 0.3) * math.cos(tangent_angle_cw)
    base1_y_cw = arc_end_y_cw + (arrow_width / 2) * math.sin(perp_angle_cw) - (arrow_length * 0.3) * math.sin(tangent_angle_cw)
    base2_x_cw = arc_end_x_cw - (arrow_width / 2) * math.cos(perp_angle_cw) - (arrow_length * 0.3) * math.cos(tangent_angle_cw)
    base2_y_cw = arc_end_y_cw - (arrow_width / 2) * math.sin(perp_angle_cw) - (arrow_length * 0.3) * math.sin(tangent_angle_cw)

    arrowhead_cw = f"M {tip_x_cw},{tip_y_cw} L {base1_x_cw},{base1_y_cw} L {base2_x_cw},{base2_y_cw} Z"

    # COUNTER-CLOCKWISE ARROW (Mirror reflection - horizontal flip)
    gap_start_ccw = 180 - gap_start_cw  # = 150 degrees
    gap_end_ccw = 180 - gap_end_cw      # = -150 = 210 degrees

    gap_start_rad_ccw = math.radians(gap_start_ccw)
    gap_end_rad_ccw = math.radians(gap_end_ccw)

    # Arc endpoints
    arc_start_x_ccw = cx2 + radius * math.cos(gap_end_rad_ccw)
    arc_start_y_ccw = cy + radius * math.sin(gap_end_rad_ccw)
    arc_end_x_ccw = cx2 + radius * math.cos(gap_start_rad_ccw)
    arc_end_y_ccw = cy + radius * math.sin(gap_start_rad_ccw)

    # Arc path (counter-clockwise, large arc)
    # sweep-flag=0 for counter-clockwise
    arc_path_ccw = f"M {arc_start_x_ccw},{arc_start_y_ccw} A {radius},{radius} 0 1 0 {arc_end_x_ccw},{arc_end_y_ccw}"

    # Arrowhead for CCW
    tangent_angle_ccw = gap_start_rad_ccw - math.pi / 2

    tip_x_ccw = arc_end_x_ccw + (arrow_length * 0.6) * math.cos(tangent_angle_ccw)
    tip_y_ccw = arc_end_y_ccw + (arrow_length * 0.6) * math.sin(tangent_angle_ccw)

    perp_angle_ccw = tangent_angle_ccw + math.pi / 2
    base1_x_ccw = arc_end_x_ccw + (arrow_width / 2) * math.cos(perp_angle_ccw) - (arrow_length * 0.3) * math.cos(tangent_angle_ccw)
    base1_y_ccw = arc_end_y_ccw + (arrow_width / 2) * math.sin(perp_angle_ccw) - (arrow_length * 0.3) * math.sin(tangent_angle_ccw)
    base2_x_ccw = arc_end_x_ccw - (arrow_width / 2) * math.cos(perp_angle_ccw) - (arrow_length * 0.3) * math.cos(tangent_angle_ccw)
    base2_y_ccw = arc_end_y_ccw - (arrow_width / 2) * math.sin(perp_angle_ccw) - (arrow_length * 0.3) * math.sin(tangent_angle_ccw)

    arrowhead_ccw = f"M {tip_x_ccw},{tip_y_ccw} L {base1_x_ccw},{base1_y_ccw} L {base2_x_ccw},{base2_y_ccw} Z"

    # Generate SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="white"/>

  <!-- Labels -->
  <text x="{cx1}" y="50" text-anchor="middle" font-family="Arial" font-size="18" fill="black">Clockwise</text>
  <text x="{cx2}" y="50" text-anchor="middle" font-family="Arial" font-size="18" fill="black">Counter-Clockwise (Mirror)</text>

  <!-- Clockwise Arrow -->
  <g id="clockwise-arrow">
    <path d="{arc_path_cw}"
          fill="none"
          stroke="black"
          stroke-width="{stroke_width}"
          stroke-linecap="round"/>
    <path d="{arrowhead_cw}" fill="black"/>
  </g>

  <!-- Counter-Clockwise Arrow (Mirror Reflection) -->
  <g id="counter-clockwise-arrow">
    <path d="{arc_path_ccw}"
          fill="none"
          stroke="black"
          stroke-width="{stroke_width}"
          stroke-linecap="round"/>
    <path d="{arrowhead_ccw}" fill="black"/>
  </g>

  <!-- Direction indicators -->
  <text x="{cx1}" y="360" text-anchor="middle" font-family="Arial" font-size="14" fill="gray">↻ Refresh</text>
  <text x="{cx2}" y="360" text-anchor="middle" font-family="Arial" font-size="14" fill="gray">↺ Undo</text>
</svg>'''

    # Write to file
    with open(filename, 'w') as f:
        f.write(svg_content)

    print(f"SVG saved to: {filename}")

    # Also print the path data for reference
    print("\n=== PATH DATA ===")
    print(f"\nClockwise Arrow:")
    print(f"  Arc: {arc_path_cw}")
    print(f"  Arrowhead: {arrowhead_cw}")
    print(f"\nCounter-Clockwise Arrow (Mirror):")
    print(f"  Arc: {arc_path_ccw}")
    print(f"  Arrowhead: {arrowhead_ccw}")

    return svg_content

if __name__ == "__main__":
    generate_circular_arrow_svg()
