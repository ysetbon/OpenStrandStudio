// Core types for OpenStrand Studio Mobile

export interface Point {
  x: number;
  y: number;
}

export interface BezierCurve {
  start: Point;
  control1: Point;
  control2: Point;
  end: Point;
}

export interface StrandSegment {
  bezier: BezierCurve;
  length: number;
}

export interface StrandStyle {
  color: string;           // Fill color
  strokeColor: string;     // Border/stroke color
  strokeWidth: number;     // Border width
  width: number;           // Strand width
  shadowEnabled: boolean;
  shadowColor: string;
  shadowOffset: Point;
  shadowBlur: number;
}

export type ArrowTexture = 'none' | 'stripes' | 'dots' | 'crosshatch';
export type ArrowShaftStyle = 'solid' | 'stripes' | 'dots';

export interface KnotConnection {
  connectedStrandId: string;
  connectedEnd: 'start' | 'end';
}

export interface StrandKnotConnections {
  start?: KnotConnection;
  end?: KnotConnection;
}

export interface Strand {
  id: string;
  segments: StrandSegment[];
  style: StrandStyle;
  closed: boolean;
  visible: boolean;
  locked: boolean;
  // Desktop parity fields (optional to avoid breaking existing usage)
  start?: Point;
  end?: Point;
  controlPoint1?: Point;
  controlPoint2?: Point;
  controlPointCenter?: Point;
  controlPointCenterLocked?: boolean;
  triangleHasMoved?: boolean;
  controlPoint2Shown?: boolean;
  controlPoint2Activated?: boolean;
  startAttached?: boolean;
  endAttached?: boolean;
  isSelected?: boolean;
  isHidden?: boolean;
  shadowOnly?: boolean;
  hasCircles?: [boolean, boolean];
  isStartSide?: boolean;
  curveResponseExponent?: number;
  controlPointBaseFraction?: number;
  distanceMultiplier?: number;
  endpointTension?: number;
  startLineVisible?: boolean;
  endLineVisible?: boolean;
  startExtensionVisible?: boolean;
  endExtensionVisible?: boolean;
  startArrowVisible?: boolean;
  endArrowVisible?: boolean;
  fullArrowVisible?: boolean;
  arrowColor?: string | null;
  arrowTransparency?: number;
  arrowTexture?: ArrowTexture;
  arrowShaftStyle?: ArrowShaftStyle;
  arrowHeadVisible?: boolean;
  layerName?: string;
  setNumber?: number | null;
  knotConnections?: StrandKnotConnections;
  attachable?: boolean;
  attachedStrandIds?: string[];
  color?: string;
  strokeColor?: string;
  strokeWidth?: number;
  width?: number;
  shadowColor?: string;
  sideLineColor?: string;
  circleStrokeColor?: string | null;
  startCircleStrokeColor?: string | null;
  endCircleStrokeColor?: string | null;
  parentId?: string;
  attachmentSide?: 0 | 1;
}

export interface Layer {
  id: string;
  name: string;
  strands: Strand[];
  visible: boolean;
  locked: boolean;
  opacity: number;
}

export interface GroupLayer {
  id: string;
  name: string;
  layers: Layer[];
  visible: boolean;
  locked: boolean;
  expanded: boolean;
}

export interface CanvasState {
  layers: (Layer | GroupLayer)[];
  selectedLayerId: string | null;
  selectedStrandId: string | null;
  zoom: number;
  panOffset: Point;
  gridEnabled: boolean;
  gridSize: number;
}

export interface AppSettings {
  language: string;
  theme: 'light' | 'dark';
  defaultStrandColor: string;
  defaultStrandWidth: number;
  autoSave: boolean;
  autoSaveInterval: number;
}

export enum InteractionMode {
  SELECT = 'select',
  MOVE = 'move',
  ATTACH = 'attach',
  MASK = 'mask',
  ROTATE = 'rotate',
  ANGLE_ADJUST = 'angle_adjust',
  DRAW = 'draw',
  PAN = 'pan',
}

export interface LayerColor {
  fill: string;
  border: string;
}

export interface UndoState {
  canvasState: CanvasState;
  timestamp: number;
  description: string;
}

export interface LayerState {
  order: string[];
  connections: Record<string, [string | null, string | null]>;
  maskedLayers: string[];
  colors: Record<string, string>;
  positions: Record<string, [number, number, number, number]>;
  selectedStrand: string | null;
  newestStrand: string | null;
  newestLayer: string | null;
  shadowOverrides: Record<string, Record<string, Record<string, unknown>>>;
}
