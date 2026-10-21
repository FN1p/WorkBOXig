"""
Floating Desktop Mini Widget for WorkBOXig (Spotify-Style Productivity HUD).
Always-on-top, draggable, acrylic/cyberpunk styled compact overlay with live Pomodoro timer,
next upcoming lesson countdown, quick-complete urgent tasks, and window restore.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor, QMouseEvent

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t
from src.icons import get_pixmap, get_icon
from src.storage import get_storage
from src.components.pomodoro import PomodoroManager


class DesktopMiniWidget(QWidget):
    """Floating desktop widget displaying timer, active task, and upcoming classes."""
    expand_requested = pyqtSignal()

    def __init__(self, pomodoro_manager: PomodoroManager, parent=None):
        super().__init__(None)  # Top-level window independent of main window
        self.pomodoro = pomodoro_manager
        self.storage = get_storage()

        self._is_compact = False
        self._is_pinned = True
        self._drag_position = QPoint()

        # Frameless, Always on Top, Tool window
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("WorkBOXig Mini HUD")

        self._init_ui()
        self._connect_signals()
        self._load_saved_position()
        self._refresh_content()

        # Refresh schedule countdowns every 30 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(30000)
        self._refresh_timer.timeout.connect(self._refresh_content)
        self._refresh_timer.start()

    def _apply_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self._is_pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)

        # Main Card Container
        self.card = QFrame(self)
        self.card.setObjectName("MiniCard")
        self._update_card_style()

        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        self.card_layout = QHBoxLayout(self.card)
        self.card_layout.setContentsMargins(14, 10, 14, 10)
        self.card_layout.setSpacing(12)

        # 1. Left Block: Timer & Mode Pill
        timer_box = QVBoxLayout()
        timer_box.setSpacing(2)
        timer_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t_row = QHBoxLayout()
        t_row.setSpacing(6)
        self.mode_icon = QLabel()
        self.mode_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 16))
        t_row.addWidget(self.mode_icon)

        self.time_lbl = QLabel(self.pomodoro._format_time(self.pomodoro.time_left))
        self.time_lbl.setFont(QFont("Consolas", 15, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        t_row.addWidget(self.time_lbl)
        timer_box.addLayout(t_row)

        self.mode_pill = QLabel(t("mini_widget_focus"))
        self.mode_pill.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        self.mode_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_pill.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(244, 63, 94, 0.2);
                color: {COLORS['rose']};
                border-radius: 4px;
                padding: 1px 6px;
            }}
        """)
        timer_box.addWidget(self.mode_pill)
        self.card_layout.addLayout(timer_box)

        # Vertical Divider
        self.div1 = QFrame()
        self.div1.setFrameShape(QFrame.Shape.VLine)
        self.div1.setStyleSheet(f"color: {COLORS['border_subtle']};")
        self.card_layout.addWidget(self.div1)

        # 2. Middle Block: Active Task with Checkbox & Upcoming Lesson
        self.info_box = QVBoxLayout()
        self.info_box.setSpacing(4)
        self.info_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        task_row = QHBoxLayout()
        task_row.setSpacing(6)

        self.task_check_btn = QPushButton()
        self.task_check_btn.setFixedSize(18, 18)
        self.task_check_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.task_check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1.5px solid {COLORS['border_subtle']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['emerald']};
                background-color: rgba(16, 185, 129, 0.15);
            }}
        """)
        self.task_check_btn.clicked.connect(self._complete_current_task)
        task_row.addWidget(self.task_check_btn)

        self.task_lbl = QLabel(t("mini_free_focus"))
        self.task_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.task_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        task_row.addWidget(self.task_lbl, stretch=1)
        self.info_box.addLayout(task_row)

        self.next_event_lbl = QLabel(t("mini_no_classes"))
        self.next_event_lbl.setFont(QFont("Segoe UI", 8))
        self.next_event_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self.info_box.addWidget(self.next_event_lbl)

        self.card_layout.addLayout(self.info_box, stretch=1)

        # 3. Right Block: Spotify-Style HUD Media Controls
        self.ctrl_box = QHBoxLayout()
        self.ctrl_box.setSpacing(6)
        self.ctrl_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Play/Pause
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_play_icon(self.pomodoro.is_running)
        self.play_btn.clicked.connect(self.pomodoro.toggle_timer)
        self.ctrl_box.addWidget(self.play_btn)

        # Skip
        self.skip_btn = QPushButton()
        self.skip_btn.setIcon(get_icon("skip", COLORS['text_secondary'], 14))
        self.skip_btn.setIconSize(QSize(14, 14))
        self.skip_btn.setFixedSize(26, 26)
        self.skip_btn.setToolTip(t("mini_skip"))
        self.skip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.skip_btn.clicked.connect(self.pomodoro.skip_session)
        self.ctrl_box.addWidget(self.skip_btn)

        # Expand / Restore Main Window
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(get_icon("expand", COLORS['text_secondary'], 14))
        self.expand_btn.setIconSize(QSize(14, 14))
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.setToolTip(t("mini_expand"))
        self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_btn.clicked.connect(self._restore_main_window)
        self.ctrl_box.addWidget(self.expand_btn)

        # Pin / Unpin
        self.pin_btn = QPushButton()
        self.pin_btn.setIcon(get_icon("pin", COLORS['primary_light'] if self._is_pinned else COLORS['text_muted'], 14))
        self.pin_btn.setIconSize(QSize(14, 14))
        self.pin_btn.setFixedSize(26, 26)
        self.pin_btn.setToolTip(t("mini_pin"))
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_btn.clicked.connect(self._toggle_pin)
        self.ctrl_box.addWidget(self.pin_btn)

        # Close
        self.close_btn = QPushButton()
        self.close_btn.setIcon(get_icon("close", COLORS['text_muted'], 12))
        self.close_btn.setIconSize(QSize(12, 12))
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip(t("mini_close"))
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.hide)
        self.ctrl_box.addWidget(self.close_btn)

        self._style_ctrl_buttons()
        self.card_layout.addLayout(self.ctrl_box)

        root_layout.addWidget(self.card)
        self.setFixedSize(450, 96)

    def _update_card_style(self):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        bg_col = "#0B0F19" if is_cyber else "#0F172A"
        border_col = "#00F0FF" if is_cyber else "rgba(99, 102, 241, 0.4)"

        self.card.setStyleSheet(f"""
            QFrame#MiniCard {{
                background-color: {bg_col};
                border: 1.5px solid {border_col};
                border-radius: {'6px' if is_cyber else '16px'};
            }}
        """)

    def _style_ctrl_buttons(self):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        accent = "#FCEE0A" if is_cyber else COLORS['primary']

        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                border-radius: {'4px' if is_cyber else '15px'};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {'#FFF152' if is_cyber else COLORS['primary_hover']};
            }}
        """)

        for btn in [self.skip_btn, self.expand_btn, self.pin_btn, self.close_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                }}
            """)

    def _update_play_icon(self, is_running: bool):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        icon_name = "pause" if is_running else "play"
        icon_col = "#000000" if is_cyber else "#FFFFFF"
        self.play_btn.setIcon(get_icon(icon_name, icon_col, 14))
        self.play_btn.setIconSize(QSize(14, 14))

    def _connect_signals(self):
        self.pomodoro.time_updated.connect(self._on_time_updated)
        self.storage.data_changed.connect(self._on_storage_changed)

    def _on_time_updated(self, time_left: int, mode: str, is_running: bool):
        self.time_lbl.setText(self.pomodoro._format_time(time_left))
        self._update_play_icon(is_running)

        if mode == "focus":
            self.mode_pill.setText(t("mini_widget_focus"))
            self.mode_pill.setStyleSheet(f"background-color: rgba(244, 63, 94, 0.2); color: {COLORS['rose']}; border-radius: 4px; padding: 1px 6px;")
            self.mode_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 16))
        else:
            self.mode_pill.setText(t("mini_widget_break"))
            self.mode_pill.setStyleSheet(f"background-color: rgba(56, 189, 248, 0.2); color: {COLORS['sky']}; border-radius: 4px; padding: 1px 6px;")
            self.mode_icon.setPixmap(get_pixmap("coffee", COLORS['sky'], 16))

    def _on_storage_changed(self, entity: str):
        if entity in ("tasks", "events", "all"):
            self._refresh_content()

    def _refresh_content(self):
        # 1. Fetch top urgent incomplete task
        tasks = self.storage.get_tasks()
        pending_tasks = [t for t in tasks if not t.get("completed", False)]
        urgent_tasks = [t for t in pending_tasks if t.get("priority") == "urgent"]
        active_task = urgent_tasks[0] if urgent_tasks else (pending_tasks[0] if pending_tasks else None)

        self._active_task_id = active_task["id"] if active_task else None
        if active_task:
            title = active_task.get("title", "")
            if len(title) > 28:
                title = title[:26] + "…"
            self.task_lbl.setText(title)
            self.task_check_btn.setVisible(True)
        else:
            self.task_lbl.setText(t("mini_free_focus"))
            self.task_check_btn.setVisible(False)

        # 2. Fetch next upcoming event today
        today_iso = date.today().isoformat()
        now_time = datetime.now().strftime("%H:%M")
        events = [e for e in self.storage.get_events() if e.get("date") == today_iso]
        upcoming = [e for e in events if e.get("time", "00:00") >= now_time]
        upcoming.sort(key=lambda x: x.get("time", "00:00"))

        if upcoming:
            ev = upcoming[0]
            ev_title = ev.get("title", "")
            if len(ev_title) > 20:
                ev_title = ev_title[:18] + "…"
            room = f" ({ev.get('room')})" if ev.get("room") else ""
            self.next_event_lbl.setText(f"📅 {ev.get('time')} {ev_title}{room}")
        else:
            self.next_event_lbl.setText(f"✓ {t('mini_no_classes')}")

    def _complete_current_task(self):
        if hasattr(self, '_active_task_id') and self._active_task_id:
            self.storage.toggle_task(self._active_task_id)
            self.task_check_btn.setIcon(get_icon("check", COLORS['emerald'], 12))
            QTimer.singleShot(400, self._refresh_content)

    def _toggle_pin(self):
        self._is_pinned = not self._is_pinned
        self._apply_window_flags()
        self.pin_btn.setIcon(get_icon("pin", COLORS['primary_light'] if self._is_pinned else COLORS['text_muted'], 14))
        self.show()  # Re-show required after setWindowFlags

    def _restore_main_window(self):
        self.expand_requested.emit()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._save_position()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Toggle ultra-compact pill mode on double-click."""
        self._is_compact = not self._is_compact
        self.div1.setVisible(not self._is_compact)
        self.info_box.setEnabled(not self._is_compact)
        for i in range(self.info_box.count()):
            w = self.info_box.itemAt(i).widget()
            if w:
                w.setVisible(not self._is_compact)

        if self._is_compact:
            self.setFixedSize(240, 68)
        else:
            self.setFixedSize(450, 96)
        event.accept()

    def _save_position(self):
        self.storage.set_setting("mini_widget_x", self.x())
        self.storage.set_setting("mini_widget_y", self.y())

    def _load_saved_position(self):
        x = self.storage.get_setting("mini_widget_x")
        y = self.storage.get_setting("mini_widget_y")
        if x is not None and y is not None:
            self.move(x, y)
        else:
            # Default to bottom-right corner of primary screen
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.width() - 480, geo.height() - 120)
