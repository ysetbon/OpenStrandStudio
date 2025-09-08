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

## Version 1.102 (Released: 08/09/2025)

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
