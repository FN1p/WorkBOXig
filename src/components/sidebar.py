"""
Sidebar Navigation Component for WorkBOXig.
Designed for high contrast, modern ergonomics, clear visual hierarchy,
and animated collapse to icon-only mode.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QCursor
from src.styles import COLORS
from src.icons import get_pixmap, get_icon
from src.i18n import t, get_i18n


class NavItem(QPushButton):
    """Custom styled navigation button with high contrast, glow effects, and icon-only mode."""
    
    def __init__(self, icon_name: str, text: str, shortcut_str: str, tab_id: str, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.icon_name = icon_name
        self.item_text = text
        self.shortcut_str = shortcut_str
        self.is_collapsed = False
        self.is_active = False

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setAutoExclusive(True)

        self.btn_layout = QHBoxLayout(self)
        self.btn_layout.setContentsMargins(12, 0, 10, 0)
        self.btn_layout.setSpacing(12)

        # Vector Icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(22, 22)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent;")
        self.btn_layout.addWidget(self.icon_lbl)

        # Label
        self.text_lbl = QLabel(text)
        self.text_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.text_lbl.setStyleSheet(f"background: transparent; color: {COLORS['text_secondary']};")
        self.btn_layout.addWidget(self.text_lbl)

        self.btn_layout.addStretch()

        # Keyboard shortcut hint (sleek minimalist keycap)
        self.shortcut_lbl = QLabel(shortcut_str)
        self.shortcut_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        self.shortcut_lbl.setFixedHeight(18)
        self.shortcut_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_layout.addWidget(self.shortcut_lbl)

        # Counter badge (sleek glowing pill)
        self.badge_lbl = QLabel("")
        self.badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.badge_lbl.setFixedHeight(18)
        self.badge_lbl.setMinimumWidth(18)
        self.badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_lbl.hide()
        self.btn_layout.addWidget(self.badge_lbl)

        self.update_style(False)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        if collapsed:
            self.text_lbl.hide()
            self.shortcut_lbl.hide()
            self.badge_lbl.hide()
            self.btn_layout.setContentsMargins(0, 0, 0, 0)
            self.btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setFixedSize(48, 44)
            self.setToolTip(f"{self.item_text} ({self.shortcut_str})")
        else:
            self.text_lbl.show()
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setFixedHeight(44)
            self.btn_layout.setContentsMargins(12, 0, 10, 0)
            self.btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.setToolTip("")
            if self.badge_lbl.text():
                self.badge_lbl.show()
                self.shortcut_lbl.hide()
            else:
                self.shortcut_lbl.show()
        self.update_style(self.is_active)

    def set_label_text(self, text: str):
        self.item_text = text
        self.text_lbl.setText(text)
        if self.is_collapsed:
            self.setToolTip(f"{self.item_text} ({self.shortcut_str})")
        else:
            self.setToolTip("")

    def set_badge(self, count: int):
        if count > 0:
            self.badge_lbl.setText(str(count))
            if not self.is_collapsed:
                self.badge_lbl.show()
                self.shortcut_lbl.hide()
        else:
            self.badge_lbl.setText("")
            self.badge_lbl.hide()
            if not self.is_collapsed:
                self.shortcut_lbl.show()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self.update_style(checked)

    def update_style(self, active: bool):
        self.is_active = active
        is_dark = (COLORS.get("text_primary", "#FFFFFF") == "#FFFFFF")

        # Badge styling (sleek glowing circular pill)
        badge_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #4F46E5)" if is_dark else "#4F46E5"
        self.badge_lbl.setStyleSheet(f"""
            background: {badge_bg};
            color: #FFFFFF;
            border-radius: 9px;
            padding: 0px 6px;
            font-size: 10px;
            font-weight: 700;
        """)

        if active:
            act_color = "#FFFFFF" if is_dark else COLORS['primary']
            self.icon_lbl.setPixmap(get_pixmap(self.icon_name, act_color, 22))
            self.text_lbl.setStyleSheet(f"color: {act_color}; font-weight: 600; background: transparent;")
            self.shortcut_lbl.setStyleSheet(f"""
                color: {act_color};
                background-color: rgba(99, 102, 241, 0.25);
                border: 1px solid rgba(129, 140, 248, 0.35);
                border-radius: 4px;
                padding: 0px 5px;
                font-size: 9px;
            """)
            if self.is_collapsed:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(99, 102, 241, 0.14);
                        border: 1px solid rgba(99, 102, 241, 0.35);
                        border-radius: 10px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(99, 102, 241, 0.12);
                        border: 1px solid rgba(99, 102, 241, 0.22);
                        border-left: 3px solid #6366F1;
                        border-radius: 8px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(99, 102, 241, 0.18);
                        border-color: rgba(99, 102, 241, 0.35);
                    }}
                """)
        else:
            inact_icon = "#94A3B8" if is_dark else COLORS['text_muted']
            sc_bg = "rgba(255, 255, 255, 0.04)" if is_dark else "rgba(0, 0, 0, 0.04)"
            sc_bd = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.08)"
            self.icon_lbl.setPixmap(get_pixmap(self.icon_name, inact_icon, 22))
            self.text_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500; background: transparent;")
            self.shortcut_lbl.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                background-color: {sc_bg};
                border: 1px solid {sc_bd};
                border-radius: 4px;
                padding: 0px 5px;
                font-size: 9px;
            """)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card_hover']};
                    border-color: {COLORS['border_subtle']};
                }}
            """)


