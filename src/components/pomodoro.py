"""
Pomodoro & Deep Focus System for WorkBOXig.
Includes compact header capsule and Zen Focus Mode dialog.
"""

import ctypes
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QDialog, QComboBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor, QIcon
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon


class PomodoroManager(QWidget):
    """Pomodoro capsule widget for header and timer engine."""
    session_completed = pyqtSignal(str) # mode: 'focus' or 'break'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        
        self.FOCUS_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        
        self.time_left = self.FOCUS_TIME
        self.is_running = False
        self.mode = "focus" # "focus" or "break"
        self.completed_today = 0
        self.active_task_title = "Свободная сессия"

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        # Capsule layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.capsule = QFrame()
        self.capsule.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.capsule.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 15px;
                padding: 2px 8px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary_border']};
            }}
        """)
        c_layout = QHBoxLayout(self.capsule)
        c_layout.setContentsMargins(6, 2, 6, 2)
        c_layout.setSpacing(6)

        # Icon / Mode
        self.mode_icon = QLabel()
        self.mode_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 16))
        self.mode_icon.setStyleSheet("background: transparent;")
        c_layout.addWidget(self.mode_icon)

        # Time label
        self.time_lbl = QLabel(self._format_time(self.time_left))
        self.time_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        c_layout.addWidget(self.time_lbl)

        # Play/Pause button
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(get_icon("play", COLORS['primary_light'], 16))
        self.toggle_btn.setIconSize(QSize(16, 16))
        self.toggle_btn.setFixedSize(24, 24)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }}
        """)
        self.toggle_btn.clicked.connect(self.toggle_timer)
        c_layout.addWidget(self.toggle_btn)

        layout.addWidget(self.capsule)

        # Click capsule to open Zen Mode
        self.capsule.mousePressEvent = self._on_capsule_clicked

    def _on_capsule_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_zen_mode()

    def _tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.time_lbl.setText(self._format_time(self.time_left))
        else:
            self.timer.stop()
            self.is_running = False
            self.toggle_btn.setIcon(get_icon("play", COLORS['primary_light'], 16))
            
            # Sound alert (Windows beep) if enabled in settings
            if self.storage.get_setting("sound_alert", True):
                try:
                    ctypes.windll.user32.MessageBeep(0x00000040)
                except Exception:
                    pass

            if self.mode == "focus":
                self.completed_today += 1
                self.session_completed.emit("focus")
                self.mode = "break"
                self.time_left = self.BREAK_TIME
                self.mode_icon.setPixmap(get_pixmap("coffee", COLORS['sky'], 16))
            else:
                self.session_completed.emit("break")
                self.mode = "focus"
                self.time_left = self.FOCUS_TIME
                self.mode_icon.setPixmap(get_pixmap("timer", COLORS['rose'], 16))

            self.time_lbl.setText(self._format_time(self.time_left))

    def toggle_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.toggle_btn.setIcon(get_icon("play", COLORS['primary_light'], 16))
        else:
            self.timer.start()
            self.is_running = True
            self.toggle_btn.setIcon(get_icon("pause", COLORS['primary_light'], 16))

    def start_timer(self):
        if not self.is_running:
            self.toggle_timer()

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.toggle_btn.setIcon(get_icon("play", COLORS['primary_light'], 16))
        self.time_left = self.FOCUS_TIME if self.mode == "focus" else self.BREAK_TIME
        self.time_lbl.setText(self._format_time(self.time_left))

    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def open_zen_mode(self):
        dlg = ZenFocusDialog(self, parent=self.window())
        dlg.exec()


