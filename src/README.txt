# OpenStrand Studio

OpenStrand Studio is an interactive tool for creating and manipulating strand-based designs. It provides a canvas where users can draw, connect, and modify strands to create complex patterns or structures. The software offers various modes for attaching, moving, and customizing strands, making it versatile for different design needs.

Created by Yonatan Setbon, owner of the YouTube channel LanYarD.

## Key Features:
- Attach Mode: Create new strands and connect them
- Move Mode: Adjust the position and shape of existing strands
- Layer Panel: Manage and organize your strands
- Color Customization: Change colors of individual strands or sets
- Grid System: Snap strands to a grid for precise placement

## IMPORTANT: Control Button Functionality

The Control button enables a crucial feature in OpenStrand Studio: the ability to create masked layers. When you hold down the Control key, you enter "Masked Mode". In this mode, you can select two existing layers, and the software will create a new masked layer that represents the intersection of these two layers. This powerful feature allows for complex designs and interactions between different parts of your strand structure.

To use this feature:
1. Hold down the Control key
2. Click on two different layers in your design
3. Release the Control key to create the masked layer

The masked layer feature is essential for creating intricate, overlapping designs and is one of the most powerful tools in OpenStrand Studio. Make sure to experiment with this functionality to unlock the full potential of your strand designs!

------

## Version 1.01 (Released: 8/11/2024)

We're excited to introduce new features to enhance your design experience:

### New Features:

1. Lock Button:
   - Prevents accidental movement of strands
   - Useful for securing parts of your design while working on others
   - Toggle lock/unlock for individual strands

2. Delete Button (Beta):
   - Allows removal of specific strands
   - Only works on strands that don't have two attached strands
   - For main strands (x_1), it deletes the entire branch (all attached strands)

### How to Use:

- Lock Button: Click to toggle lock/unlock on selected strands
- Delete Button: Select a strand and click delete. Remember:
  - Works only on strands with 0 or 1 attached strands
  - Use caution with main strands as it will remove all connected strands

Note: The delete function is in beta.

------

## Version 1.02 (Released: 8/18/2024)

We're thrilled to announce further improvements and new features in this update:

### Improvements and New Features:

1. Delete Option Enhancement:
   - Fixed issues with the delete functionality
   - More reliable and consistent strand deletion

2. Angle Adjust Mode:
   - New mode for precise angle adjustments of strands
   - Easily fine-tune the angles of your designs

3. Save and Load Functionality:
   - Now you can save your projects and load them later
   - Seamlessly continue your work across sessions

### How to Use:

- Angle Adjust Mode: Select a strand and enter this mode to adjust its angle
- Save: Click the 'Save' button to store your current project
- Load: Use the 'Load' button to open a previously saved project

These updates aim to provide a smoother, more flexible design experience. The improved delete option, new angle adjustment capabilities, and project persistence features should significantly enhance your workflow in OpenStrand Studio.

Enjoy creating with OpenStrand Studio!

------

## version 1.03 (Released 8/25/2024)

New Features:

1. Save Image Button: Export designs as image files.
2. Mask Mode Button: Quick access to masking functionality.
3. Select Strand Button: Improved strand selection tool.
4. Angle Adjustment Update: Strands automatically deselect after angle adjustment.

------
**HIGHLIGHTED FEATURE:**

> **Sample Projects: Download and load sample projects from the provided folder to explore different design techniques and possibilities**

------

## version 1.04 (Released 9/1/2024)

New Features:

1. Group Function: Create and manage groups of strands.
2. Group Panel: Organize and edit groups easily.
3. Group Operations: Move, rotate, or scale entire groups at once.
4. Group Properties: Apply changes to all strands in a group simultaneously.

------
**HIGHLIGHTED FEATURE:**

> **Group Functionality: Efficiently handle complex designs by grouping and manipulating multiple strands as a single unit**

------

## version 1.05 (Released: 9/12/2024)

Fixed Features:

1. Masking layers now take into consideration the circle of attached strands.
2. Enhanced typography for canvas overlay buttons.
3. Angle adjust now disables strands that cannot have new strands attached, simplifying the process.
4. Better overall functionality for angle adjust, improving user experience and precision.

------

## version 1.06 (Released: 9/20/2024)

### Fixed Features:

1. Fixed group issues.
2. Now saving and loading takes into consideration the groups.
3. Masks are better drawn.

------
## Version 1.061 (Released: 9/23/2024)

### New Features:

1. Settings Dialog:
   - Introduced a new settings dialog with the following options:
     - Theme customization: Users can now change the color theme of the application windows.
     - Language selection: Added support for French language interface.

2. Upcoming Features:
   - A comprehensive tutorial for beginners is planned for inclusion in the settings dialog in the next version.

------
## Version 1.062 (Released: 9/25/2024)

### New Features:

1. **User Settings:**
   - **Persistent Preferences:** User preferences are now automatically saved, ensuring that your settings remain consistent every time you open the application. This enhancement eliminates the need to reconfigure your preferences with each session, providing a more seamless and personalized user experience.

2. **Group Management:**
   - **Proper Group Creation:** Groups are now created correctly, allowing for effective organization and management of multiple strands within your design.
   - **Adding Strands to Groups:** When adding more strands to an existing group, please ensure to delete and recreate the group. This ensures that all strands are properly integrated and that the group's functionality remains intact. This will be fixed in later version to work automatically, for now you'll need to delete and create on your own.

------

## Version 1.063 (Released: 10/01/2024)

### New Features:

1. **Refresh Button for Layer Panel:**
   - Added a refresh button to align the layers to the bottom of the layer panel.

2. **Automatic Group Deletion:**
   - When attaching a new strand related to an attached strand from a group, the group is automatically deleted to prevent issues.

3. **Save Functionality Update:**
   - Saving now excludes groups to resolve previous issues.

