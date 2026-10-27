"""
Dashboard Overview View for WorkBOXig.
Cyber-minimal, high-contrast, glow-accented productivity command center.
Combines daily agenda/lessons, urgent deadlines, quick scratchpad, and key productivity metrics.
"""

from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit, QCheckBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QSize, QTimer
from PyQt6.QtGui import QFont, QCursor
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon
from src.utils.shortcuts import clear_layout
from src.i18n import t, get_i18n, format_lessons, format_tasks, format_days, get_language
from src.components.activity_heatmap import ActivityHeatmapWidget
from src.components.grades_dialog import GradesTrackerWidget, AddGradeDialog, GradesManagementDialog
from src.views.calendar_view import localized_badge


def format_lessons_ru(n: int) -> str:
    return format_lessons(n)


def format_tasks_ru(n: int) -> str:
    return format_tasks(n)


class MetricCard(QFrame):
    """Interactive refined metric summary card."""
    clicked = pyqtSignal(str) # view_id

    def __init__(self, icon_name: str, title: str, subtitle: str, value_str: str,
                 accent_hex: str, glow_rgba: str, target_view: str, parent=None):
        super().__init__(parent)
        self.target_view = target_view
        self.accent_hex = accent_hex
        self.glow_rgba = glow_rgba
        self.icon_name = icon_name
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("metric_card")
        self.setStyleSheet(f"""
            QFrame#metric_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
            QFrame#metric_card:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_light']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Top Row: Icon + Value
        top_row = QHBoxLayout()
        self.icon_box = QLabel()
        self.icon_box.setPixmap(get_pixmap(icon_name, accent_hex, 18))
        self.icon_box.setStyleSheet(f"""
            background-color: {glow_rgba};
            border: 1px solid {accent_hex};
            border-radius: 8px;
            padding: 5px;
        """)
        top_row.addWidget(self.icon_box)

        self.val_lbl = QLabel(value_str)
        self.val_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; padding-left: 8px; background: transparent;")
        top_row.addWidget(self.val_lbl)
        top_row.addStretch()

        # Mini arrow indicator on right
        self.arrow_lbl = QLabel("→")
        self.arrow_lbl.setFont(QFont("Segoe UI", 12))
        self.arrow_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        top_row.addWidget(self.arrow_lbl)

        layout.addLayout(top_row)

        # Title & Subtitle
        self.t_lbl = QLabel(title)
        self.t_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.t_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(self.t_lbl)

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setFont(QFont("Segoe UI", 8))
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(self.sub_lbl)

    def set_value(self, val: str):
        self.val_lbl.setText(val)

    def refresh_theme(self, accent_hex: str = None, glow_rgba: str = None):
        if accent_hex:
            self.accent_hex = accent_hex
        if glow_rgba:
            self.glow_rgba = glow_rgba
        self.setStyleSheet(f"""
            QFrame#metric_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
            QFrame#metric_card:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_light']};
            }}
        """)
        self.val_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; padding-left: 8px; background: transparent;")
        self.t_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self.arrow_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        self.icon_box.setStyleSheet(f"""
            background-color: {self.glow_rgba};
            border: 1px solid {self.accent_hex};
            border-radius: 8px;
            padding: 5px;
        """)
        self.icon_box.setPixmap(get_pixmap(self.icon_name, self.accent_hex, 18))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.target_view)
        super().mousePressEvent(event)


class DashboardView(QWidget):
    """
    Central Command & Overview Dashboard with glowing ambient effects.
    """
    navigate_requested = pyqtSignal(str) # tab_id
    toast_requested = pyqtSignal(str, str) # message, level
    start_pomodoro_requested = pyqtSignal()
    quick_add_task_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.selected_tag = t("metric_tags").split("|")[0]

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.scroll_content = QWidget()
        self.scroll_content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.scroll_content.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self.scroll_content)
        self.main_layout.setContentsMargins(28, 22, 28, 24)
        self.main_layout.setSpacing(16)

        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area)

        self._init_ui()
        self.storage.data_changed.connect(self._refresh_all)
        get_i18n().language_changed.connect(self._on_language_changed)
        self._refresh_all()
        self._last_date = date.today()
        self._day_timer = QTimer(self)
        self._day_timer.timeout.connect(self._refresh_day_if_needed)
        self._day_timer.start(60000)

    def _update_banner_style(self):
        is_dark = (COLORS.get("text_primary", "#FFFFFF") == "#FFFFFF")
        welcome_bg = "#111420" if is_dark else "#FFFFFF"
        welcome_bd = COLORS['border_subtle']
        if hasattr(self, "welcome_frame"):
            self.welcome_frame.setStyleSheet(f"""
                QFrame#welcome_frame {{
                    background-color: {welcome_bg};
                    border: 1px solid {welcome_bd};
                    border-radius: 12px;
                }}
            """)

    def _init_ui(self):
        # 1. Welcome Greeting Banner
        self.welcome_frame = QFrame()
        self.welcome_frame.setObjectName("welcome_frame")
        self._update_banner_style()

        w_layout = QHBoxLayout(self.welcome_frame)
        w_layout.setContentsMargins(24, 20, 24, 20)
        w_layout.setSpacing(20)

        # Left Info Stack
        g_layout = QVBoxLayout()
        g_layout.setSpacing(6)

        now = datetime.now()
        greeting_text = t("welcome_msg")
        if 5 <= now.hour < 12:
            greeting_text = t("good_morning")
        elif 12 <= now.hour < 18:
            greeting_text = t("good_afternoon")
        elif 18 <= now.hour < 23:
            greeting_text = t("good_evening")
        else:
            greeting_text = t("good_night")

        self.greeting_lbl = QLabel(greeting_text)
        self.greeting_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.greeting_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        g_layout.addWidget(self.greeting_lbl)

        self.summary_lbl = QLabel(t("loading_status"))
        self.summary_lbl.setFont(QFont("Segoe UI", 10))
        self.summary_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        self.summary_lbl.setWordWrap(True)
        g_layout.addWidget(self.summary_lbl)

        # Quick Actions Row inside Banner
        banner_actions = QHBoxLayout()
        banner_actions.setSpacing(10)
        banner_actions.setContentsMargins(0, 6, 0, 0)

        is_cyber = (COLORS.get('primary') == '#FCEE0A')
        btn_fg = '#000000' if is_cyber else '#FFFFFF'

        self.focus_btn = QPushButton(t("start_focus_btn"))
        self.focus_btn.setIcon(get_icon("play", btn_fg, 16))
        self.focus_btn.setIconSize(QSize(16, 16))
        self.focus_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.focus_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {btn_fg};
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.focus_btn.clicked.connect(self._on_start_focus_clicked)
        banner_actions.addWidget(self.focus_btn)

        self.add_t_btn = QPushButton(t("btn_new_task"))
        self.add_t_btn.setIcon(get_icon("plus", COLORS['text_secondary'], 16))
        self.add_t_btn.setIconSize(QSize(16, 16))
        self.add_t_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_t_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['border_light']};
            }}
        """)
        self.add_t_btn.clicked.connect(self.quick_add_task_requested.emit)
        banner_actions.addWidget(self.add_t_btn)

        self.add_l_btn = QPushButton(t("nav_calendar"))
        self.add_l_btn.setIcon(get_icon("calendar", COLORS['text_secondary'], 16))
        self.add_l_btn.setIconSize(QSize(16, 16))
        self.add_l_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_l_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['border_light']};
            }}
        """)
        self.add_l_btn.clicked.connect(lambda: self.navigate_requested.emit("calendar"))
        banner_actions.addWidget(self.add_l_btn)

        banner_actions.addStretch()
        g_layout.addLayout(banner_actions)
        w_layout.addLayout(g_layout, stretch=1)

        # Right Date & Streak Card
        self.date_card = QFrame()
        self.date_card.setObjectName("date_card")
        self.date_card.setFixedWidth(200)
        self.date_card.setStyleSheet(f"""
            QFrame#date_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        dc_layout = QVBoxLayout(self.date_card)
        dc_layout.setContentsMargins(12, 10, 12, 10)
        dc_layout.setSpacing(4)
        dc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from src.i18n import get_language
        if get_language() == "en":
            months_en = ["", "January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
            days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_str = f"{months_en[now.month]} {now.day}"
            weekday_str = days_en[now.weekday()]
        else:
            months_ru = ["", "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
                         "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"]
            days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            day_str = f"{now.day} {months_ru[now.month]}"
            weekday_str = days_ru[now.weekday()]

        self.date_big = QLabel(day_str)
        self.date_big.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.date_big.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.date_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dc_layout.addWidget(self.date_big)

        self.date_sub = QLabel(f"{weekday_str} • {now.year}")
        self.date_sub.setFont(QFont("Segoe UI", 9))
        self.date_sub.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent;")
        self.date_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dc_layout.addWidget(self.date_sub)

        w_layout.addWidget(self.date_card)
        self.main_layout.addWidget(self.welcome_frame)

        # 2. Metrics 4-Card Grid with Glowing Borders
        self.metrics_container = QWidget(self)
        metrics_grid = QGridLayout(self.metrics_container)
        metrics_grid.setSpacing(14)

        self.card_today_tasks = MetricCard(
            "zap", t("metric_today_title"), t("metric_today_sub"), "0",
            COLORS['amber'], "rgba(245, 158, 11, 0.16)", "tasks"
        )
        self.card_today_tasks.clicked.connect(self.navigate_requested)
        metrics_grid.addWidget(self.card_today_tasks, 0, 0)

        self.card_events = MetricCard(
            "calendar", t("metric_events_title"), t("metric_events_sub"), "0",
            COLORS['sky'], "rgba(56, 189, 248, 0.16)", "calendar"
        )
        self.card_events.clicked.connect(self.navigate_requested)
        metrics_grid.addWidget(self.card_events, 0, 1)

        self.card_notebooks = MetricCard(
            "notebooks", t("metric_notebooks_title"), t("metric_notebooks_sub"), "0",
            COLORS['emerald'], "rgba(16, 185, 129, 0.16)", "notebooks"
        )
        self.card_notebooks.clicked.connect(self.navigate_requested)
        metrics_grid.addWidget(self.card_notebooks, 0, 2)

        self.card_notes = MetricCard(
            "notes", t("metric_notes_title"), t("metric_quick_notes_sub"), "0",
            COLORS['purple'], "rgba(168, 85, 247, 0.16)", "notes"
        )
        self.card_notes.clicked.connect(self.navigate_requested)
        metrics_grid.addWidget(self.card_notes, 0, 3)

        self.metrics_container.hide()

        # 3. Three-Column Main Working Area
        work_layout = QHBoxLayout()
        work_layout.setSpacing(16)

        # Col 1: Today's Schedule & Lessons
        self.sched_box = QFrame()
        self.sched_box.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.sched_box.setObjectName("sched_box")
        self.sched_box.setStyleSheet(f"""
            QFrame#sched_box {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        sb_layout = QVBoxLayout(self.sched_box)
        sb_layout.setContentsMargins(16, 14, 16, 14)
        sb_layout.setSpacing(10)

        sb_header = QHBoxLayout()
        self.sc_icon = QLabel()
        self.sc_icon.setPixmap(get_pixmap("calendar", COLORS['sky'], 16))
        sb_header.addWidget(self.sc_icon)

        self.sc_title = QLabel(t("section_today_schedule"))
        self.sc_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.sc_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        sb_header.addWidget(self.sc_title)

        self.sched_badge_lbl = QLabel("")
        self.sched_badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.sched_badge_lbl.setStyleSheet(f"""
            color: {COLORS['sky']};
            background-color: {COLORS['sky_subtle']};
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 8px;
            padding: 1px 7px;
        """)
        sb_header.addWidget(self.sched_badge_lbl)
        sb_header.addStretch()

        view_cal_btn = QPushButton(t("view_all_schedule"))
        view_cal_btn.setObjectName("ghost-btn")
        view_cal_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_cal_btn.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent; border: none; font-size: 11px;")
        view_cal_btn.clicked.connect(lambda: self.navigate_requested.emit("calendar"))
        sb_header.addWidget(view_cal_btn)
        sb_layout.addLayout(sb_header)

        # Scroll for schedule
        self.today_sched_scroll = QScrollArea()
        self.today_sched_scroll.setWidgetResizable(True)
        self.today_sched_scroll.setStyleSheet("background: transparent; border: none;")

        self.sched_container = QWidget()
        self.sched_container.setStyleSheet("background: transparent;")
        self.today_sched_layout = QVBoxLayout(self.sched_container)
        self.today_sched_layout.setContentsMargins(0, 4, 0, 4)
        self.today_sched_layout.setSpacing(8)
        self.today_sched_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.today_sched_scroll.setWidget(self.sched_container)
        sb_layout.addWidget(self.today_sched_scroll, stretch=1)
        work_layout.addWidget(self.sched_box, stretch=4)

        # Col 2: Today's Tasks Interactive List
        self.left_box = QFrame()
        self.left_box.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.left_box.setObjectName("left_box")
        self.left_box.setStyleSheet(f"""
            QFrame#left_box {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        lb_layout = QVBoxLayout(self.left_box)
        lb_layout.setContentsMargins(16, 14, 16, 14)
        lb_layout.setSpacing(10)

        lb_header = QHBoxLayout()
        self.h_icon = QLabel()
        self.h_icon.setPixmap(get_pixmap("tasks", COLORS['primary_light'], 16))
        lb_header.addWidget(self.h_icon)

        self.t_title = QLabel(t("today_tasks_title"))
        self.t_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.t_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        lb_header.addWidget(self.t_title)

        self.task_badge_lbl = QLabel("")
        self.task_badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.task_badge_lbl.setStyleSheet(f"""
            color: {COLORS['primary_light']};
            background-color: {COLORS['primary_subtle']};
            border: 1px solid {COLORS['primary_border']};
            border-radius: 8px;
            padding: 1px 7px;
        """)
        lb_header.addWidget(self.task_badge_lbl)
        lb_header.addStretch()

        view_all_btn = QPushButton(t("view_all_tasks"))
        view_all_btn.setObjectName("ghost-btn")
        view_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_all_btn.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent; border: none; font-size: 11px;")
        view_all_btn.clicked.connect(lambda: self.navigate_requested.emit("tasks"))
        lb_header.addWidget(view_all_btn)
        lb_layout.addLayout(lb_header)

        # Scroll for today tasks
        self.today_tasks_scroll = QScrollArea()
        self.today_tasks_scroll.setWidgetResizable(True)
        self.today_tasks_scroll.setStyleSheet("background: transparent; border: none;")

        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.today_tasks_layout = QVBoxLayout(self.tasks_container)
        self.today_tasks_layout.setContentsMargins(0, 4, 0, 4)
        self.today_tasks_layout.setSpacing(8)
        self.today_tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.today_tasks_scroll.setWidget(self.tasks_container)
        lb_layout.addWidget(self.today_tasks_scroll, stretch=1)
        work_layout.addWidget(self.left_box, stretch=4)

        # Col 3: Quick Thought Scratchpad
        self.right_box = QFrame()
        self.right_box.setObjectName("right_box")
        self.right_box.setStyleSheet(f"""
            QFrame#right_box {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        rb_layout = QVBoxLayout(self.right_box)
        rb_layout.setContentsMargins(16, 14, 16, 14)
        rb_layout.setSpacing(10)

        rb_header = QHBoxLayout()
        self.th_icon = QLabel()
        self.th_icon.setPixmap(get_pixmap("zap", COLORS['amber'], 16))
        rb_header.addWidget(self.th_icon)

        self.rb_title = QLabel(t("section_quick_note"))
        self.rb_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.rb_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        rb_header.addWidget(self.rb_title)
        rb_header.addStretch()
        rb_layout.addLayout(rb_header)

        self.rb_desc = QLabel(t("quick_note_desc"))
        self.rb_desc.setFont(QFont("Segoe UI", 9))
        self.rb_desc.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        rb_layout.addWidget(self.rb_desc)

        self.quick_note_title = QLineEdit()
        self.quick_note_title.setPlaceholderText(t("quick_note_title_ph"))
        rb_layout.addWidget(self.quick_note_title)

        # Quick Tag Chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)

        self.tag_chips = []
        for tag_name in t("metric_tags").split("|"):
            chip_btn = QPushButton(f"#{tag_name}")
            chip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            chip_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_muted']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 6px;
                    padding: 3px 8px;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    color: {COLORS['primary_light']};
                    border-color: {COLORS['primary_border']};
                }}
            """)
            chip_btn.clicked.connect(lambda ch, tag=tag_name: self._apply_tag_chip(tag))
            chips_row.addWidget(chip_btn)
            self.tag_chips.append(chip_btn)

        chips_row.addStretch()
        rb_layout.addLayout(chips_row)

        self.quick_note_body = QTextEdit()
        self.quick_note_body.setPlaceholderText(t("quick_note_placeholder"))
        rb_layout.addWidget(self.quick_note_body, stretch=1)

        self.quick_save_btn = QPushButton(t("quick_note_save"))
        self.quick_save_btn.setIcon(get_icon("notes", btn_fg, 16))
        self.quick_save_btn.setIconSize(QSize(16, 16))
        self.quick_save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.quick_save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {btn_fg};
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.quick_save_btn.clicked.connect(self._save_quick_note)
        rb_layout.addWidget(self.quick_save_btn)

        self.right_box.hide()
        self.right_box.setMinimumHeight(260)
        self.sched_box.setMinimumHeight(330)
        self.left_box.setMinimumHeight(330)
        self.main_layout.addLayout(work_layout)

        self.more_btn = QPushButton(t("today_more"))
        self.more_btn.setCheckable(True)
        self.more_btn.toggled.connect(self._toggle_extras)
        self.main_layout.addWidget(self.more_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.right_box)

        # 4. Sprint 2: Analytics Row (Activity Heatmap + Subject Focus & Grades / GPA Tracker)
        self.analytics_container = QWidget()
        self.analytics_row = QHBoxLayout(self.analytics_container)
        self.analytics_row.setContentsMargins(0, 0, 0, 0)
        self.analytics_row.setSpacing(16)

        self.heatmap_widget = ActivityHeatmapWidget(self.storage, self)
        self.analytics_row.addWidget(self.heatmap_widget, stretch=3)

        self.grades_widget = GradesTrackerWidget(self.storage, self)
        self.grades_widget.grade_added.connect(lambda: self.toast_requested.emit(t("grade_added_toast"), "success"))
        self.analytics_row.addWidget(self.grades_widget, stretch=2)

        self.main_layout.addWidget(self.analytics_container)
        self.analytics_container.hide()

    def _toggle_extras(self, visible):
        self.right_box.setVisible(visible)
        self.analytics_container.setVisible(visible)
        self.more_btn.setText(t("today_less" if visible else "today_more"))

    def _refresh_day_if_needed(self):
        if date.today() != self._last_date:
            self._last_date = date.today()
            self._update_date_card_text()
            self._refresh_all()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_day_if_needed()

    def _apply_tag_chip(self, tag: str):
        self.selected_tag = tag
        current = self.quick_note_title.text().strip()
        if not current:
            self.quick_note_title.setText(f"[{tag.capitalize()}] ")
            self.quick_note_title.setFocus()

    def _on_start_focus_clicked(self):
        self.start_pomodoro_requested.emit()
        self.toast_requested.emit(t("focus_started"), "info")

    def refresh_theme(self):
        self._update_banner_style()
        if hasattr(self, "greeting_lbl"):
            self.greeting_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        if hasattr(self, "summary_lbl"):
            self.summary_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        if hasattr(self, "date_card"):
            self.date_card.setStyleSheet(f"""
                QFrame#date_card {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 12px;
                    padding: 12px;
                }}
            """)
            self.date_big.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            self.date_sub.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent;")

        cards = [
            (getattr(self, "card_today_tasks", None), COLORS['amber'], COLORS['amber_subtle']),
            (getattr(self, "card_events", None), COLORS['sky'], COLORS['sky_subtle']),
            (getattr(self, "card_notebooks", None), COLORS['emerald'], COLORS['emerald_subtle']),
            (getattr(self, "card_notes", None), COLORS['purple'], COLORS['purple_subtle']),
        ]
        for card, hex_c, rgba_c in cards:
            if card:
                card.refresh_theme(hex_c, rgba_c)

        for box in [getattr(self, "sched_box", None), getattr(self, "left_box", None), getattr(self, "right_box", None)]:
            if box:
                box.setStyleSheet(f"""
                    QFrame#{box.objectName()} {{
                        background-color: {COLORS['bg_card']};
                        border: 1px solid {COLORS['border_subtle']};
                        border-radius: 12px;
                    }}
                """)

        if hasattr(self, "add_t_btn"):
            btn_style = f"""
                QPushButton {{
                    background-color: {COLORS['bg_card']};
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card_hover']};
                    color: {COLORS['text_primary']};
                    border-color: {COLORS['border_light']};
                }}
            """
            self.add_t_btn.setStyleSheet(btn_style)
            self.add_l_btn.setStyleSheet(btn_style)
            self.add_t_btn.setIcon(get_icon("plus", COLORS['text_secondary'], 16))
            self.add_l_btn.setIcon(get_icon("calendar", COLORS['text_secondary'], 16))

        if hasattr(self, "sc_title"):
            self.sc_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            self.t_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            self.rb_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            self.rb_desc.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            self.sc_icon.setPixmap(get_pixmap("calendar", COLORS['sky'], 16))
            self.h_icon.setPixmap(get_pixmap("tasks", COLORS['primary_light'], 16))
            self.th_icon.setPixmap(get_pixmap("zap", COLORS['amber'], 16))

        is_cyber = (COLORS.get('primary') == '#FCEE0A')
        btn_fg = '#000000' if is_cyber else '#FFFFFF'
        if hasattr(self, "focus_btn"):
            self.focus_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: {btn_fg};
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_hover']};
                }}
            """)
            self.focus_btn.setIcon(get_icon("play", btn_fg, 16))

        if hasattr(self, "quick_save_btn"):
            self.quick_save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: {btn_fg};
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_hover']};
                }}
            """)
            self.quick_save_btn.setIcon(get_icon("notes", btn_fg, 16))

        if hasattr(self, "heatmap_widget"):
            self.heatmap_widget.refresh_data()
        if hasattr(self, "grades_widget"):
            self.grades_widget.refresh_data()

        self._refresh_all()

    def _refresh_all(self):
        tasks = self.storage.get_tasks()
        notebooks = self.storage.get_notebooks()
        notes = self.storage.get_notes()
        events = self.storage.get_events()

        today = date.today()
        today_iso = today.isoformat()
        parity = "even" if today.isocalendar().week % 2 == 0 else "odd"
        matches_week = lambda item: item.get("week_parity", "all") in ("all", parity, "", None)
        today_events = [e for e in events if e.get("date") == today_iso and matches_week(e)]
        today_events.extend(e for e in self.storage.get_recurring_lessons()
                            if e.get("weekday") == today.weekday() and matches_week(e))

        def task_date(task):
            try:
                return date.fromisoformat(task.get("due_date") or "")
            except (TypeError, ValueError):
                return None

        pending = [task for task in tasks if not task.get("completed")]
        overdue = [task for task in pending if task_date(task) and task_date(task) < today]
        due_today = [task for task in pending if task_date(task) == today]
        order = lambda item: (item.get("due_date") or "", item.get("due_time") or "", item.get("title") or "")
        overdue.sort(key=order)
        due_today.sort(key=order)

        # Update metric cards
        self.card_today_tasks.set_value(str(len(due_today) + len(overdue)))
        self.card_events.set_value(str(len(today_events)))
        self.card_notebooks.set_value(str(len(notebooks)))
        self.card_notes.set_value(str(len(notes)))

        # Update summary text
        self.task_badge_lbl.setText(str(len(due_today) + len(overdue)))
        self.sched_badge_lbl.setText(format_lessons_ru(len(today_events)))
        
        if hasattr(self, "heatmap_widget"):
            self.heatmap_widget.refresh_data()
        if hasattr(self, "grades_widget"):
            self.grades_widget.refresh_data()

        self.summary_lbl.setText(t("today_summary", events=len(today_events), today=len(due_today), overdue=len(overdue)))

        # 1. Update Today's Schedule List
        clear_layout(self.today_sched_layout)

        if today_events:
            sorted_events = sorted(today_events, key=lambda x: x.get("time", "99:99"))
            for ev in sorted_events:
                ev_card = QFrame()
                ev_card.setObjectName("today_event_card")
                col = ev.get("color", COLORS['primary_light'])
                ev_card.setStyleSheet(f"""
                    QFrame#today_event_card {{
                        background-color: {COLORS['bg_input']};
                        border: 1px solid {COLORS['border_subtle']};
                        border-left: 3px solid {col};
                        border-radius: 8px;
                        padding: 6px 10px;
                    }}
                    QFrame#today_event_card:hover {{
                        border-color: {COLORS['border_light']};
                        background-color: {COLORS['bg_card_hover']};
                    }}
                """)
                ec_layout = QVBoxLayout(ev_card)
                ec_layout.setContentsMargins(6, 6, 6, 6)
                ec_layout.setSpacing(4)

                top_row = QHBoxLayout()
                t_lbl = QLabel(f"{ev.get('time', '')} - {ev.get('end_time', '')}")
                t_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                t_lbl.setStyleSheet(f"color: {col};")
                top_row.addWidget(t_lbl)

                top_row.addStretch()

                if ev.get("badge"):
                    b_lbl = QLabel(localized_badge(ev.get("badge")))
                    b_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    b_lbl.setStyleSheet(f"""
                        color: {col};
                        background-color: rgba(255, 255, 255, 0.06);
                        border-radius: 4px;
                        padding: 1px 5px;
                    """)
                    top_row.addWidget(b_lbl)

                ec_layout.addLayout(top_row)

                subj_lbl = QLabel(ev.get("title", ""))
                subj_lbl.setWordWrap(True)
                subj_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                subj_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
                ec_layout.addWidget(subj_lbl)

                if ev.get("description") or ev.get("room"):
                    info_text = f"{ev.get('room', '')} • {ev.get('description', '')}".strip(" •")
                    sub_lbl = QLabel(info_text)
                    sub_lbl.setFont(QFont("Segoe UI", 8))
                    sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
                    ec_layout.addWidget(sub_lbl)

                self.today_sched_layout.addWidget(ev_card)
        else:
            # If no lessons today, show friendly empty state
            empty_sched = QFrame()
            empty_sched.setStyleSheet("background: transparent;")
            es_layout = QVBoxLayout(empty_sched)
            es_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            es_layout.setSpacing(8)

            es_msg = QLabel(t("no_classes_today"))
            es_msg.setFont(QFont("Segoe UI", 10))
            es_msg.setStyleSheet(f"color: {COLORS['text_muted']};")
            es_layout.addWidget(es_msg)

            add_btn = QPushButton(t("btn_add_event"))
            add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            add_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(99, 102, 241, 0.15);
                    color: {COLORS['primary_light']};
                    border: 1px solid {COLORS['primary_border']};
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: rgba(99, 102, 241, 0.25);
                }}
            """)
            add_btn.clicked.connect(lambda: self.navigate_requested.emit("calendar"))
            es_layout.addWidget(add_btn)

            self.today_sched_layout.addWidget(empty_sched)

        # 2. Update Today Tasks list
        clear_layout(self.today_tasks_layout)

        if not overdue and not due_today:
            empty_lbl = QLabel(t("today_no_tasks"))
            empty_lbl.setFont(QFont("Segoe UI", 10))
            empty_lbl.setStyleSheet(f"color: {COLORS['emerald']}; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setWordWrap(True)
            self.today_tasks_layout.addWidget(empty_lbl)
            return

        priority_colors = {
            "urgent": COLORS['rose'],
            "high": COLORS['amber'],
            "medium": COLORS['sky'],
            "low": COLORS['emerald'],
        }

        for task_card in overdue + due_today:
            group = "overdue" if task_card in overdue else "today"
            if task_card is (overdue[0] if group == "overdue" else due_today[0]):
                group_label = QLabel(t("today_overdue" if group == "overdue" else "today_due"))
                group_label.setObjectName(f"today_group_{group}")
                group_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
                group_label.setStyleSheet(f"color: {COLORS['rose'] if group == 'overdue' else COLORS['text_secondary']};")
                self.today_tasks_layout.addWidget(group_label)
            prio = task_card.get("priority", "medium")
            p_color = COLORS['rose'] if group == "overdue" else priority_colors.get(prio, COLORS['primary_light'])

            row = QFrame()
            row.setObjectName("task_row")
            row.setStyleSheet(f"""
                QFrame#task_row {{
                    background-color: {COLORS['bg_input']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-left: 3px solid {p_color};
                    border-radius: 8px;
                    padding: 8px 10px;
                }}
                QFrame#task_row:hover {{
                    border-color: {COLORS['border_light']};
                    background-color: {COLORS['bg_card_hover']};
                }}
            """)
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(6, 6, 6, 6)
            r_layout.setSpacing(10)

            cb = QCheckBox()
            cb.setChecked(False)
            cb.setAccessibleName(task_card.get("title", ""))
            cb.toggled.connect(lambda checked, tid=task_card["id"]: self._toggle_task(tid))
            r_layout.addWidget(cb)

            t_lbl = QLabel(task_card.get("title", ""))
            t_lbl.setWordWrap(True)
            t_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            t_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            t_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            r_layout.addWidget(t_lbl, stretch=1)

            # Subject chip
            if task_card.get("subject"):
                subj_lbl = QLabel(task_card.get("subject"))
                subj_lbl.setFont(QFont("Segoe UI", 8))
                subj_lbl.setStyleSheet(f"""
                    color: {COLORS['text_muted']};
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 4px;
                    padding: 2px 6px;
                """)
                r_layout.addWidget(subj_lbl)

            d_lbl = QLabel(task_card.get('due_date', '') if group == "overdue" else (task_card.get('due_time') or ''))
            d_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
            d_lbl.setStyleSheet(f"color: {COLORS['amber'] if task_card.get('due_date') == today_iso else COLORS['text_muted']};")
            r_layout.addWidget(d_lbl)

            self.today_tasks_layout.addWidget(row)

    def _toggle_task(self, task_id: str):
        self.storage.toggle_task(task_id)
        self.toast_requested.emit(t("task_marked_done"), "success")

    def _save_quick_note(self):
        title = self.quick_note_title.text().strip() or t("quick_thought_default")
        body = self.quick_note_body.toPlainText().strip()
        if not body:
            self.quick_note_body.setFocus()
            return

        tags = [self.selected_tag, t("quick_thought_default").lower()] if self.selected_tag else [t("quick_thought_default").lower()]
        self.storage.add_note(title=title, content=body, color=COLORS['primary'], tags=tags)
        self.quick_note_title.clear()
        self.quick_note_body.clear()
        self.toast_requested.emit(t("note_saved_toast"), "success")
        self._refresh_all()

    def _update_date_card_text(self):
        now = datetime.now()
        from src.i18n import get_language
        if get_language() == "en":
            months_en = ["", "January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
            days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_str = f"{months_en[now.month]} {now.day}"
            weekday_str = days_en[now.weekday()]
        else:
            months_ru = ["", "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
                         "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"]
            days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            day_str = f"{now.day} {months_ru[now.month]}"
            weekday_str = days_ru[now.weekday()]

        if hasattr(self, "date_big"):
            self.date_big.setText(day_str)
        if hasattr(self, "date_sub"):
            self.date_sub.setText(f"{weekday_str} • {now.year}")

    def _on_language_changed(self, _lang=None):
        self._update_date_card_text()
        self.t_title.setText(t("today_tasks_title"))
        self.more_btn.setText(t("today_less" if self.more_btn.isChecked() else "today_more"))
        if hasattr(self, "card_today_tasks"):
            self.card_today_tasks.t_lbl.setText(t("metric_today_title"))
            self.card_today_tasks.sub_lbl.setText(t("metric_today_sub"))
        if hasattr(self, "card_events"):
            self.card_events.t_lbl.setText(t("metric_events_title"))
            self.card_events.sub_lbl.setText(t("metric_events_sub"))
        if hasattr(self, "card_notebooks"):
            self.card_notebooks.t_lbl.setText(t("metric_notebooks_title"))
            self.card_notebooks.sub_lbl.setText(t("metric_notebooks_sub"))
        if hasattr(self, "card_notes"):
            self.card_notes.t_lbl.setText(t("metric_notes_title"))
            self.card_notes.sub_lbl.setText(t("metric_quick_notes_sub"))
        for chip, tag in zip(getattr(self, "tag_chips", []), t("metric_tags").split("|")):
            chip.setText(f"#{tag}")
        self.selected_tag = t("metric_tags").split("|")[0]
        if hasattr(self, "streak_chip"):
            self.streak_chip.setText(t("streak_format", count=3))
        self._refresh_all()
