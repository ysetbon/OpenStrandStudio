// Main Screen - Main application screen with full features
import React, {useState, useEffect} from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  Alert,
  Share,
  Dimensions,
} from 'react-native';
import {useNavigation, useRoute} from '@react-navigation/native';
import {useTranslation} from 'react-i18next';
import EnhancedStrandCanvas from '../components/EnhancedStrandCanvas';
import Toolbar from '../components/Toolbar';
import LayerPanel from '../components/LayerPanel';
import ColorPicker from '../components/ColorPicker';
import {
  CanvasState,
  InteractionMode,
  Point,
  Layer,
  Strand,
} from '../types';
import {LayerModel} from '../models/Layer';
import {StrandModel} from '../models/Strand';
import {UndoRedoManager} from '../services/UndoRedoManager';
import {SaveLoadManager} from '../services/SaveLoadManager';
import {exportToSVGCropped, generateShareData, saveSVGToFile} from '../utils/export';

const MainScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const {t} = useTranslation();
  const [undoManager] = useState(() => new UndoRedoManager());
  const [projectName, setProjectName] = useState('Untitled');
  const [currentColor, setCurrentColor] = useState('#8B4513');
  const [currentWidth, setCurrentWidth] = useState(20);

  // Initial canvas state
  const [canvasState, setCanvasState] = useState<CanvasState>({
    layers: [LayerModel.create('layer-1', 'Layer 1')],
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
  const [showLayerPanel, setShowLayerPanel] = useState(true);

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
    Alert.alert(t('confirmDelete'), t('confirmDelete'), [
      {text: t('cancel'), style: 'cancel'},
      {
        text: t('delete'),
        style: 'destructive',
        onPress: () => {
          saveStateForUndo('Delete layer');
          const newLayers = canvasState.layers.filter(l => l.id !== layerId);
          setCanvasState({
            ...canvasState,
            layers: newLayers,
            selectedLayerId:
              canvasState.selectedLayerId === layerId
                ? null
                : canvasState.selectedLayerId,
          });
        },
      },
    ]);
  };

  const handleLayerAdd = () => {
    saveStateForUndo('Add layer');
    const newLayer = LayerModel.create(
      `layer-${Date.now()}`,
      `Layer ${canvasState.layers.length + 1}`,
    );
    setCanvasState({
      ...canvasState,
      layers: [...canvasState.layers, newLayer],
      selectedLayerId: newLayer.id,
    });
  };

  const handleGroupAdd = () => {
    saveStateForUndo('Add group');
    const newGroup = LayerModel.createGroup(
      `group-${Date.now()}`,
      `Group ${canvasState.layers.length + 1}`,
    );
    setCanvasState({
      ...canvasState,
      layers: [...canvasState.layers, newGroup],
      selectedLayerId: newGroup.id,
    });
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
    saveStateForUndo('Move strand');
    const newLayers = canvasState.layers.map(layer => {
      if (layer.id === layerId && 'strands' in layer) {
        return {
          ...layer,
          strands: layer.strands.map(strand =>
            strand.id === strandId
              ? StrandModel.translate(strand, offset)
              : strand,
          ),
        };
      }
      return layer;
    });
    setCanvasState({...canvasState, layers: newLayers});
  };

  const handleStrandCreated = (layerId: string, strand: Strand) => {
    saveStateForUndo('Create strand');
    const newLayers = canvasState.layers.map(layer => {
      if (layer.id === layerId && 'strands' in layer) {
        return LayerModel.addStrand(layer, strand);
      }
      return layer;
    });
    setCanvasState({
      ...canvasState,
      layers: newLayers,
      selectedStrandId: strand.id,
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
      Alert.alert(t('projectSaved'), `Project "${projectName}" saved successfully`);
    } else {
      Alert.alert(t('errorSaving'), 'Failed to save project');
    }
  };

  const handleExport = async () => {
    const {width, height} = Dimensions.get('window');
    const svg = exportToSVGCropped(canvasState);
    const success = await saveSVGToFile(`${projectName}-export`, svg);

    if (success) {
      Alert.alert('Exported', 'Project exported as SVG successfully');
    } else {
      Alert.alert('Export Failed', 'Failed to export project');
    }
  };

  const handleShare = async () => {
    try {
      const shareData = generateShareData(canvasState, projectName);
      await Share.share({
        title: shareData.title,
        message: shareData.message,
      });
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  const handleOpenProjects = () => {
    navigation.navigate('ProjectManager' as never);
  };

  const handleSettings = () => {
    navigation.navigate('Settings' as never);
  };

  return (
    <View style={styles.container}>
      {/* Top toolbar */}
      <Toolbar
        currentMode={currentMode}
        onModeChange={setCurrentMode}
        onUndo={handleUndo}
        onRedo={handleRedo}
        canUndo={canUndo}
        canRedo={canRedo}
      />

      {/* Main canvas */}
      <View style={styles.canvasContainer}>
        <EnhancedStrandCanvas
          canvasState={canvasState}
          currentMode={currentMode}
          currentColor={currentColor}
          currentWidth={currentWidth}
          onStrandSelected={handleStrandSelected}
          onStrandMoved={handleStrandMoved}
          onStrandCreated={handleStrandCreated}
          onControlPointMove={handleControlPointMove}
        />
      </View>

      {/* Layer panel (collapsible) */}
      {showLayerPanel && (
        <LayerPanel
          layers={canvasState.layers}
          selectedLayerId={canvasState.selectedLayerId}
          onLayerSelect={handleLayerSelect}
          onLayerToggleVisibility={handleLayerToggleVisibility}
          onLayerToggleLock={handleLayerToggleLock}
          onLayerDelete={handleLayerDelete}
          onLayerAdd={handleLayerAdd}
          onGroupAdd={handleGroupAdd}
        />
      )}

      {/* Floating action buttons */}
      <View style={styles.fabContainer}>
        <TouchableOpacity
          style={styles.fab}
          onPress={() => setShowLayerPanel(!showLayerPanel)}>
          <Text style={styles.fabText}>{showLayerPanel ? '📁' : '📂'}</Text>
        </TouchableOpacity>

        <ColorPicker selectedColor={currentColor} onColorChange={setCurrentColor} />

        <TouchableOpacity style={styles.fab} onPress={handleSave}>
          <Text style={styles.fabText}>💾</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.fab} onPress={handleOpenProjects}>
          <Text style={styles.fabText}>📋</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.fab} onPress={handleExport}>
          <Text style={styles.fabText}>📤</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.fab} onPress={handleShare}>
          <Text style={styles.fabText}>🔗</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.fab} onPress={handleSettings}>
          <Text style={styles.fabText}>⚙️</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ecf0f1',
  },
  canvasContainer: {
    flex: 1,
  },
  fabContainer: {
    position: 'absolute',
    right: 16,
    top: 100,
    alignItems: 'flex-end',
  },
  fab: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#3498db',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 8,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  fabText: {
    fontSize: 24,
  },
});

export default MainScreen;