4. **Theme Setting Improvements:**
   - After setting a new theme, please reopen the application to ensure the theme is properly applied to the group window.

5. **Video Tutorials Included:**
   - Included video tutorials to provide better user guidance.

6. **About Section Added:**
   - Added "About Open Strand" section in settings for more information about the application.

### Important Note for this version:
- It is recommended to close the application when the theme settings are changed to ensure that the theme affects the group panel.

------

## Version 1.064 (Released: 10/07/2024)

### New Features and Improvements:

1. **Enhanced Group Colors:**
   - When setting a new theme, group colors now appear correctly.

2. **Improved JSON File Loading:**
   - When loading a JSON file, the order of importing layers is now correct, including masked layers.

These updates enhance the visual experience when changing themes and ensure better accuracy when loading projects.

------

## Version 1.070 (Released: 10/25/2024)

### Major New Features:

1. **Complete Bezier Curve Implementation:**
   - Revolutionary improvement in strand manipulation and control
   - Smoother and more precise strand creation and editing
   - Enhanced visual quality of all strands
   - More natural and fluid strand behavior

2. **Enhanced Save/Load System:**
   - New comprehensive save/load system that includes group data
   - Improved project persistence and reliability
   - Better handling of complex designs

This version represents a significant leap forward in OpenStrand Studio's capabilities, particularly with the implementation of Bezier curves. Users will notice immediately improved control and smoother appearance of all strands, making the design process more intuitive and professional.

------

## Version 1.071 (Released: 27/10/2024)

### New Features:

1. **Enhanced Mask Creation:**
   - Improved visual feedback during mask creation
   - First strand selection is now highlighted in red for better clarity
   - Right-click on masked layers to edit or reset the mask intersection

2. **Improved Attached Strand Visualization:**
   - Better implementation of attached strand circles
   - Half-circles are now properly masked when intersecting with other strands

These updates enhance the masking workflow and improve the visual quality of attached strands, making the design process more intuitive and visually accurate.

------

## Version 1.072 (Released: 5/11/2024)

### Improvements:

1. **Enhanced Group Management:**
   - Groups now correctly update when new strands are attached
   - Ensures proper movement, rotation, and angle adjustments for grouped elements

2. **Improved Mask Functionality:**
   - Edited masks now properly update their position when moving associated strands
   - Enhanced attached strand visualization with properly masked half-circles

------

## Version 1.073 (Released: 7/11/2024)

### Improvements:

1. **JSON File Handling:**
   - Fixed JSON loading and saving functionality
   - More reliable project file handling

2. **Layer Panel Enhancement:**
   - Fixed layer deletion in the layer panel
   - Improved layer management stability

------

## Version 1.080 (Released: 16/01/2025)

### Improvements:

1. **Enhanced Move and Attach Mode:**
   - Made the move and attach functionality more intuitive and user-friendly
   - Clearer visual indicators for available actions
   - Improved user guidance for strand manipulation

2. **Group Management Fixes:**
   - Resolved attachment issues that occurred after creating groups
   - Fixed problems with strand attachments when using the angle strand dialog

3. **UI Enhancement:**
   - Improved colors and styling of buttons in the main window
   - Better visual consistency across the application
   - Enhanced user interface elements for better clarity

4. **Save/Load Functionality Improvements:**
   - Enhanced layer loading to maintain correct creation order from JSON saves
   - More reliable and consistent project file handling

5. **Mask Editing Enhancements:**
   - Improved mask editing behavior when working with groups
   - Better rotation handling of edited masks based on group center
   - Enhanced overall mask manipulation (work in progress but functional)

These updates focus on improving the user experience by making the interface more intuitive and fixing key functionality issues with groups and attachments.

------

## Version 1.081 (Released: 28/01/2025)

### Improvements and New Features:

1. **Save/Load Improvements:**
   - Maintains correct layer order when loading from JSON
   - More reliable project file handling

2. **Mask Editing:**
   - Better rotation handling based on group center
   - Improved mask manipulation with groups

3. **Additional Improvements:**
   - Transparent circle stroke visualization during right-click
   - Better font rendering in settings dialog
   - Updated attachment point visualization when deleting strands

------

## Version 1.090 (Released: 16/03/2025)

### Improvements and New Features:

1. **UI Enhancement:**
   - Improved UI for move and attached modes
   - Faster calculation when handling many strands

2. **Bug Fixes:**
   - Fixed various bugs in main window
   - Fixed connection of strands that lost information

3. **New Feature:**
   - Added shading option for improved visual appearance

These updates focus on performance improvements and visual enhancements to provide a smoother and more efficient design experience.

------

## Version 1.091 (Released: 9/04/2025)

### Improvements and New Features:

1.  **Undo/Redo Functionality:**
    *   Easily undo and redo your actions using dedicated buttons.

2.  **History Tab:**
    *   Added a "History" tab in the Settings dialog to view and load past action sessions.

3.  **Bug Fixes:**
    *   Improved visual drawing of strands and control points in move mode.
    *   Corrected drawing issues when connecting an attached strand to the starting point of a main strand.

4.  **Language Support:**
    *   Added support for the following languages: Italian, Spanish, Portuguese, and Hebrew.

------

## Version 1.092 (Released: 3/05/2025)

### Improvements and New Features:

1.  **Persistent Undo/Redo History:**
    *   Undo/Redo history is now saved with your project for persistent session support.

2.  **Customizable Dashed Lines and Arrowheads:**
    *   Configure dashed line patterns and arrowhead styles on strands for clearer visuals.

3.  **Improved Control Point Visuals:**
    *   Larger handles and enhanced highlighting for more accurate control point manipulation.

4.  **Mask Extension Options:**
    *   Fine-tune mask extension behavior with additional control settings.

