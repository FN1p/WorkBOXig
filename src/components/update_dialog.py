"""
Update Dialog for WorkBOXig.
Displays new version details, changelog notes, safe-data guarantees,
and real-time download and installation progress.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextBrowser, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QCursor, QDesktopServices

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t
from src.version import __version__
from src.utils.updater import DownloadUpdateThread, launch_installer_and_quit


class UpdateDialog(QDialog):
    """Modern modal dialog presenting available application updates."""

    def __init__(self, release_info: dict, storage=None, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.storage = storage
        self.download_thread: Optional[DownloadUpdateThread] = None

        self.setWindowTitle(t("update_dialog_title"))
        self.setMinimumSize(580, 520)
        self.resize(600, 560)
        self.setModal(True)

        is_cyber = (CURRENT_THEME == "cyberpunk")
        bg_color = "#0B0E17" if is_cyber else COLORS['bg_root']
        card_bg = "#111726" if is_cyber else COLORS['bg_card']
        border_color = "#00F0FF" if is_cyber else COLORS['border_subtle']

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }}
            QTextBrowser {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }}
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                text-align: center;
                color: {COLORS['text_primary']};
                font-weight: bold;
                font-size: 11px;
                height: 16px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 5px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header Card
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(14, 12, 14, 12)
        h_layout.setSpacing(6)

        tag = self.release_info.get("tag_name", "")
        title_text = self.release_info.get("title", tag)

        title_lbl = QLabel(t('update_dialog_title'))
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {'#FCEE0A' if is_cyber else COLORS['text_primary']};")
        h_layout.addWidget(title_lbl)

        ver_sub = QLabel(f"{t('current_version_lbl')} v{__version__}  ->  {tag} ({title_text})")
        ver_sub.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        ver_sub.setStyleSheet(f"color: {'#00F0FF' if is_cyber else COLORS['primary_light']};")
        h_layout.addWidget(ver_sub)
        layout.addWidget(header_card)

        # 2. Release Notes / Changelog
        notes_lbl = QLabel(t("update_notes_title"))
        notes_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        notes_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(notes_lbl)

        self.notes_browser = QTextBrowser()
        body_text = self.release_info.get("body", "").strip() or "• Bug fixes, enhancements, and performance optimizations."
        self.notes_browser.setMarkdown(body_text)
        self.notes_browser.setOpenExternalLinks(True)
        layout.addWidget(self.notes_browser, 1)

        # 3. Data Safety Guarantee Banner
        safety_frame = QFrame()
        safety_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'rgba(0, 240, 255, 0.08)' if is_cyber else 'rgba(16, 185, 129, 0.08)'};
                border: 1px solid {'#00F0FF' if is_cyber else '#10B981'};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        s_layout = QHBoxLayout(safety_frame)
        s_layout.setContentsMargins(10, 8, 10, 8)
        safety_lbl = QLabel(t("data_safe_guarantee"))
        safety_lbl.setWordWrap(True)
        safety_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        safety_lbl.setStyleSheet(f"color: {'#00F0FF' if is_cyber else '#10B981'}; background: transparent;")
        s_layout.addWidget(safety_lbl)
        layout.addWidget(safety_frame)

        # 4. Progress Section (hidden until download starts)
        self.progress_container = QWidget()
        p_layout = QVBoxLayout(self.progress_container)
        p_layout.setContentsMargins(0, 4, 0, 4)
        p_layout.setSpacing(6)

        self.progress_lbl = QLabel(t("downloading_progress", percent=0, mb_done=0, mb_total=0))
        self.progress_lbl.setFont(QFont("Segoe UI", 9))
        self.progress_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        p_layout.addWidget(self.progress_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        p_layout.addWidget(self.progress_bar)

        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        # 5. Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.github_btn = QPushButton(t("btn_open_github"))
        self.github_btn.setObjectName("ghost-btn")
        self.github_btn.setFixedHeight(40)
        self.github_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.github_btn.clicked.connect(self._open_github)
        btn_row.addWidget(self.github_btn)

        btn_row.addStretch()

        self.later_btn = QPushButton(t("btn_later"))
        self.later_btn.setObjectName("ghost-btn")
        self.later_btn.setFixedHeight(40)
        self.later_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.later_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.later_btn)

        self.install_btn = QPushButton(t("btn_download_update"))
        self.install_btn.setObjectName("primary-btn")
        self.install_btn.setFixedHeight(40)
        self.install_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.install_btn.setStyleSheet(f"""
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
        self.install_btn.clicked.connect(self._start_update)
        btn_row.addWidget(self.install_btn)

        layout.addLayout(btn_row)

    def _open_github(self):
        url = self.release_info.get("html_url", f"https://github.com/FN1p/WorkBOXig/releases")
        QDesktopServices.openUrl(QUrl(url))

    def _start_update(self):
        # A portable EXE is not an installer. Do not launch it as an upgrade.
        installer_url = self.release_info.get("installer_url")
        if not installer_url:
            # If no direct asset exists, open GitHub release page in browser
            self._open_github()
            self.accept()
            return

        filename = self.release_info.get("installer_name") or "WorkBOXig_Setup.exe"

        self.install_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.progress_container.setVisible(True)

        self.download_thread = DownloadUpdateThread(installer_url, filename, self)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.completed.connect(self._on_download_completed)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_progress(self, downloaded: int, total: int, pct: float):
        mb_done = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024) if total > 0 else 0
        self.progress_bar.setValue(int(pct))
        self.progress_lbl.setText(t("downloading_progress", percent=pct, mb_done=mb_done, mb_total=mb_total))

    def _on_download_completed(self, local_path: str):
        self.progress_lbl.setText(t("download_complete_msg"))
        self.progress_bar.setValue(100)
        # Execute installer and quit safely
        launch_installer_and_quit(local_path, self.storage)

    def _on_download_error(self, err_msg: str):
        self.progress_container.setVisible(False)
        self.install_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
        self.notes_browser.append(f"\n\n**{t('update_error_title')}:** {err_msg}")

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
        super().closeEvent(event)
