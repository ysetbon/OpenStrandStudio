// LayerStateManager - Tracks layer/strand state and connections (desktop parity)
import {CanvasState, Layer, GroupLayer, LayerState, Strand} from '../types';
import {MaskedStrandModel} from '../models/MaskedStrand';
import {AttachedStrandModel, AttachedStrand} from '../models/AttachedStrand';

type ConnectionMap = Record<string, [string | null, string | null]>;

type StrandWithLayer = {
  strand: Strand;
  layerName: string;
};

const DEFAULT_LAYER_STATE: LayerState = {
  order: [],
  connections: {},
  maskedLayers: [],
  colors: {},
  positions: {},
  selectedStrand: null,
  newestStrand: null,
  newestLayer: null,
  shadowOverrides: {},
};

export class LayerStateManager {
  private layerState: LayerState;
  private cachedConnections: ConnectionMap | null;
  private movementInProgress: boolean;

  constructor() {
    this.layerState = {...DEFAULT_LAYER_STATE};
    this.cachedConnections = null;
    this.movementInProgress = false;
  }

  startMovementOperation(layers: (Layer | GroupLayer)[]): void {
    this.movementInProgress = true;
    const strands = this.flattenLayers(layers).map(entry => entry.strand);
    this.cachedConnections = this.getLayerConnections(strands);
  }

  endMovementOperation(): void {
    this.movementInProgress = false;
    this.cachedConnections = null;
  }

  saveCurrentState(canvasState: CanvasState): LayerState {
    const flattened = this.flattenLayers(canvasState.layers);
    const strands = flattened.map(entry => entry.strand);
    const order = this.buildOrder(canvasState.layers, flattened);
    const connections =
      this.movementInProgress && this.cachedConnections
        ? this.cachedConnections
        : this.getLayerConnections(strands);

    const maskedLayers = this.getMaskedLayersFromEntries(flattened);
    const colors = this.getColorsFromEntries(flattened);
    const positions = this.getPositionsFromEntries(flattened);

    const newestStrand = this.findNewestStrandId(strands);
    const newestLayer = this.findNewestLayerName(canvasState.layers);

    this.layerState = {
      ...this.layerState,
      order,
      connections,
      maskedLayers,
      colors,
      positions,
      selectedStrand: canvasState.selectedStrandId,
      newestStrand,
      newestLayer,
    };

    return this.layerState;
  }

  applyLoadedState(stateData: LayerState): void {
    this.layerState = {
      ...this.layerState,
      ...stateData,
    };
  }

  getOrder(): string[] {
    return this.layerState.order;
  }

  getConnections(): ConnectionMap {
    return this.layerState.connections;
  }

  getDetailedConnections(): ConnectionMap {
    return this.layerState.connections;
  }

  getMaskedLayers(): string[] {
    return this.layerState.maskedLayers;
  }

  getColors(): Record<string, string> {
    return this.layerState.colors;
  }

  getPositions(): Record<string, [number, number, number, number]> {
    return this.layerState.positions;
  }

  getSelectedStrand(): string | null {
    return this.layerState.selectedStrand;
  }

  getNewestStrand(): string | null {
    return this.layerState.newestStrand;
  }

  getNewestLayer(): string | null {
    return this.layerState.newestLayer;
  }

  setShadowOverride(
    castingLayer: string,
    receivingLayer: string,
    overrideData: Record<string, unknown>,
  ): void {
    if (!this.layerState.shadowOverrides[castingLayer]) {
      this.layerState.shadowOverrides[castingLayer] = {};
    }
    this.layerState.shadowOverrides[castingLayer][receivingLayer] = overrideData;
  }

  getShadowOverride(
    castingLayer: string,
    receivingLayer: string,
  ): Record<string, unknown> | null {
    return (
      this.layerState.shadowOverrides[castingLayer]?.[receivingLayer] ?? null
    );
  }

  removeShadowOverride(castingLayer: string, receivingLayer: string): void {
    if (!this.layerState.shadowOverrides[castingLayer]) {
      return;
    }
    delete this.layerState.shadowOverrides[castingLayer][receivingLayer];
  }

  private flattenLayers(layers: (Layer | GroupLayer)[]): StrandWithLayer[] {
    const results: StrandWithLayer[] = [];

    const walk = (layerList: (Layer | GroupLayer)[]) => {
      layerList.forEach(layer => {
        if ('layers' in layer) {
          walk(layer.layers);
          return;
        }
        layer.strands.forEach(strand => {
          results.push({strand, layerName: layer.name});
        });
      });
    };

    walk(layers);
    return results;
  }

