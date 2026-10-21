"""
Calendar & Weekly Timetable View for WorkBOXig.
Full interactive school/university weekly timetable grid by hour slots,
custom color-coded subjects/lessons, current-time indicator line,
and dual-mode (Weekly Timetable / Monthly Grid).
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QFrame, QScrollArea, QDialog, QLineEdit,
    QComboBox, QTextEdit, QTimeEdit, QDateEdit, QMessageBox, QCheckBox,
    QGridLayout, QStackedWidget, QButtonGroup, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QTimer, QSize, QRectF
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QCursor, QPainter, QPen, QBrush, QFontMetrics
from src.styles import COLORS
from src.storage import get_storage
from src.views.tasks_view import TaskDialog
from src.icons import get_pixmap, get_icon
from src.utils.shortcuts import clear_layout
from src.i18n import t, get_language
from src.components.google_sync_dialog import GoogleSyncDialog


COLOR_PALETTE = [
    ("#8B5CF6", "Фиолетовый"),
    ("#3B82F6", "Синий"),
    ("#38BDF8", "Голубой"),
    ("#10B981", "Изумрудный"),
    ("#F59E0B", "Янтарный"),
    ("#EC4899", "Розовый"),
    ("#F43F5E", "Коралловый"),
    ("#6366F1", "Индиго"),
]

SUBJECT_PRESETS = [
    ("Русский язык", "#8B5CF6"),
    ("Литература", "#EC4899"),
    ("Алгебра", "#38BDF8"),
    ("Геометрия", "#38BDF8"),
    ("Информатика", "#6366F1"),
    ("Физика", "#F43F5E"),
    ("Химия", "#06B6D4"),
    ("Биология", "#10B981"),
    ("Английский язык", "#6366F1"),
    ("История", "#F59E0B"),
    ("Обществознание", "#10B981"),
    ("Физкультура", "#A855F7"),
]


def hex_to_rgba(hex_color: str, alpha: float = 0.22) -> str:
    """Convert hex color string to rgba CSS string."""
    h = hex_color.lstrip('#')
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    return f"rgba(99, 102, 241, {alpha})"


class AddLessonDialog(QDialog):
    """
    Dialog to create or edit a lesson, seminar, lecture, or scheduled task.
    """
    def __init__(self, preset_date: Optional[QDate] = None, preset_hour: int = 9,
                 existing_event: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.existing_event = existing_event
        self.setWindowTitle(t("cal_edit_title") if existing_event else t("cal_new_title"))
        self.setFixedSize(540, 680)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(10)

        # Header
        header_l = QHBoxLayout()
        header_l.setSpacing(8)
        c_ic = QLabel()
        c_ic.setPixmap(get_pixmap("calendar", COLORS['primary_light'], 22))
        header_l.addWidget(c_ic)

        title_text = t("cal_edit_title") if existing_event else t("cal_new_title")
        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_l.addWidget(title_lbl)
        header_l.addStretch()
        layout.addLayout(header_l)

        # Quick Subject preset chips
        preset_lbl = QLabel(t("cal_presets_lbl"))
        preset_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
        preset_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; margin-top: 2px;")
        layout.addWidget(preset_lbl)

        presets_scroll = QScrollArea()
        presets_scroll.setFixedHeight(36)
        presets_scroll.setWidgetResizable(True)
        presets_scroll.setStyleSheet("background: transparent; border: none;")
        presets_container = QWidget()
        presets_container.setStyleSheet("background: transparent;")
        presets_layout = QHBoxLayout(presets_container)
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setSpacing(6)

        for subj_name, col in SUBJECT_PRESETS:
            p_btn = QPushButton(subj_name)
            p_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            p_btn.setFixedHeight(30)
            p_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-left: 3px solid {col};
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    border-color: {col};
                    color: {COLORS['text_primary']};
                }}
            """)
            p_btn.clicked.connect(lambda ch, s=subj_name, c=col: self._apply_preset(s, c))
            presets_layout.addWidget(p_btn)

        presets_layout.addStretch()
        presets_scroll.setWidget(presets_container)
        layout.addWidget(presets_scroll)

        # Subject Title
        lbl_subj = QLabel(t("cal_subj_lbl"))
        lbl_subj.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_subj.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_subj)

        self.title_input = QLineEdit()
        self.title_input.setFixedHeight(38)
        self.title_input.setPlaceholderText(t("cal_subj_ph"))
        layout.addWidget(self.title_input)

        # Topic / Description
        lbl_desc = QLabel(t("cal_desc_lbl"))
        lbl_desc.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_desc)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(t("cal_desc_ph"))
        self.desc_input.setFixedHeight(64)
        layout.addWidget(self.desc_input)

        # Date & Badge Type Row
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        date_col = QVBoxLayout()
        date_col.setSpacing(4)
        lbl_date = QLabel(t("cal_date_lbl"))
        lbl_date.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_date.setStyleSheet(f"color: {COLORS['text_secondary']};")
        date_col.addWidget(lbl_date)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setFixedHeight(38)
        init_date = preset_date or QDate.currentDate()
        self.date_input.setDate(init_date)
        date_col.addWidget(self.date_input)
        row1.addLayout(date_col, stretch=1)

        badge_col = QVBoxLayout()
        badge_col.setSpacing(4)
        lbl_badge = QLabel(t("cal_type_lbl"))
        lbl_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_badge.setStyleSheet(f"color: {COLORS['text_secondary']};")
        badge_col.addWidget(lbl_badge)

        self.badge_combo = QComboBox()
        self.badge_combo.setFixedHeight(38)
        self.badge_combo.addItems(["Урок", "Запись урока", "Задание", "Онлайн", "Репетитор", "Семинар / Практика", "Экзамен / Зачет", "Секция / Клуб"])
        badge_col.addWidget(self.badge_combo)
        row1.addLayout(badge_col, stretch=1)

        layout.addLayout(row1)

        # Time range (Start - End)
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        start_col = QVBoxLayout()
        start_col.setSpacing(4)
        lbl_start = QLabel(t("cal_start_lbl"))
        lbl_start.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_start.setStyleSheet(f"color: {COLORS['text_secondary']};")
        start_col.addWidget(lbl_start)

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setFixedHeight(38)
        self.start_time.setTime(QTime(preset_hour, 0))
        start_col.addWidget(self.start_time)
        row2.addLayout(start_col, stretch=1)

        end_col = QVBoxLayout()
        end_col.setSpacing(4)
        lbl_end = QLabel(t("cal_end_lbl"))
        lbl_end.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_end.setStyleSheet(f"color: {COLORS['text_secondary']};")
        end_col.addWidget(lbl_end)

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setFixedHeight(38)
        self.end_time.setTime(QTime(preset_hour + 1, 30 if preset_hour < 22 else 0))
        end_col.addWidget(self.end_time)
        row2.addLayout(end_col, stretch=1)

        layout.addLayout(row2)

        # Room / Link
        lbl_room = QLabel(t("cal_room_lbl"))
        lbl_room.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_room.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_room)

        self.room_input = QLineEdit()
        self.room_input.setFixedHeight(38)
        self.room_input.setPlaceholderText(t("cal_room_ph"))
        layout.addWidget(self.room_input)

        # Color Palette Picker
        lbl_col = QLabel(t("cal_color_lbl"))
        lbl_col.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        lbl_col.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_col)

        color_layout = QHBoxLayout()
        color_layout.setSpacing(10)
        self.color_group = QButtonGroup(self)
        self.selected_color = COLOR_PALETTE[0][0]

        for hex_code, color_name in COLOR_PALETTE:
            c_btn = QPushButton()
            c_btn.setFixedSize(28, 28)
            c_btn.setCheckable(True)
            c_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            c_btn.setToolTip(color_name)
            c_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:checked {{
                    border: 2px solid #FFFFFF;
                }}
            """)
            c_btn.clicked.connect(lambda ch, c=hex_code: self._set_color(c))
            self.color_group.addButton(c_btn)
            color_layout.addWidget(c_btn)
            if hex_code == self.selected_color:
                c_btn.setChecked(True)

        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Populate if editing
        if existing_event:
            self.title_input.setText(existing_event.get("title", ""))
            self.desc_input.setText(existing_event.get("description", ""))
            d_val = existing_event.get("date", init_date.toString(Qt.DateFormat.ISODate))
            try:
                self.date_input.setDate(QDate.fromString(d_val, Qt.DateFormat.ISODate))
            except Exception:
                pass
            self.room_input.setText(existing_event.get("room", ""))
            t_str = existing_event.get("time", "10:00")
            e_str = existing_event.get("end_time", "11:30")
            try:
                self.start_time.setTime(QTime.fromString(t_str, "HH:mm"))
                self.end_time.setTime(QTime.fromString(e_str, "HH:mm"))
            except Exception:
                pass
            c_val = existing_event.get("color", COLOR_PALETTE[0][0])
            self._set_color(c_val)
            for btn in self.color_group.buttons():
                if btn.toolTip() == c_val:
                    btn.setChecked(True)
            b_val = existing_event.get("badge", "Урок")
            idx = self.badge_combo.findText(b_val)
            if idx >= 0:
                self.badge_combo.setCurrentIndex(idx)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setObjectName("ghost-btn")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(t("cal_save_btn") if not existing_event else t("cal_update_btn"))
        save_btn.setObjectName("primary-btn")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._on_save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _set_color(self, hex_color: str):
        self.selected_color = hex_color

    def _apply_preset(self, subject_name: str, color: str):
        self.title_input.setText(subject_name)
        self.selected_color = color
        for btn in self.color_group.buttons():
            # Check button by color
            btn.setChecked(btn.styleSheet().find(color) != -1)

    def _on_save(self):
        if not self.title_input.text().strip():
            self.title_input.setFocus()
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "date": self.date_input.date().toString(Qt.DateFormat.ISODate),
            "time": self.start_time.time().toString("HH:mm"),
            "end_time": self.end_time.time().toString("HH:mm"),
            "color": self.selected_color,
            "badge": self.badge_combo.currentText(),
            "room": self.room_input.text().strip(),
            "type": "lesson"
        }


class LessonCard(QFrame):
    """
    Sleek, colored timetable card in the weekly schedule grid.
    """
    clicked = pyqtSignal(dict)
    delete_requested = pyqtSignal(str)

    def __init__(self, event_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        color = event_data.get("color", "#8B5CF6")
        rgba = hex_to_rgba(color, 0.22)
        
        self.setObjectName("lesson_card")
        self.setStyleSheet(f"""
            QFrame#lesson_card {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {rgba}, stop:1 #121524);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 4px;
            }}
            QFrame#lesson_card:hover {{
                border-color: {color};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hex_to_rgba(color, 0.35)}, stop:1 #181D2E);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Header: Subject Title + Delete button
        top_l = QHBoxLayout()
        top_l.setSpacing(4)
        
        title_lbl = QLabel(event_data.get("title", ""))
        title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        title_lbl.setWordWrap(True)
        top_l.addWidget(title_lbl, stretch=1)

        del_btn = QPushButton()
        del_btn.setIcon(get_icon("close", COLORS['text_muted'], 14))
        del_btn.setIconSize(QSize(14, 14))
        del_btn.setFixedSize(20, 20)
        del_btn.setToolTip(t("cal_del_btn"))
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.event_data["id"]))
        top_l.addWidget(del_btn)
        layout.addLayout(top_l)

        # Description / Topic
        desc = event_data.get("description", "")
        if desc:
            d_lbl = QLabel(desc)
            d_lbl.setFont(QFont("Segoe UI", 8))
            d_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            d_lbl.setWordWrap(True)
            layout.addWidget(d_lbl)

        # Badges & Time Row
        b_layout = QHBoxLayout()
        b_layout.setSpacing(4)
        b_layout.setContentsMargins(0, 2, 0, 0)

        badge_text = event_data.get("badge") or event_data.get("type", "")
        if badge_text:
            badge_lbl = QLabel(badge_text)
            badge_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            badge_lbl.setStyleSheet(f"""
                color: #FFFFFF;
                background-color: {hex_to_rgba(color, 0.45)};
                border-radius: 4px;
                padding: 1px 5px;
            """)
            b_layout.addWidget(badge_lbl)

        time_str = event_data.get("time", "")
        end_time_str = event_data.get("end_time", "")
        t_label_text = f"{time_str} - {end_time_str}" if end_time_str and end_time_str != time_str else time_str
        
        t_lbl = QLabel(t_label_text)
        t_lbl.setFont(QFont("Segoe UI", 7))
        t_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        b_layout.addWidget(t_lbl)
        b_layout.addStretch()

        if event_data.get("room"):
            r_lbl = QLabel(event_data["room"])
            r_lbl.setFont(QFont("Segoe UI", 7))
            r_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
            b_layout.addWidget(r_lbl)

        layout.addLayout(b_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_data)
        super().mousePressEvent(event)


