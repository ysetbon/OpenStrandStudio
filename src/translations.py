translations = {
    'en': {
        # MainWindow translations
        'play_video': 'Play Video',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Attach',
        'move_mode': 'Move',
        'rotate_mode': 'Rotate',
        'toggle_grid': 'Grid',
        'angle_adjust_mode': 'Angle/Length',
        'select_mode': 'Select',
        'mask_mode': 'Mask',
        'new_strand_mode': 'New',
        'save': 'Save',
        'load': 'Load',
        'save_image': 'Image',
        'settings': 'Settings',
        'light': 'Light',
        'dark': 'Dark',
        'english': 'English',
        'french': 'French',
        'german': 'German',
        'italian': 'Italian',
        'spanish': 'Spanish',
        'portuguese': 'Portuguese',
        'hebrew': 'Hebrew',
        'select_theme': 'Select Theme',
        'default': 'Default',
        'light': 'Light',
        'dark': 'Dark',
        'layer_state': 'State',
        'layer_state_log_title': 'State',
        'layer_state_info_title': 'Info',
        'layer_state_info_tooltip': 'Info',
        'close': 'Close',
        'toggle_control_points': 'Points',
        'toggle_shadow': 'Shadow',
        'shadow_color': 'Shadow Color',
        'draw_only_affected_strand': 'Draw only affected strand when dragging',
        'enable_third_control_point': 'Enable third control point at center',
        'enable_curvature_bias_control': 'Enable curvature bias controls',
        'enable_snap_to_grid': 'Enable snap to grid',
        'show_move_highlights': 'Show selection indicators in move/attach modes',
        'use_extended_mask': 'Use extended mask (wider overlap)',
        'use_extended_mask_tooltip': 'If you want to use shadows, toggle on; if you don\'t want shadows, toggle off.',
        'use_extended_mask_desc': 'If you want to use shadows, toggle on; if you don\'t want shadows, toggle off.',
        'shadow_blur_steps': 'Shadow Blur Steps:',
        'shadow_blur_steps_tooltip': 'Number of steps for the shadow fade effect',
        'shadow_blur_radius': 'Shadow Blur Radius:',
        'shadow_blur_radius_tooltip': 'Shadow blur radius in pixels (range: 0.0 - 360.0)',
        'reset_curvature_settings': 'Reset Curvature Settings:',
        'reset': 'Reset',
        'reset_curvature_tooltip': 'Reset all curvature settings to default values',
        'base_fraction': 'Control Point Influence (pull strength):',
        'base_fraction_tooltip': 'Control point influence strength (1.0=normal, 2.0=strong, 3.0=very strong)',
        'distance_multiplier': 'Distance Boost (magnifies curves):',
        'distance_mult_tooltip': 'Distance multiplication factor (1.0=no boost, 2.0=2x boost, 5.0=5x boost)',
        'curve_response': 'Curve Shape (1=sharp, 3=smooth):',
        'curve_response_tooltip': 'Curve response type (1.0=linear, 1.5=mild curve, 2.0=quadratic, 3.0=cubic)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Explanation of Layer State Information:</b><br>
<br><br>
<b>Order:</b> The sequence of layers (strands) in the canvas.<br>
<br>
<b>Connections:</b> The relationships between strands, indicating which strands are connected or attached.<br>
<br>
<b>Groups:</b> The groups of strands that are collectively manipulated.<br>
<br>
<b>Masked Layers:</b> The layers that have masking applied for over-under effects.<br>
<br>
<b>Colors:</b> The colors assigned to each strand.<br>
<br>
<b>Positions:</b> The positions of strands on the canvas.<br>
<br>
<b>Selected Strand:</b> The strand currently selected in the canvas.<br>
<br>
<b>Newest Strand:</b> The most recently created strand.<br>
<br>
<b>Newest Layer:</b> The most recently added layer in the canvas.
''',
        # SettingsDialog translations
        'general_settings': 'General Settings',
        'change_language': 'Change Language',
        'tutorial': 'Tutorial',
        'button_explanations': 'Button Guide',
        'history': 'History',
        'whats_new': "What's New?",
        'samples': 'Samples',
        'samples_header': 'Sample projects',
        'samples_sub': 'Choose a sample to load and learn from. The dialog will close and the sample will be loaded.',
        'sample_closed_knot': 'Closed Knot',
        'sample_box_stitch': 'Box Stitch',
        'sample_overhand_knot': 'Overhand Knot',
        'sample_three_strand_braid': 'Three-Strand Braid',
        'sample_interwoven_double_closed_knot': 'Interwoven Double Closed Knot',
        'about': 'About',
        'select_theme': 'Select Theme:',
        'select_language': 'Select Language:',
        'ok': 'OK',
        'cancel': 'Cancel',
        'apply': 'Apply',
        'language_settings_info': 'Change the language of the application.',
        'tutorial_info': 'Press the "play video" button below each text\nto view the tutorial explaining:',
        'button_guide_info': 'Learn about the different buttons and their functions in OpenStrand Studio.\n\nTip: You can click on emoji layer panel icons to see their explanations!',
        'layer_panel_buttons': 'Layer Panel Buttons',
        'main_window_buttons': 'Main Window Buttons',
        'group_buttons': 'Group Buttons',
        'general_settings_buttons': 'General Settings',
        'draw_names_desc': 'Draw Names - Shows/hides strand names on the canvas',
        'lock_layers_desc': 'Lock Layers - Enters lock mode to lock/unlock strands from editing',
        'add_new_strand_desc': 'New Strand - Adds a new strand to your design',
        'delete_strand_desc': 'Delete Strand - Removes the selected strand',
        'deselect_all_desc': 'Deselect All - Clears all selections (or clears all locks in lock mode)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Pan (✋/✊) - ✋ Click to activate pan mode, ✊ Drag the canvas to move around your design',
        'zoom_in_desc': 'Zoom In (🔍) - Zoom into your design for detailed work',
        'zoom_out_desc': 'Zoom Out (🔎) - Zoom out to see the bigger picture',
        'center_strands_desc': 'Center Strands (🎯) - Center all strands in the view',
        'multi_select_desc': 'Hide Mode (🙉/🙈) - 🙉 Click to activate hide mode, 🙈 Select layers then right-click for batch hide/show operations',
        'refresh_desc': 'Refresh (🔄) - Refresh the layer panel display',
        'reset_states_desc': 'Reset States (🏠) - Reset all layer states to default',
        # Main window button descriptions
        'attach_mode_desc': 'Attach Mode - Connect strands together at their endpoints',
        'move_mode_desc': 'Move Mode - Move strands and control points around the canvas',
        'rotate_mode_desc': 'Rotate Mode - Rotate selected strands',
        'toggle_grid_desc': 'Toggle Grid - Show/hide the grid on the canvas',
        'angle_adjust_desc': 'Angle Adjust Mode - Fine-tune the angles of strand connections',
        'save_desc': 'Save - Save your project to a file',
        'load_desc': 'Load - Load a project from a file',
        'save_image_desc': 'Save as Image - Export your design as an image file',
        'select_strand_desc': 'Select Strand - Enter selection mode to select strands',
        'mask_mode_desc': 'Mask Mode - Hide parts of strands that pass under others',
        'settings_desc': 'Settings - Open the settings dialog',
        'toggle_control_points_desc': 'Toggle Control Points - Show/hide the control points for bezier curves',
        'toggle_shadow_desc': 'Toggle Shadow - Show/hide shadows on strands',
        'layer_state_desc': 'Layer State - View debug information about layers',
        # Group button descriptions
        'create_group_desc': 'Create Group - Create a new group from selected strands',
        'group_header_desc': 'Group Header - Click to expand/collapse group. Right-click for options',
        'rename_group_desc': 'Rename Group - Change the name of this group',
        'delete_group_desc': 'Delete Group - Remove this group (strands remain)',
        'select_group_desc': 'Select Group - Select all strands in this group',
        'move_group_desc': 'Move Group - Move all strands in the group together',
        'rotate_group_desc': 'Rotate Group - Rotate all strands in the group',
        'edit_strand_angles_desc': 'Edit Strand Angles - Aligns all strand angles in the group to be parallel with a single click',
        'duplicate_group_desc': 'Duplicate Group - Create a copy of this group and its strands',
        # General settings descriptions
        'theme_select_desc': 'Theme Selection - Choose between light and dark themes for the interface',
        'shadow_color_desc': 'Shadow Color - Set the color and opacity for strand shadows',
        'draw_only_affected_desc': 'Draw Only Affected Strand - When enabled, only shows the strand being edited during drag operations',
        'enable_third_cp_desc': 'Enable Third Control Point - Adds an additional control point at the center for more complex curves',
        'enable_snap_desc': 'Enable Snap to Grid - Automatically aligns strands to grid points when moving',
        'shadow_blur_steps_desc': 'Shadow Blur Steps - Number of steps for creating smooth shadow fade effect (1-10)',
        'shadow_blur_radius_desc': 'Shadow Blur Radius - Controls the spread of the shadow blur in pixels',
        'control_point_influence_desc': 'Control Point Influence - Adjusts how strongly control points affect curve shape (1.0=normal)',
        'distance_boost_desc': 'Distance Boost - Multiplies the distance influence for stronger curves (2.0=double strength)',
        'curvature_type_desc': 'Curvature Type - Changes the mathematical curve response (1.0=linear, 2.0=quadratic, 3.0=cubic)',
        'reset_curvature_desc': 'Reset Curvature - Restores all curvature settings to default values (1.0, 2.0, 2.0)',
        # General Settings descriptions for button guide
        'general_settings_header': 'General Settings',
        'theme_selection_desc': 'Theme Selection - Choose between Default, Light, or Dark themes for the interface',
        'shadow_color_desc': 'Shadow Color - Set the color used for strand shadows',
        'shadow_blur_steps_desc': 'Shadow Blur Steps - Number of blur iterations (higher = smoother shadows)',
        'shadow_blur_radius_desc': 'Shadow Blur Radius - Size of the blur effect (higher = softer edges)',
        'draw_affected_strand_desc': 'Draw Only Affected Strand - When enabled, only shows the strand being dragged during editing',
        'third_control_point_desc': 'Enable Third Control Point - Adds a center control point for more complex curves',
        'curvature_bias_desc': 'Enable Curvature Bias Controls - Adds small triangle/circle controls to fine-tune curve shape',
        'snap_to_grid_desc': 'Enable Snap to Grid - Automatically aligns points to the grid when moving',
        'control_influence_full_desc': 'Control Point Influence - Sets how strongly control points pull the curve (0.25=weak, 1.0=normal, 3.0=very strong)',
        'distance_boost_full_desc': 'Distance Boost - Multiplies the curve strength to make curves more pronounced (1.0=normal, 10.0=maximum)',
        'curve_shape_full_desc': 'Curve Shape - Controls the mathematical curve type (1.0=sharp angles, 2.0=smooth curves, 3.0=very smooth)',
        'reset_curvature_full_desc': 'Reset Curvature Settings - Restores Control Influence, Distance Boost, and Curve Shape to defaults',
        'whats_new_info': '''
        <h2>What's New in Version 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Enhanced Curvature Bias Controls:</b> New bias control points positioned between the center control point and the two end control points provide fine-tuned curvature adjustment. These controls appear as small squares with either a triangle or circle icon inside, allowing you to independently adjust the curve influence from each side toward the center for more precise strand shaping.</li>
            <li style="font-size:15px;"><b>Advanced Curvature Settings:</b> Three new curvature parameters give you complete control over strand curves:
                <ul style="margin-left: 20px;">
                    <li><b>Control Point Influence:</b> Adjusts the pull strength of control points (1.0=normal, up to 3.0=very strong)</li>
                    <li><b>Distance Boost:</b> Magnifies curves by multiplying the distance factor (1.0=no boost, up to 5.0=5x boost)</li>
                    <li><b>Curve Shape:</b> Controls curve response type (1.0=sharp/linear, 3.0=smooth/cubic)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Progressive Control Point Display:</b> When creating new strands, only the starting control point is initially visible. Additional control points (end points, center point, and bias controls) appear progressively as you begin moving the strand, reducing visual clutter during initial placement.</li>
            <li style="font-size:15px;"><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality and more accurate shadow representation across all strand configurations.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Version 1.102</p>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'Layer Panel',
        'draw_names': 'Draw Names',
        'lock_layers': 'Lock Layers',
        'add_new_strand': 'New Strand',
        'delete_strand': 'Delete Strand',
        'deselect_all': 'Deselect All',
        'notification_message': 'Notification',
        'button_color': 'Choose a different button color (not default):',
        'extension_dash_gap_length': 'Gap length between strand end and start of dashes',
        'extension_dash_gap_length_tooltip': 'Gap between the strand end and the start of the dashes',
        'exit_lock_mode': 'Exit Lock',
        'clear_all_locks': 'Clear Locks', 
        'select_layers_to_lock': 'Select layers to lock/unlock',
        'exited_lock_mode': 'Exited lock mode',
        # Button tooltips
        'reset_tooltip': 'Reset:\nKeep only current state\nas first state',
        'refresh_tooltip': 'Refresh:\nReload layers',
        'center_tooltip': 'Center:\nPan to center all strands\nin canvas',
        'hide_mode_tooltip': 'Hide Mode:\nClick to enable layer\nselection, then right-click\nfor batch hide/show\noperations',
        'zoom_in_tooltip': 'Zoom In',
        'zoom_out_tooltip': 'Zoom Out',
        'pan_tooltip': 'Pan:\nClick and drag to move\nthe canvas',
        'undo_tooltip': 'Undo:\nUndo last action',
        'redo_tooltip': 'Redo:\nRedo last undone\naction',
        'currently_unavailable': 'Currently unavailable',
        'layer_cannot_delete_tooltip': 'This layer cannot be deleted (both ends are attached)',
     
   
        # Additional texts
        'adjust_angle_and_length': 'Adjust Angle and Length',
        'angle_label': 'Angle:',
        'length_label': 'Length:',
        'create_group': 'Create Group',
        'enter_group_name': 'Enter group name:',
        'group_creation_cancelled': 'No main strands selected. Group creation cancelled.',
        'move_group_strands': 'Move Strands',
        'rotate_group_strands': 'Rotate Strands',
        'edit_strand_angles': 'Edit Strand Angles',
        'duplicate_group': 'Duplicate Group',
        'rename_group': 'Rename Group',
        'delete_group': 'Delete Group',
        'gif_explanation_1': 'Setting themes and language.',
        'gif_explanation_2': 'Right-clicking on buttons in the layer panel area reveals their\ndescriptions.',
        'gif_explanation_3': 'Activating hide mode for selecting and batch hiding/showing layers.',
        'gif_explanation_4': 'Tutorial: How to create a closed knot.',
        'gif_placeholder_1': 'GIF 1 Placeholder',
        'gif_placeholder_2': 'GIF 2 Placeholder',
        'gif_placeholder_3': 'GIF 3 Placeholder',
        'gif_placeholder_4': 'GIF 4 Placeholder',
        'layer': 'Layer',
        'angle': 'Angle:',
        'adjust_1_degree': 'Adjust (±1°)',
        'fast_adjust': 'Fast Adjust',
        'end_x': 'End X',
        'end_y': 'End Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Attachable',
        'X_angle': 'Angle X:',
        'snap_to_grid': 'Snap to grid',
        'precise_angle': 'Precise angle:',
        'select_main_strands': 'Select Main Strands',
        'select_main_strands_to_include_in_the_group': 'Select main strands to include in the group:',
        # New translation keys for Layer State Log
        'current_layer_state': 'Current Layer State',
        'order': 'Order',
        'connections': 'Connections',
        
        # Canvas Indicators translations
        'canvas_indicators_title': 'Canvas Indicators',
        'control_points_title': 'Control Points',
        'triangle_control_name': "Triangle (Green with strand's color center)",
        'triangle_control_desc': 'Starting control point that defines the initial curve direction',
        'circle_control_name': "Circle (Green with strand's color center)",
        'circle_control_desc': 'Ending control point that defines the final curve direction',
        'square_control_name': "Square (Green with strand's color center)",
        'square_control_desc': 'Center control point for adjusting the middle of the curve',
        'bias_triangle_name': 'Small Square with Triangle',
        'bias_triangle_desc': 'Bias control for the curve from start to center (influences how the curve bends in the first half)',
        'bias_circle_name': 'Small Square with Circle',
        'bias_circle_desc': 'Bias control for the curve from center to end (influences how the curve bends in the second half)',
        'selection_indicators_title': 'Selection Indicators (Move/Attach Modes)',
        'red_circle_name': 'Red Circle',
        'red_circle_desc': 'Indicates the starting side of a strand for attachment',
        'blue_circle_name': 'Blue Circle',
        'blue_circle_desc': 'Indicates the ending side of a strand for attachment',
        'red_square_name': 'Semi-transparent Red Square',
        'red_square_desc': 'Hover indicator for start/end points of strands',
        'green_square_name': 'Semi-transparent Green Square',
        'green_square_desc': 'Hover indicator for control points',
        'yellow_square_name': 'Yellow Square',
        'yellow_square_desc': 'Active selection indicator when control point is being dragged',
        'groups': 'Groups',
        'masked_layers': 'Masked Layers',
        'colors': 'Colors',
        'positions': 'Positions',
        'selected_strand': 'Selected Strand',
        'newest_strand': 'Newest Strand',
        'newest_layer': 'Newest Layer',
        'x_movement': 'X Movement',
        'y_movement': 'Y Movement',
        'move_group': 'Move Group',
        'grid_movement': 'Grid Movement',
        'x_grid_steps': 'X Grid Steps',
        'y_grid_steps': 'Y Grid Steps',
        'apply': 'Apply',
        'toggle_shadow': 'Shadow',
        'mask_edit_mode_message': '             MASK EDIT MODE -\n              Press ESC to exit',
        'mask_edit_mode_exited': 'Mask edit mode exited',
        'edit_mask': 'Edit Mask',
        'reset_mask': 'Reset Mask',
        'transparent_stroke': 'Transparent Starting Edge',
        'transparent_closing_knot_side': 'Transparent Closing Knot Side',
        'restore_default_stroke': 'Restore Default Stroke',
        'restore_default_closing_knot_stroke': 'Restore Default Closing Knot Stroke',
        'change_color': 'Change Color',
        'change_stroke_color': 'Change Stroke Color',
        'change_width': 'Change Width',
        # --- NEW ---
        'hide_layer': 'Hide Layer',
        'show_layer': 'Show Layer',
        'hide_selected_layers': 'Hide Selected Layers',
        'show_selected_layers': 'Show Selected Layers',
        'enable_shadow_only_selected': 'Shadow Only Selected',
        'disable_shadow_only_selected': 'Show Full Layers (Disable Shadow Only)',
        'hide_start_line': 'Hide Start Line',
        'show_start_line': 'Show Start Line',
        'hide_end_line': 'Hide End Line',
        'show_end_line': 'Show End Line',
        'hide_start_circle': 'Hide Start Circle',
        'show_start_circle': 'Show Start Circle',
        'hide_end_circle': 'Hide End Circle',
        'show_end_circle': 'Show End Circle',
        'close_the_knot': 'Close the Knot',
        'hide_start_arrow': 'Hide Start Arrow',
        'show_start_arrow': 'Show Start Arrow',
        'hide_end_arrow': 'Hide End Arrow',
        'show_end_arrow': 'Show End Arrow',
        'hide_start_extension': 'Hide Start Dash',
        'show_start_extension': 'Show Start Dash',
        'hide_end_extension': 'Hide End Dash',
        'show_end_extension': 'Show End Dash',
        'line': 'Line',
        'arrow': 'Arrow',
        'extension': 'Dash',
        'circle': 'Circle',
        'shadow_only': 'Shadow Only',
        # Layer panel extension and arrow settings translations
        'extension_length': 'Extension Length',
        'extension_length_tooltip': 'Length of extension lines',
        'extension_dash_count': 'Dash Count',
        'extension_dash_count_tooltip': 'Number of dashes in extension line',
        'extension_dash_width': 'Extension Dash Width',
        'extension_dash_width_tooltip': 'Width of extension dashes',
        'extension_dash_gap_length': 'Gap length between strand end and start of dashes',
        'extension_dash_gap_length_tooltip': 'Gap between the strand end and the start of the dashes',
        'arrow_head_length': 'Arrow Head Length',
        'arrow_head_length_tooltip': 'Length of arrow head in pixels',
        'arrow_head_width': 'Arrow Head Width',
        'arrow_head_width_tooltip': 'Width of arrow head base in pixels',
        'arrow_head_stroke_width': 'Arrow Head Stroke Width',
        'arrow_head_stroke_width_tooltip': 'Thickness of arrow head border in pixels',
        'arrow_gap_length': 'Arrow Gap Length',
        'arrow_gap_length_tooltip': 'Gap between strand end and arrow shaft start',
        'arrow_line_length': 'Arrow Line Length',
        'arrow_line_length_tooltip': 'Length of the arrow shaft',
        'arrow_line_width': 'Arrow Line Width',
        'arrow_line_width_tooltip': 'Thickness of the arrow shaft',
        'use_default_arrow_color': 'Use Default Arrow Color',
        'button_color': 'Choose a different button color (not default):',
        'default_strand_color': 'Default Strand Color:',
        'default_stroke_color': 'Stroke Color:',
        'default_strand_width': 'Default Strand Width',
        'default_strand_width_tooltip': 'Click to set the default width for new strands',
        # --- END NEW ---
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "Show Full Arrow",
        'hide_full_arrow': "Hide Full Arrow",
        # --- END NEW ---
        # Group-related translations
        'group_exists': 'Group Exists',
        'group_replace_confirm': 'A group named "{}" already exists. Do you want to replace it?',
        # History translations
        'load_selected_history': 'Load Selected',
        'clear_all_history': 'Clear All History',
        'confirm_clear_history_title': 'Confirm Clear History',
        'confirm_clear_history_text': 'Are you sure you want to delete ALL past history sessions? This cannot be undone.',
        'history_load_error_title': 'History Load Error',
        'history_load_error_text': 'Could not load the selected history state.',
        'history_cleared_title': 'History Cleared',
        'history_cleared_text': 'All past history sessions have been cleared.',
        'no_history_found': 'No past history sessions found.',
        'history_explanation': 'Select a past session and click "Load Selected" to restore its final state.\nWarning: Loading history will clear your current undo/redo steps.',
        'history_list_tooltip': 'Select a session to load its final state',
        # About translations
        'about': 'About',
        'about_info': '''
        <h2>About OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio was developed by Yonatan Setbon. The software is designed to create any knot in a diagrammatic way by using layers for each section of a strand and incorporating masked layers that allow for an "over-under effect."
        </p>
        <p style="font-size:15px;">
            Yonatan runs a YouTube channel dedicated to lanyards called <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, where many tutorials feature diagrams of knots. This software was created to facilitate designing any knot, in order to demonstrate and explain how to make complex tutorials involving knot tying.
        </p>
        <p style="font-size:15px;">
            Feel free to contact me at <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> or connect with me on
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> or
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''',
        'width_preview_label': 'Total: {total}px | Color: {color}px | Stroke: {stroke}px each side',
        'percent_available_color': '% of Available Color Space',
        'total_thickness_label': 'Total Thickness (grid squares):',
        'grid_squares': 'squares',
        'color_vs_stroke_label': 'Color vs Stroke Distribution (total thickness fixed):',
    },
    'fr': {
        # MainWindow translations
        'play_video': 'Lire la vidéo',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Lier',
        'move_mode': 'Bouger',
        'rotate_mode': 'Pivoter',
        'toggle_grid': 'Grille',
        'angle_adjust_mode': 'Angle/Long.',
        'select_mode': 'Choisir',
        'mask_mode': 'Masque',
        'new_strand_mode': 'Nouveau',
        'save': 'Sauver',
        'load': 'Ouvrir',
        'save_image': 'Image',
        'settings': 'Paramètres',
        'light': 'Clair',
        'dark': 'Sombre',
        'english': 'Anglais',
        'french': 'Français',
        'german': 'Allemand',
        'italian': 'Italien',
        'spanish': 'Espagnol',
        'portuguese': 'Portugais',
        'hebrew': 'Hébreu',
        'select_theme': 'Sélectionner le thème',
        'default': 'Par défaut',
        'light': 'Clair',
        'dark': 'Sombre',
        'layer_state': 'État',
        'layer_state_log_title': 'État',
        'layer_state_info_title': 'Infos',
        'layer_state_info_tooltip': 'Infos',
        'close': 'Fermer',
        'toggle_control_points': 'Points',
        'toggle_shadow': 'Ombres',
        'shadow_color': 'Couleur d\'ombre',
        'draw_only_affected_strand': 'Afficher uniquement le brin affecté lors du déplacement',
        'enable_third_control_point': 'Activer le troisième point de contrôle au centre',
        'enable_curvature_bias_control': 'Activer les contrôles de biais de courbure',
        'enable_snap_to_grid': 'Activer l\'alignement sur la grille',
        'show_move_highlights': 'Afficher les indicateurs de sélection en modes déplacement/attachement',
        'use_extended_mask': 'Utiliser une extension de masque (surposition plus large)',
        'use_extended_mask_tooltip': "Si vous voulez utiliser des ombres, cochez ; si vous ne voulez pas d'ombre, décochez.",
        'use_extended_mask_desc': "Si vous voulez utiliser des ombres, cochez ; si vous ne voulez pas d'ombre, décochez.",
        'shadow_blur_steps': 'Étapes de flou d\'ombre:',
        'shadow_blur_steps_tooltip': 'Nombre d\'étapes pour l\'effet de fondu d\'ombre',
        'shadow_blur_radius': 'Rayon de flou d\'ombre:',
        'shadow_blur_radius_tooltip': 'Rayon de flou d\'ombre en pixels (plage: 0.0 - 360.0)',
        'reset_curvature_settings': 'Réinitialiser les paramètres de courbure:',
        'reset': 'Réinitialiser',
        'reset_curvature_tooltip': 'Réinitialiser tous les paramètres de courbure aux valeurs par défaut',
        'base_fraction': 'Influence (force de traction):',
        'base_fraction_tooltip': 'Force d\'influence du point de contrôle (1.0=normal, 2.0=fort, 3.0=très fort)',
        'distance_multiplier': 'Amplification (agrandit courbes):',
        'distance_mult_tooltip': 'Facteur de multiplication de distance (1.0=aucune amplification, 2.0=2x, 5.0=5x)',
        'curve_response': 'Forme courbe (1=angulaire, 3=lisse):',
        'curve_response_tooltip': 'Type de réponse de courbe (1.0=linéaire, 1.5=courbe douce, 2.0=quadratique, 3.0=cubique)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Explication des informations sur l'état des couches :</b><br>
<br><br>
<b>Ordre :</b> La séquence des couches (brins) dans le canevas.<br>
<br>
<b>Connexions :</b> Les relations entre les brins, indiquant quels brins sont connectés ou attachés.<br>
<br>
<b>Groupes :</b> Les groupes de brins qui sont manipulés collectivement.<br>
<br>
<b>Couches Masquées :</b> Les couches qui ont un masquage appliqué pour les effets de dessus-dessous.<br>
<br>
<b>Couleurs :</b> Les couleurs assignées à chaque brin.<br>
<br>
<b>Positions :</b> Les positions des brins sur le canevas.<br>
<br>
<b>Brin Sélectionné :</b> Le brin actuellement sélectionné dans le canevas.<br>
<br>
<b>Dernier Brin :</b> Le brin le plus récemment créé.<br>
<br>
<b>Dernière Couche :</b> La couche la plus récemment ajoutée dans le canevas.
''',
        # SettingsDialog translations
        'general_settings': 'Paramètres généraux',
        'change_language': 'Changer la langue',
        'tutorial': 'Tutoriel',
        'button_explanations': 'Guide des boutons',
        'history': 'Historique',
        'whats_new': "Quoi de neuf ?",
        'samples': 'Exemples',
        'samples_header': 'Projets d’exemple',
        'samples_sub': 'Choisissez un exemple à charger pour apprendre. La boîte de dialogue se fermera et l’exemple sera chargé.',
            'sample_closed_knot': 'Nœud fermé',
            'sample_box_stitch': 'Couture en boîte',
            'sample_overhand_knot': 'Nœud simple',
            'sample_three_strand_braid': 'Tresse à trois brins',
            'sample_interwoven_double_closed_knot': 'Nœud fermé double entrelacé',
        'about': 'À propos',
        'select_theme': 'Sélectionner le thème :',
        'select_language': 'Sélectionner la langue :',
        'ok': 'OK',
        'cancel': 'Annuler',
        'apply': 'Appliquer',
        'language_settings_info': 'Changer la langue de l\'application.',
        'tutorial_info': 'Appuyez sur le bouton "lire la vidéo" sous chaque texte\npour voir le tutoriel explicatif :',
        'button_guide_info': 'Découvrez les différents boutons et leurs fonctions dans OpenStrand Studio.\n\nAstuce : Vous pouvez cliquer sur les icônes emoji du panneau des calques pour voir leurs explications !',
        'layer_panel_buttons': 'Boutons du Panneau de Calques',
        'main_window_buttons': 'Boutons de la Fenêtre Principale',
        # General Settings descriptions for button guide
        'general_settings_header': 'Paramètres Généraux',
        'theme_selection_desc': 'Sélection du Thème - Choisir entre les thèmes Par défaut, Clair ou Sombre',
        'shadow_color_desc': "Couleur de l'Ombre - Définir la couleur utilisée pour les ombres des brins",
        'shadow_blur_steps_desc': "Étapes de Flou d'Ombre - Nombre d'itérations de flou (plus = ombres plus lisses)",
        'shadow_blur_radius_desc': "Rayon de Flou d'Ombre - Taille de l'effet de flou (plus = bords plus doux)",
        'draw_affected_strand_desc': 'Dessiner Uniquement le Brin Affecté - Affiche uniquement le brin en cours de glissement',
        'third_control_point_desc': 'Activer le Troisième Point de Contrôle - Ajoute un point de contrôle central pour des courbes complexes',
        'curvature_bias_desc': 'Activer les Contrôles de Biais de Courbure - Ajoute de petits contrôles triangle/cercle pour affiner la forme',
        'snap_to_grid_desc': "Activer l'Alignement sur la Grille - Aligne automatiquement les points sur la grille lors du déplacement",
        'control_influence_full_desc': "Influence du Point de Contrôle - Définit la force de traction des points de contrôle (0.25=faible, 1.0=normal, 3.0=très fort)",
        'distance_boost_full_desc': 'Amplification de Distance - Multiplie la force de la courbe pour des courbes plus prononcées (1.0=normal, 10.0=maximum)',
        'curve_shape_full_desc': 'Forme de Courbe - Contrôle le type de courbe mathématique (1.0=angles aigus, 2.0=courbes lisses, 3.0=très lisse)',
        'reset_curvature_full_desc': "Réinitialiser les Paramètres de Courbure - Restaure l'Influence, l'Amplification et la Forme aux valeurs par défaut",
        'whats_new_info': '''
        <h2>Nouveautés de la version 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Contrôles de biais de courbure améliorés :</b> De nouveaux points de contrôle de biais positionnés entre le point de contrôle central et les deux points de contrôle d'extrémité permettent un ajustement précis de la courbure. Ces contrôles apparaissent sous forme de petits carrés avec une icône de triangle ou de cercle à l'intérieur, vous permettant d'ajuster indépendamment l'influence de la courbe de chaque côté vers le centre pour un façonnage plus précis des brins.</li>
            <li style="font-size:15px;"><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres de courbure vous donnent un contrôle complet sur les courbes des brins :
                <ul style="margin-left: 20px;">
                    <li><b>Influence du point de contrôle :</b> Ajuste la force d'attraction des points de contrôle (1.0=normal, jusqu'à 3.0=très fort)</li>
                    <li><b>Amplification de distance :</b> Amplifie les courbes en multipliant le facteur de distance (1.0=pas d'amplification, jusqu'à 5.0=amplification 5x)</li>
                    <li><b>Forme de courbe :</b> Contrôle le type de réponse de courbe (1.0=net/linéaire, 3.0=lisse/cubique)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Affichage progressif des points de contrôle :</b> Lors de la création de nouveaux brins, seul le point de contrôle de départ est initialement visible. Les points de contrôle supplémentaires (points d'extrémité, point central et contrôles de biais) apparaissent progressivement lorsque vous commencez à déplacer le brin, réduisant l'encombrement visuel lors du placement initial.</li>
            <li style="font-size:15px;"><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle et une représentation plus précise des ombres dans toutes les configurations de brins.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Version 1.102</p>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'Panneau des Couches',
        'draw_names': 'Dessin. Noms',
        'lock_layers': 'Verr. Calques',
        'add_new_strand': 'Nouveau Brin',
        'delete_strand': 'Supprim. Brin',
        'deselect_all': 'Désél. Tous',
        'notification_message': 'Notification',
        'button_color': 'Choisissez une couleur de bouton différente (pas par défaut):',
        'default_strand_color': 'Couleur de Brin par Défaut:',
        'default_stroke_color': 'Couleur de Contour:',
        'default_strand_width': 'Largeur de Brin par Défaut',
        'default_strand_width_tooltip': 'Cliquez pour définir la largeur par défaut des nouveaux brins',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "Afficher la flèche complète",
        'hide_full_arrow': "Masquer la flèche complète",
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'Ajust. Angle',
        'angle_label': 'Angle :',
        'length_label': 'Longueur :',
        'create_group': 'Créer Groupe',
        'enter_group_name': 'Entrez le nom du groupe:',
        'group_creation_cancelled': 'Aucun brin principal sélectionné. Création du groupe annulée.',
        'move_group_strands': 'Déplacer Groupe',
        'rotate_group_strands': 'Tourner Groupe',
        'edit_strand_angles': 'Modifier les angles des brins',
        'duplicate_group': 'Dupliquer Groupe',
        'rename_group': 'Renommer Groupe',
        'delete_group': 'Supprimer Groupe',
        'gif_explanation_1': 'Configuration des thèmes et de la langue.',
        'gif_explanation_2': 'Un clic droit sur les boutons dans la zone du panneau de calques révèle\nleurs descriptions.',
        'gif_explanation_3': 'Activation du mode masquage pour sélectionner et masquer/afficher\ndes calques en groupe.',
        'gif_explanation_4': 'Tutoriel : Comment créer un nœud fermé.',
        'gif_placeholder_1': 'Espace réservé pour GIF 1',
        'gif_placeholder_2': 'Espace réservé pour GIF 2',
        'gif_placeholder_3': 'Espace réservé pour GIF 3',
        'gif_placeholder_4': 'Espace réservé pour GIF 4',
        'layer': 'Calque',
        'angle': 'Angle:',
        'adjust_1_degree': 'Ajuster (±1°)',
        'fast_adjust': 'Ajustement rapide',
        'end_x': 'Fin X',
        'end_y': 'Fin Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Attachable',
        'X_angle': 'Angle X:',
        'snap_to_grid': 'Aligner sur la grille',
        'precise_angle': 'Angle précis:',
        'select_main_strands': 'Sélectionner les principaux axes',
        'select_main_strands_to_include_in_the_group': 'Sélectionner les principaux axes à inclure dans le groupe:',
        # New translation keys for Layer State Log
        'current_layer_state': 'État Actuel',
        'order': 'Ordre',
        'connections': 'Liens',
        'groups': 'Groupes',
        'masked_layers': 'Masques',
        'colors': 'Couleurs',
        'positions': 'Positions',
        'selected_strand': 'Sélection',
        'newest_strand': 'Nouveau Brin',
        'newest_layer': 'Nouvelle',
        'x_movement': 'Mouvement X',
        'y_movement': 'Mouvement Y',
        'move_group': 'Déplacer le Groupe',
        'grid_movement': 'Mouvement Grille',
        'x_grid_steps': 'Pas Grille X',
        'y_grid_steps': 'Pas Grille Y',
        'apply': 'Appliquer',
        'toggle_shadow': 'Ombres',
        'mask_edit_mode_message': '             MODE ÉDITION MASQUE -\n                 ÉCHAP pour quitter',
        'mask_edit_mode_exited': 'Mode édition masque terminé',
        'edit_mask': 'Éditer Masque',
        'reset_mask': 'Réinit Masque',
        'transparent_stroke': 'Bord de Départ Transparent',
        'transparent_closing_knot_side': 'Côté Transparent du Nœud Fermé',
        'restore_default_closing_knot_stroke': 'Restaurer le Trait du Nœud Fermé par Défaut',
        'restore_default_stroke': 'Restaurer Tracé Par Défaut',
        'change_color': 'Changer la couleur',
        'change_stroke_color': 'Changer la couleur du trait',
        'change_width': 'Changer largeur',
        # --- NEW ---
        'hide_layer': 'Masquer Couche',
        'show_layer': 'Afficher Couche',
        'hide_selected_layers': 'Masquer Couches Sélectionnées',
        'show_selected_layers': 'Afficher Couches Sélectionnées',
        'enable_shadow_only_selected': 'Ombre Sélectionnées',
        'disable_shadow_only_selected': 'Afficher Couches Complètes (Désactiver Ombre Seulement)',
        'hide_start_line': 'Masquer Ligne Départ',
        'show_start_line': 'Afficher Ligne Départ',
        'hide_end_line': 'Masquer Ligne Fin',
        'show_end_line': 'Afficher Ligne Fin',
        'hide_start_circle': 'Masquer Cercle Départ',
        'show_start_circle': 'Afficher Cercle Départ',
        'hide_end_circle': 'Masquer Cercle Fin',
        'show_end_circle': 'Afficher Cercle Fin',
        'close_the_knot': 'Fermer le Nœud',
        'hide_start_arrow': 'Masquer Flèche Départ',
        'show_start_arrow': 'Afficher Flèche Départ',
        'hide_end_arrow': 'Masquer Flèche Fin',
        'show_end_arrow': 'Afficher Flèche Fin',
        'hide_start_extension': 'Masquer Tiret Départ',
        'show_start_extension': 'Afficher Tiret Départ',
        'hide_end_extension': 'Masquer Tiret Fin',
        'show_end_extension': 'Afficher Tiret Fin',
        'line': 'Ligne',
        'arrow': 'Flèche',
        'extension': 'Tiret',
        'circle': 'Cercle',
        'shadow_only': 'Ombre Seulement',
        # Layer panel extension and arrow settings translations
        'extension_length': "Longueur de l'Extension",
        'extension_length_tooltip': "Longueur des lignes d'extension",
        'extension_dash_count': "Nombre de Tirets",
        'extension_dash_count_tooltip': "Nombre de tirets dans la ligne d'extension",
        'extension_dash_width': "Largeur des Tirets d'Extension",
        'extension_dash_width_tooltip': "Largeur des tirets d'extension",
        'extension_dash_gap_length': "Longueur de l'espace entre l'extrémité du brin et le début des tirets",
        'extension_dash_gap_length_tooltip': "Espace entre l'extrémité du brin et le début des tirets",
        'exit_lock_mode': 'Quitter',
        'clear_all_locks': 'Effacer',
        'select_layers_to_lock': 'Sélectionner les calques à verrouiller/déverrouiller',
        'exited_lock_mode': 'Mode verrouillage quitté',
        # Button tooltips
        'reset_tooltip': 'Réinitialiser :\nGarder uniquement l\'état\nactuel comme premier état',
        'refresh_tooltip': 'Actualiser :\nRecharger les calques',
        'center_tooltip': 'Centrer :\nDéplacer pour centrer tous\nles fils dans le canevas',
        'hide_mode_tooltip': 'Mode Masquer :\nCliquez pour activer la\nsélection de calques, puis\nclic droit pour les\nopérations de masquage/\naffichage par lot',
        'zoom_in_tooltip': 'Zoom avant',
        'zoom_out_tooltip': 'Zoom arrière',
        'pan_tooltip': 'Panoramique :\nCliquez et faites glisser\npour déplacer le canevas',
        'undo_tooltip': 'Annuler :\nAnnuler la dernière\naction',
        'redo_tooltip': 'Refaire :\nRefaire la dernière\naction annulée',
        'currently_unavailable': 'Actuellement indisponible',
        'layer_cannot_delete_tooltip': 'Cette couche ne peut pas être supprimée (les deux extrémités sont attachées)',
        'arrow_head_length': "Longueur de la Tête de Flèche",
        'arrow_head_length_tooltip': "Longueur de la tête de flèche en pixels",
        'arrow_head_width': "Largeur de la Tête de Flèche",
        'arrow_head_width_tooltip': "Largeur de la base de la tête de flèche en pixels",
        'arrow_head_stroke_width': "Épaisseur du Contour de la Tête de Flèche",
        'arrow_head_stroke_width_tooltip': "Épaisseur du contour de la tête de flèche en pixels",
        'arrow_gap_length': "Longueur de l'Espace de la Flèche",
        'arrow_gap_length_tooltip': "Espace entre l'extrémité du brin et le début du corps de la flèche",
        'arrow_line_length': "Longueur de la Ligne de Flèche",
        'arrow_line_length_tooltip': "Longueur du corps de la flèche",
        'arrow_line_width': "Largeur de la Ligne de Flèche",
        'arrow_line_width_tooltip': "Épaisseur du corps de la flèche",
        'use_default_arrow_color': "Utiliser la Couleur de Flèche par Défaut",
        # --- END NEW ---
        # Group-related translations
        'group_exists': 'Groupe Existant',
        'group_replace_confirm': 'Un groupe nommé "{}" existe déjà. Voulez-vous le remplacer?',
        # History translations (French)
        'load_selected_history': 'Charger Sélection',
        'clear_all_history': 'Effacer Tout l\'Historique',
        'confirm_clear_history_title': 'Confirmer la Suppression',
        'confirm_clear_history_text': 'Êtes-vous sûr de vouloir supprimer TOUTES les sessions d\'historique passées ? Cette action est irréversible.',
        'history_load_error_title': 'Erreur Chargement Historique',
        'history_load_error_text': 'Impossible de charger l\'état d\'historique sélectionné.',
        'history_cleared_title': 'Historique Effacé',
        'history_cleared_text': 'Toutes les sessions d\'historique passées ont été effacées.',
        'no_history_found': 'Aucune session d\'historique passée trouvée.',
        'history_explanation': 'Sélectionnez une session passée et cliquez sur "Charger Sélection" pour restaurer son état final.\\nAttention : Le chargement de l\'historique effacera vos étapes annuler/rétablir actuelles.',
        'history_list_tooltip': 'Sélectionnez une session à charger dans son état final',
        'extension_dash_gap_length': 'Longueur de l\'espace entre l\'extrémité du brin et le début des tirets',
        'extension_dash_gap_length_tooltip': 'Espace entre l\'extrémité du brin et le début des tirets',
        'width_preview_label': 'Total : {total}px | Couleur : {color}px | Contour : {stroke}px de chaque côté',
        'percent_available_color': '% de l\'espace couleur disponible',
        'total_thickness_label': 'Épaisseur totale (cases de grille):',
        'grid_squares': 'cases',
        'color_vs_stroke_label': 'Répartition Couleur / Contour (épaisseur totale fixe):',
        # Button descriptions for settings dialog
        'group_buttons': 'Boutons de Groupe',
        'draw_names_desc': 'Dessiner Noms - Affiche/masque les noms des brins sur le canevas',
        'lock_layers_desc': 'Verrouiller Calques - Active le mode verrouillage pour verrouiller/déverrouiller les brins',
        'add_new_strand_desc': 'Nouveau Brin - Ajoute un nouveau brin à votre design',
        'delete_strand_desc': 'Supprimer Brin - Supprime le brin sélectionné',
        'deselect_all_desc': 'Tout Désélectionner - Efface toutes les sélections (ou efface tous les verrous en mode verrouillage)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Panoramique (✋/✊) - ✋ Cliquez pour activer le mode panoramique, ✊ Faites glisser le canevas pour vous déplacer dans votre design',
        'zoom_in_desc': 'Zoom Avant (🔍) - Zoomez dans votre design pour un travail détaillé',
        'zoom_out_desc': 'Zoom Arrière (🔎) - Zoomez en arrière pour voir l\'ensemble',
        'center_strands_desc': 'Centrer Brins (🎯) - Centre tous les brins dans la vue',
        'multi_select_desc': 'Mode Masquer (🙉/🙈) - 🙉 Cliquez pour activer le mode masquer, 🙈 Sélectionnez les calques puis clic droit pour les opérations de masquage/affichage par lot',
        'refresh_desc': 'Actualiser (🔄) - Actualise l\'affichage du panneau des calques',
        'reset_states_desc': 'Réinitialiser États (🏠) - Remet tous les états des calques par défaut',
        # Main window button descriptions
        'attach_mode_desc': 'Mode Attacher - Connecte les brins ensemble à leurs extrémités',
        'move_mode_desc': 'Mode Déplacer - Déplace les brins et points de contrôle sur le canevas',
        'rotate_mode_desc': 'Mode Pivoter - Fait pivoter les brins sélectionnés',
        'toggle_grid_desc': 'Basculer Grille - Affiche/masque la grille sur le canevas',
        'angle_adjust_desc': 'Mode Ajustement Angle - Affine les angles des connexions de brins',
        'save_desc': 'Sauvegarder - Sauvegarde votre projet dans un fichier',
        'load_desc': 'Charger - Charge un projet depuis un fichier',
        'save_image_desc': 'Sauvegarder comme Image - Exporte votre design comme fichier image',
        'select_strand_desc': 'Sélectionner Brin - Active le mode sélection pour sélectionner les brins',
        'mask_mode_desc': 'Mode Masque - Masque les parties de brins qui passent sous d\'autres',
        'settings_desc': 'Paramètres - Ouvre la boîte de dialogue des paramètres',
        'toggle_control_points_desc': 'Basculer Points de Contrôle - Affiche/masque les points de contrôle pour les courbes de bézier',
        'toggle_shadow_desc': 'Basculer Ombre - Affiche/masque les ombres sur les brins',
        'layer_state_desc': 'État Calque - Affiche les informations de débogage sur les calques',
        # Group button descriptions
        'create_group_desc': 'Créer Groupe - Crée un nouveau groupe à partir des brins sélectionnés',
        'group_header_desc': 'En-tête Groupe - Cliquez pour développer/réduire le groupe. Clic droit pour les options',
        'rename_group_desc': 'Renommer Groupe - Change le nom de ce groupe',
        'delete_group_desc': 'Supprimer Groupe - Supprime ce groupe (les brins restent)',
        'select_group_desc': 'Sélectionner Groupe - Sélectionne tous les brins de ce groupe',
        'move_group_desc': 'Déplacer Groupe - Déplace tous les brins du groupe ensemble',
        'rotate_group_desc': 'Tourner Groupe - Fait pivoter tous les brins du groupe',
        'edit_strand_angles_desc': 'Éditer Angles des Brins - Aligne tous les angles des brins du groupe pour qu\'ils soient parallèles en un clic',
        'duplicate_group_desc': 'Dupliquer Groupe - Crée une copie de ce groupe et de ses brins',
        # About translations
        'about_info': '''
        <h2>À propos d'OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio a été développé par Yonatan Setbon. Ce logiciel a été conçu pour créer n'importe quel nœud de manière schématique en utilisant des calques pour chaque section d'un brin et en incorporant des calques masqués qui permettent un effet "dessus-dessous".
        </p>
        <p style="font-size:15px;">
            Yonatan anime une chaîne YouTube dédiée aux bracelets appelée <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, où de nombreux tutoriels présentent des diagrammes de nœuds. Ce logiciel a été créé pour faciliter la conception de tout nœud, afin de démontrer et d'expliquer comment réaliser des tutoriels de nouage complexes.
        </p>
        <p style="font-size:15px;">
            N'hésitez pas à me contacter à <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> ou à me suivre sur
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> ou
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''' ,
    },
    'de': {
        # MainWindow translations
        'play_video': 'Video abspielen',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Verbinden',
        'move_mode': 'Bewegen',
        'rotate_mode': 'Drehen',
        'toggle_grid': 'Raster',
        'angle_adjust_mode': 'Winkel/Länge',
        'select_mode': 'Auswählen',
        'mask_mode': 'Maske',
        'new_strand_mode': 'Neu',
        'save': 'Speiche.',
        'load': 'Laden',
        'save_image': 'Bild',
        'settings': 'Einstellungen',
        'light': 'Hell',
        'dark': 'Dunkel',
        'english': 'Englisch',
        'french': 'Französisch',
        'german': 'Deutsch',
        'italian': 'Italienisch',
        'spanish': 'Spanisch',
        'portuguese': 'Portugiesisch',
        'hebrew': 'Hebräisch',
        'select_theme': 'Thema auswählen',
        'default': 'Standard',
        'light': 'Hell',
        'dark': 'Dunkel',
        'layer_state': 'Status',
        'layer_state_log_title': 'Status',
        'layer_state_info_title': 'Info',
        'layer_state_info_tooltip': 'Info',
        'close': 'Schließen',
        'toggle_control_points': 'Punkte',
        'toggle_shadow': 'Schatten',
        'shadow_color': 'Schattenfarbe',
        'draw_only_affected_strand': 'Nur den betroffenen Strang beim Ziehen zeichnen',
        'enable_third_control_point': 'Dritten Kontrollpunkt in der Mitte aktivieren',
        'enable_curvature_bias_control': 'Krümmungsvoreinstellungen aktivieren',
        'enable_snap_to_grid': 'Am Raster ausrichten aktivieren',
        'show_move_highlights': 'Auswahlindikatoren in Verschiebe-/Anhängemodus anzeigen',
        'use_extended_mask': 'Erweiterte Maske verwenden (breitere Überlappung)',
        'use_extended_mask_tooltip': 'Wenn Sie Schatten verwenden möchten, einschalten; wenn nicht, ausschalten.',
        'use_extended_mask_desc': 'Wenn Sie Schatten verwenden möchten, einschalten; wenn nicht, ausschalten.',
        'shadow_blur_steps': 'Schatten-Unschärfeschritte:',
        'shadow_blur_steps_tooltip': 'Anzahl der Schritte für den Schatten-Verlaufseffekt',
        'shadow_blur_radius': 'Schatten-Unschärferadius:',
        'shadow_blur_radius_tooltip': 'Schatten-Unschärferadius in Pixeln (Bereich: 0.0 - 360.0)',
        'reset_curvature_settings': 'Krümmungseinstellungen zurücksetzen:',
        'reset': 'Zurücksetzen',
        'reset_curvature_tooltip': 'Alle Krümmungseinstellungen auf Standardwerte zurücksetzen',
        'base_fraction': 'Einfluss (Zugkraft):',
        'base_fraction_tooltip': 'Kontrollpunkt-Einflussstärke (1.0=normal, 2.0=stark, 3.0=sehr stark)',
        'distance_multiplier': 'Verstärkung (vergrößert Kurven):',
        'distance_mult_tooltip': 'Distanz-Multiplikationsfaktor (1.0=keine Verstärkung, 2.0=2x, 5.0=5x)',
        'curve_response': 'Kurvenform (1=scharf, 3=glatt):',
        'curve_response_tooltip': 'Kurvenreaktionstyp (1.0=linear, 1.5=sanfte Kurve, 2.0=quadratisch, 3.0=kubisch)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Erklärung der Layer-Statusinformationen:</b><br>
<br><br>
<b>Reihenfolge:</b> Die Abfolge der Ebenen (Stränge) auf der Leinwand.<br>
<br>
<b>Verbindungen:</b> Die Beziehungen zwischen Strängen, die anzeigen, welche Stränge verbunden oder angeheftet sind.<br>
<br>
<b>Gruppen:</b> Die Gruppen von Strängen, die gemeinsam bearbeitet werden.<br>
<br>
<b>Maskierte Ebenen:</b> Ebenen, auf die Maskierung für Über-/Unter-Effekte angewendet wurde.<br>
<br>
<b>Farben:</b> Die den Strängen zugewiesenen Farben.<br>
<br>
<b>Positionen:</b> Die Positionen der Stränge auf der Leinwand.<br>
<br>
<b>Ausgewählter Strang:</b> Der aktuell auf der Leinwand ausgewählte Strang.<br>
<br>
<b>Neuester Strang:</b> Der zuletzt erstellte Strang.<br>
<br>
<b>Neueste Ebene:</b> Die zuletzt hinzugefügte Ebene auf der Leinwand.
''',
        # SettingsDialog translations
        'general_settings': 'Einstellungen',
        'change_language': 'Sprache ändern',
        'tutorial': 'Tutorial',
        'button_explanations': 'Schaltflächen',
        'history': 'Verlauf',
        'whats_new': 'Was ist neu?',
        'samples': 'Beispiele',
        'samples_header': 'Beispielprojekte',
        'samples_sub': 'Wählen Sie ein Beispiel zum Laden und Lernen. Der Dialog schließt sich und das Beispiel wird geladen.',
            'sample_closed_knot': 'Geschlossener Knoten',
            'sample_box_stitch': 'Kästchennaht',
            'sample_overhand_knot': 'Achterknoten',
            'sample_three_strand_braid': 'Dreisträngiger Zopf',
            'sample_interwoven_double_closed_knot': 'Verflochtener doppelter geschlossener Knoten',
        'about': 'Über',
        'select_theme': 'Thema auswählen:',
        'select_language': 'Sprache auswählen:',
        'ok': 'OK',
        'cancel': 'Abbrechen',
        'apply': 'Übernehmen',
        'language_settings_info': 'Ändern Sie die Sprache der Anwendung.',
        'tutorial_info': 'Drücken Sie die Taste "Video abspielen" unter jedem Text,\num das erklärende Tutorial anzusehen:',
        'button_guide_info': 'Erfahren Sie mehr über die verschiedenen Schaltflächen und ihre Funktionen in OpenStrand Studio.\n\nTipp: Sie können auf Emoji-Symbole im Ebenenpanel klicken, um ihre Erklärungen zu sehen!',
        'layer_panel_buttons': 'Ebenenpanel-Schaltflächen',
        'main_window_buttons': 'Hauptfenster-Schaltflächen',
        'group_buttons': 'Gruppenschaltflächen',
        # General Settings descriptions for button guide
        'general_settings_header': 'Allgemeine Einstellungen',
        'theme_selection_desc': 'Thema-Auswahl - Wählen zwischen Standard, Hell oder Dunkel Themen',
        'shadow_color_desc': 'Schattenfarbe - Farbe für Strängenschatten festlegen',
        'shadow_blur_steps_desc': 'Schatten-Unschärfe-Schritte - Anzahl der Unschärfe-Iterationen (höher = glattere Schatten)',
        'shadow_blur_radius_desc': 'Schatten-Unschärfe-Radius - Größe des Unschärfe-Effekts (höher = weichere Kanten)',
        'draw_affected_strand_desc': 'Nur Betroffenen Strang Zeichnen - Zeigt nur den gezogenen Strang beim Bearbeiten',
        'third_control_point_desc': 'Dritten Kontrollpunkt Aktivieren - Fügt einen zentralen Kontrollpunkt für komplexe Kurven hinzu',
        'curvature_bias_desc': 'Krümmungs-Bias-Kontrollen Aktivieren - Fügt kleine Dreieck/Kreis-Kontrollen zur Feinabstimmung hinzu',
        'snap_to_grid_desc': 'Am Raster Ausrichten Aktivieren - Richtet Punkte automatisch am Raster beim Verschieben aus',
        'control_influence_full_desc': 'Kontrollpunkt-Einfluss - Legt fest, wie stark Kontrollpunkte die Kurve ziehen (0.25=schwach, 1.0=normal, 3.0=sehr stark)',
        'distance_boost_full_desc': 'Distanzverstärkung - Multipliziert die Kurvenstärke für ausgeprägtere Kurven (1.0=normal, 10.0=maximum)',
        'curve_shape_full_desc': 'Kurvenform - Steuert den mathematischen Kurventyp (1.0=scharfe Winkel, 2.0=glatte Kurven, 3.0=sehr glatt)',
        'reset_curvature_full_desc': 'Krümmungseinstellungen Zurücksetzen - Stellt Einfluss, Verstärkung und Form auf Standard zurück',
        # Button descriptions for settings dialog
        'draw_names_desc': 'Namen zeichnen - Zeigt/verbirgt Strangnamen auf der Leinwand',
        'lock_layers_desc': 'Ebenen sperren - Wechselt in den Sperrmodus zum Sperren/Entsperren gegen Bearbeitung',
        'add_new_strand_desc': 'Neuer Strang - Fügt Ihrem Design einen neuen Strang hinzu',
        'delete_strand_desc': 'Strang löschen - Entfernt den ausgewählten Strang',
        'deselect_all_desc': 'Alle abwählen - Hebt alle Auswahlen auf (oder entfernt alle Sperren im Sperrmodus)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Verschieben (✋/✊) - ✋ Klicken, um den Verschiebemodus zu aktivieren, ✊ Leinwand ziehen, um sich zu bewegen',
        'zoom_in_desc': 'Heranzoomen (🔍) - In Ihr Design hineinzoomen für Detailarbeit',
        'zoom_out_desc': 'Herauszoomen (🔎) - Herauszoomen, um den Überblick zu sehen',
        'center_strands_desc': 'Stränge zentrieren (🎯) - Zentriert alle Stränge in der Ansicht',
        'multi_select_desc': 'Versteckmodus (🙉/🙈) - 🙉 Aktivieren, 🙈 Ebenen wählen, dann Rechtsklick für Sammel Ein-/Ausblendung',
        'refresh_desc': 'Aktualisieren (🔄) - Aktualisiert die Anzeige des Ebenenpanels',
        'reset_states_desc': 'Zustände zurücksetzen (🏠) - Setzt alle Ebenenzustände auf Standard zurück',
        # Main window button descriptions
        'attach_mode_desc': 'Verbinden-Modus - Verbindet Stränge an ihren Endpunkten',
        'move_mode_desc': 'Bewegen-Modus - Bewegt Stränge und Kontrollpunkte auf der Leinwand',
        'rotate_mode_desc': 'Drehen-Modus - Dreht ausgewählte Stränge',
        'toggle_grid_desc': 'Raster umschalten - Raster auf der Leinwand anzeigen/ausblenden',
        'angle_adjust_desc': 'Winkel anpassen - Feinjustierung der Winkel von Strangverbindungen',
        'save_desc': 'Speichern - Speichert Ihr Projekt in einer Datei',
        'load_desc': 'Laden - Lädt ein Projekt aus einer Datei',
        'save_image_desc': 'Als Bild speichern - Exportiert Ihr Design als Bilddatei',
        'select_strand_desc': 'Strang auswählen - Aktiviert den Auswahlmodus zum Auswählen von Strängen',
        'mask_mode_desc': 'Maskenmodus - Blendet Teile von Strängen aus, die unter anderen verlaufen',
        'settings_desc': 'Einstellungen - Öffnet den Einstellungsdialog',
        'toggle_control_points_desc': 'Kontrollpunkte ein/aus - Zeigt/verbirgt Kontrollpunkte für Bézierkurven',
        'toggle_shadow_desc': 'Schatten ein/aus - Zeigt/verbirgt Schatten auf Strängen',
        'layer_state_desc': 'Layer-Status - Zeigt Debug-Informationen zu Ebenen',
        'whats_new_info': '''
        <h2>Neu in Version 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen dem mittleren Kontrollpunkt und den beiden End-Kontrollpunkten ermöglichen eine präzise Krümmungsanpassung. Diese Steuerungen erscheinen als kleine Quadrate mit einem Dreieck- oder Kreissymbol im Inneren und ermöglichen es Ihnen, den Kurveneinfluss von jeder Seite zur Mitte unabhängig anzupassen für eine präzisere Strangformung.</li>
            <li style="font-size:15px;"><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Krümmungsparameter geben Ihnen vollständige Kontrolle über Strangkurven:
                <ul style="margin-left: 20px;">
                    <li><b>Kontrollpunkt-Einfluss:</b> Passt die Zugkraft der Kontrollpunkte an (1.0=normal, bis zu 3.0=sehr stark)</li>
                    <li><b>Distanz-Verstärkung:</b> Vergrößert Kurven durch Multiplikation des Distanzfaktors (1.0=keine Verstärkung, bis zu 5.0=5-fache Verstärkung)</li>
                    <li><b>Kurvenform:</b> Steuert den Kurvenreaktionstyp (1.0=scharf/linear, 3.0=glatt/kubisch)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Progressive Kontrollpunkt-Anzeige:</b> Bei der Erstellung neuer Stränge ist zunächst nur der Start-Kontrollpunkt sichtbar. Zusätzliche Kontrollpunkte (Endpunkte, Mittelpunkt und Bias-Steuerungen) erscheinen progressiv, wenn Sie beginnen, den Strang zu bewegen, was die visuelle Unordnung bei der anfänglichen Platzierung reduziert.</li>
            <li style="font-size:15px;"><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme wurden behoben für bessere visuelle Qualität und genauere Schattendarstellung in allen Strangkonfigurationen.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Version 1.102</p>
        ''',
        # About translations
        'about_info': '''
        <h2>Über OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio wurde von Yonatan Setbon entwickelt. Die Software ist dafür gedacht, beliebige Knoten schematisch zu erstellen, indem Ebenen für jeden Abschnitt eines Strangs verwendet werden und maskierte Ebenen ein "Über-Unter-Effekt" ermöglichen.
        </p>
        <p style="font-size:15px;">
            Yonatan betreibt einen YouTube-Kanal zum Thema Lanyards namens <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, in dem viele Tutorials Knotendiagramme zeigen. Diese Software wurde entwickelt, um das Entwerfen beliebiger Knoten zu erleichtern, um zu demonstrieren und zu erklären, wie man komplexe Knotentutorials erstellt.
        </p>
        <p style="font-size:15px;">
            Kontakt: <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> oder folgen Sie mir auf
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> oder
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'Ebenenpanel',
        'draw_names': 'Namen zeigen',
        'lock_layers': 'Sperrmodus',
        'exit_lock_mode': 'Beenden',
        'clear_all_locks': 'Sperren aus',
        'select_layers_to_lock': 'Ebenen zum Sperren/Entsperren auswählen',
        'exited_lock_mode': 'Sperrmodus beendet',
        'add_new_strand': 'Neuer Strang',
        'delete_strand': 'Strang entf.',
        'deselect_all': 'Alle abwählen',
        'notification_message': 'Benachrichtigung',
        'button_color': 'Wählen Sie eine andere Schaltflächenfarbe (nicht Standard):',
        'default_strand_color': 'Standard-Strangfarbe:',
        'default_stroke_color': 'Konturfarbe:',
        'default_strand_width': 'Standard-Strangbreite',
        'default_strand_width_tooltip': 'Klicken, um die Standardbreite für neue Stränge festzulegen',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': 'Vollständigen Pfeil anzeigen',
        'hide_full_arrow': 'Vollständigen Pfeil ausblenden',
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'Winkel/Länge anpassen',
        'angle_label': 'Winkel:',
        'length_label': 'Länge:',
        'create_group': 'Neue Gruppe',
        'enter_group_name': 'Gruppennamen eingeben:',
        'group_creation_cancelled': 'Keine Hauptstränge ausgewählt. Gruppenerstellung abgebrochen.',
        'move_group_strands': 'Gruppe verschieben',
        'rotate_group_strands': 'Gruppe drehen',
        'edit_strand_angles': 'Strangwinkel bearbeiten',
        'duplicate_group': 'Gruppe duplizieren',
        'rename_group': 'Gruppe umbenennen',
        'delete_group': 'Gruppe löschen',
        'gif_explanation_1': 'Themen und Sprache einstellen.',
        'gif_explanation_2': 'Rechtsklick auf Schaltflächen im Ebenenpanel-Bereich zeigt\nderen Beschreibungen.',
        'gif_explanation_3': 'Versteckmodus aktivieren, um Ebenen auszuwählen und\nin Gruppen ein-/auszublenden.',
        'gif_explanation_4': 'Tutorial: Wie man einen geschlossenen Knoten erstellt.',
        'gif_placeholder_1': 'GIF 1 Platzhalter',
        'gif_placeholder_2': 'GIF 2 Platzhalter',
        'gif_placeholder_3': 'GIF 3 Platzhalter',
        'gif_placeholder_4': 'GIF 4 Platzhalter',
        'layer': 'Ebene',
        'angle': 'Winkel:',
        'adjust_1_degree': 'Anpassen (±1°)',
        'fast_adjust': 'Schnell anpassen',
        'end_x': 'Ende X',
        'end_y': 'Ende Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Verbindbar',
        'X_angle': 'Winkel X:',
        'snap_to_grid': 'Am Raster ausrichten',
        'precise_angle': 'Exakter Winkel:',
        'select_main_strands': 'Hauptstränge auswählen',
        'select_main_strands_to_include_in_the_group': 'Hauptstränge auswählen, die in die Gruppe aufgenommen werden sollen:',
        # New translation keys for Layer State Log
        'current_layer_state': 'Aktueller Layer-Status',
        'order': 'Reihenfolge',
        'connections': 'Verbindungen',
        'groups': 'Gruppen',
        'masked_layers': 'Maskierte Ebenen',
        'colors': 'Farben',
        'positions': 'Positionen',
        'selected_strand': 'Ausgewählter Strang',
        'newest_strand': 'Neuester Strang',
        'newest_layer': 'Neueste Ebene',
        'x_movement': 'X-Bewegung',
        'y_movement': 'Y-Bewegung',
        'move_group': 'Gruppe bewegen',
        'grid_movement': 'Rasterbewegung',
        'x_grid_steps': 'X-Rasterschritte',
        'y_grid_steps': 'Y-Rasterschritte',
        'apply': 'Übernehmen',
        'toggle_shadow': 'Schatten',
        'mask_edit_mode_message': '             MASKEN-BEARBEITUNGSMODUS -\n              Drücken Sie ESC zum Beenden',
        'mask_edit_mode_exited': 'Masken-Bearbeitungsmodus beendet',
        'edit_mask': 'Maske bearbeiten',
        'reset_mask': 'Maske zurücksetzen',
        'transparent_stroke': 'Transparente Startkante',
        'transparent_closing_knot_side': 'Transparente Seite des geschlossenen Knotens',
        'restore_default_stroke': 'Standardkontur wiederherstellen',
        'restore_default_closing_knot_stroke': 'Standardkontur (geschl. Knoten) wiederherstellen',
        'change_color': 'Farbe ändern',
        'change_stroke_color': 'Konturfarbe ändern',
        'change_width': 'Breite ändern',
        # --- NEW ---
        'hide_layer': 'Ebene ausblenden',
        'show_layer': 'Ebene einblenden',
        'hide_selected_layers': 'Ausgewählte Ebenen ausblenden',
        'show_selected_layers': 'Ausgewählte Ebenen einblenden',
        'enable_shadow_only_selected': 'Nur Schatten (Auswahl)',
        'disable_shadow_only_selected': 'Volle Ebenen anzeigen (Nur Schatten deaktivieren)',
        'hide_start_line': 'Startlinie ausblenden',
        'show_start_line': 'Startlinie einblenden',
        'hide_end_line': 'Endlinie ausblenden',
        'show_end_line': 'Endlinie einblenden',
        'hide_start_circle': 'Startkreis ausblenden',
        'show_start_circle': 'Startkreis einblenden',
        'hide_end_circle': 'Endkreis ausblenden',
        'show_end_circle': 'Endkreis einblenden',
        'close_the_knot': 'Knoten schließen',
        'hide_start_arrow': 'Startpfeil ausblenden',
        'show_start_arrow': 'Startpfeil einblenden',
        'hide_end_arrow': 'Endpfeil ausblenden',
        'show_end_arrow': 'Endpfeil einblenden',
        'hide_start_extension': 'Startstrich ausblenden',
        'show_start_extension': 'Startstrich einblenden',
        'hide_end_extension': 'Endstrich ausblenden',
        'show_end_extension': 'Endstrich einblenden',
        'line': 'Linie',
        'arrow': 'Pfeil',
        'extension': 'Strich',
        'circle': 'Kreis',
        'shadow_only': 'Nur Schatten',
        # Layer panel extension and arrow settings translations
        'extension_length': 'Länge der Erweiterung',
        'extension_length_tooltip': 'Länge der Erweiterungslinien',
        'extension_dash_count': 'Strichanzahl',
        'extension_dash_count_tooltip': 'Anzahl der Striche in der Erweiterungslinie',
        'extension_dash_width': 'Breite der Erweiterungsstriche',
        'extension_dash_width_tooltip': 'Breite der Erweiterungsstriche',
        'extension_dash_gap_length': 'Abstand zwischen Strangende und Beginn der Striche',
        'extension_dash_gap_length_tooltip': 'Abstand zwischen Strangende und Beginn der Striche',
        'arrow_head_length': 'Pfeilspitzenlänge',
        'arrow_head_length_tooltip': 'Länge der Pfeilspitze in Pixeln',
        'arrow_head_width': 'Pfeilspitzenbreite',
        'arrow_head_width_tooltip': 'Breite der Pfeilspitzenbasis in Pixeln',
        'arrow_head_stroke_width': 'Linienstärke der Pfeilspitze',
        'arrow_head_stroke_width_tooltip': 'Linienstärke der Pfeilspitze in Pixeln',
        'arrow_gap_length': 'Abstand vor dem Pfeil',
        'arrow_gap_length_tooltip': 'Abstand zwischen Strangende und Beginn des Pfeilschafts',
        'arrow_line_length': 'Pfeilschaftlänge',
        'arrow_line_length_tooltip': 'Länge des Pfeilschafts',
        'arrow_line_width': 'Pfeilschaftbreite',
        'arrow_line_width_tooltip': 'Stärke des Pfeilschafts',
        'use_default_arrow_color': 'Standard-Pfeilfarbe verwenden',
        # Button tooltips
        'reset_tooltip': 'Zurücksetzen:\nNur aktuellen Zustand\nals ersten Zustand behalten',
        'refresh_tooltip': 'Aktualisieren:\nEbenen neu laden',
        'center_tooltip': 'Zentrieren:\nLeinwand verschieben, um\nalle Stränge zu zentrieren',
        'hide_mode_tooltip': 'Versteckmodus:\nKlicken,\n um Ebenenauswahl zu \naktivieren, dann Rechtsklick\nfür Sammel-\nEin-/Ausblendung',
        'zoom_in_tooltip': 'Heranzoomen',
        'zoom_out_tooltip': 'Herauszoomen',
        'pan_tooltip': 'Verschieben:\nKlicken und ziehen, um\ndie Leinwand zu bewegen',
        'undo_tooltip': 'Rückgängig:\nLetzte Aktion rückgängig',
        'redo_tooltip': 'Wiederholen:\nLetzte Rückgängig-\nAktion wiederholen',
        'currently_unavailable': 'Derzeit nicht verfügbar',
        'layer_cannot_delete_tooltip': 'Diese Ebene kann nicht gelöscht werden (beide Enden sind verbunden)',
        # Group-related translations
        'create_group_desc': 'Gruppe erstellen - Neue Gruppe aus ausgewählten Strängen erstellen',
        'group_header_desc': 'Gruppenkopf - Klicken zum Ein-/Ausklappen. Rechtsklick für Optionen',
        'rename_group_desc': 'Gruppe umbenennen - Den Namen dieser Gruppe ändern',
        'delete_group_desc': 'Gruppe löschen - Diese Gruppe entfernen (Stränge bleiben)',
        'select_group_desc': 'Gruppe auswählen - Alle Stränge dieser Gruppe auswählen',
        'move_group_desc': 'Gruppe verschieben - Alle Stränge der Gruppe gemeinsam verschieben',
        'rotate_group_desc': 'Gruppe drehen - Alle Stränge der Gruppe drehen',
        'edit_strand_angles_desc': 'Strangwinkel bearbeiten - Alle Strangwinkel der Gruppe parallel ausrichten',
        'duplicate_group_desc': 'Gruppe duplizieren - Eine Kopie dieser Gruppe und ihrer Stränge erstellen',
        # History translations
        'load_selected_history': 'Ausgewählten laden',
        'clear_all_history': 'Gesamten Verlauf löschen',
        'confirm_clear_history_title': 'Löschen bestätigen',
        'confirm_clear_history_text': 'Möchten Sie WIRKLICH ALLE bisherigen Verlaufssitzungen löschen? Dies kann nicht rückgängig gemacht werden.',
        'history_load_error_title': 'Fehler beim Laden des Verlaufs',
        'history_load_error_text': 'Der ausgewählte Verlaufseintrag konnte nicht geladen werden.',
        'history_cleared_title': 'Verlauf gelöscht',
        'history_cleared_text': 'Alle bisherigen Verlaufssitzungen wurden gelöscht.',
        'no_history_found': 'Keine bisherigen Verlaufssitzungen gefunden.',
        'history_explanation': 'Wählen Sie eine frühere Sitzung aus und klicken Sie auf "Ausgewählten laden", um den Endzustand wiederherzustellen.\nWarnung: Das Laden des Verlaufs löscht Ihre aktuellen Rückgängig/Wiederholen-Schritte.',
        'history_list_tooltip': 'Eine Sitzung auswählen, um ihren Endzustand zu laden',
        'width_preview_label': 'Gesamt: {total}px | Farbe: {color}px | Kontur: {stroke}px je Seite',
        'percent_available_color': '% des verfügbaren Farbraums',
        'total_thickness_label': 'Gesamtdicke (Rasterfelder):',
        'grid_squares': 'Felder',
        'color_vs_stroke_label': 'Verteilung Farbe vs. Kontur (Gesamtdicke fix):',
        'extension_dash_gap_length': 'Abstand zwischen Strangende und Beginn der Striche',
        'extension_dash_gap_length_tooltip': 'Abstand zwischen Strangende und Beginn der Striche',
    },
    'it': {
        # MainWindow translations
        'play_video': 'Riproduci Video',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Collega',
        'move_mode': 'Sposta',
        'rotate_mode': 'Ruota',
        'toggle_grid': 'Griglia',
        'angle_adjust_mode': 'Angolo/Lung.',
        'select_mode': 'Seleziona',
        'mask_mode': 'Maschera',
        'new_strand_mode': 'Nuovo',
        'save': 'Salva',
        'load': 'Carica',
        'save_image': 'Immagine',
        'settings': 'Impostazioni',
        'light': 'Chiaro',
        'dark': 'Scuro',
        'english': 'Inglese',
        'french': 'Francese',
        'german': 'Tedesco',
        'italian': 'Italiano',
        'spanish': 'Spagnolo',
        'portuguese': 'Portoghese',
        'hebrew': 'Ebraico',
        'select_theme': 'Seleziona Tema',
        'default': 'Predefinito',
        'layer_state': 'Stato',
        'layer_state_log_title': 'Stato',
        'layer_state_info_title': 'Info',
        'layer_state_info_tooltip': 'Info',
        'close': 'Chiudi',
        'toggle_control_points': 'Punti',
        'toggle_shadow': 'Ombra',
        'shadow_color': 'Colore Ombra',
        'draw_only_affected_strand': 'Disegna solo il trefolo interessato durante il trascinamento',
        'enable_third_control_point': 'Abilita il terzo punto di controllo al centro',
        'enable_curvature_bias_control': 'Abilita controlli di bias di curvatura',
        'enable_snap_to_grid': 'Abilita l\'aggancio alla griglia',
        'show_move_highlights': 'Mostra indicatori di selezione nelle modalità sposta/attacca',
        'use_extended_mask': 'Usa estensione di maschera (sovrapposizione più larga)',
        'use_extended_mask_tooltip': 'Se vuoi usare le ombre, attiva; se non vuoi ombre, disattiva.',
        'use_extended_mask_desc': 'Se vuoi usare le ombre, attiva; se non vuoi ombre, disattiva.',
        'shadow_blur_steps': 'Passi di sfocatura dell\'ombra:',
        'shadow_blur_steps_tooltip': 'Numero di passi per l\'effetto di dissolvenza dell\'ombra',
        'shadow_blur_radius': 'Raggio di sfocatura dell\'ombra:',
        'shadow_blur_radius_tooltip': 'Raggio di sfocatura dell\'ombra in pixel (intervallo: 0.0 - 360.0)',
        'reset_curvature_settings': 'Ripristina impostazioni curvatura:',
        'reset': 'Ripristina',
        'reset_curvature_tooltip': 'Ripristina tutte le impostazioni di curvatura ai valori predefiniti',
        'base_fraction': 'Influenza (forza di trazione):',
        'base_fraction_tooltip': 'Forza influenza punto di controllo (1.0=normale, 2.0=forte, 3.0=molto forte)',
        'distance_multiplier': 'Amplificazione (ingrandisce curve):',
        'distance_mult_tooltip': 'Fattore di moltiplicazione distanza (1.0=nessun aumento, 2.0=2x, 5.0=5x)',
        'curve_response': 'Forma curva (1=spigolosa, 3=liscia):',
        'curve_response_tooltip': 'Tipo di risposta curva (1.0=lineare, 1.5=curva lieve, 2.0=quadratica, 3.0=cubica)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Spiegazione delle informazioni sullo stato dei livelli:</b><br>
<br><br>
<b>Ordine:</b> La sequenza dei livelli (trefoli) nell'area di disegno.<br>
<br>
<b>Connessioni:</b> Le relazioni tra i trefoli, indicando quali trefoli sono connessi o collegati.<br>
<br>
<b>Gruppi:</b> I gruppi di trefoli che vengono manipolati collettivamente.<br>
<br>
<b>Livelli Mascherati:</b> I livelli a cui è applicata una maschera per effetti sopra-sotto.<br>
<br>
<b>Colori:</b> I colori assegnati a ciascun trefolo.<br>
<br>
<b>Posizioni:</b> Le posizioni dei trefoli nell'area di disegno.<br>
<br>
<b>Trefolo Selezionato:</b> Il trefolo attualmente selezionato nell'area di disegno.<br>
<br>
<b>Trefolo Più Recente:</b> Il trefolo creato più di recente.<br>
<br>
<b>Livello Più Recente:</b> Il livello aggiunto più di recente nell'area di disegno.
''',
        # SettingsDialog translations
        'general_settings': 'Impostazioni Generali',
        'change_language': 'Cambia Lingua',
        'tutorial': 'Tutorial',
        'button_explanations': 'Guida ai pulsanti',
        'history': 'Cronologia',
        'whats_new': "Novità?",
        'samples': 'Esempi',
        'samples_header': 'Progetti di esempio',
        'samples_sub': 'Scegli un esempio da caricare per imparare. La finestra si chiuderà e l\'esempio verrà caricato.',
            'sample_closed_knot': 'Nodo chiuso',
            'sample_box_stitch': 'Punto scatola',
            'sample_overhand_knot': 'Nodo semplice',
            'sample_three_strand_braid': 'Treccia a tre capi',
            'sample_interwoven_double_closed_knot': 'Nodo chiuso doppio intrecciato',
        'about': 'Informazioni',
        'select_theme': 'Seleziona Tema:',
        'select_language': 'Seleziona Lingua:',
        'ok': 'OK',
        'cancel': 'Annulla',
        'apply': 'Applica',
        'language_settings_info': 'Cambia la lingua dell\'applicazione.',
        'tutorial_info': 'Premi il pulsante "riproduci video" sotto ogni testo\nper visualizzare il tutorial che spiega:',
        'button_guide_info': 'Scopri i diversi pulsanti e le loro funzioni in OpenStrand Studio.\n\nSuggerimento: Puoi cliccare sulle icone emoji del pannello dei livelli per vedere le loro spiegazioni!',
        'layer_panel_buttons': 'Pulsanti del Pannello Livelli',
        'main_window_buttons': 'Pulsanti della Finestra Principale',
        # General Settings descriptions for button guide
        'general_settings_header': 'Impostazioni Generali',
        'theme_selection_desc': 'Selezione Tema - Scegli tra i temi Predefinito, Chiaro o Scuro',
        'shadow_color_desc': "Colore Ombra - Imposta il colore usato per le ombre dei fili",
        'shadow_blur_steps_desc': "Passi Sfocatura Ombra - Numero di iterazioni di sfocatura (più alto = ombre più lisce)",
        'shadow_blur_radius_desc': "Raggio Sfocatura Ombra - Dimensione dell'effetto sfocatura (più alto = bordi più morbidi)",
        'draw_affected_strand_desc': 'Disegna Solo Filo Interessato - Mostra solo il filo trascinato durante la modifica',
        'third_control_point_desc': 'Abilita Terzo Punto di Controllo - Aggiunge un punto di controllo centrale per curve complesse',
        'curvature_bias_desc': 'Abilita Controlli Bias Curvatura - Aggiunge piccoli controlli triangolo/cerchio per rifinire la forma',
        'snap_to_grid_desc': 'Abilita Allineamento alla Griglia - Allinea automaticamente i punti alla griglia durante lo spostamento',
        'control_influence_full_desc': 'Influenza Punto di Controllo - Imposta quanto i punti di controllo tirano la curva (0.25=debole, 1.0=normale, 3.0=molto forte)',
        'distance_boost_full_desc': 'Amplificazione Distanza - Moltiplica la forza della curva per curve più pronunciate (1.0=normale, 10.0=massimo)',
        'curve_shape_full_desc': 'Forma Curva - Controlla il tipo di curva matematica (1.0=angoli acuti, 2.0=curve lisce, 3.0=molto liscio)',
        'reset_curvature_full_desc': 'Ripristina Impostazioni Curvatura - Ripristina Influenza, Amplificazione e Forma ai valori predefiniti',
        'whats_new_info': '''
        <h2>Novità della versione 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias posizionati tra il punto di controllo centrale e i due punti di controllo finali forniscono una regolazione fine della curvatura. Questi controlli appaiono come piccoli quadrati con un'icona triangolare o circolare all'interno, permettendoti di regolare indipendentemente l'influenza della curva da ciascun lato verso il centro per una modellazione più precisa dei trefoli.</li>
            <li style="font-size:15px;"><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri di curvatura ti danno il controllo completo sulle curve dei trefoli:
                <ul style="margin-left: 20px;">
                    <li><b>Influenza del punto di controllo:</b> Regola la forza di attrazione dei punti di controllo (1.0=normale, fino a 3.0=molto forte)</li>
                    <li><b>Amplificazione della distanza:</b> Ingrandisce le curve moltiplicando il fattore di distanza (1.0=nessuna amplificazione, fino a 5.0=amplificazione 5x)</li>
                    <li><b>Forma della curva:</b> Controlla il tipo di risposta della curva (1.0=netto/lineare, 3.0=liscio/cubico)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Visualizzazione progressiva dei punti di controllo:</b> Durante la creazione di nuovi trefoli, inizialmente è visibile solo il punto di controllo iniziale. I punti di controllo aggiuntivi (punti finali, punto centrale e controlli di bias) appaiono progressivamente quando inizi a muovere il trefolo, riducendo il disordine visivo durante il posizionamento iniziale.</li>
            <li style="font-size:15px;"><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva e una rappresentazione più accurata delle ombre in tutte le configurazioni dei trefoli.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Versione 1.102</p>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'Pannello Livelli',
        'draw_names': 'Disegna Nomi',
        'lock_layers': 'Blocca Liv.',
        'add_new_strand': 'Nuovo Trefolo',
        'delete_strand': 'Elim. Trefolo',
        'deselect_all': 'Desel. Tutto',
        'notification_message': 'Notifica',
        'button_color': 'Scegli un colore di pulsante diverso (non predefinito):',
        'default_strand_color': 'Colore Trefolo Predefinito:',
        'default_stroke_color': 'Colore Contorno:',
        'default_strand_width': 'Larghezza Trefolo Predefinita',
        'default_strand_width_tooltip': 'Clicca per impostare la larghezza predefinita per i nuovi trefoli',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "Mostra freccia completa",
        'hide_full_arrow': "Nascondi freccia completa",
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'Regola Ang.',
        'angle_label': 'Angolo:',
        'length_label': 'Lunghezza:',
        'create_group': 'Crea Gruppo',
        'enter_group_name': 'Inserisci nome gruppo:',
        'group_creation_cancelled': 'Nessun trefolo principale selezionato. Creazione gruppo annullata.',
        'move_group_strands': 'Sposta Gruppo',
        'rotate_group_strands': 'Ruota Gruppo',
        'edit_strand_angles': 'Modifica Angoli Trefolo',
        'duplicate_group': 'Duplica Gruppo',
        'rename_group': 'Rinomina Gruppo',
        'delete_group': 'Elimina Gruppo',
        'gif_explanation_1': 'Impostazione temi e lingua.',
        'gif_explanation_2': 'Facendo clic con il pulsante destro sui pulsanti nell\'area del pannello\ndei livelli si rivelano le loro descrizioni.',
        'gif_explanation_3': 'Attivazione della modalità nascondi per selezionare e\nnascondere/mostrare livelli in batch.',
        'gif_explanation_4': 'Tutorial: Come creare un nodo chiuso.',
        'gif_placeholder_1': 'Segnaposto GIF 1',
        'gif_placeholder_2': 'Segnaposto GIF 2',
        'gif_placeholder_3': 'Segnaposto GIF 3',
        'gif_placeholder_4': 'Segnaposto GIF 4',
        'layer': 'Livello',
        'angle': 'Angolo:',
        'adjust_1_degree': 'Regola (±1°)',
        'fast_adjust': 'Regolazione Rapida',
        'end_x': 'Fine X',
        'end_y': 'Fine Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Collegabile',
        'X_angle': 'Angolo X:',
        'snap_to_grid': 'Aggancia alla griglia',
        'precise_angle': 'Angolo preciso:',
        'select_main_strands': 'Seleziona Trefoli Principali',
        'select_main_strands_to_include_in_the_group': 'Seleziona i trefoli principali da includere nel gruppo:',
        # New translation keys for Layer State Log
        'current_layer_state': 'Stato Livello Corrente',
        'order': 'Ordine',
        'connections': 'Connessioni',
        'groups': 'Gruppi',
        'masked_layers': 'Livelli Mascherati',
        'colors': 'Colori',
        'positions': 'Posizioni',
        'selected_strand': 'Trefolo Selezionato',
        'newest_strand': 'Trefolo Più Recente',
        'newest_layer': 'Livello Più Recente',
        'x_movement': 'Movimento X',
        'y_movement': 'Movimento Y',
        'move_group': 'Sposta Gruppo',
        'grid_movement': 'Movimento Griglia',
        'x_grid_steps': 'Passi Griglia X',
        'y_grid_steps': 'Passi Griglia Y',
        'apply': 'Applica',
        'toggle_shadow': 'Ombra',
        'mask_edit_mode_message': '             MODALITÀ MODIFICA MASCHERA -\n              Premi ESC per uscire',
        'mask_edit_mode_exited': 'Modalità modifica maschera terminata',
        'edit_mask': 'Modifica Maschera',
        'reset_mask': 'Reimposta Maschera',
        'transparent_stroke': 'Bordo di Partenza Trasparente',
        'transparent_closing_knot_side': 'Lato Trasparente del Nodo Chiuso',
        'restore_default_closing_knot_stroke': 'Ripristina Bordo del Nodo Chiuso Predefinito',
        'restore_default_stroke': 'Ripristina Traccia Predefinita',
        'change_color': 'Cambia colore',
        'change_stroke_color': 'Cambia colore del tratto',
        'change_width': 'Cambia larghezza',
        # --- NEW ---
        'hide_layer': 'Nascondi Livello',
        'show_layer': 'Mostra Livello',
        'hide_selected_layers': 'Nascondi Livelli Selezionati',
        'show_selected_layers': 'Mostra Livelli Selezionati',
        'enable_shadow_only_selected': 'Solo Ombra Selezionati',
        'disable_shadow_only_selected': 'Mostra Livelli Completi (Disabilita Solo Ombra)',
        'hide_start_line': 'Nascondi Linea Inizio',
        'show_start_line': 'Mostra Linea Inizio',
        'hide_end_line': 'Nascondi Linea Fine',
        'show_end_line': 'Mostra Linea Fine',
        'hide_start_circle': 'Nascondi Cerchio Inizio',
        'show_start_circle': 'Mostra Cerchio Inizio',
        'hide_end_circle': 'Nascondi Cerchio Fine',
        'show_end_circle': 'Mostra Cerchio Fine',
        'close_the_knot': 'Chiudi il Nodo',
        'hide_start_arrow': 'Nascondi Freccia Inizio',
        'show_start_arrow': 'Mostra Freccia Inizio',
        'hide_end_arrow': 'Nascondi Freccia Fine',
        'show_end_arrow': 'Mostra Freccia Fine',
        'hide_start_extension': 'Nascondi Trattino Inizio',
        'show_start_extension': 'Mostra Trattino Inizio',
        'hide_end_extension': 'Nascondi Trattino Fine',
        'show_end_extension': 'Mostra Trattino Fine',
        'line': 'Linea',
        'arrow': 'Freccia',
        'extension': 'Trattino',
        'circle': 'Cerchio',
        'shadow_only': 'Solo Ombra',
        # Layer panel extension and arrow settings translations
        'extension_length': 'Lunghezza estensione',
        'extension_length_tooltip': 'Lunghezza della linea di estensione',
        'extension_dash_count': 'Numero di trattini',
        'extension_dash_count_tooltip': 'Numero di trattini nella linea di estensione',
        'extension_dash_width': 'Spessore trattino estensione',
        'extension_dash_width_tooltip': 'Spessore del trattino di estensione',
        'extension_dash_gap_length': 'Lunghezza dello spazio tra la fine del filo e l\'inizio dei trattini',
        'extension_dash_gap_length_tooltip': 'Spazio tra la fine del filo e l\'inizio dei trattini',
        'exit_lock_mode': 'Esci',
        'clear_all_locks': 'Cancella',
        'select_layers_to_lock': 'Seleziona livelli da bloccare/sbloccare',
        'exited_lock_mode': 'Uscito dalla modalità blocco',
        # Button tooltips
        'reset_tooltip': 'Ripristina:\nMantieni solo lo stato\ncorrente come primo stato',
        'refresh_tooltip': 'Aggiorna:\nRicarica i livelli',
        'center_tooltip': 'Centra:\nSposta per centrare tutti\ni fili nel canvas',
        'hide_mode_tooltip': 'Modalità Nascondi:\nClicca per abilitare la\nselezione dei livelli, poi\nclick destro per operazioni\ndi nascondi/mostra in batch',
        'zoom_in_tooltip': 'Zoom avanti',
        'zoom_out_tooltip': 'Zoom indietro',
        'pan_tooltip': 'Panoramica:\nClicca e trascina per\nmuovere il canvas',
        'undo_tooltip': 'Annulla:\nAnnulla l\'ultima azione',
        'redo_tooltip': 'Ripeti:\nRipeti l\'ultima azione\nannullata',
        'currently_unavailable': 'Attualmente non disponibile',
        'layer_cannot_delete_tooltip': 'Questo livello non può essere eliminato (entrambe le estremità sono collegate)',
        'arrow_head_length': 'Lunghezza punta freccia',
        'arrow_head_length_tooltip': 'Lunghezza della punta della freccia in pixel',
        'arrow_head_width': 'Larghezza punta freccia',
        'arrow_head_width_tooltip': 'Larghezza della punta della freccia in pixel',
        'arrow_head_stroke_width': 'Spessore Contorno Punta Freccia',
        'arrow_head_stroke_width_tooltip': 'Spessore del contorno della punta della freccia in pixel',
        'arrow_gap_length': 'Spazio prima della freccia',
        'arrow_gap_length_tooltip': 'Spazio tra l\'estremità del filo e l\'inizio della freccia',
        'arrow_line_length': 'Lunghezza corpo freccia',
        'arrow_line_length_tooltip': 'Lunghezza del corpo della freccia in pixel',
        'arrow_line_width': 'Spessore corpo freccia',
        'arrow_line_width_tooltip': 'Spessore del corpo della freccia in pixel',
        'use_default_arrow_color': 'Usa colore freccia predefinito',

        # --- END NEW ---
        # Group-related translations
        'group_exists': 'Gruppo Esistente',
        'group_replace_confirm': 'Un gruppo chiamato "{}" esiste già. Vuoi sostituirlo?',
        # History translations
        'load_selected_history': 'Carica Selezionato',
        'clear_all_history': 'Cancella Tutta la Cronologia',
        'confirm_clear_history_title': 'Conferma Cancellazione Cronologia',
        'confirm_clear_history_text': 'Sei sicuro di voler eliminare TUTTE le sessioni di cronologia passate? Questa operazione non può essere annullata.',
        'history_load_error_title': 'Errore Caricamento Cronologia',
        'history_load_error_text': 'Impossibile caricare lo stato della cronologia selezionato.',
        'history_cleared_title': 'Cronologia Cancellata',
        'history_cleared_text': 'Tutte le sessioni di cronologia passate sono state cancellate.',
        'no_history_found': 'Nessuna sessione di cronologia passata trovata.',
        'history_explanation': 'Seleziona una sessione passata e fai clic su "Carica Selezionato" per ripristinarne lo stato finale.\nAttenzione: il caricamento della cronologia cancellerà i passaggi annulla/ripristina correnti.',
        'history_list_tooltip': 'Seleziona una sessione da caricare nel suo stato finale',
        'extension_dash_gap_length': 'Lunghezza dello spazio tra la fine del filo e l\'inizio dei trattini',
        'extension_dash_gap_length_tooltip': 'Spazio tra la fine del filo e l\'inizio dei trattini',
        'width_preview_label': 'Totale: {total}px | Colore: {color}px | Contorno: {stroke}px per lato',
        'percent_available_color': '% dello Spazio Colore Disponibile',
        'total_thickness_label': 'Spessore Totale (quadrati griglia):',
        'grid_squares': 'quadrati',
        'color_vs_stroke_label': 'Distribuzione Colore vs Contorno (spessore totale fisso):',
        # Button descriptions for settings dialog
        'group_buttons': 'Pulsanti Gruppo',
        'draw_names_desc': 'Disegna Nomi - Mostra/nasconde i nomi dei fili sul canvas',
        'lock_layers_desc': 'Blocca Livelli - Attiva la modalità blocco per bloccare/sbloccare i fili dalla modifica',
        'add_new_strand_desc': 'Nuovo Filo - Aggiunge un nuovo filo al tuo design',
        'delete_strand_desc': 'Elimina Filo - Rimuove il filo selezionato',
        'deselect_all_desc': 'Deseleziona Tutto - Cancella tutte le selezioni (o cancella tutti i blocchi in modalità blocco)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Panoramica (✋/✊) - ✋ Clicca per attivare la modalità panoramica, ✊ Trascina il canvas per muoverti nel tuo design',
        'zoom_in_desc': 'Zoom Avanti (🔍) - Ingrandisci il tuo design per lavori dettagliati',
        'zoom_out_desc': 'Zoom Indietro (🔎) - Rimpicciolisci per vedere il quadro generale',
        'center_strands_desc': 'Centra Fili (🎯) - Centra tutti i fili nella vista',
        'multi_select_desc': 'Modalità Nascondi (🙉/🙈) - 🙉 Clicca per attivare la modalità nascondi, 🙈 Seleziona i livelli poi click destro per operazioni di nascondi/mostra in batch',
        'refresh_desc': 'Aggiorna (🔄) - Aggiorna la visualizzazione del pannello livelli',
        'reset_states_desc': 'Ripristina Stati (🏠) - Ripristina tutti gli stati dei livelli al default',
        # Main window button descriptions
        'attach_mode_desc': 'Modalità Collega - Collega i fili insieme alle loro estremità',
        'move_mode_desc': 'Modalità Sposta - Sposta fili e punti di controllo sul canvas',
        'rotate_mode_desc': 'Modalità Ruota - Ruota i fili selezionati',
        'toggle_grid_desc': 'Attiva/Disattiva Griglia - Mostra/nasconde la griglia sul canvas',
        'angle_adjust_desc': 'Modalità Regola Angolo - Regola finemente gli angoli delle connessioni dei fili',
        'save_desc': 'Salva - Salva il tuo progetto in un file',
        'load_desc': 'Carica - Carica un progetto da un file',
        'save_image_desc': 'Salva come Immagine - Esporta il tuo design come file immagine',
        'select_strand_desc': 'Seleziona Filo - Attiva la modalità selezione per selezionare i fili',
        'mask_mode_desc': 'Modalità Maschera - Nasconde parti di fili che passano sotto altri',
        'settings_desc': 'Impostazioni - Apre la finestra delle impostazioni',
        'toggle_control_points_desc': 'Attiva/Disattiva Punti di Controllo - Mostra/nasconde i punti di controllo per le curve di bézier',
        'toggle_shadow_desc': 'Attiva/Disattiva Ombra - Mostra/nasconde le ombre sui fili',
        'layer_state_desc': 'Stato Livello - Visualizza informazioni di debug sui livelli',
        # Group button descriptions
        'create_group_desc': 'Crea Gruppo - Crea un nuovo gruppo dai fili selezionati',
        'group_header_desc': 'Intestazione Gruppo - Clicca per espandere/collassare il gruppo. Click destro per opzioni',
        'rename_group_desc': 'Rinomina Gruppo - Cambia il nome di questo gruppo',
        'delete_group_desc': 'Elimina Gruppo - Rimuove questo gruppo (i fili rimangono)',
        'select_group_desc': 'Seleziona Gruppo - Seleziona tutti i fili in questo gruppo',
        'move_group_desc': 'Sposta Gruppo - Sposta tutti i fili del gruppo insieme',
        'rotate_group_desc': 'Ruota Gruppo - Ruota tutti i fili del gruppo',
        'edit_strand_angles_desc': 'Modifica Angoli dei Fili - Allinea tutti gli angoli dei fili nel gruppo per renderli paralleli con un solo clic',
        'duplicate_group_desc': 'Duplica Gruppo - Crea una copia di questo gruppo e dei suoi fili',
        # About translations
        'about_info': '''
        <h2>Informazioni su OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio è stato sviluppato da Yonatan Setbon. Il software è stato progettato per creare qualsiasi nodo in modo schematico utilizzando strati per ogni sezione di un filo e incorporando strati mascherati che consentono un effetto "sopra-sotto".
        </p>
        <p style="font-size:15px;">
            Yonatan gestisce un canale YouTube dedicato ai nastro di sicurezza chiamato <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, dove molti tutorial presentano diagrammi di nodi. Questo software è stato creato per facilitare la progettazione di qualsiasi nodo, al fine di dimostrare e spiegare come realizzare tutorial di nuovo nodo complessi.
        </p>
        <p style="font-size:15px;">
            Sentitevi liberi di contattarmi a <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> o di seguirmi su
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> o
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''' ,
    },
    # New Spanish Translations
    'es': {
        # MainWindow translations
        'play_video': 'Reproducir Vídeo',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Unir',
        'move_mode': 'Mover',
        'rotate_mode': 'Rotar',
        'toggle_grid': 'Cuadrícula',
        'angle_adjust_mode': 'Ángulo/Long.',
        'select_mode': 'Seleccionar',
        'mask_mode': 'Máscara',
        'new_strand_mode': 'Nuevo',
        'save': 'Guardar',
        'load': 'Cargar',
        'save_image': 'Imagen',
        'settings': 'Configuración',
        'light': 'Claro',
        'dark': 'Oscuro',
        'english': 'Inglés',
        'french': 'Francés',
        'german': 'Alemán',
        'italian': 'Italiano',
        'spanish': 'Español',
        'portuguese': 'Portugués',
        'hebrew': 'Hebreo',
        'select_theme': 'Seleccionar Tema',
        'default': 'Predeterm.',
        'light': 'Claro',
        'dark': 'Oscuro',
        'layer_state': 'Estado',
        'layer_state_log_title': 'Estado',
        'layer_state_info_title': 'Info',
        'layer_state_info_tooltip': 'Info',
        'close': 'Cerrar',
        'toggle_control_points': 'Puntos',
        'toggle_shadow': 'Sombra',
        'shadow_color': 'Color de Sombra',
        'draw_only_affected_strand': 'Dibujar solo el cordón afectado al arrastrar',
        'enable_third_control_point': 'Habilitar tercer punto de control en el centro',
        'enable_curvature_bias_control': 'Habilitar controles de sesgo de curvatura',
        'enable_snap_to_grid': 'Habilitar ajuste a la cuadrícula',
        'show_move_highlights': 'Mostrar indicadores de selección en modos mover/adjuntar',
        'use_extended_mask': 'Usar extensión de máscara (superposición más ancha)',
        'use_extended_mask_tooltip': 'Si quieres usar sombras, activa; si no quieres sombras, desactiva.',
        'use_extended_mask_desc': 'Si quieres usar sombras, activa; si no quieres sombras, desactiva.',
        'shadow_blur_steps': 'Pasos de desenfoque de sombra:',
        'shadow_blur_steps_tooltip': 'Número de pasos para el efecto de desvanecimiento de sombra',
        'shadow_blur_radius': 'Radio de desenfoque de sombra:',
        'shadow_blur_radius_tooltip': 'Radio de desenfoque de sombra en píxeles (rango: 0.0 - 360.0)',
        'reset_curvature_settings': 'Restablecer configuración de curvatura:',
        'reset': 'Restablecer',
        'reset_curvature_tooltip': 'Restablecer toda la configuración de curvatura a los valores predeterminados',
        'base_fraction': 'Influencia (fuerza de tracción):',
        'base_fraction_tooltip': 'Fuerza de influencia del punto de control (1.0=normal, 2.0=fuerte, 3.0=muy fuerte)',
        'distance_multiplier': 'Amplificación (agranda curvas):',
        'distance_mult_tooltip': 'Factor de multiplicación de distancia (1.0=sin aumento, 2.0=2x, 5.0=5x)',
        'curve_response': 'Forma curva (1=angular, 3=suave):',
        'curve_response_tooltip': 'Tipo de respuesta de curva (1.0=lineal, 1.5=curva suave, 2.0=cuadrática, 3.0=cúbica)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Explicación de la Información de Estado de Capas:</b><br>
<br><br>
<b>Orden:</b> La secuencia de capas (cordones) en el lienzo.<br>
<br>
<b>Conexiones:</b> Las relaciones entre los cordones, indicando qué cordones están conectados o unidos.<br>
<br>
<b>Grupos:</b> Los grupos de cordones que se manipulan colectivamente.<br>
<br>
<b>Capas Enmascaradas:</b> Las capas que tienen aplicada una máscara para efectos de arriba-abajo.<br>
<br>
<b>Colores:</b> Los colores asignados a cada cordón.<br>
<br>
<b>Posiciones:</b> Las posiciones de los cordones en el lienzo.<br>
<br>
<b>Cordón Seleccionado:</b> El cordón actualmente seleccionado en el lienzo.<br>
<br>
<b>Cordón Más Reciente:</b> El cordón creado más recientemente.<br>
<br>
<b>Capa Más Reciente:</b> La capa añadida más recientemente en el lienzo.
''',
        # SettingsDialog translations
        'general_settings': 'Configuración General',
        'change_language': 'Cambiar Idioma',
        'tutorial': 'Tutorial',
        'button_explanations': 'Guía de botones',
        'history': 'Historial',
        'whats_new': "¿Qué hay de nuevo?",
        'samples': 'Ejemplos',
        'samples_header': 'Proyectos de ejemplo',
        'samples_sub': 'Elige un ejemplo para cargar y aprender. El cuadro de diálogo se cerrará y el ejemplo se cargará.',
            'sample_closed_knot': 'Nudo cerrado',
            'sample_box_stitch': 'Puntada de caja',
            'sample_overhand_knot': 'Nudo simple',
            'sample_three_strand_braid': 'Trenza de tres cabos',
            'sample_interwoven_double_closed_knot': 'Nudo cerrado doble entrelazado',
        'about': 'Acerca',
        'select_theme': 'Seleccionar Tema:',
        'select_language': 'Seleccionar Idioma:',
        'ok': 'OK',
        'cancel': 'Cancelar',
        'apply': 'Aplicar',
        'language_settings_info': 'Cambiar el idioma de la aplicación.',
        'tutorial_info': 'Presiona el botón "reproducir vídeo" debajo de cada texto\npara ver el tutorial que explica:',
        'button_guide_info': 'Aprende sobre los diferentes botones y sus funciones en OpenStrand Studio.\n\n¡Consejo: Puedes hacer clic en los iconos emoji del panel de capas para ver sus explicaciones!',
        'layer_panel_buttons': 'Botones del Panel de Capas',
        'main_window_buttons': 'Botones de la Ventana Principal',
        # General Settings descriptions for button guide
        'general_settings_header': 'Configuración General',
        'theme_selection_desc': 'Selección de Tema - Elegir entre los temas Predeterminado, Claro u Oscuro',
        'shadow_color_desc': 'Color de Sombra - Establecer el color usado para las sombras de las hebras',
        'shadow_blur_steps_desc': 'Pasos de Desenfoque de Sombra - Número de iteraciones de desenfoque (mayor = sombras más suaves)',
        'shadow_blur_radius_desc': 'Radio de Desenfoque de Sombra - Tamaño del efecto de desenfoque (mayor = bordes más suaves)',
        'draw_affected_strand_desc': 'Dibujar Solo Hebra Afectada - Muestra solo la hebra arrastrada durante la edición',
        'third_control_point_desc': 'Habilitar Tercer Punto de Control - Añade un punto de control central para curvas complejas',
        'curvature_bias_desc': 'Habilitar Controles de Sesgo de Curvatura - Añade pequeños controles triángulo/círculo para afinar la forma',
        'snap_to_grid_desc': 'Habilitar Ajuste a la Cuadrícula - Alinea automáticamente los puntos a la cuadrícula al mover',
        'control_influence_full_desc': 'Influencia del Punto de Control - Establece cuánto los puntos de control tiran de la curva (0.25=débil, 1.0=normal, 3.0=muy fuerte)',
        'distance_boost_full_desc': 'Amplificación de Distancia - Multiplica la fuerza de la curva para curvas más pronunciadas (1.0=normal, 10.0=máximo)',
        'curve_shape_full_desc': 'Forma de Curva - Controla el tipo de curva matemática (1.0=ángulos agudos, 2.0=curvas suaves, 3.0=muy suave)',
        'reset_curvature_full_desc': 'Restablecer Configuración de Curvatura - Restaura Influencia, Amplificación y Forma a valores predeterminados',
        'whats_new_info': '''
        <h2>Novedades de la versión 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo posicionados entre el punto de control central y los dos puntos de control finales proporcionan un ajuste fino de la curvatura. Estos controles aparecen como pequeños cuadrados con un icono de triángulo o círculo en su interior, permitiéndote ajustar independientemente la influencia de la curva desde cada lado hacia el centro para un modelado más preciso de las hebras.</li>
            <li style="font-size:15px;"><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros de curvatura te dan control completo sobre las curvas de las hebras:
                <ul style="margin-left: 20px;">
                    <li><b>Influencia del punto de control:</b> Ajusta la fuerza de atracción de los puntos de control (1.0=normal, hasta 3.0=muy fuerte)</li>
                    <li><b>Amplificación de distancia:</b> Magnifica las curvas multiplicando el factor de distancia (1.0=sin amplificación, hasta 5.0=amplificación 5x)</li>
                    <li><b>Forma de curva:</b> Controla el tipo de respuesta de curva (1.0=agudo/lineal, 3.0=suave/cúbico)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Visualización progresiva de puntos de control:</b> Al crear nuevas hebras, inicialmente solo es visible el punto de control inicial. Los puntos de control adicionales (puntos finales, punto central y controles de sesgo) aparecen progresivamente cuando comienzas a mover la hebra, reduciendo el desorden visual durante la colocación inicial.</li>
            <li style="font-size:15px;"><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para obtener mejor calidad visual y una representación más precisa de las sombras en todas las configuraciones de hebras.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Versión 1.102</p>

        ''',
 

        # LayerPanel translations
        'layer_panel_title': 'Panel de Capas',
        'draw_names': 'Ver Nombres',
        'lock_layers': 'Bloq. Capas',
        'add_new_strand': 'Nuevo Cordón',
        'delete_strand': 'Elim. Cordón',
        'deselect_all': 'Deselec. Todo',
        'notification_message': 'Notificación',
        'button_color': 'Elija un color de botón diferente (no predeterminado):',
        'default_strand_color': 'Color de Cordón Predeterminado:',
        'default_stroke_color': 'Color de Contorno:',
        'default_strand_width': 'Ancho de Cordón Predeterminado',
        'default_strand_width_tooltip': 'Haga clic para establecer el ancho predeterminado para nuevos cordones',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "Mostrar flecha completa",
        'hide_full_arrow': "Ocultar flecha completa",
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'Ajust. Áng.',
        'angle_label': 'Ángulo:',
        'length_label': 'Longitud:',
        'create_group': 'Crear Grupo',
        'enter_group_name': 'Introduce nombre del grupo:',
        'group_creation_cancelled': 'No hay cordones principales seleccionados. Creación de grupo cancelada.',
        'move_group_strands': 'Mover Grupo',
        'rotate_group_strands': 'Rotar Grupo',
        'edit_strand_angles': 'Editar Ángulos del Cordón',
        'duplicate_group': 'Duplicar Grupo',
        'rename_group': 'Renombrar Grupo',
        'delete_group': 'Eliminar Grupo',
        'gif_explanation_1': 'Configuración de temas e idioma.',
        'gif_explanation_2': 'Hacer clic derecho en los botones del área del panel de capas revela\nsus descripciones.',
        'gif_explanation_3': 'Activación del modo ocultar para seleccionar y ocultar/mostrar\ncapas en lote.',
        'gif_explanation_4': 'Tutorial: Cómo crear un nudo cerrado.',
        'gif_placeholder_1': 'Marcador GIF 1',
        'gif_placeholder_2': 'Marcador GIF 2',
        'gif_placeholder_3': 'Marcador GIF 3',
        'gif_placeholder_4': 'Marcador GIF 4',
        'layer': 'Capa',
        'angle': 'Ángulo:',
        'adjust_1_degree': 'Ajustar (±1°)',
        'fast_adjust': 'Ajuste Rápido',
        'end_x': 'Fin X',
        'end_y': 'Fin Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Unible',
        'X_angle': 'Ángulo X:',
        'snap_to_grid': 'Ajustar a la cuadrícula',
        'precise_angle': 'Ángulo preciso:',
        'select_main_strands': 'Seleccionar Cordones Principales',
        'select_main_strands_to_include_in_the_group': 'Seleccionar cordones principales para incluir en el grupo:',
        # New translation keys for Layer State Log
        'current_layer_state': 'Estado Actual de Capas',
        'order': 'Orden',
        'connections': 'Conexiones',
        'groups': 'Grupos',
        'masked_layers': 'Capas Enmascaradas',
        'colors': 'Colores',
        'positions': 'Posiciones',
        'selected_strand': 'Cordón Seleccionado',
        'newest_strand': 'Cordón Más Reciente',
        'newest_layer': 'Capa Más Reciente',
        'x_movement': 'Movimiento X',
        'y_movement': 'Movimiento Y',
        'move_group': 'Mover Grupo',
        'grid_movement': 'Movimiento Cuadrícula',
        'x_grid_steps': 'Pasos Cuadrícula X',
        'y_grid_steps': 'Pasos Cuadrícula Y',
        'apply': 'Aplicar',
        'toggle_shadow': 'Sombra',
        'mask_edit_mode_message': '             MODO EDICIÓN MÁSCARA -\n              Presiona ESC para salir',
        'mask_edit_mode_exited': 'Modo edición máscara finalizado',
        'edit_mask': 'Editar Máscara',
        'reset_mask': 'Restablecer Máscara',
        'transparent_stroke': 'Borde de Inicio Transparente',
        'transparent_closing_knot_side': 'Lado Transparente del Nudo Cerrado',
        'restore_default_closing_knot_stroke': 'Restaurar Borde del Nudo Cerrado Predeterminado',
        'restore_default_stroke': 'Restaurar Trazo Predeterminado',
        'change_color': 'Cambiar color',
        'change_stroke_color': 'Cambiar color del trazo',
        'change_width': 'Cambiar ancho',
        # --- NEW ---
        'hide_layer': 'Ocultar Capa',
        'show_layer': 'Mostrar Capa',
        'hide_selected_layers': 'Ocultar Capas Seleccionadas',
        'show_selected_layers': 'Mostrar Capas Seleccionadas',
        'enable_shadow_only_selected': 'Solo Sombra Seleccionadas',
        'disable_shadow_only_selected': 'Mostrar Capas Completas (Desactivar Solo Sombra)',
        'hide_start_line': 'Ocultar Línea Inicio',
        'show_start_line': 'Mostrar Línea Inicio',
        'hide_end_line': 'Ocultar Línea Fin',
        'show_end_line': 'Mostrar Línea Fin',
        'hide_start_circle': 'Ocultar Círculo Inicio',
        'show_start_circle': 'Mostrar Círculo Inicio',
        'hide_end_circle': 'Ocultar Círculo Fim',
        'show_end_circle': 'Mostrar Círculo Fin',
        'close_the_knot': 'Cerrar el Nudo',
        'hide_start_arrow': 'Ocultar Flecha Inicio',
        'show_start_arrow': 'Mostrar Flecha Inicio',
        'hide_end_arrow': 'Ocultar Flecha Fin',
        'show_end_arrow': 'Mostrar Flecha Fin',
        'hide_start_extension': 'Ocultar Guión Inicio',
        'show_start_extension': 'Mostrar Guión Inicio',
        'hide_end_extension': 'Ocultar Guión Fin',
        'show_end_extension': 'Mostrar Guión Fin',
        'line': 'Línea',
        'arrow': 'Flecha',
        'extension': 'Guión',
        'circle': 'Círculo',
        'shadow_only': 'Solo Sombra',
        # Layer panel extension and arrow settings translations
        'extension_length': 'Longitud de la extensión',
        'extension_length_tooltip': 'Longitud de la línea de extensión',
        'extension_dash_count': 'Número de guiones de extensión',
        'extension_dash_count_tooltip': 'Número de guiones en la línea de extensión',
        'extension_dash_width': 'Grosor del guión de extensión',
        'extension_dash_width_tooltip': 'Grosor de los guiones de extensión',
        'extension_dash_gap_length': 'Longitud del espacio entre el extremo del cordón y el inicio de los guiones',
        'extension_dash_gap_length_tooltip': 'Espacio entre el extremo del cordón y el inicio de los guiones',
        'exit_lock_mode': 'Salir',
        'clear_all_locks': 'Limpiar',
        'select_layers_to_lock': 'Seleccionar capas para bloquear/desbloquear',
        'exited_lock_mode': 'Salió del modo bloqueo',
        # Button tooltips
        'reset_tooltip': 'Restablecer:\nMantener solo el estado\nactual como primer estado',
        'refresh_tooltip': 'Actualizar:\nRecargar capas',
        'center_tooltip': 'Centrar:\nDesplazar para centrar\ntodos los cordones en el\nlienzo',
        'hide_mode_tooltip': 'Modo Ocultar:\nHaga clic para habilitar la\nselección de capas, luego\nclic derecho para\noperaciones de ocultar/\nmostrar por lotes',
        'zoom_in_tooltip': 'Acercar',
        'zoom_out_tooltip': 'Alejar',
        'pan_tooltip': 'Panorámica:\nHaga clic y arrastre para\nmover el lienzo',
        'undo_tooltip': 'Deshacer:\nDeshacer la última acción',
        'redo_tooltip': 'Rehacer:\nRehacer la última acción\ndeshecha',
        'currently_unavailable': 'Actualmente no disponible',
        'layer_cannot_delete_tooltip': 'Esta capa no se puede eliminar (ambos extremos están conectados)',
        'arrow_head_length': 'Longitud de la punta de la flecha',
        'arrow_head_length_tooltip': 'Longitud de la punta de la flecha en píxeles',
        'arrow_head_width': 'Ancho de la punta de la flecha',
        'arrow_head_width_tooltip': 'Ancho de la punta de la flecha en píxeles',
        'arrow_head_stroke_width': 'Grosor del Contorno de la Punta de Flecha',
        'arrow_head_stroke_width_tooltip': 'Grosor del contorno de la punta de la flecha en píxeles',
        'arrow_gap_length': 'Longitud del espacio antes de la flecha',
        'arrow_gap_length_tooltip': 'Espacio entre el extremo del cordón y el inicio de la flecha',
        'arrow_line_length': 'Longitud del cuerpo de la flecha',
        'arrow_line_length_tooltip': 'Longitud del cuerpo de la flecha en píxeles',
        'arrow_line_width': 'Grosor del cuerpo de la flecha',
        'arrow_line_width_tooltip': 'Grosor del cuerpo de la flecha en píxeles',
        'use_default_arrow_color': 'Usar color predeterminado de las flechas',

        # --- END NEW ---
        # Group-related translations
        'group_exists': 'Grupo Existente',
        'group_replace_confirm': 'Ya existe un grupo llamado "{}". ¿Deseas reemplazarlo?',
        # History translations
        'load_selected_history': 'Cargar Seleccionado',
        'clear_all_history': 'Borrar Todo el Historial',
        'confirm_clear_history_title': 'Confirmar Borrado de Historial',
        'confirm_clear_history_text': '¿Estás seguro de que deseas eliminar TODAS las sesiones de historial pasadas? Esto no se puede deshacer.',
        'history_load_error_title': 'Error al Cargar Historial',
        'history_load_error_text': 'No se pudo cargar el estado de historial seleccionado.',
        'history_cleared_title': 'Historial Borrado',
        'history_cleared_text': 'Todas las sesiones de historial pasadas han sido borradas.',
        'no_history_found': 'No se encontraron sesiones de historial pasadas.',
        'history_explanation': 'Selecciona una sesión pasada y haz clic en "Cargar Seleccionado" para restaurarla.\nAdvertencia: Borra deshacer/rehacer actuales.',
        'history_list_tooltip': 'Selecciona una sesión para cargar su estado final',
        'extension_dash_gap_length': 'Longitud del espacio entre el extremo del cordón y el inicio de los guiones',
        'extension_dash_gap_length_tooltip': 'Espacio entre el extremo del cordón y el inicio de los guiones',
        'width_preview_label': 'Total: {total}px | Color: {color}px | Contorno: {stroke}px cada lado',
        'percent_available_color': '% del Espacio de Color Disponible',
        'total_thickness_label': 'Grosor Total (cuadros de cuadrícula):',
        'grid_squares': 'cuadros',
        'color_vs_stroke_label': 'Distribución Color vs Contorno (grosor total fijo):',
        # Button descriptions for settings dialog
        'group_buttons': 'Botones de Grupo',
        'draw_names_desc': 'Dibujar Nombres - Muestra/oculta los nombres de los cordones en el lienzo',
        'lock_layers_desc': 'Bloquear Capas - Activa el modo bloqueo para bloquear/desbloquear cordones de la edición',
        'add_new_strand_desc': 'Nuevo Cordón - Agrega un nuevo cordón a tu diseño',
        'delete_strand_desc': 'Eliminar Cordón - Elimina el cordón seleccionado',
        'deselect_all_desc': 'Deseleccionar Todo - Borra todas las selecciones (o borra todos los bloqueos en modo bloqueo)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Panorámica (✋/✊) - ✋ Haga clic para activar el modo panorámica, ✊ Arrastre el lienzo para moverse por su diseño',
        'zoom_in_desc': 'Acercar (🔍) - Acérquese a su diseño para trabajo detallado',
        'zoom_out_desc': 'Alejar (🔎) - Aléjese para ver el panorama general',
        'center_strands_desc': 'Centrar Cordones (🎯) - Centra todos los cordones en la vista',
        'multi_select_desc': 'Modo Ocultar (🙉/🙈) - 🙉 Haga clic para activar el modo ocultar, 🙈 Seleccione capas luego clic derecho para operaciones de ocultar/mostrar por lotes',
        'refresh_desc': 'Actualizar (🔄) - Actualiza la visualización del panel de capas',
        'reset_states_desc': 'Reiniciar Estados (🏠) - Reinicia todos los estados de las capas al predeterminado',
        # Main window button descriptions
        'attach_mode_desc': 'Modo Conectar - Conecta cordones juntos en sus extremos',
        'move_mode_desc': 'Modo Mover - Mueve cordones y puntos de control en el lienzo',
        'rotate_mode_desc': 'Modo Rotar - Rota los cordones seleccionados',
        'toggle_grid_desc': 'Alternar Cuadrícula - Muestra/oculta la cuadrícula en el lienzo',
        'angle_adjust_desc': 'Modo Ajustar Ángulo - Ajusta finamente los ángulos de las conexiones de cordones',
        'save_desc': 'Guardar - Guarda tu proyecto en un archivo',
        'load_desc': 'Cargar - Carga un proyecto desde un archivo',
        'save_image_desc': 'Guardar como Imagen - Exporta tu diseño como archivo de imagen',
        'select_strand_desc': 'Seleccionar Cordón - Activa el modo selección para seleccionar cordones',
        'mask_mode_desc': 'Modo Máscara - Oculta partes de cordones que pasan por debajo de otros',
        'settings_desc': 'Configuración - Abre el diálogo de configuración',
        'toggle_control_points_desc': 'Alternar Puntos de Control - Muestra/oculta los puntos de control para curvas de bézier',
        'toggle_shadow_desc': 'Alternar Sombra - Muestra/oculta sombras en los cordones',
        'layer_state_desc': 'Estado de Capa - Ver información de depuración sobre capas',
        # Group button descriptions
        'create_group_desc': 'Crear Grupo - Crea un nuevo grupo a partir de cordones seleccionados',
        'group_header_desc': 'Encabezado de Grupo - Haga clic para expandir/contraer grupo. Clic derecho para opciones',
        'rename_group_desc': 'Renombrar Grupo - Cambia el nombre de este grupo',
        'delete_group_desc': 'Eliminar Grupo - Elimina este grupo (los cordones permanecen)',
        'select_group_desc': 'Seleccionar Grupo - Selecciona todos los cordones en este grupo',
        'move_group_desc': 'Mover Grupo - Mueve todos los cordones del grupo juntos',
        'rotate_group_desc': 'Rotar Grupo - Rota todos los cordones del grupo',
        'edit_strand_angles_desc': 'Editar Ángulos de Cordones - Alinea todos los ángulos de los cordones del grupo para que sean paralelos con un solo clic',
        'duplicate_group_desc': 'Duplicar Grupo - Crea una copia de este grupo y sus cordones',
        # About translations
        'about_info': '''
        <h2>Acerca de OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio fue desarrollado por Yonatan Setbon. El software está diseñado para crear cualquier nudo de manera esquemática utilizando capas para cada sección de un cordón y utilizando capas enmascaradas que permiten un efecto "sobre-debajo".
        </p>
        <p style="font-size:15px;">
            Yonatan mantiene un canal de YouTube dedicado a los nudos de lazo llamado <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, donde muchos tutoriales muestran diagramas de nudos. Este software fue creado para facilitar el diseño de cualquier nudo, con el fin de demostrar y explicar cómo realizar tutoriales de nudo complejos.
        </p>
        <p style="font-size:15px;">
            Siéntase libre de contactarme a <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> o seguirme en
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> o
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''' ,
    },
    # New Portuguese Translations
    'pt': {
        # MainWindow translations
        'play_video': 'Reproduzir Vídeo',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Anexar',
        'move_mode': 'Mover',
        'rotate_mode': 'Rotacionar',
        'toggle_grid': 'Grade',
        'angle_adjust_mode': 'Ângulo/Comp.',
        'select_mode': 'Selecionar',
        'mask_mode': 'Máscara',
        'new_strand_mode': 'Novo',
        'save': 'Salvar',
        'load': 'Carregar',
        'save_image': 'Imagem',
        'settings': 'Configurações',
        'light': 'Claro',
        'dark': 'Escuro',
        'english': 'Inglês',
        'french': 'Francês',
        'german': 'Alemão',
        'italian': 'Italiano',
        'spanish': 'Espanhol',
        'portuguese': 'Português',
        'hebrew': 'Hebraico',
        'select_theme': 'Selecionar Tema',
        'default': 'Padrão',
        'light': 'Claro',
        'dark': 'Escuro',
        'layer_state': 'Estado',
        'layer_state_log_title': 'Estado',
        'layer_state_info_title': 'Info',
        'layer_state_info_tooltip': 'Info',
        'close': 'Fechar',
        'toggle_control_points': 'Pontos',
        'toggle_shadow': 'Sombra',
        'shadow_color': 'Cor da Sombra',
        'draw_only_affected_strand': 'Desenhar apenas a mecha afetada ao arrastar',
        'enable_third_control_point': 'Habilitar terceiro ponto de controle no centro',
        'enable_curvature_bias_control': 'Habilitar controles de viés de curvatura',
        'enable_snap_to_grid': 'Habilitar encaixe na grade',
        'show_move_highlights': 'Mostrar indicadores de seleção em modos mover/anexar',
        'use_extended_mask': 'Usar extensão de máscara (superposição mais larga)',
        'use_extended_mask_tooltip': 'Se você quiser usar sombras, ligue; se não quiser sombras, desligue.',
        'use_extended_mask_desc': 'Se você quiser usar sombras, ligue; se não quiser sombras, desligue.',
        'shadow_blur_steps': 'Passos de desfoque de sombra:',
        'shadow_blur_steps_tooltip': 'Número de passos para o efeito de desvanecimento da sombra',
        'shadow_blur_radius': 'Raio de desfoque de sombra:',
        'shadow_blur_radius_tooltip': 'Raio de desfoque da sombra em pixels (faixa: 0.0 - 360.0)',
        'reset_curvature_settings': 'Redefinir configurações de curvatura:',
        'reset': 'Redefinir',
        'reset_curvature_tooltip': 'Redefinir todas as configurações de curvatura para valores padrão',
        'base_fraction': 'Influência (força de tração):',
        'base_fraction_tooltip': 'Força de influência do ponto de controle (1.0=normal, 2.0=forte, 3.0=muito forte)',
        'distance_multiplier': 'Amplificação (amplia curvas):',
        'distance_mult_tooltip': 'Fator de multiplicação de distância (1.0=sem aumento, 2.0=2x, 5.0=5x)',
        'curve_response': 'Forma curva (1=angular, 3=suave):',
        'curve_response_tooltip': 'Tipo de resposta da curva (1.0=linear, 1.5=curva suave, 2.0=quadrática, 3.0=cúbica)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>Explicação das Informações de Estado das Camadas:</b><br>
<br><br>
<b>Ordem:</b> A sequência de camadas (mechas) na tela.<br>
<br>
<b>Conexões:</b> Os relacionamentos entre mechas, indicando quais mechas estão conectadas ou anexadas.<br>
<br>
<b>Grupos:</b> Os grupos de mechas que são manipulados coletivamente.<br>
<br>
<b>Camadas com Máscara:</b> As camadas que têm máscaras aplicadas para efeitos de sobreposição.<br>
<br>
<b>Cores:</b> As cores atribuídas a cada mecha.<br>
<br>
<b>Posições:</b> As posições das mechas na tela.<br>
<br>
<b>Mecha Selecionada:</b> A mecha atualmente selecionada na tela.<br>
<br>
<b>Mecha Mais Recente:</b> A mecha criada mais recentemente.<br>
<br>
<b>Camada Mais Recente:</b> A camada adicionada mais recentemente na tela.
''',
        # SettingsDialog translations
        'general_settings': 'Configurações Gerais',
        'change_language': 'Mudar Idioma',
        'tutorial': 'Tutorial',
        'button_explanations': 'Guia de botões',
        'history': 'Histórico',
        'whats_new': "O que há de novo?",
        'samples': 'Exemplos',
        'samples_header': 'Projetos de exemplo',
        'samples_sub': 'Escolha um exemplo para carregar e aprender. A janela será fechada e o exemplo será carregado.',
            'sample_closed_knot': 'Nó fechado',
            'sample_box_stitch': 'Ponto caixa',
            'sample_overhand_knot': 'Nó simples',
            'sample_three_strand_braid': 'Trança de três mechas',
            'sample_interwoven_double_closed_knot': 'Nó fechado duplo entrelaçado',
        'about': 'Sobre',
        'select_theme': 'Selecionar Tema:',
        'select_language': 'Selecionar Idioma:',
        'ok': 'OK',
        'cancel': 'Cancelar',
        'apply': 'Aplicar',
        'language_settings_info': 'Mudar o idioma da aplicação.',
        'tutorial_info': 'Pressione o botão "reproduzir vídeo" abaixo de cada texto\npara visualizar o tutorial explicando:',
        'button_guide_info': 'Aprenda sobre os diferentes botões e suas funções no OpenStrand Studio.\n\nDica: Você pode clicar nos ícones emoji do painel de camadas para ver suas explicações!',
        'layer_panel_buttons': 'Botões do Painel de Camadas',
        'main_window_buttons': 'Botões da Janela Principal',
        # General Settings descriptions for button guide
        'general_settings_header': 'Configurações Gerais',
        'theme_selection_desc': 'Seleção de Tema - Escolher entre os temas Padrão, Claro ou Escuro',
        'shadow_color_desc': 'Cor da Sombra - Definir a cor usada para as sombras dos fios',
        'shadow_blur_steps_desc': 'Passos de Desfoque de Sombra - Número de iterações de desfoque (maior = sombras mais suaves)',
        'shadow_blur_radius_desc': 'Raio de Desfoque de Sombra - Tamanho do efeito de desfoque (maior = bordas mais suaves)',
        'draw_affected_strand_desc': 'Desenhar Apenas Fio Afetado - Mostra apenas o fio arrastado durante a edição',
        'third_control_point_desc': 'Ativar Terceiro Ponto de Controle - Adiciona um ponto de controle central para curvas complexas',
        'curvature_bias_desc': 'Ativar Controles de Viés de Curvatura - Adiciona pequenos controles triângulo/círculo para refinar a forma',
        'snap_to_grid_desc': 'Ativar Ajuste à Grade - Alinha automaticamente os pontos à grade ao mover',
        'control_influence_full_desc': 'Influência do Ponto de Controle - Define o quanto os pontos de controle puxam a curva (0.25=fraco, 1.0=normal, 3.0=muito forte)',
        'distance_boost_full_desc': 'Amplificação de Distância - Multiplica a força da curva para curvas mais pronunciadas (1.0=normal, 10.0=máximo)',
        'curve_shape_full_desc': 'Forma da Curva - Controla o tipo de curva matemática (1.0=ângulos agudos, 2.0=curvas suaves, 3.0=muito suave)',
        'reset_curvature_full_desc': 'Redefinir Configurações de Curvatura - Restaura Influência, Amplificação e Forma aos padrões',
        'whats_new_info': '''
        <h2>Novidades da versão 1.102</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés posicionados entre o ponto de controle central e os dois pontos de controle finais fornecem ajuste fino de curvatura. Esses controles aparecem como pequenos quadrados com um ícone de triângulo ou círculo dentro, permitindo ajustar independentemente a influência da curva de cada lado em direção ao centro para modelagem mais precisa dos fios.</li>
            <li style="font-size:15px;"><b>Configurações de curvatura avançadas:</b> Três novos parâmetros de curvatura dão controle completo sobre as curvas dos fios:
                <ul style="margin-left: 20px;">
                    <li><b>Influência do ponto de controle:</b> Ajusta a força de atração dos pontos de controle (1.0=normal, até 3.0=muito forte)</li>
                    <li><b>Amplificação de distância:</b> Amplifica as curvas multiplicando o fator de distância (1.0=sem amplificação, até 5.0=amplificação 5x)</li>
                    <li><b>Forma da curva:</b> Controla o tipo de resposta da curva (1.0=acentuado/linear, 3.0=suave/cúbico)</li>
                </ul>
            </li>
            <li style="font-size:15px;"><b>Exibição progressiva de pontos de controle:</b> Ao criar novos fios, apenas o ponto de controle inicial é visível inicialmente. Pontos de controle adicionais (pontos finais, ponto central e controles de viés) aparecem progressivamente quando você começa a mover o fio, reduzindo a desordem visual durante o posicionamento inicial.</li>
            <li style="font-size:15px;"><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento foram corrigidos para melhor qualidade visual e representação mais precisa de sombras em todas as configurações de fios.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio – Versão 1.102</p>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'Painel de Camadas',
        'draw_names': 'Exib. Nomes',
        'lock_layers': 'Bloq. Camad.',
        'add_new_strand': 'Nova Mecha',
        'delete_strand': 'Excl. Mecha',
        'deselect_all': 'Desmar. Tudo',
        'notification_message': 'Notificação',
        'button_color': 'Escolha uma cor de botão diferente (não padrão):',
        'default_strand_color': 'Cor de Mecha Padrão:',
        'default_stroke_color': 'Cor de Contorno:',
        'default_strand_width': 'Largura de Mecha Padrão',
        'default_strand_width_tooltip': 'Clique para definir a largura padrão para novas mechas',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "Mostrar seta completa",
        'hide_full_arrow': "Ocultar seta completa",
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'Ajust. Âng.',
        'angle_label': 'Ângulo:',
        'length_label': 'Comprimento:',
        'create_group': 'Criar Grupo',
        'enter_group_name': 'Digite o nome do grupo:',
        'group_creation_cancelled': 'Nenhuma mecha principal selecionada. Criação do grupo cancelada.',
        'move_group_strands': 'Mover Grupo',
        'rotate_group_strands': 'Rotacionar Grupo',
        'edit_strand_angles': 'Editar Ângulos da Mecha',
        'duplicate_group': 'Duplicar Grupo',
        'rename_group': 'Renomear Grupo',
        'delete_group': 'Excluir Grupo',
        'gif_explanation_1': 'Configurando temas e idioma.',
        'gif_explanation_2': 'Clicar com o botão direito nos botões na área do painel de camadas\nrevela suas descrições.',
        'gif_explanation_3': 'Ativação do modo ocultar para selecionar e ocultar/mostrar camadas\nem lote.',
        'gif_explanation_4': 'Tutorial: Como criar um nó fechado.',
        'gif_placeholder_1': 'Espaço Reservado GIF 1',
        'gif_placeholder_2': 'Espaço Reservado GIF 2',
        'gif_placeholder_3': 'Espaço Reservado GIF 3',
        'gif_placeholder_4': 'Espaço Reservado GIF 4',
        'layer': 'Camada',
        'angle': 'Ângulo:',
        'adjust_1_degree': 'Ajustar (±1°)',
        'fast_adjust': 'Ajuste Rápido',
        'end_x': 'Fim X',
        'end_y': 'Fim Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'Anexável',
        'X_angle': 'Ângulo X:',
        'snap_to_grid': 'Ajustar à grade',
        'precise_angle': 'Ângulo preciso:',
        'select_main_strands': 'Selecionar Mechas Principais',
        'select_main_strands_to_include_in_the_group': 'Selecionar mechas principais para incluir no grupo:',
        # New translation keys for Layer State Log
        'current_layer_state': 'Estado Atual da Camada',
        'order': 'Ordem',
        'connections': 'Conexões',
        'groups': 'Grupos',
        'masked_layers': 'Camadas com Máscara',
        'colors': 'Cores',
        'positions': 'Posições',
        'selected_strand': 'Mecha Selecionada',
        'newest_strand': 'Mecha Mais Recente',
        'newest_layer': 'Camada Mais Recente',
        'x_movement': 'Movimento X',
        'y_movement': 'Movimento Y',
        'move_group': 'Mover Grupo',
        'grid_movement': 'Movimento Grade',
        'x_grid_steps': 'Passos Grade X',
        'y_grid_steps': 'Passos Grade Y',
        'apply': 'Aplicar',
        'toggle_shadow': 'Sombra',
        'mask_edit_mode_message': '             MODO EDIÇÃO DE MÁSCARA -\n              Pressione ESC para sair',
        'mask_edit_mode_exited': 'Modo de edição de máscara encerrado',
        'edit_mask': 'Editar Máscara',
        'reset_mask': 'Redefinir Máscara',
        'transparent_stroke': 'Borda Inicial Transparente',
        'transparent_closing_knot_side': 'Lado Transparente do Nó Fechado',
        'restore_default_closing_knot_stroke': 'Restaurar Borda do Nó Fechado Padrão',
        'restore_default_stroke': 'Restaurar Traço Padrão',
        'change_color': 'Mudar cor',
        'change_stroke_color': 'Mudar cor do traço',
        'change_width': 'Mudar largura',
        # --- NEW ---
        'hide_layer': 'Ocultar Camada',
        'show_layer': 'Mostrar Camada',
        'hide_selected_layers': 'Ocultar Camadas Selecionadas',
        'show_selected_layers': 'Mostrar Camadas Selecionadas',
        'enable_shadow_only_selected': 'Só Sombra Selecionadas',
        'disable_shadow_only_selected': 'Mostrar Camadas Completas (Desativar Apenas Sombra)',
        'hide_start_line': 'Ocultar Linha Início',
        'show_start_line': 'Mostrar Linha Início',
        'hide_end_line': 'Ocultar Linha Fim',
        'show_end_line': 'Mostrar Linha Fim',
        'hide_start_circle': 'Ocultar Círculo Início',
        'show_start_circle': 'Mostrar Círculo Início',
        'hide_end_circle': 'Ocultar Círculo Fim',
        'show_end_circle': 'Mostrar Círculo Fim',
        'close_the_knot': 'Fechar o Nó',
        'hide_start_arrow': 'Ocultar Flecha Início',
        'show_start_arrow': 'Mostrar Flecha Início',
        'hide_end_arrow': 'Ocultar Flecha Fim',
        'show_end_arrow': 'Mostrar Flecha Fim',
        'hide_start_extension': 'Ocultar Travessão Início',
        'show_start_extension': 'Mostrar Travessão Início',
        'hide_end_extension': 'Ocultar Travessão Fim',
        'show_end_extension': 'Mostrar Travessão Fim',
        'line': 'Linha',
        'arrow': 'Flecha',
        'extension': 'Travessão',
        'circle': 'Círculo',
        'shadow_only': 'Apenas Sombra',
        # Layer panel extension and arrow settings translations
        'extension_length': 'Comprimento da extensão',
        'extension_length_tooltip': 'Comprimento da linha de extensão',
        'extension_dash_count': 'Número de traços de extensão',
        'extension_dash_count_tooltip': 'Número de traços na linha de extensão',
        'extension_dash_width': 'Espessura do traço de extensão',
        'extension_dash_width_tooltip': 'Espessura dos traços de extensão',
        'extension_dash_gap_length': 'Comprimento do espaço entre a extremidade da mecha e o início dos traços',
        'extension_dash_gap_length_tooltip': 'Espaço entre a extremidade da mecha e o início dos traços',
        'exit_lock_mode': 'Sair',
        'clear_all_locks': 'Limpar',
        'select_layers_to_lock': 'Selecionar camadas para bloquear/desbloquear',
        'exited_lock_mode': 'Saiu do modo bloqueio',
        # Button tooltips
        'reset_tooltip': 'Redefinir:\nManter apenas o estado\natual como primeiro estado',
        'refresh_tooltip': 'Atualizar:\nRecarregar camadas',
        'center_tooltip': 'Centralizar:\nMover para centralizar\ntodas as mechas na tela',
        'hide_mode_tooltip': 'Modo Ocultar:\nClique para ativar a\nseleção de camadas, depois\nclique direito para\noperações de ocultar/\nmostrar em lote',
        'zoom_in_tooltip': 'Aumentar zoom',
        'zoom_out_tooltip': 'Diminuir zoom',
        'pan_tooltip': 'Panorâmica:\nClique e arraste para\nmover a tela',
        'undo_tooltip': 'Desfazer:\nDesfazer a última ação',
        'redo_tooltip': 'Refazer:\nRefazer a última ação\ndesfeita',
        'currently_unavailable': 'Atualmente indisponível',
        'layer_cannot_delete_tooltip': 'Esta camada não pode ser excluída (ambas as extremidades estão conectadas)',
        'arrow_head_length': 'Comprimento da ponta da flecha',
        'arrow_head_length_tooltip': 'Comprimento da ponta da flecha em pixels',
        'arrow_head_width': 'Largura da ponta da flecha',
        'arrow_head_width_tooltip': 'Largura da ponta da flecha em pixels',
        'arrow_head_stroke_width': 'Espessura do Contorno da Ponta da Flecha',
        'arrow_head_stroke_width_tooltip': 'Espessura do contorno da ponta da flecha em pixels',
        'arrow_gap_length': 'Comprimento do espaço antes da flecha',
        'arrow_gap_length_tooltip': 'Espaço entre a extremidade da mecha e o início da flecha',
        'arrow_line_length': 'Comprimento do corpo da flecha',
        'arrow_line_length_tooltip': 'Comprimento do corpo da flecha em pixels',
        'arrow_line_width': 'Espessura do corpo da flecha',
        'arrow_line_width_tooltip': 'Espessura do corpo da flecha em pixels',
        'use_default_arrow_color': 'Usar cor padrão das flechas',
        # --- END NEW ---
        # Group-related translations
        'group_exists': 'Grupo Existente',
        'group_replace_confirm': 'Um grupo chamado "{}" já existe. Deseja substituí-lo?',
        # History translations
        'load_selected_history': 'Carregar Selecionado',
        'clear_all_history': 'Limpar Todo o Histórico',
        'confirm_clear_history_title': 'Confirmar Limpeza do Histórico',
        'confirm_clear_history_text': 'Tem certeza de que deseja excluir TODAS as sessões de histórico passadas? Isso não pode ser desfeito.',
        'history_load_error_title': 'Erro ao Carregar Histórico',
        'history_load_error_text': 'Não foi possível carregar o estado do histórico selecionado.',
        'history_cleared_title': 'Histórico Limpo',
        'history_cleared_text': 'Todas as sessões de histórico passadas foram limpas.',
        'no_history_found': 'Nenhuma sessão de histórico passada encontrada.',
        'history_explanation': 'Selecione uma sessão passada e clique em "Carregar Selecionado" para restaurar seu estado final.\nAviso: Carregar histórico limpará suas etapas atuais de desfazer/refazer.',
        'history_list_tooltip': 'Selecione uma sessão para carregar seu estado final',
        'extension_dash_gap_length': 'Comprimento do espaço entre a extremidade da mecha e o início dos traços',
        'extension_dash_gap_length_tooltip': 'Espaço entre a extremidade da mecha e o início dos traços',
        'width_preview_label': 'Total: {total}px | Cor: {color}px | Contorno: {stroke}px de cada lado',
        'percent_available_color': '% do Espaço de Cor Disponível',
        'total_thickness_label': 'Espessura Total (quadrados da grade):',
        'grid_squares': 'quadrados',
        'color_vs_stroke_label': 'Distribuição Cor vs Contorno (espessura total fixa):',
        # Button descriptions for settings dialog
        'group_buttons': 'Botões de Grupo',
        'draw_names_desc': 'Desenhar Nomes - Mostra/oculta os nomes das mechas na tela',
        'lock_layers_desc': 'Bloquear Camadas - Ativa o modo de bloqueio para bloquear/desbloquear mechas da edição',
        'add_new_strand_desc': 'Nova Mecha - Adiciona uma nova mecha ao seu design',
        'delete_strand_desc': 'Excluir Mecha - Remove a mecha selecionada',
        'deselect_all_desc': 'Desselecionar Tudo - Limpa todas as seleções (ou limpa todos os bloqueios no modo de bloqueio)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'Panorâmica (✋/✊) - ✋ Clique para ativar o modo panorâmica, ✊ Arraste a tela para se mover pelo seu design',
        'zoom_in_desc': 'Aproximar (🔍) - Aproxime-se do seu design para trabalho detalhado',
        'zoom_out_desc': 'Afastar (🔎) - Afaste-se para ver o quadro geral',
        'center_strands_desc': 'Centralizar Mechas (🎯) - Centraliza todas as mechas na vista',
        'multi_select_desc': 'Modo Ocultar (🙉/🙈) - 🙉 Clique para ativar o modo ocultar, 🙈 Selecione camadas então clique direito para operações de ocultar/mostrar em lote',
        'refresh_desc': 'Atualizar (🔄) - Atualiza a exibição do painel de camadas',
        'reset_states_desc': 'Redefinir Estados (🏠) - Redefine todos os estados das camadas para o padrão',
        # Main window button descriptions
        'attach_mode_desc': 'Modo Anexar - Conecta mechas juntas em suas extremidades',
        'move_mode_desc': 'Modo Mover - Move mechas e pontos de controle na tela',
        'rotate_mode_desc': 'Modo Girar - Gira as mechas selecionadas',
        'toggle_grid_desc': 'Alternar Grade - Mostra/oculta a grade na tela',
        'angle_adjust_desc': 'Modo Ajustar Ângulo - Ajusta finamente os ângulos das conexões das mechas',
        'save_desc': 'Salvar - Salva seu projeto em um arquivo',
        'load_desc': 'Carregar - Carrega um projeto de um arquivo',
        'save_image_desc': 'Salvar como Imagem - Exporta seu design como arquivo de imagem',
        'select_strand_desc': 'Selecionar Mecha - Ativa o modo de seleção para selecionar mechas',
        'mask_mode_desc': 'Modo Máscara - Oculta partes de mechas que passam por baixo de outras',
        'settings_desc': 'Configurações - Abre o diálogo de configurações',
        'toggle_control_points_desc': 'Alternar Pontos de Controle - Mostra/oculta os pontos de controle para curvas de bézier',
        'toggle_shadow_desc': 'Alternar Sombra - Mostra/oculta sombras nas mechas',
        'layer_state_desc': 'Estado da Camada - Ver informações de depuração sobre camadas',
        # Group button descriptions
        'create_group_desc': 'Criar Grupo - Cria um novo grupo a partir de mechas selecionadas',
        'group_header_desc': 'Cabeçalho do Grupo - Clique para expandir/recolher grupo. Clique direito para opções',
        'rename_group_desc': 'Renomear Grupo - Altera o nome deste grupo',
        'delete_group_desc': 'Excluir Grupo - Remove este grupo (as mechas permanecem)',
        'select_group_desc': 'Selecionar Grupo - Seleciona todas as mechas neste grupo',
        'move_group_desc': 'Mover Grupo - Move todas as mechas do grupo juntas',
        'rotate_group_desc': 'Rotacionar Grupo - Rotaciona todas as mechas do grupo',
        'edit_strand_angles_desc': 'Editar Ângulos das Mechas - Alinha todos os ângulos das mechas do grupo para ficarem paralelos com um único clique',
        'duplicate_group_desc': 'Duplicar Grupo - Cria uma cópia deste grupo e suas mechas',
        # About translations
        'about_info': '''
        <h2>Sobre OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio foi desenvolvido por Yonatan Setbon. O software foi projetado para criar qualquer nó de forma esquemática usando camadas para cada seção de um fio e incorporando camadas mascaradas que permitem um efeito "sobre-sobre".
        </p>
        <p style="font-size:15px;">
            Yonatan mantém um canal do YouTube dedicado a cordões de segurança chamado <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, onde vários tutoriais apresentam diagramas de nós. Este software foi criado para facilitar o design de qualquer nó, com o objetivo de demonstrar e explicar como realizar tutoriais de nó complexo.
        </p>
        <p style="font-size:15px;">
            Sinta-se à vontade para me contatar em <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> ou me seguir no
            <a href="https://www.instagram.com/ysetbon/">Instagram</a> ou
            <a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''' ,
        'width_preview_label': 'Total : {total}px | Couleur : {color}px | Contour : {stroke}px de chaque côté',
        'percent_available_color': '% de l\'espace couleur disponible',
        'total_thickness_label': 'Épaisseur totale (cases de grille):',
        'grid_squares': 'cases',
        'color_vs_stroke_label': 'Répartition Couleur / Contour (épaisseur totale fixe):',
    },
    # New Hebrew Translations (RTL language)
    'he': {
        # MainWindow translations
        'play_video': 'הפעל וידאו',
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'חיבור',
        'move_mode': 'הזזה',
        'rotate_mode': 'סיבוב',
        'toggle_grid': 'רשת',
        'angle_adjust_mode': 'זווית/אורך',
        'select_mode': 'בחירה',
        'mask_mode': 'מסכה',
        'new_strand_mode': 'חדש',
        'save': 'שמירה',
        'load': 'טעינה',
        'save_image': 'תמונה',
        'settings': 'הגדרות',
        'light': 'בהיר',
        'dark': 'כהה',
        'english': 'אנגלית',
        'french': 'צרפתית',
        'german': 'גרמנית',
        'italian': 'איטלקית',
        'spanish': 'ספרדית',
        'portuguese': 'פורטוגזית',
        'hebrew': 'עברית',
        'select_theme': 'בחר ערכת נושא',
        'default': 'ברירת מחדל',
        'light': 'בהיר',
        'dark': 'כהה',
        'layer_state': 'מצב',
        'layer_state_log_title': 'מצב',
        'layer_state_info_title': 'מידע',
        'layer_state_info_tooltip': 'מידע',
        'close': 'סגור',
        'toggle_control_points': 'נקודות',
        'toggle_shadow': 'צל',
        'shadow_color': 'צבע צל',
        'draw_only_affected_strand': 'צייר רק את החוט המושפע בעת גרירה',
        'enable_third_control_point': 'הפעל נקודת בקרה שלישית במרכז',
        'enable_curvature_bias_control': 'הפעל בקרות הטיית עקמומיות',
        'enable_snap_to_grid': 'הפעל הצמדה לרשת',
        'show_move_highlights': 'הצג מחווני בחירה במצבי הזזה/חיבור',
        'use_extended_mask': 'השימוש במסכה המורחבת (הסובב מרחב יותר)',
        'use_extended_mask_tooltip': 'אם אתה רוצה להשתמש בצללים, הפעל; אם אתה לא רוצה צללים, כבה.',
        'use_extended_mask_desc': 'אם אתה רוצה להשתמש בצללים, הפעל; אם אתה לא רוצה צללים, כבה.',
        'shadow_blur_steps': 'צעדי טשטוש צל:',
        'shadow_blur_steps_tooltip': 'מספר צעדים לאפקט דהייה של צל',
        'shadow_blur_radius': 'רדיוס טשטוש צל:',
        'shadow_blur_radius_tooltip': 'רדיוס טשטוש צל בפיקסלים (טווח: 0.0 - 360.0)',
        'reset_curvature_settings': 'איפוס הגדרות עקמומיות:',
        'reset': 'איפוס',
        'reset_curvature_tooltip': 'איפוס כל הגדרות העקמומיות לערכי ברירת המחדל',
        'base_fraction': 'השפעה (עוצמת משיכה):',
        'base_fraction_tooltip': 'עוצמת השפעת נקודת בקרה (1.0=רגיל, 2.0=חזק, 3.0=חזק מאוד)',
        'distance_multiplier': 'הגברה (מגדיל עקומות):',
        'distance_mult_tooltip': 'מקדם הכפלת מרחק (1.0=ללא הגברה, 2.0=פי 2, 5.0=פי 5)',
        'curve_response': 'צורת עקומה (1=חד, 3=חלק):',
        'curve_response_tooltip': 'סוג תגובת עקומה (1.0=לינארי, 1.5=עקומה עדינה, 2.0=ריבועי, 3.0=קובי)',
        # Layer State Info Text
        'layer_state_info_text': '''
<b>הסבר על מידע מצב השכבות:</b><br>
<br><br>
<b>סדר:</b> רצף השכבות (חוטים) בקנבס.<br>
<br>
<b>חיבורים:</b> היחסים בין החוטים, המציינים אילו חוטים מחוברים או מצורפים.<br>
<br>
<b>קבוצות:</b> קבוצות החוטים שמטופלות באופן קולקטיבי.<br>
<br>
<b>שכבות עם מסכות:</b> השכבות שיש להן מיסוך מוחל לאפקטים של מעל-מתחת.<br>
<br>
<b>צבעים:</b> הצבעים המוקצים לכל חוט.<br>
<br>
<b>מיקומים:</b> המיקומים של החוטים בקנבס.<br>
<br>
<b>חוט נבחר:</b> החוט הנבחר כעת בקנבס.<br>
<br>
<b>החוט החדש ביותר:</b> החוט שנוצר לאחרונה.<br>
<br>
<b>השכבה החדשה ביותר:</b> השכבה שנוספה לאחרונה בקנבס.
''',
        # SettingsDialog translations
        'general_settings': 'הגדרות כלליות',
        'change_language': 'שינוי שפה',
        'tutorial': 'מדריך',
        'button_explanations': 'מדריך כפתורים',
        'history': 'היסטוריה',
        'whats_new': "?מה חדש",
        'samples': 'דוגמאות',
        'samples_header': 'פרויקטים לדוגמה',
        'samples_sub': 'בחר דוגמה לטעינה כדי ללמוד ממנה. הדיאלוג ייסגר והדוגמה תיטען.',
            'sample_closed_knot': 'קשר סגור',
            'sample_box_stitch': 'תפר קופסה',
            'sample_overhand_knot': 'קשר רגיל',
            'sample_three_strand_braid': 'צמה משלושה חוטים',
            'sample_interwoven_double_closed_knot': 'קשר סגור כפול משולב',
        'about': ' אודות OpenStrand Studio',
        'select_theme': 'בחר ערכת נושא:    ',
        'select_language': 'בחר שפה:',
        'ok': 'אישור',
        'cancel': 'ביטול',
        'apply': 'החל',
        'language_settings_info': 'שנה את שפת האפליקציה.',
        'tutorial_info': 'לחץ על כפתור "הפעל וידאו" מתחת לכל טקסט\nכדי לראות את המדריך המסביר:',
        'button_guide_info': 'למד על הכפתורים השונים והפונקציות שלהם ב-OpenStrand Studio.\n\nטיפ: אתה יכול ללחוץ על אייקוני האימוג׳י בפאנל השכבות כדי לראות הסברים!',
        'layer_panel_buttons': 'כפתורי פאנל השכבות',
        'main_window_buttons': 'כפתורי החלון הראשי',
        # General Settings descriptions for button guide
        'general_settings_header': 'הגדרות כלליות',
        'theme_selection_desc': 'בחירת ערכת נושא - בחר בין ברירת מחדל, בהיר או כהה',
        'shadow_color_desc': 'צבע צל - הגדר את הצבע המשמש לצללי חוטים',
        'shadow_blur_steps_desc': 'שלבי טשטוש צל - מספר חזרות טשטוש (יותר = צללים חלקים יותר)',
        'shadow_blur_radius_desc': 'רדיוס טשטוש צל - גודל אפקט הטשטוש (יותר = קצוות רכים יותר)',
        'draw_affected_strand_desc': 'צייר רק חוט מושפע - מציג רק את החוט הנגרר בעת עריכה',
        'third_control_point_desc': 'הפעל נקודת בקרה שלישית - מוסיף נקודת בקרה מרכזית לעקומות מורכבות',
        'curvature_bias_desc': 'הפעל בקרות הטיית עקמומיות - מוסיף בקרות משולש/עיגול קטנות לכיוונון עדין',
        'snap_to_grid_desc': 'הפעל הצמדה לרשת - מיישר אוטומטית נקודות לרשת בעת הזזה',
        'control_influence_full_desc': 'השפעת נקודת בקרה - קובע כמה חזק נקודות הבקרה מושכות את העקומה (0.25=חלש, 1.0=רגיל, 3.0=חזק מאוד)',
        'distance_boost_full_desc': 'הגברת מרחק - מכפיל את עוצמת העקומה לעקומות בולטות יותר (1.0=רגיל, 10.0=מקסימום)',
        'curve_shape_full_desc': 'צורת עקומה - שולט בסוג העקומה המתמטי (1.0=זוויות חדות, 2.0=עקומות חלקות, 3.0=חלק מאוד)',
        'reset_curvature_full_desc': 'אפס הגדרות עקמומיות - מחזיר השפעה, הגברה וצורה לברירת המחדל',
        'whats_new_info': '''
        <div dir="rtl" style="text-align: right;">
        <b>מה חדש בגרסה 1.101</b><br><br>
        • <b>ניהול שכבות משופר:</b> מבנה StateLayerManager משופר לניהול טוב יותר של חיבורי קשרים ויחסים בין חוטים, המספק פעולות שכבה אמינות יותר וביצועים משופרים.<br>
        • <b>שכפול קבוצה:</b> עכשיו אפשר לשכפל קבוצות שלמות עם כל החוטים שלהן על ידי לחיצה ימנית על כותרת הקבוצה ובחירת "שכפל קבוצה". הקבוצה המשוכפלת שומרת על כל המאפיינים של החוטים ויוצרת אוטומטית שמות שכבה ייחודיים.<br>
        • <b>מצב הסתרה:</b> מצב הסתרה חדש נגיש דרך כפתור הקוף (🙉/🙈) מאפשר להסתיר במהירות מספר שכבות בבת אחת. לחץ על הכפתור כדי להיכנס למצב הסתרה, ואז לחץ על שכבות כדי להסתיר אותן. צא ממצב הסתרה כדי להחיל את השינויים.<br>
        • <b>מרכוז תצוגה:</b> מרכז מיידית את כל החוטים בתצוגה שלך עם כפתור המטרה החדש (🎯). זה מכוונן אוטומטית את מיקום הקנבס כדי להציג את כל העבודה שלך במרכז המסך.<br>
        • <b>סגירת קשר מהירה:</b> לחץ לחיצה ימנית על כל חוט או חוט מחובר עם קצה חופשי כדי לסגור במהירות את הקשר. המערכת מוצאת ומתחברת אוטומטית לחוט התואם הקרוב ביותר עם קצה חופשי.<br>
        • <b>שפה חדשה - גרמנית (🇩🇪):</b> עכשיו אפשר לבחור גרמנית דרך הגדרות → שינוי שפה.<br>
        • <b>קטגוריית דוגמאות חדשה:</b> אפשר לצפות בפרויקטים לדוגמה שמוכנים לטעינה דרך הגדרות → דוגמאות. בחר דוגמה כדי ללמוד; תיבת הדו־שיח תיסגר והדוגמה תיטען.<br><br>
        © 2025 OpenStrand Studio - גרסה 1.102
        </div>
        ''',


        # LayerPanel translations
        'layer_panel_title': 'חלונית השכבות',
        'draw_names': 'צייר שמות',
        'lock_layers': 'נעל שכבות',
        'add_new_strand': 'חוט חדש',
        'delete_strand': 'מחק חוט',
        'deselect_all': 'בטל בחירה',
        'notification_message': 'התראה',
        'button_color': 'בחר צבע כפתור שונה (לא ברירת מחדל):',
        'default_strand_color': 'צבע חוט ברירת מחדל:',
        'default_stroke_color': 'צבע מתאר:',
        'default_strand_width': 'רוחב חוט ברירת מחדל',
        'default_strand_width_tooltip': 'לחץ כדי להגדיר את הרוחב ברירת המחדל עבור חוטים חדשים',
        # --- NEW: Full Arrow translations ---
        'show_full_arrow': "הצג חץ מלא",
        'hide_full_arrow': "הסתר חץ מלא",
        # --- END NEW ---
        # Additional texts
        'adjust_angle_and_length': 'התאם זווית ואורך',
        'angle_label': 'זווית:',
        'length_label': 'אורך:',
        'create_group': 'צור קבוצה',
        'enter_group_name': 'הזן שם קבוצה:',
        'group_creation_cancelled': 'לא נבחרו חוטים עיקריים. יצירת הקבוצה בוטלה.',
        'move_group_strands': 'הזז קבוצה',
        'rotate_group_strands': 'סובב קבוצה',
        'edit_strand_angles': 'ערוך זוויות חוט',
        'duplicate_group': 'שכפל קבוצה',
        'rename_group': 'שנה שם קבוצה',
        'delete_group': 'מחק קבוצה',
        'gif_explanation_1': 'הגדרת ערכות נושא ושפה.',
        'gif_explanation_2': 'לחיצה ימנית על כפתורים באזור פאנל השכבות חושפת את התיאורים שלהם.',
        'gif_explanation_3': 'הפעלת מצב הסתרה לבחירה והסתרה/הצגה קבוצתית של שכבות.',
        'gif_explanation_4': 'מדריך: איך ליצור קשר סגור.',
        
        'gif_placeholder_1': 'מיקום GIF 1',
        'gif_placeholder_2': 'מיקום GIF 2',
        'gif_placeholder_3': 'מיקום GIF 3',
        'gif_placeholder_4': 'מיקום GIF 4',
        'layer': 'שכבה',
        'angle': 'זווית:',
        'adjust_1_degree': 'התאם (±1°)',
        'fast_adjust': 'התאמה מהירה',
        'end_x': 'סוף X',
        'end_y': 'סוף Y',
        'x': 'X',
        'x_plus_180': '180+X',
        'attachable': 'ניתן לחיבור',
        'X_angle': 'זווית X:',
        'snap_to_grid': 'הצמד לרשת',
        'precise_angle': 'זווית מדויקת:',
        'select_main_strands': 'בחר חוטים עיקריים',
        'select_main_strands_to_include_in_the_group': 'בחר חוטים עיקריים לכלול בקבוצה:',
        # New translation keys for Layer State Log
        'current_layer_state': 'מצב שכבה נוכחי',
        'order': 'סדר',
        'connections': 'חיבורים',
        'groups': 'קבוצות',
        'masked_layers': 'שכבות עם מסכה',
        'colors': 'צבעים',
        'positions': 'מיקומים',
        'selected_strand': 'חוט נבחר',
        'newest_strand': 'חוט חדש ביותר',
        'newest_layer': 'שכבה חדשה ביותר',
        'x_movement': 'תנועת X',
        'y_movement': 'תנועת Y',
        'move_group': 'הזז קבוצה',
        'grid_movement': 'תנועת רשת',
        'x_grid_steps': 'צעדי רשת X',
        'y_grid_steps': 'צעדי רשת Y',
        'apply': 'החל',
        'toggle_shadow': 'צל',
        'mask_edit_mode_message': '             מצב עריכת מסכה -\n              לחץ ESC ליציאה',
        'mask_edit_mode_exited': 'מצב עריכת מסכה הסתיים',
        'edit_mask': 'ערוך מסכה',
        'reset_mask': 'אפס מסכה',
        'transparent_stroke': 'קצה התחלתי שקוף',
        'transparent_closing_knot_side': 'צד שקוף של קשר סגור',
        'restore_default_closing_knot_stroke': 'שחזר קו קשר סגור ברירת מחדל',
        'restore_default_stroke': 'שחזר קו ברירת מחדל',
        'change_color': 'שנה צבע',
        'change_stroke_color': 'שנה צבע קו',
        'change_width': 'שנה רוחב',
        # Layer panel extension and arrow settings translations
        'extension_length': 'אורך הרחבה',
        'extension_length_tooltip': 'אורך קווי ההרחבה',
        'extension_dash_count': 'מספר המקפים',
        'extension_dash_count_tooltip': 'מספר המקפים בקו ההרחבה',
        'extension_dash_width': 'עובי מקף ההרחבה',
        'extension_dash_width_tooltip': 'עובי קטעי קו ההרחבה',
        'extension_dash_gap_length': 'אורך הרווח בין קצה החוט לתחילת המקפים',
        'extension_dash_gap_length_tooltip': 'מרווח בין החוט לתחילת המקפים',
        'exit_lock_mode': 'יציאה',
        'clear_all_locks': 'נקה',
        'select_layers_to_lock': 'בחר שכבות לנעילה/שחרור',
        'exited_lock_mode': 'יצא ממצב נעילה',
        # Button tooltips
        'reset_tooltip': 'איפוס:\nשמור רק את המצב\nהנוכחי כמצב ראשון',
        'refresh_tooltip': 'רענון:\nטען מחדש שכבות',
        'center_tooltip': 'מרכז:\nהזז למרכז כל החוטים\nבקנבס',
        'hide_mode_tooltip': 'מצב הסתרה:\nלחץ להפעלת בחירת\nשכבות, ואז לחץ ימני\nלפעולות הסתרה/הצגה\nקבוצתיות',
        'zoom_in_tooltip': 'הגדל',
        'zoom_out_tooltip': 'הקטן',
        'pan_tooltip': 'גרירה:\nלחץ וגרור להזזת\nהקנבס',
        'undo_tooltip': 'ביטול:\nבטל את הפעולה האחרונה',
        'redo_tooltip': 'חזרה:\nחזור על הפעולה\nהאחרונה שבוטלה',
        'currently_unavailable': 'לא זמין כרגע',
        'layer_cannot_delete_tooltip': 'שכבה זו לא ניתנת למחיקה (שני הקצוות מחוברים)',
        'arrow_head_length': 'אורך ראש החץ',
        'arrow_head_length_tooltip': 'אורך ראש החץ בפיקסלים',
        'arrow_head_width': 'רוחב ראש החץ',
        'arrow_head_width_tooltip': 'רוחב ראש החץ בפיקסלים',
        'arrow_head_stroke_width': 'עובי מתאר ראש החץ',
        'arrow_head_stroke_width_tooltip': 'עובי מתאר ראש החץ בפיקסלים',
        'arrow_gap_length': 'אורך הרווח לפני החץ',
        'arrow_gap_length_tooltip': 'מרווח בין קצה החוט לתחילת החץ',
        'arrow_line_length': 'אורך גוף החץ',
        'arrow_line_length_tooltip': 'אורך גוף החץ בפיקסלים',
        'arrow_line_width': 'עובי גוף החץ',
        'arrow_line_width_tooltip': 'עובי גוף החץ בפיקסלים',
        'use_default_arrow_color': 'השתמש בצבע ברירת המחדל של החצים',        
        # --- NEW ---
        'hide_layer': 'הסתר שכבה',
        'show_layer': 'הצג שכבה',
        'hide_selected_layers': 'הסתר שכבות נבחרות',
        'show_selected_layers': 'הצג שכבות נבחרות',
        'enable_shadow_only_selected': 'צל לנבחרו בלבד',
        'disable_shadow_only_selected': 'הצג שכבות מלאות (בטל צל בלבד)',
        'hide_start_line': 'הסתר קו התחלה',
        'show_start_line': 'הצג קו התחלה',
        'hide_end_line': 'הסתר קו סיום',
        'show_end_line': 'הצג קו סיום',
        'hide_start_circle': 'הסתר עיגול התחלתי',
        'show_start_circle': 'הצג עיגול התחלתי',
        'hide_end_circle': 'הסתר עיגול סופי',
        'show_end_circle': 'הצג עיגול סופי',
        'close_the_knot': 'סגור את הקשר',
        'hide_start_arrow': 'הסתר חץ התחלתי',
        'show_start_arrow': 'הצג חץ התחלתי',
        'hide_end_arrow': 'הסתר חץ סופי',
        'show_end_arrow': 'הצג חץ סופי',
        'hide_start_extension': 'הסתר מקף התחלתי',
        'show_start_extension': 'הצג מקף התחלתי',
        'hide_end_extension': 'הסתר מקף סופי',
        'show_end_extension': 'הצג מקף סופי',
        'shadow_only': 'צל בלבד',
        'line': 'קו',
        'arrow': 'חץ',
        'extension': 'מקף',
        'circle': 'עיגול',
        # --- END NEW ---
        # Group-related translations
        'group_exists': 'קבוצה קיימת',
        'group_replace_confirm': 'קבוצה בשם "{}" כבר קיימת. האם ברצונך להחליף אותה?',
        # History translations
        'load_selected_history': 'טען נבחר',
        'clear_all_history': 'נקה את כל ההיסטוריה',
        'confirm_clear_history_title': 'אשר ניקוי היסטוריה',
        'confirm_clear_history_text': 'האם אתה בטוח שברצונך למחוק את כל הפעלות ההיסטוריה הקודמות? לא ניתן לבטל פעולה זו.',
        'history_load_error_title': 'שגיאת טעינת היסטוריה',
        'history_load_error_text': 'לא ניתן לטעון את מצב ההיסטוריה שנבחר.',
        'history_cleared_title': 'היסטוריה נוקתה',
        'history_cleared_text': 'כל הפעלות ההיסטוריה הקודמות נוקו.',
        'no_history_found': 'לא נמצאו הפעלות היסטוריה קודמות.',
        'history_explanation': ' בחר הפעלה קודמת ולחץ "טען נבחר" כדי לשחזר את המצב הסופי שלה.\n' +
            'אזהרה: טעינת היסטוריה תנקה את שלבי הביטול/שחזור הנוכחיים שלך.',
        'history_list_tooltip': 'בחר הפעלה לטעינת המצב הסופי שלה',
        # About translations
        'about': 'אודות',
        'about_info': '''
        <h2>אודות OpenStrand Studio</h2>
        <p style="font-size:15px;">
            OpenStrand Studio פותחה על ידי יהונתן סטבון. התוכנה מיועדת ליצירת כל קשר באופן סכמטי על ידי שימוש בשכבות לכל קטע של חוט ושילוב שכבות עם מסכות המאפשרות אפקט "מעל-מתחת".
        </p>
        <p style="font-size:15px;">
            יהונתן מפעיל ערוץ YouTube ייעודי לרצועות בשם <b><a href="https://www.youtube.com/@1anya7d">LanYarD</a></b>, בו מדריכים רבים מציגים דיאגרמות של קשרים. תוכנה זו נוצרה כדי להקל על עיצוב כל קשר, במטרה להדגים ולהסביר כיצד להכין מדריכים מורכבים הכוללים קשירת קשרים.
        </p>
        <p style="font-size:15px;">
            אתם מוזמנים לפנות אליי בכתובת <a href="mailto:ysetbon@gmail.com">ysetbon@gmail.com</a> או להתחבר איתי ב־<a href="https://www.instagram.com/ysetbon/">Instagram</a> או ב־<a href="https://www.linkedin.com/in/yonatan-setbon-4a980986/">LinkedIn</a>.
        </p>
        <p style="font-size:13px;">
            © 2025 OpenStrand Studio
        </p>
        ''',
        # Button descriptions for settings dialog
        'group_buttons': 'כפתורי קבוצה',
        'draw_names_desc': 'הצג שמות - מציג/מסתיר שמות חוטים על הקנווס',
        'lock_layers_desc': 'נעל שכבות - מפעיל מצב נעילה לנעילת/שחרור חוטים מעריכה',
        'add_new_strand_desc': 'חוט חדש - מוסיף חוט חדש לעיצוב שלך',
        'delete_strand_desc': 'מחק חוט - מסיר את החוט הנבחר',
        'deselect_all_desc': 'בטל בחירה - מוחק את כל הבחירות (או מוחק את כל הנעילות במצב נעילה)',
        # Layer panel emoji icon descriptions
        'pan_desc': 'גרירה (✋/✊) - ✋ לחץ להפעלת מצב גרירה, ✊ גרור את הקנווס להזזה בעיצוב שלך',
        'zoom_in_desc': 'הגדל (🔍) - הגדל את העיצוב שלך לעבודה מפורטת',
        'zoom_out_desc': 'הקטן (🔎) - הקטן כדי לראות את התמונה הכללית',
        'center_strands_desc': 'מרכז חוטים (🎯) - ממרכז את כל החוטים בתצוגה',
        'multi_select_desc': 'מצב הסתרה (🙉/🙈) - 🙉 לחץ להפעלת מצב הסתרה, 🙈 בחר שכבות ואז לחץ ימני לפעולות הסתרה/הצגה קבוצתיות',
        'refresh_desc': 'רענן (🔄) - מרענן את תצוגת פאנל השכבות',
        'reset_states_desc': 'איפוס מצבים (🏠) - מאפס את כל מצבי השכבות לברירת מחדל',
        # Main window button descriptions
        'attach_mode_desc': 'מצב חיבור - מחבר חוטים יחד בקצותיהם',
        'move_mode_desc': 'מצב הזזה - מזיז חוטים ונקודות בקרה על הקנווס',
        'rotate_mode_desc': 'מצב סיבוב - מסובב חוטים נבחרים',
        'toggle_grid_desc': 'החלף רשת - מציג/מסתיר את הרשת על הקנווס',
        'angle_adjust_desc': 'מצב התאמת זווית - מכוונן במדויק זוויות של חיבורי חוטים',
        'save_desc': 'שמור - שומר את הפרויקט שלך לקובץ',
        'load_desc': 'טען - טוען פרויקט מקובץ',
        'save_image_desc': 'שמור כתמונה - מייצא את העיצוב שלך כקובץ תמונה',
        'select_strand_desc': 'בחר חוט - מפעיל מצב בחירה לבחירת חוטים',
        'mask_mode_desc': 'מצב מסכה - מסתיר חלקים של חוטים העוברים מתחת לאחרים',
        'settings_desc': 'הגדרות - פותח את דיאלוג ההגדרות',
        'toggle_control_points_desc': 'החלף נקודות בקרה - מציג/מסתיר נקודות בקרה עבור עקומות בזייה',
        'toggle_shadow_desc': 'החלף צל - מציג/מסתיר צללים על חוטים',
        'layer_state_desc': 'מצב שכבה - מציג מידע דיבאג על שכבות',
        # Group button descriptions
        'create_group_desc': 'צור קבוצה - יוצר קבוצה חדשה מחוטים נבחרים',
        'group_header_desc': 'כותרת קבוצה - לחץ להרחבה/כווץ קבוצה. לחיצה ימנית לאפשרויות',
        'rename_group_desc': 'שנה שם קבוצה - משנה את השם של הקבוצה הזו',
        'delete_group_desc': 'מחק קבוצה - מסיר את הקבוצה הזו (החוטים נשארים)',
        'select_group_desc': 'בחר קבוצה - בוחר את כל החוטים בקבוצה הזו',
        'move_group_desc': 'הזז קבוצה - מזיז את כל החוטים בקבוצה יחד',
        'rotate_group_desc': 'סובב קבוצה - מסובב את כל החוטים בקבוצה',
        'edit_strand_angles_desc': 'ערוך זוויות חוטים - מיישר את כל זוויות החוטים בקבוצה כך שיהיו מקבילים זה לזה בלחיצת כפתור',
        'duplicate_group_desc': 'שכפל קבוצה - יוצר עותק של הקבוצה הזו והחוטים שלה',
        # Width dialog translations
        'total_thickness_label': 'עובי כולל (משבצות רשת):',
        'grid_squares': 'משבצות',
        'color_vs_stroke_label': 'חלוקת צבע מול קו (העובי הכולל קבוע):',
        'percent_available_color': '% מהשטח הזמין לצבע',
        'width_preview_label': 'סה"כ: {total}px | צבע: {color}px | קו: {stroke}px בכל צד',
    },

}