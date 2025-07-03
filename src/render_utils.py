"""
Utility class for enhanced high-DPI rendering across the application.
Provides consistent crisp rendering for all QPainter instances.
"""

from PyQt5.QtGui import QPainter, QImage, QPen, QBrush
from PyQt5.QtCore import Qt, QRect, QPoint
import logging


class RenderUtils:
    """Utility class for enhanced rendering with high-DPI support."""
    
    # Global rendering quality multiplier (4x for crisp rendering)
    QUALITY_FACTOR = 4.0
    
    @staticmethod
    def setup_painter(painter, enable_high_quality=True, ui_element=False):
        """
        Set up a QPainter with optimal render hints for crisp drawing.
        
        Args:
            painter (QPainter): The painter to configure
            enable_high_quality (bool): Whether to enable high-quality rendering
            ui_element (bool): Whether this is for UI elements (buttons, panels, etc.)
        """
        # Check if this painter has already been configured by us
        # to avoid double setup that can cause QBackingStore warnings
        if hasattr(painter, '_renderutils_configured'):
            logging.info(f"[RenderUtils.setup_painter] Painter already configured, skipping setup")
            return
        
        # Log the painter setup call
        caller_info = "Unknown"
        try:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        except:
            pass
        
        logging.info(f"[RenderUtils.setup_painter] Called from: {caller_info}")
        logging.info(f"[RenderUtils.setup_painter] enable_high_quality={enable_high_quality}, ui_element={ui_element}")
        
        if enable_high_quality:
            # Enable all antialiasing and high-quality rendering
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            logging.info(f"[RenderUtils.setup_painter] Basic render hints enabled")
            
            # Only enable high-DPI features for canvas elements, not UI elements
            if not ui_element:
                logging.info(f"[RenderUtils.setup_painter] Enabling HIGH-DPI features for canvas element")
                # Enable high-quality antialiasing if available
                if hasattr(QPainter, 'HighQualityAntialiasing'):
                    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    logging.info(f"[RenderUtils.setup_painter] HighQualityAntialiasing enabled")
                
                # Additional render hints for better quality
                if hasattr(QPainter, 'LosslessImageRendering'):
                    painter.setRenderHint(QPainter.LosslessImageRendering, True)
                    logging.info(f"[RenderUtils.setup_painter] LosslessImageRendering enabled")
            else:
                logging.info(f"[RenderUtils.setup_painter] SKIPPING HIGH-DPI features for UI element")
            
            # Set composition mode for better blending
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            logging.info(f"[RenderUtils.setup_painter] CompositionMode_SourceOver set")
        else:
            # Standard rendering for performance-critical scenarios
            painter.setRenderHint(QPainter.Antialiasing, True)
            logging.info(f"[RenderUtils.setup_painter] Standard rendering mode enabled")
        
        # Mark this painter as configured to prevent double setup
        painter._renderutils_configured = True
    
    @staticmethod
    def create_smooth_pen(color, width, style=Qt.SolidLine):
        """
        Create a pen optimized for smooth antialiased drawing.
        
        Args:
            color: Pen color
            width: Pen width
            style: Pen style (default SolidLine)
            
        Returns:
            QPen: Optimized pen for smooth drawing
        """
        pen = QPen(color, width, style)
        # Set optimal settings for smooth antialiasing
        pen.setCapStyle(Qt.RoundCap)  # Round caps for smoother lines
        pen.setJoinStyle(Qt.RoundJoin)  # Round joins for smoother corners
        return pen
    
    @staticmethod
    def create_smooth_brush(color):
        """
        Create a brush optimized for smooth antialiased drawing.
        
        Args:
            color: Brush color
            
        Returns:
            QBrush: Optimized brush for smooth drawing
        """
        return QBrush(color, Qt.SolidPattern)
    
    @staticmethod
    def setup_ui_painter(painter):
        """
        Set up a QPainter specifically for UI elements (buttons, panels, etc.)
        This ensures UI elements don't get affected by high-DPI scaling.
        
        Args:
            painter (QPainter): The painter to configure for UI rendering
        """
        logging.info(f"[RenderUtils.setup_ui_painter] Setting up painter for UI element")
        RenderUtils.setup_painter(painter, enable_high_quality=True, ui_element=True)
    
    @staticmethod
    def enhance_pen_for_antialiasing(pen):
        """
        Enhance an existing pen for better antialiasing.
        
        Args:
            pen (QPen): The pen to enhance
            
        Returns:
            QPen: Enhanced pen with better antialiasing settings
        """
        enhanced_pen = QPen(pen)  # Copy the original pen
        
        # Only change cap/join style if not specifically set for design reasons
        if enhanced_pen.capStyle() == Qt.SquareCap:
            enhanced_pen.setCapStyle(Qt.RoundCap)
        if enhanced_pen.joinStyle() == Qt.MiterJoin:
            enhanced_pen.setJoinStyle(Qt.RoundJoin)
            
        return enhanced_pen
    
    @staticmethod
    def create_high_dpi_image(size, device_pixel_ratio=None):
        """
        Create a high-DPI QImage for crisp rendering.
        
        Args:
            size (QSize): The logical size of the image
            device_pixel_ratio (float): Device pixel ratio, auto-detected if None
            
        Returns:
            QImage: High-DPI image ready for painting
        """
        if device_pixel_ratio is None:
            device_pixel_ratio = RenderUtils.QUALITY_FACTOR
        
        # Create image with scaled dimensions
        scaled_size = size * device_pixel_ratio
        image = QImage(scaled_size, QImage.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(device_pixel_ratio)
        image.fill(Qt.transparent)
        
        return image
    
    @staticmethod
    def scale_value(value, scale_factor=None):
        """
        Scale a value by the quality factor for high-DPI rendering.
        
        Args:
            value (float): Value to scale
            scale_factor (float): Scale factor, uses QUALITY_FACTOR if None
            
        Returns:
            float: Scaled value
        """
        if scale_factor is None:
            scale_factor = RenderUtils.QUALITY_FACTOR
        scaled_result = value * scale_factor
        logging.info(f"[RenderUtils.scale_value] Scaling {value} by {scale_factor} = {scaled_result}")
        return scaled_result
    
    @staticmethod
    def get_device_pixel_ratio(widget):
        """
        Get the device pixel ratio for a widget.
        
        Args:
            widget (QWidget): Widget to get ratio for
            
        Returns:
            float: Device pixel ratio
        """
        if hasattr(widget, 'devicePixelRatio'):
            return widget.devicePixelRatio()
        return 1.0
    
    @staticmethod
    def setup_high_dpi_painting(widget, painter):
        """
        Set up high-DPI painting for a widget's painter.
        
        Args:
            widget (QWidget): The widget being painted
            painter (QPainter): The painter to configure
        """
        # Get device pixel ratio
        device_ratio = RenderUtils.get_device_pixel_ratio(widget)
        
        # Set up high-quality rendering
        RenderUtils.setup_painter(painter, enable_high_quality=True)
        
        # If we have a high-DPI display, no additional scaling needed
        # The system will handle it automatically with proper render hints
        return device_ratio


class HighDPIBuffer:
    """
    Helper class for rendering to a high-DPI offscreen buffer.
    Useful for complex drawing operations that benefit from supersampling.
    """
    
    def __init__(self, size, quality_factor=None):
        """
        Initialize the high-DPI buffer.
        
        Args:
            size (QSize): Logical size of the buffer
            quality_factor (float): Quality multiplier, uses RenderUtils.QUALITY_FACTOR if None
        """
        if quality_factor is None:
            quality_factor = RenderUtils.QUALITY_FACTOR
            
        self.logical_size = size
        self.quality_factor = quality_factor
        self.buffer = RenderUtils.create_high_dpi_image(size, quality_factor)
    
    def get_painter(self):
        """
        Get a QPainter for drawing to the buffer.
        
        Returns:
            QPainter: Configured painter for the buffer
        """
        painter = QPainter(self.buffer)
        RenderUtils.setup_painter(painter, enable_high_quality=True)
        
        # Scale the painter to account for the quality factor
        painter.scale(self.quality_factor, self.quality_factor)
        
        return painter
    
    def draw_to_painter(self, target_painter, target_rect=None):
        """
        Draw the buffer contents to a target painter.
        
        Args:
            target_painter (QPainter): Painter to draw to
            target_rect (QRect): Target rectangle, uses logical size if None
        """
        if target_rect is None:
            target_rect = QRect(QPoint(0, 0), self.logical_size)
        
        target_painter.drawImage(target_rect, self.buffer)