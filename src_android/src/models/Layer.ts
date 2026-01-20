// Layer model - Manages layers and group layers
// Ported from src/layer_panel.py and src/group_layers.py

import {Layer, GroupLayer, Strand} from '../types';

export class LayerModel {
  /**
   * Create a new layer
   */
  static create(id: string, name: string): Layer {
    return {
      id,
      name,
      strands: [],
      visible: true,
      locked: false,
      opacity: 1.0,
    };
  }

  /**
   * Create a new group layer
   */
  static createGroup(id: string, name: string): GroupLayer {
    return {
      id,
      name,
      layers: [],
      visible: true,
      locked: false,
      expanded: true,
    };
  }

  /**
   * Add a strand to a layer
   */
  static addStrand(layer: Layer, strand: Strand): Layer {
    return {
      ...layer,
      strands: [...layer.strands, strand],
    };
  }

  /**
   * Remove a strand from a layer
   */
  static removeStrand(layer: Layer, strandId: string): Layer {
    return {
      ...layer,
      strands: layer.strands.filter(s => s.id !== strandId),
    };
  }

  /**
   * Update a strand in a layer
   */
  static updateStrand(layer: Layer, strand: Strand): Layer {
    return {
      ...layer,
      strands: layer.strands.map(s => (s.id === strand.id ? strand : s)),
    };
  }

  /**
   * Get a strand by ID from a layer
   */
  static getStrand(layer: Layer, strandId: string): Strand | null {
    return layer.strands.find(s => s.id === strandId) || null;
  }

  /**
   * Check if layer is a group layer
   */
  static isGroupLayer(layer: Layer | GroupLayer): layer is GroupLayer {
    return 'layers' in layer;
  }

  /**
   * Add a layer to a group
   */
  static addLayerToGroup(group: GroupLayer, layer: Layer): GroupLayer {
    return {
      ...group,
      layers: [...group.layers, layer],
    };
  }

  /**
   * Remove a layer from a group
   */
  static removeLayerFromGroup(group: GroupLayer, layerId: string): GroupLayer {
    return {
      ...group,
      layers: group.layers.filter(l => l.id !== layerId),
    };
  }

  /**
   * Get all strands from a layer (including nested layers if it's a group)
   */
  static getAllStrands(layer: Layer | GroupLayer): Strand[] {
    if (LayerModel.isGroupLayer(layer)) {
      return layer.layers.flatMap(l => LayerModel.getAllStrands(l));
    }
    return layer.strands;
  }

  /**
   * Count total strands in a layer
   */
  static countStrands(layer: Layer | GroupLayer): number {
    return LayerModel.getAllStrands(layer).length;
  }

  /**
   * Toggle layer visibility
   */
  static toggleVisibility(layer: Layer | GroupLayer): Layer | GroupLayer {
    return {
      ...layer,
      visible: !layer.visible,
    };
  }

  /**
   * Toggle layer lock
   */
  static toggleLock(layer: Layer | GroupLayer): Layer | GroupLayer {
    return {
      ...layer,
      locked: !layer.locked,
    };
  }

  /**
   * Set layer opacity (only for regular layers)
   */
  static setOpacity(layer: Layer, opacity: number): Layer {
    return {
      ...layer,
      opacity: Math.max(0, Math.min(1, opacity)),
    };
  }

  /**
   * Rename a layer
   */
  static rename(layer: Layer | GroupLayer, name: string): Layer | GroupLayer {
    return {
      ...layer,
      name,
    };
  }

  /**
   * Clone a layer (deep copy)
   */
  static clone(layer: Layer | GroupLayer): Layer | GroupLayer {
    return JSON.parse(JSON.stringify(layer));
  }
}
