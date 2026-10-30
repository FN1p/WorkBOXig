"""
Settings View for WorkBOXig.
Provides categorized settings navigation (Appearance, Bells & Schedule, Focus,
System/Windows, Data & Backups, About) with custom Bell Schedule configurator.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame, QScrollArea,
    QStackedWidget, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTime
from PyQt6.QtGui import QFont, QCursor

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t, get_i18n, get_language, set_language
from src.storage import get_storage, DEFAULT_BELL_SCHEDULE
from src.icons import get_pixmap, get_icon
from src.version import __version__
from src.utils.updater import CheckUpdateThread
from src.components.update_dialog import UpdateDialog
from src.utils.autostart import (
    is_autostart_supported, is_autostart_enabled, set_autostart_enabled
)


class SettingsCard(QFrame):
    """Clean grouped settings container card."""
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 14px;
                padding: 18px;
            }}
        """)
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(18, 16, 18, 18)
        self.card_layout.setSpacing(14)

        header_l = QVBoxLayout()
        header_l.setSpacing(3)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_l.addWidget(self.title_lbl)

        if subtitle:
            self.sub_lbl = QLabel(subtitle)
            self.sub_lbl.setFont(QFont("Segoe UI", 9))
            self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            header_l.addWidget(self.sub_lbl)

        self.card_layout.addLayout(header_l)

    def add_widget(self, widget: QWidget):
        self.card_layout.addWidget(widget)

    def add_layout(self, layout):
        self.card_layout.addLayout(layout)


