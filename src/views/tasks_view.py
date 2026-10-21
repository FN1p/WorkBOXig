"""
Tasks & Homework (Задачи и ДЗ) View for WorkBOXig.
Modern, clean, and highly readable task tracker with priority badges and calendar links.
"""

from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QProgressBar, QFrame,
    QDialog, QTextEdit, QDateEdit, QTimeEdit, QMessageBox, QScrollArea,
    QGridLayout
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor, QIcon
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.utils.shortcuts import clear_layout


PRIORITY_CONFIG = {
    "urgent": {"label": "Срочно", "color": "#EF4444", "bg": "rgba(239, 68, 68, 0.18)"},
    "high": {"label": "Высокий", "color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.18)"},
    "medium": {"label": "Средний", "color": "#38BDF8", "bg": "rgba(56, 189, 248, 0.18)"},
    "low": {"label": "Низкий", "color": "#10B981", "bg": "rgba(16, 185, 129, 0.18)"},
}


class TaskDialog(QDialog):
    """Dialog to create or edit a task / homework entry."""
    def __init__(self, existing_task=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("task_edit_title") if existing_task else t("task_new_title"))
        self.setFixedSize(520, 580)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        dlg_title = QLabel(t("task_new_title") if not existing_task else t("task_edit_title"))
        dlg_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        dlg_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(dlg_title)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setFixedHeight(38)
        self.title_input.setPlaceholderText(t("task_title_ph"))
        layout.addWidget(self.title_input)

        # Subject / Category
        subj_layout = QHBoxLayout()
        s_lbl = QLabel(t("task_subject_lbl"))
        s_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        s_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.subj_input = QComboBox()
        self.subj_input.setFixedHeight(38)
        self.subj_input.setEditable(True)
        self.subj_input.addItems(["Информатика & Python", "Математический анализ", "Физика", "Иностранный язык", "Общие задачи"])
        subj_layout.addWidget(s_lbl)
        subj_layout.addWidget(self.subj_input, stretch=1)
        layout.addLayout(subj_layout)

        # Date & Time linked to calendar
        dt_layout = QHBoxLayout()
        d_lbl = QLabel(t("task_due_lbl"))
        d_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        d_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setFixedHeight(38)
        self.date_edit.setDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFixedHeight(38)
        self.time_edit.setTime(QTime(18, 0))

        dt_layout.addWidget(d_lbl)
        dt_layout.addWidget(self.date_edit, stretch=1)
        dt_layout.addWidget(self.time_edit)
        layout.addLayout(dt_layout)

        # Priority
        p_layout = QHBoxLayout()
        p_lbl = QLabel(t("task_priority_lbl"))
        p_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        p_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.p_combo = QComboBox()
        self.p_combo.setFixedHeight(38)
        self.p_combo.addItem(t("task_priority_urgent"), "urgent")
        self.p_combo.addItem(t("task_priority_high"), "high")
        self.p_combo.addItem(t("task_priority_med"), "medium")
        self.p_combo.addItem(t("task_priority_low"), "low")
        self.p_combo.setCurrentIndex(2)
        p_layout.addWidget(p_lbl)
        p_layout.addWidget(self.p_combo, stretch=1)
        layout.addLayout(p_layout)

        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(t("task_desc_ph"))
        self.desc_input.setFixedHeight(85)
        layout.addWidget(self.desc_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setObjectName("ghost-btn")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(t("task_save_btn"))
        save_btn.setObjectName("primary-btn")
        save_btn.setFixedHeight(38)
        save_btn.setObjectName("primary-btn")
        save_btn.clicked.connect(self._validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if existing_task:
            self.title_input.setText(existing_task.get("title", ""))
            self.subj_input.setCurrentText(existing_task.get("subject", "Общие задачи"))
            self.desc_input.setText(existing_task.get("description", ""))
            if existing_task.get("due_date"):
                try:
                    self.date_edit.setDate(QDate.fromString(existing_task["due_date"], Qt.DateFormat.ISODate))
                except Exception:
                    pass
            if existing_task.get("due_time"):
                try:
                    self.time_edit.setTime(QTime.fromString(existing_task["due_time"], "HH:mm"))
                except Exception:
                    pass
            p_val = existing_task.get("priority", "medium")
            idx = self.p_combo.findData(p_val)
            if idx >= 0:
                self.p_combo.setCurrentIndex(idx)

    def _validate_and_save(self):
        if not self.title_input.text().strip():
            self.title_input.setFocus()
            self.title_input.setStyleSheet(f"border: 1px solid {COLORS['rose']};")
            return
        self.accept()

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "subject": self.subj_input.currentText().strip() or "Общее",
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self.date_edit.date().toString(Qt.DateFormat.ISODate),
            "due_time": self.time_edit.time().toString("HH:mm"),
            "priority": self.p_combo.currentData()
        }


class TaskItemWidget(QFrame):
    """Custom Card Item for Tasks."""
    toggled = pyqtSignal(str) # task_id
    deleted = pyqtSignal(str) # task_id
    edited = pyqtSignal(str) # task_id

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task_id = task["id"]
        is_done = task.get("completed", False)
        priority = task.get("priority", "medium")
        p_cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["medium"])

        self.setObjectName("taskCard")
        border_col = COLORS['emerald'] if is_done else p_cfg['color']
        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-left: 4px solid {border_col};
                border-radius: 12px;
            }}
            QFrame#taskCard:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_light']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        # Checkbox
        self.cb = QCheckBox()
        self.cb.setChecked(is_done)
        self.cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cb.toggled.connect(lambda: self.toggled.emit(self.task_id))
        layout.addWidget(self.cb)

        # Content column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Top row: Title + Subject + Priority
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.title_lbl = QLabel(task.get("title", ""))
        self.title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        if is_done:
            self.title_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; text-decoration: line-through; background: transparent;")
        else:
            self.title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        top_row.addWidget(self.title_lbl)

        # Subject badge pill
        subj_lbl = QLabel(f"#{task.get('subject', 'Общее')}")
        subj_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
        subj_lbl.setStyleSheet(f"""
            background-color: {COLORS['primary_subtle']};
            color: {COLORS['primary_light']};
            border: 1px solid {COLORS['primary_border']};
            border-radius: 6px;
            padding: 2px 8px;
        """)
        top_row.addWidget(subj_lbl)

        # Priority badge pill
        p_lbl = QLabel(p_cfg["label"])
        p_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p_lbl.setStyleSheet(f"""
            background-color: {p_cfg['bg']};
            color: {p_cfg['color']};
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 2px 8px;
        """)
        top_row.addWidget(p_lbl)

        top_row.addStretch()
        info_layout.addLayout(top_row)

        # Description row if present
        if task.get("description"):
            d_lbl = QLabel(task["description"])
            d_lbl.setFont(QFont("Segoe UI", 9))
            d_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            d_lbl.setWordWrap(True)
            info_layout.addWidget(d_lbl)

        # Due Date / Deadline status badge
        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)

        due_date_str = task.get("due_date", "")
        due_time_str = task.get("due_time", "")
        
        date_badge_text = t("task_due_exact", date=due_date_str)
        date_bg = COLORS['bg_input']
        date_fg = COLORS['text_muted']

        if due_date_str:
            try:
                task_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                diff = (task_date - date.today()).days
                if is_done:
                    date_badge_text = t("task_stat_done")
                    date_bg = COLORS['emerald_subtle']
                    date_fg = COLORS['emerald']
                elif diff < 0:
                    date_badge_text = t("task_due_overdue", days=abs(diff), date=due_date_str)
                    date_bg = COLORS['rose_subtle']
                    date_fg = COLORS['rose']
                elif diff == 0:
                    date_badge_text = t("task_due_today", time=due_time_str)
                    date_bg = COLORS['amber_subtle']
                    date_fg = COLORS['amber']
                elif diff == 1:
                    date_badge_text = t("task_due_tomorrow", time=due_time_str)
                    date_bg = COLORS['sky_subtle']
                    date_fg = COLORS['sky']
                else:
                    date_badge_text = t("task_due_in_days", days=diff, date=due_date_str)
                    date_fg = COLORS['text_secondary']
            except Exception:
                pass

        date_badge = QLabel(date_badge_text)
        date_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
        date_badge.setStyleSheet(f"""
            background-color: {date_bg};
            color: {date_fg};
            border-radius: 6px;
            padding: 3px 8px;
        """)
        meta_row.addWidget(date_badge)

        meta_row.addStretch()
        info_layout.addLayout(meta_row)

        layout.addLayout(info_layout, stretch=1)

        # Right Action Buttons (Edit, Delete) with Vector Icons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        edit_btn = QPushButton()
        edit_btn.setIcon(get_icon("edit", "#CBD5E1", 16))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setFixedSize(32, 32)
        edit_btn.setToolTip(t("edit"))
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['primary_border']};
            }}
        """)
        edit_btn.clicked.connect(lambda: self.edited.emit(self.task_id))
        actions_layout.addWidget(edit_btn)

        del_btn = QPushButton()
        del_btn.setIcon(get_icon("trash", "#F87171", 16))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setFixedSize(32, 32)
        del_btn.setToolTip(t("delete"))
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['rose']};
                border-color: {COLORS['rose']};
            }}
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self.task_id))
        actions_layout.addWidget(del_btn)

        layout.addLayout(actions_layout)


class TasksView(QWidget):
    """
    Tasks and Homework Tracker View.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.active_filter = "all"
        self.active_subject = "all"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        # 1. Top 4 Metric Cards in a Grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)

        self.card_total = self._create_stat_card("tasks", t("task_stat_total"), "0", COLORS['primary_light'])
        self.card_pending = self._create_stat_card("clock", t("task_stat_pending"), "0", COLORS['sky'])
        self.card_today = self._create_stat_card("alert_circle", t("task_stat_today"), "0", COLORS['amber'])
        self.card_done = self._create_stat_card("check_circle", t("task_stat_done"), "0", COLORS['emerald'])

        metrics_grid.addWidget(self.card_total, 0, 0)
        metrics_grid.addWidget(self.card_pending, 0, 1)
        metrics_grid.addWidget(self.card_today, 0, 2)
        metrics_grid.addWidget(self.card_done, 0, 3)

        main_layout.addLayout(metrics_grid)

        # 2. Row 1: Filter Segmented Pills & Main Action
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(8)

        self.filter_buttons = {}
        filters_list = [
            ("all", t("filter_all")),
            ("today", t("task_stat_today")),
            ("upcoming", t("task_stat_pending")),
            ("overdue", t("task_priority_urgent")),
            ("urgent", t("task_priority_urgent")),
            ("done", t("task_stat_done"))
        ]

        for f_id, text in filters_list:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setChecked(f_id == "all")
            btn.clicked.connect(lambda checked, fid=f_id: self._set_filter(fid))
            row1_layout.addWidget(btn)
            self.filter_buttons[f_id] = btn

        self._style_filter_buttons()
        row1_layout.addStretch()

        add_task_btn = QPushButton(t("btn_new_task"))
        add_task_btn.setIcon(get_icon("plus", "#FFFFFF", 16))
        add_task_btn.setIconSize(QSize(16, 16))
        add_task_btn.setObjectName("primary-btn")
        add_task_btn.setFixedHeight(34)
        add_task_btn.clicked.connect(self._open_new_task_dialog)
        row1_layout.addWidget(add_task_btn)

        main_layout.addLayout(row1_layout)

        # Row 2: Subject Filter, Clear Done, & Instant Search
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(12)

        s_lbl = QLabel(t("category"))
        s_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-weight: 500;")
        row2_layout.addWidget(s_lbl)

        self.subj_filter = QComboBox()
        self.subj_filter.addItem(t("filter_all"), "all")
        self.subj_filter.setFixedWidth(200)
        self.subj_filter.currentIndexChanged.connect(self._on_subject_filter_changed)
        row2_layout.addWidget(self.subj_filter)

        clear_done_btn = QPushButton(t("clear_completed"))
        clear_done_btn.setIcon(get_icon("trash", COLORS['text_muted'], 16))
        clear_done_btn.setIconSize(QSize(16, 16))
        clear_done_btn.setObjectName("ghost-btn")
        clear_done_btn.clicked.connect(self._clear_completed_tasks)
        row2_layout.addWidget(clear_done_btn)

        row2_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_tasks_ph"))
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self._render_tasks)
        row2_layout.addWidget(self.search_input)

        main_layout.addLayout(row2_layout)

        # 3. Tasks List Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 4, 0, 8)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.tasks_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Connect storage signals
        self.storage.data_changed.connect(self._on_storage_changed)

        self._update_subject_dropdown()
        self._render_tasks()

    def _create_stat_card(self, icon_name: str, title: str, value: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(4)

        top = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap(icon_name, color_hex, 18))
        icon_lbl.setStyleSheet("background: transparent;")
        top.addWidget(icon_lbl)

        v_lbl = QLabel(value)
        v_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color: {color_hex}; background: transparent; padding-left: 6px;")
        v_lbl.setObjectName("stat_value")
        top.addWidget(v_lbl)
        top.addStretch()
        l.addLayout(top)

        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 9))
        t_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        l.addWidget(t_lbl)
        return card

    def _style_filter_buttons(self):
        for fid, btn in self.filter_buttons.items():
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: #FFFFFF;
                        border: 1px solid {COLORS['primary']};
                        border-radius: 8px;
                        font-weight: 600;
                        padding: 6px 14px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_card']};
                        color: {COLORS['text_secondary']};
                        border: 1px solid {COLORS['border_subtle']};
                        border-radius: 8px;
                        padding: 6px 14px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg_card_hover']};
                        color: #FFFFFF;
                    }}
                """)

    def _set_filter(self, filter_id: str):
        self.active_filter = filter_id
        for fid, btn in self.filter_buttons.items():
            btn.setChecked(fid == filter_id)
        self._style_filter_buttons()
        self._render_tasks()

    def _on_subject_filter_changed(self):
        self.active_subject = self.subj_filter.currentData() or "all"
        self._render_tasks()

    def _update_subject_dropdown(self):
        current = self.subj_filter.currentData()
        self.subj_filter.blockSignals(True)
        self.subj_filter.clear()
        self.subj_filter.addItem(t("filter_all"), "all")
        
        subjects = set()
        for task_record in self.storage.get_tasks():
            s = task_record.get("subject")
            if s:
                subjects.add(s)

        for s in sorted(subjects):
            self.subj_filter.addItem(s, s)

        idx = self.subj_filter.findData(current)
        if idx >= 0:
            self.subj_filter.setCurrentIndex(idx)
        self.subj_filter.blockSignals(False)

    def _render_tasks(self):
        clear_layout(self.tasks_layout)

        tasks = self.storage.get_tasks()
        today_iso = date.today().isoformat()
        query = self.search_input.text().lower().strip()

        # Compute metrics
        total = len(tasks)
        done = sum(1 for task_item in tasks if task_item.get("completed"))
        pending = total - done
        today_due = sum(1 for task_item in tasks if not task_item.get("completed") and task_item.get("due_date") == today_iso)

        self.card_total.findChild(QLabel, "stat_value").setText(str(total))
        self.card_pending.findChild(QLabel, "stat_value").setText(str(pending))
        self.card_today.findChild(QLabel, "stat_value").setText(str(today_due))
        self.card_done.findChild(QLabel, "stat_value").setText(str(done))

        # Filter tasks
        filtered = []
        for single_task in tasks:
            is_done = single_task.get("completed", False)
            d_date = single_task.get("due_date", "")
            priority = single_task.get("priority", "medium")
            subj = single_task.get("subject", "")

            # Subject filter
            if self.active_subject != "all" and subj != self.active_subject:
                continue

            # Query filter
            if query and (query not in single_task.get("title", "").lower() and query not in single_task.get("description", "").lower()):
                continue

            # Status filter
            if self.active_filter == "today":
                if not (not is_done and d_date == today_iso):
                    continue
            elif self.active_filter == "upcoming":
                if not (not is_done and d_date >= today_iso):
                    continue
            elif self.active_filter == "overdue":
                if not (not is_done and d_date < today_iso):
                    continue
            elif self.active_filter == "urgent":
                if not (not is_done and priority in ("urgent", "high")):
                    continue
            elif self.active_filter == "done":
                if not is_done:
                    continue

            filtered.append(single_task)

        sorted_tasks = sorted(filtered, key=lambda x: (x.get("completed", False), x.get("due_date", "9999-99-99")))

        if not sorted_tasks:
            empty_lbl = QLabel(t("no_tasks"))
            empty_lbl.setFont(QFont("Segoe UI", 11))
            empty_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 48px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.addWidget(empty_lbl)
            return

        for task in sorted_tasks:
            widget = TaskItemWidget(task)
            widget.toggled.connect(self._on_task_toggled)
            widget.deleted.connect(self._on_task_deleted)
            widget.edited.connect(self._on_task_edited)
            self.tasks_layout.addWidget(widget)

    def _open_new_task_dialog(self):
        dlg = TaskDialog(parent=self)
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
            self._update_subject_dropdown()
            self._render_tasks()

    def _on_task_edited(self, task_id: str):
        task = next((task_item for task_item in self.storage.get_tasks() if task_item["id"] == task_id), None)
        if not task:
            return
        dlg = TaskDialog(existing_task=task, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.storage.update_task(task_id, **data)
            self._update_subject_dropdown()
            self._render_tasks()

    def _on_task_toggled(self, task_id: str):
        self.storage.toggle_task(task_id)
        self._render_tasks()

    def _on_task_deleted(self, task_id: str):
        if QMessageBox.question(self, t("delete"), t("delete_task_confirm")) == QMessageBox.StandardButton.Yes:
            self.storage.delete_task(task_id)
            self._render_tasks()

    def _clear_completed_tasks(self):
        tasks = self.storage.get_tasks()
        completed = [task_item for task_item in tasks if task_item.get("completed")]
        if not completed:
            return
        if QMessageBox.question(self, t("clear_completed"), t("clear_completed_confirm", count=len(completed))) == QMessageBox.StandardButton.Yes:
            for t in completed:
                self.storage.delete_task(t["id"])
            self._render_tasks()

    def select_task(self, task_id: str):
        self._set_filter("all")
        self.search_input.clear()
        self._render_tasks()

    def _on_storage_changed(self, entity_type: str):
        if entity_type in ("tasks", "all"):
            self._update_subject_dropdown()
            self._render_tasks()
