"""
Floating Toast Notification System for WorkBOXig.
Provides unobtrusive status feedback (saves, actions, confirmations).
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor
from src.styles import COLORS
from src.icons import get_pixmap


class ToastNotification(QWidget):
    """Sleek floating pill notification."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(get_pixmap("check", COLORS['emerald'], 16))
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Успешно")
        self.text_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #FFFFFF;")
        layout.addWidget(self.text_label)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: #1F2433;
                border: 1px solid {COLORS['border_light']};
                border-radius: 20px;
            }}
        """)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._fade_out)

        self.anim = None

    def show_message(self, message: str, level: str = "success", duration_ms: int = 2200):
        self.text_label.setText(message)
        
        if level == "success":
            self.icon_label.setPixmap(get_pixmap("check", COLORS['emerald'], 16))
        elif level == "info":
            self.icon_label.setPixmap(get_pixmap("zap", COLORS['sky'], 16))
        elif level == "warning":
            self.icon_label.setPixmap(get_pixmap("warning", COLORS['amber'], 16))
        elif level == "error":
            self.icon_label.setPixmap(get_pixmap("close", COLORS['rose'], 16))

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()

        # Fade in
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(180)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

        self.hide_timer.start(duration_ms)

    def _fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(240)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    def _reposition(self):
        if self.parent():
            p_geom = self.parent().rect()
            x = (p_geom.width() - self.width()) // 2
            y = p_geom.height() - self.height() - 32
            self.move(x, y)
