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
        'enable_snap_to_grid': 'Enable snap to grid',
        'use_extended_mask': 'Use extended mask (wider overlap)',
        'use_extended_mask_tooltip': 'If you want to use shadows, toggle on; if you don\'t want shadows, toggle off.',
        'use_extended_mask_desc': 'If you want to use shadows, toggle on; if you don\'t want shadows, toggle off.',
        'shadow_blur_steps': 'Shadow Blur Steps:',
        'shadow_blur_radius': 'Shadow Blur Radius:',
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
        'history': 'History',
        'whats_new': "What's New?",
        'about': 'About',
        'select_theme': 'Select Theme:',
        'select_language': 'Select Language:',
        'ok': 'OK',
        'cancel': 'Cancel',
        'apply': 'Apply',
        'language_settings_info': 'Change the language of the application.',
        'tutorial_info': 'Press the "play video" button below each text\nto view the tutorial explaining:',
        'whats_new_info': '''
        <h2>What's New in Version 1.100</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
            <li style="font-size:15px;"><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
            <li style="font-size:15px;"><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
            <li style="font-size:15px;"><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
            <li style="font-size:15px;"><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
            <li style="font-size:15px;"><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
            <li style="font-size:15px;"><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
            <li style="font-size:15px;"><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Version 1.100</p>
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
        'gif_explanation_2': 'Attaching strands, creating a mask, and changing layer positions.',
        'gif_explanation_3': 'Changing the width of a strand.',
        'gif_explanation_4': 'Creating a box (1x1) stitch.',
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
        'restore_default_stroke': 'Restore Default Stroke',
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
        'enable_snap_to_grid': 'Activer l\'alignement sur la grille',
        'use_extended_mask': 'Utiliser une extension de masque (surposition plus large)',
        'use_extended_mask_tooltip': "Si vous voulez utiliser des ombres, cochez ; si vous ne voulez pas d'ombre, décochez.",
        'use_extended_mask_desc': "Si vous voulez utiliser des ombres, cochez ; si vous ne voulez pas d'ombre, décochez.",
        'shadow_blur_steps': 'Étapes de flou d\'ombre:',
        'shadow_blur_radius': 'Rayon de flou d\'ombre:',
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
        'history': 'Historique',
        'whats_new': "Quoi de neuf ?",
        'about': 'À propos',
        'select_theme': 'Sélectionner le thème :',
        'select_language': 'Sélectionner la langue :',
        'ok': 'OK',
        'cancel': 'Annuler',
        'apply': 'Appliquer',
        'language_settings_info': 'Changer la langue de l\'application.',
        'tutorial_info': 'Appuyez sur le bouton "lire la vidéo" sous chaque texte\npour voir le tutoriel explicatif :',
        'whats_new_info': '''
        <h2>Nouveautés de la version 1.100</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
            <li style="font-size:15px;"><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
            <li style="font-size:15px;"><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
            <li style="font-size:15px;"><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
            <li style="font-size:15px;"><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
            <li style="font-size:15px;"><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
            <li style="font-size:15px;"><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
            <li style="font-size:15px;"><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Version 1.100</p>
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
        'gif_explanation_2': 'Attacher les brins, créer un masque et changer la position des calques.',
        'gif_explanation_3': 'Changer la largeur d\'un brin.',
        'gif_explanation_4': 'Création d\'un point boîte (1x1).',
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
        'extension_dash_gap_length': 'Longueur de l\'espace entre l\'extrémité du brin et le début des tirets',
        'extension_dash_gap_length_tooltip': 'Espace entre l\'extrémité du brin et le début des tirets',
        'width_preview_label': 'Total : {total}px | Couleur : {color}px | Contour : {stroke}px de chaque côté',
        'percent_available_color': '% de l\'espace couleur disponible',
        'total_thickness_label': 'Épaisseur totale (cases de grille):',
        'grid_squares': 'cases',
        'color_vs_stroke_label': 'Répartition Couleur / Contour (épaisseur totale fixe):',
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
        'enable_snap_to_grid': 'Abilita l\'aggancio alla griglia',
        'use_extended_mask': 'Usa estensione di maschera (sovrapposizione più larga)',
        'use_extended_mask_tooltip': 'Se vuoi usare le ombre, attiva; se non vuoi ombre, disattiva.',
        'use_extended_mask_desc': 'Se vuoi usare le ombre, attiva; se non vuoi ombre, disattiva.',
        'shadow_blur_steps': 'Passi di sfocatura dell\'ombra:',
        'shadow_blur_radius': 'Raggio di sfocatura dell\'ombra:',
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
        'history': 'Cronologia',
        'whats_new': "Novità?",
        'about': 'Informazioni',
        'select_theme': 'Seleziona Tema:',
        'select_language': 'Seleziona Lingua:',
        'ok': 'OK',
        'cancel': 'Annulla',
        'apply': 'Applica',
        'language_settings_info': 'Cambia la lingua dell\'applicazione.',
        'tutorial_info': 'Premi il pulsante "riproduci video" sotto ogni testo\nper visualizzare il tutorial che spiega:',
        'whats_new_info': '''
        <h2>Novità della versione 1.100</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
            <li style="font-size:15px;"><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
            <li style="font-size:15px;"><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
            <li style="font-size:15px;"><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
            <li style="font-size:15px;"><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
            <li style="font-size:15px;"><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
            <li style="font-size:15px;"><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
            <li style="font-size:15px;"><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Versione 1.100</p>
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
        'gif_explanation_2': 'Collegare trefoli, creare una maschera e cambiare la posizione dei livelli.',
        'gif_explanation_3': 'Cambiare la larghezza di un trefolo.',
        'gif_explanation_4': 'Creazione di un punto scatola (1x1).',
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
        'extension_dash_gap_length': 'Lunghezza dello spazio tra la fine del filo e l\'inizio dei trattini',
        'extension_dash_gap_length_tooltip': 'Spazio tra la fine del filo e l\'inizio dei trattini',
        'width_preview_label': 'Totale: {total}px | Colore: {color}px | Contorno: {stroke}px per lato',
        'percent_available_color': '% dello Spazio Colore Disponibile',
        'total_thickness_label': 'Spessore Totale (quadrati griglia):',
        'grid_squares': 'quadrati',
        'color_vs_stroke_label': 'Distribuzione Colore vs Contorno (spessore totale fisso):',
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
        'enable_snap_to_grid': 'Habilitar ajuste a la cuadrícula',
        'use_extended_mask': 'Usar extensión de máscara (superposición más ancha)',
        'use_extended_mask_tooltip': 'Si quieres usar sombras, activa; si no quieres sombras, desactiva.',
        'use_extended_mask_desc': 'Si quieres usar sombras, activa; si no quieres sombras, desactiva.',
        'shadow_blur_steps': 'Pasos de desenfoque de sombra:',
        'shadow_blur_radius': 'Radio de desenfoque de sombra:',
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
        'history': 'Historial',
        'whats_new': "¿Qué hay de nuevo?",
        'about': 'Acerca',
        'select_theme': 'Seleccionar Tema:',
        'select_language': 'Seleccionar Idioma:',
        'ok': 'OK',
        'cancel': 'Cancelar',
        'apply': 'Aplicar',
        'language_settings_info': 'Cambiar el idioma de la aplicación.',
        'tutorial_info': 'Presiona el botón "reproducir vídeo" debajo de cada texto\npara ver el tutorial que explica:',
        'whats_new_info': '''
        <h2>Novedades de la versión 1.100</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
            <li style="font-size:15px;"><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
            <li style="font-size:15px;"><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
            <li style="font-size:15px;"><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
            <li style="font-size:15px;"><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
            <li style="font-size:15px;"><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
            <li style="font-size:15px;"><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
            <li style="font-size:15px;"><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio - Versión 1.100</p>

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
        'gif_explanation_2': 'Unir cordones, crear una máscara y cambiar la posición de las capas.',
        'gif_explanation_3': 'Cambiar el ancho de un cordón.',
        'gif_explanation_4': 'Creación de un punto caja (1x1).',
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
        'extension_dash_gap_length': 'Longitud del espacio entre el extremo del cordón y el inicio de los guiones',
        'extension_dash_gap_length_tooltip': 'Espacio entre el extremo del cordón y el inicio de los guiones',
        'width_preview_label': 'Total: {total}px | Color: {color}px | Contorno: {stroke}px cada lado',
        'percent_available_color': '% del Espacio de Color Disponible',
        'total_thickness_label': 'Grosor Total (cuadros de cuadrícula):',
        'grid_squares': 'cuadros',
        'color_vs_stroke_label': 'Distribución Color vs Contorno (grosor total fijo):',
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
        'enable_snap_to_grid': 'Habilitar encaixe na grade',
        'use_extended_mask': 'Usar extensão de máscara (superposição mais larga)',
        'use_extended_mask_tooltip': 'Se você quiser usar sombras, ligue; se não quiser sombras, desligue.',
        'use_extended_mask_desc': 'Se você quiser usar sombras, ligue; se não quiser sombras, desligue.',
        'shadow_blur_steps': 'Passos de desfoque de sombra:',
        'shadow_blur_radius': 'Raio de desfoque de sombra:',
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
        'history': 'Histórico',
        'whats_new': "O que há de novo?",
        'about': 'Sobre',
        'select_theme': 'Selecionar Tema:',
        'select_language': 'Selecionar Idioma:',
        'ok': 'OK',
        'cancel': 'Cancelar',
        'apply': 'Aplicar',
        'language_settings_info': 'Mudar o idioma da aplicação.',
        'tutorial_info': 'Pressione o botão "reproduzir vídeo" abaixo de cada texto\npara visualizar o tutorial explicando:',
        'whats_new_info': '''
        <h2>Novidades da versão 1.100</h2>
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li style="font-size:15px;"><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
            <li style="font-size:15px;"><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
            <li style="font-size:15px;"><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
            <li style="font-size:15px;"><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
            <li style="font-size:15px;"><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
            <li style="font-size:15px;"><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
            <li style="font-size:15px;"><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
            <li style="font-size:15px;"><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
        </ul>
        <p style="font-size:13px;">© 2025 OpenStrand Studio – Versão 1.100</p>
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
        'gif_explanation_2': 'Anexar mechas, criar uma máscara e mudar a posição das camadas.',
        'gif_explanation_3': 'Mudando a largura de uma mecha.',
        'gif_explanation_4': 'Criando um ponto caixa (1x1).',
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
        'extension_dash_gap_length': 'Comprimento do espaço entre a extremidade da mecha e o início dos traços',
        'extension_dash_gap_length_tooltip': 'Espaço entre a extremidade da mecha e o início dos traços',
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
        'enable_snap_to_grid': 'הפעל הצמדה לרשת',
        'use_extended_mask': 'השימוש במסכה המורחבת (הסובב מרחב יותר)',
        'use_extended_mask_tooltip': 'אם אתה רוצה להשתמש בצללים, הפעל; אם אתה לא רוצה צללים, כבה.',
        'use_extended_mask_desc': 'אם אתה רוצה להשתמש בצללים, הפעל; אם אתה לא רוצה צללים, כבה.',
        'shadow_blur_steps': 'צעדי טשטוש צל:',
        'shadow_blur_radius': 'רדיוס טשטוש צל:',
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
        'history': 'היסטוריה',
        'whats_new': "?מה חדש",
        'about': ' אודות OpenStrand Studio',
        'select_theme': 'בחר ערכת נושא:    ',
        'select_language': 'בחר שפה:',
        'ok': 'אישור',
        'cancel': 'ביטול',
        'apply': 'החל',
        'language_settings_info': 'שנה את שפת האפליקציה.',
        'tutorial_info': 'לחץ על כפתור "הפעל וידאו" מתחת לכל טקסט\nכדי לראות את המדריך המסביר:',
        'whats_new_info': '''
        <div dir="rtl" style="text-align: right;">
        <b>מה חדש בגרסה 1.100</b><br><br>
        • <b>שינוי רוחב חוטים:</b> עכשיו אפשר לשנות את העובי של כל חוט בנפרד, כך שתוכלו ליצור עיצובים יותר מגוונים.<br>
        • <b>הגדלה והקטנה:</b> אפשר להתקרב ולהתרחק מהעיצוב שלכם כדי לראות פרטים קטנים או את כל הדיאגרמה.<br>
        • <b>הזזת המסך:</b> אפשר לגרור את הקנבס על ידי לחיצה על כפתור היד, מה שעוזר בעבודה על דיאגרמות גדולות יותר.<br>
        • <b>מצב צל בלבד:</b> עכשיו אפשר להסתיר שכבה תוך הצגת הצללים וההדגשות שלה על ידי לחיצה ימנית על כפתור שכבה ובחירת "צל בלבד". זה עוזר להמחיש אפקטי צל ללא העומס החזותי.<br>
        • <b>התחלת עבודה:</b> כשפותחים את התוכנה בפעם הראשונה, צריך ללחוץ על "חוט חדש" כדי להתחיל לצייר.<br>
        • <b>תיקונים כלליים:</b>תוקנו מספר תקלות ובעיות שנגרמו מגרסאות קודמות, כמו למשל כפתורי ביטול וחזרה יצרו חלון זמני ולא סיפקו חווית משתמש חלקה.<br>
        • <b>איכות תצוגה משופרת:</b> שיפור באיכות תצוגת הקנבס ויצוא תמונות ברזולוציה גבוהה פי 4 לתוצאות חדות ומקצועיות.<br>
        • <b>הסרת אפשרות מסכה מורחבת:</b> האפשרות למסכה מורחבת בשכבה הכללית הוסרה מכיוון שהיא הייתה נחוצה רק כגיבוי לבעיות shader בגרסאות קודמות (1.09x). עם שיפור ההצללה באופן משמעותי, אפשרות זו אינה נחוצה עוד.<br><br>
        © 2025 OpenStrand Studio - גרסה 1.100
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
        'gif_explanation_2': 'חיבור חוטים, יצירת מסכה ושינוי מיקום השכבות.',
        'gif_explanation_3': 'שינוי רוחב של חוט.',
        'gif_explanation_4': 'יצירת קשר קופסה (1x1).',
        
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
        # Width dialog translations
        'total_thickness_label': 'עובי כולל (משבצות רשת):',
        'grid_squares': 'משבצות',
        'color_vs_stroke_label': 'חלוקת צבע מול קו (העובי הכולל קבוע):',
        'percent_available_color': '% מהשטח הזמין לצבע',
        'width_preview_label': 'סה"כ: {total}px | צבע: {color}px | קו: {stroke}px בכל צד',
    },

}