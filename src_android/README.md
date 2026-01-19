# OpenStrand Studio Mobile - React Native

This is the React Native implementation of OpenStrand Studio for Android (and potentially iOS).

## Overview

OpenStrand Studio Mobile is a mobile application for creating strand diagrams and tutorials with advanced features like:

- Layer-based design
- Bezier curve-based strand rendering
- Interactive touch gestures
- Undo/Redo functionality
- Multi-language support (EN, FR, ES)
- Auto-save functionality
- Project management

## Architecture

The application is structured as follows:

```
src_android/
├── src/
│   ├── models/          # Data models (Strand, Layer)
│   ├── components/      # React components (StrandCanvas, Toolbar, LayerPanel)
│   ├── screens/         # Screen components (MainScreen, SettingsScreen)
│   ├── utils/           # Utility functions (bezier math, etc.)
│   ├── services/        # Business logic services (UndoRedoManager, SaveLoadManager)
│   ├── i18n/            # Internationalization
│   └── types/           # TypeScript type definitions
├── App.tsx              # Main app entry point
├── index.js             # React Native entry point
├── package.json         # Dependencies
└── tsconfig.json        # TypeScript configuration
```

## Technology Stack

- **React Native 0.73** - Mobile framework
- **TypeScript** - Type safety
- **React Native SVG** - Vector graphics rendering
- **React Native Gesture Handler** - Touch gesture handling
- **React Native Reanimated** - Smooth animations
- **React Navigation** - Screen navigation
- **i18next** - Internationalization
- **AsyncStorage** - Local storage
- **React Native FS** - File system access

## Key Components

### Models

- **Strand.ts** - Core strand data model with Bezier curves
- **Layer.ts** - Layer and group layer management

### Services

- **UndoRedoManager.ts** - Undo/redo functionality with history stack
- **SaveLoadManager.ts** - File persistence and auto-save

### Components

- **StrandCanvas.tsx** - Main canvas for rendering strands using SVG
- **Toolbar.tsx** - Tool selection and actions
- **LayerPanel.tsx** - Layer management UI

### Screens

- **MainScreen.tsx** - Main application screen
- **SettingsScreen.tsx** - Settings and preferences

## Features Implemented

### Core Features

- ✅ Strand data model with Bezier curves
- ✅ Layer management (add, delete, visibility, lock)
- ✅ Group layers
- ✅ Canvas rendering with React Native SVG
- ✅ Undo/Redo functionality
- ✅ Save/Load projects
- ✅ Auto-save
- ✅ Multi-language support (EN, FR, ES)
- ✅ Settings screen

### Partial Implementation

- ⚠️ Touch gestures (pan, tap implemented, but interaction modes need work)
- ⚠️ Strand drawing (model exists, UI interaction needed)
- ⚠️ Strand selection and manipulation
- ⚠️ Masking functionality
- ⚠️ Attach mode

### Not Yet Implemented

- ❌ Full drawing mode with touch
- ❌ Advanced masking with over/under effects
- ❌ Export to image formats
- ❌ Import from desktop version
- ❌ Advanced strand editing (angle adjust, control point editing)
- ❌ Group transformations
- ❌ Shadows and visual effects

## Setup Instructions

### Prerequisites

- Node.js 18+
- React Native development environment
- Android Studio (for Android)
- Xcode (for iOS, macOS only)

### Installation

1. Navigate to the src_android directory:
   ```bash
   cd src_android
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. For Android, install Pods (if needed):
   ```bash
   cd android && ./gradlew clean && cd ..
   ```

4. Start Metro bundler:
   ```bash
   npm start
   ```

5. Run on Android:
   ```bash
   npm run android
   ```

6. Run on iOS (macOS only):
   ```bash
   npm run ios
   ```

## Development

### Adding New Features

1. **Models**: Add data models in `src/models/`
2. **Components**: Add UI components in `src/components/`
3. **Screens**: Add screens in `src/screens/`
4. **Services**: Add business logic in `src/services/`
5. **Utils**: Add utility functions in `src/utils/`

### Code Ported from Python

The following modules were ported from the original Python/PyQt5 implementation:

- `src/strand.py` → `src/models/Strand.ts`
- `src/layer_panel.py` → `src/models/Layer.ts`
- `src/undo_redo_manager.py` → `src/services/UndoRedoManager.ts`
- `src/save_load_manager.py` → `src/services/SaveLoadManager.ts`
- `src/translations.py` → `src/i18n/config.ts`
- Bezier math → `src/utils/bezier.ts`

## Known Limitations

1. **Performance**: SVG rendering may be slower than native canvas on older devices
2. **Complex Curves**: Very complex strands with many segments may impact performance
3. **File Format**: Currently uses JSON format (compatible with desktop version structure)
4. **Touch Interaction**: Advanced gestures need refinement

## Future Enhancements

1. Implement full drawing mode with touch
2. Add advanced masking and over/under effects
3. Optimize rendering performance
4. Add export to PNG/SVG
5. Implement cloud sync
6. Add tutorial/onboarding
7. Implement all interaction modes from desktop version
8. Add gesture-based shortcuts

## Compatibility with Desktop Version

The mobile version uses the same JSON save format as the desktop version, allowing projects to be shared between platforms. However, some features may not be fully compatible yet.

## Contributing

When adding features, ensure:

1. TypeScript types are properly defined
2. Components are tested on both Android and iOS
3. Performance is considered for mobile devices
4. Touch interactions are intuitive
5. Code follows React Native best practices

## License

Same as the main OpenStrand Studio project.
