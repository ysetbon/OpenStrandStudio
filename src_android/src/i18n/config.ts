// Internationalization configuration
// Based on src/translations.py

import i18n from 'i18next';
import {initReactI18next} from 'react-i18next';

const resources = {
  en: {
    translation: {
      // Common
      ok: 'OK',
      cancel: 'Cancel',
      save: 'Save',
      load: 'Load',
      delete: 'Delete',
      rename: 'Rename',
      new: 'New',
      close: 'Close',

      // Main screen
      mainTitle: 'OpenStrand Studio',
      newProject: 'New Project',
      openProject: 'Open Project',
      saveProject: 'Save Project',
      settings: 'Settings',

      // Tools
      select: 'Select',
      move: 'Move',
      draw: 'Draw',
      attach: 'Attach',
      mask: 'Mask',
      rotate: 'Rotate',
      angleAdjust: 'Angle Adjust',

      // Layer panel
      layers: 'Layers',
      newLayer: 'New Layer',
      newGroup: 'New Group',
      deleteLayer: 'Delete Layer',
      duplicateLayer: 'Duplicate Layer',
      mergeDown: 'Merge Down',

      // Properties
      color: 'Color',
      width: 'Width',
      opacity: 'Opacity',
      visible: 'Visible',
      locked: 'Locked',

      // Settings
      language: 'Language',
      theme: 'Theme',
      autoSave: 'Auto Save',
      gridSize: 'Grid Size',
      showGrid: 'Show Grid',

      // Messages
      projectSaved: 'Project saved successfully',
      projectLoaded: 'Project loaded successfully',
      errorSaving: 'Error saving project',
      errorLoading: 'Error loading project',
      confirmDelete: 'Are you sure you want to delete this?',

      // Undo/Redo
      undo: 'Undo',
      redo: 'Redo',
    },
  },
  fr: {
    translation: {
      ok: 'OK',
      cancel: 'Annuler',
      save: 'Enregistrer',
      load: 'Charger',
      delete: 'Supprimer',
      rename: 'Renommer',
      new: 'Nouveau',
      close: 'Fermer',

      mainTitle: 'OpenStrand Studio',
      newProject: 'Nouveau Projet',
      openProject: 'Ouvrir Projet',
      saveProject: 'Enregistrer Projet',
      settings: 'Paramètres',

      select: 'Sélectionner',
      move: 'Déplacer',
      draw: 'Dessiner',
      attach: 'Attacher',
      mask: 'Masquer',
      rotate: 'Pivoter',
      angleAdjust: 'Ajuster Angle',

      layers: 'Calques',
      newLayer: 'Nouveau Calque',
      newGroup: 'Nouveau Groupe',
      deleteLayer: 'Supprimer Calque',
      duplicateLayer: 'Dupliquer Calque',
      mergeDown: 'Fusionner Vers Bas',

      color: 'Couleur',
      width: 'Largeur',
      opacity: 'Opacité',
      visible: 'Visible',
      locked: 'Verrouillé',

      language: 'Langue',
      theme: 'Thème',
      autoSave: 'Sauvegarde Auto',
      gridSize: 'Taille Grille',
      showGrid: 'Afficher Grille',

      projectSaved: 'Projet enregistré avec succès',
      projectLoaded: 'Projet chargé avec succès',
      errorSaving: 'Erreur lors de l\'enregistrement',
      errorLoading: 'Erreur lors du chargement',
      confirmDelete: 'Êtes-vous sûr de vouloir supprimer ceci?',

      undo: 'Annuler',
      redo: 'Rétablir',
    },
  },
  es: {
    translation: {
      ok: 'OK',
      cancel: 'Cancelar',
      save: 'Guardar',
      load: 'Cargar',
      delete: 'Eliminar',
      rename: 'Renombrar',
      new: 'Nuevo',
      close: 'Cerrar',

      mainTitle: 'OpenStrand Studio',
      newProject: 'Nuevo Proyecto',
      openProject: 'Abrir Proyecto',
      saveProject: 'Guardar Proyecto',
      settings: 'Configuración',

      select: 'Seleccionar',
      move: 'Mover',
      draw: 'Dibujar',
      attach: 'Adjuntar',
      mask: 'Máscara',
      rotate: 'Rotar',
      angleAdjust: 'Ajustar Ángulo',

      layers: 'Capas',
      newLayer: 'Nueva Capa',
      newGroup: 'Nuevo Grupo',
      deleteLayer: 'Eliminar Capa',
      duplicateLayer: 'Duplicar Capa',
      mergeDown: 'Combinar Abajo',

      color: 'Color',
      width: 'Ancho',
      opacity: 'Opacidad',
      visible: 'Visible',
      locked: 'Bloqueado',

      language: 'Idioma',
      theme: 'Tema',
      autoSave: 'Guardado Automático',
      gridSize: 'Tamaño de Cuadrícula',
      showGrid: 'Mostrar Cuadrícula',

      projectSaved: 'Proyecto guardado exitosamente',
      projectLoaded: 'Proyecto cargado exitosamente',
      errorSaving: 'Error al guardar proyecto',
      errorLoading: 'Error al cargar proyecto',
      confirmDelete: '¿Está seguro de que desea eliminar esto?',

      undo: 'Deshacer',
      redo: 'Rehacer',
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
