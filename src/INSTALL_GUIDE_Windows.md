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

### Method 1: Using batch script with virtual environment (Recommended)

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
   - Build the executable using PyInstaller
   - Place the .exe in the `dist` folder

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
   - Build the executable with all required DLLs
   - Place the .exe in the `dist` folder

### Method 3: Manual PyInstaller build

1. If using Anaconda, first set the PATH:
   ```powershell
   $env:PATH = "C:\ProgramData\Anaconda3\Library\bin;$env:PATH"
   ```

2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

3. Build the executable:
   ```bash
   pyinstaller --onefile --windowed --name OpenStrandStudio --icon=box_stitch.ico --add-data "box_stitch.ico;." --add-data "settings_icon.png;." --add-data "flags;flags" main.py
   ```

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

## Creating an Installer

After building the .exe, you can create an installer using tools like:
- NSIS (Nullsoft Scriptable Install System)
- Inno Setup
- WiX Toolset

The executable will be in the `dist` folder after a successful build.