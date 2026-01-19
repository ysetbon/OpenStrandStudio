// Strand Canvas - Main rendering component
// Ported from src/strand_drawing_canvas.py

import React, {useRef, useState} from 'react';
import {View, StyleSheet, Dimensions} from 'react-native';
import Svg, {Path, Defs, Filter, FeGaussianBlur, G} from 'react-native-svg';
import {GestureDetector, Gesture} from 'react-native-gesture-handler';
import Animated from 'react-native-reanimated';
import {Strand, Point, Layer, GroupLayer, CanvasState} from '../types';
import {bezierPoint} from '../utils/bezier';

interface StrandCanvasProps {
  canvasState: CanvasState;
  onStrandSelected?: (strandId: string) => void;
  onStrandMoved?: (strandId: string, offset: Point) => void;
  onCanvasPan?: (offset: Point) => void;
}

const StrandCanvas: React.FC<StrandCanvasProps> = ({
  canvasState,
  onStrandSelected,
  onStrandMoved,
  onCanvasPan,
}) => {
  const {width: screenWidth, height: screenHeight} = Dimensions.get('window');
  const [dimensions] = useState({width: screenWidth, height: screenHeight});

  // Convert Bezier curve to SVG path data
  const bezierToPathData = (bezier: any): string => {
    return `M ${bezier.start.x} ${bezier.start.y} C ${bezier.control1.x} ${bezier.control1.y}, ${bezier.control2.x} ${bezier.control2.y}, ${bezier.end.x} ${bezier.end.y}`;
  };

  // Render a single strand
  const renderStrand = (strand: Strand, layerId: string) => {
    if (!strand.visible) {
      return null;
    }

    const pathData = strand.segments
      .map(seg => bezierToPathData(seg.bezier))
      .join(' ');

    const isSelected = strand.id === canvasState.selectedStrandId;

    return (
      <G key={strand.id}>
        {/* Shadow layer */}
        {strand.style.shadowEnabled && (
          <Path
            d={pathData}
            stroke={strand.style.shadowColor}
            strokeWidth={strand.style.width}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={0.5}
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
          opacity={isSelected ? 0.8 : 1}
        />

        {/* Selection highlight */}
        {isSelected && (
          <Path
            d={pathData}
            stroke="#00ffff"
            strokeWidth={strand.style.width + 4}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={0.3}
          />
        )}
      </G>
    );
  };

  // Render all strands from a layer
  const renderLayer = (layer: Layer | GroupLayer) => {
    if (!layer.visible) {
      return null;
    }

    if ('layers' in layer) {
      // Group layer
      return layer.layers.map(l => renderLayer(l));
    } else {
      // Regular layer
      return layer.strands.map(strand => renderStrand(strand, layer.id));
    }
  };

  // Render grid
  const renderGrid = () => {
    if (!canvasState.gridEnabled) {
      return null;
    }

    const gridLines = [];
    const gridSize = canvasState.gridSize;

    // Vertical lines
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

    // Horizontal lines
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
  };

  // Gesture handlers
  const panGesture = Gesture.Pan()
    .onUpdate(e => {
      if (onCanvasPan) {
        onCanvasPan({x: e.translationX, y: e.translationY});
      }
    })
    .runOnJS(true);

  const tapGesture = Gesture.Tap()
    .onEnd(e => {
      // Find strand at tap location
      const tapPoint = {x: e.x, y: e.y};
      // TODO: Implement hit testing to find strand at point
      // For now, just log the tap
      console.log('Tapped at:', tapPoint);
    })
    .runOnJS(true);

  const composed = Gesture.Race(tapGesture, panGesture);

  return (
    <GestureDetector gesture={composed}>
      <View style={styles.container}>
        <Svg
          width={dimensions.width}
          height={dimensions.height}
          style={styles.svg}>
          <Defs>
            <Filter id="shadow-blur">
              <FeGaussianBlur stdDeviation="2" />
            </Filter>
          </Defs>

          {/* Grid */}
          {renderGrid()}

          {/* Render all layers */}
          {canvasState.layers.map(layer => renderLayer(layer))}
        </Svg>
      </View>
    </GestureDetector>
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

export default StrandCanvas;