5.  **Enhanced Shading Algorithm:**
    *   Produces smoother, more natural shadow effects on strands.

6.  **Upgraded Layer Panel:**
    *   Added drag-and-drop reordering of layers and quick visibility toggles in the panel.

------

## Version 1.100 (Released: 7/6/2025)

### Improvements and New Features:

1.  **Strand Width Control:**
    *   Dynamically adjust the width of individual strands for more design flexibility.

2.  **Zoom In/Out Functionality:**
    *   Navigate designs with new zoom controls for detailed views or full canvas overview.

3.  **Pan Tool:**
    *   Drag smoothly around your canvas with the new pan functionality.

4.  **Shadow-Only Mode:**
    *   You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.

5.  **Initial Setup:**
    *   When first starting the application, click "New Strand" to begin creating your first strand.

6.  **General Fixes:**
    *   Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.

7.  **Higher Quality Rendering:**
    *   Improved canvas display quality and 4x higher resolution image export for crisp, professional results.

8.  **Removed Extended Mask Option:**
    *   The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.

------


## Version 1.101 (Released: 13/08/2025)

### Improvements and New Features:

1. **Improved Layer Management:**
   - Enhanced `StateLayerManager` structure for better handling of knot connections and strand relationships, providing more reliable layer operations and improved performance.

2. **Group Duplication:**
   - You can now duplicate entire groups with all their strands by right-clicking on a group header and selecting "Duplicate Group". The duplicated group maintains all strand properties and automatically generates unique layer names.

3. **Hide Mode:**
   - New hide mode accessible via the monkey button (🙉/🙈) allows you to quickly hide multiple layers at once. Click the button to enter hide mode, then click on layers to hide them. Exit hide mode to apply changes.

4. **Center View:**
   - Instantly center all strands in your view with the new target button (🎯). This automatically adjusts the canvas position to show all your work centered on screen.

5. **Quick Knot Closing:**
   - Right-click on any strand or attached strand with one free end to quickly close the knot. The system automatically finds and connects to the nearest compatible strand with a free end.

6. **Language Support:**
   - Added German (🇩🇪). Switch in Settings → Change Language.

7. **Samples:**
   - New Samples category in Settings → Samples to load ready-to-use projects. Selecting a sample will close the dialog and load the sample.

------

## Version 1.102 (Released: 09/09/2025)

### Improvements and New Features:

1. **Attached Strand Improvements:**
   - Fixed painting issues for attached strands that were similar to regular strands
   - Resolved movement issues when everything is disabled with control points
   - Fixed initial movement behavior when only ending control point is enabled

2. **Control Point Enhancements:**
   - Improved handling of disabled third control point to allow only ending control point movement
   - Better control point behavior during initial strand manipulation

3. **Build System Optimization:**
   - Optimized build process for smaller executable size using virtual environment
   - Removed unnecessary scientific library dependencies from main application
   - Improved build consistency between Windows and macOS platforms

4. **Performance Improvements:**
   - Reduced application size by excluding unused Anaconda scientific packages
   - Faster application startup with leaner executable

------

## Version 1.103 (Released: 30/09/2025)

### Improvements and Bug Fixes:

1. **Fixed Group Duplication Issues:**
   - Control point visibility now correctly preserved when duplicating groups
   - Fixed zoom behavior for duplicated groups - strands now zoom properly
   - Resolved canvas reference issues in duplicated group widgets

2. **Full Arrow Drawing Fix:**
   - Fixed full arrow rendering for attached strands in zoomed/panned views
   - Arrow now displays correctly in both normal and direct drawing modes

3. **Code Cleanup:**
   - Removed debug logging statements for cleaner console output
   - Eliminated arrow-related debug messages from production code

4. **Improved Stability:**
   - Better handling of group creation and duplication workflows
   - Fixed duplicate strand additions to canvas during group operations

------

## Version 1.104 (Released: 02/11/2025)

### New Features and Improvements:

1. **Enhanced Control Point System:**
   - Improved UX for control point movement and activation behavior
   - Better visual feedback when working with control points
   - Smoother interaction during control point manipulation
   - Fixed control point movement area and starting control point behavior

2. **Endpoint Properties Management:**
   - Save samples and duplicate endpoint properties functionality
   - Streamlined workflow for managing endpoint configurations
   - Ability to copy endpoint settings between different strands

3. **Advanced Shadow Editor:**
   - Fixed dialog layout with proper multi-language support
   - Added subtraction operations for shadow effects
   - Improved history table for better shadow management
   - Enhanced shadow dialog window columns layout

4. **User Settings Persistence:**
   - Save and load functionality for user settings
   - Preferences are now maintained across sessions
   - Automatic restoration of workspace configuration

5. **Rendering Improvements:**
   - Fixed side line of strand rendering issues
   - Enhanced undo/redo functionality for more reliable operations
   - Improved visual output consistency
   - Fixed rendering for attached strands

6. **Control Point Constraints:**
   - Center and bias controls cannot move when starting control point is not activated
   - Improved logical flow for control point manipulation
   - Better prevention of invalid control point states

------

## Version 1.105 (Released: 06/12/2025)

### New Features and Improvements:

1. **Mask Grid:**
   - Quickly create multiple strand masks using a visual N×N grid interface in group functionalities

2. **Keyboard Shortcuts:**
   - Space: Hold to quickly pan/unpan the canvas
   - Z: Undo your last action
   - X: Redo what you just undid
   - N: New Strand
   - 1: Draw Names
   - L: Lock Layers
   - D: Delete Strand
   - A: Deselect All

3. **Fixed Selection & Zoom:**
   - Selection in move, select, and attach modes now remains accurate at all zoom levels

4. **Smoother Knot Connections:**
   - Fixed a rendering issue where "closed knots" (loops) would sometimes show visible seams or gaps at the connection point
   - Strands now merge seamlessly for a cleaner look

