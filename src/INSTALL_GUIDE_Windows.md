# Installation Guide for Windows

## Version 1.101 - Released August 11, 2025

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

## Installation Methods

### Method 1: Using Anaconda (Recommended for beginners)

1. Install Anaconda from https://www.anaconda.com/download

2. Open Anaconda Prompt

3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/OpenStrandStudio.git
   cd OpenStrandStudio/src
   ```

4. Install dependencies:
   ```bash
   conda install pyqt pillow
   ```

5. Run the application:
   ```bash
   python main.py
   ```

### Method 2: Using pip with virtual environment

1. Open Command Prompt or PowerShell

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/OpenStrandStudio.git
   cd OpenStrandStudio/src
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install PyQt5 pillow
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## Building Executable (.exe)

### Method 1: Using spec file with virtual environment (BEST METHOD - Recommended)

1. Open Command Prompt or PowerShell and navigate to the src directory:
   ```bash
   cd C:\path\to\OpenStrandStudio\src
   ```

2. Run the provided build script:
   - In Command Prompt:
     ```cmd
     build_with_venv.bat
     ```
   - In PowerShell:
     ```powershell
     .\build_with_venv.bat
     ```

   This script will:
   - Create a clean virtual environment
   - Install required dependencies
   - Build the executable using the OpenStrandStudio.spec file
   - Include all resources (icons, flags, mp4, samples, SVG images)
   - Place the .exe in the `dist` folder

   **Why this is the BEST method:**
   - Uses a spec file for consistent builds
   - Automatically includes all SVG files from images folder
   - Clean virtual environment prevents DLL conflicts
   - All resources properly bundled in one executable

### Method 2: Using Anaconda environment

1. Open Anaconda Prompt and navigate to the src directory:
   ```bash
   cd C:\path\to\OpenStrandStudio\src
   ```

2. Run the Windows-specific build script:
   - In Anaconda Prompt/Command Prompt:
     ```cmd
     build_windows.bat
     ```
   - In PowerShell:
     ```powershell
     .\build_windows.bat
     ```

   This script will:
   - Set up the proper PATH for Anaconda's Qt libraries
   - Build the executable using the OpenStrandStudio.spec file
   - Include all resources (icons, flags, mp4, samples, SVG images)
   - Place the .exe in the `dist` folder

### Method 3: Manual PyInstaller build using spec file

1. If using Anaconda, first set the PATH:
   ```powershell
   $env:PATH = "C:\ProgramData\Anaconda3\Library\bin;$env:PATH"
   ```

2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

3. Build the executable using the spec file:
   ```bash
   pyinstaller OpenStrandStudio.spec
   ```
   
   Note: The spec file includes all necessary resources:
   - Icons (box_stitch.ico, settings_icon.png)
   - Flags folder with country flags
   - MP4 tutorial videos
   - Sample JSON files
   - SVG images (shapes and guides)

## Troubleshooting

### DLL Load Failed Error

If you encounter "DLL load failed while importing QtWidgets", this is typically due to PyQt5 DLL conflicts with Anaconda. Solutions:

1. Use the `build_with_venv.bat` script which creates a clean environment
2. Or manually add Anaconda's library path before building:
   ```powershell
   $env:PATH = "C:\ProgramData\Anaconda3\Library\bin;$env:PATH"
   ```

### Missing Dependencies

If the application fails to start, ensure all dependencies are installed:
```bash
pip install --upgrade PyQt5 pillow
```

### Icon Not Showing

Ensure `box_stitch.ico` and `settings_icon.png` are in the same directory as `main.py`

### Missing Flag Images

Ensure the `flags` directory with country flag PNG files (us.png, fr.png, it.png, es.png, pt.png, il.png) is in the same directory as `main.py`

## Creating a Windows Installer

After building the .exe, create a professional installer using Inno Setup (Recommended):

### Using Inno Setup (RECOMMENDED)

1. Install Inno Setup from https://jrsoftware.org/isdl.php

2. Use the provided Inno Setup script:
   - Navigate to `src\inno setup\`
   - Open `OpenStrand Studio1_102.iss` in Inno Setup Compiler
   - Click "Compile" to create the installer

3. The installer will be created in the `dist` folder with features:
   - Multi-language support (7 languages)
   - Start Menu shortcuts
   - Desktop icon (optional)
   - File associations for .oss project files
   - Clean uninstall
   - User or admin installation options

### Alternative installer tools:
- NSIS (Nullsoft Scriptable Install System)
- WiX Toolset
- InstallShield

The executable will be in the `dist` folder after a successful build.