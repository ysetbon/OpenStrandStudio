"""Checkbox styles with private base styles and explicit widget ownership."""

from PyQt5.QtWidgets import QApplication, QProxyStyle, QStyle


class LargeIndicatorStyle(QProxyStyle):
    def __init__(self, indicator_size=20, parent=None, style_name=None):
        # The QStyle* overload takes ownership. Never pass widget.style():
        # it may be the application style or a shared stylesheet wrapper.
        # The string overload creates a separate base style for this proxy.
        name = style_name or QApplication.style().objectName()
        super().__init__(name)
        self.setParent(parent)
        self._indicator_size = indicator_size

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight):
            return self._indicator_size
        return super().pixelMetric(metric, option, widget)


def apply_large_indicator(checkbox, indicator_size=20, style_name=None):
    """Keep one proxy per checkbox; QWidget.setStyle does not own its style."""
    style = getattr(checkbox, '_large_indicator_style', None)
    if style is None:
        style = LargeIndicatorStyle(indicator_size, checkbox, style_name)
        checkbox._large_indicator_style = style
        checkbox.setStyle(style)
    else:
        style._indicator_size = indicator_size
        checkbox.updateGeometry()
        checkbox.update()
