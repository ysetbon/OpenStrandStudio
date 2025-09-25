import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QEvent, QObject
from PyQt5.QtGui import QColor, QCursor, QGuiApplication
from main_window import MainWindow
from undo_redo_manager import connect_to_move_mode, connect_to_attach_mode, connect_to_mask_mode

# Configure logging before importing other modules







# At the start of your main.py
# os.environ['QT_MAC_WANTS_LAYER'] = '1'

def get_settings_directory():
    """Get the settings directory path consistently across platforms."""
    from PyQt5.QtCore import QStandardPaths
    
    app_name = "OpenStrand Studio"
    if sys.platform.startswith('darwin'):  # macOS
        program_data_dir = os.path.expanduser('~/Library/Application Support')
        settings_dir = os.path.join(program_data_dir, app_name)
    else:
        program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        settings_dir = program_data_dir  # AppDataLocation already includes the app name
    return settings_dir

def load_user_settings():
    settings_dir = get_settings_directory()
    file_path = os.path.join(settings_dir, 'user_settings.txt')
    pass

    # Initialize with default values
    theme_name = 'default'
    language_code = 'en'
    shadow_color = QColor(0, 0, 0, 150)  # Default shadow color (black with 59% opacity)
    draw_only_affected_strand = False  # Default to drawing all strands
    enable_third_control_point = False  # Default to two control points
    enable_curvature_bias_control = False  # Default to no bias controls
    # use_extended_mask = False  # Default exact mask
    # Initialize arrow settings defaults
    arrow_head_length = 20.0
    arrow_head_width = 10.0
    arrow_gap_length = 10.0
    arrow_line_length = 20.0
    arrow_line_width = 10.0
    # Initialize default arrow fill color and toggle for using default color
    use_default_arrow_color = False
    default_arrow_fill_color = QColor(0, 0, 0, 255)
    
    # Initialize default strand and stroke colors
    default_strand_color = QColor(200, 170, 230, 255)  # Default purple
    default_stroke_color = QColor(0, 0, 0, 255)  # Default black

    # Initialize curve parameters with defaults
    control_point_base_fraction = 0.4  # Default base fraction
    distance_multiplier = 1.2  # Default distance multiplier
    curve_response_exponent = 1.5  # Default curve response exponent
    
    # Try to load from settings file
    shadow_color_loaded = False
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                pass
                content = file.read()
                pass
                
                # Reset file position to beginning
                file.seek(0)
                
                for line in file:
                    line = line.strip()
                    pass
                    
                    if line.startswith('Theme:'):
                        theme_name = line.strip().split(':', 1)[1].strip()
                        pass
                    elif line.startswith('Language:'):
                        language_code = line.strip().split(':', 1)[1].strip()
                        pass
                    elif line.startswith('ShadowColor:'):
                        # Parse the RGBA values
                        rgba_str = line.strip().split(':', 1)[1].strip()
                        pass
                        try:
                            r, g, b, a = map(int, rgba_str.split(','))
                            # Create a fresh QColor instance
                            shadow_color = QColor(r, g, b, a)
                            shadow_color_loaded = True
                            pass
                        except Exception as e:
                            pass
                    elif line.startswith('DrawOnlyAffectedStrand:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        draw_only_affected_strand = (value == 'true')
                        pass
                    elif line.startswith('EnableThirdControlPoint:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        enable_third_control_point = (value == 'true')
                        pass
                    elif line.startswith('EnableCurvatureBiasControl:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        enable_curvature_bias_control = (value == 'true')
                        pass
                    # elif line.startswith('UseExtendedMask:'):
                    #     value = line.strip().split(':', 1)[1].strip().lower()
                    #     use_extended_mask = (value == 'true')
                    #     logging.info(f"Found UseExtendedMask: {use_extended_mask}")
                    elif line.startswith('ArrowHeadLength:'):
                        try:
                            arrow_head_length = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('ArrowHeadWidth:'):
                        try:
                            arrow_head_width = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('ArrowGapLength:'):
                        try:
                            arrow_gap_length = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('ArrowLineLength:'):
                        try:
                            arrow_line_length = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('ArrowLineWidth:'):
                        try:
                            arrow_line_width = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('UseDefaultArrowColor:'):
                        value = line.split(':', 1)[1].strip().lower()
                        use_default_arrow_color = (value == 'true')
                        pass
                    elif line.startswith('DefaultArrowColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_arrow_fill_color = QColor(r, g, b, a)
                            pass
                        except Exception as e:
                            pass
                    elif line.startswith('DefaultStrandColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_strand_color = QColor(r, g, b, a)
                            pass
                        except Exception as e:
                            pass
                    elif line.startswith('DefaultStrokeColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_stroke_color = QColor(r, g, b, a)
                            pass
                        except Exception as e:
                            pass
                    elif line.startswith('ControlPointBaseFraction:'):
                        try:
                            control_point_base_fraction = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('DistanceMultiplier:'):
                        try:
                            distance_multiplier = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
                    elif line.startswith('CurveResponseExponent:'):
                        try:
                            curve_response_exponent = float(line.split(':', 1)[1].strip())
                            pass
                        except ValueError:
                            pass
            
            if shadow_color_loaded:
                pass
                # logging.info(f"User settings loaded successfully. Theme: {theme_name}, Language: {language_code}, Shadow Color: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}, Draw Only Affected Strand: {draw_only_affected_strand}, Enable Third Control Point: {enable_third_control_point}, Use Extended Mask: {use_extended_mask}, ArrowHeadLength: {arrow_head_length}, ArrowHeadWidth: {arrow_head_width}, ArrowGapLength: {arrow_gap_length}, ArrowLineLength: {arrow_line_length}, ArrowLineWidth: {arrow_line_width}")
            else:
                
                pass
        except Exception as e:
            pass
    else:
        pass

    return theme_name, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, enable_curvature_bias_control, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color, default_strand_color, default_stroke_color, control_point_base_fraction, distance_multiplier, curve_response_exponent

if __name__ == '__main__':
    pass

    # Disable automatic high-DPI scaling to prevent UI elements from being scaled
    # We'll handle high-DPI rendering manually only for canvas elements
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # Keep high-DPI pixmaps for better image quality
    
    pass
    pass
    
    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, enable_curvature_bias_control, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color, default_strand_color, default_stroke_color, control_point_base_fraction, distance_multiplier, curve_response_exponent = load_user_settings()
    # logging.info(f"Loaded settings - Theme: {theme}, Language: {language_code}, Shadow Color RGBA: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}, Draw Only Affected Strand: {draw_only_affected_strand}, Enable Third Control Point: {enable_third_control_point}, Use Extended Mask: {use_extended_mask}, ArrowHeadLength: {arrow_head_length}, ArrowHeadWidth: {arrow_head_width}, ArrowGapLength: {arrow_gap_length}, ArrowLineLength: {arrow_line_length}, ArrowLineWidth: {arrow_line_width}")

    # Initialize the main window with settings
    window = MainWindow()
    
    # Set the shadow color immediately on the canvas
    if hasattr(window, 'canvas') and window.canvas:
        # Check if the canvas already has this shadow color (might have been set during initialization)
        should_set_shadow = True
        if hasattr(window.canvas, 'default_shadow_color') and window.canvas.default_shadow_color:
            current_color = window.canvas.default_shadow_color
            if (current_color.red() == shadow_color.red() and 
                current_color.green() == shadow_color.green() and 
                current_color.blue() == shadow_color.blue() and 
                current_color.alpha() == shadow_color.alpha()):
                pass
                should_set_shadow = False
        
        if should_set_shadow:
            # Force it to be a new QColor instance to ensure it's correctly applied
            rgb_color = QColor(shadow_color.red(), shadow_color.green(), shadow_color.blue(), shadow_color.alpha())
            window.canvas.set_shadow_color(rgb_color)
            
        
        # Set draw only affected strand setting for all modes
        if hasattr(window.canvas, 'move_mode'):
            window.canvas.move_mode.draw_only_affected_strand = draw_only_affected_strand
            
        if hasattr(window.canvas, 'rotate_mode'):
            window.canvas.rotate_mode.draw_only_affected_strand = draw_only_affected_strand
            
        if hasattr(window.canvas, 'angle_adjust_mode'):
            window.canvas.angle_adjust_mode.draw_only_affected_strand = draw_only_affected_strand
            
            
            # Connect the move_mode's mouseReleaseEvent to the undo/redo manager if layer_panel exists
            if hasattr(window, 'layer_panel') and window.layer_panel and hasattr(window.layer_panel, 'undo_redo_manager'):
                connect_to_move_mode(window.canvas, window.layer_panel.undo_redo_manager)
                
                
                # Also connect the attach_mode if it exists
                if hasattr(window.canvas, 'attach_mode') and window.canvas.attach_mode:
                    connect_to_attach_mode(window.canvas, window.layer_panel.undo_redo_manager)
                    
                
                # Also connect the mask_mode if it exists
                if hasattr(window.canvas, 'mask_mode') and window.canvas.mask_mode:
                    connect_to_mask_mode(window.canvas, window.layer_panel.undo_redo_manager)
                    
        
        # Set enable third control point setting
        window.canvas.enable_third_control_point = enable_third_control_point
        
        # Set enable curvature bias control setting
        window.canvas.enable_curvature_bias_control = enable_curvature_bias_control

        # Set extended mask setting
        # window.canvas.use_extended_mask = use_extended_mask
        # logging.info(f"Set use_extended_mask to {use_extended_mask}")
        # Apply arrow settings to canvas
        window.canvas.arrow_head_length = arrow_head_length
        window.canvas.arrow_head_width = arrow_head_width
        window.canvas.arrow_gap_length = arrow_gap_length
        window.canvas.arrow_line_length = arrow_line_length
        window.canvas.arrow_line_width = arrow_line_width
        # Apply default arrow color settings to canvas
        window.canvas.use_default_arrow_color = use_default_arrow_color
        window.canvas.default_arrow_fill_color = default_arrow_fill_color
        # Apply default strand and stroke colors to canvas
        window.canvas.default_strand_color = default_strand_color
        window.canvas.default_stroke_color = default_stroke_color
        # Apply curve parameters to canvas
        window.canvas.control_point_base_fraction = control_point_base_fraction
        window.canvas.distance_multiplier = distance_multiplier
        window.canvas.curve_response_exponent = curve_response_exponent
        pass
        pass
        pass
        
        # Update LayerPanel's default colors to match the canvas
        if hasattr(window, 'layer_panel') and window.layer_panel:
            window.layer_panel.update_default_colors()
            
    else:
        pass
    
    window.set_language(language_code)
    
    # Apply theme before window is shown
    window.apply_theme(theme)
    
    # ================== ENHANCED MULTI-MONITOR WINDOW POSITIONING ==================
    
 
    
    # STEP 1: Ensure window is completely hidden during setup
    window.setVisible(False)
    window.hide()
    window.setAttribute(Qt.WA_DontShowOnScreen, True)  # Extra insurance
    
    
    # STEP 2: Find screen where cursor is currently located
    cursor_pos = QCursor.pos()
    
    
    # Debug: Log all available screens first
    try:
        screens = QGuiApplication.screens()
        
        for i, screen in enumerate(screens):
            screen_rect = screen.geometry()
            available_rect = screen.availableGeometry()
         
            
            # Check if cursor is on this screen
            if screen_rect.contains(cursor_pos):
                pass
    except Exception as e:
        pass
    
    try:
        # Find which screen contains the cursor
        target_screen = None
        target_screen_index = -1
        for i, screen in enumerate(screens):
            screen_rect = screen.geometry()
            if screen_rect.contains(cursor_pos):
                target_screen = screen
                target_screen_index = i
                
                break
        
        # Fallback to primary screen if cursor position doesn't match any screen
        if not target_screen:
            target_screen = QGuiApplication.primaryScreen()
            target_screen_index = 0
            
        
        # Get the available geometry (excluding taskbar/dock)
        available_rect = target_screen.availableGeometry()
        full_rect = target_screen.geometry()
        
        
        
        # STEP 3: Create window handle and assign to correct screen BEFORE any geometry changes
        window.setAttribute(Qt.WA_NativeWindow, True)
        window_id = window.winId()  # Force native window creation
        
        
        # Ensure we have a window handle before proceeding
        if not window.windowHandle():
            pass
            raise Exception("Window handle creation failed")
        
        # Assign window to the target screen
        window.windowHandle().setScreen(target_screen)
        
        
        # STEP 4: Set minimum size constraints
        window.setMinimumSize(677, 820)
        
        
        # STEP 5: Set window flags for better multi-monitor support
        # Remove any flags that might interfere with proper screen placement
        window.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                            Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # STEP 6: DO NOT manually position - let Qt handle it when maximized
        
        
        # STEP 7: Process pending events
        app.processEvents()
        
        
        # Remove the attribute that was keeping window off-screen
        window.setAttribute(Qt.WA_DontShowOnScreen, False)
        
        # STEP 8: Show window with explicit positioning
        def show_window_on_target_screen():
           
            
            try:
                # Ensure window is assigned to correct screen
                if window.windowHandle():
                    window.windowHandle().setScreen(target_screen)
                
                # First, show window in normal state at a specific position on target screen
                # This helps ensure it appears on the correct screen
                center_x = available_rect.x() + available_rect.width() // 2
                center_y = available_rect.y() + available_rect.height() // 2
                window.move(center_x - 400, center_y - 300)
                window.resize(800, 600)
                
                # Show the window
                window.show()
                
                # Process events to ensure window is created on correct screen
                app.processEvents()
                
                # Now move to full screen position and maximize
                def maximize_on_correct_screen():
                    # Verify we're on the right screen
                    current_screen = window.windowHandle().screen() if window.windowHandle() else None
                    if current_screen != target_screen:
                        pass
                        window.windowHandle().setScreen(target_screen)
                    
                    # Method 1: Try standard maximization
                    window.showMaximized()
                    app.processEvents()
                    
                    # Check if maximization worked correctly
                    QTimer.singleShot(50, lambda: verify_and_fix_maximization())
                
                def verify_and_fix_maximization():
                    current_screen = window.windowHandle().screen() if window.windowHandle() else None
                    frame_geom = window.frameGeometry()
                    
                    # Check if window is on correct screen with correct size
                    correct_screen = current_screen == target_screen
                    correct_size = (
                        abs(frame_geom.width() - available_rect.width()) < 50 and
                        abs(frame_geom.height() - available_rect.height()) < 50
                    )
                    
                    if not correct_screen or not correct_size:
                        pass
                        
                        # Method 2: Manual fullscreen positioning
                        window.setWindowState(Qt.WindowNoState)  # Clear maximized state
                        window.setGeometry(available_rect)  # Set to exact screen dimensions
                        
                        # Try maximizing again after positioning
                        QTimer.singleShot(50, lambda: window.showMaximized())
                    
                    # Log final state
                    actual_screen = window.windowHandle().screen() if window.windowHandle() else None
                    actual_geom = window.geometry()
                    frame_geom = window.frameGeometry()
                    
                 
                    
                    if actual_screen and actual_screen != target_screen:
                        pass
                       
                
                # Ensure window is on top and focused
                window.raise_()
                window.activateWindow()
                window.setFocus(Qt.OtherFocusReason)
                
                # Start maximization process
                QTimer.singleShot(100, maximize_on_correct_screen)
                
            except Exception as e:
                
                # Emergency fallback
                window.show()
                window.showMaximized()
        
        # Show window
        show_window_on_target_screen()
        
        # Additional aggressive correction if needed
        def force_correct_screen_placement():
            """Force window to correct screen with proper dimensions"""
            try:
                if window.isVisible() and window.windowHandle():
                    current_screen = window.windowHandle().screen()
                    frame_geom = window.frameGeometry()
                    
                    # Check if we need correction
                    wrong_screen = current_screen != target_screen
                    wrong_size = (
                        abs(frame_geom.width() - available_rect.width()) > 100 or
                        abs(frame_geom.height() - available_rect.height()) > 100
                    )
                    
                    if wrong_screen or wrong_size:
                     
                        
                        # Clear all window states
                        window.setWindowState(Qt.WindowNoState)
                        window.hide()
                        
                        # Force to target screen
                        window.windowHandle().setScreen(target_screen)
                        
                        # Set exact geometry
                        window.setGeometry(available_rect)
                        
                        # Show and maximize
                        window.show()
                        window.showMaximized()
                        
                        # Force raise and activate
                        window.raise_()
                        window.activateWindow()
                        
                        
                    
                    # Log final state
                    final_screen = window.windowHandle().screen()
                    final_geom = window.frameGeometry()
                 
                    
            except Exception as e:
                pass
        
        # Apply aggressive correction after a delay
        QTimer.singleShot(300, force_correct_screen_placement)
        
        # Final verification
        def verify_window_placement():
         
            
            try:
                if window.isVisible() and window.windowHandle():
                    current_screen = window.windowHandle().screen()
                    current_geom = window.geometry()
                    frame_geom = window.frameGeometry()
                    cursor_now = QCursor.pos()
                    
               
                    
                    # Check screen
                    screen_correct = current_screen == target_screen
                    if not screen_correct:
                        pass
                     
                    
                    # Check if properly maximized
                    expected_area = target_screen.availableGeometry()
                    
                    # For maximized windows, check if frame is near the expected area
                    position_correct = (
                        abs(frame_geom.x() - expected_area.x()) <= 10 and
                        abs(frame_geom.y() - expected_area.y()) <= 50  # Allow more tolerance for title bar
                    )
                    
                    size_correct = (
                        abs(frame_geom.width() - expected_area.width()) <= 50 and
                        abs(frame_geom.height() - expected_area.height()) <= 50
                    )
                    
                    if not position_correct or not size_correct:
                     
                        
                        # One final correction attempt
                        if not screen_correct or not size_correct:
                            
                            window.hide()
                            window.setWindowState(Qt.WindowNoState)
                            window.windowHandle().setScreen(target_screen)
                            window.setGeometry(available_rect)
                            window.show()
                            window.showMaximized()
                            
                            # Check again after correction
                            QTimer.singleShot(200, lambda: log_final_state())
                    else:
                        pass
                    
                    if screen_correct and window.isMaximized() and position_correct and size_correct:
                        pass
                    else:
                        pass
                
                def log_final_state():
                    final_screen = window.windowHandle().screen() if window.windowHandle() else None
                    final_frame = window.frameGeometry()
                  
                        
            except Exception as e:
                pass
                
        
        # Verify after window settles
        QTimer.singleShot(500, verify_window_placement)
        
    except Exception as e:
        pass
        
        
        # Emergency fallback
        try:
            window.setAttribute(Qt.WA_DontShowOnScreen, False)
            window.setMinimumSize(677, 820)
            window.showMaximized()
            window.raise_()
            window.activateWindow()
            
        except Exception as e2:
            pass
    
    pass
   
    
    # Add event filter to handle minimize/restore properly
    class ScreenKeeper(QObject):
        """Ensures window stays on correct screen when minimized/restored"""
        def __init__(self, window, target_screen):
            super().__init__()
            self.window = window
            self.target_screen = target_screen
            self.last_geometry = None
            self.was_maximized = False
            self.repositioning_in_progress = False
            
        def eventFilter(self, obj, event):
            try:
                # Window state is about to change
                if event.type() == QEvent.WindowStateChange:
                    current_state = self.window.windowState()
                    
                    # Log window state changes for debugging
                    if current_state & Qt.WindowMinimized:
                        pass
                        pass
                        pass
                        
                        # Store state before minimizing
                        if not hasattr(self, '_stored_state'):  # Only store once per minimize cycle
                            self.last_geometry = self.window.geometry()
                            # Store the actual maximized state to restore exactly like startup
                            # The startup behavior shows the window maximized, so we should restore it maximized too
                            self.was_maximized = bool(current_state & Qt.WindowMaximized)
                            if self.window.windowHandle():
                                current_screen = self.window.windowHandle().screen()
                                if current_screen:
                                    # Always update to the current screen - respect user's choice
                                    self.target_screen = current_screen
                            pass
                            self._stored_state = True
                    else:
                        # Window is not minimized anymore - might be restoring
                        if hasattr(self, '_stored_state'):
                            pass
                            pass
                            pass
                            del self._stored_state  # Clear the flag
                
                # Window is being shown/restored
                elif event.type() == QEvent.Show:
                    pass
                    # Only check if we have stored state (i.e., this is a restore from minimize)
                    if hasattr(self, '_stored_state'):
                        pass
                        # Add a small delay to let the window settle before checking
                        QTimer.singleShot(50, self.check_and_restore_screen)
                    else:
                        pass
                elif event.type() == QEvent.WindowActivate:
                    # Check if window activation events should be suppressed (during undo/redo)
                    if hasattr(self.window, 'suppress_activation_events') and self.window.suppress_activation_events:
                        # Skip logging and processing during undo/redo operations
                        pass
                    else:
                        pass
                        # Don't check on activate to avoid duplicate repositioning
                    
            except Exception as e:
                pass
            
            return False  # Don't consume the event
        
        def check_and_restore_screen(self):
            """Check if window is on correct screen after restore"""
            try:
                # Prevent multiple repositioning calls during the same restore cycle
                if self.repositioning_in_progress:
                    
                    return
                
                if not self.window.isMinimized() and self.window.isVisible():
                    current_screen = self.window.windowHandle().screen() if self.window.windowHandle() else None
                    current_maximized = self.window.isMaximized()
                
                    
                    # Determine if repositioning is needed to match startup behavior
                    needs_repositioning = False
                    
                    # Check if screen is wrong
                    if current_screen and current_screen != self.target_screen:
                        
                        needs_repositioning = True
                    
                    # Check if maximization state doesn't match what was stored
                    elif self.was_maximized and not current_maximized:
                        
                        needs_repositioning = True
                    
                    # For maximized windows, always ensure they're properly positioned like startup
                    elif self.was_maximized and current_maximized:
                        current_geometry = self.window.frameGeometry()
                        available_rect = self.target_screen.availableGeometry()
                        
                   
                        
                        # Check if window is properly positioned and sized
                        position_correct = (
                            abs(current_geometry.x() - available_rect.x()) <= 10 and
                            abs(current_geometry.y() - available_rect.y()) <= 50
                        )
                        size_correct = (
                            abs(current_geometry.width() - available_rect.width()) <= 50 and
                            abs(current_geometry.height() - available_rect.height()) <= 50
                        )
                        
                        if not position_correct or not size_correct:
                           
                            needs_repositioning = True
                        else:
                            
                            # Even if geometry matches, ensure window is properly focused and visible
                            self.window.raise_()
                            self.window.activateWindow()
                            self.window.setFocus(Qt.OtherFocusReason)
                            
                    
                    if needs_repositioning:
                        # Set flag to prevent multiple repositioning calls
                        self.repositioning_in_progress = True
                        
                        
                        
                        # Get the target screen's available area
                        available_rect = self.target_screen.availableGeometry()
                        
                        # Restore to correct screen with proper positioning
                        if self.was_maximized:
                            # For maximized windows - restore exactly like startup
                            
                            
                            # Step 1: Hide window briefly to avoid visible repositioning
                            self.window.setVisible(False)
                            
                            # Step 2: Ensure correct screen assignment
                            if self.window.windowHandle():
                                self.window.windowHandle().setScreen(self.target_screen)
                                pass
                            
                            # Step 3: Clear current state
                            self.window.setWindowState(Qt.WindowNoState)
                            
                            # Step 4: Process events to ensure state is cleared
                            from PyQt5.QtWidgets import QApplication
                            QApplication.processEvents()
                            
                            # Step 5: Set geometry to available area (like startup)
                            self.window.setGeometry(available_rect)
                            
                            # Step 6: Show and maximize (exactly like showEvent in main_window.py)
                            self.window.setVisible(True)
                            self.window.setWindowState(Qt.WindowMaximized)
                            
                            
                            # Step 7: Ensure window is on top and focused
                            self.window.raise_()
                            self.window.activateWindow()
                            self.window.setFocus(Qt.OtherFocusReason)
                            
                            
                        else:
                            # For normal windows, restore last position
                            
                            if self.window.windowHandle():
                                self.window.windowHandle().setScreen(self.target_screen)
                            if self.last_geometry:
                                # Adjust position to be within target screen bounds
                                x = max(available_rect.x(), min(self.last_geometry.x(), available_rect.x() + available_rect.width() - self.last_geometry.width()))
                                y = max(available_rect.y(), min(self.last_geometry.y(), available_rect.y() + available_rect.height() - self.last_geometry.height()))
                                self.window.move(x, y)
                                self.window.resize(self.last_geometry.size())
                        
                        pass
                        
                        # Clear flag after repositioning is complete
                        QTimer.singleShot(100, lambda: setattr(self, 'repositioning_in_progress', False))
                        
                    else:
                        pass
                    
            except Exception as e:
                pass
    
    # Install the event filter
    screen_keeper = ScreenKeeper(window, target_screen)
    window.installEventFilter(screen_keeper)
    
    
    # Set the initial splitter sizes to make the layer panel narrower
    window.set_initial_splitter_sizes()
    
    # Verify shadow color after everything is initialized
    if hasattr(window, 'canvas') and window.canvas:
        current_shadow = window.canvas.default_shadow_color
        

    sys.exit(app.exec_())