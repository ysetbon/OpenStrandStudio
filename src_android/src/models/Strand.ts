// Strand model - Core data structure for strands
// Ported from src/strand.py

import {
  Strand,
  StrandSegment,
  StrandStyle,
  Point,
  BezierCurve,
} from '../types';
import {
  bezierLength,
  bezierPoint,
  distance,
  rotatePoint,
  angleBetweenPoints,
} from '../utils/bezier';

export class StrandModel {
  private static buildDefaultStyle(style?: Partial<StrandStyle>): StrandStyle {
    const defaultStyle: StrandStyle = {
      color: '#C8AAE6', // Purple like desktop (200, 170, 230)
      strokeColor: '#000000', // Black stroke like desktop
      strokeWidth: 4, // Default stroke width like desktop
      width: 20,
      shadowEnabled: true,
      shadowColor: 'rgba(0, 0, 0, 0.59)', // 150/255 opacity like desktop
      shadowOffset: {x: 2, y: 2},
      shadowBlur: 4,
    };

    return {...defaultStyle, ...style};
  }

  private static deriveEndpoints(segments: StrandSegment[]): {
    start?: Point;
    end?: Point;
  } {
    if (segments.length === 0) {
      return {};
    }
    const first = segments[0].bezier;
    const last = segments[segments.length - 1].bezier;
    return {
      start: {...first.start},
      end: {...last.end},
    };
  }

  private static midpoint(a: Point, b: Point): Point {
    return {x: (a.x + b.x) / 2, y: (a.y + b.y) / 2};
  }

  /**
   * Create a new strand with default styling
   */
  static create(
    id: string,
    segments: StrandSegment[] = [],
    style?: Partial<StrandStyle>,
  ): Strand {
    const resolvedStyle = StrandModel.buildDefaultStyle(style);
    const {start, end} = StrandModel.deriveEndpoints(segments);
    const fallbackStart = start ?? {x: 0, y: 0};
    const fallbackEnd = end ?? {x: 0, y: 0};
    const controlPoint1 = segments[0]?.bezier.control1 ?? fallbackStart;
    const controlPoint2 =
      segments[segments.length - 1]?.bezier.control2 ?? fallbackStart;
    const controlPointCenter = StrandModel.midpoint(
      controlPoint1,
      controlPoint2,
    );

    return {
      id,
      segments,
      style: resolvedStyle,
      closed: false,
      visible: true,
      locked: false,
      start: fallbackStart,
      end: fallbackEnd,
      controlPoint1,
      controlPoint2,
      controlPointCenter,
      controlPointCenterLocked: false,
      triangleHasMoved: false,
      controlPoint2Shown: false,
      controlPoint2Activated: false,
      startAttached: false,
      endAttached: false,
      isSelected: false,
      isHidden: false,
      shadowOnly: false,
      hasCircles: [false, false],
      isStartSide: true,
      curveResponseExponent: 1.5,
      controlPointBaseFraction: 0.4,
      distanceMultiplier: 1.2,
      endpointTension: 1.15,
      startLineVisible: true,
      endLineVisible: true,
      startExtensionVisible: false,
      endExtensionVisible: false,
      startArrowVisible: false,
      endArrowVisible: false,
      fullArrowVisible: false,
      arrowColor: null,
      arrowTransparency: 100,
      arrowTexture: 'none',
      arrowShaftStyle: 'solid',
      arrowHeadVisible: true,
      layerName: '',
      setNumber: null,
      knotConnections: {},
      attachable: true,
      attachedStrandIds: [],
      color: resolvedStyle.color,
      strokeColor: resolvedStyle.strokeColor,
      strokeWidth: resolvedStyle.strokeWidth,
      width: resolvedStyle.width,
      shadowColor: resolvedStyle.shadowColor,
      sideLineColor: '#000000',
      circleStrokeColor: null,
      startCircleStrokeColor: null,
      endCircleStrokeColor: null,
    };
  }

  /**
   * Create a simple straight strand between two points
   */
  static createStraight(
    id: string,
    start: Point,
    end: Point,
    style?: Partial<StrandStyle>,
  ): Strand {
    const dx = (end.x - start.x) / 3;
    const dy = (end.y - start.y) / 3;

    const bezier: BezierCurve = {
      start,
      control1: {x: start.x + dx, y: start.y + dy},
      control2: {x: end.x - dx, y: end.y - dy},
      end,
    };

    const segment: StrandSegment = {
      bezier,
      length: bezierLength(bezier),
    };

    const strand = StrandModel.create(id, [segment], style);
    const controlPointCenter = StrandModel.midpoint(
      segment.bezier.control1,
      segment.bezier.control2,
    );
    return {
      ...strand,
      start,
      end,
      controlPoint1: segment.bezier.control1,
      controlPoint2: segment.bezier.control2,
      controlPointCenter,
    };
  }