  private buildOrder(
    layers: (Layer | GroupLayer)[],
    entries: StrandWithLayer[],
  ): string[] {
    const order: string[] = [];
    layers.forEach(layer => {
      if ('layers' in layer) {
        layer.layers.forEach(child => {
          if (!order.includes(child.name)) {
            order.push(child.name);
          }
        });
        return;
      }
      if (!order.includes(layer.name)) {
        order.push(layer.name);
      }
    });

    entries.forEach(entry => {
      if (!order.includes(entry.layerName)) {
        order.push(entry.layerName);
      }
    });

    return order;
  }

  private getMaskedLayersFromEntries(entries: StrandWithLayer[]): string[] {
    const masked = new Set<string>();
    entries.forEach(entry => {
      if (MaskedStrandModel.isMasked(entry.strand)) {
        masked.add(entry.layerName);
      }
    });
    return Array.from(masked);
  }

  private getColorsFromEntries(
    entries: StrandWithLayer[],
  ): Record<string, string> {
    const colors: Record<string, string> = {};
    entries.forEach(entry => {
      if (!colors[entry.layerName]) {
        colors[entry.layerName] = entry.strand.style.color;
      }
    });
    return colors;
  }

  private getPositionsFromEntries(
    entries: StrandWithLayer[],
  ): Record<string, [number, number, number, number]> {
    const positions: Record<string, [number, number, number, number]> = {};

    entries.forEach(entry => {
      if (positions[entry.layerName]) {
        return;
      }

      const start =
        entry.strand.start ?? entry.strand.segments[0]?.bezier.start ?? {x: 0, y: 0};
      const end =
        entry.strand.end ??
        entry.strand.segments[entry.strand.segments.length - 1]?.bezier.end ??
        {x: 0, y: 0};

      positions[entry.layerName] = [start.x, start.y, end.x, end.y];
    });

    return positions;
  }

  private findNewestStrandId(strands: Strand[]): string | null {
    if (strands.length === 0) {
      return null;
    }
    return strands[strands.length - 1].id;
  }

  private findNewestLayerName(layers: (Layer | GroupLayer)[]): string | null {
    if (layers.length === 0) {
      return null;
    }
    const last = layers[layers.length - 1];
    return last.name ?? null;
  }

  private getLayerConnections(strands: Strand[]): ConnectionMap {
    const connections: ConnectionMap = {};

    strands.forEach(strand => {
      connections[strand.id] = [null, null];
    });

    const ensureEntry = (strandId: string) => {
      if (!connections[strandId]) {
        connections[strandId] = [null, null];
      }
    };

    const setConnection = (
      sourceId: string,
      sourceEnd: 0 | 1,
      targetId: string,
      targetEnd: 0 | 1,
    ) => {
      ensureEntry(sourceId);
      ensureEntry(targetId);
      connections[sourceId][sourceEnd] = `${targetId}(${targetEnd})`;
    };

    strands.forEach(strand => {
      if (AttachedStrandModel.isAttached(strand)) {
        const attached = strand as AttachedStrand;
        const parentId =
          attached.parentId ?? attached.attachments.start?.strandId ?? null;
        if (parentId) {
          const parentEnd =
            attached.attachmentSide ??
            attached.attachments.start?.attachmentSide ??
            (attached.attachments.start && attached.attachments.start.t <= 0.5
              ? 0
              : 1);
          setConnection(attached.id, 0, parentId, parentEnd);
          setConnection(parentId, parentEnd, attached.id, 0);
        }

        if (attached.attachments.end) {
          const endParentId = attached.attachments.end.strandId;
          const endParentSide =
            attached.attachments.end.attachmentSide ??
            (attached.attachments.end.t <= 0.5 ? 0 : 1);
          setConnection(attached.id, 1, endParentId, endParentSide);
          setConnection(endParentId, endParentSide, attached.id, 1);
        }
      }

      if (strand.knotConnections?.start) {
        const target = strand.knotConnections.start;
        const targetEnd = target.connectedEnd === 'start' ? 0 : 1;
        setConnection(strand.id, 0, target.connectedStrandId, targetEnd);
        setConnection(target.connectedStrandId, targetEnd, strand.id, 0);
      }

      if (strand.knotConnections?.end) {
        const target = strand.knotConnections.end;
        const targetEnd = target.connectedEnd === 'start' ? 0 : 1;
        setConnection(strand.id, 1, target.connectedStrandId, targetEnd);
        setConnection(target.connectedStrandId, targetEnd, strand.id, 1);
      }
    });

    return connections;
  }
}