------

## Version 1.106 (Released: 04/01/2026)

### New Features and Improvements:

1. **Hover Highlight in Select and Mask Modes:**
   - Strands now highlight when hovering over them in Select mode
   - Strands also highlight when hovering in Mask mode
   - Provides better visual feedback for strand selection

2. **Main Buttons Responsiveness:**
   - Fixed main window buttons (at the top of the canvas) to display correctly on any screen size and aspect ratio
   - Improved button layout for better compatibility across different displays

------

## Version 1.107 (Released: 20/04/2026)

### New Features and Improvements:

1. **Group Shadow Editor:**
   - Shadows can now be edited for entire groups, giving you full control over how group strands cast shadows on the canvas.

2. **Shadow Editor Fixes & Masked Strand Support:**
   - Shadow subtraction logic is unified between the main renderer and the shadow preview.
   - Masked strands can now be edited through the shadow editor dialog with smart defaults.

3. **Selected Strand Settings:**
   - New "Selected Strand" category in Settings gathers options that apply only to the currently selected strand — move-only, control-points-only, shadow-only, and a customizable selection highlight color.

4. **Group Creation Stability:**
   - Fixed unexpected crashes caused by orphan hidden group dialogs when creating groups or exiting the application.

5. **Hebrew Right-to-Left Alignment:**
   - The main window, settings dialog, group context menu, and group panel are now mirrored right-to-left in Hebrew for a natural reading order.

6. **View Button:**
   - New View button in the main window that hides all mode indicators (Move, Attach, etc.) so you can see your design clearly without any UI overlays.

------------------------------------------------------------------------------------------
# OpenStrand Studio - Français

OpenStrand Studio est un outil interactif pour créer et manipuler des designs basés sur des brins. Il offre un canevas où les utilisateurs peuvent dessiner, connecter et modifier des brins pour créer des motifs ou des structures complexes. Le logiciel propose divers modes pour attacher, déplacer et personnaliser les brins, le rendant polyvalent pour différents besoins de conception.

Créé par Yonatan Setbon, propriétaire de la chaîne YouTube LanYarD.

## Fonctionnalités clés :
- Mode Attache : Créez de nouveaux brins et connectez-les
- Mode Déplacement : Ajustez la position et la forme des brins existants
- Panneau de Calques : Gérez et organisez vos brins
- Personnalisation des Couleurs : Changez les couleurs des brins individuels ou des ensembles
- Système de Grille : Alignez les brins sur une grille pour un placement précis

## IMPORTANT : Fonctionnalité du bouton Contrôle

Le bouton Contrôle active une fonctionnalité cruciale dans OpenStrand Studio : la capacité de créer des calques masqués. Lorsque vous maintenez la touche Contrôle enfoncée, vous entrez en "Mode Masque". Dans ce mode, vous pouvez sélectionner deux calques existants, et le logiciel créera un nouveau calque masqué qui représente l'intersection de ces deux calques. Cette puissante fonctionnalité permet des designs complexes et des interactions entre différentes parties de votre structure de brins.

Pour utiliser cette fonctionnalité :
1. Maintenez la touche Contrôle enfoncée
2. Cliquez sur deux calques différents dans votre design
3. Relâchez la touche Contrôle pour créer le calque masqué

La fonctionnalité de calque masqué est essentielle pour créer des designs complexes et superposés et c'est l'un des outils les plus puissants d'OpenStrand Studio. Assurez-vous d'expérimenter avec cette fonctionnalité pour libérer tout le potentiel de vos designs de brins !

------

## Version 1.01 (Sortie : 11/08/2024)

Nous sommes ravis d'introduire de nouvelles fonctionnalités pour améliorer votre expérience de design :

### Nouvelles Fonctionnalités :

1. Bouton de Verrouillage :
   - Empêche le mouvement accidentel des brins
   - Utile pour sécuriser des parties de votre design pendant que vous travaillez sur d'autres
   - Basculez entre verrouillage/déverrouillage pour les brins individuels

2. Bouton de Suppression (Bêta) :
   - Permet la suppression de brins spécifiques
   - Fonctionne uniquement sur les brins qui n'ont pas deux brins attachés
   - Pour les brins principaux (x_1), il supprime toute la branche (tous les brins attachés)

### Comment utiliser :

- Bouton de Verrouillage : Cliquez pour basculer entre verrouillage/déverrouillage sur les brins sélectionnés
- Bouton de Suppression : Sélectionnez un brin et cliquez sur supprimer. Rappelez-vous :
  - Fonctionne uniquement sur les brins avec 0 ou 1 brin attaché
  - Utilisez avec précaution sur les brins principaux car cela supprimera tous les brins connectés

Note : La fonction de suppression est en version bêta.

------

## Version 1.02 (Sortie : 18/08/2024)

Nous sommes ravis d'annoncer de nouvelles améliorations et fonctionnalités dans cette mise à jour :

### Améliorations et Nouvelles Fonctionnalités :

1. Amélioration de l'Option de Suppression :
   - Correction des problèmes avec la fonctionnalité de suppression
   - Suppression de brins plus fiable et cohérente

2. Mode d'Ajustement d'Angle :
   - Nouveau mode pour des ajustements précis des angles des brins
   - Affinez facilement les angles de vos designs

3. Fonctionnalité de Sauvegarde et de Chargement :
   - Vous pouvez maintenant sauvegarder vos projets et les charger plus tard
   - Continuez votre travail sans interruption entre les sessions

### Comment utiliser :

- Mode d'Ajustement d'Angle : Sélectionnez un brin et entrez dans ce mode pour ajuster son angle
- Sauvegarder : Cliquez sur le bouton 'Sauvegarder' pour stocker votre projet actuel
- Charger : Utilisez le bouton 'Charger' pour ouvrir un projet précédemment sauvegardé

