# OpenStrand Studio - Project Overview (Version 1.0 - Draft)

## Table of Contents
1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [User Interface Structure](#user-interface-structure)
5. [Drawing Modes and Tools](#drawing-modes-and-tools)
6. [Data Management](#data-management)
7. [File Structure](#file-structure)
8. [Getting Started for Users](#getting-started-for-users)

## Introduction

OpenStrand Studio is a specialized PyQt5-based application designed for creating and manipulating strand-based graphics, particularly for rope work, knots, and textile patterns. The application provides a comprehensive set of tools for drawing, editing, and organizing strand structures with sophisticated layer management and multiple drawing modes.

## Architecture Overview

The application follows a Model-View-Controller (MVC) pattern with the following main components:

```
main.py → MainWindow → StrandDrawingCanvas ← LayerPanel
    ↓                      ↓                    ↓
Settings &             Various Modes        Layer Management
Initialization        (Attach, Move, etc.)   & Undo/Redo
```

## Core Components

### 1. Application Entry Point (`main.py:176-784`)
- **Purpose**: Application initialization and window management
- **Key Features**:
  - Multi-monitor support with intelligent window positioning
  - User settings loading (theme, language, shadow colors, etc.)
  - PyQt5 application setup with high-DPI support
  - Window restoration and screen management

### 2. Main Window (`main_window.py:37-400`)
- **Purpose**: Primary application window and UI coordination
- **Key Components**:
  - Button toolbar for mode switching
  - Canvas and layer panel integration
  - Settings dialog management
  - Language and theme management
  - Splitter layout for resizable panels

### 3. Strand Drawing Canvas (`strand_drawing_canvas.py:33-100`)
- **Purpose**: Core drawing surface and strand manipulation
- **Key Features**:
  - High-DPI rendering with supersampling
  - Multiple drawing modes (attach, move, rotate, etc.)
  - Grid system with snap-to-grid functionality
  - Real-time strand preview and manipulation
  - Signal-based communication with other components

### 4. Layer Panel (`layer_panel.py:46-100`)
- **Purpose**: Layer management and organization interface
- **Key Features**:
  - Numbered layer buttons for each strand
  - Drag-and-drop layer reordering
  - Group management functionality
  - Undo/redo system integration
  - Custom tooltips and visual feedback

## User Interface Structure

### Main Interface Layout
```
┌─────────────────────────────────────────────────────────────┐
│ [Attach] [Move] [Rotate] [Grid] [Angle] [Save] [Load] [⚙️]   │
├─────────────────────────────────┬───────────────────────────┤
│                                 │   Layer Panel             │
│                                 │  ┌─────────────────────┐  │
│                                 │  │ [1] [2] [3] [4] ... │  │
│          Drawing Canvas         │  │                     │  │
│                                 │  │ Group Controls      │  │
│                                 │  │                     │  │
│                                 │  │ Undo/Redo          │  │
│                                 │  └─────────────────────┘  │
└─────────────────────────────────┴───────────────────────────┘
```

### Button Toolbar Features
- **Mode Buttons**: Attach, Move, Rotate, Angle Adjust, Select, Mask modes
- **Utility Buttons**: Toggle Grid, Save/Load projects, Export images
- **Settings Button**: Access to application preferences

## Drawing Modes and Tools

### 1. Attach Mode (`attach_mode.py`)
- **Purpose**: Create new strands by drawing paths
- **Usage**: Click and drag to create strand paths
- **Features**: 
  - Real-time path preview
  - Control point creation
  - Automatic strand generation

### 2. Move Mode (`move_mode.py`)
- **Purpose**: Reposition and modify existing strands
- **Usage**: Select and drag strands or control points
- **Features**:
  - Multi-strand selection
  - Control point manipulation
  - Constrained movement options

### 3. Rotate Mode (`rotate_mode.py`)
- **Purpose**: Rotate strands around their center points
- **Usage**: Select strand and drag to rotate
- **Features**:
  - Visual rotation indicators
  - Angle snapping
  - Multi-strand rotation

### 4. Angle Adjust Mode (`angle_adjust_mode.py`)
- **Purpose**: Fine-tune strand angles and orientations
- **Usage**: Precise angle adjustments for selected strands

### 5. Mask Mode (`mask_mode.py`)
- **Purpose**: Create masked layers and visual effects
- **Usage**: Define mask regions for strand visibility control

### 6. Select Mode (`select_mode.py`)
- **Purpose**: General selection and properties editing
- **Usage**: Click to select strands for property modification

## Data Management

### Strand Data Structure
- **Strand Class** (`strand.py`): Base class for all strand types
- **Attached Strand** (`attached_strand.py`): Strands connected to other strands
- **Masked Strand** (`masked_strand.py`): Strands with visibility masks

### State Management
- **Undo/Redo System** (`undo_redo_manager.py`): Complete state history tracking
- **Layer State Manager** (`layer_state_manager.py`): Layer organization and persistence
- **Save/Load Manager** (`save_load_manager.py`): Project file handling

### File Formats
- **Project Files**: JSON-based strand and layer data
- **Image Export**: PNG/JPEG rendering capabilities
- **Settings Storage**: User preferences in application data directory

## File Structure

```
src/
├── main.py                    # Application entry point
├── main_window.py            # Primary window class
├── strand_drawing_canvas.py  # Core drawing functionality
├── layer_panel.py           # Layer management interface
├── documentation/           # Project documentation (this folder)
│   └── Project_Overview_v1.md
├── modes/                   # Drawing mode implementations
│   ├── attach_mode.py
│   ├── move_mode.py
│   ├── rotate_mode.py
│   ├── angle_adjust_mode.py
│   ├── mask_mode.py
│   └── select_mode.py
├── data_structures/         # Core data classes
│   ├── strand.py
│   ├── attached_strand.py
│   └── masked_strand.py
├── managers/               # State and system management
│   ├── save_load_manager.py
│   ├── undo_redo_manager.py
│   └── layer_state_manager.py
├── ui_components/          # Custom UI elements
│   ├── numbered_layer_button.py
│   ├── settings_dialog.py
│   └── splitter_handle.py
└── utilities/              # Helper functions and utilities
    ├── render_utils.py
    ├── translations.py
    └── shader_utils.py
```

## Getting Started for Users

### Installation
1. Ensure Python 3.7+ and PyQt5 are installed
2. Navigate to the project directory
3. Run: `python src/main.py`

### Basic Workflow
1. **Start Drawing**: Click "Attach Mode" and draw your first strand
2. **Organize**: Use the layer panel to manage multiple strands
3. **Edit**: Switch to "Move Mode" to adjust positions
4. **Refine**: Use "Angle Adjust Mode" for precise positioning
5. **Save**: Export your work as an image or save as a project

### Key Features to Explore
- **Grid Snapping**: Enable grid for precise alignment
- **Layer Groups**: Organize complex projects with grouped layers
- **Undo/Redo**: Full history tracking for all operations
- **Multi-language Support**: Available in multiple languages
- **Theme System**: Customize the application appearance

---

**Note**: This is Version 1.0 (Draft) of the project overview. Future versions will include more detailed technical specifications, API documentation, and expanded user guides.