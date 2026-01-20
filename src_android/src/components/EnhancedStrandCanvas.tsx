// Enhanced Strand Canvas with full interaction support
import React, {useState, useCallback, useRef} from 'react';
import {View, StyleSheet, Dimensions} from 'react-native';
import Svg, {Path, G, Circle, Rect} from 'react-native-svg';
import {GestureDetector, Gesture} from 'react-native-gesture-handler';
import {Strand, Point, Layer, GroupLayer, CanvasState, InteractionMode} from '../types';
import {bezierPoint} from '../utils/bezier';
import {findStrandAtPoint, findClosestControlPoint, findEndpointAttachment, findStrandEndpointForMove, getAttachableEndpoints} from '../utils/hitTesting';
import {StrandModel} from '../models/Strand';
import {MaskedStrandModel, MaskedStrand} from '../models/MaskedStrand';
import {AttachedStrandModel} from '../models/AttachedStrand';
import DrawingMode from './DrawingMode';

interface EnhancedStrandCanvasProps {
  canvasState: CanvasState;
  currentMode: InteractionMode;
  currentColor: string;
  currentWidth: number;
  showControlPoints?: boolean;
  showShadows?: boolean;
  onStrandSelected?: (strandId: string, layerId: string) => void;
  onStrandMoveStart?: (strandId: string, layerId: string) => void;
  onStrandMoved?: (strandId: string, layerId: string, offset: Point) => void;
  onStrandMoveEnd?: (strandId: string, layerId: string) => void;
  onStrandCreated?: (layerId: string, strand: Strand) => void;
  onCanvasPan?: (offset: Point) => void;
  onControlPointMove?: (strandId: string, layerId: string, segmentIndex: number, pointType: string, newPos: Point) => void;
  // For MOVE mode - update strand endpoint position
  onStrandEndpointMove?: (strandId: string, layerId: string, side: 0 | 1, newPos: Point) => void;
  // For updating parent strand when child is attached
  onStrandUpdated?: (layerId: string, strand: Strand) => void;
}