  /**
   * Get total length of the strand
   */
  static getTotalLength(strand: Strand): number {
    return strand.segments.reduce((sum, seg) => sum + seg.length, 0);
  }

  /**
   * Get a point on the strand at a specific parameter t (0 to 1 along entire strand)
   */
  static getPointAt(strand: Strand, t: number): Point | null {
    if (strand.segments.length === 0) {
      return null;
    }

    const totalLength = StrandModel.getTotalLength(strand);
    let targetLength = t * totalLength;
    let accumulated = 0;

    for (const segment of strand.segments) {
      if (accumulated + segment.length >= targetLength) {
        const segmentT = (targetLength - accumulated) / segment.length;
        return bezierPoint(segment.bezier, segmentT);
      }
      accumulated += segment.length;
    }

    // Return the end point if we somehow didn't find it
    const lastSegment = strand.segments[strand.segments.length - 1];
    return bezierPoint(lastSegment.bezier, 1);
  }

  /**
   * Translate (move) a strand by an offset
   */
  static translate(strand: Strand, offset: Point): Strand {
    const newSegments = strand.segments.map(seg => ({
      ...seg,
      bezier: {
        start: {x: seg.bezier.start.x + offset.x, y: seg.bezier.start.y + offset.y},
        control1: {x: seg.bezier.control1.x + offset.x, y: seg.bezier.control1.y + offset.y},
        control2: {x: seg.bezier.control2.x + offset.x, y: seg.bezier.control2.y + offset.y},
        end: {x: seg.bezier.end.x + offset.x, y: seg.bezier.end.y + offset.y},
      },
    }));

    return {
      ...strand,
      segments: newSegments,
      start: strand.start ? {x: strand.start.x + offset.x, y: strand.start.y + offset.y} : strand.start,
      end: strand.end ? {x: strand.end.x + offset.x, y: strand.end.y + offset.y} : strand.end,
      controlPoint1: strand.controlPoint1
        ? {x: strand.controlPoint1.x + offset.x, y: strand.controlPoint1.y + offset.y}
        : strand.controlPoint1,
      controlPoint2: strand.controlPoint2
        ? {x: strand.controlPoint2.x + offset.x, y: strand.controlPoint2.y + offset.y}
        : strand.controlPoint2,
      controlPointCenter: strand.controlPointCenter
        ? {x: strand.controlPointCenter.x + offset.x, y: strand.controlPointCenter.y + offset.y}
        : strand.controlPointCenter,
    };
  }

  /**
   * Rotate a strand around a center point
   */
  static rotate(strand: Strand, center: Point, angle: number): Strand {
    const newSegments = strand.segments.map(seg => ({
      ...seg,
      bezier: {
        start: rotatePoint(seg.bezier.start, center, angle),
        control1: rotatePoint(seg.bezier.control1, center, angle),
        control2: rotatePoint(seg.bezier.control2, center, angle),
        end: rotatePoint(seg.bezier.end, center, angle),
      },
    }));

    return {
      ...strand,
      segments: newSegments,
      start: strand.start ? rotatePoint(strand.start, center, angle) : strand.start,
      end: strand.end ? rotatePoint(strand.end, center, angle) : strand.end,
      controlPoint1: strand.controlPoint1
        ? rotatePoint(strand.controlPoint1, center, angle)
        : strand.controlPoint1,
      controlPoint2: strand.controlPoint2
        ? rotatePoint(strand.controlPoint2, center, angle)
        : strand.controlPoint2,
      controlPointCenter: strand.controlPointCenter
        ? rotatePoint(strand.controlPointCenter, center, angle)
        : strand.controlPointCenter,
    };
  }

  /**
   * Scale a strand from a center point
   */
  static scale(strand: Strand, center: Point, factor: number): Strand {
    const scalePoint = (pt: Point): Point => ({
      x: center.x + (pt.x - center.x) * factor,
      y: center.y + (pt.y - center.y) * factor,
    });

    const newSegments = strand.segments.map(seg => {
      const newBezier = {
        start: scalePoint(seg.bezier.start),
        control1: scalePoint(seg.bezier.control1),
        control2: scalePoint(seg.bezier.control2),
        end: scalePoint(seg.bezier.end),
      };
      return {
        bezier: newBezier,
        length: bezierLength(newBezier),
      };
    });

    return {
      ...strand,
      segments: newSegments,
      start: strand.start ? scalePoint(strand.start) : strand.start,
      end: strand.end ? scalePoint(strand.end) : strand.end,
      controlPoint1: strand.controlPoint1
        ? scalePoint(strand.controlPoint1)
        : strand.controlPoint1,
      controlPoint2: strand.controlPoint2
        ? scalePoint(strand.controlPoint2)
        : strand.controlPoint2,
      controlPointCenter: strand.controlPointCenter
        ? scalePoint(strand.controlPointCenter)
        : strand.controlPointCenter,
    };
  }