class SettingsView(QWidget):
    """Categorized Settings View coordinating appearance, bells, system, timer, and data."""
    theme_changed = pyqtSignal(str) # 'dark' or 'light'
    toast_requested = pyqtSignal(str, str) # message, type
    test_notification_requested = pyqtSignal()
    show_onboarding_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self._check_update_thread = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(20)

        # ----------------- 1. LEFT CATEGORY SIDEBAR -----------------
        cat_sidebar = QFrame()
        cat_sidebar.setFixedWidth(240)
        cat_sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 14px;
            }}
        """)
        cat_layout = QVBoxLayout(cat_sidebar)
        cat_layout.setContentsMargins(12, 16, 12, 16)
        cat_layout.setSpacing(6)

        cat_title = QLabel(t("settings_title"))
        cat_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        cat_title.setStyleSheet(f"color: {COLORS['text_primary']}; padding-left: 8px; margin-bottom: 6px;")
        cat_layout.addWidget(cat_title)

        self.cat_buttons: Dict[str, QPushButton] = {}
        categories = [
            ("appearance", t("settings_cat_appearance"), "palette"),
            ("bells", t("settings_cat_bells"), "clock"),
            ("focus", t("settings_cat_focus"), "focus"),
            ("system", t("settings_cat_system"), "activity"),
            ("data", t("settings_cat_data"), "database"),
            ("about", t("settings_cat_about"), "alert_circle"),
        ]

        for idx, (cat_id, cat_name, icon_name) in enumerate(categories):
            btn = QPushButton(cat_name)
            btn.setIcon(get_icon(icon_name, COLORS['text_secondary'], 16))
            btn.setIconSize(QSize(16, 16))
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda ch, i=idx, cid=cat_id: self._switch_category(i, cid))
            cat_layout.addWidget(btn)
            self.cat_buttons[cat_id] = btn

        cat_layout.addStretch()
        main_layout.addWidget(cat_sidebar)

        # ----------------- 2. RIGHT STACKED CONTENT -----------------
        self.stack = QStackedWidget()

        # Page 0: Appearance & Language
        self.stack.addWidget(self._create_appearance_page())

        # Page 1: Bells & Schedule
        self.stack.addWidget(self._create_bells_page())

        # Page 2: Focus & Timer
        self.stack.addWidget(self._create_focus_page())

        # Page 3: System & Windows
        self.stack.addWidget(self._create_system_page())

        # Page 4: Data & Backups
        self.stack.addWidget(self._create_data_page())

        # Page 5: About App
        self.stack.addWidget(self._create_about_page())

        main_layout.addWidget(self.stack, stretch=1)

        # Default to first category
        self._switch_category(0, "appearance")

        # Initial UI states
        self._update_theme_buttons(self.storage.get_setting("theme", "dark"))
        self._update_lang_buttons(self.storage.get_setting("language", "en"))

    def _switch_category(self, page_index: int, category_id: str):
        self.stack.setCurrentIndex(page_index)
        for cid, btn in self.cat_buttons.items():
            is_active = (cid == category_id)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        text-align: left;
                        padding-left: 14px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {COLORS['text_secondary']};
                        border: none;
                        border-radius: 8px;
                        font-weight: 500;
                        font-size: 12px;
                        text-align: left;
                        padding-left: 14px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg_card_hover']};
                        color: {COLORS['text_primary']};
                    }}
                """)

    def _wrap_in_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setWidget(widget)
        return scroll

    # ----------------- PAGE BUILDERS -----------------

    def _create_appearance_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        # 1. Language Card
        self.lang_card = SettingsCard(t("card_language"), t("card_language_sub"))
        lang_row = QHBoxLayout()
        lang_row.setSpacing(16)

        self.ru_btn = QPushButton(t("lang_ru"))
        self.ru_btn.setIcon(get_icon("globe", COLORS['primary_light'], 16))
        self.ru_btn.setCheckable(True)
        self.ru_btn.setFixedHeight(48)
        self.ru_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ru_btn.clicked.connect(lambda: self._select_language("ru"))

        self.en_btn = QPushButton("English")
        self.en_btn.setIcon(get_icon("globe", COLORS['primary_light'], 16))
        self.en_btn.setCheckable(True)
        self.en_btn.setFixedHeight(48)
        self.en_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.en_btn.clicked.connect(lambda: self._select_language("en"))

        lang_row.addWidget(self.ru_btn)
        lang_row.addWidget(self.en_btn)
        self.lang_card.add_layout(lang_row)
        layout.addWidget(self.lang_card)

        # 2. Appearance Card
        theme_card = SettingsCard(t("card_appearance"), t("card_appearance_sub"))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)

        self.dark_btn = QPushButton(t("theme_dark"))
        self.dark_btn.setCheckable(True)
        self.dark_btn.setIcon(get_icon("moon", "#FFFFFF", 18))
        self.dark_btn.setIconSize(QSize(18, 18))
        self.dark_btn.setFixedHeight(50)
        self.dark_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dark_btn.clicked.connect(lambda: self._select_theme("dark"))

        self.light_btn = QPushButton(t("theme_light"))
        self.light_btn.setCheckable(True)
        self.light_btn.setIcon(get_icon("sun", "#F59E0B", 18))
        self.light_btn.setIconSize(QSize(18, 18))
        self.light_btn.setFixedHeight(50)
        self.light_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.light_btn.clicked.connect(lambda: self._select_theme("light"))

        self.cyber_btn = QPushButton("Cyberpunk Neon (Edgerunner)")
        self.cyber_btn.setCheckable(True)
        self.cyber_btn.setIcon(get_icon("zap", "#FCEE0A", 18))
        self.cyber_btn.setIconSize(QSize(18, 18))
        self.cyber_btn.setFixedHeight(50)
        self.cyber_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cyber_btn.clicked.connect(lambda: self._select_theme("cyberpunk"))

        theme_row.addWidget(self.dark_btn)
        theme_row.addWidget(self.light_btn)
        theme_row.addWidget(self.cyber_btn)
        theme_card.add_layout(theme_row)
        layout.addWidget(theme_card)

        layout.addStretch()
        return self._wrap_in_scroll(container)

    def _create_bells_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        bells_card = SettingsCard(
            t("settings_cat_bells"),
            t("bell_settings_desc")
        )

        self.bell_editors = []
        schedule = self.storage.get_bell_schedule()

        grid = QVBoxLayout()
        grid.setSpacing(8)

        for item in schedule:
            row = QHBoxLayout()
            row.setSpacing(12)

            num_lbl = QLabel(f"{t('bell_number')} {item.get('number', 1)}:")
            num_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            num_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 80px;")
            row.addWidget(num_lbl)

            s_lbl = QLabel(f"{t('bell_start')}:")
            s_lbl.setFont(QFont("Segoe UI", 9))
            s_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            row.addWidget(s_lbl)

            s_edit = QTimeEdit()
            s_edit.setDisplayFormat("HH:mm")
            s_edit.setFixedHeight(34)
            s_edit.setTime(QTime.fromString(item.get("start", "08:30"), "HH:mm"))
            row.addWidget(s_edit)

            e_lbl = QLabel(f"{t('bell_end')}:")
            e_lbl.setFont(QFont("Segoe UI", 9))
            e_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            row.addWidget(e_lbl)

            e_edit = QTimeEdit()
            e_edit.setDisplayFormat("HH:mm")
            e_edit.setFixedHeight(34)
            e_edit.setTime(QTime.fromString(item.get("end", "10:00"), "HH:mm"))
            row.addWidget(e_edit)

            row.addStretch()
            grid.addLayout(row)
            self.bell_editors.append((item.get("number", 1), s_edit, e_edit))

        bells_card.add_layout(grid)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        save_bells_btn = QPushButton(t("bell_save"))
        save_bells_btn.setObjectName("primary-btn")
        save_bells_btn.setFixedHeight(38)
        save_bells_btn.clicked.connect(self._save_bell_schedule)
        btn_row.addWidget(save_bells_btn)

        reset_bells_btn = QPushButton(t("bell_reset"))
        reset_bells_btn.setFixedHeight(38)
        reset_bells_btn.clicked.connect(self._reset_bell_schedule)
        btn_row.addWidget(reset_bells_btn)
        btn_row.addStretch()

        bells_card.add_layout(btn_row)
        layout.addWidget(bells_card)
        layout.addStretch()
        return self._wrap_in_scroll(container)

    def _save_bell_schedule(self):
        new_schedule = []
        for num, s_edit, e_edit in self.bell_editors:
            new_schedule.append({
                "number": num,
                "start": s_edit.time().toString("HH:mm"),
                "end": e_edit.time().toString("HH:mm")
            })
        self.storage.set_bell_schedule(new_schedule)
        self.toast_requested.emit(t("bell_saved_toast"), "check")

    def _reset_bell_schedule(self):
        self.storage.set_bell_schedule(DEFAULT_BELL_SCHEDULE)
        for idx, (num, s_edit, e_edit) in enumerate(self.bell_editors):
            if idx < len(DEFAULT_BELL_SCHEDULE):
                def_item = DEFAULT_BELL_SCHEDULE[idx]
                s_edit.setTime(QTime.fromString(def_item["start"], "HH:mm"))
                e_edit.setTime(QTime.fromString(def_item["end"], "HH:mm"))
        self.toast_requested.emit(t("bell_reset_toast"), "check")

    def _create_focus_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        focus_card = SettingsCard(t("card_focus"), t("card_focus_sub"))

        sound_row = QHBoxLayout()
        sound_row.setSpacing(12)
        self.sound_cb = QCheckBox(t("sound_alert_cb"))
        self.sound_cb.setFont(QFont("Segoe UI", 10))
        self.sound_cb.setChecked(self.storage.get_setting("sound_alert", True))
        self.sound_cb.toggled.connect(lambda ch: self.storage.set_setting("sound_alert", ch))
        sound_row.addWidget(self.sound_cb)
        sound_row.addStretch()
        focus_card.add_layout(sound_row)

        timer_config_row = QHBoxLayout()
        timer_config_row.setSpacing(16)

        f_lbl = QLabel(t("focus_duration_lbl"))
        f_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        timer_config_row.addWidget(f_lbl)

        self.focus_combo = QComboBox()
        for m in [20, 25, 30, 45, 50, 60]:
            self.focus_combo.addItem(f"{m} {t('settings_min')}", m)
        saved_f = self.storage.get_setting("focus_minutes", 25)
        for i in range(self.focus_combo.count()):
            if self.focus_combo.itemData(i) == saved_f:
                self.focus_combo.setCurrentIndex(i)
                break
        self.focus_combo.currentIndexChanged.connect(self._on_focus_time_changed)
        timer_config_row.addWidget(self.focus_combo)

        b_lbl = QLabel(t("break_duration_lbl"))
        b_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        timer_config_row.addWidget(b_lbl)

        self.break_combo = QComboBox()
        for m in [5, 10, 15]:
            self.break_combo.addItem(f"{m} {t('settings_min')}", m)
        saved_b = self.storage.get_setting("break_minutes", 5)
        for i in range(self.break_combo.count()):
            if self.break_combo.itemData(i) == saved_b:
                self.break_combo.setCurrentIndex(i)
                break
        self.break_combo.currentIndexChanged.connect(self._on_break_time_changed)
        timer_config_row.addWidget(self.break_combo)
        timer_config_row.addStretch()

        focus_card.add_layout(timer_config_row)
        layout.addWidget(focus_card)
        layout.addStretch()
        return self._wrap_in_scroll(container)

    def _create_system_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        # Autostart
        startup_card = SettingsCard(t("card_autostart"), t("card_autostart_sub"))
        startup_row = QHBoxLayout()
        startup_row.setSpacing(12)

        self.autostart_cb = QCheckBox(t("autostart_cb"))
        self.autostart_cb.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.autostart_cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.autostart_cb.setChecked(is_autostart_enabled())
        self.autostart_cb.toggled.connect(self._on_autostart_toggled)
        startup_row.addWidget(self.autostart_cb)
        startup_row.addStretch()

        self.autostart_status = QLabel()
        self.autostart_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._update_autostart_status_pill(is_autostart_enabled())
        startup_row.addWidget(self.autostart_status)
        startup_card.add_layout(startup_row)
        layout.addWidget(startup_card)

        # Close Action
        self.close_action_card = SettingsCard(t("card_close_action"), t("card_close_action_sub"))
        close_row = QHBoxLayout()
        close_row.setSpacing(16)

        c_lbl = QLabel(t("card_close_action") + ":")
        c_lbl.setFont(QFont("Segoe UI", 10))
        c_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        close_row.addWidget(c_lbl)

        self.close_combo = QComboBox()
        self.close_combo.addItem(t("close_action_ask"), "ask")
        self.close_combo.addItem(t("close_action_tray"), "tray")
        self.close_combo.addItem(t("close_action_exit"), "exit")
        saved_action = self.storage.get_setting("close_action", "ask")
        idx_close = self.close_combo.findData(saved_action)
        if idx_close >= 0:
            self.close_combo.setCurrentIndex(idx_close)
        self.close_combo.currentIndexChanged.connect(self._on_close_action_changed)
        close_row.addWidget(self.close_combo)
        close_row.addStretch()

        self.close_action_card.add_layout(close_row)
        layout.addWidget(self.close_action_card)

        # Desktop Notifications
        notif_card = SettingsCard(t("card_notifications"), t("card_notifications_sub"))
        notif_row = QHBoxLayout()
        notif_row.setSpacing(12)
        self.notif_lessons_cb = QCheckBox(t("notif_lessons_cb"))
        self.notif_lessons_cb.setFont(QFont("Segoe UI", 10))
        self.notif_lessons_cb.setChecked(self.storage.get_setting("notif_lessons", True))
        self.notif_lessons_cb.toggled.connect(lambda ch: self.storage.set_setting("notif_lessons", ch))
        notif_row.addWidget(self.notif_lessons_cb)
        notif_row.addStretch()

        test_notif_btn = QPushButton(t("test_notif_btn"))
        test_notif_btn.setIcon(get_icon("zap", COLORS['primary_light'], 16))
        test_notif_btn.setIconSize(QSize(16, 16))
        test_notif_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        test_notif_btn.clicked.connect(self.test_notification_requested.emit)
        notif_row.addWidget(test_notif_btn)
        notif_card.add_layout(notif_row)

        tasks_notif_row = QHBoxLayout()
        tasks_notif_row.setSpacing(12)
        self.notif_tasks_cb = QCheckBox(t("notif_tasks_cb"))
        self.notif_tasks_cb.setFont(QFont("Segoe UI", 10))
        self.notif_tasks_cb.setChecked(self.storage.get_setting("notif_tasks", True))
        self.notif_tasks_cb.toggled.connect(lambda ch: self.storage.set_setting("notif_tasks", ch))
        tasks_notif_row.addWidget(self.notif_tasks_cb)
        tasks_notif_row.addStretch()
        notif_card.add_layout(tasks_notif_row)

        layout.addWidget(notif_card)
        layout.addStretch()
        return self._wrap_in_scroll(container)

    def _create_data_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        data_card = SettingsCard(t("card_data"), t("card_data_sub"))
        data_actions = QHBoxLayout()
        data_actions.setSpacing(12)

        export_btn = QPushButton(t("export_btn"))
        export_btn.setIcon(get_icon("database", COLORS['sky'], 16))
        export_btn.setIconSize(QSize(16, 16))
        export_btn.clicked.connect(self._export_backup)
        data_actions.addWidget(export_btn)

        import_btn = QPushButton(t("import_btn"))
        import_btn.setIcon(get_icon("folder", COLORS['amber'], 16))
        import_btn.setIconSize(QSize(16, 16))
        import_btn.clicked.connect(self._import_backup)
        data_actions.addWidget(import_btn)

        open_folder_btn = QPushButton(t("open_folder_btn"))
        open_folder_btn.setIcon(get_icon("export", COLORS['text_muted'], 16))
        open_folder_btn.setIconSize(QSize(16, 16))
        open_folder_btn.clicked.connect(self._open_data_folder)
        data_actions.addWidget(open_folder_btn)

        data_actions.addStretch()
        data_card.add_layout(data_actions)
        layout.addWidget(data_card)
        layout.addStretch()
        return self._wrap_in_scroll(container)

    def _create_about_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 16)
        layout.setSpacing(16)

        # Updates
        updates_card = SettingsCard(t("card_updates"), t("card_updates_sub"))
        updates_layout = QVBoxLayout()
        updates_layout.setSpacing(12)

        up_row1 = QHBoxLayout()
        up_row1.setSpacing(12)

        self.ver_status_lbl = QLabel(f"WorkBOXig v{__version__}")
        self.ver_status_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.ver_status_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        up_row1.addWidget(self.ver_status_lbl)

        self.update_status_pill = QLabel(t("up_to_date_status", version=__version__))
        self.update_status_pill.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.update_status_pill.setStyleSheet(f"color: {COLORS['emerald']}; background-color: rgba(16, 185, 129, 0.12); padding: 4px 10px; border-radius: 6px;")
        up_row1.addWidget(self.update_status_pill)
        up_row1.addStretch()

        self.check_updates_btn = QPushButton(t("check_updates_btn"))
        self.check_updates_btn.setIcon(get_icon("zap", COLORS['primary_light'], 16))
        self.check_updates_btn.setIconSize(QSize(16, 16))
        self.check_updates_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.check_updates_btn.clicked.connect(self._check_updates)
        up_row1.addWidget(self.check_updates_btn)
        updates_layout.addLayout(up_row1)

        up_row2 = QHBoxLayout()
        self.auto_update_cb = QCheckBox(t("auto_check_updates_cb"))
        self.auto_update_cb.setFont(QFont("Segoe UI", 10))
        self.auto_update_cb.setChecked(self.storage.get_setting("check_updates_on_startup", True))
        self.auto_update_cb.toggled.connect(lambda ch: self.storage.set_setting("check_updates_on_startup", ch))
        up_row2.addWidget(self.auto_update_cb)
        up_row2.addStretch()
        updates_layout.addLayout(up_row2)

        # Explicit opt-in: regular users never receive beta builds by default.
        self.beta_updates_cb = QCheckBox(t("receive_beta_updates_cb"))
        self.beta_updates_cb.setFont(QFont("Segoe UI", 10))
        self.beta_updates_cb.setChecked(
            self.storage.get_setting("update_channel", "stable") == "beta"
        )
        self.beta_updates_cb.toggled.connect(self._on_beta_updates_toggled)
        updates_layout.addWidget(self.beta_updates_cb)

        self.beta_updates_hint = QLabel(t("receive_beta_updates_hint"))
        self.beta_updates_hint.setWordWrap(True)
        self.beta_updates_hint.setFont(QFont("Segoe UI", 9))
        self.beta_updates_hint.setStyleSheet(f"color: {COLORS['text_muted']};")
        updates_layout.addWidget(self.beta_updates_hint)

        up_safety = QLabel(t("data_safe_guarantee"))
        up_safety.setWordWrap(True)
        up_safety.setFont(QFont("Segoe UI", 9))
        up_safety.setStyleSheet(f"color: {COLORS['text_muted']};")
        updates_layout.addWidget(up_safety)

        updates_card.add_layout(updates_layout)
        layout.addWidget(updates_card)

        # About Details
        about_card = SettingsCard(t("card_about"), t("card_about_sub"))
        about_l = QVBoxLayout()
        about_l.setSpacing(6)

        ver_lbl = QLabel(f"WorkBOXig — Work & Study Studio v{__version__}")
        ver_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ver_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        about_l.addWidget(ver_lbl)

        priv_lbl = QLabel(t("about_privacy"))
        priv_lbl.setFont(QFont("Segoe UI", 9))
        priv_lbl.setStyleSheet(f"color: {COLORS['emerald']};")
        about_l.addWidget(priv_lbl)

        self.stats_lbl = QLabel()
        self.stats_lbl.setFont(QFont("Segoe UI", 9))
        self.stats_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._refresh_stats()
        about_l.addWidget(self.stats_lbl)

        guide_btn = QPushButton(t("onboarding_reopen"))
        guide_btn.clicked.connect(self.show_onboarding_requested.emit)
        about_l.addWidget(guide_btn)

        about_card.add_layout(about_l)
        layout.addWidget(about_card)
        layout.addStretch()
        return self._wrap_in_scroll(container)

    # ----------------- ACTIONS & HELPERS -----------------

    def _update_autostart_status_pill(self, enabled: bool):
        if enabled:
            self.autostart_status.setText(t("autostart_active"))
            self.autostart_status.setStyleSheet(f"""
                color: {COLORS['emerald']};
                background-color: {COLORS['emerald_subtle']};
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 8px;
                padding: 4px 10px;
            """)
        else:
            self.autostart_status.setText(t("autostart_disabled"))
            self.autostart_status.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 4px 10px;
            """)

    def _on_autostart_toggled(self, checked: bool):
        success = set_autostart_enabled(checked)
        if success:
            self._update_autostart_status_pill(checked)
            msg = t("autostart_on_msg") if checked else t("autostart_off_msg")
            self.toast_requested.emit(msg, "check" if checked else "zap")
        else:
            self.autostart_cb.setChecked(not checked)
            self.toast_requested.emit(t("autostart_error"), "warning")

    def _select_theme(self, theme_name: str):
        self.storage.set_setting("theme", theme_name)
        self._update_theme_buttons(theme_name)
        self.theme_changed.emit(theme_name)
        theme_names = {
            "dark": t("theme_dark"),
            "light": t("theme_light"),
            "cyberpunk": "Cyberpunk Neon (Edgerunner)"
        }
        self.toast_requested.emit(t("theme_applied", theme=theme_names.get(theme_name, theme_name)), "check")

    def _update_theme_buttons(self, active_theme: str):
        is_dark = (active_theme == "dark")
        is_light = (active_theme == "light")
        is_cyber = (active_theme == "cyberpunk")

        self.dark_btn.setChecked(is_dark)
        self.light_btn.setChecked(is_light)
        self.cyber_btn.setChecked(is_cyber)

        self.dark_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card_selected'] if is_dark else COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['primary'] if is_dark else COLORS['border_subtle']};
                border-radius: 10px;
                font-weight: {'bold' if is_dark else 'normal'};
                font-size: 13px;
                padding: 8px 18px;
            }}
        """)
        self.light_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card_selected'] if is_light else COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['primary'] if is_light else COLORS['border_subtle']};
                border-radius: 10px;
                font-weight: {'bold' if is_light else 'normal'};
                font-size: 13px;
                padding: 8px 18px;
            }}
        """)
        self.cyber_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#182033' if is_cyber else COLORS['bg_input']};
                color: {'#FCEE0A' if is_cyber else COLORS['text_primary']};
                border: 2px solid {'#FCEE0A' if is_cyber else COLORS['border_subtle']};
                border-radius: 10px;
                font-weight: {'bold' if is_cyber else 'normal'};
                font-size: 13px;
                padding: 8px 18px;
            }}
        """)

    def _on_focus_time_changed(self):
        text = self.focus_combo.currentText()
        try:
            mins = int(text.split()[0])
            self.storage.set_setting("focus_minutes", mins)
        except Exception:
            pass

    def _on_break_time_changed(self):
        text = self.break_combo.currentText()
        try:
            mins = int(text.split()[0])
            self.storage.set_setting("break_minutes", mins)
        except Exception:
            pass

    def _refresh_stats(self):
        nb_count = len(self.storage.get_notebooks())
        notes_count = len(self.storage.get_notes())
        tasks_count = len(self.storage.get_tasks())
        events_count = len(self.storage.get_events())
        self.stats_lbl.setText(
            t("local_db_stats", nb=nb_count, notes=notes_count, tasks=tasks_count, events=events_count)
        )

    def _export_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("backup_export_title"),
            "WorkBOXig_backup.workboxig",
            "WorkBOXig Backup (*.workboxig);;Legacy JSON (*.json)"
        )
        if path:
            try:
                self.storage.export_full_backup(path)
                self.toast_requested.emit(t("backup_exported"), "check")
            except Exception as e:
                QMessageBox.critical(self, t("card_data"), f"{t('backup_save_error')} {e}")

    def _import_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("backup_import_title"),
            "",
            "WorkBOXig Backup (*.workboxig *.zip);;Legacy JSON (*.json)"
        )
        if path:
            confirm = QMessageBox.question(
                self,
                t("backup_confirm_title"),
                t("backup_confirm_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    if self.storage.import_full_backup(path):
                        self._refresh_stats()
                        self.toast_requested.emit(t("backup_imported"), "check")
                    else:
                        QMessageBox.warning(self, t("card_data"), t("backup_corrupt_error"))
                except Exception as e:
                    QMessageBox.critical(self, t("card_data"), f"{t('backup_read_error')} {e}")

    def _open_data_folder(self):
        folder = self.storage.base_dir
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{folder}"')
        else:
            subprocess.Popen(["xdg-open", folder])

    def _select_language(self, lang: str):
        self.storage.set_setting("language", lang)
        set_language(lang)
        self._update_lang_buttons(lang)
        if hasattr(self, "close_combo"):
            saved_data = self.close_combo.currentData()
            self.close_combo.blockSignals(True)
            self.close_combo.clear()
            self.close_combo.addItem(t("close_action_ask"), "ask")
            self.close_combo.addItem(t("close_action_tray"), "tray")
            self.close_combo.addItem(t("close_action_exit"), "exit")
            idx = self.close_combo.findData(saved_data)
            if idx >= 0:
                self.close_combo.setCurrentIndex(idx)
            self.close_combo.blockSignals(False)
        if hasattr(self, "focus_combo"):
            saved_f = self.storage.get_setting("focus_minutes", 25)
            self.focus_combo.blockSignals(True)
            self.focus_combo.clear()
            for m in [20, 25, 30, 45, 50, 60]:
                self.focus_combo.addItem(f"{m} {t('settings_min')}", m)
            for i in range(self.focus_combo.count()):
                if self.focus_combo.itemData(i) == saved_f:
                    self.focus_combo.setCurrentIndex(i)
                    break
            self.focus_combo.blockSignals(False)

        if hasattr(self, "break_combo"):
            saved_b = self.storage.get_setting("break_minutes", 5)
            self.break_combo.blockSignals(True)
            self.break_combo.clear()
            for m in [5, 10, 15]:
                self.break_combo.addItem(f"{m} {t('settings_min')}", m)
            for i in range(self.break_combo.count()):
                if self.break_combo.itemData(i) == saved_b:
                    self.break_combo.setCurrentIndex(i)
                    break
            self.break_combo.blockSignals(False)

        if hasattr(self, "beta_updates_cb"):
            self.beta_updates_cb.setText(t("receive_beta_updates_cb"))
            self.beta_updates_hint.setText(t("receive_beta_updates_hint"))
        self.toast_requested.emit(t("language_changed_toast"), "check")

    def _update_lang_buttons(self, active_lang: str):
        is_ru = (active_lang == "ru")
        is_en = (active_lang == "en")
        self.ru_btn.setChecked(is_ru)
        self.en_btn.setChecked(is_en)
        for btn, active in [(self.ru_btn, is_ru), (self.en_btn, is_en)]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_card_selected'] if active else COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['primary'] if active else COLORS['border_subtle']};
                    border-radius: 10px;
                    font-weight: {'bold' if active else 'normal'};
                    font-size: 13px;
                    padding: 8px 18px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['primary_border']};
                }}
            """)

    def _on_beta_updates_toggled(self, enabled: bool):
        self.storage.set_setting("update_channel", "beta" if enabled else "stable")
        # A previous channel's status is no longer applicable.
        self.update_status_pill.setText(t("check_updates_btn"))

    def _check_updates(self):
        if self._check_update_thread is not None and self._check_update_thread.isRunning():
            return
        self.check_updates_btn.setEnabled(False)
        self.update_status_pill.setText(t("checking_updates"))
        self.update_status_pill.setStyleSheet(f"color: {COLORS['amber']}; background-color: rgba(245, 158, 11, 0.12); padding: 4px 10px; border-radius: 6px;")

        channel = self.storage.get_setting("update_channel", "stable")
        self._check_update_thread = CheckUpdateThread(parent=self, channel=channel)
        self._check_update_thread.update_available.connect(self._on_update_available)
        self._check_update_thread.up_to_date.connect(self._on_up_to_date)
        self._check_update_thread.error.connect(self._on_update_check_error)
        self._check_update_thread.finished.connect(self._on_update_thread_finished)
        self._check_update_thread.start()

    def _on_update_thread_finished(self):
        worker = self.sender()
        if worker is self._check_update_thread:
            self._check_update_thread = None
        worker.deleteLater()

    def _on_update_available(self, info: dict):
        self.check_updates_btn.setEnabled(True)
        tag = info.get("tag_name", "")
        self.update_status_pill.setText(t("update_available_status", version=tag))
        self.update_status_pill.setStyleSheet("color: #00F0FF; background-color: rgba(0, 240, 255, 0.15); padding: 4px 10px; border-radius: 6px; font-weight: bold;")

        dialog = UpdateDialog(info, storage=self.storage, parent=self)
        dialog.exec()

    def _on_up_to_date(self, info: dict):
        self.check_updates_btn.setEnabled(True)
        self.update_status_pill.setText(t("up_to_date_status", version=__version__))
        self.update_status_pill.setStyleSheet(f"color: {COLORS['emerald']}; background-color: rgba(16, 185, 129, 0.12); padding: 4px 10px; border-radius: 6px;")
        self.toast_requested.emit(t("up_to_date_status", version=__version__), "check")

    def _on_update_check_error(self, err_msg: str):
        self.check_updates_btn.setEnabled(True)
        self.update_status_pill.setText(t("settings_network_err"))
        self.update_status_pill.setStyleSheet(f"color: {COLORS['rose']}; background-color: rgba(244, 63, 94, 0.12); padding: 4px 10px; border-radius: 6px;")
        self.toast_requested.emit(f"{t('update_error_title')}: {err_msg}", "alert")

    _check_for_updates = _check_updates

    def _on_close_action_changed(self, index: int):
        val = self.close_combo.itemData(index)
        if val:
            self.storage.set_setting("close_action", val)

    def _refresh_close_action_ui(self):
        if hasattr(self, "close_combo"):
            saved = self.storage.get_setting("close_action", "ask")
            idx = self.close_combo.findData(saved)
            if idx >= 0 and self.close_combo.currentIndex() != idx:
                self.close_combo.blockSignals(True)
                self.close_combo.setCurrentIndex(idx)
                self.close_combo.blockSignals(False)
