// Drawing mode component - Handle strand drawing with touch
import React, {useState, useCallback} from 'react';
import {View, StyleSheet} from 'react-native';
import {GestureDetector, Gesture} from 'react-native-gesture-handler';
import Svg, {Path, Circle} from 'react-native-svg';
import {Point, BezierCurve, StrandSegment} from '../types';
import {bezierLength, distance} from '../utils/bezier';

interface DrawingModeProps {
  width: number;
  height: number;
  strandColor: string;
  strandWidth: number;
  onComplete: (segments: StrandSegment[]) => void;
  onCancel: () => void;
}

const DrawingMode: React.FC<DrawingModeProps> = ({
  width,
  height,
  strandColor,
  strandWidth,
  onComplete,
  onCancel,
}) => {
  const [points, setPoints] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);

  // Convert points to Bezier segments
  const createSegments = useCallback((pts: Point[]): StrandSegment[] => {
    if (pts.length < 2) {
      return [];
    }

    const segments: StrandSegment[] = [];

    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p3 = pts[i + 1];

      // Calculate control points for smooth curve
      const dx = p3.x - p0.x;
      const dy = p3.y - p0.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const tension = 0.3; // Curve tension

      // Look ahead and behind for better curve
      const prevPoint = i > 0 ? pts[i - 1] : p0;
      const nextPoint = i < pts.length - 2 ? pts[i + 2] : p3;

      // Calculate tangent direction
      const tangentX1 = (p3.x - prevPoint.x) / 2;
      const tangentY1 = (p3.y - prevPoint.y) / 2;
      const tangentX2 = (nextPoint.x - p0.x) / 2;
      const tangentY2 = (nextPoint.y - p0.y) / 2;

      const p1: Point = {
        x: p0.x + tangentX1 * tension,
        y: p0.y + tangentY1 * tension,
      };

      const p2: Point = {
        x: p3.x - tangentX2 * tension,
        y: p3.y - tangentY2 * tension,
      };

      const bezier: BezierCurve = {
        start: p0,
        control1: p1,
        control2: p2,
        end: p3,
      };

      segments.push({
        bezier,
        length: bezierLength(bezier),
      });
    }

    return segments;
  }, []);

  // Generate SVG path from points
  const generatePath = useCallback((pts: Point[]): string => {
    if (pts.length === 0) {
      return '';
    }

    if (pts.length === 1) {
      return `M ${pts[0].x} ${pts[0].y}`;
    }

    const segments = createSegments(pts);
    return segments
      .map(
        seg =>
          `M ${seg.bezier.start.x} ${seg.bezier.start.y} C ${seg.bezier.control1.x} ${seg.bezier.control1.y}, ${seg.bezier.control2.x} ${seg.bezier.control2.y}, ${seg.bezier.end.x} ${seg.bezier.end.y}`,
      )
      .join(' ');
  }, [createSegments]);

  const panGesture = Gesture.Pan()
    .onBegin(e => {
      setIsDrawing(true);
      setPoints([{x: e.x, y: e.y}]);
    })
    .onUpdate(e => {
      const newPoint = {x: e.x, y: e.y};
      setPoints(prev => {
        // Add point if it's far enough from the last point
        const lastPoint = prev[prev.length - 1];
        if (!lastPoint || distance(lastPoint, newPoint) > 5) {
          return [...prev, newPoint];
        }
        return prev;
      });
    })
    .onEnd(() => {
      setIsDrawing(false);
      if (points.length >= 2) {
        const segments = createSegments(points);
        onComplete(segments);
      } else {
        onCancel();
      }
      setPoints([]);
    })
    .onFinalize(() => {
      setIsDrawing(false);
    })
    .runOnJS(true);

  const tapGesture = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      if (points.length >= 2) {
        const segments = createSegments(points);
        onComplete(segments);
        setPoints([]);
      }
    })
    .runOnJS(true);

  const composed = Gesture.Race(tapGesture, panGesture);

  return (
    <GestureDetector gesture={composed}>
      <View style={styles.container}>
        <Svg width={width} height={height} style={styles.svg}>
          {/* Draw the path being created */}
          {points.length > 0 && (
            <Path
              d={generatePath(points)}
              stroke={strandColor}
              strokeWidth={strandWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.8}
            />
          )}

          {/* Draw control points */}
          {points.map((point, index) => (
            <Circle
              key={index}
              cx={point.x}
              cy={point.y}
              r={index === 0 || index === points.length - 1 ? 8 : 4}
              fill={index === 0 ? '#00ff00' : index === points.length - 1 ? '#ff0000' : strandColor}
              opacity={0.6}
            />
          ))}
        </Svg>
      </View>
    </GestureDetector>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  svg: {
    backgroundColor: 'transparent',
  },
});

export default DrawingMode;