  /**
   * Get the center point (centroid) of a strand
   */
  static getCenter(strand: Strand): Point {
    if (strand.segments.length === 0) {
      return {x: 0, y: 0};
    }

    let sumX = 0;
    let sumY = 0;
    let count = 0;

    strand.segments.forEach(seg => {
      // Sample points along the curve
      for (let i = 0; i <= 10; i++) {
        const pt = bezierPoint(seg.bezier, i / 10);
        sumX += pt.x;
        sumY += pt.y;
        count++;
      }
    });

    return {
      x: sumX / count,
      y: sumY / count,
    };
  }

  /**
   * Check if a point is near the strand (for selection)
   */
  static isPointNear(
    strand: Strand,
    point: Point,
    threshold: number = 20,
  ): boolean {
    for (const segment of strand.segments) {
      // Sample points along the curve
      for (let i = 0; i <= 20; i++) {
        const pt = bezierPoint(segment.bezier, i / 20);
        if (distance(pt, point) <= threshold) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Get bounding box of the strand
   */
  static getBoundingBox(strand: Strand): {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  } {
    if (strand.segments.length === 0) {
      return {minX: 0, minY: 0, maxX: 0, maxY: 0};
    }

    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    strand.segments.forEach(seg => {
      for (let i = 0; i <= 20; i++) {
        const pt = bezierPoint(seg.bezier, i / 20);
        minX = Math.min(minX, pt.x);
        minY = Math.min(minY, pt.y);
        maxX = Math.max(maxX, pt.x);
        maxY = Math.max(maxY, pt.y);
      }
    });

    return {minX, minY, maxX, maxY};
  }

  /**
   * Clone a strand (deep copy)
   */
  static clone(strand: Strand): Strand {
    return JSON.parse(JSON.stringify(strand));
  }

  /**
   * Update strand style
   */
  static updateStyle(strand: Strand, style: Partial<StrandStyle>): Strand {
    const updatedStyle = {
      ...strand.style,
      ...style,
    };
    return {
      ...strand,
      style: updatedStyle,
      color: updatedStyle.color,
      strokeColor: updatedStyle.strokeColor,
      strokeWidth: updatedStyle.strokeWidth,
      width: updatedStyle.width,
      shadowColor: updatedStyle.shadowColor,
    };
  }

  /**
   * Create a new strand with initial zero-length geometry.
   * Control points are initialized at start position, matching desktop behavior.
   * Desktop strand.py __init__ lines 44-61
   */
  static createInitial(
    id: string,
    startPoint: Point,
    style?: Partial<StrandStyle>,
  ): Strand {
    const resolvedStyle = StrandModel.buildDefaultStyle(style);

    // Create with zero-length bezier (start == end, control points at start)
    // This matches desktop strand.py lines 44-61 where:
    // dx = 0, dy = 0
    // control_point1 = QPointF(self._start.x(), self._start.y())
    // control_point2 = QPointF(self._start.x(), self._start.y())
    // control_point_center = QPointF(self._start.x(), self._start.y())
    const bezier: BezierCurve = {
      start: startPoint,
      control1: {...startPoint}, // At start, like desktop
      control2: {...startPoint}, // At start, like desktop
      end: {...startPoint},
    };

    const segment: StrandSegment = {
      bezier,
      length: 0,
    };

    return {
      id,
      segments: [segment],
      style: resolvedStyle,
      closed: false,
      visible: true,
      locked: false,
      start: {...startPoint},
      end: {...startPoint},
      controlPoint1: {...startPoint},
      controlPoint2: {...startPoint},
      controlPointCenter: {...startPoint},
      controlPointCenterLocked: false,
      triangleHasMoved: false,
      controlPoint2Shown: false,
      controlPoint2Activated: false,
      startAttached: false,
      endAttached: false,
      isSelected: false,
      isHidden: false,
      shadowOnly: false,
      hasCircles: [false, false],
      isStartSide: true,
      curveResponseExponent: 1.5,
      controlPointBaseFraction: 0.4,
      distanceMultiplier: 1.2,
      endpointTension: 1.15,
      startLineVisible: true,
      endLineVisible: true,
      startExtensionVisible: false,
      endExtensionVisible: false,
      startArrowVisible: false,
      endArrowVisible: false,
      fullArrowVisible: false,
      arrowColor: null,
      arrowTransparency: 100,
      arrowTexture: 'none',
      arrowShaftStyle: 'solid',
      arrowHeadVisible: true,
      layerName: '',
      setNumber: null,
      knotConnections: {},
      attachable: true,
      attachedStrandIds: [],
      color: resolvedStyle.color,
      strokeColor: resolvedStyle.strokeColor,
      strokeWidth: resolvedStyle.strokeWidth,
      width: resolvedStyle.width,
      shadowColor: resolvedStyle.shadowColor,
      sideLineColor: '#000000',
      circleStrokeColor: null,
      startCircleStrokeColor: null,
      endCircleStrokeColor: null,
    };
  }

  /**
   * Update strand endpoint during drag operation.
   * Does NOT recalculate control points (they stay at their current position).
   * Matches desktop behavior during mouse drag where only strand.end is updated.
   */
  static updateEndpoint(strand: Strand, newEnd: Point): Strand {
    const start = strand.start ?? {x: 0, y: 0};

    const bezier: BezierCurve = {
      start,
      control1: strand.controlPoint1 ?? start,
      control2: strand.controlPoint2 ?? start,
      end: newEnd,
    };

    const segment: StrandSegment = {
      bezier,
      length: bezierLength(bezier),
    };

    return {
      ...strand,
      segments: [segment],
      end: newEnd,
    };
  }

  /**
   * Update control points based on current start and end positions.
   * Matches desktop strand.py update_control_points_from_geometry() at lines 3432-3454
   * Positions control_point1 at 1/3 and control_point2 at 2/3 along the line.
   */
  static updateControlPointsFromGeometry(strand: Strand): Strand {
    const start = strand.start ?? {x: 0, y: 0};
    const end = strand.end ?? {x: 0, y: 0};

    const dx = end.x - start.x;
    const dy = end.y - start.y;

    const controlPoint1 = {
      x: start.x + dx / 3,
      y: start.y + dy / 3,
    };
    const controlPoint2 = {
      x: start.x + (2 * dx) / 3,
      y: start.y + (2 * dy) / 3,
    };

    // Update center as midpoint, reset lock
    const controlPointCenter = StrandModel.midpoint(controlPoint1, controlPoint2);

    // Update segments with new control points
    const newSegments = strand.segments.map((seg, idx) => {
      if (idx === 0) {
        const newBezier: BezierCurve = {
          start: seg.bezier.start,
          control1: controlPoint1,
          control2: controlPoint2,
          end: seg.bezier.end,
        };
        return {
          ...seg,
          bezier: newBezier,
          length: bezierLength(newBezier),
        };
      }
      return seg;
    });

    return {
      ...strand,
      segments: newSegments,
      controlPoint1,
      controlPoint2,
      controlPointCenter,
      controlPointCenterLocked: false,
    };
  }

  /**
   * Update the shape of the strand based on its start, end, and control points.
   * Matches desktop strand.py update_shape() at lines 441-497
   * Recalculates controlPointCenter as midpoint, respects controlPointCenterLocked flag.
   */
  static updateShape(strand: Strand): Strand {
    const controlPoint1 = strand.controlPoint1 ?? {x: 0, y: 0};
    const controlPoint2 = strand.controlPoint2 ?? {x: 0, y: 0};

    // Calculate the default center position (midpoint between control points 1 and 2)
    const defaultCenter = StrandModel.midpoint(controlPoint1, controlPoint2);

    let newControlPointCenter = strand.controlPointCenter ?? defaultCenter;
    let newControlPointCenterLocked = strand.controlPointCenterLocked ?? false;

    // Check if center point is at its default position (unlock if very close)
    // Desktop strand.py lines 466-474
    if (newControlPointCenterLocked && strand.controlPointCenter) {
      const dx = strand.controlPointCenter.x - defaultCenter.x;
      const dy = strand.controlPointCenter.y - defaultCenter.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 0.5) {
        // Within half a pixel
        newControlPointCenterLocked = false;
      }
    }

    // Only recalculate center if not locked
    if (!newControlPointCenterLocked) {
      newControlPointCenter = defaultCenter;
    }

    return {
      ...strand,
      controlPointCenter: newControlPointCenter,
      controlPointCenterLocked: newControlPointCenterLocked,
    };
  }
}