Ces mises à jour visent à fournir une expérience de design plus fluide et flexible. L'option de suppression améliorée, les nouvelles capacités d'ajustement d'angle et les fonctionnalités de persistance de projet devraient améliorer significativement votre flux de travail dans OpenStrand Studio.

Profitez de la création avec OpenStrand Studio !

------

## Version 1.03 (Sortie : 25/08/2024)

Nouvelles Fonctionnalités :

1. Bouton de Sauvegarde d'Image : Exportez les designs sous forme de fichiers image.
2. Bouton de Mode Masque : Accès rapide à la fonctionnalité de masquage.
3. Bouton de Sélection de Brin : Outil de sélection de brin amélioré.
4. Mise à jour de l'Ajustement d'Angle : Les brins se désélectionnent automatiquement après l'ajustement de l'angle.

------
**FONCTIONNALITÉ MISE EN AVANT :**

> **Projets Exemples : Téléchargez et chargez des projets exemples à partir du dossier fourni pour explorer différentes techniques et possibilités de design**

------

## Version 1.04 (Sortie : 01/09/2024)

Nouvelles Fonctionnalités :

1. Fonction de Groupe : Créez et gérez des groupes de brins.
2. Panneau de Groupe : Organisez et modifiez facilement les groupes.
3. Opérations de Groupe : Déplacez, faites pivoter ou redimensionnez des groupes entiers en une seule fois.
4. Propriétés de Groupe : Appliquez des changements à tous les brins d'un groupe simultanément.

------
**FONCTIONNALITÉ MISE EN AVANT :**

> **Fonctionnalité de Groupe : Gérez efficacement des designs complexes en groupant et manipulant plusieurs brins comme une seule unité**

------

## Version 1.05 (Sortie : 12/09/2024)

Fonctionnalités Corrigées :

1. Les calques de masquage prennent maintenant en compte le cercle des brins attachés.
2. Typographie améliorée pour les boutons de superposition du canevas.
3. L'ajustement d'angle désactive maintenant les brins qui ne peuvent pas avoir de nouveaux brins attachés, simplifiant le processus.
4. Meilleure fonctionnalité globale pour l'ajustement d'angle, améliorant l'expérience utilisateur et la précision.

------

## Version 1.06 (Sortie : 20/09/2024)

### Fonctionnalités Corrigées :

1. Correction des problèmes de groupe.
2. La sauvegarde et le chargement prennent maintenant en compte les groupes.
3. Les masques sont mieux dessinés.

------

## Version 1.061 (Sortie : 23/09/2024)

### Nouvelles Fonctionnalités :

1. Dialogue de Paramètres :
   - Introduction d'un nouveau dialogue de paramètres avec les options suivantes :
     - Personnalisation du thème : Les utilisateurs peuvent maintenant changer le thème de couleur des fenêtres de l'application.
     - Sélection de la langue : Ajout du support pour l'interface en langue française.

2. Fonctionnalités à Venir :
   - Un tutoriel complet pour les débutants est prévu pour être inclus dans le dialogue des paramètres dans la prochaine version.

------

## Version 1.062 (Sortie : 25/09/2024)

### Nouvelles Fonctionnalités :

1. **Paramètres Utilisateur :**
   - **Préférences Persistantes :** Les préférences utilisateur sont désormais enregistrées automatiquement, garantissant que vos paramètres restent cohérents à chaque ouverture de l'application. Cette amélioration élimine le besoin de reconfigurer vos préférences à chaque session, offrant une expérience utilisateur plus fluide et personnalisée.

2. **Gestion des Groupes :**
   - **Création Correcte des Groupes :** Les groupes sont désormais créés correctement, permettant une organisation et une gestion efficaces de plusieurs brins au sein de votre design.
   - **Ajout de Brins aux Groupes :** Lors de l'ajout de nouveaux brins à un groupe existant, veuillez vous assurer de supprimer et recréer le groupe. Cela garantit que tous les brins sont correctement intégrés et que la fonctionnalité du groupe reste intacte. Cela sera corrigé dans les versions ultérieures pour fonctionner automatiquement ; pour l'instant, vous devrez supprimer et recréer le groupe vous-même.

------

## Version 1.063 (Sortie : 10/01/2025)

### Nouvelles Fonctionnalités :

1. **Bouton de Rafraîchissement pour le Panneau de Calques :**
   - Ajout d'un bouton de rafraîchissement pour aligner les calques en bas du panneau de calques.

2. **Suppression Automatique des Groupes :**
   - Lors de l'attachement d'un nouveau brin lié à un brin attaché d'un groupe, le groupe est automatiquement supprimé pour éviter des problèmes.

3. **Mise à Jour de la Fonctionnalité de Sauvegarde :**
   - La sauvegarde exclut désormais les groupes pour résoudre les problèmes précédents.

4. **Améliorations des Paramètres de Thème :**
   - Après avoir défini un nouveau thème, veuillez rouvrir l'application pour vous assurer que le thème est correctement appliqué à la fenêtre des groupes.

5. **Tutoriels Vidéo Inclus :**
   - Ajout de tutoriels vidéo pour une meilleure orientation des utilisateurs.

6. **Section À Propos Ajoutée :**
   - Ajout de la section "À propos d'Open Strand" dans les paramètres pour plus d'informations sur l'application.

### Note Importante :
- Il est recommandé de fermer l'application lorsque les paramètres de thème sont changés pour s'assurer que les effets de thème s'appliquent également au panneau de groupes.

------
## Version 1.064 (Sortie : 07/10/2024)

### Nouvelles Fonctionnalités et Améliorations :

1. **Amélioration des Couleurs de Groupe :**
   - Lors du changement de thème, les couleurs des groupes apparaissent maintenant correctement.

