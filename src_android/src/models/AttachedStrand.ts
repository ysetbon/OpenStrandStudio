// Attached Strand model - Handles strand attachment
// Ported from src/attached_strand.py

import {Strand, Point, StrandSegment} from '../types';
import {StrandModel} from './Strand';

export interface AttachmentPoint {
  strandId: string;
  segmentIndex: number;
  t: number; // Parameter along the segment (0 to 1)
}

export interface AttachedStrand extends Strand {
  attachments: {
    start?: AttachmentPoint;
    end?: AttachmentPoint;
  };
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

    // Update start position if attached
    if (strand.attachments.start && newSegments.length > 0) {
      const parentStrand = allStrands.get(strand.attachments.start.strandId);
      if (parentStrand) {
        const attachPoint = StrandModel.getPointAt(
          parentStrand,
          strand.attachments.start.t,
        );
        if (attachPoint) {
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
