// Undo/Redo manager - Manages undo/redo history
// Ported from src/undo_redo_manager.py

import {CanvasState, UndoState} from '../types';

export class UndoRedoManager {
  private undoStack: UndoState[] = [];
  private redoStack: UndoState[] = [];
  private maxHistorySize: number = 50;
  private currentState: CanvasState | null = null;

  constructor(maxHistorySize: number = 50) {
    this.maxHistorySize = maxHistorySize;
  }

  /**
   * Save current state before making changes
   */
  saveState(state: CanvasState, description: string = 'Action'): void {
    // Deep clone the state
    const stateCopy: CanvasState = JSON.parse(JSON.stringify(state));

    const undoState: UndoState = {
      canvasState: stateCopy,
      timestamp: Date.now(),
      description,
    };

    this.undoStack.push(undoState);

    // Limit stack size
    if (this.undoStack.length > this.maxHistorySize) {
      this.undoStack.shift();
    }

    // Clear redo stack when new action is performed
    this.redoStack = [];

    this.currentState = state;
  }

  /**
   * Undo the last action
   */
  undo(): CanvasState | null {
    if (!this.canUndo()) {
      return null;
    }

    const currentStateCopy: CanvasState = JSON.parse(
      JSON.stringify(this.currentState),
    );

    // Save current state to redo stack
    if (this.currentState) {
      this.redoStack.push({
        canvasState: currentStateCopy,
        timestamp: Date.now(),
        description: 'Current State',
      });
    }

    // Pop from undo stack
    const previousState = this.undoStack.pop()!;
    this.currentState = previousState.canvasState;

    return previousState.canvasState;
  }

  /**
   * Redo the last undone action
   */
  redo(): CanvasState | null {
    if (!this.canRedo()) {
      return null;
    }

    const currentStateCopy: CanvasState = JSON.parse(
      JSON.stringify(this.currentState),
    );

    // Save current state to undo stack
    if (this.currentState) {
      this.undoStack.push({
        canvasState: currentStateCopy,
        timestamp: Date.now(),
        description: 'Current State',
      });
    }

    // Pop from redo stack
    const nextState = this.redoStack.pop()!;
    this.currentState = nextState.canvasState;

    return nextState.canvasState;
  }

  /**
   * Check if undo is available
   */
  canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  /**
   * Check if redo is available
   */
  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  /**
   * Clear all history
   */
  clear(): void {
    this.undoStack = [];
    this.redoStack = [];
    this.currentState = null;
  }

  /**
   * Get undo stack size
   */
  getUndoStackSize(): number {
    return this.undoStack.length;
  }

  /**
   * Get redo stack size
   */
  getRedoStackSize(): number {
    return this.redoStack.length;
  }

  /**
   * Get description of the last action in undo stack
   */
  getUndoDescription(): string | null {
    if (this.undoStack.length === 0) {
      return null;
    }
    return this.undoStack[this.undoStack.length - 1].description;
  }

  /**
   * Get description of the last action in redo stack
   */
  getRedoDescription(): string | null {
    if (this.redoStack.length === 0) {
      return null;
    }
    return this.redoStack[this.redoStack.length - 1].description;
  }

  /**
   * Get current state
   */
  getCurrentState(): CanvasState | null {
    return this.currentState;
  }

  /**
   * Set current state (for initialization)
   */
  setCurrentState(state: CanvasState): void {
    this.currentState = state;
  }
}
