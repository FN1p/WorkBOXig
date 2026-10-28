"""
Tasks & Homework (Задачи и ДЗ) View for WorkBOXig.
Modern, clean, and highly readable task tracker with priority badges and calendar links.
"""

from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QProgressBar, QFrame,
    QDialog, QTextEdit, QDateEdit, QTimeEdit, QMessageBox, QScrollArea,
    QGridLayout, QButtonGroup, QStackedWidget
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor, QIcon
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.utils.shortcuts import clear_layout
from src.utils.quick_task import parse_quick_task


def get_priority_config(priority: str) -> dict:
    colors = {
        "urgent": ("#EF4444", "rgba(239, 68, 68, 0.18)"),
        "high": ("#F59E0B", "rgba(245, 158, 11, 0.18)"),
        "medium": ("#38BDF8", "rgba(56, 189, 248, 0.18)"),
        "low": ("#10B981", "rgba(16, 185, 129, 0.18)"),
    }
    col, bg = colors.get(priority, colors["medium"])
    return {
        "label": t(f"priority_{priority}_badge"),
        "color": col,
        "bg": bg
    }


class TaskDialog(QDialog):
    """Dialog to create or edit a task / homework entry."""
    def __init__(self, existing_task=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("task_edit_title") if existing_task else t("task_new_title"))
        self.resize(520, 580)
        self.setMinimumSize(480, 520)
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
        self.subj_input.addItems([t("task_preset_cs"), t("task_preset_math"), t("task_preset_physics"), t("task_preset_lang"), t("task_preset_general")])
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
        self.desc_input.setFixedHeight(75)
        layout.addWidget(self.desc_input)

        # Subtasks (Checklist)
        sub_title_lbl = QLabel(t("subtasks_lbl"))
        sub_title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        sub_title_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(sub_title_lbl)

        self.subtasks_container = QWidget()
        self.subtasks_container.setStyleSheet("background: transparent;")
        self.subtasks_layout = QVBoxLayout(self.subtasks_container)
        self.subtasks_layout.setContentsMargins(0, 0, 0, 0)
        self.subtasks_layout.setSpacing(4)
        layout.addWidget(self.subtasks_container)

        self.subtasks_data = []

        add_sub_row = QHBoxLayout()
        add_sub_row.setSpacing(6)
        self.new_sub_input = QLineEdit()
        self.new_sub_input.setFixedHeight(34)
        self.new_sub_input.setPlaceholderText(t("subtask_add_ph"))
        self.new_sub_input.returnPressed.connect(self._add_subtask_item)
        add_sub_row.addWidget(self.new_sub_input)

        add_sub_btn = QPushButton("+")
        add_sub_btn.setFixedSize(34, 34)
        add_sub_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_sub_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary_subtle']};
                color: {COLORS['primary_light']};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
            }}
        """)
        add_sub_btn.clicked.connect(self._add_subtask_item)
        add_sub_row.addWidget(add_sub_btn)
        layout.addLayout(add_sub_row)

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
            self.subtasks_data = [dict(s) for s in existing_task.get("subtasks", [])]
            self._render_subtask_rows()
            self.subj_input.setCurrentText(existing_task.get("subject", t("task_preset_general")))
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

    def _add_subtask_item(self):
        text = self.new_sub_input.text().strip()
        if not text:
            return
        import uuid
        self.subtasks_data.append({
            "id": str(uuid.uuid4()),
            "title": text,
            "completed": False
        })
        self.new_sub_input.clear()
        self._render_subtask_rows()

    def _render_subtask_rows(self):
        clear_layout(self.subtasks_layout)
        for idx, sub in enumerate(self.subtasks_data):
            row = QHBoxLayout()
            row.setSpacing(8)
            cb = QCheckBox(sub.get("title", ""))
            cb.setChecked(sub.get("completed", False))
            cb.setStyleSheet("color: " + COLORS['text_primary'] + ";")
            cb.toggled.connect(lambda checked, i=idx: self._toggle_subtask_at(i, checked))
            row.addWidget(cb, stretch=1)

            del_btn = QPushButton()
            del_btn.setIcon(get_icon("close", COLORS["text_muted"], 12))
            del_btn.setFixedSize(22, 22)
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setStyleSheet("QPushButton { background: transparent; color: " + COLORS['text_muted'] + "; border: none; font-size: 11px; } QPushButton:hover { color: " + COLORS['rose'] + "; }")
            del_btn.clicked.connect(lambda ch, i=idx: self._remove_subtask_at(i))
            row.addWidget(del_btn)
            self.subtasks_layout.addLayout(row)

    def _toggle_subtask_at(self, idx: int, completed: bool):
        if 0 <= idx < len(self.subtasks_data):
            self.subtasks_data[idx]["completed"] = completed

    def _remove_subtask_at(self, idx: int):
        if 0 <= idx < len(self.subtasks_data):
            self.subtasks_data.pop(idx)
            self._render_subtask_rows()

    def _validate_and_save(self):
        if not self.title_input.text().strip():
            self.title_input.setFocus()
            self.title_input.setStyleSheet(f"border: 1px solid {COLORS['rose']};")
            return
        self.accept()

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "subject": self.subj_input.currentText().strip() or t("task_default_subj"),
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self.date_edit.date().toString(Qt.DateFormat.ISODate),
            "due_time": self.time_edit.time().toString("HH:mm"),
            "priority": self.p_combo.currentData(),
            "subtasks": self.subtasks_data
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
        p_cfg = get_priority_config(priority)

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
        self.cb.setAccessibleName(f"{t('task_stat_done')}: {task.get('title', '')}")
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
        subj_lbl = QLabel(f"#{task.get('subject', t('task_default_subj'))}")
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

        # Subtasks progress pill
        subtasks = task.get("subtasks", [])
        if subtasks:
            sub_count = len(subtasks)
            sub_done = sum(1 for s in subtasks if s.get("completed"))
            sub_box = QFrame()
            sb_l = QHBoxLayout(sub_box)
            sb_l.setContentsMargins(6, 2, 7, 2)
            sb_l.setSpacing(4)
            s_col = COLORS['emerald'] if sub_done == sub_count else COLORS['sky']
            s_ico = QLabel()
            s_ico.setPixmap(get_pixmap("check_square", s_col, 12))
            sb_l.addWidget(s_ico)
            sub_lbl = QLabel(f"{sub_done}/{sub_count}")
            sub_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            sub_lbl.setStyleSheet(f"color: {s_col}; background: transparent;")
            sb_l.addWidget(sub_lbl)
            sub_box.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            """)
            meta_row.addWidget(sub_box)

        meta_row.addStretch()
        info_layout.addLayout(meta_row)

        layout.addLayout(info_layout, stretch=1)

        # Right Action Buttons (Edit, Delete) with Vector Icons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        edit_btn = QPushButton()
        edit_btn.setIcon(get_icon("edit", COLORS['text_secondary'], 16))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setFixedSize(36, 36)
        edit_btn.setToolTip(t("edit"))
        edit_btn.setAccessibleName(f"{t('edit')}: {task.get('title', '')}")
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
        del_btn.setFixedSize(36, 36)
        del_btn.setToolTip(t("delete"))
        del_btn.setAccessibleName(f"{t('delete')}: {task.get('title', '')}")
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



