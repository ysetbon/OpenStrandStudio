// Enhanced Strand Canvas with full interaction support
import React, {useRef, useState, useCallback} from 'react';
import {View, StyleSheet, Dimensions} from 'react-native';
import Svg, {Path, Defs, Filter, FeGaussianBlur, G, Circle, Rect} from 'react-native-svg';
import {GestureDetector, Gesture} from 'react-native-gesture-handler';
import {Strand, Point, Layer, GroupLayer, CanvasState, InteractionMode} from '../types';
import {bezierPoint} from '../utils/bezier';
import {findStrandAtPoint, findClosestControlPoint} from '../utils/hitTesting';
import {StrandModel} from '../models/Strand';
import {MaskedStrandModel, MaskedStrand} from '../models/MaskedStrand';
import DrawingMode from './DrawingMode';

interface EnhancedStrandCanvasProps {
  canvasState: CanvasState;
  currentMode: InteractionMode;
  currentColor: string;
  currentWidth: number;
  onStrandSelected?: (strandId: string, layerId: string) => void;
  onStrandMoved?: (strandId: string, layerId: string, offset: Point) => void;
  onStrandCreated?: (layerId: string, strand: Strand) => void;
  onCanvasPan?: (offset: Point) => void;
  onControlPointMove?: (strandId: string, layerId: string, segmentIndex: number, pointType: string, newPos: Point) => void;
}

const EnhancedStrandCanvas: React.FC<EnhancedStrandCanvasProps> = ({
  canvasState,
  currentMode,
  currentColor,
  currentWidth,
  onStrandSelected,
  onStrandMoved,
  onStrandCreated,
  onCanvasPan,
  onControlPointMove,
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

  // Convert Bezier curve to SVG path data
  const bezierToPathData = (bezier: any): string => {
    return `M ${bezier.start.x} ${bezier.start.y} C ${bezier.control1.x} ${bezier.control1.y}, ${bezier.control2.x} ${bezier.control2.y}, ${bezier.end.x} ${bezier.end.y}`;
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
          {strand.style.shadowEnabled && (
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
              filter="url(#shadow-blur)"
            />
          )}

          {/* Main strand */}
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
        {isSelected && currentMode === InteractionMode.SELECT && strand.segments.map((seg, segIndex) => (
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
  }, [canvasState.selectedStrandId, currentMode]);

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
    .onBegin(e => {
      const point = {x: e.x, y: e.y};
      setDragStartPos(point);

      if (currentMode === InteractionMode.MOVE) {
        const result = findStrandAtPoint(canvasState.layers, point);
        if (result) {
          setDraggedStrand({id: result.strand.id, layerId: result.layerId});
          if (onStrandSelected) {
            onStrandSelected(result.strand.id, result.layerId);
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
      if (currentMode === InteractionMode.MOVE && draggedStrand && dragStartPos) {
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
      } else if (currentMode === InteractionMode.SELECT && !draggedStrand) {
        // Selection rectangle
        setSelectionRect({
          start: dragStartPos!,
          end: {x: e.x, y: e.y},
        });
      }
    })
    .onEnd(() => {
      setDraggedStrand(null);
      setDragStartPos(null);
      setSelectionRect(null);
      setEditingControlPoint(null);
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
              <Defs>
                <Filter id="shadow-blur">
                  <FeGaussianBlur stdDeviation="2" />
                </Filter>
              </Defs>

              {renderGrid()}
              {canvasState.layers.map(layer => renderLayer(layer))}

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
