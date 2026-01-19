// Masked Strand model - Handles strand masking (over/under effects)
// Ported from src/masked_strand.py

import {Strand, Point} from '../types';
import {distance, bezierPoint, closestPointOnBezier} from '../utils/bezier';

export interface MaskSegment {
  strandId: string;
  segmentIndex: number;
  tStart: number;
  tEnd: number;
  isOver: boolean; // true = this strand goes over, false = goes under
}

export interface MaskedStrand extends Strand {
  masks: MaskSegment[];
}

export class MaskedStrandModel {
  /**
   * Create a masked strand
   */
  static create(baseStrand: Strand, masks: MaskSegment[] = []): MaskedStrand {
    return {
      ...baseStrand,
      masks,
    };
  }

  /**
   * Check if a strand is masked
   */
  static isMasked(strand: Strand | MaskedStrand): strand is MaskedStrand {
    return 'masks' in strand && Array.isArray(strand.masks);
  }

  /**
   * Add a mask to a strand
   */
  static addMask(strand: MaskedStrand, mask: MaskSegment): MaskedStrand {
    return {
      ...strand,
      masks: [...strand.masks, mask],
    };
  }

  /**
   * Remove a mask from a strand
   */
  static removeMask(strand: MaskedStrand, index: number): MaskedStrand {
    return {
      ...strand,
      masks: strand.masks.filter((_, i) => i !== index),
    };
  }

  /**
   * Clear all masks from a strand
   */
  static clearMasks(strand: MaskedStrand): MaskedStrand {
    return {
      ...strand,
      masks: [],
    };
  }

  /**
   * Find intersections between two strands
   */
  static findIntersections(
    strand1: Strand,
    strand2: Strand,
    threshold: number = 10,
  ): Array<{
    strand1Segment: number;
    strand1T: number;
    strand2Segment: number;
    strand2T: number;
    point: Point;
  }> {
    const intersections: Array<{
      strand1Segment: number;
      strand1T: number;
      strand2Segment: number;
      strand2T: number;
      point: Point;
    }> = [];

    // Check each segment of strand1 against each segment of strand2
    strand1.segments.forEach((seg1, seg1Index) => {
      strand2.segments.forEach((seg2, seg2Index) => {
        // Sample points along both segments
        for (let i = 0; i <= 50; i++) {
          const t1 = i / 50;
          const pt1 = bezierPoint(seg1.bezier, t1);

          // Find closest point on seg2
          const closest = closestPointOnBezier(seg2.bezier, pt1, 50);

          if (closest.distance < threshold) {
            // Found an intersection
            intersections.push({
              strand1Segment: seg1Index,
              strand1T: t1,
              strand2Segment: seg2Index,
              strand2T: closest.t,
              point: pt1,
            });
          }
        }
      });
    });

    // Merge nearby intersections
    return MaskedStrandModel.mergeIntersections(intersections, threshold * 2);
  }

  /**
   * Merge nearby intersections to avoid duplicates
   */
  private static mergeIntersections(
    intersections: Array<{
      strand1Segment: number;
      strand1T: number;
      strand2Segment: number;
      strand2T: number;
      point: Point;
    }>,
    mergeThreshold: number,
  ): Array<{
    strand1Segment: number;
    strand1T: number;
    strand2Segment: number;
    strand2T: number;
    point: Point;
  }> {
    if (intersections.length === 0) {
      return [];
    }

    const merged: typeof intersections = [intersections[0]];

    for (let i = 1; i < intersections.length; i++) {
      const current = intersections[i];
      let shouldMerge = false;

      for (const existing of merged) {
        if (distance(current.point, existing.point) < mergeThreshold) {
          shouldMerge = true;
          break;
        }
      }

      if (!shouldMerge) {
        merged.push(current);
      }
    }

    return merged;
  }

  /**
   * Auto-generate masks based on intersections with another strand
   */
  static autoMask(
    strand: MaskedStrand,
    otherStrand: Strand,
    isOver: boolean,
  ): MaskedStrand {
    const intersections = MaskedStrandModel.findIntersections(strand, otherStrand);

    if (intersections.length === 0) {
      return strand;
    }

    // Create mask segments for each intersection
    const newMasks: MaskSegment[] = intersections.map(intersection => ({
      strandId: otherStrand.id,
      segmentIndex: intersection.strand1Segment,
      tStart: Math.max(0, intersection.strand1T - 0.05),
      tEnd: Math.min(1, intersection.strand1T + 0.05),
      isOver,
    }));

    return {
      ...strand,
      masks: [...strand.masks, ...newMasks],
    };
  }

  /**
   * Toggle mask direction (over/under)
   */
  static toggleMaskDirection(strand: MaskedStrand, maskIndex: number): MaskedStrand {
    return {
      ...strand,
      masks: strand.masks.map((mask, i) =>
        i === maskIndex ? {...mask, isOver: !mask.isOver} : mask,
      ),
    };
  }

  /**
   * Get mask at a specific segment and parameter
   */
  static getMaskAt(
    strand: MaskedStrand,
    segmentIndex: number,
    t: number,
  ): MaskSegment | null {
    return (
      strand.masks.find(
        mask =>
          mask.segmentIndex === segmentIndex &&
          t >= mask.tStart &&
          t <= mask.tEnd,
      ) || null
    );
  }
}
