// Main Screen - Desktop-like layout with toolbar, canvas, and layer panel
import React, {useState, useEffect} from 'react';
import {
  View,
  StyleSheet,
  Alert,
  Share,
  Dimensions,
  StatusBar,
  Modal,
  ScrollView,
  Text,
  TouchableOpacity,
} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useTranslation} from 'react-i18next';
import EnhancedStrandCanvas from '../components/EnhancedStrandCanvas';
import Toolbar from '../components/Toolbar';
import LayerPanel from '../components/LayerPanel';
import {
  CanvasState,
  InteractionMode,
  Point,
  Layer,
  GroupLayer,
  Strand,
} from '../types';
import {LayerModel} from '../models/Layer';
import {StrandModel} from '../models/Strand';
import {AttachedStrandModel} from '../models/AttachedStrand';
import {UndoRedoManager} from '../services/UndoRedoManager';
import {SaveLoadManager} from '../services/SaveLoadManager';
import {LayerStateManager} from '../services/LayerStateManager';
import {exportToSVGCropped, generateShareData, saveSVGToFile} from '../utils/export';

const MainScreen: React.FC = () => {
  const navigation = useNavigation();
  const {t} = useTranslation();
  const [undoManager] = useState(() => new UndoRedoManager());
  const [layerStateManager] = useState(() => new LayerStateManager());
  const [projectName, setProjectName] = useState('Untitled');
  const [currentColor, setCurrentColor] = useState('#C8AAE6'); // Default purple like desktop
  const [currentWidth, setCurrentWidth] = useState(20);
  const [layerStateVisible, setLayerStateVisible] = useState(false);
  const [layerStateText, setLayerStateText] = useState('');

  // UI state
  const [showControlPoints, setShowControlPoints] = useState(true);
  const [showShadows, setShowShadows] = useState(true);

  // Initial canvas state
  const [canvasState, setCanvasState] = useState<CanvasState>({
    layers: [LayerModel.create('layer-1', 'Set 1')],
    selectedLayerId: 'layer-1',
    selectedStrandId: null,
    zoom: 1,
    panOffset: {x: 0, y: 0},
    gridEnabled: false,
    gridSize: 20,
  });

  const [currentMode, setCurrentMode] = useState<InteractionMode>(
    InteractionMode.SELECT,
  );
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  // Initialize save/load manager
  useEffect(() => {
    SaveLoadManager.initialize();
    loadAutoSave();
  }, []);

  // Auto-save every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      SaveLoadManager.autoSave(canvasState);
    }, 30000);

    return () => clearInterval(interval);
  }, [canvasState]);

  useEffect(() => {
    layerStateManager.saveCurrentState(canvasState);
  }, [canvasState, layerStateManager]);

  const loadAutoSave = async () => {
    const saved = await SaveLoadManager.loadAutoSave();
    if (saved) {
      setCanvasState(saved);
      undoManager.setCurrentState(saved);
    }
  };

  const handleUndo = () => {
    const state = undoManager.undo();
    if (state) {
      setCanvasState(state);
      updateUndoRedoState();
    }
  };

  const handleRedo = () => {
    const state = undoManager.redo();
    if (state) {
      setCanvasState(state);
      updateUndoRedoState();
    }
  };

  const updateUndoRedoState = () => {
    setCanUndo(undoManager.canUndo());
    setCanRedo(undoManager.canRedo());
  };

  const saveStateForUndo = (description: string) => {
    undoManager.saveState(canvasState, description);
    updateUndoRedoState();
  };

  // Canvas controls
  const handleZoomIn = () => {
    setCanvasState(prev => ({
      ...prev,
      zoom: Math.min(prev.zoom * 1.2, 5),
    }));
  };

  const handleZoomOut = () => {
    setCanvasState(prev => ({
      ...prev,
      zoom: Math.max(prev.zoom / 1.2, 0.2),
    }));
  };

  const handleResetView = () => {
    setCanvasState(prev => ({
      ...prev,
      zoom: 1,
      panOffset: {x: 0, y: 0},
    }));
  };

  const handleToggleGrid = () => {
    setCanvasState(prev => ({
      ...prev,
      gridEnabled: !prev.gridEnabled,
    }));
  };

  // Layer management
  const handleLayerSelect = (layerId: string) => {
    setCanvasState({
      ...canvasState,
      selectedLayerId: layerId,
    });
  };

  const handleLayerToggleVisibility = (layerId: string) => {
    saveStateForUndo('Toggle layer visibility');
    const newLayers = canvasState.layers.map(layer =>
      layer.id === layerId ? LayerModel.toggleVisibility(layer) : layer,
    );
    setCanvasState({
      ...canvasState,
      layers: newLayers,
    });
  };

  const handleLayerToggleLock = (layerId: string) => {
    const newLayers = canvasState.layers.map(layer =>
      layer.id === layerId ? LayerModel.toggleLock(layer) : layer,
    );
    setCanvasState({
      ...canvasState,
      layers: newLayers,
    });
  };

  const handleLayerDelete = (layerId: string) => {
    Alert.alert(t('confirmDelete'), t('confirmDeleteMessage'), [
      {text: t('cancel'), style: 'cancel'},
      {
        text: t('delete'),
        style: 'destructive',
        onPress: () => {
          saveStateForUndo('Delete layer');
          const newLayers = canvasState.layers.filter(l => l.id !== layerId);
          setCanvasState({
            ...canvasState,
            layers: newLayers.length > 0 ? newLayers : [LayerModel.create('layer-1', 'Set 1')],
            selectedLayerId:
              canvasState.selectedLayerId === layerId
                ? newLayers[0]?.id || 'layer-1'
                : canvasState.selectedLayerId,
          });
        },
      },
    ]);
  };

  const handleResetStates = () => {
    undoManager.clear();
    undoManager.setCurrentState(canvasState);
    updateUndoRedoState();
  };

  const handleRefreshLayers = () => {
    setCanvasState(prev => ({...prev}));
  };

  const handleDeselectAll = () => {
    setCanvasState(prev => ({
      ...prev,
      selectedStrandId: null,
    }));
  };

  const handleLayerAdd = () => {
    // Match desktop layer_panel.py request_new_strand() behavior:
    // 1. Create/select a layer (set)
    // 2. Switch to drawing mode so user can draw a new strand
    saveStateForUndo('Add layer');

    // Check if current layer is empty (no strands) - reuse it instead of creating new
    const currentLayer = canvasState.layers.find(l => l.id === canvasState.selectedLayerId);
    const isCurrentLayerEmpty = currentLayer && !('layers' in currentLayer) && currentLayer.strands.length === 0;

    if (isCurrentLayerEmpty && currentLayer) {
      // Reuse the empty current layer, just switch to ATTACH mode
      setCurrentMode(InteractionMode.ATTACH);
    } else {
      // Create a new layer and switch to ATTACH mode
      const setNumber = canvasState.layers.length + 1;
      const newLayer = LayerModel.create(
        `layer-${Date.now()}`,
        `Set ${setNumber}`,
      );
      setCanvasState({
        ...canvasState,
        layers: [...canvasState.layers, newLayer],
        selectedLayerId: newLayer.id,
      });
      // Switch to ATTACH mode so user can draw on the canvas
      // This matches desktop's start_new_strand_mode() which sets is_drawing_new_strand = True
      setCurrentMode(InteractionMode.ATTACH);
    }
  };

  const handleLayerColorChange = (layerId: string, color: string) => {
    // Store layer color (this would typically be stored in layer metadata)
    console.log('Layer color changed:', layerId, color);
  };

  // Strand management
  const handleStrandSelected = (strandId: string, layerId: string) => {
    setCanvasState({
      ...canvasState,
      selectedStrandId: strandId,
      selectedLayerId: layerId,
    });
  };

  const handleStrandMoved = (strandId: string, layerId: string, offset: Point) => {
    setCanvasState(prevState => {
      const snapOffset = prevState.gridEnabled
        ? {
            x: Math.round(offset.x / prevState.gridSize) * prevState.gridSize,
            y: Math.round(offset.y / prevState.gridSize) * prevState.gridSize,
          }
        : offset;

      const translateLayer = (layer: Layer | GroupLayer): Layer | GroupLayer => {
        if ('layers' in layer) {
          return {
            ...layer,
            layers: layer.layers.map(child => translateLayer(child)),
          };
        }
        if (layer.id !== layerId) {
          return layer;
        }
        return {
          ...layer,
          strands: layer.strands.map((strand: Strand) =>
            strand.id === strandId ? StrandModel.translate(strand, snapOffset) : strand,
          ),
        };
      };

      const translatedLayers = prevState.layers.map(layer => translateLayer(layer));

      const collectStrands = (layers: (Layer | GroupLayer)[], acc: Strand[] = []): Strand[] => {
        layers.forEach(layer => {
          if ('layers' in layer) {
            collectStrands(layer.layers, acc);
            return;
          }
          layer.strands.forEach((strand: Strand) => acc.push(strand));
        });
        return acc;
      };

      const allStrands = collectStrands(translatedLayers);
      const strandMap = new Map<string, Strand>(allStrands.map(strand => [strand.id, strand]));

      const updateAttachments = (layer: Layer | GroupLayer): Layer | GroupLayer => {
        if ('layers' in layer) {
          return {
            ...layer,
            layers: layer.layers.map(child => updateAttachments(child)),
          };
        }
        return {
          ...layer,
          strands: layer.strands.map((strand: Strand) =>
            AttachedStrandModel.isAttached(strand)
              ? AttachedStrandModel.updateAttachedPositions(strand, strandMap)
              : strand,
          ),
        };
      };

      const finalLayers = translatedLayers.map(layer => updateAttachments(layer));

      return {
        ...prevState,
        layers: finalLayers,
      };
    });
  };

  const handleStrandMoveStart = (strandId: string, layerId: string) => {
    saveStateForUndo('Move strand');
    layerStateManager.startMovementOperation(canvasState.layers);
  };

  const handleStrandMoveEnd = (strandId: string, layerId: string) => {
    layerStateManager.endMovementOperation();
    updateUndoRedoState();
  };

  // Handle endpoint movement (desktop-style move mode)
  // Matches desktop move_mode.py where individual endpoints are moved
  const handleStrandEndpointMove = (
    strandId: string,
    layerId: string,
    side: 0 | 1,
    newPos: Point,
  ) => {
    setCanvasState(prevState => {
      const updateLayer = (layer: Layer | GroupLayer): Layer | GroupLayer => {
        if ('layers' in layer) {
          return {
            ...layer,
            layers: layer.layers.map(child => updateLayer(child)),
          };
        }
        if (layer.id !== layerId) {
          return layer;
        }
        return {
          ...layer,
          strands: layer.strands.map((strand: Strand) => {
            if (strand.id !== strandId) {
              return strand;
            }
            // Update the appropriate endpoint
            if (side === 0) {
              // Update start point
              const newSegments = strand.segments.map((seg, idx) => {
                if (idx === 0) {
                  return {
                    ...seg,
                    bezier: {
                      ...seg.bezier,
                      start: newPos,
                      // Also update control point 1 if it was at the old start
                      control1: seg.bezier.control1.x === seg.bezier.start.x &&
                                seg.bezier.control1.y === seg.bezier.start.y
                        ? newPos
                        : seg.bezier.control1,
                    },
                  };
                }
                return seg;
              });
              return {
                ...strand,
                segments: newSegments,
                start: newPos,
                controlPoint1: strand.controlPoint1?.x === strand.start?.x &&
                               strand.controlPoint1?.y === strand.start?.y
                  ? newPos
                  : strand.controlPoint1,
              };
            } else {
              // Update end point
              const newSegments = strand.segments.map((seg, idx) => {
                if (idx === strand.segments.length - 1) {
                  return {
                    ...seg,
                    bezier: {
                      ...seg.bezier,
                      end: newPos,
                      // Also update control point 2 if it was at the old end
                      control2: seg.bezier.control2.x === seg.bezier.end.x &&
                                seg.bezier.control2.y === seg.bezier.end.y
                        ? newPos
                        : seg.bezier.control2,
                    },
                  };
                }
                return seg;
              });
              return {
                ...strand,
                segments: newSegments,
                end: newPos,
                controlPoint2: strand.controlPoint2?.x === strand.end?.x &&
                               strand.controlPoint2?.y === strand.end?.y
                  ? newPos
                  : strand.controlPoint2,
              };
            }
          }),
        };
      };

      return {
        ...prevState,
        layers: prevState.layers.map(layer => updateLayer(layer)),
      };
    });
  };

  // Handle strand updates (for updating parent when child is attached)
  const handleStrandUpdated = (layerId: string, updatedStrand: Strand) => {
    setCanvasState(prevState => {
      const updateLayer = (layer: Layer | GroupLayer): Layer | GroupLayer => {
        if ('layers' in layer) {
          return {
            ...layer,
            layers: layer.layers.map(child => updateLayer(child)),
          };
        }
        if (layer.id !== layerId) {
          return layer;
        }
        return {
          ...layer,
          strands: layer.strands.map((strand: Strand) =>
            strand.id === updatedStrand.id ? updatedStrand : strand,
          ),
        };
      };

      return {
        ...prevState,
        layers: prevState.layers.map(layer => updateLayer(layer)),
      };
    });
  };

  const handleStrandCreated = (layerId: string, strand: Strand) => {
    console.log('handleStrandCreated called - layerId:', layerId, 'strand:', strand.id);

    // Use functional update to avoid stale state issues
    setCanvasState(prevState => {
      console.log('Current layers:', prevState.layers.map(l => ({id: l.id, name: l.name, hasStrands: 'strands' in l})));

      const newLayers = prevState.layers.map(layer => {
        if (layer.id === layerId && 'strands' in layer) {
          console.log('Adding strand to layer:', layer.id);
          const updatedLayer = LayerModel.addStrand(layer as Layer, strand);
          console.log('Layer now has strands:', updatedLayer.strands.length);
          return updatedLayer;
        }
        return layer;
      });

      console.log('Setting new canvas state with layers:', newLayers.length);

      // Save for undo after we have the new state
      undoManager.saveState(prevState, 'Create strand');
      updateUndoRedoState();

      return {
        ...prevState,
        layers: newLayers,
        selectedStrandId: strand.id,
      };
    });
  };

  const handleControlPointMove = (
    strandId: string,
    layerId: string,
    segmentIndex: number,
    pointType: string,
    newPos: Point,
  ) => {
    const newLayers = canvasState.layers.map(layer => {
      if (layer.id === layerId && 'strands' in layer) {
        return {
          ...layer,
          strands: layer.strands.map(strand => {
            if (strand.id === strandId) {
              const newSegments = strand.segments.map((seg, idx) => {
                if (idx === segmentIndex) {
                  return {
                    ...seg,
                    bezier: {
                      ...seg.bezier,
                      [pointType]: newPos,
                    },
                  };
                }
                return seg;
              });
              return {...strand, segments: newSegments};
            }
            return strand;
          }),
        };
      }
      return layer;
    });
    setCanvasState({...canvasState, layers: newLayers});
  };

  // File operations
  const handleSave = async () => {
    const success = await SaveLoadManager.saveToFile(projectName, canvasState);
    if (success) {
      Alert.alert(t('saved'), `${projectName} saved`);
    } else {
      Alert.alert(t('error'), t('saveFailed'));
    }
  };

  const handleLoad = () => {
    navigation.navigate('ProjectManager' as never);
  };

  const handleExport = async () => {
    const svg = exportToSVGCropped(canvasState);
    const success = await saveSVGToFile(`${projectName}-export`, svg);

    if (success) {
      Alert.alert(t('exported'), t('exportSuccess'));
    } else {
      Alert.alert(t('error'), t('exportFailed'));
    }
  };

  const handleSaveImage = async () => {
    await handleExport();
  };

  const formatLayerState = () => {
    const state = layerStateManager.saveCurrentState(canvasState);
    const formatList = (title: string, items: string[] | null) => {
      if (!items || items.length === 0) {
        return `${title}:\n  (empty)\n`;
      }
      return `${title}:\n${items.map(item => `  - ${item}`).join('\n')}\n`;
    };

    const formatDict = (title: string, obj: Record<string, unknown>) => {
      const keys = Object.keys(obj);
      if (keys.length === 0) {
        return `${title}:\n  (empty)\n`;
      }
      return `${title}:\n${keys
        .map(key => `  ${key}: ${JSON.stringify(obj[key])}`)
        .join('\n')}\n`;
    };

    const lines = [
      formatList('Order', state.order),
      formatDict('Connections', state.connections),
      formatList('Masked Layers', state.maskedLayers),
      formatDict('Colors', state.colors),
      formatDict('Positions', state.positions),
      `Selected Strand:\n  ${state.selectedStrand ?? 'null'}\n`,
      `Newest Strand:\n  ${state.newestStrand ?? 'null'}\n`,
      `Newest Layer:\n  ${state.newestLayer ?? 'null'}\n`,
    ];

    return lines.join('\n');
  };

  const handleLayerState = () => {
    if (layerStateVisible) {
      setLayerStateVisible(false);
      return;
    }
    setLayerStateText(formatLayerState());
    setLayerStateVisible(true);
  };

  const handleSettings = () => {
    navigation.navigate('Settings' as never);
  };

  return (
    <View style={styles.container}>
      <StatusBar hidden />

      {/* Top toolbar - matches desktop button bar */}
      <Toolbar
        currentMode={currentMode}
        onModeChange={setCurrentMode}
        gridEnabled={canvasState.gridEnabled}
        onToggleGrid={handleToggleGrid}
        showControlPoints={showControlPoints}
        onToggleControlPoints={() => setShowControlPoints(!showControlPoints)}
        showShadows={showShadows}
        onToggleShadows={() => setShowShadows(!showShadows)}
        onSave={handleSave}
        onLoad={handleLoad}
        onSaveImage={handleSaveImage}
        onLayerState={handleLayerState}
        layerStateActive={layerStateVisible}
        onSettings={handleSettings}
      />

      {/* Main content area - horizontal split like desktop */}
      <View style={styles.mainContent}>
        {/* Canvas area (left/center - takes most space) */}
        <View style={styles.canvasArea}>
          <EnhancedStrandCanvas
            canvasState={canvasState}
            currentMode={currentMode}
            currentColor={currentColor}
            currentWidth={currentWidth}
            showControlPoints={showControlPoints}
            showShadows={showShadows}
            onStrandSelected={handleStrandSelected}
            onStrandMoveStart={handleStrandMoveStart}
            onStrandMoved={handleStrandMoved}
            onStrandMoveEnd={handleStrandMoveEnd}
            onStrandCreated={handleStrandCreated}
            onControlPointMove={handleControlPointMove}
            onStrandEndpointMove={handleStrandEndpointMove}
            onStrandUpdated={handleStrandUpdated}
          />
        </View>

        {/* Layer panel (right side - fixed width like desktop) */}
        <LayerPanel
          layers={canvasState.layers}
          selectedLayerId={canvasState.selectedLayerId}
          zoom={canvasState.zoom}
          canUndo={canUndo}
          canRedo={canRedo}
          isPanMode={currentMode === InteractionMode.PAN}
          currentColor={currentColor}
          onLayerSelect={handleLayerSelect}
          onLayerToggleVisibility={handleLayerToggleVisibility}
          onLayerToggleLock={handleLayerToggleLock}
          onLayerDelete={handleLayerDelete}
          onLayerAdd={handleLayerAdd}
          onLayerColorChange={handleLayerColorChange}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetView={handleResetView}
          onUndo={handleUndo}
          onRedo={handleRedo}
          onTogglePanMode={() =>
            setCurrentMode(currentMode === InteractionMode.PAN ? InteractionMode.SELECT : InteractionMode.PAN)
          }
          onColorChange={setCurrentColor}
          onResetStates={handleResetStates}
          onRefreshLayers={handleRefreshLayers}
          onDeselectAll={handleDeselectAll}
          onDrawNamesToggle={() => {}}
          onToggleLockMode={() => {}}
          onCreateGroup={() => Alert.alert(t('error'), 'Not implemented')}
        />
      </View>

      <Modal visible={layerStateVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView style={styles.modalScroll}>
              <Text style={styles.modalText}>{layerStateText}</Text>
            </ScrollView>
            <TouchableOpacity
              style={styles.modalCloseBtn}
              onPress={() => setLayerStateVisible(false)}>
              <Text style={styles.modalCloseText}>{t('close')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ECECEC',
  },
  mainContent: {
    flex: 1,
    flexDirection: 'row',
  },
  canvasArea: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    maxHeight: '80%',
    backgroundColor: '#ECECEC',
    borderRadius: 6,
    padding: 12,
  },
  modalScroll: {
    marginBottom: 12,
  },
  modalText: {
    color: '#000000',
    fontSize: 12,
  },
  modalCloseBtn: {
    alignSelf: 'center',
    backgroundColor: '#E8E8E8',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#B0B0B0',
  },
  modalCloseText: {
    color: '#000000',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default MainScreen;