const EnhancedStrandCanvas: React.FC<EnhancedStrandCanvasProps> = ({
  canvasState,
  currentMode,
  currentColor,
  currentWidth,
  showControlPoints = true,
  showShadows = true,
  onStrandSelected,
  onStrandMoveStart,
  onStrandMoved,
  onStrandMoveEnd,
  onStrandCreated,
  onCanvasPan,
  onControlPointMove,
  onStrandEndpointMove,
  onStrandUpdated,
}) => {
  const {width: screenWidth, height: screenHeight} = Dimensions.get('window');
  const [dimensions] = useState({width: screenWidth, height: screenHeight});
  const [draggedStrand, setDraggedStrand] = useState<{id: string; layerId: string} | null>(null);
  const [dragStartPos, setDragStartPos] = useState<Point | null>(null);
  const [selectionRect, setSelectionRect] = useState<{start: Point; end: Point} | null>(null);
  const [editingControlPoint, setEditingControlPoint] = useState<{
    strandId: string;
    layerId: string;
    segmentIndex: number;
    pointType: string;
  } | null>(null);
  // For ATTACH mode - creating new strands
  const [newStrandPreview, setNewStrandPreview] = useState<{start: Point; end: Point} | null>(null);

  // For MOVE mode - moving strand endpoints
  const [movingEndpoint, setMovingEndpoint] = useState<{
    strand: Strand;
    layerId: string;
    side: 0 | 1;
    originalPoint: Point;
  } | null>(null);

  // Use refs to avoid stale closure issues in gesture handlers
  const attachStartRef = useRef<Point | null>(null);
  const isAttachingRef = useRef(false);
  const dragStartPosRef = useRef<Point | null>(null);
  const attachStartTargetRef = useRef<{
    strand: Strand;
    layerId: string;
    attachmentSide: 0 | 1;
    segmentIndex: number;
    t: number;
  } | null>(null);

  // For MOVE mode refs
  const isMovingEndpointRef = useRef(false);
  const movingEndpointRef = useRef<{
    strand: Strand;
    layerId: string;
    side: 0 | 1;
    originalPoint: Point;
  } | null>(null);

  // Convert Bezier curve to SVG path data
  // Matches desktop strand.py _build_curve_profile() behavior:
  // When control points are at start position, render as a line instead of a curve
  const bezierToPathData = (bezier: any): string => {
    // Check if both control points are at the start position (within 1 pixel tolerance)
    // This matches desktop strand.py lines 1206-1213
    const cp1AtStart = Math.abs(bezier.control1.x - bezier.start.x) < 1.0 &&
                       Math.abs(bezier.control1.y - bezier.start.y) < 1.0;
    const cp2AtStart = Math.abs(bezier.control2.x - bezier.start.x) < 1.0 &&
                       Math.abs(bezier.control2.y - bezier.start.y) < 1.0;

    if (cp1AtStart && cp2AtStart) {
      // Render as a straight line when control points are at start
      return `M ${bezier.start.x} ${bezier.start.y} L ${bezier.end.x} ${bezier.end.y}`;
    }

    // Otherwise render as cubic Bezier
    return `M ${bezier.start.x} ${bezier.start.y} C ${bezier.control1.x} ${bezier.control1.y}, ${bezier.control2.x} ${bezier.control2.y}, ${bezier.end.x} ${bezier.end.y}`;
  };

  const resolveAttachmentPoint = (target: {
    strand: Strand;
    attachmentSide: 0 | 1;
    segmentIndex: number;
  }): Point => {
    const segment = target.strand.segments[target.segmentIndex];
    if (!segment) {
      return {x: 0, y: 0};
    }
    return target.attachmentSide === 0 ? segment.bezier.start : segment.bezier.end;
  };

  // Render a single strand with masking support
  const renderStrand = useCallback((strand: Strand, layerId: string, layer: Layer) => {
    if (!strand.visible || !layer.visible) {
      return null;
    }

    const isSelected = strand.id === canvasState.selectedStrandId;
    const isMasked = MaskedStrandModel.isMasked(strand);

    // Render each segment separately for masking
    const segments = strand.segments.map((seg, segIndex) => {
      const pathData = bezierToPathData(seg.bezier);

      // Check if this segment has masks
      let maskData: any = null;
      if (isMasked) {
        const maskedStrand = strand as MaskedStrand;
        maskData = maskedStrand.masks.filter(m => m.segmentIndex === segIndex);
      }

      return (
        <G key={`${strand.id}-${segIndex}`}>
          {/* Shadow layer */}
          {showShadows && strand.style.shadowEnabled && (
            <Path
              d={pathData}
              stroke={strand.style.shadowColor}
              strokeWidth={strand.style.width}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.5 * layer.opacity}
              translateX={strand.style.shadowOffset.x}
              translateY={strand.style.shadowOffset.y}
            />
          )}

          {/* Stroke/border layer */}
          <Path
            d={pathData}
            stroke={strand.style.strokeColor}
            strokeWidth={strand.style.width + strand.style.strokeWidth * 2}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={layer.opacity}
          />

          {/* Main fill strand */}
          <Path
            d={pathData}
            stroke={strand.style.color}
            strokeWidth={strand.style.width}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={layer.opacity}
          />

          {/* Mask visualization (gaps for under-crossings) */}
          {maskData && maskData.length > 0 && maskData.map((mask: any, maskIdx: number) => {
            if (!mask.isOver) {
              // Draw white gap for under-crossing
              const gapStart = bezierPoint(seg.bezier, mask.tStart);
              const gapEnd = bezierPoint(seg.bezier, mask.tEnd);
              return (
                <Path
                  key={`mask-${maskIdx}`}
                  d={`M ${gapStart.x} ${gapStart.y} L ${gapEnd.x} ${gapEnd.y}`}
                  stroke="#ffffff"
                  strokeWidth={strand.style.width + 4}
                  strokeLinecap="round"
                  opacity={layer.opacity}
                />
              );
            }
            return null;
          })}
        </G>
      );
    });

    return (
      <G key={strand.id}>
        {segments}

        {/* Selection highlight */}
        {isSelected && strand.segments.map((seg, segIndex) => {
          const pathData = bezierToPathData(seg.bezier);
          return (
            <Path
              key={`select-${segIndex}`}
              d={pathData}
              stroke="#00ffff"
              strokeWidth={strand.style.width + 4}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.3}
            />
          );
        })}

        {/* Control points (when selected) */}
        {showControlPoints && isSelected && currentMode === InteractionMode.SELECT && strand.segments.map((seg, segIndex) => (
          <G key={`controls-${segIndex}`}>
            <Circle cx={seg.bezier.start.x} cy={seg.bezier.start.y} r={6} fill="#00ff00" opacity={0.7} />
            <Circle cx={seg.bezier.control1.x} cy={seg.bezier.control1.y} r={4} fill="#ffff00" opacity={0.7} />
            <Circle cx={seg.bezier.control2.x} cy={seg.bezier.control2.y} r={4} fill="#ffff00" opacity={0.7} />
            <Circle cx={seg.bezier.end.x} cy={seg.bezier.end.y} r={6} fill="#ff0000" opacity={0.7} />

            {/* Control lines */}
            <Path
              d={`M ${seg.bezier.start.x} ${seg.bezier.start.y} L ${seg.bezier.control1.x} ${seg.bezier.control1.y}`}
              stroke="#888888"
              strokeWidth={1}
              strokeDasharray="4,4"
              opacity={0.5}
            />
            <Path
              d={`M ${seg.bezier.end.x} ${seg.bezier.end.y} L ${seg.bezier.control2.x} ${seg.bezier.control2.y}`}
              stroke="#888888"
              strokeWidth={1}
              strokeDasharray="4,4"
              opacity={0.5}
            />
          </G>
        ))}
      </G>
    );
  }, [canvasState.selectedStrandId, currentMode, showControlPoints, showShadows]);

  // Render all strands from a layer
  const renderLayer = useCallback((layer: Layer | GroupLayer) => {
    if (!layer.visible) {
      return null;
    }

    if ('layers' in layer) {
      // Group layer
      return layer.layers.map(l => renderLayer(l));
    } else {
      // Regular layer
      return layer.strands.map(strand => renderStrand(strand, layer.id, layer));
    }
  }, [renderStrand]);

  // Render grid
  const renderGrid = useCallback(() => {
    if (!canvasState.gridEnabled) {
      return null;
    }

    const gridLines = [];
    const gridSize = canvasState.gridSize;

    for (let x = 0; x < dimensions.width; x += gridSize) {
      gridLines.push(
        <Path
          key={`v-${x}`}
          d={`M ${x} 0 L ${x} ${dimensions.height}`}
          stroke="#cccccc"
          strokeWidth={0.5}
          opacity={0.3}
        />,
      );
    }

    for (let y = 0; y < dimensions.height; y += gridSize) {
      gridLines.push(
        <Path
          key={`h-${y}`}
          d={`M 0 ${y} L ${dimensions.width} ${y}`}
          stroke="#cccccc"
          strokeWidth={0.5}
          opacity={0.3}
        />,
      );
    }

    return gridLines;
  }, [canvasState.gridEnabled, canvasState.gridSize, dimensions]);

  // Handle tap gesture (selection)
  const handleTap = useCallback((x: number, y: number) => {
    if (currentMode === InteractionMode.SELECT) {
      const result = findStrandAtPoint(canvasState.layers, {x, y});
      if (result && onStrandSelected) {
        onStrandSelected(result.strand.id, result.layerId);
      }
    }
  }, [currentMode, canvasState.layers, onStrandSelected]);

  // Gesture handlers
  const tapGesture = Gesture.Tap()
    .onEnd(e => {
      handleTap(e.x, e.y);
    })
    .runOnJS(true);

  const panGesture = Gesture.Pan()
    .minDistance(5) // Lower the minimum distance to start pan
    .onStart(e => {
      // Calculate the actual start position from the current position and translation
      // At onStart, translationX/Y are usually small (just past minDistance)
      const point = {x: e.x - e.translationX, y: e.y - e.translationY};

      // Store in ref immediately for reliable access
      dragStartPosRef.current = point;
      setDragStartPos(point);

      console.log('Pan onStart - mode:', currentMode, 'point:', point);

      if (currentMode === InteractionMode.ATTACH) {
        // Start creating a new strand - snap to nearby attachable endpoints (60px radius like desktop)
        // This matches desktop attach_mode.py get_attachment_area() with 120px diameter
        const attachTarget = findEndpointAttachment(canvasState.layers, point, 60);
        if (attachTarget) {
          const attachPoint = resolveAttachmentPoint(attachTarget);
          attachStartRef.current = attachPoint;
          attachStartTargetRef.current = attachTarget;
          setNewStrandPreview({start: attachPoint, end: {x: e.x, y: e.y}});
          console.log('ATTACH onStart - snapped to attachment point:', attachPoint, 'side:', attachTarget.attachmentSide);
        } else {
          // Free drawing (not attached to existing strand)
          attachStartRef.current = point;
          attachStartTargetRef.current = null;
          setNewStrandPreview({start: point, end: {x: e.x, y: e.y}});
          console.log('ATTACH onStart - free start point:', point);
        }
        isAttachingRef.current = true;
      } else if (currentMode === InteractionMode.MOVE) {
        // Desktop-style MOVE mode: detect strand endpoints using 120px square areas
        // Matches desktop move_mode.py get_start_area() and get_end_area()
        const endpointResult = findStrandEndpointForMove(canvasState.layers, point, 120);
        if (endpointResult) {
          // Moving a strand endpoint
          isMovingEndpointRef.current = true;
          movingEndpointRef.current = {
            strand: endpointResult.strand,
            layerId: endpointResult.layerId,
            side: endpointResult.side,
            originalPoint: endpointResult.endpoint,
          };
          setMovingEndpoint(movingEndpointRef.current);
          if (onStrandSelected) {
            onStrandSelected(endpointResult.strand.id, endpointResult.layerId);
          }
          if (onStrandMoveStart) {
            onStrandMoveStart(endpointResult.strand.id, endpointResult.layerId);
          }
          console.log('MOVE onStart - moving endpoint:', endpointResult.side, 'of strand:', endpointResult.strand.id);
        } else {
          // Fallback: try to select/move whole strand if not on endpoint
          const result = findStrandAtPoint(canvasState.layers, point);
          if (result) {
            setDraggedStrand({id: result.strand.id, layerId: result.layerId});
            if (onStrandSelected) {
              onStrandSelected(result.strand.id, result.layerId);
            }
            if (onStrandMoveStart) {
              onStrandMoveStart(result.strand.id, result.layerId);
            }
          }
        }
      } else if (currentMode === InteractionMode.SELECT && canvasState.selectedStrandId) {
        // Check if tapping on control point
        const selectedResult = findStrandAtPoint(canvasState.layers, point);
        if (selectedResult && selectedResult.strand.id === canvasState.selectedStrandId) {
          const cpResult = findClosestControlPoint(selectedResult.strand, point, 20);
          if (cpResult) {
            setEditingControlPoint({
              strandId: selectedResult.strand.id,
              layerId: selectedResult.layerId,
              segmentIndex: cpResult.segmentIndex,
              pointType: cpResult.pointType,
            });
          }
        }
      }
    })
    .onUpdate(e => {
      if (currentMode === InteractionMode.ATTACH && isAttachingRef.current && attachStartRef.current) {
        // Update the preview strand end point
        setNewStrandPreview({
          start: attachStartRef.current,
          end: {x: e.x, y: e.y},
        });
      } else if (currentMode === InteractionMode.MOVE && isMovingEndpointRef.current && movingEndpointRef.current) {
        // Desktop-style endpoint movement
        // Matches desktop move_mode.py mouseMoveEvent where strand endpoint is updated
        const newPos = {x: e.x, y: e.y};
        if (onStrandEndpointMove) {
          onStrandEndpointMove(
            movingEndpointRef.current.strand.id,
            movingEndpointRef.current.layerId,
            movingEndpointRef.current.side,
            newPos,
          );
        }
      } else if (currentMode === InteractionMode.MOVE && draggedStrand && dragStartPosRef.current) {
        // Fallback: whole strand translation
        const offset = {
          x: e.translationX,
          y: e.translationY,
        };
        if (onStrandMoved) {
          onStrandMoved(draggedStrand.id, draggedStrand.layerId, offset);
        }
      } else if (editingControlPoint && onControlPointMove) {
        const newPos = {x: e.x, y: e.y};
        onControlPointMove(
          editingControlPoint.strandId,
          editingControlPoint.layerId,
          editingControlPoint.segmentIndex,
          editingControlPoint.pointType,
          newPos,
        );
      } else if (currentMode === InteractionMode.SELECT && dragStartPosRef.current) {
        // Selection rectangle - use ref for reliable access
        setSelectionRect({
          start: dragStartPosRef.current,
          end: {x: e.x, y: e.y},
        });
      }
    })
    .onEnd(e => {
      console.log('Pan onEnd - mode:', currentMode, 'isAttaching:', isAttachingRef.current, 'startRef:', attachStartRef.current);

      // Create strand when ATTACH mode drag ends - use ref values
      // This mirrors desktop workflow: create initial → update endpoint → finalize geometry
      if (currentMode === InteractionMode.ATTACH && isAttachingRef.current && attachStartRef.current && onStrandCreated && canvasState.selectedLayerId) {
        const startAttachment = attachStartTargetRef.current;
        // Use 60px radius for end attachment too (desktop uses 120px diameter)
        const endAttachment = findEndpointAttachment(canvasState.layers, {x: e.x, y: e.y}, 60);
        const start = startAttachment ? resolveAttachmentPoint(startAttachment) : attachStartRef.current;
        const end = endAttachment ? resolveAttachmentPoint(endAttachment) : {x: e.x, y: e.y};
        const dist = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));

        console.log('Creating strand - start:', start, 'end:', end, 'dist:', dist, 'layerId:', canvasState.selectedLayerId);

        // Only create if dragged far enough (minimum 10 pixels for mobile touch)
        if (dist >= 10) {
          const baseStyle = startAttachment
            ? {
                color: startAttachment.strand.style.color,
                strokeColor: startAttachment.strand.style.strokeColor,
                strokeWidth: startAttachment.strand.style.strokeWidth,
                width: startAttachment.strand.style.width,
                shadowEnabled: startAttachment.strand.style.shadowEnabled,
                shadowColor: startAttachment.strand.style.shadowColor,
                shadowOffset: startAttachment.strand.style.shadowOffset,
                shadowBlur: startAttachment.strand.style.shadowBlur,
              }
            : {color: currentColor, width: currentWidth};

          // Phase 1: Create initial strand with control points at start (desktop behavior)
          // Matches desktop strand.py __init__ where control points start at start position
          let baseStrand = StrandModel.createInitial(
            `strand-${Date.now()}`,
            start,
            baseStyle,
          );

          // Phase 2: Update the endpoint (like desktop mouseMoveEvent updating strand.end)
          // Control points stay at start position - this is correct desktop behavior!
          // Desktop draws strands as straight lines when control points are at start
          // (see _build_curve_profile() mode='line' check in strand.py lines 1206-1213)
          baseStrand = StrandModel.updateEndpoint(baseStrand, end);

          // NOTE: Do NOT call updateControlPointsFromGeometry() here!
          // Desktop only calls that when loading from files, not during normal creation.
          // New strands should have control points at start, rendering as straight lines.

          let newStrand: Strand = baseStrand;

          if (startAttachment || endAttachment) {
            newStrand = AttachedStrandModel.create(
              baseStrand,
              startAttachment
                ? {
                    strandId: startAttachment.strand.id,
                    segmentIndex: startAttachment.segmentIndex,
                    t: startAttachment.t,
                    attachmentSide: startAttachment.attachmentSide,
                  }
                : undefined,
              endAttachment
                ? {
                    strandId: endAttachment.strand.id,
                    segmentIndex: endAttachment.segmentIndex,
                    t: endAttachment.t,
                    attachmentSide: endAttachment.attachmentSide,
                  }
                : undefined,
            );

            if (startAttachment) {
              newStrand.parentId = startAttachment.strand.id;
              newStrand.attachmentSide = startAttachment.attachmentSide;
              newStrand.startAttached = true;
              // Match desktop attached_strand.py: has_circles = [True, False]
              newStrand.hasCircles = [true, false];
              newStrand.isStartSide = false; // AttachedStrands have is_start_side = False (desktop line 939)

              // Update parent strand's hasCircles to mark this side as occupied
              // Matches desktop attach_mode.py line 943: parent_strand.has_circles[side] = True
              const updatedParent = {
                ...startAttachment.strand,
                hasCircles: [...(startAttachment.strand.hasCircles ?? [false, false])] as [boolean, boolean],
              };
              updatedParent.hasCircles[startAttachment.attachmentSide] = true;

              // Also add this strand to parent's attachedStrandIds
              updatedParent.attachedStrandIds = [
                ...(startAttachment.strand.attachedStrandIds ?? []),
                newStrand.id,
              ];

              // Notify parent update
              if (onStrandUpdated) {
                onStrandUpdated(startAttachment.layerId, updatedParent);
              }
            }
            if (endAttachment) {
              newStrand.endAttached = true;
              // Update end attachment parent's hasCircles too
              const updatedEndParent = {
                ...endAttachment.strand,
                hasCircles: [...(endAttachment.strand.hasCircles ?? [false, false])] as [boolean, boolean],
              };
              updatedEndParent.hasCircles[endAttachment.attachmentSide] = true;
              if (onStrandUpdated && endAttachment.layerId) {
                onStrandUpdated(endAttachment.layerId, updatedEndParent);
              }
            }
          }

          console.log('Calling onStrandCreated with strand:', newStrand.id);
          onStrandCreated(canvasState.selectedLayerId, newStrand);
        }
      }

      // Reset refs
      attachStartRef.current = null;
      isAttachingRef.current = false;
      dragStartPosRef.current = null;
      isMovingEndpointRef.current = false;
      movingEndpointRef.current = null;

      setDraggedStrand(null);
      setDragStartPos(null);
      setSelectionRect(null);
      setEditingControlPoint(null);
      setNewStrandPreview(null);
      setMovingEndpoint(null);
      attachStartTargetRef.current = null;

      // Handle move end callbacks
      if (currentMode === InteractionMode.MOVE) {
        if (movingEndpoint && onStrandMoveEnd) {
          onStrandMoveEnd(movingEndpoint.strand.id, movingEndpoint.layerId);
        } else if (draggedStrand && onStrandMoveEnd) {
          onStrandMoveEnd(draggedStrand.id, draggedStrand.layerId);
        }
      }
    })
    .runOnJS(true);

  const pinchGesture = Gesture.Pinch()
    .onUpdate(e => {
      // TODO: Implement zoom
      console.log('Pinch scale:', e.scale);
    })
    .runOnJS(true);

  const composed = Gesture.Race(tapGesture, panGesture, pinchGesture);

  const handleDrawingComplete = useCallback((segments: any[]) => {
    if (onStrandCreated && canvasState.selectedLayerId) {
      const newStrand = StrandModel.create(
        `strand-${Date.now()}`,
        segments,
        {color: currentColor, width: currentWidth},
      );
      onStrandCreated(canvasState.selectedLayerId, newStrand);
    }
  }, [onStrandCreated, canvasState.selectedLayerId, currentColor, currentWidth]);

  return (
    <View style={styles.container}>
      {currentMode === InteractionMode.DRAW ? (
        <DrawingMode
          width={dimensions.width}
          height={dimensions.height}
          strandColor={currentColor}
          strandWidth={currentWidth}
          onComplete={handleDrawingComplete}
          onCancel={() => {}}
        />
      ) : (
        <GestureDetector gesture={composed}>
          <View style={styles.container}>
            <Svg width={dimensions.width} height={dimensions.height} style={styles.svg}>
              {renderGrid()}
              {canvasState.layers.map(layer => renderLayer(layer))}

              {/* Attachment points visualization (ATTACH mode) */}
              {/* Shows all attachable endpoints so users know where they can attach */}
              {/* Matches desktop attach_mode.py get_attachment_area() visual feedback */}
              {currentMode === InteractionMode.ATTACH && (
                <G>
                  {getAttachableEndpoints(canvasState.layers).map((endpoint, idx) => (
                    <G key={`attach-point-${idx}`}>
                      {/* Outer circle - attachment area indicator (60px radius like desktop 120px diameter) */}
                      <Circle
                        cx={endpoint.point.x}
                        cy={endpoint.point.y}
                        r={60}
                        fill="rgba(0, 255, 0, 0.1)"
                        stroke="rgba(0, 255, 0, 0.4)"
                        strokeWidth={2}
                        strokeDasharray="8,4"
                      />
                      {/* Inner circle - precise attachment point */}
                      <Circle
                        cx={endpoint.point.x}
                        cy={endpoint.point.y}
                        r={12}
                        fill="rgba(0, 255, 0, 0.6)"
                        stroke="#00ff00"
                        strokeWidth={2}
                      />
                    </G>
                  ))}
                </G>
              )}

              {/* Move mode endpoint indicators */}
              {/* Shows 120px square areas at strand endpoints that can be moved */}
              {currentMode === InteractionMode.MOVE && !movingEndpoint && (
                <G>
                  {canvasState.layers.flatMap(layer => {
                    if (!layer.visible || 'layers' in layer) return [];
                    return layer.strands.flatMap((strand, sIdx) => {
                      if (!strand.visible || strand.isHidden || strand.locked || strand.segments.length === 0) return [];
                      const firstSeg = strand.segments[0];
                      const lastSeg = strand.segments[strand.segments.length - 1];
                      const indicators = [];

                      // Start point indicator (only if not attached)
                      if (!strand.startAttached) {
                        indicators.push(
                          <Rect
                            key={`move-start-${strand.id}`}
                            x={firstSeg.bezier.start.x - 30}
                            y={firstSeg.bezier.start.y - 30}
                            width={60}
                            height={60}
                            fill="rgba(0, 150, 255, 0.15)"
                            stroke="rgba(0, 150, 255, 0.5)"
                            strokeWidth={1}
                            strokeDasharray="4,4"
                          />
                        );
                      }

                      // End point indicator
                      indicators.push(
                        <Rect
                          key={`move-end-${strand.id}`}
                          x={lastSeg.bezier.end.x - 30}
                          y={lastSeg.bezier.end.y - 30}
                          width={60}
                          height={60}
                          fill="rgba(255, 100, 0, 0.15)"
                          stroke="rgba(255, 100, 0, 0.5)"
                          strokeWidth={1}
                          strokeDasharray="4,4"
                        />
                      );

                      return indicators;
                    });
                  })}
                </G>
              )}

              {/* New strand preview (ATTACH mode) */}
              {newStrandPreview && (
                <G>
                  <Path
                    d={`M ${newStrandPreview.start.x} ${newStrandPreview.start.y} L ${newStrandPreview.end.x} ${newStrandPreview.end.y}`}
                    stroke={currentColor}
                    strokeWidth={currentWidth}
                    strokeLinecap="round"
                    fill="none"
                    opacity={0.6}
                  />
                  {/* Start point indicator */}
                  <Circle
                    cx={newStrandPreview.start.x}
                    cy={newStrandPreview.start.y}
                    r={10}
                    fill="#00ff00"
                    stroke="#005500"
                    strokeWidth={2}
                    opacity={0.9}
                  />
                  {/* End point indicator */}
                  <Circle
                    cx={newStrandPreview.end.x}
                    cy={newStrandPreview.end.y}
                    r={10}
                    fill="#ff0000"
                    stroke="#550000"
                    strokeWidth={2}
                    opacity={0.9}
                  />
                </G>
              )}

              {/* Selection rectangle */}
              {selectionRect && (
                <Rect
                  x={Math.min(selectionRect.start.x, selectionRect.end.x)}
                  y={Math.min(selectionRect.start.y, selectionRect.end.y)}
                  width={Math.abs(selectionRect.end.x - selectionRect.start.x)}
                  height={Math.abs(selectionRect.end.y - selectionRect.start.y)}
                  stroke="#00ffff"
                  strokeWidth={2}
                  fill="none"
                  strokeDasharray="4,4"
                />
              )}
            </Svg>
          </View>
        </GestureDetector>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  svg: {
    backgroundColor: '#ffffff',
  },
});

export default EnhancedStrandCanvas;
