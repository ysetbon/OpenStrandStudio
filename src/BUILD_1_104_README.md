# Version 1.104 Build Templates - README

## Created Files

Three template files have been created for version 1.104 (dated November 2, 2025):

1. **`inno setup/OpenStrand Studio1_104.iss`** - Windows Inno Setup installer configuration
2. **`build_dmg_1_104.sh`** - macOS DMG build script
3. **`build_installer_1_104.sh`** - macOS PKG installer build script

## Language Support

All files support 7 languages in the following order:

### Inno Setup (Windows)
- English, French, German, Italian, Spanish, Portuguese, Hebrew

### Build Scripts (macOS)
Each language has its own localized welcome.html with that language appearing first:

1. **Base (en.lproj)**: English, German, French, Italian, Spanish, Portuguese, Hebrew
2. **fr.lproj**: French, English, German, Italian, Spanish, Portuguese, Hebrew
3. **de.lproj**: German, English, French, Italian, Spanish, Portuguese, Hebrew
4. **it.lproj**: Italian, English, German, French, Spanish, Portuguese, Hebrew
5. **es.lproj**: Spanish, English, French, German, Italian, Portuguese, Hebrew
6. **pt.lproj**: Portuguese, English, French, German, Italian, Spanish, Hebrew
7. **he.lproj**: Hebrew, English, French, German, Italian, Spanish, Portuguese

## What You Need to Do Before Building

### 1. Update Feature Descriptions

Search for `[TODO:` in all three files and replace with actual version 1.104 features:

**In Inno Setup (.iss file):**
```
[TODO: Update with version 1.104 features]
```

**In build_dmg_1_104.sh:**
```
[TODO: Update with version 1.104 features - e.g., Enhanced attached strand functionality]
```

**In build_installer_1_104.sh:**
Look for HTML comments:
```html
<!-- TODO: Replace the features below with version 1.104 features -->
```

### 2. Feature List Format

Replace the placeholder 1.103 features with your actual 1.104 features. Keep the same format:

**Example for English:**
```
• Feature Name: Brief description of the feature
• Another Feature: Description
• Bug Fix: What was fixed
```

**Translate to all 7 languages:**
- English
- French (Français)
- German (Deutsch)
- Italian (Italiano)
- Spanish (Español)
- Portuguese (Português)
- Hebrew (עברית)

## Building Version 1.104

### Windows Build:
1. Update features in `inno setup/OpenStrand Studio1_104.iss`
2. Build your Windows executable using PyInstaller
3. Run Inno Setup Compiler on the .iss file
4. Output: `OpenStrandStudioSetup_02_Nov_2025_1_104.exe`

### macOS DMG Build:
1. Update features in `build_dmg_1_104.sh`
2. Build your .app using PyInstaller
3. Run: `bash build_dmg_1_104.sh`
4. Output: `installer_output/OpenStrandStudioSetup_02_November_2025_1.104.dmg`

### macOS PKG Build:
1. Update features in `build_installer_1_104.sh`
2. Build your .app using PyInstaller
3. Run: `bash build_installer_1_104.sh`
4. Output: `installer_output/OpenStrandStudio_1_104.pkg`

## Version Information

- **Version Number**: 1.104
- **Version String**: 1_104
- **Release Date**: November 2, 2025
- **Date Format (ISS)**: 02_Nov_2025
- **Date Format (DMG)**: 02_November_2025
- **Date Format (PKG)**: 02_November_2025

## Quick Find & Replace Guide

When ready to update features, use your editor's find/replace with these search terms:

| Search For | Replace With |
|------------|--------------|
| `[TODO: Update with version 1.104 features]` | Your actual features |
| `[TODO: Mettre à jour]` | French features |
| `[TODO: Aktualisieren]` | German features |
| `[TODO: Aggiornare]` | Italian features |
| `[TODO: Actualizar]` | Spanish features |
| `[TODO: Atualizar]` | Portuguese features |
| `[TODO: עדכן]` | Hebrew features |

## Notes

- The 1.103 feature descriptions are left in place as templates - you can see the format and style to match
- All version numbers have been updated to 1.104
- All dates have been updated to November 2, 2025
- The file structure and language ordering exactly matches the 1.103 pattern
- Search for "TODO" in any file to find all locations that need updates

## Contact

Publisher: Yonatan Setbon
Email: ysetbon@gmail.com
