# Creating a New OpenStrand Studio Installer

This guide explains how to cut a new release of OpenStrand Studio for both
**Windows** (PyInstaller spec → Inno Setup `.iss`) and **macOS** (PyInstaller
spec → `.sh` builder that produces a `.pkg`/`.dmg`). It documents the
conventions every existing version (1.10x) follows so future versions stay
consistent.

> **Worked example used throughout:** bumping from **1.107** to **1.108**.
> 1.107 was the most up-to-date release when this guide was written, so the
> templates are based on it. The 1.108 artifacts created from these steps are:
> `inno setup/OpenStrand Studio1_108.iss`, `build_dmg_1_108.sh`, and
> `build_installer_1_108.sh`.

---

## 0. Naming & format conventions

| Thing | Format | Example (1.108) |
|-------|--------|-----------------|
| Marketing version | `1.108` | used in spec, `.iss`, `.sh` |
| File-name version tag | `1_108` | `OpenStrand Studio1_108.iss`, `build_dmg_1_108.sh` |
| Windows date (`MyAppDate`) | `DD_Mon_YYYY` | `01_Jun_2026` |
| macOS date (`APP_DATE`) | `DD_Month_YYYY` | `01_June_2026` |
| Installer output (Win) | `OpenStrandStudioSetup_<date>_1_108.exe` | |
| Installer output (Mac) | `OpenStrandStudio_1.108.pkg` | |

Every release ships release notes in **7 languages**, always in this set and
order of definition: **English, French, German, Italian, Spanish, Portuguese,
Hebrew**. Keep the wording identical between the Windows and macOS installers.

---

## 1. The PyInstaller spec files

The spec turns `main.py` + assets into the runnable app. There is **one spec
per platform**, and they are *version-light*:

- **`OpenStrandStudio.spec`** (Windows) — produces `dist/OpenStrandStudio.exe`.
  Contains **no version string**; the version is applied later by the `.iss`.
  → **Usually no edits needed for a new release.**

- **`OpenStrandStudio_mac.spec`** (macOS) — produces
  `dist/OpenStrandStudio.app`. This one **does** hardcode the version in the
  `BUNDLE(... info_plist=...)` block:

  ```python
  'CFBundleShortVersionString': '1.108',
  'CFBundleVersion': '1.108',
  ```
  → **Bump both of these to the new version for every macOS release.**

Both specs declare bundled assets in `datas` (icons, `flags/`,
`layer_panel_icons/`, `mp4`/`mov`, `samples/`, `images/*.svg`). **If a release
adds a new asset folder, add it to `datas` in both specs *and* to the `[Files]`
section of the `.iss`.**

### Creating a brand-new spec (only if assets/structure change a lot)
From `src/`, generate a baseline and then re-apply our customizations:
```bash
pyinstaller --windowed --icon box_stitch.ico --name OpenStrandStudio main.py   # Windows
pyinstaller --windowed --icon box_stitch.icns --name OpenStrandStudio main.py  # macOS
```
Then copy the `datas`, `hiddenimports`, `excludes`, and (macOS) the `BUNDLE`
block from the existing spec so nothing regresses. In practice you should
**copy the existing spec and tweak it** rather than regenerate from scratch.

---

## 2. Windows release (Inno Setup)

### 2a. Build the executable
```bat
cd src
build_windows.bat
```
`build_windows.bat` puts Anaconda's Qt binaries on `PATH`, cleans old
`build/` and `dist/`, and runs `pyinstaller OpenStrandStudio.spec`. Result:
`src/dist/OpenStrandStudio.exe`.

### 2b. Create the version `.iss`
1. Copy the template (or the previous version's `.iss`):
   ```
   inno setup/OpenStrand Studio1_10x_template.iss  →  inno setup/OpenStrand Studio1_108.iss
   ```
2. Edit the `#define` block at the top:
   ```pascal
   #define MyAppVersion "1.108"
   #define MyAppDate "01_Jun_2026"
   ```
   and the suffix in `OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_108`.
3. Confirm the paths match this machine's checkout (they should already be
   correct in the template):
   ```pascal
   #define SourcePath "C:\Users\YonatanSetbon\projects\OpenStrandStudio\src"
   #define ExePath    "C:\Users\YonatanSetbon\projects\OpenStrandStudio\src\dist"
   ```
4. In `[CustomMessages]`, replace every `#todo` with the real release notes for
   all 7 languages. Rules for this section:
   - `%n` = line break, `%n%n` = blank line.
   - `&&` = a literal `&` (a single `&` is an accelerator hint and will vanish).
   - Format each feature as `• Feature Title: short description.`
   - Keep the intro line (`What's New in Version 1.108:`) and the closing
     "The program is brought to you by Yonatan Setbon…" paragraph.
   - Each language has two keys: `<lang>.WelcomeLabel2` and
     `<lang>.LaunchAfterInstall`.

### 2c. Compile
Open the `.iss` in the **Inno Setup Compiler** and press *Compile* (or run
`ISCC.exe "inno setup\OpenStrand Studio1_108.iss"`). The installer is written
to `src/dist/OpenStrandStudioSetup_01_Jun_2026_1_108.exe`.