2. **Amélioration du Chargement de Fichiers JSON :**
   - Lors du chargement d'un fichier JSON, l'ordre d'importation des couches est désormais correct, y compris pour les couches masquées.

Ces mises à jour améliorent l'expérience visuelle lors du changement de thème et assurent une meilleure précision lors du chargement de projets.

------

## Version 1.070 (Sortie : 25/10/2024)

### Nouvelles Fonctionnalités Majeures :

1. **Implémentation Complète des Courbes de Bézier :**
   - Amélioration révolutionnaire dans la manipulation et le contrôle des brins
   - Création et édition des brins plus fluide et précise
   - Qualité visuelle améliorée pour tous les brins
   - Comportement des brins plus naturel et fluide

2. **Système de Sauvegarde/Chargement Amélioré :**
   - Nouveau système complet de sauvegarde/chargement incluant les données de groupe
   - Persistance et fiabilité des projets améliorées
   - Meilleure gestion des designs complexes

Cette version représente une avancée significative dans les capacités d'OpenStrand Studio, particulièrement avec l'implémentation des courbes de Bézier. Les utilisateurs remarqueront immédiatement un contrôle amélioré et une apparence plus fluide de tous les brins, rendant le processus de design plus intuitif et professionnel.

------

## Version 1.071 (Sortie : 27/10/2024)

### Nouvelles Fonctionnalités :

1. **Création de Masques Améliorée :**
   - Meilleur retour visuel pendant la création de masques
   - La sélection du premier brin est maintenant mise en évidence en rouge pour plus de clarté
   - Clic droit sur les calques masqués pour éditer ou réinitialiser l'intersection du masque

2. **Visualisation Améliorée des Brins Attachés :**
   - Meilleure implémentation des cercles des brins attachés
   - Les demi-cercles sont maintenant correctement masqués lors de l'intersection avec d'autres brins

Ces mises à jour améliorent le flux de travail du masquage et la qualité visuelle des brins attachés, rendant le processus de design plus intuitif et visuellement précis.

------

## Version 1.072 (Sortie : 05/11/2024)

### Améliorations :

1. **Gestion des Groupes Améliorée :**
   - Les groupes se mettent à jour correctement lors de l'attachement de nouveaux brins
   - Assure des mouvements, rotations et ajustements d'angles appropriés pour les éléments groupés

2. **Fonctionnalité de Masque Améliorée :**
   - Les masques édités mettent à jour correctement leur position lors du déplacement des brins associés
   - Amélioration de la visualisation des brins attachés avec des demi-cercles correctement masqués

------

## Version 1.073 (Sortie : 07/11/2024)

### Améliorations :

1. **Gestion des Fichiers JSON :**
   - Correction des bugs de chargement et de sauvegarde des fichiers JSON
   - Gestion plus fiable des fichiers de projet

2. **Amélioration du Panneau de Calques :**
   - Correction de la suppression des calques dans le panneau des calques
   - Amélioration de la stabilité de la gestion des calques

------

## Version 1.080 (Sortie : 16/01/2025)

### Améliorations :

1. **Mode Déplacement et Attachement Amélioré :**
   - Fonctionnalité de déplacement et d'attachement plus intuitive et conviviale
   - Indicateurs visuels plus clairs pour les actions disponibles
   - Meilleure orientation de l'utilisateur pour la manipulation des brins

2. **Corrections de la Gestion des Groupes :**
   - Résolution des problèmes d'attachement survenant après la création de groupes
   - Correction des problèmes d'attachement des brins lors de l'utilisation du dialogue d'angle des brins

3. **Amélioration de l'Interface Utilisateur :**
   - Amélioration des couleurs et du style des boutons dans la fenêtre principale
   - Meilleure cohérence visuelle dans toute l'application
   - Éléments d'interface utilisateur améliorés pour plus de clarté

4. **Améliorations de la Sauvegarde/Chargement :**
   - Chargement amélioré des calques pour maintenir l'ordre de création correct depuis les sauvegardes JSON
   - Gestion des fichiers de projet plus fiable et cohérente

5. **Améliorations de l'Édition des Masques :**
   - Amélioration du comportement d'édition des masques lors du travail avec des groupes
   - Meilleure gestion de la rotation des masques édités basée sur le centre du groupe
   - Amélioration globale de la manipulation des masques (en développement mais fonctionnel)

Ces mises à jour se concentrent sur l'amélioration de l'expérience utilisateur en rendant l'interface plus intuitive et en corrigeant les problèmes clés de fonctionnalité avec les groupes et les attachements.

------

## Version 1.081 (Sortie : 28/01/2025)

### Améliorations et Nouvelles Fonctionnalités :

1. **Améliorations Sauvegarde/Chargement :**
   - Maintien de l'ordre correct des calques lors du chargement JSON
   - Gestion plus fiable des fichiers de projet

2. **Édition des Masques :**
   - Meilleure gestion de la rotation basée sur le centre du groupe
   - Manipulation améliorée des masques avec groupes

3. **Autres Améliorations :**
   - Visualisation du contour de cercle transparent lors du clic droit
   - Meilleur rendu des polices dans les paramètres
   - Mise à jour de la visualisation des points d'attache lors de la suppression

------

## Version 1.090 (Sortie : 16/03/2025)

### Améliorations et Nouvelles Fonctionnalités :

1. **Amélioration de l'Interface Utilisateur :**
   - Interface améliorée pour les modes de déplacement et d'attachement
   - Calcul plus rapide lors de la manipulation de nombreux brins

2. **Corrections de Bugs :**
   - Correction de divers bugs dans la fenêtre principale
   - Correction de la connexion des brins qui avaient perdu des informations

3. **Nouvelle Fonctionnalité :**
   - Ajout d'une option d'ombrage pour une meilleure apparence visuelle

