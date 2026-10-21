"""
Floating Desktop Mini Widget for WorkBOXig (Authentic Spotify-Style HUD with Timeline).
Always-on-top, draggable, acrylic/cyberpunk compact overlay featuring a horizontal
track-progress timeline, live Pomodoro status, active task checkbox, and upcoming lesson countdown.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor, QMouseEvent

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t
from src.icons import get_pixmap, get_icon
from src.storage import get_storage
from src.components.pomodoro import PomodoroManager


class DesktopMiniWidget(QWidget):
    """Spotify-style floating desktop widget with audio/focus progress timeline."""
    expand_requested = pyqtSignal()

    def __init__(self, pomodoro_manager: PomodoroManager, parent=None):
        super().__init__(None)
        self.pomodoro = pomodoro_manager
        self.storage = get_storage()

        self._is_pinned = True
        self._is_compact = False
        self._drag_position = QPoint()

        # Frameless, Always on Top, Tool window
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("WorkBOXig Spotify HUD")

        self._init_ui()
        self._connect_signals()
        self._load_saved_position()
        self._refresh_content()

        # Timer to refresh upcoming events every 30s
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

        # Main Acrylic / Cyberpunk Card
        self.card = QFrame(self)
        self.card.setObjectName("MiniCard")
        self._update_card_style()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 170))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_vbox = QVBoxLayout(self.card)
        card_vbox.setContentsMargins(14, 10, 14, 10)
        card_vbox.setSpacing(8)

        # ================= ROW 1: SPOTIFY TRACK INFO & CONTROLS =================
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # 1. Left "Album Cover / Icon" Box (38x38)
        self.cover_box = QFrame()
        self.cover_box.setFixedSize(38, 38)
        self._update_cover_style(self.pomodoro.mode)

        c_layout = QVBoxLayout(self.cover_box)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_icon = QLabel()
        self.cover_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 20))
        c_layout.addWidget(self.cover_icon)
        top_row.addWidget(self.cover_box)

        # 2. Middle: Task Title (Track) & Next Event (Artist)
        self.text_container = QVBoxLayout()
        self.text_container.setSpacing(2)
        self.text_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        task_line = QHBoxLayout()
        task_line.setSpacing(6)

        self.task_check_btn = QPushButton()
        self.task_check_btn.setFixedSize(16, 16)
        self.task_check_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.task_check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1.5px solid {COLORS['border_subtle']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['emerald']};
                background-color: rgba(16, 185, 129, 0.2);
            }}
        """)
        self.task_check_btn.clicked.connect(self._complete_current_task)
        task_line.addWidget(self.task_check_btn)

        self.task_lbl = QLabel(t("mini_free_focus"))
        self.task_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.task_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        task_line.addWidget(self.task_lbl, stretch=1)
        self.text_container.addLayout(task_line)

        self.next_event_lbl = QLabel(t("mini_no_classes"))
        self.next_event_lbl.setFont(QFont("Segoe UI", 8))
        self.next_event_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self.text_container.addWidget(self.next_event_lbl)

        top_row.addLayout(self.text_container, stretch=1)

        # 3. Right: Media HUD Controls
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(5)
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Play/Pause
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_play_icon(self.pomodoro.is_running)
        self.play_btn.clicked.connect(self.pomodoro.toggle_timer)
        ctrl_row.addWidget(self.play_btn)

        # Skip
        self.skip_btn = QPushButton()
        self.skip_btn.setIcon(get_icon("skip", COLORS['text_secondary'], 14))
        self.skip_btn.setIconSize(QSize(14, 14))
        self.skip_btn.setFixedSize(26, 26)
        self.skip_btn.setToolTip(t("mini_skip"))
        self.skip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.skip_btn.clicked.connect(self.pomodoro.skip_session)
        ctrl_row.addWidget(self.skip_btn)

        # Expand / Restore Main Window
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(get_icon("expand", COLORS['text_secondary'], 14))
        self.expand_btn.setIconSize(QSize(14, 14))
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.setToolTip(t("mini_expand"))
        self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_btn.clicked.connect(self._restore_main_window)
        ctrl_row.addWidget(self.expand_btn)

        # Pin / Unpin
        self.pin_btn = QPushButton()
        self.pin_btn.setIcon(get_icon("pin", COLORS['primary_light'] if self._is_pinned else COLORS['text_muted'], 14))
        self.pin_btn.setIconSize(QSize(14, 14))
        self.pin_btn.setFixedSize(26, 26)
        self.pin_btn.setToolTip(t("mini_pin"))
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_btn.clicked.connect(self._toggle_pin)
        ctrl_row.addWidget(self.pin_btn)

        # Close
        self.close_btn = QPushButton()
        self.close_btn.setIcon(get_icon("close", COLORS['text_muted'], 12))
        self.close_btn.setIconSize(QSize(12, 12))
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip(t("mini_close"))
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.hide)
        ctrl_row.addWidget(self.close_btn)

        self._style_ctrl_buttons()
        top_row.addLayout(ctrl_row)
        card_vbox.addLayout(top_row)

        # ================= ROW 2: SPOTIFY TRACK PROGRESS TIMELINE =================
        self.timeline_row = QHBoxLayout()
        self.timeline_row.setSpacing(8)
        self.timeline_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Elapsed Time label
        self.elapsed_lbl = QLabel("00:00")
        self.elapsed_lbl.setFont(QFont("Consolas", 8, QFont.Weight.Medium))
        self.elapsed_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self.timeline_row.addWidget(self.elapsed_lbl)

        # Sleek Minimalist Progress Timeline Bar
        self.timeline_bar = QProgressBar()
        self.timeline_bar.setRange(0, 1000)
        self.timeline_bar.setValue(0)
        self.timeline_bar.setTextVisible(False)
        self.timeline_bar.setFixedHeight(5)
        self.timeline_bar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_timeline_style()
        self.timeline_row.addWidget(self.timeline_bar, stretch=1)

        # Remaining / Total Time label (time_lbl for backward-compatible test hooks)
        self.time_lbl = QLabel(self.pomodoro._format_time(self.pomodoro.time_left))
        self.time_lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.timeline_row.addWidget(self.time_lbl)

        card_vbox.addLayout(self.timeline_row)

        root_layout.addWidget(self.card)
        self.setFixedSize(450, 102)

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

    def _update_cover_style(self, mode: str):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        if mode == "focus":
            bg = "rgba(244, 63, 94, 0.15)"
            border = COLORS['rose']
        else:
            bg = "rgba(56, 189, 248, 0.15)"
            border = COLORS['sky']

        self.cover_box.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {'4px' if is_cyber else '8px'};
            }}
        """)

    def _update_timeline_style(self):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        chunk_color = "#FCEE0A" if is_cyber else COLORS['primary']

        self.timeline_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: {chunk_color};
                border-radius: 2px;
            }}
        """)

    def _style_ctrl_buttons(self):
        is_cyber = (CURRENT_THEME == "cyberpunk")
        accent = "#FCEE0A" if is_cyber else COLORS['primary']

        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                border-radius: {'4px' if is_cyber else '16px'};
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
        self.play_btn.setIcon(get_icon(icon_name, icon_col, 15))
        self.play_btn.setIconSize(QSize(15, 15))

    def _connect_signals(self):
        self.pomodoro.time_updated.connect(self._on_time_updated)
        self.storage.data_changed.connect(self._on_storage_changed)

    def _on_time_updated(self, time_left: int, mode: str, is_running: bool):
        total_time = self.pomodoro.FOCUS_TIME if mode == "focus" else self.pomodoro.BREAK_TIME
        elapsed = max(0, total_time - time_left)

        # Update Spotify timeline labels and progress
        self.elapsed_lbl.setText(self.pomodoro._format_time(elapsed))
        self.time_lbl.setText(self.pomodoro._format_time(time_left))

        progress_val = int((elapsed / total_time) * 1000) if total_time > 0 else 0
        self.timeline_bar.setValue(progress_val)
        self._update_play_icon(is_running)

        # Cover icon update
        self._update_cover_style(mode)
        if mode == "focus":
            self.cover_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 20))
        else:
            self.cover_icon.setPixmap(get_pixmap("coffee", COLORS['sky'], 20))

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
            if len(ev_title) > 24:
                ev_title = ev_title[:22] + "…"
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
        self.show()

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
        """Toggle ultra-compact mode (hide text info, show only controls & timeline)."""
        self._is_compact = not self._is_compact
        self.text_container.setEnabled(not self._is_compact)
        for i in range(self.text_container.count()):
            item = self.text_container.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(not self._is_compact)

        if self._is_compact:
            self.setFixedSize(300, 72)
        else:
            self.setFixedSize(450, 102)
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
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.width() - 480, geo.height() - 130)
