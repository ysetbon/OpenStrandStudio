// Layer Panel component - Layer management UI
// Ported from src/layer_panel.py

import React from 'react';
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

interface LayerPanelProps {
  layers: (Layer | GroupLayer)[];
  selectedLayerId: string | null;
  onLayerSelect: (layerId: string) => void;
  onLayerToggleVisibility: (layerId: string) => void;
  onLayerToggleLock: (layerId: string) => void;
  onLayerDelete: (layerId: string) => void;
  onLayerAdd: () => void;
  onGroupAdd: () => void;
}

const LayerPanel: React.FC<LayerPanelProps> = ({
  layers,
  selectedLayerId,
  onLayerSelect,
  onLayerToggleVisibility,
  onLayerToggleLock,
  onLayerDelete,
  onLayerAdd,
  onGroupAdd,
}) => {
  const {t} = useTranslation();

  const renderLayer = (layer: Layer | GroupLayer, depth: number = 0) => {
    const isSelected = layer.id === selectedLayerId;
    const strandCount = LayerModel.countStrands(layer);

    return (
      <View key={layer.id} style={{marginLeft: depth * 20}}>
        <TouchableOpacity
          style={[styles.layerItem, isSelected && styles.layerItemSelected]}
          onPress={() => onLayerSelect(layer.id)}>
          <View style={styles.layerInfo}>
            <Text style={styles.layerName}>{layer.name}</Text>
            <Text style={styles.layerCount}>({strandCount})</Text>
          </View>

          <View style={styles.layerActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => onLayerToggleVisibility(layer.id)}>
              <Text style={styles.actionIcon}>
                {layer.visible ? '👁️' : '🙈'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => onLayerToggleLock(layer.id)}>
              <Text style={styles.actionIcon}>
                {layer.locked ? '🔒' : '🔓'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => onLayerDelete(layer.id)}>
              <Text style={styles.actionIcon}>🗑️</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>

        {/* Render child layers if it's a group */}
        {LayerModel.isGroupLayer(layer) &&
          layer.expanded &&
          layer.layers.map(childLayer => renderLayer(childLayer, depth + 1))}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('layers')}</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerButton} onPress={onLayerAdd}>
            <Text style={styles.headerButtonText}>+ {t('newLayer')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={onGroupAdd}>
            <Text style={styles.headerButtonText}>+ {t('newGroup')}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.layerList}>
        {layers.map(layer => renderLayer(layer))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#34495e',
    borderTopWidth: 1,
    borderTopColor: '#2c3e50',
    height: 300,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#2c3e50',
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ecf0f1',
  },
  headerActions: {
    flexDirection: 'row',
  },
  headerButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginLeft: 8,
    backgroundColor: '#3498db',
    borderRadius: 4,
  },
  headerButtonText: {
    color: '#ecf0f1',
    fontSize: 12,
  },
  layerList: {
    flex: 1,
  },
  layerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2c3e50',
    backgroundColor: '#34495e',
  },
  layerItemSelected: {
    backgroundColor: '#3498db',
  },
  layerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  layerName: {
    color: '#ecf0f1',
    fontSize: 14,
    fontWeight: '500',
  },
  layerCount: {
    color: '#95a5a6',
    fontSize: 12,
    marginLeft: 8,
  },
  layerActions: {
    flexDirection: 'row',
  },
  actionButton: {
    paddingHorizontal: 8,
  },
  actionIcon: {
    fontSize: 18,
  },
});

export default LayerPanel;