class Sidebar(QWidget):
    """
    Application Sidebar with animated collapse to icon-only mode.
    """
    page_changed = pyqtSignal(str) # emits tab_id
    collapse_toggled = pyqtSignal(bool) # emits is_collapsed

    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 68

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setObjectName("sidebar_container")
        self.setStyleSheet(f"""
            QWidget#sidebar_container {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border_subtle']};
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 16, 12, 16)
        self.main_layout.setSpacing(6)

        # Header / Brand
        self.brand_layout = QHBoxLayout()
        self.brand_layout.setSpacing(10)
        self.brand_layout.setContentsMargins(2, 0, 2, 14)

        self.logo_box = QLabel()
        self.logo_box.setPixmap(get_pixmap("logo", COLORS['primary_light'], 22))
        self.logo_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['primary_subtle']}, stop:1 rgba(0, 0, 0, 0.05));
            border: 1px solid {COLORS['primary_border']};
            border-radius: 10px;
            padding: 6px;
        """)
        self.logo_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['primary_subtle']}, stop:1 rgba(0, 0, 0, 0.05));
            border: 1px solid {COLORS['primary_border']};
            border-radius: 10px;
            padding: 6px;
        """)
        self.logo_box.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.logo_box.setToolTip("WorkBOXig (Нажмите для переключения меню)")
        self.logo_box.mousePressEvent = lambda e: self.toggle_collapse()
        self.brand_layout.addWidget(self.logo_box)

        self.brand_text_widget = QWidget()
        self.brand_text_widget.setStyleSheet("background: transparent;")
        brand_text_layout = QVBoxLayout(self.brand_text_widget)
        brand_text_layout.setContentsMargins(0, 0, 0, 0)
        brand_text_layout.setSpacing(1)
        
        self.title_lbl = QLabel("WorkBOXig")
        self.title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 0.5px;")
        
        self.sub_lbl = QLabel("Work & Study OS")
        self.sub_lbl.setFont(QFont("Segoe UI", 8))
        self.sub_lbl.setStyleSheet(f"color: {COLORS['primary_light']};")
        
        brand_text_layout.addWidget(self.title_lbl)
        brand_text_layout.addWidget(self.sub_lbl)
        self.brand_layout.addWidget(self.brand_text_widget, stretch=1)

        # Collapse toggle button in header
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(get_icon("panel_left", COLORS['text_muted'], 18))
        self.toggle_btn.setIconSize(QSize(18, 18))
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setToolTip("Свернуть меню (Ctrl+B)")
        self.toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.12);
            }}
        """)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        self.brand_layout.addWidget(self.toggle_btn)

        self.main_layout.addLayout(self.brand_layout)

        # Section label
        self.sec_lbl = QLabel(t("sections"))
        self.sec_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.sec_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding-left: 6px; margin-bottom: 4px; letter-spacing: 1px;")
        self.main_layout.addWidget(self.sec_lbl)

        # Navigation items
        self.nav_items = {}
        items_config = [
            ("dashboard", t("nav_dashboard"), "Ctrl+1", "dashboard"),
            ("calendar", t("nav_calendar"), "Ctrl+2", "calendar"),
            ("notebooks", t("nav_notebooks"), "Ctrl+3", "notebooks"),
            ("notes", t("nav_notes"), "Ctrl+4", "notes"),
            ("tasks", t("nav_tasks"), "Ctrl+5", "tasks"),
            ("settings", t("nav_settings"), "Ctrl+,", "settings"),
        ]

        for icon_name, label_text, shortcut_str, tab_id in items_config:
            btn = NavItem(icon_name, label_text, shortcut_str, tab_id, self)
            btn.clicked.connect(lambda checked, tid=tab_id: self._on_item_clicked(tid))
            self.main_layout.addWidget(btn)
            self.nav_items[tab_id] = btn

        self.main_layout.addStretch()

        # Bottom Workspace & Status Card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self.status_card.setFixedHeight(50)
        self.status_card.setStyleSheet(f"""
            QFrame#status_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 10px;
            }}
        """)
        self.s_layout = QHBoxLayout(self.status_card)
        self.s_layout.setContentsMargins(8, 6, 8, 6)
        self.s_layout.setSpacing(10)

        self.avatar = QLabel()
        self.avatar.setPixmap(get_pixmap("user", COLORS['primary_light'], 16))
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(28, 28)
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 14px;
            }}
        """)
        self.s_layout.addWidget(self.avatar)

        self.user_info_widget = QWidget()
        self.user_info_widget.setStyleSheet("background: transparent;")
        u_info = QVBoxLayout(self.user_info_widget)
        u_info.setContentsMargins(0, 0, 0, 0)
        u_info.setSpacing(1)
        self.name_lbl = QLabel(t("workspace_personal"))
        self.name_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; border: none; padding: 0px;")
        
        self.status_text = QLabel(f"● {t('workspace_local')}")
        self.status_text.setFont(QFont("Segoe UI", 8))
        self.status_text.setStyleSheet(f"color: {COLORS['emerald']}; background: transparent; border: none; padding: 0px;")
        
        u_info.addWidget(self.name_lbl)
        u_info.addWidget(self.status_text)
        self.s_layout.addWidget(self.user_info_widget, stretch=1)

        self.main_layout.addWidget(self.status_card)

        get_i18n().language_changed.connect(self._on_language_changed)

        # Set default active
        self.select_tab("dashboard")

    def toggle_collapse(self, animated: bool = True):
        """Toggle between expanded full sidebar and compact icon-only mode."""
        self.is_collapsed = not self.is_collapsed
        target_w = self.COLLAPSED_WIDTH if self.is_collapsed else self.EXPANDED_WIDTH

        if animated:
            self.anim = QPropertyAnimation(self, b"maximumWidth")
            self.anim.setDuration(160)
            self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim.setStartValue(self.width())
            self.anim.setEndValue(target_w)
            
            self.anim.valueChanged.connect(lambda val: self.setFixedWidth(val))
            
            def on_finish():
                self.setFixedWidth(target_w)
                self._apply_collapse_state()
            self.anim.finished.connect(on_finish)
            
            self._apply_collapse_state()
            self.anim.start()
        else:
            self.setFixedWidth(target_w)
            self._apply_collapse_state()

        self.collapse_toggled.emit(self.is_collapsed)

    def _apply_collapse_state(self):
        if self.is_collapsed:
            self.brand_text_widget.hide()
            self.sec_lbl.hide()
            self.user_info_widget.hide()
            self.toggle_btn.hide()
            self.logo_box.setFixedSize(42, 42)
            self.logo_box.setToolTip("Развернуть меню (Ctrl+B)")
            self.brand_layout.setContentsMargins(0, 0, 0, 14)
            self.brand_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.setContentsMargins(8, 16, 8, 16)
            self.main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.status_card.setFixedSize(44, 44)
            self.status_card.setToolTip("Личное пространство (Локально)")
            self.s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.s_layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.brand_text_widget.show()
            self.sec_lbl.show()
            self.user_info_widget.show()
            self.toggle_btn.show()
            self.toggle_btn.setIcon(get_icon("panel_left", COLORS['text_muted'], 18))
            self.toggle_btn.setIconSize(QSize(18, 18))
            self.toggle_btn.setToolTip("Свернуть меню (Ctrl+B)")
            self.logo_box.setFixedSize(38, 38)
            self.logo_box.setToolTip("WorkBOXig")
            self.brand_layout.setContentsMargins(2, 0, 2, 14)
            self.brand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.main_layout.setContentsMargins(12, 16, 12, 16)
            self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.status_card.setMinimumWidth(0)
            self.status_card.setMaximumWidth(16777215)
            self.status_card.setFixedHeight(50)
            self.status_card.setToolTip("")
            self.s_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.s_layout.setContentsMargins(8, 6, 8, 6)

        for btn in self.nav_items.values():
            btn.set_collapsed(self.is_collapsed)

    def refresh_theme(self):
        """Update sidebar styling and icons when theme changes."""
        self.setStyleSheet(f"""
            QWidget#sidebar_container {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border_subtle']};
            }}
        """)
        self.logo_box.setPixmap(get_pixmap("logo", COLORS['primary_light'], 22))
        self.logo_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['primary_subtle']}, stop:1 rgba(0, 0, 0, 0.05));
            border: 1px solid {COLORS['primary_border']};
            border-radius: 10px;
            padding: 6px;
        """)
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 0.5px;")
        self.sub_lbl.setStyleSheet(f"color: {COLORS['primary_light']};")
        self.sec_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding-left: 6px; margin-bottom: 4px; letter-spacing: 1px;")
        self.toggle_btn.setIcon(get_icon("panel_left" if not self.is_collapsed else "panel_left_open", COLORS['text_muted'], 18))
        self.status_card.setStyleSheet(f"""
            QFrame#status_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 10px;
            }}
        """)
        self.avatar.setPixmap(get_pixmap("user", COLORS['primary_light'], 16))
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['primary_border']};
                border-radius: 14px;
            }}
        """)
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; border: none; padding: 0px;")
        self.status_text.setStyleSheet(f"color: {COLORS['emerald']}; background: transparent; border: none; padding: 0px;")
        for item in self.nav_items.values():
            item.update_style(item.is_active)

    def _on_item_clicked(self, tab_id: str):
        self.select_tab(tab_id)
        self.page_changed.emit(tab_id)

    def select_tab(self, tab_id: str):
        for tid, btn in self.nav_items.items():
            btn.setChecked(tid == tab_id)

    def update_task_count(self, pending_count: int):
        if "tasks" in self.nav_items:
            self.nav_items["tasks"].set_badge(pending_count)

    def _on_language_changed(self, lang: str):
        self.sec_lbl.setText(t("sections"))
        self.name_lbl.setText(t("workspace_personal"))
        self.status_text.setText(f"● {t('workspace_local')}")
        self.toggle_btn.setToolTip(t("collapse_sidebar"))
        titles = {
            "dashboard": t("nav_dashboard"),
            "calendar": t("nav_calendar"),
            "notebooks": t("nav_notebooks"),
            "notes": t("nav_notes"),
            "tasks": t("nav_tasks"),
            "settings": t("nav_settings")
        }
        for tab_id, btn in self.nav_items.items():
            if tab_id in titles:
                btn.set_label_text(titles[tab_id])