class KanbanTaskCard(QFrame):
    """Compact task card for Kanban columns."""
    toggled = pyqtSignal(str)
    status_changed = pyqtSignal(str, str) # task_id, new_status
    deleted = pyqtSignal(str)
    edited = pyqtSignal(str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task_id = task["id"]
        status = task.get("status", "done" if task.get("completed") else "todo")
        p_cfg = get_priority_config(task.get("priority", "medium"))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-left: 4px solid {p_cfg['color']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary_border']};
                background-color: {COLORS['bg_card_hover']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header: Subject pill + actions
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        subj_lbl = QLabel(f"#{task.get('subject', t('task_default_subj'))}")
        subj_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
        subj_lbl.setStyleSheet(f"""
            background-color: {COLORS['primary_subtle']};
            color: {COLORS['primary_light']};
            border-radius: 4px;
            padding: 1px 6px;
        """)
        top_row.addWidget(subj_lbl)
        top_row.addStretch()

        edit_btn = QPushButton()
        edit_btn.setIcon(get_icon("edit", COLORS['text_muted'], 12))
        edit_btn.setIconSize(QSize(12, 12))
        edit_btn.setFixedSize(22, 22)
        edit_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 4px; } QPushButton:hover { background-color: rgba(255,255,255,0.1); }")
        edit_btn.clicked.connect(lambda: self.edited.emit(self.task_id))
        top_row.addWidget(edit_btn)

        del_btn = QPushButton()
        del_btn.setIcon(get_icon("close", COLORS['text_muted'], 12))
        del_btn.setIconSize(QSize(12, 12))
        del_btn.setFixedSize(22, 22)
        del_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 4px; } QPushButton:hover { background-color: rgba(239, 68, 68, 0.25); }")
        del_btn.clicked.connect(lambda: self.deleted.emit(self.task_id))
        top_row.addWidget(del_btn)

        layout.addLayout(top_row)

        # Title
        title_lbl = QLabel(task.get("title", ""))
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setWordWrap(True)
        if status == "done":
            title_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; text-decoration: line-through; background: transparent;")
        else:
            title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl)

        # Meta: Deadline & Subtasks
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        due_date_str = task.get("due_date", "")
        if due_date_str:
            d_box = QHBoxLayout()
            d_box.setSpacing(3)
            d_ico = QLabel()
            d_ico.setPixmap(get_pixmap("calendar", COLORS['text_muted'], 11))
            d_box.addWidget(d_ico)
            d_lbl = QLabel(due_date_str)
            d_lbl.setFont(QFont("Segoe UI", 7))
            d_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            d_box.addWidget(d_lbl)
            meta_row.addLayout(d_box)

        subtasks = task.get("subtasks", [])
        if subtasks:
            sub_done = sum(1 for s in subtasks if s.get("completed"))
            s_box = QHBoxLayout()
            s_box.setSpacing(3)
            s_ico = QLabel()
            s_ico.setPixmap(get_pixmap("check_square", COLORS['sky'], 11))
            s_box.addWidget(s_ico)
            s_lbl = QLabel(f"{sub_done}/{len(subtasks)}")
            s_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            s_lbl.setStyleSheet(f"color: {COLORS['sky']}; background: transparent;")
            s_box.addWidget(s_lbl)
            meta_row.addLayout(s_box)

        meta_row.addStretch()
        layout.addLayout(meta_row)

        # Action move buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        if status == "todo":
            move_btn = QPushButton(t("kanban_start"))
            move_btn.setIcon(get_icon("arrow_right", COLORS["sky"], 11))
            move_btn.setFixedHeight(24)
            move_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            move_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['sky']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(56, 189, 248, 0.15);
                    border-color: {COLORS['sky']};
                }}
            """)
            move_btn.clicked.connect(lambda: self.status_changed.emit(self.task_id, "in_progress"))
            btn_row.addWidget(move_btn)

            done_btn = QPushButton(t("kanban_complete"))
            done_btn.setIcon(get_icon("check", COLORS["emerald"], 11))
            done_btn.setFixedHeight(24)
            done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            done_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['emerald']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(16, 185, 129, 0.15);
                    border-color: {COLORS['emerald']};
                }}
            """)
            done_btn.clicked.connect(lambda: self.status_changed.emit(self.task_id, "done"))
            btn_row.addWidget(done_btn)

        elif status == "in_progress":
            back_btn = QPushButton(t("kanban_back"))
            back_btn.setIcon(get_icon("rotate_ccw", COLORS["text_muted"], 11))
            back_btn.setFixedHeight(24)
            back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_muted']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    color: {COLORS['text_primary']};
                }}
            """)
            back_btn.clicked.connect(lambda: self.status_changed.emit(self.task_id, "todo"))
            btn_row.addWidget(back_btn)

            done_btn = QPushButton(t("kanban_submit"))
            done_btn.setIcon(get_icon("check", COLORS["emerald"], 11))
            done_btn.setFixedHeight(24)
            done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            done_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(16, 185, 129, 0.15);
                    color: {COLORS['emerald']};
                    border: 1px solid rgba(16, 185, 129, 0.4);
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['emerald']};
                    color: #FFFFFF;
                }}
            """)
            done_btn.clicked.connect(lambda: self.status_changed.emit(self.task_id, "done"))
            btn_row.addWidget(done_btn)

        elif status == "done":
            reopen_btn = QPushButton(t("kanban_reopen"))
            reopen_btn.setIcon(get_icon("rotate_ccw", COLORS["amber"], 11))
            reopen_btn.setFixedHeight(24)
            reopen_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            reopen_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['amber']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['amber']};
                }}
            """)
            reopen_btn.clicked.connect(lambda: self.status_changed.emit(self.task_id, "in_progress"))
            btn_row.addWidget(reopen_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

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

        # 2. Row 1: compact filter, view mode and main action
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(8)

        filters_list = [
            ("all", t("filter_all")),
            ("today", t("task_stat_today")),
            ("upcoming", t("filter_upcoming")),
            ("overdue", t("filter_overdue")),
            ("urgent", t("filter_urgent")),
            ("done", t("filter_done"))
        ]
        self.status_filter = QComboBox()
        self.status_filter.setAccessibleName(t("filter_status_accessible"))
        for f_id, label in filters_list:
            self.status_filter.addItem(label, f_id)
        self.status_filter.currentIndexChanged.connect(self._on_status_filter_changed)
        row1_layout.addWidget(self.status_filter)
        row1_layout.addStretch()

        # View Mode switcher: List / Kanban
        self.view_switcher = QFrame()
        self.view_switcher.setStyleSheet(f"""
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
                padding: 5px 12px;
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
        vs_layout = QHBoxLayout(self.view_switcher)
        vs_layout.setContentsMargins(2, 2, 2, 2)
        vs_layout.setSpacing(2)

        self.list_mode_btn = QPushButton(t("task_view_list"))
        self.list_mode_btn.setIcon(get_icon("list", "#FFFFFF", 13))
        self.list_mode_btn.setIconSize(QSize(13, 13))
        self.list_mode_btn.setCheckable(True)
        self.list_mode_btn.setChecked(True)
        self.list_mode_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.kanban_mode_btn = QPushButton(t("task_view_kanban"))
        self.kanban_mode_btn.setIcon(get_icon("kanban", COLORS["text_muted"], 13))
        self.kanban_mode_btn.setIconSize(QSize(13, 13))
        self.kanban_mode_btn.setCheckable(True)
        self.kanban_mode_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.view_group = QButtonGroup(self)
        self.view_group.addButton(self.list_mode_btn)
        self.view_group.addButton(self.kanban_mode_btn)
        self.view_group.buttonClicked.connect(self._on_view_mode_switched)

        vs_layout.addWidget(self.list_mode_btn)
        vs_layout.addWidget(self.kanban_mode_btn)
        row1_layout.addWidget(self.view_switcher)

        add_task_btn = QPushButton(t("btn_new_task"))
        add_task_btn.setIcon(get_icon("plus", "#FFFFFF", 16))
        add_task_btn.setIconSize(QSize(16, 16))
        add_task_btn.setObjectName("primary-btn")
        add_task_btn.setFixedHeight(34)
        add_task_btn.clicked.connect(self._open_new_task_dialog)
        row1_layout.addWidget(add_task_btn)

        main_layout.addLayout(row1_layout)

        self.quick_task_input = QLineEdit()
        self.quick_task_input.setPlaceholderText(t("quick_task_placeholder"))
        self.quick_task_input.setAccessibleName(t("quick_task_accessible"))
        self.quick_task_input.setToolTip(t("quick_task_hint"))
        self.quick_task_input.textChanged.connect(lambda: self.quick_task_input.setStyleSheet(""))
        self.quick_task_input.returnPressed.connect(self._add_quick_task)
        main_layout.addWidget(self.quick_task_input)

        self.quick_task_example = QLabel(t("onboarding_quick_example", date=(date.today() + timedelta(days=1)).isoformat()))
        self.quick_task_example.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        main_layout.addWidget(self.quick_task_example)

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

        row2_layout.addStretch()

        self.clear_done_btn = QPushButton(t("clear_completed"))
        self.clear_done_btn.setObjectName("ghost-btn")
        self.clear_done_btn.clicked.connect(self._clear_completed_tasks)
        row2_layout.addWidget(self.clear_done_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_tasks_ph"))
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self._render_tasks)
        row2_layout.addWidget(self.search_input)

        main_layout.addLayout(row2_layout)

        # 3. View Stack (Page 0: List, Page 1: Kanban)
        self.content_stack = QStackedWidget()

        # Page 0: List Scroll Area
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
        self.content_stack.addWidget(self.scroll_area)

        # Page 1: Kanban Board Container
        self.kanban_container = QWidget()
        self.kanban_container.setStyleSheet("background: transparent;")
        self.kanban_layout = QHBoxLayout(self.kanban_container)
        self.kanban_layout.setContentsMargins(0, 4, 0, 8)
        self.kanban_layout.setSpacing(14)

        # 3 Columns: To Do, In Progress, Done
        self.col_todo_layout, self.col_todo_badge = self._create_kanban_col(t("kanban_col_todo"), COLORS['sky'])
        self.col_inprog_layout, self.col_inprog_badge = self._create_kanban_col(t("kanban_col_in_progress"), COLORS['amber'])
        self.col_done_layout, self.col_done_badge = self._create_kanban_col(t("kanban_col_done"), COLORS['emerald'])

        self.content_stack.addWidget(self.kanban_container)
        main_layout.addWidget(self.content_stack, stretch=1)

        # Connect storage signals
        self.storage.data_changed.connect(self._on_storage_changed)

        self._update_subject_dropdown()
        self._render_tasks()

    def _on_view_mode_switched(self):
        checked_text = "#000000" if COLORS['primary'] == "#FCEE0A" else "#FFFFFF"
        for button, icon in ((self.list_mode_btn, "list"), (self.kanban_mode_btn, "kanban")):
            button.setIcon(get_icon(icon, checked_text if button.isChecked() else COLORS['text_muted'], 13))
        kanban = self.kanban_mode_btn.isChecked()
        self.status_filter.setVisible(not kanban)
        if kanban:
            self.content_stack.setCurrentIndex(1)
            self._render_kanban()
        else:
            self.content_stack.setCurrentIndex(0)
            self._render_tasks()

    def _create_kanban_col(self, title: str, accent_color: str):
        col_frame = QFrame()
        col_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid {COLORS['border_subtle']};
                border-top: 3px solid {accent_color};
                border-radius: 10px;
            }}
        """)
        l = QVBoxLayout(col_frame)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # Header
        h_row = QHBoxLayout()
        h_row.setSpacing(8)
        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        t_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        h_row.addWidget(t_lbl)

        badge_lbl = QLabel("0")
        badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        badge_lbl.setStyleSheet(f"""
            color: #FFFFFF;
            background-color: {accent_color};
            border-radius: 8px;
            padding: 2px 7px;
        """)
        h_row.addWidget(badge_lbl)
        h_row.addStretch()
        l.addLayout(h_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        col_content = QWidget()
        col_content.setStyleSheet("background: transparent;")
        cards_layout = QVBoxLayout(col_content)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(8)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(col_content)
        l.addWidget(scroll, stretch=1)

        self.kanban_layout.addWidget(col_frame, stretch=1)
        return cards_layout, badge_lbl

    def _render_kanban(self):
        clear_layout(self.col_todo_layout)
        clear_layout(self.col_inprog_layout)
        clear_layout(self.col_done_layout)

        tasks = self.storage.get_tasks()
        query = self.search_input.text().lower().strip()

        count_todo = 0
        count_inprog = 0
        count_done = 0

        for t_item in tasks:
            subj = t_item.get("subject", "")
            if self.active_subject != "all" and subj != self.active_subject:
                continue
            if query and (query not in t_item.get("title", "").lower() and query not in t_item.get("description", "").lower()):
                continue

            status = t_item.get("status", "done" if t_item.get("completed") else "todo")
            card = KanbanTaskCard(t_item)
            card.edited.connect(self._on_task_edited)
            card.deleted.connect(self._on_task_deleted)
            card.status_changed.connect(self._on_kanban_status_changed)

            if status == "done":
                self.col_done_layout.addWidget(card)
                count_done += 1
            elif status == "in_progress":
                self.col_inprog_layout.addWidget(card)
                count_inprog += 1
            else:
                self.col_todo_layout.addWidget(card)
                count_todo += 1

        self.col_todo_badge.setText(str(count_todo))
        self.col_inprog_badge.setText(str(count_inprog))
        self.col_done_badge.setText(str(count_done))

    def _on_kanban_status_changed(self, task_id: str, new_status: str):
        self.storage.update_task_status(task_id, new_status)
        self._render_kanban()
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
        icon_lbl.setObjectName("stat_icon")
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
        t_lbl.setObjectName("stat_title")
        t_lbl.setFont(QFont("Segoe UI", 9))
        t_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        l.addWidget(t_lbl)
        return card

    def refresh_theme(self):
        """Rebuild styles captured when task cards were first created."""
        checked_text = "#000000" if COLORS['primary'] == "#FCEE0A" else "#FFFFFF"
        self.view_switcher.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border_subtle']}; border-radius: 8px; padding: 1px; }}
            QPushButton {{ background: transparent; border: none; border-radius: 6px; padding: 5px 12px; color: {COLORS['text_muted']}; font-size: 11px; font-weight: 500; }}
            QPushButton:checked {{ background: {COLORS['primary']}; color: {checked_text}; font-weight: 600; }}
        """)
        for button, icon in ((self.list_mode_btn, "list"), (self.kanban_mode_btn, "kanban")):
            button.setIcon(get_icon(icon, checked_text if button.isChecked() else COLORS['text_muted'], 13))
        for card, icon_name, color in (
            (self.card_total, "tasks", COLORS['primary_light']),
            (self.card_pending, "clock", COLORS['sky']),
            (self.card_today, "alert_circle", COLORS['amber']),
            (self.card_done, "check_circle", COLORS['emerald']),
        ):
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 12px;
                    padding: 12px;
                }}
            """)
            card.findChild(QLabel, "stat_icon").setPixmap(get_pixmap(icon_name, color, 18))
            card.findChild(QLabel, "stat_value").setStyleSheet(
                f"color: {color}; background: transparent; padding-left: 6px;"
            )
            card.findChild(QLabel, "stat_title").setStyleSheet(
                f"color: {COLORS['text_muted']}; background: transparent;"
            )
        self._render_tasks()

    def _set_filter(self, filter_id: str):
        self.active_filter = filter_id
        index = self.status_filter.findData(filter_id)
        if index >= 0 and index != self.status_filter.currentIndex():
            self.status_filter.blockSignals(True)
            self.status_filter.setCurrentIndex(index)
            self.status_filter.blockSignals(False)
        self._render_tasks()

    def _on_status_filter_changed(self):
        self._set_filter(self.status_filter.currentData() or "all")

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
        self.clear_done_btn.setVisible(self.active_filter == "done" and done > 0)
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
            empty_lbl = QLabel(t("no_tasks") if not tasks else t("no_tasks_filtered"))
            empty_lbl.setFont(QFont("Segoe UI", 11))
            empty_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 24px 0 8px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.addWidget(empty_lbl)
            action = QPushButton(t("btn_new_task") if not tasks else t("clear_filters"))
            action.setObjectName("primary-btn" if not tasks else "ghost-btn")
            action.clicked.connect(self._open_new_task_dialog if not tasks else self._clear_empty_filters)
            self.tasks_layout.addWidget(action, alignment=Qt.AlignmentFlag.AlignCenter)
            if self.kanban_mode_btn.isChecked():
                self._render_kanban()
            return

        for task in sorted_tasks:
            widget = TaskItemWidget(task)
            widget.toggled.connect(self._on_task_toggled)
            widget.deleted.connect(self._on_task_deleted)
            widget.edited.connect(self._on_task_edited)
            self.tasks_layout.addWidget(widget)

        if hasattr(self, "kanban_mode_btn") and self.kanban_mode_btn.isChecked():
            self._render_kanban()

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
                priority=data["priority"],
                subtasks=data.get("subtasks", [])
            )
            self._update_subject_dropdown()
            self._render_tasks()

    def _clear_empty_filters(self):
        self.search_input.clear()
        self.subj_filter.setCurrentIndex(0)
        self._set_filter("all")

    def _add_quick_task(self):
        try:
            task_data = parse_quick_task(self.quick_task_input.text())
        except ValueError:
            self.quick_task_input.setToolTip(t("quick_task_invalid"))
            self.quick_task_input.setStyleSheet(f"border: 1px solid {COLORS['rose']};")
            self.quick_task_input.setFocus()
            return
        self.storage.add_task(**task_data)
        self.quick_task_input.clear()
        self.quick_task_input.setToolTip(t("quick_task_hint"))
        self._set_filter("all")

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
