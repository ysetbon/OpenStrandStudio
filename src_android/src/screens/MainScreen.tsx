// Main Screen - Main application screen
import React, {useState, useEffect} from 'react';
import {View, StyleSheet, TouchableOpacity, Text, Alert} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useTranslation} from 'react-i18next';
import StrandCanvas from '../components/StrandCanvas';
import Toolbar from '../components/Toolbar';
import LayerPanel from '../components/LayerPanel';
import {
  CanvasState,
  InteractionMode,
  Point,
  Layer,
  GroupLayer,
} from '../types';
import {LayerModel} from '../models/Layer';
import {StrandModel} from '../models/Strand';
import {UndoRedoManager} from '../services/UndoRedoManager';
import {SaveLoadManager} from '../services/SaveLoadManager';

const MainScreen: React.FC = () => {
  const navigation = useNavigation();
  const {t} = useTranslation();
  const [undoManager] = useState(() => new UndoRedoManager());

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
    Alert.alert(
      t('confirmDelete'),
      t('confirmDelete'),
      [
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
      ],
    );
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

  const handleStrandSelected = (strandId: string) => {
    setCanvasState({
      ...canvasState,
      selectedStrandId: strandId,
    });
  };

  const handleStrandMoved = (strandId: string, offset: Point) => {
    // TODO: Implement strand movement
    console.log('Strand moved:', strandId, offset);
  };

  const handleCanvasPan = (offset: Point) => {
    setCanvasState({
      ...canvasState,
      panOffset: {
        x: canvasState.panOffset.x + offset.x,
        y: canvasState.panOffset.y + offset.y,
      },
    });
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
        <StrandCanvas
          canvasState={canvasState}
          onStrandSelected={handleStrandSelected}
          onStrandMoved={handleStrandMoved}
          onCanvasPan={handleCanvasPan}
        />
      </View>

      {/* Layer panel */}
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

      {/* Settings button */}
      <TouchableOpacity style={styles.settingsButton} onPress={handleSettings}>
        <Text style={styles.settingsButtonText}>⚙️</Text>
      </TouchableOpacity>
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
  settingsButton: {
    position: 'absolute',
    top: 60,
    right: 16,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#3498db',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  settingsButtonText: {
    fontSize: 24,
  },
});

export default MainScreen;
