// Attached Strand model - Handles strand attachment
// Ported from src/attached_strand.py

import {Strand, Point, StrandSegment} from '../types';
import {StrandModel} from './Strand';

export interface AttachmentPoint {
  strandId: string;
  segmentIndex: number;
  t: number; // Parameter along the segment (0 to 1)
  attachmentSide?: 0 | 1;
}

export interface AttachedStrand extends Strand {
  attachments: {
    start?: AttachmentPoint;
    end?: AttachmentPoint;
  };
  parentId?: string;
  attachmentSide?: 0 | 1;
  angle?: number;
  length?: number;
  minLength?: number;
  shadowOnly?: boolean;
  hasCircles?: [boolean, boolean];
  startAttached?: boolean;
  endAttached?: boolean;
}

export class AttachedStrandModel {
  /**
   * Create an attached strand
   */
  static create(
    baseStrand: Strand,
    startAttachment?: AttachmentPoint,
    endAttachment?: AttachmentPoint,
  ): AttachedStrand {
    return {
      ...baseStrand,
      attachments: {
        start: startAttachment,
        end: endAttachment,
      },
      startAttached: Boolean(startAttachment),
      endAttached: Boolean(endAttachment),
      hasCircles: baseStrand.hasCircles ?? [true, false],
    };
  }

  /**
   * Create an attached strand derived from a parent strand and attachment side.
   * Uses createInitial() to match desktop behavior where control points start at start position.
   * Desktop attached_strand.py __init__ lines 15-50
   */
  static createFromParent(
    parent: Strand,
    startPoint: Point,
    attachmentSide: 0 | 1,
  ): AttachedStrand {
    // Use createInitial instead of createStraight to match desktop behavior
    // Desktop attached_strand.py creates strand with zero initial length
    const base = StrandModel.createInitial(
      `strand-${Date.now()}`,
      startPoint,
      {
        color: parent.style.color,
        strokeColor: parent.style.strokeColor,
        strokeWidth: parent.style.strokeWidth,
        width: parent.style.width,
        shadowEnabled: parent.style.shadowEnabled,
        shadowColor: parent.style.shadowColor,
        shadowOffset: parent.style.shadowOffset,
        shadowBlur: parent.style.shadowBlur,
      },
    );

    return {
      ...base,
      parentId: parent.id,
      attachmentSide,
      angle: 0,
      length: 0,
      minLength: 40,
      // Match desktop attached_strand.py line 37: has_circles = [True, False]
      hasCircles: [true, false],
      shadowOnly: false,
      startAttached: true,
      endAttached: false,
      isStartSide: true,
      // Inherit curvature parameters from parent (desktop attached_strand.py lines 43-46)
      curveResponseExponent: parent.curveResponseExponent ?? 1.5,
      controlPointBaseFraction: parent.controlPointBaseFraction ?? 0.4,
      distanceMultiplier: parent.distanceMultiplier ?? 1.2,
      attachments: {
        start: {
          strandId: parent.id,
          segmentIndex: 0,
          t: attachmentSide === 0 ? 0 : 1,
          attachmentSide,
        },
      },
    };
  }

  /**
   * Check if a strand is attached
   */
  static isAttached(strand: Strand | AttachedStrand): strand is AttachedStrand {
    return 'attachments' in strand;
  }

  /**
   * Attach strand start to another strand
   */
  static attachStart(
    strand: AttachedStrand,
    attachment: AttachmentPoint,
  ): AttachedStrand {
    return {
      ...strand,
      attachments: {
        ...strand.attachments,
        start: attachment,
      },
    };
  }

  /**
   * Attach strand end to another strand
   */
  static attachEnd(
    strand: AttachedStrand,
    attachment: AttachmentPoint,
  ): AttachedStrand {
    return {
      ...strand,
      attachments: {
        ...strand.attachments,
        end: attachment,
      },
    };
  }

  /**
   * Detach strand start
   */
  static detachStart(strand: AttachedStrand): AttachedStrand {
    return {
      ...strand,
      attachments: {
        ...strand.attachments,
        start: undefined,
      },
    };
  }

  /**
   * Detach strand end
   */
  static detachEnd(strand: AttachedStrand): AttachedStrand {
    return {
      ...strand,
      attachments: {
        ...strand.attachments,
        end: undefined,
      },
    };
  }

  /**
   * Update attached strand positions based on parent strands
   */
  static updateAttachedPositions(
    strand: AttachedStrand,
    allStrands: Map<string, Strand>,
  ): AttachedStrand {
    let newSegments = [...strand.segments];
    let updatedStart = strand.start;
    let updatedEnd = strand.end;

    // Update start position if attached
    if (strand.attachments.start && newSegments.length > 0) {
      const parentStrand = allStrands.get(strand.attachments.start.strandId);
      if (parentStrand) {
        const attachPoint = StrandModel.getPointAt(
          parentStrand,
          strand.attachments.start.t,
        );
        if (attachPoint) {
          updatedStart = attachPoint;
          newSegments[0] = {
            ...newSegments[0],
            bezier: {
              ...newSegments[0].bezier,
              start: attachPoint,
            },
          };
        }
      }
    }

    // Update end position if attached
    if (strand.attachments.end && newSegments.length > 0) {
      const parentStrand = allStrands.get(strand.attachments.end.strandId);
      if (parentStrand) {
        const attachPoint = StrandModel.getPointAt(
          parentStrand,
          strand.attachments.end.t,
        );
        if (attachPoint) {
          const lastIndex = newSegments.length - 1;
          updatedEnd = attachPoint;
          newSegments[lastIndex] = {
            ...newSegments[lastIndex],
            bezier: {
              ...newSegments[lastIndex].bezier,
              end: attachPoint,
            },
          };
        }
      }
    }

    return {
      ...strand,
      segments: newSegments,
      start: updatedStart,
      end: updatedEnd,
    };
  }

  /**
   * Get all strands that are attached to a given strand
   */
  static getChildStrands(
    parentStrandId: string,
    allStrands: (Strand | AttachedStrand)[],
  ): AttachedStrand[] {
    return allStrands.filter(
      (s): s is AttachedStrand =>
        AttachedStrandModel.isAttached(s) &&
        (s.attachments.start?.strandId === parentStrandId ||
          s.attachments.end?.strandId === parentStrandId),
    );
  }
}
