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
  /**
   * Create a new strand with default styling
   */
  static create(
    id: string,
    segments: StrandSegment[] = [],
    style?: Partial<StrandStyle>,
  ): Strand {
    const defaultStyle: StrandStyle = {
      color: '#8B4513',
      width: 20,
      shadowEnabled: true,
      shadowColor: 'rgba(0, 0, 0, 0.5)',
      shadowOffset: {x: 2, y: 2},
      shadowBlur: 4,
    };

    return {
      id,
      segments,
      style: {...defaultStyle, ...style},
      closed: false,
      visible: true,
      locked: false,
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

    return StrandModel.create(id, [segment], style);
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
    return {
      ...strand,
      style: {
        ...strand.style,
        ...style,
      },
    };
  }
}
