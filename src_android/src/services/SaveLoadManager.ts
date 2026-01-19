// Save/Load manager - Handles file persistence
// Ported from src/save_load_manager.py

import AsyncStorage from '@react-native-async-storage/async-storage';
import RNFS from 'react-native-fs';
import {CanvasState} from '../types';

export class SaveLoadManager {
  private static readonly AUTOSAVE_KEY = '@OpenStrand:autosave';
  private static readonly PROJECTS_DIR = `${RNFS.DocumentDirectoryPath}/projects`;

  /**
   * Initialize the save/load manager
   */
  static async initialize(): Promise<void> {
    try {
      // Create projects directory if it doesn't exist
      const exists = await RNFS.exists(SaveLoadManager.PROJECTS_DIR);
      if (!exists) {
        await RNFS.mkdir(SaveLoadManager.PROJECTS_DIR);
      }
    } catch (error) {
      console.error('Failed to initialize SaveLoadManager:', error);
    }
  }

  /**
   * Save canvas state to a file
   */
  static async saveToFile(
    filename: string,
    state: CanvasState,
  ): Promise<boolean> {
    try {
      const filepath = `${SaveLoadManager.PROJECTS_DIR}/${filename}.oss`;
      const data = JSON.stringify(state, null, 2);
      await RNFS.writeFile(filepath, data, 'utf8');
      return true;
    } catch (error) {
      console.error('Failed to save file:', error);
      return false;
    }
  }

  /**
   * Load canvas state from a file
   */
  static async loadFromFile(filename: string): Promise<CanvasState | null> {
    try {
      const filepath = `${SaveLoadManager.PROJECTS_DIR}/${filename}.oss`;
      const exists = await RNFS.exists(filepath);
      if (!exists) {
        return null;
      }

      const data = await RNFS.readFile(filepath, 'utf8');
      const state = JSON.parse(data) as CanvasState;
      return state;
    } catch (error) {
      console.error('Failed to load file:', error);
      return null;
    }
  }

  /**
   * Get list of saved projects
   */
  static async listProjects(): Promise<string[]> {
    try {
      const files = await RNFS.readDir(SaveLoadManager.PROJECTS_DIR);
      return files
        .filter(file => file.name.endsWith('.oss'))
        .map(file => file.name.replace('.oss', ''))
        .sort();
    } catch (error) {
      console.error('Failed to list projects:', error);
      return [];
    }
  }

  /**
   * Delete a project file
   */
  static async deleteProject(filename: string): Promise<boolean> {
    try {
      const filepath = `${SaveLoadManager.PROJECTS_DIR}/${filename}.oss`;
      const exists = await RNFS.exists(filepath);
      if (exists) {
        await RNFS.unlink(filepath);
      }
      return true;
    } catch (error) {
      console.error('Failed to delete project:', error);
      return false;
    }
  }

  /**
   * Auto-save current state
   */
  static async autoSave(state: CanvasState): Promise<boolean> {
    try {
      const data = JSON.stringify(state);
      await AsyncStorage.setItem(SaveLoadManager.AUTOSAVE_KEY, data);
      return true;
    } catch (error) {
      console.error('Failed to auto-save:', error);
      return false;
    }
  }

  /**
   * Load auto-saved state
   */
  static async loadAutoSave(): Promise<CanvasState | null> {
    try {
      const data = await AsyncStorage.getItem(SaveLoadManager.AUTOSAVE_KEY);
      if (!data) {
        return null;
      }
      return JSON.parse(data) as CanvasState;
    } catch (error) {
      console.error('Failed to load auto-save:', error);
      return null;
    }
  }

  /**
   * Clear auto-save
   */
  static async clearAutoSave(): Promise<void> {
    try {
      await AsyncStorage.removeItem(SaveLoadManager.AUTOSAVE_KEY);
    } catch (error) {
      console.error('Failed to clear auto-save:', error);
    }
  }

  /**
   * Export canvas state as JSON string
   */
  static exportAsJSON(state: CanvasState): string {
    return JSON.stringify(state, null, 2);
  }

  /**
   * Import canvas state from JSON string
   */
  static importFromJSON(json: string): CanvasState | null {
    try {
      return JSON.parse(json) as CanvasState;
    } catch (error) {
      console.error('Failed to import JSON:', error);
      return null;
    }
  }

  /**
   * Check if a project exists
   */
  static async projectExists(filename: string): Promise<boolean> {
    try {
      const filepath = `${SaveLoadManager.PROJECTS_DIR}/${filename}.oss`;
      return await RNFS.exists(filepath);
    } catch (error) {
      console.error('Failed to check project existence:', error);
      return false;
    }
  }

  /**
   * Get project file size
   */
  static async getProjectSize(filename: string): Promise<number> {
    try {
      const filepath = `${SaveLoadManager.PROJECTS_DIR}/${filename}.oss`;
      const stat = await RNFS.stat(filepath);
      return stat.size;
    } catch (error) {
      console.error('Failed to get project size:', error);
      return 0;
    }
  }

  /**
   * Rename a project
   */
  static async renameProject(
    oldName: string,
    newName: string,
  ): Promise<boolean> {
    try {
      const oldPath = `${SaveLoadManager.PROJECTS_DIR}/${oldName}.oss`;
      const newPath = `${SaveLoadManager.PROJECTS_DIR}/${newName}.oss`;
      await RNFS.moveFile(oldPath, newPath);
      return true;
    } catch (error) {
      console.error('Failed to rename project:', error);
      return false;
    }
  }
}
