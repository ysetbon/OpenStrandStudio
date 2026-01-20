// Settings Screen
import React, {useState} from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Switch,
} from 'react-native';
import {useTranslation} from 'react-i18next';
import i18n from '../i18n/config';

const SettingsScreen: React.FC = () => {
  const {t} = useTranslation();
  const [language, setLanguage] = useState(i18n.language);
  const [autoSave, setAutoSave] = useState(true);
  const [gridEnabled, setGridEnabled] = useState(false);

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    i18n.changeLanguage(lang);
  };

  const languages = [
    {code: 'en', name: 'English'},
    {code: 'fr', name: 'Français'},
    {code: 'es', name: 'Español'},
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t('language')}</Text>
        {languages.map(lang => (
          <TouchableOpacity
            key={lang.code}
            style={[
              styles.option,
              language === lang.code && styles.optionSelected,
            ]}
            onPress={() => handleLanguageChange(lang.code)}>
            <Text
              style={[
                styles.optionText,
                language === lang.code && styles.optionTextSelected,
              ]}>
              {lang.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t('autoSave')}</Text>
        <View style={styles.switchContainer}>
          <Text style={styles.optionText}>
            Enable automatic saving every 30 seconds
          </Text>
          <Switch value={autoSave} onValueChange={setAutoSave} />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t('showGrid')}</Text>
        <View style={styles.switchContainer}>
          <Text style={styles.optionText}>Display grid on canvas</Text>
          <Switch value={gridEnabled} onValueChange={setGridEnabled} />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.aboutText}>OpenStrand Studio Mobile</Text>
        <Text style={styles.aboutText}>Version 1.0.0</Text>
        <Text style={styles.aboutText}>
          A mobile application for creating strand diagrams and tutorials
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ecf0f1',
  },
  section: {
    backgroundColor: '#fff',
    marginVertical: 8,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  option: {
    padding: 12,
    marginVertical: 4,
    backgroundColor: '#ecf0f1',
    borderRadius: 8,
  },
  optionSelected: {
    backgroundColor: '#3498db',
  },
  optionText: {
    fontSize: 16,
    color: '#2c3e50',
  },
  optionTextSelected: {
    color: '#fff',
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  aboutText: {
    fontSize: 14,
    color: '#7f8c8d',
    marginVertical: 4,
  },
});

export default SettingsScreen;
