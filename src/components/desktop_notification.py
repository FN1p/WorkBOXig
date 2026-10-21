"""
Modern Floating Desktop Notification System for WorkBOXig.
Displays glassmorphic alert cards in the bottom-right corner of the screen
with smooth slide-up animations, action buttons, and countdown timers.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor, QScreen
from src.styles import COLORS
from src.icons import get_pixmap, get_icon


class DesktopNotification(QWidget):
    """
    Sleek, glowing desktop notification card.
    Slides in smoothly above the Windows taskbar in the bottom-right of the screen.
    """
    action_clicked = pyqtSignal(str, dict) # action_type, payload
    dismissed = pyqtSignal()

    WIDTH = 380
    HEIGHT = 120

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.payload: Dict[str, Any] = {}
        self.action_type: str = ""

        # Outer container layout for drop shadow margins
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Card Frame
        self.card = QFrame()
        self.card.setObjectName("NotificationCard")
        self.card.setStyleSheet(f"""
            QFrame#NotificationCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:0.5 #151D2F, stop:1 #0F172A);
                border: 1px solid rgba(129, 140, 248, 0.4);
                border-top: 1px solid #818CF8;
                border-radius: 12px;
            }}
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 10, 14, 8)
        card_layout.setSpacing(6)

        # Top Row: Icon + Title + Badge + Close Button
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(22, 22)
        top_row.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("Напоминание")
        self.title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        top_row.addWidget(self.title_lbl, stretch=1)

        self.badge_lbl = QLabel("Урок")
        self.badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.badge_lbl.setStyleSheet(f"""
            color: {COLORS['sky']};
            background-color: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 6px;
            padding: 2px 7px;
        """)
        top_row.addWidget(self.badge_lbl)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94A3B8;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.12);
                border-radius: 4px;
            }
        """)
        self.close_btn.clicked.connect(self.close_animated)
        top_row.addWidget(self.close_btn)

        card_layout.addLayout(top_row)

        # Body message
        self.body_lbl = QLabel("Через 15 минут начинается занятие по расписанию.")
        self.body_lbl.setFont(QFont("Segoe UI", 9))
        self.body_lbl.setStyleSheet("color: #CBD5E1; background: transparent;")
        self.body_lbl.setWordWrap(True)
        card_layout.addWidget(self.body_lbl, stretch=1)

        # Bottom Row: Action Buttons
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        actions_row.addStretch()

        self.snooze_btn = QPushButton("Отложить (10 мин)")
        self.snooze_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.snooze_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 4px 10px;
                color: #94A3B8;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
            }
        """)
        self.snooze_btn.clicked.connect(self._on_snooze_clicked)
        actions_row.addWidget(self.snooze_btn)

        self.action_btn = QPushButton("Перейти →")
        self.action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
                border: 1px solid #818CF8;
                border-radius: 6px;
                padding: 4px 12px;
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #4F46E5);
            }}
        """)
        self.action_btn.clicked.connect(self._on_action_clicked)
        actions_row.addWidget(self.action_btn)

        card_layout.addLayout(actions_row)

        outer_layout.addWidget(self.card)

        # Auto-dismiss timer (6 seconds)
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.close_animated)

        self.anim = None

    def notify(
        self,
        title: str,
        message: str,
        category: str = "lesson",
        badge_text: str = "",
        action_type: str = "",
        payload: Optional[Dict[str, Any]] = None,
        duration_ms: int = 6500
    ):
        """Display the alert with custom icon, texts, and action."""
        self.title_lbl.setText(title)
        self.body_lbl.setText(message)
        self.action_type = action_type
        self.payload = payload or {}

        # Icon and accent styling based on category
        cat_configs = {
            "lesson": ("calendar", COLORS['sky'], badge_text or "Расписание"),
            "task": ("tasks", COLORS['amber'], badge_text or "Дедлайн"),
            "focus": ("play", COLORS['emerald'], badge_text or "Фокус"),
            "success": ("check", COLORS['emerald'], badge_text or "Успешно"),
            "info": ("zap", COLORS['primary_light'], badge_text or "WorkBOXig"),
        }
        icon_name, accent_col, badge_ru = cat_configs.get(category, ("zap", COLORS['primary_light'], "Уведомление"))

        self.icon_lbl.setPixmap(get_pixmap(icon_name, accent_col, 20))
        self.badge_lbl.setText(badge_ru)
        self.badge_lbl.setStyleSheet(f"""
            color: {accent_col};
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid {accent_col};
            border-radius: 6px;
            padding: 2px 7px;
        """)

        # Position in bottom-right of primary screen above taskbar
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            end_x = screen_geom.x() + screen_geom.width() - self.WIDTH - 16
            end_y = screen_geom.y() + screen_geom.height() - self.HEIGHT - 12
            start_y = end_y + 40 # start slightly below and slide up
        else:
            end_x, end_y = 100, 100
            start_y = 140

        self.move(end_x, start_y)
        self.show()
        self.raise_()

        # Smooth slide-up entrance animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(260)
        self.anim.setStartValue(QPoint(end_x, start_y))
        self.anim.setEndValue(QPoint(end_x, end_y))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

        self.dismiss_timer.start(duration_ms)

    def close_animated(self):
        """Slide down and hide."""
        self.dismiss_timer.stop()
        curr_pos = self.pos()
        end_pos = QPoint(curr_pos.x(), curr_pos.y() + 50)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(200)
        self.anim.setStartValue(curr_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self._on_slide_finished)
        self.anim.start()

    def _on_slide_finished(self):
        self.hide()
        self.dismissed.emit()

    def _on_action_clicked(self):
        self.dismiss_timer.stop()
        self.action_clicked.emit(self.action_type, self.payload)
        self.close_animated()

    def _on_snooze_clicked(self):
        self.close_animated()