### What the `.iss` sections do
- `[Setup]` — identity, output name, compression, per-user install
  (`PrivilegesRequired=lowest`), icons.
- `[Languages]` — the 7 bundled message files.
- `[Files]` — the exe plus every asset folder (mirror of the spec `datas`).
- `[Icons]` — Start-menu + optional desktop shortcut.
- `[Tasks]` — the (unchecked) "create desktop icon" option.
- `[Registry]` — registers the `.oss` file type so projects open on double-click.
- `[UninstallDelete]` — wipes `%appdata%\OpenStrandStudio` on uninstall.
- `[Run]` — offers to launch the app after install.
- `[CustomMessages]` — the localized welcome/release-notes text.

---

## 3. macOS release (`.sh` → `.pkg` / `.dmg`)

There are two builder scripts per version; both are self-contained bash scripts
that embed all 7 languages of HTML welcome/license screens:

- **`build_installer_1_108.sh`** → a `.pkg` (guided Installer.app flow).
- **`build_dmg_1_108.sh`** → the same content packaged for a drag-install image.

> These run **on macOS** (they use `pkgbuild`, `productbuild`, `osascript`,
> `.lproj` localization folders). They are committed here so the Mac build box
> always has the current version.

### 3a. Build the app bundle (on macOS)
```bash
cd src
pyinstaller OpenStrandStudio_mac.spec     # → dist/OpenStrandStudio.app
```

### 3b. Create the version builder script
1. Copy the template (or the previous version):
   ```
   build_installer_template.sh  →  build_installer_1_108.sh
   build_dmg_template.sh         →  build_dmg_1_108.sh
   ```
2. Update the variables at the top:
   ```bash
   VERSION="1.108"
   APP_DATE="01_June_2026"
   ```
3. Fill in the release notes. Search for `#todo` and replace:
   - `#todo What's New message` → the localized "What's New in Version 1.108:" header.
   - each `#todo feature description` → an actual `<li>` bullet.

   **Localization layout (important):** macOS shows the welcome screen from the
   `.lproj` folder matching the user's language. Each language's `welcome.html`
   contains **all 7 languages**, but with **that language listed first**. The
   builder script writes one base `welcome.html` plus one per `*.lproj`
   (`en/fr/de/it/es/pt/he`) with the per-language ordering. So the same feature
   bullets appear ~7 times in the script — keep them in sync.

   **Hebrew is written as HTML entities** (`&#x05D1;` …), not raw UTF-8, to
   render reliably in the Installer welcome pane. To convert Hebrew text to
   entities:
   ```python
   "".join(f"&#x{ord(c):04X};" if ord(c) > 127 else c for c in text)
   ```

### 3c. Run the builder (on macOS)
```bash
chmod +x build_installer_1_108.sh
./build_installer_1_108.sh
```
Output lands in `…/OpenStrandStudio/src/installer_output/OpenStrandStudio_1.108.pkg`.
Adjust the `PKG_PATH` / app-source paths at the top of the script if the
checkout location differs from `/Users/yonatan/Documents/GitHub/OpenStrandStudio`.

### What the builder does
1. Writes a `postinstall` script (drops a desktop icon, offers to launch).
2. Writes `Distribution.xml` (installer config, references welcome + license).
3. Writes base + per-language `welcome.html` and `license.html` into `.lproj`s.
4. `pkgbuild` → component package, `productbuild` → final `.pkg`.
5. Cleans up the temp working dir and opens `installer_output/`.

---

## 4. Tip: generate the localized files instead of hand-editing

Because each Mac script repeats every language's bullets 7×, and the `.iss`
needs the same wording, it's easy to drift. A small one-off Python script that
holds the release notes in a single dict and rewrites the version tokens +
welcome blocks (converting Hebrew to entities) keeps Windows and macOS in sync.
See `src/_gen_1_108.py` (the generator used for the 1.108 bump) as a starting
point — copy it, update the `CONTENT` dict and the `OLD_VER`/`NEW_VER`
constants, and run it from `src/`.

---

## 5. Release checklist

- [ ] `OpenStrandStudio_mac.spec` — bump `CFBundleShortVersionString` & `CFBundleVersion`.
- [ ] New asset folders (if any) added to **both** specs and the `.iss` `[Files]`.
- [ ] `inno setup/OpenStrand Studio1_<ver>.iss` — version, date, output suffix, 7-language notes.
- [ ] `build_installer_1_<ver>.sh` & `build_dmg_1_<ver>.sh` — `VERSION`, `APP_DATE`, 7-language notes (Hebrew as entities).
- [ ] Windows exe built (`build_windows.bat`) and `.iss` compiled.
- [ ] macOS `.app` built (`OpenStrandStudio_mac.spec`) and `.sh` run.
- [ ] Release notes added to `README.md` and `src/README.txt`.
- [ ] Smoke-test both installers on a clean machine/VM.
