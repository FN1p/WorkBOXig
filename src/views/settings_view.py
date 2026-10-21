"""
Settings View for WorkBOXig.
Provides clean theme switching (Dark / Light), Windows Autostart registry toggle,
Pomodoro sound/timer preferences, and JSON backup export/import.
"""

import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t, get_i18n, get_language, set_language
from src.storage import get_storage
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
    """Settings screen coordinating appearance, system, timer, and data."""
    theme_changed = pyqtSignal(str) # 'dark' or 'light'
    toast_requested = pyqtSignal(str, str) # message, type
    test_notification_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for comfortable viewing on any screen resolution
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 24, 32, 32)
        content_layout.setSpacing(20)

        # 1. Header
        header_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        
        main_title = QLabel(t("settings_title"))
        main_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        main_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_box.addWidget(main_title)

        sub_title = QLabel(t("settings_subtitle"))
        sub_title.setFont(QFont("Segoe UI", 10))
        sub_title.setStyleSheet(f"color: {COLORS['text_muted']};")
        title_box.addWidget(sub_title)
        header_box.addLayout(title_box)
        header_box.addStretch()
        content_layout.addLayout(header_box)

                # Language Section Card
        self.lang_card = SettingsCard("Язык интерфейса / Interface Language", "Выберите язык приложения / Select interface language")
        lang_row = QHBoxLayout()
        lang_row.setSpacing(16)

        self.ru_btn = QPushButton("🇷🇺 Русский")
        self.ru_btn.setCheckable(True)
        self.ru_btn.setFixedHeight(48)
        self.ru_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ru_btn.clicked.connect(lambda: self._select_language("ru"))

        self.en_btn = QPushButton("🇬🇧 English")
        self.en_btn.setCheckable(True)
        self.en_btn.setFixedHeight(48)
        self.en_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.en_btn.clicked.connect(lambda: self._select_language("en"))

        lang_row.addWidget(self.ru_btn)
        lang_row.addWidget(self.en_btn)
        self.lang_card.add_layout(lang_row)
        content_layout.addWidget(self.lang_card)

        # 2. Section: Appearance (Theme Switching)
        theme_card = SettingsCard(t("card_appearance"), t("card_appearance_sub"))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)

        # Dark Mode Card Button
        self.dark_btn = QPushButton(t("theme_dark"))
        self.dark_btn.setCheckable(True)
        self.dark_btn.setIcon(get_icon("moon", "#FFFFFF", 18))
        self.dark_btn.setIconSize(QSize(18, 18))
        self.dark_btn.setFixedHeight(50)
        self.dark_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dark_btn.clicked.connect(lambda: self._select_theme("dark"))

        # Light Mode Card Button
        self.light_btn = QPushButton(t("theme_light"))
        self.light_btn.setCheckable(True)
        self.light_btn.setIcon(get_icon("sun", "#F59E0B", 18))
        self.light_btn.setIconSize(QSize(18, 18))
        self.light_btn.setFixedHeight(50)
        self.light_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.light_btn.clicked.connect(lambda: self._select_theme("light"))

        # Cyberpunk Mode Card Button
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
        content_layout.addWidget(theme_card)

        # 3. Section: Windows Autostart
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
        content_layout.addWidget(startup_card)

        # 3b. Section: Window Close Behavior
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
        content_layout.addWidget(self.close_action_card)

        # 4. Section: Focus & Timer Preferences
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
        content_layout.addWidget(focus_card)

        # 5. Section: Desktop Notifications
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

        content_layout.addWidget(notif_card)

        # 6. Section: Data, Backups & Files
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
        content_layout.addWidget(data_card)

        # 7. Section: Application Updates & Data Safety
        self._check_update_thread = None
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

        up_safety = QLabel(t("data_safe_guarantee"))
        up_safety.setWordWrap(True)
        up_safety.setFont(QFont("Segoe UI", 9))
        up_safety.setStyleSheet(f"color: {COLORS['text_muted']};")
        updates_layout.addWidget(up_safety)

        updates_card.add_layout(updates_layout)
        content_layout.addWidget(updates_card)

        # 8. Section: About
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

        about_card.add_layout(about_l)
        content_layout.addWidget(about_card)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)

        # Refresh theme & language button visual states
        self._update_theme_buttons(self.storage.get_setting("theme", "dark"))
        self._update_lang_buttons(self.storage.get_setting("language", "en"))

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
            f"WorkBOXig_backup_{os.path.basename(self.storage.file_path)}",
            "JSON Files (*.json)"
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
            "JSON Files (*.json)"
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

        msg = "Language switched to English" if lang == "en" else "Язык изменён на Русский"
        self.toast_requested.emit(msg, "check")

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

    def _check_updates(self):
        self.check_updates_btn.setEnabled(False)
        self.update_status_pill.setText(t("checking_updates"))
        self.update_status_pill.setStyleSheet(f"color: {COLORS['amber']}; background-color: rgba(245, 158, 11, 0.12); padding: 4px 10px; border-radius: 6px;")

        self._check_update_thread = CheckUpdateThread(parent=self)
        self._check_update_thread.update_available.connect(self._on_update_available)
        self._check_update_thread.up_to_date.connect(self._on_up_to_date)
        self._check_update_thread.error.connect(self._on_update_check_error)
        self._check_update_thread.start()

    def _on_update_available(self, info: dict):
        self.check_updates_btn.setEnabled(True)
        tag = info.get("tag_name", "")
        self.update_status_pill.setText(t("update_available_status", version=tag))
        self.update_status_pill.setStyleSheet("color: #00F0FF; background-color: rgba(0, 240, 255, 0.15); padding: 4px 10px; border-radius: 6px; font-weight: bold;")

        # Display update dialog
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
