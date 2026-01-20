// Color Picker component
import React, {useState} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  TextInput,
  ScrollView,
} from 'react-native';
import {useTranslation} from 'react-i18next';

interface ColorPickerProps {
  selectedColor: string;
  onColorChange: (color: string) => void;
}

const PRESET_COLORS = [
  '#C8AAE6', // Purple (default desktop color - Set 1)
  '#AAE6C8', // Green (Set 2)
  '#E6AAC8', // Pink (Set 3)
  '#AAC8E6', // Blue (Set 4)
  '#E6C8AA', // Orange (Set 5)
  '#C8E6AA', // Lime (Set 6)
  '#E6AAAA', // Red (Set 7)
  '#AAE6E6', // Cyan (Set 8)
  '#8B4513', // Brown
  '#D2691E', // Chocolate
  '#000000', // Black
  '#808080', // Gray
  '#FFFFFF', // White
  '#FF0000', // Red
  '#00FF00', // Green
  '#0000FF', // Blue
  '#FFFF00', // Yellow
  '#FF00FF', // Magenta
];

const ColorPicker: React.FC<ColorPickerProps> = ({selectedColor, onColorChange}) => {
  const {t} = useTranslation();
  const [modalVisible, setModalVisible] = useState(false);
  const [customColor, setCustomColor] = useState(selectedColor);

  const handlePresetColor = (color: string) => {
    onColorChange(color);
    setModalVisible(false);
  };

  const handleCustomColor = () => {
    // Validate hex color
    if (/^#[0-9A-F]{6}$/i.test(customColor)) {
      onColorChange(customColor);
      setModalVisible(false);
    }
  };

  return (
    <View>
      <TouchableOpacity
        style={styles.colorButton}
        onPress={() => setModalVisible(true)}>
        <View style={[styles.colorPreview, {backgroundColor: selectedColor}]} />
        <Text style={styles.colorButtonText}>{t('color')}</Text>
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{t('color')}</Text>

            <ScrollView style={styles.colorGrid}>
              <View style={styles.colorRow}>
                {PRESET_COLORS.map(color => (
                  <TouchableOpacity
                    key={color}
                    style={[
                      styles.colorSwatch,
                      {backgroundColor: color},
                      selectedColor === color && styles.colorSwatchSelected,
                    ]}
                    onPress={() => handlePresetColor(color)}>
                    {selectedColor === color && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>

            <View style={styles.customColorSection}>
              <Text style={styles.customColorLabel}>Custom Hex Color:</Text>
              <View style={styles.customColorInput}>
                <TextInput
                  style={styles.hexInput}
                  value={customColor}
                  onChangeText={setCustomColor}
                  placeholder="#000000"
                  maxLength={7}
                  autoCapitalize="characters"
                />
                <TouchableOpacity
                  style={styles.applyButton}
                  onPress={handleCustomColor}>
                  <Text style={styles.applyButtonText}>Apply</Text>
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setModalVisible(false)}>
              <Text style={styles.closeButtonText}>{t('close')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  colorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#34495e',
    borderRadius: 8,
  },
  colorPreview: {
    width: 30,
    height: 30,
    borderRadius: 15,
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#ecf0f1',
  },
  colorButtonText: {
    color: '#ecf0f1',
    fontSize: 14,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: '90%',
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#2c3e50',
  },
  colorGrid: {
    maxHeight: 300,
  },
  colorRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
  },
  colorSwatch: {
    width: 50,
    height: 50,
    margin: 8,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: '#ddd',
    justifyContent: 'center',
    alignItems: 'center',
  },
  colorSwatchSelected: {
    borderColor: '#3498db',
    borderWidth: 3,
  },
  checkmark: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    textShadowColor: '#000',
    textShadowOffset: {width: 1, height: 1},
    textShadowRadius: 2,
  },
  customColorSection: {
    marginTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    paddingTop: 16,
  },
  customColorLabel: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 8,
  },
  customColorInput: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  hexInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginRight: 8,
  },
  applyButton: {
    backgroundColor: '#3498db',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  applyButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  closeButton: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#95a5a6',
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default ColorPicker;
