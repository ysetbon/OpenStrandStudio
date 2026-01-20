// Bezier curve mathematics utilities
// Ported from the Python implementation in src/strand.py

import {Point, BezierCurve} from '../types';

/**
 * Calculate a point on a cubic Bezier curve at parameter t (0 to 1)
 */
export function bezierPoint(curve: BezierCurve, t: number): Point {
  const {start, control1, control2, end} = curve;
  const mt = 1 - t;
  const mt2 = mt * mt;
  const mt3 = mt2 * mt;
  const t2 = t * t;
  const t3 = t2 * t;

  return {
    x:
      mt3 * start.x +
      3 * mt2 * t * control1.x +
      3 * mt * t2 * control2.x +
      t3 * end.x,
    y:
      mt3 * start.y +
      3 * mt2 * t * control1.y +
      3 * mt * t2 * control2.y +
      t3 * end.y,
  };
}

/**
 * Calculate the tangent vector at parameter t on a cubic Bezier curve
 */
export function bezierTangent(curve: BezierCurve, t: number): Point {
  const {start, control1, control2, end} = curve;
  const mt = 1 - t;
  const mt2 = mt * mt;
  const t2 = t * t;

  return {
    x:
      3 * mt2 * (control1.x - start.x) +
      6 * mt * t * (control2.x - control1.x) +
      3 * t2 * (end.x - control2.x),
    y:
      3 * mt2 * (control1.y - start.y) +
      6 * mt * t * (control2.y - control1.y) +
      3 * t2 * (end.y - control2.y),
  };
}

/**
 * Calculate the normal vector at parameter t on a cubic Bezier curve
 */
export function bezierNormal(curve: BezierCurve, t: number): Point {
  const tangent = bezierTangent(curve, t);
  const length = Math.sqrt(tangent.x * tangent.x + tangent.y * tangent.y);

  if (length === 0) {
    return {x: 0, y: 0};
  }

  // Perpendicular to tangent (rotate 90 degrees)
  return {
    x: -tangent.y / length,
    y: tangent.x / length,
  };
}

/**
 * Calculate the approximate length of a Bezier curve using adaptive subdivision
 */
export function bezierLength(curve: BezierCurve, subdivisions: number = 100): number {
  let length = 0;
  let prevPoint = bezierPoint(curve, 0);

  for (let i = 1; i <= subdivisions; i++) {
    const t = i / subdivisions;
    const point = bezierPoint(curve, t);
    const dx = point.x - prevPoint.x;
    const dy = point.y - prevPoint.y;
    length += Math.sqrt(dx * dx + dy * dy);
    prevPoint = point;
  }

  return length;
}

/**
 * Split a Bezier curve at parameter t into two curves
 */
export function splitBezier(
  curve: BezierCurve,
  t: number,
): [BezierCurve, BezierCurve] {
  const {start, control1, control2, end} = curve;

  // De Casteljau's algorithm
  const p01 = lerp(start, control1, t);
  const p12 = lerp(control1, control2, t);
  const p23 = lerp(control2, end, t);

  const p012 = lerp(p01, p12, t);
  const p123 = lerp(p12, p23, t);

  const split = lerp(p012, p123, t);

  const curve1: BezierCurve = {
    start: start,
    control1: p01,
    control2: p012,
    end: split,
  };

  const curve2: BezierCurve = {
    start: split,
    control1: p123,
    control2: p23,
    end: end,
  };

  return [curve1, curve2];
}

/**
 * Linear interpolation between two points
 */
function lerp(p1: Point, p2: Point, t: number): Point {
  return {
    x: p1.x + (p2.x - p1.x) * t,
    y: p1.y + (p2.y - p1.y) * t,
  };
}

/**
 * Calculate distance between two points
 */
export function distance(p1: Point, p2: Point): number {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Find the closest point on a Bezier curve to a given point
 * Returns the parameter t and the distance
 */
export function closestPointOnBezier(
  curve: BezierCurve,
  point: Point,
  samples: number = 100,
): {t: number; distance: number; point: Point} {
  let minDist = Infinity;
  let minT = 0;
  let closestPt = bezierPoint(curve, 0);

  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    const pt = bezierPoint(curve, t);
    const dist = distance(pt, point);

    if (dist < minDist) {
      minDist = dist;
      minT = t;
      closestPt = pt;
    }
  }

  return {t: minT, distance: minDist, point: closestPt};
}

/**
 * Calculate the bounding box of a Bezier curve
 */
export function bezierBoundingBox(curve: BezierCurve): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} {
  const samples = 50;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    const pt = bezierPoint(curve, t);
    minX = Math.min(minX, pt.x);
    minY = Math.min(minY, pt.y);
    maxX = Math.max(maxX, pt.x);
    maxY = Math.max(maxY, pt.y);
  }

  return {minX, minY, maxX, maxY};
}

/**
 * Calculate angle in radians between two points
 */
export function angleBetweenPoints(p1: Point, p2: Point): number {
  return Math.atan2(p2.y - p1.y, p2.x - p1.x);
}

/**
 * Rotate a point around a center by an angle (in radians)
 */
export function rotatePoint(point: Point, center: Point, angle: number): Point {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const dx = point.x - center.x;
  const dy = point.y - center.y;

  return {
    x: center.x + dx * cos - dy * sin,
    y: center.y + dx * sin + dy * cos,
  };
}

/**
 * Snap a value to a grid
 */
export function snapToGrid(value: number, gridSize: number): number {
  return Math.round(value / gridSize) * gridSize;
}

/**
 * Snap a point to a grid
 */
export function snapPointToGrid(point: Point, gridSize: number): Point {
  return {
    x: snapToGrid(point.x, gridSize),
    y: snapToGrid(point.y, gridSize),
  };
}
