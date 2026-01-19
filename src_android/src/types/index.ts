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
  color: string;
  width: number;
  shadowEnabled: boolean;
  shadowColor: string;
  shadowOffset: Point;
  shadowBlur: number;
}

export interface Strand {
  id: string;
  segments: StrandSegment[];
  style: StrandStyle;
  closed: boolean;
  visible: boolean;
  locked: boolean;
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
}

export interface UndoState {
  canvasState: CanvasState;
  timestamp: number;
  description: string;
}
