// Toolbar component - Desktop-like tool selection bar
// Matches the desktop layout: Mask | Select | Attach | Move | Rotate | Grid | Angle | Save | Load | Image | Points | Shadow | State | Settings
import React from 'react';
import {
  View,
  TouchableOpacity,
  Text,
  StyleSheet,
  ScrollView,
  Image,
} from 'react-native';
import {useTranslation} from 'react-i18next';
import {InteractionMode} from '../types';

interface ToolbarProps {
  currentMode: InteractionMode;
  onModeChange: (mode: InteractionMode) => void;
  gridEnabled: boolean;
  onToggleGrid: () => void;
  showControlPoints: boolean;
  onToggleControlPoints: () => void;
  showShadows: boolean;
  onToggleShadows: () => void;
  onSave: () => void;
  onLoad: () => void;
  onSaveImage: () => void;
  onLayerState: () => void;
  layerStateActive?: boolean;
  onSettings: () => void;
}

interface ToolButton {
  id: string;
  label: string;
  mode?: InteractionMode;
  isToggle?: boolean;
  isActive?: boolean;
  onPress: () => void;
  color?: string;
  isDisabled?: boolean;
}

const Toolbar: React.FC<ToolbarProps> = ({
  currentMode,
  onModeChange,
  gridEnabled,
  onToggleGrid,
  showControlPoints,
  onToggleControlPoints,
  showShadows,
  onToggleShadows,
  onSave,
  onLoad,
  onSaveImage,
  onLayerState,
  layerStateActive = false,
  onSettings,
}) => {
  const {t} = useTranslation();

  const modeTools: ToolButton[] = [
    {
      id: 'mask',
      label: t('mask_mode'),
      mode: InteractionMode.MASK,
      onPress: () => onModeChange(InteractionMode.MASK),
      color: '#199693',
    },
    {
      id: 'select',
      label: t('select_mode'),
      mode: InteractionMode.SELECT,
      onPress: () => onModeChange(InteractionMode.SELECT),
      color: '#F1C40F',
    },
    {
      id: 'attach',
      label: t('attach_mode'),
      mode: InteractionMode.ATTACH,
      onPress: () => onModeChange(InteractionMode.ATTACH),
      color: '#9B59B6',
    },
    {
      id: 'move',
      label: t('move_mode'),
      mode: InteractionMode.MOVE,
      onPress: () => onModeChange(InteractionMode.MOVE),
      color: '#D35400',
    },
    {
      id: 'rotate',
      label: t('rotate_mode'),
      mode: InteractionMode.ROTATE,
      onPress: () => onModeChange(InteractionMode.ROTATE),
      color: '#3498DB',
    },
  ];

  const toggleTools: ToolButton[] = [
    {
      id: 'grid',
      label: t('toggle_grid'),
      isToggle: true,
      isActive: gridEnabled,
      onPress: onToggleGrid,
      color: '#E93E3E',
    },
    {
      id: 'angleAdjust',
      label: t('angle_adjust_mode'),
      mode: InteractionMode.ANGLE_ADJUST,
      onPress: () => onModeChange(InteractionMode.ANGLE_ADJUST),
      color: '#B89EE6',
    },
  ];

  const actionTools: ToolButton[] = [
    {
      id: 'save',
      label: t('save'),
      onPress: onSave,
      color: '#E75480',
    },
    {
      id: 'load',
      label: t('load'),
      onPress: onLoad,
      color: '#8D6E63',
    },
    {
      id: 'saveImage',
      label: t('save_image'),
      onPress: onSaveImage,
      color: '#7D344D',
    },
  ];

  const viewTools: ToolButton[] = [
    {
      id: 'controlPoints',
      label: t('toggle_control_points'),
      isToggle: true,
      isActive: showControlPoints,
      onPress: onToggleControlPoints,
      color: '#4CAF50',
    },
    {
      id: 'shadow',
      label: t('toggle_shadow'),
      isToggle: true,
      isActive: showShadows,
      onPress: onToggleShadows,
      color: 'rgba(176, 190, 197, 0.7)',
    },
    {
      id: 'layerState',
      label: t('layer_state'),
      isToggle: true,
      isActive: layerStateActive,
      onPress: onLayerState,
      color: '#FFD700',
    },
  ];

  const renderButton = (tool: ToolButton) => {
    const isActive = tool.mode ? currentMode === tool.mode : tool.isActive;

    return (
      <TouchableOpacity
        key={tool.id}
        style={[
          styles.toolButton,
          {backgroundColor: tool.color || '#E8E8E8'},
          isActive && styles.toolButtonActive,
        ]}
        onPress={tool.onPress}
        disabled={tool.isDisabled}>
        <Text style={styles.toolLabel}>{tool.label}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}>
        <View style={styles.section}>{modeTools.map(renderButton)}</View>
        <View style={styles.separator} />
        <View style={styles.section}>{toggleTools.map(renderButton)}</View>
        <View style={styles.separator} />
        <View style={styles.section}>{actionTools.map(renderButton)}</View>
        <View style={styles.separator} />
        <View style={styles.section}>{viewTools.map(renderButton)}</View>
        <View style={styles.separator} />
        <TouchableOpacity style={styles.settingsButton} onPress={onSettings}>
          <Image
            source={require('../../assets/settings_icon.png')}
            style={styles.settingsIcon}
            resizeMode="contain"
          />
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ECECEC',
    borderBottomWidth: 1,
    borderBottomColor: '#C8C8C8',
    height: 40,
  },
  scrollContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  section: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  toolButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    marginHorizontal: 2,
    borderRadius: 6,
    minWidth: 70,
    height: 32,
  },
  toolButtonActive: {
    borderWidth: 4,
    borderColor: '#000000',
  },
  toolLabel: {
    fontSize: 11,
    color: '#000000',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  separator: {
    width: 1,
    height: 24,
    backgroundColor: '#C8C8C8',
    marginHorizontal: 6,
  },
  settingsButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(150, 150, 150, 1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 4,
  },
  settingsIcon: {
    width: 24,
    height: 24,
  },
});

export default Toolbar;