class CurrentTimeLine(QWidget):
    """
    Sleek, real-time indicator bar positioned accurately by hour and minute.
    Features an exact time badge, glowing indicator dot, and continuous hairline bar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hour = 0
        self.minute = 0
        self.setFixedHeight(18)

    def set_time(self, hour: int, minute: int):
        self.hour = hour
        self.minute = minute
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        mid_y = 9 # Half of 18px

        time_str = f"{self.hour:02d}:{self.minute:02d}"
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text_w = metrics.horizontalAdvance(time_str) + 12
        badge_w = text_w
        badge_h = 16

        rose_color = QColor(COLORS.get("rose", "#EF4444"))

        # 1. Left glowing circle dot
        dot_radius = 4
        painter.setBrush(QBrush(rose_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, mid_y - dot_radius, dot_radius * 2, dot_radius * 2)

        # 2. Time badge pill: [ 14:55 ]
        badge_rect = QRectF(12, mid_y - (badge_h / 2), badge_w, badge_h)
        painter.setBrush(QBrush(rose_color))
        painter.drawRoundedRect(badge_rect, 4, 4)

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, time_str)

        # 3. Continuous 2px horizontal line spanning all the way across to the right edge
        line_start_x = int(badge_rect.right() + 4)
        if line_start_x < w:
            pen = QPen(rose_color, 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(line_start_x, mid_y, w, mid_y)


class TimetableSlotCell(QFrame):
    """
    Interactive hour cell container with support for floating current-time line overlay.
    """
    clicked = pyqtSignal(QDate, int)

    def __init__(self, slot_date: QDate, hour: int, is_today: bool, parent=None):
        super().__init__(parent)
        self.slot_date = slot_date
        self.hour = hour
        self.is_today = is_today
        self.is_current_hour = False
        self.current_minute = 0
        self.time_line = None

        self.setObjectName("slot_cell")
        cell_bg = "rgba(99, 102, 241, 0.04)" if is_today else "rgba(255, 255, 255, 0.015)"
        border_color = "rgba(129, 140, 248, 0.25)" if is_today else COLORS['border_subtle']

        self.setStyleSheet(f"""
            QFrame#slot_cell {{
                background-color: {cell_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                min-height: 52px;
            }}
            QFrame#slot_cell:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.2);
            }}
        """)

        self.cell_layout = QVBoxLayout(self)
        self.cell_layout.setContentsMargins(4, 4, 4, 4)
        self.cell_layout.setSpacing(3)
        self.cell_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_current_time(self, hour: int, minute: int):
        self.is_current_hour = True
        self.current_minute = minute
        if not self.time_line:
            self.time_line = CurrentTimeLine(self)
        self.time_line.set_time(hour, minute)
        self._reposition_time_line()
        self.time_line.show()
        self.time_line.raise_()

    def clear_current_time(self):
        self.is_current_hour = False
        if self.time_line:
            self.time_line.hide()

    def _reposition_time_line(self):
        if not self.is_current_hour or not self.time_line:
            return
        h = max(self.height(), 52)
        ratio = max(0.0, min(1.0, self.current_minute / 60.0))
        target_y = int(h * ratio)
        target_y = max(2, min(h - 18, target_y - 9))
        self.time_line.setGeometry(0, target_y, self.width(), 18)
        self.time_line.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_time_line()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.slot_date, self.hour)
        super().mousePressEvent(event)


class WeeklyTimetableWidget(QWidget):
    """
    Weekly Timetable Grid component.
    Displays days Monday through Sunday with hourly rows from 07:00 to 22:00.
    """
    edit_event_requested = pyqtSignal(dict)
    delete_event_requested = pyqtSignal(str)
    slot_clicked = pyqtSignal(QDate, int) # date, hour

    HOURS = list(range(7, 23)) # 07:00 to 22:00

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monday_date = self._get_current_monday()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Fixed Header with 7 Day Columns
        self.header_frame = QFrame()
        self.header_frame.setObjectName("timetable_header")
        self.header_frame.setStyleSheet(f"""
            QFrame#timetable_header {{
                background-color: {COLORS['bg_card']};
                border-bottom: 2px solid {COLORS['border_light']};
            }}
        """)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(60, 8, 16, 8)
        self.header_layout.setSpacing(6)
        main_layout.addWidget(self.header_frame)

        # Scrollable Grid Body
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(10, 8, 16, 16)
        self.grid_layout.setSpacing(6)

        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll, stretch=1)

        # Current time timer for live red line
        self.current_time_cell = None
        self.last_indicator_hour = None
        self.time_timer = QTimer(self)
        self.time_timer.setInterval(30000)
        self.time_timer.timeout.connect(self._check_time_update)
        self.time_timer.start()

    def _get_current_monday(self) -> QDate:
        today = QDate.currentDate()
        day_of_week = today.dayOfWeek() # 1=Mon, 7=Sun
        return today.addDays(-(day_of_week - 1))

    def set_monday(self, qdate: QDate):
        self.monday_date = qdate

    def render_schedule(self, events: List[Dict[str, Any]], tasks: List[Dict[str, Any]]):
        # 1. Update Header
        clear_layout(self.header_layout)

        days_short = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"] if get_language() == "ru" else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        months_short = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"] if get_language() == "ru" else ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        today = QDate.currentDate()

        for i in range(7):
            cur_date = self.monday_date.addDays(i)
            is_today = (cur_date == today)

            col_header = QFrame()
            col_header.setObjectName("col_header")
            if is_today:
                col_header.setStyleSheet(f"""
                    QFrame#col_header {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(99, 102, 241, 0.25), stop:1 rgba(99, 102, 241, 0.08));
                        border: 1px solid rgba(129, 140, 248, 0.5);
                        border-radius: 8px;
                        padding: 4px;
                    }}
                """)
            else:
                col_header.setStyleSheet("""
                    QFrame#col_header {
                        background: transparent;
                        border: 1px solid transparent;
                        padding: 4px;
                    }
                """)
            ch_layout = QVBoxLayout(col_header)
            ch_layout.setContentsMargins(4, 2, 4, 2)
            ch_layout.setSpacing(1)
            ch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            d_title = QLabel(f"{days_short[i]} · {cur_date.day()} {months_short[cur_date.month()]}")
            d_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold if is_today else QFont.Weight.Medium))
            d_title.setStyleSheet(f"color: {COLORS['primary'] if is_today else COLORS['text_secondary']};")
            d_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ch_layout.addWidget(d_title)

            if is_today:
                sub_t = QLabel(t("today_btn"))
                sub_t.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                sub_t.setStyleSheet(f"color: {COLORS['primary_light']};")
                sub_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ch_layout.addWidget(sub_t)

            self.header_layout.addWidget(col_header, stretch=1)

        # 2. Rebuild Grid Body
        clear_layout(self.grid_layout)

        # Build hour labels on col 0
        now_dt = datetime.now()
        cur_hour = now_dt.hour
        cur_min = now_dt.minute
        self.last_indicator_hour = cur_hour
        self.current_time_cell = None

        today = QDate.currentDate()
        is_today_in_view = (self.monday_date <= today <= self.monday_date.addDays(6))

        for row_idx, h in enumerate(self.HOURS):
            time_lbl = QLabel(f"{h:02d}:00")
            is_active_hour = (is_today_in_view and h == cur_hour)
            time_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold if is_active_hour else QFont.Weight.Normal))
            if is_active_hour:
                time_lbl.setStyleSheet(f"color: {COLORS['rose']}; padding-right: 6px;")
            else:
                time_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; padding-right: 6px;")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            time_lbl.setFixedWidth(50)
            self.grid_layout.addWidget(time_lbl, row_idx, 0)

            # 7 Day slots for this hour
            for col_idx in range(7):
                slot_date = self.monday_date.addDays(col_idx)
                date_str = slot_date.toString(Qt.DateFormat.ISODate)
                is_today = (slot_date == today)

                # Custom interactive slot cell with floating time indicator bar
                cell = TimetableSlotCell(slot_date, h, is_today, self)
                cell.clicked.connect(self.slot_clicked.emit)

                # Filter events for this date & hour
                matching_events = [
                    e for e in events
                    if e.get("date") == date_str and self._get_event_hour(e) == h
                ]

                # Tasks due at this date & hour
                matching_tasks = [
                    tsk for tsk in tasks
                    if tsk.get("due_date") == date_str and self._get_task_hour(tsk) == h and not tsk.get("completed")
                ]

                # Add lesson cards
                for evt in matching_events:
                    card = LessonCard(evt, cell)
                    card.clicked.connect(self.edit_event_requested.emit)
                    card.delete_requested.connect(self.delete_event_requested.emit)
                    cell.cell_layout.addWidget(card)

                # Add tasks due in this slot
                for tsk in matching_tasks:
                    t_card = QFrame()
                    t_card.setStyleSheet(f"""
                        QFrame {{
                            background-color: {COLORS['amber_subtle']};
                            border: 1px solid rgba(245, 158, 11, 0.35);
                            border-radius: 6px;
                            padding: 3px;
                        }}
                    """)
                    t_l = QHBoxLayout(t_card)
                    t_l.setContentsMargins(4, 2, 4, 2)
                    t_l.setSpacing(4)
                    t_dot = QLabel("●")
                    t_dot.setStyleSheet(f"color: {COLORS['amber']}; font-size: 8px;")
                    t_l.addWidget(t_dot)
                    t_text = QLabel(f"{t('task_due_date')}: {tsk.get('title', '')}")
                    t_text.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    t_text.setStyleSheet("color: #FFFFFF;")
                    t_l.addWidget(t_text, stretch=1)
                    cell.cell_layout.addWidget(t_card)

                # Position the live time indicator line accurately by hour and minute
                if is_today and h == cur_hour:
                    cell.set_current_time(cur_hour, cur_min)
                    self.current_time_cell = cell

                self.grid_layout.addWidget(cell, row_idx, col_idx + 1)

    def _get_event_hour(self, event: Dict[str, Any]) -> int:
        t_str = event.get("time", "09:00")
        try:
            return int(t_str.split(":")[0])
        except Exception:
            return 9

    def _get_task_hour(self, task: Dict[str, Any]) -> int:
        t_str = task.get("due_time", "12:00")
        try:
            return int(t_str.split(":")[0])
        except Exception:
            return 12

    def _check_time_update(self):
        now = datetime.now()
        cur_hour = now.hour
        cur_min = now.minute

        # If hour changed, we need to refresh the timetable so indicator moves to the next hour slot
        if self.last_indicator_hour is not None and cur_hour != self.last_indicator_hour:
            self.last_indicator_hour = cur_hour
            parent = self.parent()
            while parent and not hasattr(parent, "_refresh_timetable"):
                parent = parent.parent()
            if parent:
                parent._refresh_timetable()
        elif self.current_time_cell:
            self.current_time_cell.set_current_time(cur_hour, cur_min)

    def scroll_to_current_time(self):
        now_h = datetime.now().hour
        target_row = max(0, now_h - 7 - 1)
        approx_y = target_row * 56
        self.scroll.verticalScrollBar().setValue(approx_y)


class CalendarView(QWidget):
    """
    Main Calendar & Timetable View with Weekly Schedule and Monthly Grid modes.
    """
    open_task_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.selected_qdate = QDate.currentDate()
        self.current_monday = self._get_monday_for_date(self.selected_qdate)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        # 1. Top Controls Bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(10)

        # View Mode Switcher: "Неделя" / "Месяц"
        self.mode_week_btn = QPushButton(t("view_week"))
        self.mode_week_btn.setCheckable(True)
        self.mode_week_btn.setChecked(True)
        self.mode_week_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.mode_month_btn = QPushButton(t("view_month"))
        self.mode_month_btn.setCheckable(True)
        self.mode_month_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        mode_group = QButtonGroup(self)
        mode_group.addButton(self.mode_week_btn)
        mode_group.addButton(self.mode_month_btn)
        mode_group.buttonClicked.connect(self._on_mode_switched)

        mode_container = QFrame()
        mode_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 1px;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                color: {COLORS['text_muted']};
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background: {COLORS['primary']};
                color: #FFFFFF;
                font-weight: 600;
            }}
        """)
        m_layout = QHBoxLayout(mode_container)
        m_layout.setContentsMargins(2, 2, 2, 2)
        m_layout.setSpacing(2)
        m_layout.addWidget(self.mode_week_btn)
        m_layout.addWidget(self.mode_month_btn)
        ctrl_bar.addWidget(mode_container)

        # Week Navigation Controls (←, Сегодня, →)
        nav_box = QHBoxLayout()
        nav_box.setSpacing(4)

        self.prev_btn = QPushButton("←")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.prev_btn.setToolTip(t("cal_prev_week"))
        self.prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_btn.clicked.connect(self._prev_week)
        nav_box.addWidget(self.prev_btn)

        self.today_btn = QPushButton(t("today_btn"))
        self.today_btn.setFixedHeight(32)
        self.today_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.today_btn.clicked.connect(self._jump_to_today)
        nav_box.addWidget(self.today_btn)

        self.next_btn = QPushButton("→")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.next_btn.setToolTip(t("cal_next_week"))
        self.next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_btn.clicked.connect(self._next_week)
        nav_box.addWidget(self.next_btn)

        ctrl_bar.addLayout(nav_box)

        # Current range title
        self.range_title_lbl = QLabel()
        self.range_title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.range_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; padding-left: 6px;")
        ctrl_bar.addWidget(self.range_title_lbl)

        ctrl_bar.addStretch()

        # Action Buttons (+ Урок, + Задача)
        is_cyber = (COLORS.get('primary') == '#FCEE0A')
        btn_fg = '#000000' if is_cyber else '#FFFFFF'
        self.add_lesson_btn = QPushButton(t("btn_add_event"))
        self.add_lesson_btn.setIcon(get_icon("plus", btn_fg, 16))
        self.add_lesson_btn.setIconSize(QSize(16, 16))
        self.add_lesson_btn.setObjectName("primary-btn")
        self.add_lesson_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_lesson_btn.clicked.connect(self._open_add_lesson_dialog)
        ctrl_bar.addWidget(self.add_lesson_btn)

        add_task_btn = QPushButton(t("btn_new_task"))
        add_task_btn.setIcon(get_icon("tasks", COLORS['primary_light'], 16))
        add_task_btn.setIconSize(QSize(16, 16))
        add_task_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_task_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['primary_light']};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_subtle']};
                color: #FFFFFF;
            }}
        """)
        add_task_btn.clicked.connect(self._open_add_task_dialog)
        ctrl_bar.addWidget(add_task_btn)

        self.export_btn = QPushButton(t("export_ics"))
        self.export_btn.setIcon(get_icon("calendar", COLORS['text_secondary'], 16))
        self.export_btn.setIconSize(QSize(16, 16))
        self.export_btn.setToolTip(t("act_export_ics_title"))
        self.export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
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
        self.export_btn.clicked.connect(self.export_to_ics)
        ctrl_bar.addWidget(self.export_btn)

        self.google_sync_btn = QPushButton(t("btn_google_sync"))
        self.google_sync_btn.setIcon(get_icon("sync", "#4285F4", 16))
        self.google_sync_btn.setIconSize(QSize(16, 16))
        self.google_sync_btn.setToolTip(t("google_sync_tooltip"))
        self.google_sync_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.google_sync_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: #4285F4;
            }}
        """)
        self.google_sync_btn.clicked.connect(self._open_google_sync)
        ctrl_bar.addWidget(self.google_sync_btn)

        layout.addLayout(ctrl_bar)

        # 2. View Mode Stack (Page 0: Timetable, Page 1: Month Grid)
        self.view_stack = QStackedWidget(self)

        # Page 0: Weekly Timetable
        self.timetable = WeeklyTimetableWidget(self)
        self.timetable.edit_event_requested.connect(self._edit_event)
        self.timetable.delete_event_requested.connect(self._delete_event)
        self.timetable.slot_clicked.connect(self._on_slot_clicked)
        self.view_stack.addWidget(self.timetable)

        # Page 1: Traditional Month Grid
        self.month_container = QWidget()
        month_layout = QHBoxLayout(self.month_container)
        month_layout.setContentsMargins(0, 0, 0, 0)
        month_layout.setSpacing(18)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        month_layout.addWidget(self.calendar, stretch=6)

        # Right Month Inspector
        self.inspector_frame = QFrame()
        self.inspector_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 14px;
            }}
        """)
        ins_layout = QVBoxLayout(self.inspector_frame)
        ins_layout.setContentsMargins(18, 16, 18, 16)
        ins_layout.setSpacing(12)

        self.day_title_lbl = QLabel()
        self.day_title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.day_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        ins_layout.addWidget(self.day_title_lbl)

        self.agenda_scroll = QScrollArea()
        self.agenda_scroll.setWidgetResizable(True)
        self.agenda_scroll.setStyleSheet("background: transparent; border: none;")
        self.agenda_container = QWidget()
        self.agenda_container.setStyleSheet("background: transparent;")
        self.agenda_layout = QVBoxLayout(self.agenda_container)
        self.agenda_layout.setContentsMargins(0, 0, 0, 0)
        self.agenda_layout.setSpacing(8)
        self.agenda_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.agenda_scroll.setWidget(self.agenda_container)
        ins_layout.addWidget(self.agenda_scroll, stretch=1)

        month_layout.addWidget(self.inspector_frame, stretch=4)
        self.view_stack.addWidget(self.month_container)

        layout.addWidget(self.view_stack, stretch=1)

        # Storage listener
        self.storage.data_changed.connect(self._on_storage_changed)

        self._update_range_title()
        self._refresh_timetable()
        self._highlight_calendar_days()
        QTimer.singleShot(150, self.timetable.scroll_to_current_time)

    def _get_monday_for_date(self, qdate: QDate) -> QDate:
        day_of_week = qdate.dayOfWeek() # 1=Mon, 7=Sun
        return qdate.addDays(-(day_of_week - 1))

    def _prev_week(self):
        self.current_monday = self.current_monday.addDays(-7)
        self.timetable.set_monday(self.current_monday)
        self._update_range_title()
        self._refresh_timetable()

    def _next_week(self):
        self.current_monday = self.current_monday.addDays(7)
        self.timetable.set_monday(self.current_monday)
        self._update_range_title()
        self._refresh_timetable()

    def _jump_to_today(self):
        today = QDate.currentDate()
        self.selected_qdate = today
        self.current_monday = self._get_monday_for_date(today)
        self.timetable.set_monday(self.current_monday)
        self.calendar.setSelectedDate(today)
        self._update_range_title()
        self._refresh_timetable()
        self._on_date_selected()
        self.timetable.scroll_to_current_time()

    def _update_range_title(self):
        sun_date = self.current_monday.addDays(6)
        months_ru = ["", "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
                     "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"]
        
        if self.current_monday.month() == sun_date.month():
            range_str = f"{self.current_monday.day()} — {sun_date.day()} {months_ru[sun_date.month()]} {sun_date.year()}"
        else:
            range_str = f"{self.current_monday.day()} {months_ru[self.current_monday.month()]} — {sun_date.day()} {months_ru[sun_date.month()]} {sun_date.year()}"
        self.range_title_lbl.setText(range_str)

    def refresh_theme(self):
        self.range_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; padding-left: 6px;")
        is_cyber = (COLORS.get('primary') == '#FCEE0A')
        btn_fg = '#000000' if is_cyber else '#FFFFFF'
        if hasattr(self, "add_lesson_btn"):
            self.add_lesson_btn.setIcon(get_icon("plus", btn_fg, 16))
        if hasattr(self, "timetable"):
            self.timetable.header_frame.setStyleSheet(f"""
                QFrame#timetable_header {{
                    background-color: {COLORS['bg_card']};
                    border-bottom: 2px solid {COLORS['border_light']};
                }}
            """)
            self._refresh_timetable()

    def _on_mode_switched(self):
        if self.mode_week_btn.isChecked():
            self.view_stack.setCurrentIndex(0)
            self._refresh_timetable()
        else:
            self.view_stack.setCurrentIndex(1)
            self._on_date_selected()

    def _refresh_timetable(self):
        events = self.storage.get_events()
        tasks = self.storage.get_tasks()
        self.timetable.render_schedule(events, tasks)

    def _on_slot_clicked(self, qdate: QDate, hour: int):
        self._open_add_lesson_dialog(preset_date=qdate, preset_hour=hour)

    def _open_add_lesson_dialog(self, preset_date: Optional[QDate] = None, preset_hour: int = 9):
        target_date = preset_date or self.selected_qdate
        dlg = AddLessonDialog(preset_date=target_date, preset_hour=preset_hour, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.storage.add_event(
                title=data["title"],
                date_str=data["date"],
                time_str=data["time"],
                end_time_str=data["end_time"],
                description=data["description"],
                color=data["color"],
                event_type=data["type"],
                badge=data["badge"],
                room=data["room"]
            )
            self._refresh_timetable()
            self._highlight_calendar_days()

    def _edit_event(self, event_data: Dict[str, Any]):
        dlg = AddLessonDialog(existing_event=event_data, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.storage.update_event(
                event_data["id"],
                title=data["title"],
                date=data["date"],
                time=data["time"],
                end_time=data["end_time"],
                description=data["description"],
                color=data["color"],
                badge=data["badge"],
                room=data["room"]
            )
            self._refresh_timetable()
            self._highlight_calendar_days()

    def _delete_event(self, event_id: str):
        self.storage.delete_event(event_id)
        self._refresh_timetable()
        self._highlight_calendar_days()

    def _open_add_task_dialog(self):
        dummy_task = {
            "title": "",
            "subject": "Общие задачи",
            "description": "",
            "due_date": self.selected_qdate.toString(Qt.DateFormat.ISODate),
            "due_time": "18:00",
            "priority": "medium"
        }
        dlg = TaskDialog(existing_task=dummy_task, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.storage.add_task(
                title=data["title"],
                subject=data["subject"],
                description=data["description"],
                due_date=data["due_date"],
                due_time=data["due_time"],
                priority=data["priority"]
            )
            self._refresh_timetable()
            self._highlight_calendar_days()

    def _on_date_selected(self):
        self.selected_qdate = self.calendar.selectedDate()
        iso_str = self.selected_qdate.toString(Qt.DateFormat.ISODate)
        self.day_title_lbl.setText(f"{self.selected_qdate.toString('dd.MM.yyyy')}")

        clear_layout(self.agenda_layout)

        events = [e for e in self.storage.get_events() if e.get("date") == iso_str]
        tasks = [t for t in self.storage.get_tasks() if t.get("due_date") == iso_str]

        if not events and not tasks:
            empty_lbl = QLabel(t("no_classes_today"))
            empty_lbl.setFont(QFont("Segoe UI", 9))
            empty_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.agenda_layout.addWidget(empty_lbl)
            return

        for evt in events:
            card = LessonCard(evt, self.agenda_container)
            card.clicked.connect(self._edit_event)
            card.delete_requested.connect(self._delete_event)
            self.agenda_layout.addWidget(card)

    def _highlight_calendar_days(self):
        date_indicators = {}
        for evt in self.storage.get_events():
            d = evt.get("date")
            if d:
                date_indicators[d] = evt.get("color", COLORS['primary'])

        for task in self.storage.get_tasks():
            if not task.get("completed") and task.get("due_date"):
                d = task["due_date"]
                if d not in date_indicators:
                    date_indicators[d] = COLORS['amber']

        for date_str, col_hex in date_indicators.items():
            try:
                qd = QDate.fromString(date_str, Qt.DateFormat.ISODate)
                fmt = QTextCharFormat()
                fmt.setFontWeight(QFont.Weight.Bold)
                fmt.setForeground(QColor(col_hex))
                fmt.setBackground(QColor(COLORS['primary_subtle']))
                self.calendar.setDateTextFormat(qd, fmt)
            except Exception:
                pass

    def _on_storage_changed(self, entity_type: str):
        if entity_type in ("events", "tasks", "all"):
            self._refresh_timetable()
            self._highlight_calendar_days()

    def export_to_ics(self):
        """Export all calendar lessons and events to an RFC 5545 iCalendar (.ics) file."""
        events = self.storage.get_events()
        if not events:
            QMessageBox.information(
                self,
                "Экспорт расписания",
                "В календаре пока нет добавленных занятий для экспорта."
            )
            return

        default_filename = f"Расписание_WorkBOXig_{date.today().strftime('%Y%m%d')}.ics"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт расписания в iCalendar (.ics)",
            default_filename,
            "Файлы iCalendar (*.ics);;Все файлы (*.*)"
        )

        if not file_path:
            return

        try:
            ics_content = self._generate_ics_content(events)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ics_content)

            parent = self.window()
            if hasattr(parent, "_show_toast"):
                parent._show_toast(t("export_ics") + ": " + t("success"), "success")
            else:
                QMessageBox.information(
                    self,
                    "Экспорт завершён",
                    f"Расписание успешно сохранено в файл:\n{file_path}\n\nТеперь вы можете импортировать его в Google Календарь, Apple Calendar или Яндекс."
                )
        except Exception as ex:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось сохранить файл .ics:\n{ex}"
            )

    def _generate_ics_content(self, events: List[Dict[str, Any]]) -> str:
        now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//WorkBOXig//Work & Study OS//RU",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Расписание WorkBOXig",
            "X-WR-TIMEZONE:Europe/Moscow",
        ]

        for ev in events:
            ev_id = ev.get("id", "0")
            title = ev.get("title", "Занятие").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
            date_str = ev.get("date", "")
            time_str = ev.get("time", "09:00")
            end_time_str = ev.get("end_time", "") or time_str

            if not date_str:
                continue

            try:
                d_parts = [int(p) for p in date_str.split("-")]
                t_parts = [int(p) for p in time_str.split(":")]
                et_parts = [int(p) for p in end_time_str.split(":")]

                start_dt = datetime(d_parts[0], d_parts[1], d_parts[2], t_parts[0], t_parts[1])
                end_dt = datetime(d_parts[0], d_parts[1], d_parts[2], et_parts[0], et_parts[1])

                if end_dt <= start_dt:
                    end_dt = start_dt + timedelta(minutes=90)

                dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
                dtend = end_dt.strftime("%Y%m%dT%H%M%S")
            except Exception:
                continue

            desc_parts = []
            if ev.get("badge") or ev.get("type"):
                desc_parts.append(f"Тип: {ev.get('badge') or ev.get('type')}")
            if ev.get("description"):
                desc_parts.append(ev.get("description"))
            desc_text = " | ".join(desc_parts).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

            location = ev.get("room", "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{ev_id}@workboxig.local")
            lines.append(f"DTSTAMP:{now_utc}")
            lines.append(f"DTSTART:{dtstart}")
            lines.append(f"DTEND:{dtend}")
            lines.append(f"SUMMARY:{title}")
            if desc_text:
                lines.append(f"DESCRIPTION:{desc_text}")
            if location:
                lines.append(f"LOCATION:{location}")
            lines.append("STATUS:CONFIRMED")
            lines.append("END:VEVENT")

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def _open_google_sync(self):
        dialog = GoogleSyncDialog(storage=self.storage, parent=self)
        dialog.sync_completed.connect(self._on_google_sync_completed)
        dialog.exec()

    def _on_google_sync_completed(self, added: int, updated: int, total: int):
        self._refresh_all_events()
        parent = self.window()
        if hasattr(parent, "show_toast"):
            if total > 0:
                parent.show_toast(t("google_sync_success", added=added, updated=updated, total=total), "check")
            else:
                parent.show_toast(t("all_data_saved"), "check")