Ces mises à jour se concentrent sur les améliorations de performance et les améliorations visuelles pour offrir une expérience de conception plus fluide et efficace.

------

## Version 1.091 (Sortie : 10/04/2025)

### Améliorations et Nouvelles Fonctionnalités :

1.  **Fonctionnalité Annuler/Rétablir :**
    *   Annulez et rétablissez facilement vos actions à l'aide des boutons dédiés.

2.  **Onglet Historique :**
    *   Ajout d'un onglet "Historique" dans la boîte de dialogue Paramètres pour visualiser et charger les sessions d'actions passées.

3.  **Corrections de Bugs :**
    *   Amélioration du dessin visuel des brins et des points de contrôle en mode déplacement.
    *   Correction des problèmes de dessin lors de la connexion d'un brin attaché au point de départ d'un brin principal.

4.  **Support des Langues :**
    *   Ajout de la prise en charge des langues suivantes : Italien, Espagnol, Portugais et Hébreu.

------

## Version 1.092 (Sortie : 03/05/2025)

### Améliorations et Nouvelles Fonctionnalités :

1.  **Historique Annuler/Rétablir Persistant :**
    *   L'historique Annuler/Rétablir est désormais enregistré avec votre projet pour une prise en charge de session persistante.

2.  **Lignes et Flèches en Pointillés Personnalisables :**
    *   Configurez les motifs de lignes pointillées et les styles de flèches sur les brins pour des visuels plus clairs.

3.  **Visuels des Points de Contrôle Améliorés :**
    *   Poignées plus grandes et mise en évidence améliorée pour une manipulation plus précise des points de contrôle.

4.  **Options d'Extension de Masque :**
    *   Affinez le comportement d'extension de masque avec des paramètres de contrôle supplémentaires.

5.  **Algorithme d'Ombrage Amélioré :**
    *   Produit des effets d'ombre plus lisses et plus naturels sur les brins.

6.  **Panneau des Calques Amélioré :**
    *   Ajout du réordonnancement par glisser-déposer des calques et de bascules rapides de visibilité dans le panneau.

------

## Version 1.100 (Sortie : 06/07/2025)

### Améliorations et Nouvelles Fonctionnalités :

1.  **Contrôle de la Largeur des Brins :**
    *   Ajustez dynamiquement la largeur des brins individuels pour plus de flexibilité dans la conception.

2.  **Fonction de Zoom Avant/Arrière :**
    *   Naviguez dans vos créations avec les nouveaux contrôles de zoom pour des vues détaillées ou une vue d'ensemble complète du canevas.

3.  **Outil de Panoramique :**
    *   Faites glisser en douceur sur votre canevas avec la nouvelle fonction de panoramique.

4.  **Mode ombre uniquement :**
    *   Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.

5.  **Configuration Initiale :**
    *   Au premier démarrage de l'application, cliquez sur "Nouveau Brin" pour commencer à créer votre premier brin.

6.  **Corrections générales :**
    *   Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.

7.  **Rendu de qualité supérieure :**
    *   Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.

8.  **Suppression de l'option masque étendu :**
     *   L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.

------

## Version 1.101 (Sortie : 13/08/2025)

### Améliorations et Nouvelles Fonctionnalités :

1. **Gestion améliorée des couches :**
   - Structure `StateLayerManager` améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.

2. **Duplication de groupe :**
   - Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant « Dupliquer le groupe ». Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.

3. **Mode masquage :**
   - Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permettant de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches à masquer. Quittez le mode masquage pour appliquer les changements.

4. **Centrer la vue :**
   - Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). La position du canevas est automatiquement ajustée pour afficher tout votre travail centré à l'écran.

5. **Fermeture rapide de nœud :**
   - Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement le brin compatible le plus proche avec une extrémité libre.

6. **Support de langue :**
   - Ajout de l'allemand (🇩🇪). Sélectionnez-la dans Paramètres → Changer la langue.

7. **Exemples :**
   - Nouvelle catégorie Exemples dans Paramètres → Exemples pour charger des projets prêts à l'emploi. Le choix d'un exemple fermera la boîte de dialogue et chargera l'exemple.

------

## Version 1.102 (Sortie : 09/09/2025)

### Améliorations et Nouvelles Fonctionnalités :

1. **Améliorations des brins attachés :**
   - Correction des problèmes de peinture pour les brins attachés similaires aux brins réguliers
   - Résolution des problèmes de mouvement lorsque tout est désactivé avec les points de contrôle
   - Correction du comportement de mouvement initial lorsque seul le point de contrôle de fin est activé

2. **Améliorations des points de contrôle :**
   - Meilleure gestion du troisième point de contrôle désactivé pour permettre uniquement le mouvement du point de contrôle de fin
   - Meilleur comportement des points de contrôle lors de la manipulation initiale des brins

3. **Optimisation du système de construction :**
   - Processus de construction optimisé pour une taille d'exécutable réduite en utilisant un environnement virtuel
   - Suppression des dépendances de bibliothèques scientifiques inutiles de l'application principale
   - Amélioration de la cohérence de construction entre les plateformes Windows et macOS

4. **Améliorations des performances :**
   - Taille d'application réduite en excluant les packages scientifiques Anaconda non utilisés
   - Démarrage plus rapide de l'application avec un exécutable plus léger

------

## Version 1.103 (Sortie : 30/09/2025)

### Améliorations et Corrections de Bugs :

1. **Correction des problèmes de duplication de groupe :**
   - La visibilité des points de contrôle est maintenant correctement préservée lors de la duplication de groupes
   - Correction du comportement du zoom pour les groupes dupliqués - les brins zooment maintenant correctement
   - Résolution des problèmes de référence de canevas dans les widgets de groupe dupliqués

2. **Correction de l'affichage des flèches complètes :**
   - Correction du rendu des flèches complètes pour les brins attachés dans les vues zoomées/déplacées
   - Les flèches s'affichent maintenant correctement dans les modes de dessin normal et direct

