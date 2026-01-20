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
  if (strand.isHidden) {
    return false;
  }
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
        if (strand.visible && !strand.isHidden && isPointNearStrand(strand, point, threshold)) {
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
        if (strand.visible && !strand.isHidden && isPointNearStrand(strand, point, threshold)) {
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
  if (strand.isHidden) {
    return false;
  }
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

/**
 * Check if a strand side is attachable (has no circle/connection)
 * Matches desktop attach_mode.py lines 870-881
 */
function isSideAttachable(strand: Strand, side: 0 | 1): boolean {
  // Check hasCircles array - if the side has a circle, it's not attachable
  const hasCircles = strand.hasCircles ?? [false, false];

  // For AttachedStrands, start side (0) is NEVER attachable (already attached to parent)
  // This matches desktop attach_mode.py line 872: start_attachable = False for AttachedStrand
  if (strand.startAttached && side === 0) {
    return false;
  }

  // Side is attachable if it doesn't have a circle (not already connected)
  return !hasCircles[side];
}

/**
 * Find endpoint attachment with desktop-compatible behavior
 * Matches desktop attach_mode.py get_attachment_area() and try_attach_to_strand()
 * Uses 60px radius (desktop uses 120/2 = 60px circle radius)
 */
export function findEndpointAttachment(
  layers: (Layer | GroupLayer)[],
  point: Point,
  threshold: number = 60, // Desktop uses 120px diameter = 60px radius
): {
  strand: Strand;
  layerId: string;
  attachmentSide: 0 | 1;
  segmentIndex: number;
  t: number;
} | null {
  let best: {
    strand: Strand;
    layerId: string;
    attachmentSide: 0 | 1;
    segmentIndex: number;
    t: number;
    distance: number;
  } | null = null;

  for (let i = layers.length - 1; i >= 0; i--) {
    const layer = layers[i];
    if (!layer.visible) {
      continue;
    }

    if ('layers' in layer) {
      const result = findEndpointAttachment(layer.layers, point, threshold);
      if (result) {
        const startDist = distance(
          result.attachmentSide === 0
            ? result.strand.segments[result.segmentIndex]?.bezier.start ?? point
            : result.strand.segments[result.segmentIndex]?.bezier.end ?? point,
          point,
        );
        if (!best || startDist < best.distance) {
          best = {...result, distance: startDist};
        }
      }
      continue;
    }

    for (let j = layer.strands.length - 1; j >= 0; j--) {
      const strand = layer.strands[j];
      if (!strand.visible || strand.isHidden || strand.segments.length === 0) {
        continue;
      }

      const firstSeg = strand.segments[0];
      const lastSeg = strand.segments[strand.segments.length - 1];

      // Check start point - only if attachable (no circle there)
      // Matches desktop attach_mode.py line 877
      const startDist = distance(firstSeg.bezier.start, point);
      if (startDist <= threshold && isSideAttachable(strand, 0) && (!best || startDist < best.distance)) {
        best = {
          strand,
          layerId: layer.id,
          attachmentSide: 0,
          segmentIndex: 0,
          t: 0,
          distance: startDist,
        };
      }

      // Check end point - only if attachable (no circle there)
      // Matches desktop attach_mode.py line 880
      const endDist = distance(lastSeg.bezier.end, point);
      if (endDist <= threshold && isSideAttachable(strand, 1) && (!best || endDist < best.distance)) {
        best = {
          strand,
          layerId: layer.id,
          attachmentSide: 1,
          segmentIndex: strand.segments.length - 1,
          t: 1,
          distance: endDist,
        };
      }
    }
  }

  if (!best) {
    return null;
  }

  const {distance: _distance, ...result} = best;
  return result;
}

/**
 * Find strand endpoint for move mode (120px square selection area)
 * Matches desktop move_mode.py get_start_area() and get_end_area()
 */
export function findStrandEndpointForMove(
  layers: (Layer | GroupLayer)[],
  point: Point,
  areaSize: number = 120,
): {
  strand: Strand;
  layerId: string;
  side: 0 | 1;
  endpoint: Point;
} | null {
  const halfSize = areaSize / 2;

  for (let i = layers.length - 1; i >= 0; i--) {
    const layer = layers[i];
    if (!layer.visible) {
      continue;
    }

    if ('layers' in layer) {
      const result = findStrandEndpointForMove(layer.layers, point, areaSize);
      if (result) {
        return result;
      }
      continue;
    }

    for (let j = layer.strands.length - 1; j >= 0; j--) {
      const strand = layer.strands[j];
      if (!strand.visible || strand.isHidden || strand.locked || strand.segments.length === 0) {
        continue;
      }

      const firstSeg = strand.segments[0];
      const lastSeg = strand.segments[strand.segments.length - 1];
      const startPoint = firstSeg.bezier.start;
      const endPoint = lastSeg.bezier.end;

      // Check start area (120x120 square)
      if (
        point.x >= startPoint.x - halfSize &&
        point.x <= startPoint.x + halfSize &&
        point.y >= startPoint.y - halfSize &&
        point.y <= startPoint.y + halfSize
      ) {
        // Don't allow moving start of attached strands (they're connected to parent)
        if (!strand.startAttached) {
          return {strand, layerId: layer.id, side: 0, endpoint: startPoint};
        }
      }

      // Check end area (120x120 square)
      if (
        point.x >= endPoint.x - halfSize &&
        point.x <= endPoint.x + halfSize &&
        point.y >= endPoint.y - halfSize &&
        point.y <= endPoint.y + halfSize
      ) {
        return {strand, layerId: layer.id, side: 1, endpoint: endPoint};
      }
    }
  }

  return null;
}

/**
 * Get all attachable endpoints for visual display
 * Returns endpoints that can accept new strand attachments
 */
export function getAttachableEndpoints(
  layers: (Layer | GroupLayer)[],
): Array<{point: Point; strand: Strand; side: 0 | 1}> {
  const endpoints: Array<{point: Point; strand: Strand; side: 0 | 1}> = [];

  function searchLayer(layer: Layer | GroupLayer) {
    if (!layer.visible) {
      return;
    }

    if ('layers' in layer) {
      layer.layers.forEach(searchLayer);
      return;
    }

    for (const strand of layer.strands) {
      if (!strand.visible || strand.isHidden || strand.segments.length === 0) {
        continue;
      }

      const firstSeg = strand.segments[0];
      const lastSeg = strand.segments[strand.segments.length - 1];

      // Check start point
      if (isSideAttachable(strand, 0)) {
        endpoints.push({point: firstSeg.bezier.start, strand, side: 0});
      }

      // Check end point
      if (isSideAttachable(strand, 1)) {
        endpoints.push({point: lastSeg.bezier.end, strand, side: 1});
      }
    }
  }

  layers.forEach(searchLayer);
  return endpoints;
}
