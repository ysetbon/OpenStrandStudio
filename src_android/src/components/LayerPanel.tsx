// Layer Panel component - Desktop-aligned layout
import React, {useState} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from 'react-native';
import {useTranslation} from 'react-i18next';
import {Layer, GroupLayer} from '../types';
import {LayerModel} from '../models/Layer';

const LAYER_COLORS = [
  {fill: '#C8AAE6', border: '#9B7BBF'}, // Purple (Set 1)
  {fill: '#AAE6C8', border: '#7BBF9B'}, // Green (Set 2)
  {fill: '#E6AAC8', border: '#BF7B9B'}, // Pink (Set 3)
  {fill: '#AAC8E6', border: '#7B9BBF'}, // Blue (Set 4)
  {fill: '#E6C8AA', border: '#BF9B7B'}, // Orange (Set 5)
  {fill: '#C8E6AA', border: '#9BBF7B'}, // Lime (Set 6)
  {fill: '#E6AAAA', border: '#BF7B7B'}, // Red (Set 7)
  {fill: '#AAE6E6', border: '#7BBFBF'}, // Cyan (Set 8)
];

interface LayerPanelProps {
  layers: (Layer | GroupLayer)[];
  selectedLayerId: string | null;
  zoom: number;
  canUndo: boolean;
  canRedo: boolean;
  isPanMode: boolean;
  currentColor: string;
  onLayerSelect: (layerId: string) => void;
  onLayerToggleVisibility: (layerId: string) => void;
  onLayerToggleLock: (layerId: string) => void;
  onLayerDelete: (layerId: string) => void;
  onLayerAdd: () => void;
  onLayerColorChange: (layerId: string, color: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onTogglePanMode: () => void;
  onColorChange: (color: string) => void;
  onResetStates?: () => void;
  onRefreshLayers?: () => void;
  onDeselectAll?: () => void;
  onDrawNamesToggle?: (enabled: boolean) => void;
  onToggleLockMode?: (enabled: boolean) => void;
  onCreateGroup?: () => void;
}

const LayerPanel: React.FC<LayerPanelProps> = ({
  layers,
  selectedLayerId,
  canUndo,
  canRedo,
  isPanMode,
  onLayerSelect,
  onLayerToggleVisibility,
  onLayerToggleLock,
  onLayerDelete,
  onLayerAdd,
  onZoomIn,
  onZoomOut,
  onResetView,
  onUndo,
  onRedo,
  onTogglePanMode,
  onResetStates,
  onRefreshLayers,
  onDeselectAll,
  onDrawNamesToggle,
  onToggleLockMode,
}) => {
  const {t} = useTranslation();
  const [drawNamesEnabled, setDrawNamesEnabled] = useState(false);
  const [lockModeEnabled, setLockModeEnabled] = useState(false);
  const [hideModeEnabled, setHideModeEnabled] = useState(false);

  const getLayerColor = (index: number) => {
    return LAYER_COLORS[index % LAYER_COLORS.length];
  };

  const renderLayerButton = (layer: Layer | GroupLayer, index: number) => {
    const isSelected = layer.id === selectedLayerId;
    const strandCount = LayerModel.countStrands(layer);
    const colors = getLayerColor(index);

    return (
      <TouchableOpacity
        key={layer.id}
        style={[
          styles.layerButton,
          {
            backgroundColor: colors.fill,
            borderColor: isSelected ? '#000000' : colors.border,
            borderWidth: isSelected ? 2 : 1,
          },
        ]}
        onPress={() => onLayerSelect(layer.id)}>
        <Text style={styles.layerName} numberOfLines={1}>
          {layer.name} ({strandCount})
        </Text>
        <View style={styles.layerActions}>
          <TouchableOpacity
            style={styles.layerActionBtn}
            onPress={() => onLayerToggleVisibility(layer.id)}>
            <Text style={styles.layerActionText}>
              {layer.visible ? 'V' : 'H'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.layerActionBtn}
            onPress={() => onLayerToggleLock(layer.id)}>
            <Text style={styles.layerActionText}>
              {layer.locked ? 'L' : 'U'}
            </Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  const handleDrawNames = () => {
    const next = !drawNamesEnabled;
    setDrawNamesEnabled(next);
    if (onDrawNamesToggle) {
      onDrawNamesToggle(next);
    }
  };

  const handleLockMode = () => {
    const next = !lockModeEnabled;
    setLockModeEnabled(next);
    if (onToggleLockMode) {
      onToggleLockMode(next);
    }
  };

  const handleHideMode = () => {
    const next = !hideModeEnabled;
    setHideModeEnabled(next);
  };

  return (
    <View style={styles.container}>
      <View style={styles.leftPanel}>
        {/* Top row: Reset + Undo/Redo */}
        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.roundButton, styles.resetButton]}
            onPress={onResetStates}>
            <Text style={styles.roundButtonText}>{t('reset_states')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.roundButton,
              styles.undoRedoButton,
              !canUndo && styles.roundButtonDisabled,
            ]}
            onPress={onUndo}
            disabled={!canUndo}>
            <Text style={styles.roundButtonText}>U</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.roundButton,
              styles.undoRedoButton,
              !canRedo && styles.roundButtonDisabled,
            ]}
            onPress={onRedo}
            disabled={!canRedo}>
            <Text style={styles.roundButtonText}>R</Text>
          </TouchableOpacity>
        </View>

        {/* Second row: Zoom/Pan */}
        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.roundButton, styles.zoomButton]}
            onPress={onZoomIn}>
            <Text style={styles.roundButtonText}>+</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.roundButton, styles.zoomButton]}
            onPress={onZoomOut}>
            <Text style={styles.roundButtonText}>-</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.roundButton,
              styles.panButton,
              isPanMode && styles.panButtonActive,
            ]}
            onPress={onTogglePanMode}>
            <Text style={styles.roundButtonText}>{t('pan')}</Text>
          </TouchableOpacity>
        </View>

        {/* Third row: Refresh/Center/Hide */}
        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.roundButton, styles.refreshButton]}
            onPress={onRefreshLayers}>
            <Text style={styles.roundButtonText}>{t('refresh')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.roundButton, styles.centerButton]}
            onPress={onResetView}>
            <Text style={styles.roundButtonText}>{t('center_strands')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.roundButton,
              styles.centerButton,
              hideModeEnabled && styles.centerButtonActive,
            ]}
            onPress={handleHideMode}>
            <Text style={styles.roundButtonText}>{t('hide_mode')}</Text>
          </TouchableOpacity>
        </View>

        {/* Layer list */}
        <ScrollView style={styles.layerList}>
          {layers.map((layer, index) => renderLayerButton(layer, index))}
        </ScrollView>

        {/* Bottom buttons */}
        <View style={styles.bottomPanel}>
          <View style={styles.bottomRow}>
            <TouchableOpacity
              style={[styles.bottomButton, styles.drawNamesButton]}
              onPress={handleDrawNames}>
              <Text style={styles.bottomButtonText}>{t('draw_names')}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.bottomButton,
                styles.lockLayersButton,
                lockModeEnabled && styles.lockLayersButtonActive,
              ]}
              onPress={handleLockMode}>
              <Text style={styles.bottomButtonText}>{t('lock_layers')}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.bottomButton,
                styles.addStrandButton,
                lockModeEnabled && styles.bottomButtonDisabled,
              ]}
              onPress={onLayerAdd}
              disabled={lockModeEnabled}>
              <Text style={styles.bottomButtonText}>{t('add_new_strand')}</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.bottomRow}>
            <TouchableOpacity
              style={[
                styles.bottomButton,
                styles.deleteButton,
                (!selectedLayerId || layers.length <= 1) && styles.bottomButtonDisabled,
              ]}
              onPress={() => selectedLayerId && onLayerDelete(selectedLayerId)}
              disabled={!selectedLayerId || layers.length <= 1}>
              <Text style={styles.bottomButtonText}>{t('delete_strand')}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.bottomButton, styles.deselectButton]}
              onPress={onDeselectAll}>
              <Text style={styles.bottomButtonText}>{t('deselect_all')}</Text>
            </TouchableOpacity>
            <View style={styles.bottomButtonSpacer} />
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 320,
    backgroundColor: '#ECECEC',
    borderLeftWidth: 1,
    borderLeftColor: '#C8C8C8',
  },
  leftPanel: {
    flex: 1,
    paddingHorizontal: 6,
    paddingTop: 6,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 6,
  },
  roundButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
    borderWidth: 1,
  },
  roundButtonText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#000000',
    textAlign: 'center',
  },
  roundButtonDisabled: {
    backgroundColor: '#D3D3D3',
    borderColor: '#A9A9A9',
  },
  resetButton: {
    backgroundColor: '#8A2BE2',
    borderColor: '#6A1B9A',
  },
  undoRedoButton: {
    backgroundColor: '#4D9958',
    borderColor: '#3C7745',
  },
  zoomButton: {
    backgroundColor: '#FFD700',
    borderColor: '#B8860B',
  },
  panButton: {
    backgroundColor: '#8B0000',
    borderColor: '#4B0000',
  },
  panButtonActive: {
    backgroundColor: '#400000',
    borderColor: '#4B0000',
  },
  refreshButton: {
    backgroundColor: '#32CD32',
    borderColor: '#228B22',
  },
  centerButton: {
    backgroundColor: '#D2B48C',
    borderColor: '#BC9A6A',
  },
  centerButtonActive: {
    backgroundColor: '#654321',
    borderColor: '#A0522D',
  },
  layerList: {
    flex: 1,
    marginVertical: 4,
  },
  layerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
    paddingHorizontal: 6,
    marginBottom: 4,
    borderRadius: 4,
  },
  layerName: {
    color: '#2c3e50',
    fontSize: 11,
    fontWeight: 'bold',
    flex: 1,
  },
  layerActions: {
    flexDirection: 'row',
  },
  layerActionBtn: {
    paddingHorizontal: 3,
  },
  layerActionText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  bottomPanel: {
    paddingBottom: 6,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  bottomButton: {
    flex: 1,
    marginHorizontal: 3,
    borderWidth: 1,
    borderColor: '#888888',
    borderRadius: 4,
    paddingVertical: 6,
  },
  bottomButtonSpacer: {
    flex: 1,
    marginHorizontal: 3,
  },
  bottomButtonText: {
    color: '#000000',
    fontSize: 11,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  bottomButtonDisabled: {
    backgroundColor: '#D3D3D3',
    borderColor: '#CCCCCC',
  },
  drawNamesButton: {
    backgroundColor: '#E07BDB',
  },
  lockLayersButton: {
    backgroundColor: 'orange',
  },
  lockLayersButtonActive: {
    backgroundColor: '#E69500',
  },
  addStrandButton: {
    backgroundColor: 'lightgreen',
  },
  deleteButton: {
    backgroundColor: '#FF6B6B',
  },
  deselectButton: {
    backgroundColor: '#76ACDC',
  },
});

export default LayerPanel;