3. **Nettoyage du code :**
   - Suppression des messages de débogage pour une sortie console plus propre
   - Élimination des messages de débogage liés aux flèches du code de production

4. **Stabilité améliorée :**
   - Meilleure gestion des flux de travail de création et de duplication de groupes
   - Correction des ajouts de brins dupliqués au canevas pendant les opérations de groupe

------

## Version 1.104 (Sortie : 02/11/2025)

### Nouvelles Fonctionnalités et Améliorations :

1. **Système de points de contrôle amélioré :**
   - Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation
   - Meilleur retour visuel lors du travail avec les points de contrôle
   - Interaction plus fluide lors de la manipulation des points de contrôle
   - Correction de la zone de déplacement des points de contrôle et du comportement du point de contrôle de départ

2. **Gestion des propriétés des extrémités :**
   - Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités
   - Flux de travail optimisé pour la gestion des configurations d'extrémités
   - Possibilité de copier les paramètres d'extrémité entre différents brins

3. **Éditeur d'ombres avancé :**
   - Disposition de dialogue corrigée avec prise en charge multilingue appropriée
   - Ajout d'opérations de soustraction pour les effets d'ombre
   - Table d'historique améliorée pour une meilleure gestion des ombres
   - Amélioration de la disposition des colonnes de la fenêtre de dialogue d'ombre

4. **Persistance des paramètres utilisateur :**
   - Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur
   - Les préférences sont maintenant maintenues d'une session à l'autre
   - Restauration automatique de la configuration de l'espace de travail

5. **Améliorations du rendu :**
   - Correction des problèmes de rendu des lignes latérales des brins
   - Fonctionnalité annuler/rétablir améliorée pour des opérations plus fiables
   - Amélioration de la cohérence de la sortie visuelle
   - Correction du rendu pour les brins attachés

6. **Contraintes des points de contrôle :**
   - Les contrôles de centre et de biais ne peuvent pas bouger lorsque le point de contrôle de départ n'est pas activé
   - Flux logique amélioré pour la manipulation des points de contrôle
   - Meilleure prévention des états de points de contrôle invalides

------

## Version 1.105 (Sortie : 06/12/2025)

### Nouvelles Fonctionnalités et Améliorations :

1. **Grille de Masques :**
   - Créez rapidement plusieurs masques de brins à l'aide d'une interface de grille visuelle N×N dans les fonctionnalités de groupe

2. **Raccourcis Clavier :**
   - Espace : Maintenez pour panoramiquer/dé-panoramiquer rapidement le canevas
   - Z : Annuler votre dernière action
   - X : Rétablir ce que vous venez d'annuler
   - N : Nouveau Brin
   - 1 : Dessiner les Noms
   - L : Verrouiller les Calques
   - D : Supprimer le Brin
   - A : Désélectionner Tout

3. **Sélection et Zoom Corrigés :**
   - La sélection dans les modes déplacement, sélection et attache reste maintenant précise à tous les niveaux de zoom

4. **Connexions de Nœuds Plus Fluides :**
   - Correction d'un problème de rendu où les "nœuds fermés" (boucles) affichaient parfois des coutures ou des espaces visibles au point de connexion
   - Les brins fusionnent maintenant de manière homogène pour un aspect plus propre

------

## Version 1.106 (Sortie : 04/01/2026)

### Nouvelles Fonctionnalités et Améliorations :

1. **Surbrillance au survol dans les modes Sélection et Masque :**
   - Les brins sont maintenant mis en surbrillance lorsque vous passez la souris dessus en mode Sélection
   - Les brins sont également mis en surbrillance lors du survol en mode Masque
   - Offre un meilleur retour visuel pour la sélection des brins

2. **Réactivité des boutons principaux :**
   - Correction des boutons de la fenêtre principale (en haut du canevas) pour qu'ils s'affichent correctement sur toute taille d'écran et tout rapport d'aspect
   - Amélioration de la disposition des boutons pour une meilleure compatibilité avec différents écrans

------

## Version 1.107 (Sortie : 20/04/2026)

### Nouvelles Fonctionnalités et Améliorations :

1. **Éditeur d'ombres de groupe :**
   - Les ombres peuvent désormais être modifiées pour des groupes entiers, vous offrant un contrôle total sur la façon dont les brins d'un groupe projettent leurs ombres sur le canevas.

2. **Corrections de l'éditeur d'ombres et prise en charge des brins masqués :**
   - La logique de soustraction des ombres est unifiée entre le rendu principal et l'aperçu des ombres.
   - Les brins masqués peuvent maintenant être modifiés via la boîte de dialogue de l'éditeur d'ombres avec des valeurs par défaut intelligentes.

3. **Paramètres du brin sélectionné :**
   - Une nouvelle catégorie « Brin Sélectionné » dans les paramètres regroupe des options qui ne s'appliquent qu'au brin actuellement sélectionné — déplacement seul, points de contrôle seuls, ombre seule, et une couleur de surbrillance de sélection personnalisable.

4. **Stabilité de la création de groupes :**
   - Correction des plantages inattendus causés par des boîtes de dialogue de groupe cachées orphelines lors de la création de groupes ou de la fermeture de l'application.

5. **Alignement de droite à gauche pour l'hébreu :**
   - La fenêtre principale, la boîte de dialogue des paramètres, le menu contextuel de groupe et le panneau de groupe sont désormais mis en miroir de droite à gauche en hébreu pour un ordre de lecture naturel.

6. **Bouton Vue :**
   - Nouveau bouton Vue dans la fenêtre principale qui masque tous les indicateurs de mode (Bouger, Lier, etc.) pour que vous puissiez voir votre conception clairement, sans aucune superposition d'interface.

------