// Project Manager Screen - Manage saved projects
import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import {useTranslation} from 'react-i18next';
import {SaveLoadManager} from '../services/SaveLoadManager';

interface ProjectManagerScreenProps {
  navigation: any;
  onProjectLoad?: (filename: string) => void;
}

interface ProjectItem {
  name: string;
  size: number;
  date: Date;
}

const ProjectManagerScreen: React.FC<ProjectManagerScreenProps> = ({
  navigation,
  onProjectLoad,
}) => {
  const {t} = useTranslation();
  const [projects, setProjects] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProjectName, setNewProjectName] = useState('');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    const projectList = await SaveLoadManager.listProjects();
    setProjects(projectList);
    setLoading(false);
  };

  const handleLoadProject = async (filename: string) => {
    if (onProjectLoad) {
      onProjectLoad(filename);
    }
    navigation.goBack();
  };

  const handleDeleteProject = (filename: string) => {
    Alert.alert(
      t('confirmDelete'),
      `Delete project "${filename}"?`,
      [
        {text: t('cancel'), style: 'cancel'},
        {
          text: t('delete'),
          style: 'destructive',
          onPress: async () => {
            await SaveLoadManager.deleteProject(filename);
            loadProjects();
          },
        },
      ],
    );
  };

  const handleNewProject = () => {
    if (newProjectName.trim()) {
      setShowNewProjectModal(false);
      navigation.navigate('Main', {newProject: true, projectName: newProjectName});
      setNewProjectName('');
    }
  };

  const renderProjectItem = ({item}: {item: string}) => (
    <View style={styles.projectItem}>
      <TouchableOpacity
        style={styles.projectInfo}
        onPress={() => handleLoadProject(item)}>
        <Text style={styles.projectName}>{item}</Text>
        <Text style={styles.projectDetails}>Tap to open</Text>
      </TouchableOpacity>

      <View style={styles.projectActions}>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDeleteProject(item)}>
          <Text style={styles.deleteButtonText}>🗑️</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('openProject')}</Text>
        <TouchableOpacity
          style={styles.newButton}
          onPress={() => setShowNewProjectModal(true)}>
          <Text style={styles.newButtonText}>+ {t('new')}</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading projects...</Text>
        </View>
      ) : projects.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No projects yet</Text>
          <Text style={styles.emptySubtext}>
            Create a new project to get started
          </Text>
        </View>
      ) : (
        <FlatList
          data={projects}
          renderItem={renderProjectItem}
          keyExtractor={item => item}
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* New Project Modal */}
      <Modal
        visible={showNewProjectModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowNewProjectModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{t('newProject')}</Text>

            <TextInput
              style={styles.input}
              placeholder="Project Name"
              value={newProjectName}
              onChangeText={setNewProjectName}
              autoFocus
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setShowNewProjectModal(false);
                  setNewProjectName('');
                }}>
                <Text style={styles.modalButtonText}>{t('cancel')}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.createButton]}
                onPress={handleNewProject}>
                <Text style={styles.modalButtonText}>{t('new')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ecf0f1',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#2c3e50',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ecf0f1',
  },
  newButton: {
    backgroundColor: '#3498db',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  newButtonText: {
    color: '#ecf0f1',
    fontWeight: 'bold',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#7f8c8d',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    color: '#7f8c8d',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#95a5a6',
  },
  listContent: {
    padding: 16,
  },
  projectItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  projectInfo: {
    flex: 1,
  },
  projectName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 4,
  },
  projectDetails: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  projectActions: {
    justifyContent: 'center',
  },
  deleteButton: {
    padding: 8,
  },
  deleteButtonText: {
    fontSize: 24,
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
    padding: 24,
    width: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#2c3e50',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  cancelButton: {
    backgroundColor: '#95a5a6',
  },
  createButton: {
    backgroundColor: '#3498db',
  },
  modalButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default ProjectManagerScreen;
