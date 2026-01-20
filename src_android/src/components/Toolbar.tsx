// Toolbar component - Tool selection and actions
import React from 'react';
import {View, TouchableOpacity, Text, StyleSheet} from 'react-native';
import {useTranslation} from 'react-i18next';
import {InteractionMode} from '../types';

interface ToolbarProps {
  currentMode: InteractionMode;
  onModeChange: (mode: InteractionMode) => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}

const Toolbar: React.FC<ToolbarProps> = ({
  currentMode,
  onModeChange,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
}) => {
  const {t} = useTranslation();

  const tools = [
    {mode: InteractionMode.SELECT, label: t('select'), icon: '👆'},
    {mode: InteractionMode.MOVE, label: t('move'), icon: '✋'},
    {mode: InteractionMode.DRAW, label: t('draw'), icon: '✏️'},
    {mode: InteractionMode.ATTACH, label: t('attach'), icon: '🔗'},
    {mode: InteractionMode.MASK, label: t('mask'), icon: '🎭'},
    {mode: InteractionMode.ROTATE, label: t('rotate'), icon: '🔄'},
  ];

  return (
    <View style={styles.container}>
      {/* Tools */}
      <View style={styles.toolsSection}>
        {tools.map(tool => (
          <TouchableOpacity
            key={tool.mode}
            style={[
              styles.toolButton,
              currentMode === tool.mode && styles.toolButtonActive,
            ]}
            onPress={() => onModeChange(tool.mode)}>
            <Text style={styles.toolIcon}>{tool.icon}</Text>
            <Text style={styles.toolLabel}>{tool.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Undo/Redo */}
      <View style={styles.actionSection}>
        <TouchableOpacity
          style={[styles.actionButton, !canUndo && styles.actionButtonDisabled]}
          onPress={onUndo}
          disabled={!canUndo}>
          <Text style={styles.actionIcon}>↶</Text>
          <Text style={styles.actionLabel}>{t('undo')}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, !canRedo && styles.actionButtonDisabled]}
          onPress={onRedo}
          disabled={!canRedo}>
          <Text style={styles.actionIcon}>↷</Text>
          <Text style={styles.actionLabel}>{t('redo')}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#2c3e50',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#34495e',
  },
  toolsSection: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  toolButton: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    marginHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#34495e',
    minWidth: 60,
  },
  toolButtonActive: {
    backgroundColor: '#3498db',
  },
  toolIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  toolLabel: {
    fontSize: 10,
    color: '#ecf0f1',
  },
  actionSection: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    marginHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#34495e',
    minWidth: 60,
  },
  actionButtonDisabled: {
    opacity: 0.3,
  },
  actionIcon: {
    fontSize: 20,
    color: '#ecf0f1',
    marginBottom: 2,
  },
  actionLabel: {
    fontSize: 10,
    color: '#ecf0f1',
  },
});

export default Toolbar;
