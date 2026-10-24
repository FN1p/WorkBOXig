"""
Academic Grades & GPA Tracker Dialogs and Widget for WorkBOXig.
Provides grade management, GPA calculations, subject breakdown, and modern Qt dialogs.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QScrollArea, QWidget, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor, QColor

from src.styles import COLORS, CURRENT_THEME
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.storage import get_storage


class AddGradeDialog(QDialog):
    """Modern modal dialog for recording a new grade with subject autocomplete and weight."""

    def __init__(self, preset_subject: str = "", storage=None, parent=None):
        super().__init__(parent)
        self.storage = storage or get_storage()
        self.preset_subject = preset_subject

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 500)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_popup']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr_icon = QLabel()
        hdr_icon.setPixmap(get_pixmap("notebooks", COLORS['primary_light'], 18))
        hdr.addWidget(hdr_icon)

        title_lbl = QLabel(t("dlg_add_grade_title"))
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()

        close_btn = QPushButton()
        close_btn.setIcon(get_icon("close", COLORS["text_muted"], 14))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 14px;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        layout.addLayout(hdr)

        # 1. Subject selector (editable combobox with suggestions)
        subj_lbl = QLabel(t("dlg_grade_subject"))
        subj_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        subj_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subj_lbl)

        self.subj_combo = QComboBox()
        self.subj_combo.setEditable(True)
        known = self.storage.get_all_known_subjects()
        for s in known:
            self.subj_combo.addItem(s)
        if self.preset_subject:
            self.subj_combo.setCurrentText(self.preset_subject)
        self.subj_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.subj_combo)

        # 2. Score & Weight (Side-by-side)
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Grade value
        g_vbox = QVBoxLayout()
        g_lbl = QLabel(t("dlg_grade_value"))
        g_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        g_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        g_vbox.addWidget(g_lbl)

        self.grade_combo = QComboBox()
        self.grade_combo.addItem("5  —  Отлично (A)", 5.0)
        self.grade_combo.addItem("4  —  Хорошо (B)", 4.0)
        self.grade_combo.addItem("3  —  Удовл. (C)", 3.0)
        self.grade_combo.addItem("2  —  Неуд. (F)", 2.0)
        self.grade_combo.setEditable(True)
        self.grade_combo.setStyleSheet(self.subj_combo.styleSheet())
        g_vbox.addWidget(self.grade_combo)
        row1.addLayout(g_vbox)

        # Weight
        w_vbox = QVBoxLayout()
        w_lbl = QLabel(t("dlg_grade_weight"))
        w_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        w_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        w_vbox.addWidget(w_lbl)

        self.weight_combo = QComboBox()
        self.weight_combo.addItem(t("weight_normal"), 1.0)
        self.weight_combo.addItem(t("weight_high"), 1.5)
        self.weight_combo.addItem(t("weight_major"), 2.0)
        self.weight_combo.setStyleSheet(self.subj_combo.styleSheet())
        w_vbox.addWidget(self.weight_combo)
        row1.addLayout(w_vbox)
        layout.addLayout(row1)

        # 3. Type & Date
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Type
        t_vbox = QVBoxLayout()
        t_lbl = QLabel(t("dlg_grade_type"))
        t_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        t_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        t_vbox.addWidget(t_lbl)

        self.type_combo = QComboBox()
        self.type_combo.addItem(t("grade_type_exam"), "exam")
        self.type_combo.addItem(t("grade_type_credit"), "credit")
        self.type_combo.addItem(t("grade_type_test"), "test")
        self.type_combo.addItem(t("grade_type_homework"), "homework")
        self.type_combo.addItem(t("grade_type_classwork"), "classwork")
        self.type_combo.setStyleSheet(self.subj_combo.styleSheet())
        t_vbox.addWidget(self.type_combo)
        row2.addLayout(t_vbox)

        # Date
        d_vbox = QVBoxLayout()
        d_lbl = QLabel(t("dlg_grade_date"))
        d_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        d_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        d_vbox.addWidget(d_lbl)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet(self.subj_combo.styleSheet())
        d_vbox.addWidget(self.date_edit)
        row2.addLayout(d_vbox)
        layout.addLayout(row2)

        # 4. Topic / Comment
        note_lbl = QLabel(t("dlg_grade_comment"))
        note_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        note_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(note_lbl)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Например: Коллоквиум по дифференциалам")
        self.note_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.note_edit)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(t("save"))
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _on_save(self):
        subj = self.subj_combo.currentText().strip()
        if not subj:
            return

        # Parse grade value
        raw_val = self.grade_combo.currentData()
        if raw_val is None:
            # Entered custom text
            try:
                first_token = self.grade_combo.currentText().split()[0]
                grade_num = float(first_token)
            except Exception:
                grade_num = 5.0
        else:
            grade_num = float(raw_val)

        weight = float(self.weight_combo.currentData() or 1.0)
        g_type = str(self.type_combo.currentData() or "exam")
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        note = self.note_edit.text().strip()

        self.storage.add_grade(
            subject=subj,
            grade=grade_num,
            weight=weight,
            date_str=date_str,
            note=note,
            grade_type=g_type
        )
        self.accept()


class GradesManagementDialog(QDialog):
    """Full-featured Gradebook viewer dialog allowing filtering, editing, and deleting grades."""

    def __init__(self, storage=None, parent=None):
        super().__init__(parent)
        self.storage = storage or get_storage()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(680, 520)
        self.resize(720, 540)

        self._init_ui()
        self._refresh_table()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_popup']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header with GPA badge and close button
        hdr = QHBoxLayout()
        hdr_icon = QLabel()
        hdr_icon.setPixmap(get_pixmap("notebooks", COLORS['primary_light'], 20))
        hdr.addWidget(hdr_icon)

        title_lbl = QLabel(t("section_grades_title"))
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        hdr.addWidget(title_lbl)

        hdr.addStretch()

        self.gpa_pill = QLabel("")
        self.gpa_pill.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.gpa_pill.setStyleSheet(f"""
            color: {COLORS['emerald']};
            background-color: {COLORS['emerald_subtle']};
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 8px;
            padding: 3px 10px;
        """)
        hdr.addWidget(self.gpa_pill)

        close_btn = QPushButton()
        close_btn.setIcon(get_icon("close", COLORS["text_muted"], 14))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 14px;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        hdr.addWidget(close_btn)
        layout.addLayout(hdr)

        # Filter bar
        flt_row = QHBoxLayout()
        flt_lbl = QLabel("Предмет:")
        flt_lbl.setFont(QFont("Segoe UI", 9))
        flt_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        flt_row.addWidget(flt_lbl)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все предметы", "")
        for s in self.storage.get_subjects_with_grades():
            self.filter_combo.addItem(s, s)
        self.filter_combo.currentIndexChanged.connect(self._refresh_table)
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            }}
        """)
        flt_row.addWidget(self.filter_combo)
        flt_row.addStretch()

        add_btn = QPushButton(t("add_grade_btn"))
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        add_btn.clicked.connect(self._open_add_dialog)
        flt_row.addWidget(add_btn)
        layout.addLayout(flt_row)

        # Table of grades
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Дата", "Предмет", "Оценка", "Вес", "Тип / Тема", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                alternate-background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                gridline-color: {COLORS['border_subtle']};
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
                border: none;
                padding: 6px;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.table)

        main_layout.addWidget(card)

    def _open_add_dialog(self):
        selected_subject = self.filter_combo.currentData() or ""
        dlg = AddGradeDialog(preset_subject=selected_subject, storage=self.storage, parent=self)
        if dlg.exec():
            self._refresh_table()

    def _refresh_table(self):
        subj = self.filter_combo.currentData()
        grades = self.storage.get_grades(subj if subj else None)

        # Update overall GPA
        overall = self.storage.get_overall_gpa()
        self.gpa_pill.setText(f"GPA: {overall:.2f}")

        self.table.setRowCount(len(grades))
        for row, g in enumerate(reversed(grades)):
            # 0. Date
            d_item = QTableWidgetItem(g.get("date", ""))
            d_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, d_item)

            # 1. Subject
            s_item = QTableWidgetItem(g.get("subject", ""))
            self.table.setItem(row, 1, s_item)

            # 2. Grade
            val = g.get("grade", 0)
            val_str = f"{val:.1f}" if isinstance(val, float) and not val.is_integer() else f"{int(val)}"
            g_item = QTableWidgetItem(f"  {val_str}  ")
            g_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            g_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            # Color code grade
            if val >= 4.5:
                g_item.setForeground(QColor(COLORS['emerald']))
            elif val >= 3.5:
                g_item.setForeground(QColor(COLORS['sky']))
            elif val >= 2.5:
                g_item.setForeground(QColor(COLORS['amber']))
            else:
                g_item.setForeground(QColor(COLORS['rose']))
            self.table.setItem(row, 2, g_item)

            # 3. Weight
            w_item = QTableWidgetItem(f"x{g.get('weight', 1.0):.1f}")
            w_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            w_item.setForeground(QColor(COLORS['text_muted']))
            self.table.setItem(row, 3, w_item)

            # 4. Type & Comment
            t_type = g.get("grade_type", "")
            t_note = g.get("note", "")
            desc = f"[{t_type}] {t_note}" if t_note else f"[{t_type}]"
            self.table.setItem(row, 4, QTableWidgetItem(desc))

            # 5. Delete Action button
            del_btn = QPushButton()
            del_btn.setIcon(get_icon("trash", COLORS["rose"], 14))
            del_btn.setFixedSize(28, 24)
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: rgba(244, 63, 94, 0.15);
                    border-radius: 4px;
                }}
            """)
            gid = g["id"]
            del_btn.clicked.connect(lambda ch, item_id=gid: self._delete_grade(item_id))
            self.table.setCellWidget(row, 5, del_btn)

    def _delete_grade(self, grade_id: str):
        self.storage.delete_grade(grade_id)
        self._refresh_table()


class GradesTrackerWidget(QFrame):
    """Compact and modern GPA & Grades Tracker Card for Dashboard."""

    grade_added = pyqtSignal()

    def __init__(self, storage=None, parent=None):
        super().__init__(parent)
        self.storage = storage or get_storage()
        self.setObjectName("grades_tracker_card")
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QFrame#grades_tracker_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 16, 18, 16)
        self.main_layout.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("notebooks", COLORS['sky'], 18))
        icon_lbl.setStyleSheet("background: transparent;")
        hdr.addWidget(icon_lbl)

        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        self.title_lbl = QLabel(t("section_grades_title"))
        self.title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        vbox.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(t("section_grades_sub"))
        self.sub_lbl.setFont(QFont("Segoe UI", 8))
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        vbox.addWidget(self.sub_lbl)
        hdr.addLayout(vbox)

        hdr.addStretch()

        # Action Buttons
        self.manage_btn = QPushButton(t("manage_grades_btn"))
        self.manage_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.manage_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
                border-color: {COLORS['border_light']};
            }}
        """)
        self.manage_btn.clicked.connect(self._open_manage_dialog)
        hdr.addWidget(self.manage_btn)

        self.add_btn = QPushButton(t("add_grade_btn"))
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.add_btn.clicked.connect(self._open_add_dialog)
        hdr.addWidget(self.add_btn)

        self.main_layout.addLayout(hdr)

        # Overview GPA Bar and Status
        self.gpa_box = QFrame()
        self.gpa_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary_subtle']}, stop:1 rgba(0, 0, 0, 0.05));
            border: 1px solid {COLORS['primary_border']};
            border-radius: 10px;
            padding: 10px 14px;
        """)
        gb_layout = QHBoxLayout(self.gpa_box)
        gb_layout.setContentsMargins(0, 0, 0, 0)
        gb_layout.setSpacing(14)

        self.star_icon = QLabel()
        self.star_icon.setPixmap(get_pixmap("star", COLORS['emerald'], 22))
        self.star_icon.setStyleSheet("background: transparent;")
        gb_layout.addWidget(self.star_icon)

        self.gpa_val_lbl = QLabel("0.00")
        self.gpa_val_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.gpa_val_lbl.setStyleSheet(f"color: {COLORS['emerald']}; background: transparent;")
        gb_layout.addWidget(self.gpa_val_lbl)

        gpa_info_vbox = QVBoxLayout()
        gpa_info_vbox.setSpacing(2)
        self.gpa_title_lbl = QLabel(t("overall_gpa_label"))
        self.gpa_title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.gpa_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        gpa_info_vbox.addWidget(self.gpa_title_lbl)

        self.gpa_status_lbl = QLabel(t("gpa_status_satisfactory"))
        self.gpa_status_lbl.setFont(QFont("Segoe UI", 8))
        self.gpa_status_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        gpa_info_vbox.addWidget(self.gpa_status_lbl)
        gb_layout.addLayout(gpa_info_vbox)

        gb_layout.addStretch()

        self.total_grades_lbl = QLabel("0 оценок")
        self.total_grades_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.total_grades_lbl.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            background-color: {COLORS['bg_input']};
            border: 1px solid {COLORS['border_subtle']};
            border-radius: 6px;
            padding: 3px 10px;
        """)
        gb_layout.addWidget(self.total_grades_lbl)

        self.main_layout.addWidget(self.gpa_box)

        # Subjects Grid / Chips
        self.subjects_container = QWidget()
        self.subjects_container.setStyleSheet("background: transparent;")
        self.subjects_layout = QGridLayout(self.subjects_container)
        self.subjects_layout.setContentsMargins(0, 4, 0, 0)
        self.subjects_layout.setSpacing(8)
        self.main_layout.addWidget(self.subjects_container)

    def _open_add_dialog(self):
        dlg = AddGradeDialog(storage=self.storage, parent=self)
        if dlg.exec():
            self.refresh_data()
            self.grade_added.emit()

    def _open_manage_dialog(self):
        dlg = GradesManagementDialog(storage=self.storage, parent=self)
        dlg.exec()
        self.refresh_data()

    def refresh_data(self):
        """Update GPA stats and subject grade pills."""
        all_grades = self.storage.get_grades()
        overall = self.storage.get_overall_gpa()

        self.gpa_val_lbl.setText(f"{overall:.2f}" if overall > 0 else "—")
        self.total_grades_lbl.setText(f"{len(all_grades)} оценок")

        if overall >= 4.75:
            self.gpa_status_lbl.setText(t("gpa_status_excellent"))
            self.gpa_val_lbl.setStyleSheet(f"color: {COLORS['emerald']}; background: transparent;")
        elif overall >= 4.0:
            self.gpa_status_lbl.setText(t("gpa_status_good"))
            self.gpa_val_lbl.setStyleSheet(f"color: {COLORS['sky']}; background: transparent;")
        elif overall >= 3.0:
            self.gpa_status_lbl.setText(t("gpa_status_satisfactory"))
            self.gpa_val_lbl.setStyleSheet(f"color: {COLORS['amber']}; background: transparent;")
        else:
            self.gpa_status_lbl.setText(t("gpa_status_attention"))
            self.gpa_val_lbl.setStyleSheet(f"color: {COLORS['rose']}; background: transparent;")

        # Clear subjects container
        while self.subjects_layout.count():
            item = self.subjects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subjects = self.storage.get_subjects_with_grades()
        if not subjects:
            empty = QLabel(t("no_grades_yet"))
            empty.setFont(QFont("Segoe UI", 9))
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-style: italic; padding: 8px 0;")
            self.subjects_layout.addWidget(empty, 0, 0)
            return

        # Render each subject card in 2 columns
        for idx, subj in enumerate(subjects):
            s_gpa = self.storage.get_subject_gpa(subj)
            s_grades = self.storage.get_grades(subj)

            s_card = QFrame()
            s_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            s_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_input']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 8px;
                    padding: 6px 10px;
                }}
                QFrame:hover {{
                    border-color: {COLORS['primary_border']};
                    background-color: {COLORS['bg_card_hover']};
                }}
            """)
            sc_l = QHBoxLayout(s_card)
            sc_l.setContentsMargins(6, 4, 6, 4)
            sc_l.setSpacing(8)

            s_title = QLabel(subj)
            s_title.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            s_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            sc_l.addWidget(s_title, stretch=1)

            # Recent grade tokens (last 4)
            tokens_box = QHBoxLayout()
            tokens_box.setSpacing(4)
            for g in s_grades[-4:]:
                val = g.get("grade", 0)
                val_str = f"{int(val)}" if isinstance(val, (int, float)) and float(val).is_integer() else f"{val:.1f}"
                tok = QLabel(val_str)
                tok.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                bg_col = (
                    "rgba(16, 185, 129, 0.2)" if val >= 4.5 else
                    "rgba(56, 189, 248, 0.2)" if val >= 3.5 else
                    "rgba(245, 158, 11, 0.2)" if val >= 2.5 else
                    "rgba(244, 63, 94, 0.2)"
                )
                fg_col = (
                    COLORS['emerald'] if val >= 4.5 else
                    COLORS['sky'] if val >= 3.5 else
                    COLORS['amber'] if val >= 2.5 else
                    COLORS['rose']
                )
                tok.setStyleSheet(f"color: {fg_col}; background-color: {bg_col}; border-radius: 4px; padding: 1px 5px;")
                tokens_box.addWidget(tok)
            sc_l.addLayout(tokens_box)

            # Subject GPA Badge
            b_frame = QFrame()
            bf_l = QHBoxLayout(b_frame)
            bf_l.setContentsMargins(5, 2, 6, 2)
            bf_l.setSpacing(4)
            s_ico = QLabel()
            s_ico.setPixmap(get_pixmap("star", COLORS['primary_light'], 11))
            bf_l.addWidget(s_ico)
            gpa_badge = QLabel(f"{s_gpa:.2f}")
            gpa_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            gpa_badge.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent;")
            bf_l.addWidget(gpa_badge)
            b_frame.setStyleSheet(f"""
                background-color: {COLORS['primary_subtle']};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 6px;
            """)
            sc_l.addWidget(b_frame)

            # Clicking subject card opens manage dialog pre-filtered
            s_card.mousePressEvent = lambda e, s=subj: self._open_subject_grades(s)

            row = idx // 2
            col = idx % 2
            self.subjects_layout.addWidget(s_card, row, col)

    def _open_subject_grades(self, subject: str):
        dlg = GradesManagementDialog(storage=self.storage, parent=self)
        idx = dlg.filter_combo.findData(subject)
        if idx >= 0:
            dlg.filter_combo.setCurrentIndex(idx)
        dlg.exec()
        self.refresh_data()
