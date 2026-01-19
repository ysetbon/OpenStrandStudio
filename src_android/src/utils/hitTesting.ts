// Hit testing utilities for strand selection
import {Point, Strand, Layer, GroupLayer} from '../types';
import {bezierPoint, distance, closestPointOnBezier} from './bezier';

/**
 * Check if a point is near a strand (for selection)
 */
export function isPointNearStrand(
  strand: Strand,
  point: Point,
  threshold: number = 30,
): boolean {
  for (const segment of strand.segments) {
    const result = closestPointOnBezier(segment.bezier, point, 50);
    if (result.distance <= threshold) {
      return true;
    }
  }
  return false;
}

/**
 * Find the first strand at a given point
 */
export function findStrandAtPoint(
  layers: (Layer | GroupLayer)[],
  point: Point,
  threshold: number = 30,
): {strand: Strand; layerId: string} | null {
  // Search in reverse order (top to bottom)
  for (let i = layers.length - 1; i >= 0; i--) {
    const layer = layers[i];

    if (!layer.visible) {
      continue;
    }

    if ('layers' in layer) {
      // Group layer - recursively search
      const result = findStrandAtPoint(layer.layers, point, threshold);
      if (result) {
        return result;
      }
    } else {
      // Regular layer - check strands in reverse order
      for (let j = layer.strands.length - 1; j >= 0; j--) {
        const strand = layer.strands[j];
        if (strand.visible && isPointNearStrand(strand, point, threshold)) {
          return {strand, layerId: layer.id};
        }
      }
    }
  }

  return null;
}

/**
 * Find all strands at a given point
 */
export function findAllStrandsAtPoint(
  layers: (Layer | GroupLayer)[],
  point: Point,
  threshold: number = 30,
): Array<{strand: Strand; layerId: string}> {
  const results: Array<{strand: Strand; layerId: string}> = [];

  function searchLayer(layer: Layer | GroupLayer) {
    if (!layer.visible) {
      return;
    }

    if ('layers' in layer) {
      layer.layers.forEach(searchLayer);
    } else {
      layer.strands.forEach(strand => {
        if (strand.visible && isPointNearStrand(strand, point, threshold)) {
          results.push({strand, layerId: layer.id});
        }
      });
    }
  }

  layers.forEach(searchLayer);
  return results;
}

/**
 * Find the closest control point to a point
 */
export function findClosestControlPoint(
  strand: Strand,
  point: Point,
  threshold: number = 30,
): {segmentIndex: number; pointType: 'start' | 'control1' | 'control2' | 'end'} | null {
  let minDist = threshold;
  let result: {segmentIndex: number; pointType: 'start' | 'control1' | 'control2' | 'end'} | null = null;

  strand.segments.forEach((segment, index) => {
    const points = [
      {type: 'start' as const, point: segment.bezier.start},
      {type: 'control1' as const, point: segment.bezier.control1},
      {type: 'control2' as const, point: segment.bezier.control2},
      {type: 'end' as const, point: segment.bezier.end},
    ];

    points.forEach(({type, point: pt}) => {
      const dist = distance(pt, point);
      if (dist < minDist) {
        minDist = dist;
        result = {segmentIndex: index, pointType: type};
      }
    });
  });

  return result;
}

/**
 * Check if point is within a rectangular selection area
 */
export function isPointInRect(
  point: Point,
  rectStart: Point,
  rectEnd: Point,
): boolean {
  const minX = Math.min(rectStart.x, rectEnd.x);
  const maxX = Math.max(rectStart.x, rectEnd.x);
  const minY = Math.min(rectStart.y, rectEnd.y);
  const maxY = Math.max(rectStart.y, rectEnd.y);

  return point.x >= minX && point.x <= maxX && point.y >= minY && point.y <= maxY;
}

/**
 * Check if a strand intersects with a rectangular selection area
 */
export function isStrandInRect(
  strand: Strand,
  rectStart: Point,
  rectEnd: Point,
): boolean {
  // Sample points along the strand
  for (const segment of strand.segments) {
    for (let i = 0; i <= 20; i++) {
      const t = i / 20;
      const pt = bezierPoint(segment.bezier, t);
      if (isPointInRect(pt, rectStart, rectEnd)) {
        return true;
      }
    }
  }
  return false;
}
