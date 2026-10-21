"""
Google Calendar Synchronization Dialog for WorkBOXig.
Interactive wizard with visual step-by-step instructions, iCal link validation,
and live background synchronization with Google Calendar.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QFont, QCursor, QDesktopServices

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t
from src.icons import get_icon
from src.storage import StorageManager
from src.utils.google_calendar import GoogleCalendarSyncWorker, normalize_calendar_url


class GoogleSyncDialog(QDialog):
    """Dialog for connecting and syncing Google Calendar with WorkBOXig."""
    sync_completed = pyqtSignal(int, int, int)  # added, updated, total

    def __init__(self, storage: StorageManager, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.worker = None

        self.setWindowTitle(t("google_dialog_title"))
        self.setMinimumSize(620, 560)
        self.resize(650, 600)
        self.setModal(True)

        is_cyber = (CURRENT_THEME == "cyberpunk")
        bg_color = "#0B0E17" if is_cyber else COLORS['bg_root']
        card_bg = "#111726" if is_cyber else COLORS['bg_card']
        border_col = "#00F0FF" if is_cyber else COLORS['border_subtle']

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {'#00F0FF' if is_cyber else COLORS['primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header Card
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {border_col};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(14, 12, 14, 12)
        h_layout.setSpacing(6)

        title_lbl = QLabel(f"📅 {t('google_dialog_title')}")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {'#FCEE0A' if is_cyber else COLORS['text_primary']};")
        h_layout.addWidget(title_lbl)

        sub_lbl = QLabel(t("google_dialog_subtitle"))
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        h_layout.addWidget(sub_lbl)
        layout.addWidget(header_card)

        # 2. Step-by-Step Instructions Card
        instr_card = QFrame()
        instr_card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        i_layout = QVBoxLayout(instr_card)
        i_layout.setContentsMargins(16, 14, 16, 14)
        i_layout.setSpacing(8)

        instr_title = QLabel(f"💡 {t('google_instructions_title')}")
        instr_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        instr_title.setStyleSheet(f"color: {'#00F0FF' if is_cyber else COLORS['text_primary']};")
        i_layout.addWidget(instr_title)

        steps = [
            t("google_step1"),
            t("google_step2"),
            t("google_step3"),
            t("google_step4"),
            t("google_step5"),
        ]
        for step_text in steps:
            step_lbl = QLabel(step_text)
            step_lbl.setWordWrap(True)
            step_lbl.setFont(QFont("Segoe UI", 9))
            step_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            i_layout.addWidget(step_lbl)

        # Open Web Calendar Button inside instructions
        open_web_btn = QPushButton(t("google_open_web_btn"))
        open_web_btn.setIcon(get_icon("calendar", COLORS['primary_light'], 14))
        open_web_btn.setIconSize(QSize(14, 14))
        open_web_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_web_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {'#00F0FF' if is_cyber else COLORS['primary_light']};
                border: none;
                font-weight: 600;
                font-size: 12px;
                text-align: left;
                padding: 4px 0px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        open_web_btn.clicked.connect(self._open_web_calendar)
        i_layout.addWidget(open_web_btn)

        layout.addWidget(instr_card)

        # 3. URL Input Card
        url_box = QVBoxLayout()
        url_box.setSpacing(6)

        url_title = QLabel(t("google_url_lbl"))
        url_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        url_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        url_box.addWidget(url_title)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(t("google_url_placeholder"))
        saved_url = self.storage.get_setting("google_calendar_url", "")
        self.url_input.setText(saved_url)
        input_row.addWidget(self.url_input, stretch=1)

        paste_btn = QPushButton(t("google_btn_paste"))
        paste_btn.setIcon(get_icon("copy", COLORS['text_secondary'], 14))
        paste_btn.setFixedHeight(38)
        paste_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        paste_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
            }}
        """)
        paste_btn.clicked.connect(self._paste_clipboard)
        input_row.addWidget(paste_btn)

        url_box.addLayout(input_row)
        layout.addLayout(url_box)

        # 4. Auto-sync Checkbox & Status
        opt_row = QHBoxLayout()
        self.auto_sync_cb = QCheckBox(t("google_auto_sync_cb"))
        self.auto_sync_cb.setFont(QFont("Segoe UI", 10))
        self.auto_sync_cb.setChecked(self.storage.get_setting("google_calendar_auto_sync", True))
        self.auto_sync_cb.toggled.connect(lambda ch: self.storage.set_setting("google_calendar_auto_sync", ch))
        opt_row.addWidget(self.auto_sync_cb)
        opt_row.addStretch()
        layout.addLayout(opt_row)

        # Status text
        self.status_lbl = QLabel()
        self.status_lbl.setFont(QFont("Segoe UI", 9))
        self._update_status_display()
        layout.addWidget(self.status_lbl)

        layout.addStretch()

        # 5. Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        if saved_url:
            self.clear_btn = QPushButton(t("google_clear_btn"))
            self.clear_btn.setObjectName("danger-btn")
            self.clear_btn.setFixedHeight(40)
            self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.clear_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['rose']};
                    border: 1px solid {COLORS['rose']};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(244, 63, 94, 0.15);
                }}
            """)
            self.clear_btn.clicked.connect(self._disconnect_calendar)
            btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()

        self.close_btn = QPushButton(t("palette_esc") if "palette_esc" in t("palette_esc") else "Закрыть")
        self.close_btn.setObjectName("ghost-btn")
        self.close_btn.setFixedHeight(40)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.close_btn)

        self.sync_btn = QPushButton(t("google_sync_now_btn"))
        self.sync_btn.setObjectName("primary-btn")
        self.sync_btn.setIcon(get_icon("sync", "#000000" if is_cyber else "#FFFFFF", 16))
        self.sync_btn.setIconSize(QSize(16, 16))
        self.sync_btn.setFixedHeight(40)
        self.sync_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sync_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#FCEE0A' if is_cyber else COLORS['primary']};
                color: {'#000000' if is_cyber else '#FFFFFF'};
                font-weight: bold;
                font-size: 13px;
                padding: 8px 22px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {'#FFF152' if is_cyber else COLORS['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border_subtle']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.sync_btn.clicked.connect(self._start_sync)
        btn_row.addWidget(self.sync_btn)

        layout.addLayout(btn_row)

    def _open_web_calendar(self):
        QDesktopServices.openUrl(QUrl("https://calendar.google.com"))

    def _paste_clipboard(self):
        cb = QApplication.clipboard()
        text = cb.text().strip()
        if text:
            self.url_input.setText(text)

    def _update_status_display(self):
        last_sync = self.storage.get_setting("google_calendar_last_sync")
        if last_sync:
            try:
                dt = datetime.fromisoformat(last_sync)
                dt_str = dt.strftime("%d.%m.%Y в %H:%M")
                self.status_lbl.setText(f"● {t('google_last_sync_lbl', time=dt_str)}")
                self.status_lbl.setStyleSheet(f"color: {COLORS['emerald']};")
            except Exception:
                self.status_lbl.setText(f"● {t('google_last_sync_lbl', time=last_sync)}")
                self.status_lbl.setStyleSheet(f"color: {COLORS['emerald']};")
        else:
            self.status_lbl.setText(f"○ {t('google_never_synced')}")
            self.status_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")

    def _start_sync(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, t("google_dialog_title"), "Пожалуйста, вставьте ссылку на секретный адрес iCal.")
            return

        clean_url = normalize_calendar_url(url)
        if not clean_url.startswith("https://"):
            QMessageBox.warning(self, t("google_dialog_title"), "Некорректная ссылка. Ссылка должна начинаться с https:// или webcal://")
            return

        self.sync_btn.setEnabled(False)
        self.sync_btn.setText(t("google_syncing"))
        self.status_lbl.setText(f"⏳ {t('google_syncing')}")
        self.status_lbl.setStyleSheet(f"color: {COLORS['sky']};")

        self.worker = GoogleCalendarSyncWorker(clean_url, self.storage, self)
        self.worker.sync_finished.connect(self._on_sync_finished)
        self.worker.sync_error.connect(self._on_sync_error)
        self.worker.start()

    def _on_sync_finished(self, added: int, updated: int, total: int):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText(t("google_sync_now_btn"))
        msg = t("google_sync_success", added=added, updated=updated, total=total)
        self.status_lbl.setText(f"✓ {msg}")
        self.status_lbl.setStyleSheet(f"color: {COLORS['emerald']}; font-weight: bold;")
        self.sync_completed.emit(added, updated, total)

    def _on_sync_error(self, err_msg: str):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText(t("google_sync_now_btn"))
        self.status_lbl.setText(f"✗ {t('google_sync_fail', error=err_msg)}")
        self.status_lbl.setStyleSheet(f"color: {COLORS['rose']}; font-weight: bold;")

    def _disconnect_calendar(self):
        confirm = QMessageBox.question(
            self,
            t("google_clear_btn"),
            "Вы уверены, что хотите отвязать Google Календарь и удалить импортированные события?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            # Remove all events with source: google
            events = self.storage.get_events()
            self.storage._data["calendar_events"] = [e for e in events if e.get("source") != "google"]
            self.storage.set_setting("google_calendar_url", "")
            self.storage.set_setting("google_calendar_last_sync", None)
            self.storage.save_immediately()
            self.storage.data_changed.emit("events")

            self.url_input.clear()
            self._update_status_display()
            self.sync_completed.emit(0, 0, 0)
            self.accept()