class ZenFocusDialog(QDialog):
    """Distraction-free Fullscreen / Modal Zen Focus Mode."""
    def __init__(self, manager: PomodoroManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Режим глубокого фокуса — WorkBOXig")
        self.setFixedSize(540, 460)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_root']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Top Mode badge
        self.mode_badge = QLabel("СЕССИЯ ФОКУСА" if self.manager.mode == "focus" else "ВРЕМЯ ОТДЫХА")
        self.mode_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.mode_badge.setStyleSheet(f"""
            color: {COLORS['primary_light']};
            background-color: {COLORS['primary_subtle']};
            border: 1px solid {COLORS['primary_border']};
            border-radius: 12px;
            padding: 4px 12px;
        """)
        layout.addWidget(self.mode_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        # Huge Countdown Timer
        self.big_timer_lbl = QLabel(self.manager._format_time(self.manager.time_left))
        self.big_timer_lbl.setFont(QFont("Segoe UI", 56, QFont.Weight.Bold))
        self.big_timer_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 2px;")
        layout.addWidget(self.big_timer_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Current Focus Task Selector
        task_box = QHBoxLayout()
        t_icon = QLabel("Фокус на:")
        t_icon.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        t_icon.setStyleSheet(f"color: {COLORS['text_secondary']};")
        task_box.addWidget(t_icon)

        self.task_selector = QComboBox()
        self.task_selector.addItem("Свободная учебная сессия", None)
        tasks = [t for t in self.manager.storage.get_tasks() if not t.get("completed")]
        for t in tasks:
            self.task_selector.addItem(f"{t.get('title')} ({t.get('subject', 'Общее')})", t["id"])
        
        self.task_selector.setMinimumWidth(260)
        task_box.addWidget(self.task_selector)
        layout.addLayout(task_box)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['emerald']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)

        # Control Buttons
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)
        ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dlg_toggle_btn = QPushButton("Пауза" if self.manager.is_running else "Старт")
        self.dlg_toggle_btn.setIcon(get_icon("pause" if self.manager.is_running else "play", "#FFFFFF", 18))
        self.dlg_toggle_btn.setIconSize(QSize(18, 18))
        self.dlg_toggle_btn.setObjectName("primary-btn")
        self.dlg_toggle_btn.setFixedSize(130, 42)
        self.dlg_toggle_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.dlg_toggle_btn.clicked.connect(self._toggle_from_dialog)
        ctrl_layout.addWidget(self.dlg_toggle_btn)

        reset_btn = QPushButton("Сброс")
        reset_btn.setFixedSize(90, 42)
        reset_btn.clicked.connect(self._reset_from_dialog)
        ctrl_layout.addWidget(reset_btn)

        layout.addLayout(ctrl_layout)

        # Daily Streak / Stats Footer
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_lbl = QLabel(f"Завершено сегодня: {self.manager.completed_today} сессий")
        self.stats_lbl.setFont(QFont("Segoe UI", 10))
        self.stats_lbl.setStyleSheet(f"color: {COLORS['amber']};")
        footer_layout.addWidget(self.stats_lbl)
        layout.addLayout(footer_layout)

        # Sync timer
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(500)
        self.sync_timer.timeout.connect(self._sync_state)
        self.sync_timer.start()

        self._sync_state()

    def _toggle_from_dialog(self):
        self.manager.toggle_timer()
        self._sync_state()

    def _reset_from_dialog(self):
        self.manager.reset_timer()
        self._sync_state()

    def _sync_state(self):
        self.big_timer_lbl.setText(self.manager._format_time(self.manager.time_left))
        is_run = self.manager.is_running
        self.dlg_toggle_btn.setText("Пауза" if is_run else "Старт")
        self.dlg_toggle_btn.setIcon(get_icon("pause" if is_run else "play", "#FFFFFF", 18))
        self.mode_badge.setText("СЕССИЯ ФОКУСА" if self.manager.mode == "focus" else "ВРЕМЯ ОТДЫХА")
        
        total = self.manager.FOCUS_TIME if self.manager.mode == "focus" else self.manager.BREAK_TIME
        done = total - self.manager.time_left
        pct = int((done / total) * 100) if total > 0 else 0
        self.progress.setValue(pct)
        self.stats_lbl.setText(f"Завершено сегодня: {self.manager.completed_today} сессий")

    def closeEvent(self, event):
        self.sync_timer.stop()
        super().closeEvent(event)
