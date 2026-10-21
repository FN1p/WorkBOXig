"""
Close Confirmation Dialog for WorkBOXig.
Allows users to either minimize to system tray or quit completely,
with an option to persist their preference in application settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor

from src.styles import COLORS, CURRENT_THEME
from src.i18n import t
from src.icons import get_icon, get_pixmap


class CloseActionDialog(QDialog):
    """Modern modal dialog prompting user for close behavior (Tray vs Exit)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("close_dialog_title"))
        self.setModal(True)
        self.setMinimumWidth(460)
        self.action = None  # 'tray', 'exit', or None

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
            QCheckBox {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {COLORS['border_light']};
                background: {COLORS['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary_light']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("settings", COLORS['primary_light'], 28))
        icon_lbl.setStyleSheet("background: transparent;")
        header_layout.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        dlg_title = QLabel(t("close_dialog_title"))
        dlg_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        dlg_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        title_box.addWidget(dlg_title)

        dlg_sub = QLabel(t("close_dialog_msg"))
        dlg_sub.setFont(QFont("Segoe UI", 10))
        dlg_sub.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        title_box.addWidget(dlg_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Info card
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_lbl = QLabel(t("close_dialog_desc"))
        info_lbl.setWordWrap(True)
        info_lbl.setFont(QFont("Segoe UI", 9))
        info_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; line-height: 1.4;")
        info_layout.addWidget(info_lbl)
        layout.addWidget(info_frame)

        # Action Buttons Container
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)

        # Button 1: Minimize to Tray (Primary Action)
        self.btn_tray = QPushButton(f"  {t('close_btn_tray')}")
        self.btn_tray.setIcon(get_icon("panel_left", "#000000" if is_cyber else "#FFFFFF", 16))
        self.btn_tray.setIconSize(QSize(16, 16))
        self.btn_tray.setFixedHeight(44)
        self.btn_tray.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tray.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_tray.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {'#000000' if is_cyber else '#FFFFFF'};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 8px;
                padding: 8px 16px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        self.btn_tray.clicked.connect(self._choose_tray)
        actions_layout.addWidget(self.btn_tray)

        # Button 2: Quit Completely (Secondary Action)
        self.btn_exit = QPushButton(f"  {t('close_btn_exit')}")
        self.btn_exit.setIcon(get_icon("trash", COLORS['rose'], 16))
        self.btn_exit.setIconSize(QSize(16, 16))
        self.btn_exit.setFixedHeight(40)
        self.btn_exit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_exit.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.btn_exit.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['rose']};
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                padding: 6px 14px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.15);
                border-color: {COLORS['rose']};
            }}
        """)
        self.btn_exit.clicked.connect(self._choose_exit)
        actions_layout.addWidget(self.btn_exit)

        layout.addLayout(actions_layout)

        # Bottom row: Remember Choice Checkbox & Cancel button
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 4, 0, 0)

        self.remember_cb = QCheckBox(t("close_dialog_remember"))
        self.remember_cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        bottom_layout.addWidget(self.remember_cb)

        bottom_layout.addStretch()

        self.btn_cancel = QPushButton(t("close_btn_cancel"))
        self.btn_cancel.setFixedHeight(32)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
                text-decoration: underline;
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        bottom_layout.addWidget(self.btn_cancel)

        layout.addLayout(bottom_layout)

    def _choose_tray(self):
        self.action = "tray"
        self.accept()

    def _choose_exit(self):
        self.action = "exit"
        self.accept()
