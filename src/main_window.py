"""
Main Application Window for WorkBOXig.
Coordinates sidebar navigation, top header, Spotlight Command Palette (Ctrl+K),
Pomodoro Focus mode, view stack, global shortcuts, and notifications.
"""

import os
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton, QMenu, QFrame, QApplication,
    QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QFont, QCursor

from src.styles import THEME_STYLESHEET, COLORS, set_active_theme, get_theme_stylesheet
from src.styles_cyber import CyberpunkButtonFilter
from src.storage import get_storage
from src.icons import get_pixmap, get_icon, clear_icon_cache
from src.i18n import t, get_i18n, set_language
from src.version import __version__, APP_NAME
from src.components.close_dialog import CloseActionDialog
from src.components.sidebar import Sidebar
from src.components.toast import ToastNotification
from src.components.desktop_notification import DesktopNotification
from src.components.command_palette import CommandPalette
from src.components.pomodoro import PomodoroManager
from src.views.dashboard_view import DashboardView
from src.views.calendar_view import CalendarView
from src.views.notebooks_view import NotebooksView
from src.views.notes_view import NotesView
from src.views.tasks_view import TasksView
from src.views.settings_view import SettingsView
from src.utils.updater import CheckUpdateThread
from src.components.update_dialog import UpdateDialog
from src.components.mini_widget import DesktopMiniWidget
from src.components.onboarding_dialog import OnboardingDialog


class MainWindow(QMainWindow):
    """Primary Window holding all application modules."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(1260, 820)
        self.setMinimumSize(1020, 680)

        # Apply global stylesheet
        self.setStyleSheet(THEME_STYLESHEET)

        # Set App Window Icon if exists
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.storage = get_storage()
        saved_lang = self.storage.get_setting("language", "en")
        set_language(saved_lang)
        get_i18n().language_changed.connect(self._on_language_changed)

        # Central Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation
        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._switch_page)
        self.sidebar.collapse_toggled.connect(self._on_sidebar_toggled)
        main_layout.addWidget(self.sidebar)

        # Right side: Header + Stack
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 2. Modern Top Navigation Bar
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setFixedHeight(56)
        self.top_bar.setStyleSheet(f"""
            QFrame#top_bar {{
                background-color: {COLORS['bg_root']};
                border-bottom: 1px solid {COLORS['border_subtle']};
            }}
        """)
        tb_layout = QHBoxLayout(self.top_bar)
        tb_layout.setContentsMargins(24, 0, 24, 0)
        tb_layout.setSpacing(12)

        # Sidebar Collapse Toggle Button (Ctrl+B)
        self.sidebar_toggle_btn = QPushButton()
        self.sidebar_toggle_btn.setIcon(get_icon("panel_left", COLORS['text_secondary'], 16))
        self.sidebar_toggle_btn.setFixedSize(32, 32)
        self.sidebar_toggle_btn.setToolTip(t("collapse_sidebar"))
        self.sidebar_toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sidebar_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_subtle']};
            }}
        """)
        self.sidebar_toggle_btn.clicked.connect(self.sidebar.toggle_collapse)
        tb_layout.addWidget(self.sidebar_toggle_btn)

        # Current page breadcrumb
        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setSpacing(8)
        self.page_icon_lbl = QLabel()
        self.page_icon_lbl.setPixmap(get_pixmap("dashboard", COLORS['primary_light'], 18))
        self.page_icon_lbl.setStyleSheet("background: transparent;")
        breadcrumb_layout.addWidget(self.page_icon_lbl)

        self.page_title_lbl = QLabel(t("nav_dashboard"))
        self.page_title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.page_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        breadcrumb_layout.addWidget(self.page_title_lbl)
        tb_layout.addLayout(breadcrumb_layout)

        # Spotlight Search Button (Raycast / Mac style)
        self.search_btn = QPushButton(t("search_placeholder"))
        self.search_btn.setIcon(get_icon("search", COLORS['text_muted'], 14))
        self.search_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.search_btn.setFixedHeight(30)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_light']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.search_btn.clicked.connect(self.open_command_palette)
        tb_layout.addWidget(self.search_btn)

        tb_layout.addStretch()

        # Pomodoro Focus Capsule
        self.pomodoro = PomodoroManager(self)
        self.pomodoro.session_completed.connect(self._on_pomodoro_completed)
        tb_layout.addWidget(self.pomodoro)

        # Quick Add Button with Menu
        self.quick_add_btn = QPushButton(t("quick_add_btn"))
        self.quick_add_btn.setIcon(get_icon("plus", "#FFFFFF", 12))
        self.quick_add_btn.setObjectName("primary-btn")
        self.quick_add_btn.setFixedHeight(32)
        quick_menu = QMenu(self)
        quick_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 14px;
                border-radius: 4px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_subtle']};
                color: {COLORS['primary_light']};
            }}
        """)

        act_task = quick_menu.addAction(get_icon("tasks", COLORS["primary_light"], 16), t("add_task_menu"))
        act_task.triggered.connect(self._quick_add_task)

        act_note = quick_menu.addAction(get_icon("notes", COLORS["amber"], 16), t("add_note_menu"))
        act_note.triggered.connect(self._quick_add_note)

        act_nb = quick_menu.addAction(get_icon("notebooks", COLORS["sky"], 16), t("btn_new_notebook"))
        act_nb.triggered.connect(self._quick_add_notebook)

        act_grade = quick_menu.addAction(get_icon("notebooks", COLORS["emerald"], 16), t("dlg_add_grade_title"))
        act_grade.triggered.connect(self._quick_add_grade)

        self.quick_add_btn.setMenu(quick_menu)
        tb_layout.addWidget(self.quick_add_btn)

        content_layout.addWidget(self.top_bar)

        # 3. View Stack (QStackedWidget)
        self.stack = QStackedWidget(self)
        self.views = {}

        # Views instantiation
        self.dashboard_view = DashboardView(self)
        self.dashboard_view.navigate_requested.connect(self._navigate_to)
        self.dashboard_view.toast_requested.connect(self._show_toast)
        self.dashboard_view.start_pomodoro_requested.connect(self.pomodoro.start_timer)
        self.views["dashboard"] = self.dashboard_view
        self.stack.addWidget(self.dashboard_view)

        self.calendar_view = CalendarView(self)
        self.views["calendar"] = self.calendar_view
        self.stack.addWidget(self.calendar_view)

        self.notebooks_view = NotebooksView(self)
        self.views["notebooks"] = self.notebooks_view
        self.stack.addWidget(self.notebooks_view)

        self.notes_view = NotesView(self)
        self.views["notes"] = self.notes_view
        self.stack.addWidget(self.notes_view)

        self.tasks_view = TasksView(self)
        self.views["tasks"] = self.tasks_view
        self.stack.addWidget(self.tasks_view)

        self.settings_view = SettingsView(self)
        self.settings_view.theme_changed.connect(self._apply_theme)
        self.settings_view.toast_requested.connect(self._show_toast)
        self.settings_view.test_notification_requested.connect(self._show_test_desktop_notification)
        self.views["settings"] = self.settings_view
        self.stack.addWidget(self.settings_view)

        content_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(content_container, stretch=1)

        # 4. Notifications & Desktop Alert Card
        self.toast = ToastNotification(self)
        self.desktop_notification = DesktopNotification()
        self.desktop_notification.action_clicked.connect(self._handle_notification_action)

        self._notified_events = set()
        self._notified_tasks = set()

        # Reminder polling timer (every 30 sec)
        self._reminder_timer = QTimer(self)
        self._reminder_timer.setInterval(30000)
        self._reminder_timer.timeout.connect(self._check_reminders)
        self._reminder_timer.start()

        # 5. Storage Hook for Badges
        self.storage.data_changed.connect(self._update_badges)
        self._update_badges()

        # 6. Global Keyboard Shortcuts
        self._setup_shortcuts()

        # 7. Apply saved theme preference
        self.cyber_filter = CyberpunkButtonFilter()
        saved_theme = self.storage.get_setting("theme", "dark")
        if saved_theme != "dark":
            self._apply_theme(saved_theme)

        # 8. Check for updates on startup (non-blocking, delayed by 3s)
        self._startup_update_thread = None
        if self.storage.get_setting("check_updates_on_startup", True):
            QTimer.singleShot(3000, self._check_startup_update)

        # 9. Auto-sync Google Calendar on startup (non-blocking, delayed by 4s)
        self._startup_google_sync_thread = None
        cal_url = self.storage.get_setting("google_calendar_url", "")
        if cal_url and self.storage.get_setting("google_calendar_auto_sync", True):
            QTimer.singleShot(4000, self._check_startup_google_sync)

        # 10. Floating Desktop Mini Widget (Focus HUD)
        self.mini_widget = DesktopMiniWidget(self.pomodoro, self)
        self.mini_widget.expand_requested.connect(self._restore_from_mini_widget)

        # 11. System Tray Icon & Close Handling
        self.tray_icon = None
        self._setup_tray_icon()

        if not self.storage.get_setting("onboarding_completed", False):
            # Existing workspaces should not be interrupted after an upgrade.
            has_content = any((
                self.storage.get_tasks(), self.storage.get_notes(),
                self.storage.get_notebooks(), self.storage.get_events(),
            ))
            if has_content:
                self.storage.set_setting("onboarding_completed", True)
            else:
                QTimer.singleShot(0, self._show_onboarding)

        self.settings_view.show_onboarding_requested.connect(self._show_onboarding)

    def _show_onboarding(self):
        if not self.isVisible():
            return
        dialog = OnboardingDialog(self)
        dialog.page_requested.connect(self._navigate_to)
        dialog.exec()
        self.storage.set_setting("onboarding_completed", True)

    def _check_startup_google_sync(self):
        cal_url = self.storage.get_setting("google_calendar_url", "")
        if cal_url:
            from src.utils.google_calendar import GoogleCalendarSyncWorker
            self._startup_google_sync_thread = GoogleCalendarSyncWorker(cal_url, self.storage, parent=self)
            self._startup_google_sync_thread.sync_finished.connect(self._on_startup_google_sync_finished)
            self._startup_google_sync_thread.sync_error.connect(
                lambda error: self.show_toast(t("google_sync_fail", error=error), level="warning")
            )
            self._startup_google_sync_thread.start()

    def _on_startup_google_sync_finished(self, added: int, updated: int, total: int):
        if added > 0 or updated > 0:
            self.show_toast(t("google_sync_success", added=added, updated=updated, total=total), icon_type="check")

    def _check_startup_update(self):
        self._startup_update_thread = CheckUpdateThread(parent=self)
        self._startup_update_thread.update_available.connect(self._on_startup_update_available)
        self._startup_update_thread.start()

    def _on_startup_update_available(self, info: dict):
        tag = info.get("tag_name", "")
        self.show_toast(t("toast_new_version", version=tag), icon_type="zap")

    def toggle_mini_widget(self):
        """Toggle floating desktop mini widget visibility."""
        if hasattr(self, "mini_widget"):
            if self.mini_widget.isVisible():
                self.mini_widget.hide()
            else:
                self.mini_widget.show()
                self.mini_widget.raise_()
                self.mini_widget.activateWindow()

    def _restore_from_mini_widget(self):
        """Restore main window when expand button is clicked in mini widget."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _setup_tray_icon(self):
        """Initializes system tray icon with context menu and activation handlers."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip(f"{APP_NAME} v{__version__}")

        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 14px;
                border-radius: 4px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_subtle']};
                color: {COLORS['primary_light']};
            }}
        """)

        act_show = tray_menu.addAction(get_icon("dashboard", COLORS["primary_light"], 16), t("tray_open"))
        act_show.triggered.connect(self._restore_main_window)

        act_widget = tray_menu.addAction(get_icon("widget", COLORS["sky"], 16), t("tray_mini_widget"))
        act_widget.triggered.connect(self.toggle_mini_widget)

        act_update = tray_menu.addAction(get_icon("zap", COLORS["amber"], 16), t("tray_check_updates"))
        act_update.triggered.connect(self._check_for_updates)

        tray_menu.addSeparator()

        act_quit = tray_menu.addAction(get_icon("trash", COLORS["rose"], 16), t("tray_quit"))
        act_quit.triggered.connect(self._force_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _restore_main_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible() and not self.isMinimized() and self.isActiveWindow():
                self.hide()
            else:
                self._restore_main_window()

    def _notify_tray_minimized_once(self):
        """Shows informative balloon message when minimized to tray for first time."""
        if hasattr(self, "tray_icon") and self.tray_icon and self.tray_icon.isVisible():
            if not self.storage.get_setting("tray_balloon_notified", False):
                self.tray_icon.showMessage(
                    t("tray_minimized_title"),
                    t("tray_minimized_msg"),
                    QSystemTrayIcon.MessageIcon.Information,
                    2500
                )
                self.storage.set_setting("tray_balloon_notified", True)

    def _check_for_updates(self):
        """Trigger update check via settings view."""
        self._restore_main_window()
        self._navigate_to("settings")
        if hasattr(self, "settings_view") and hasattr(self.settings_view, "_check_for_updates"):
            self.settings_view._check_for_updates()

    def _force_quit(self):
        """Force application exit, saving state and dismissing tray/widgets."""
        try:
            self.storage.save_immediately()
        except Exception:
            pass
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        if hasattr(self, "mini_widget") and self.mini_widget:
            self.mini_widget.close()
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Intercepts window close to either minimize to tray or quit according to preferences."""
        close_action = self.storage.get_setting("close_action", "ask")

        if close_action == "tray":
            event.ignore()
            self.hide()
            self._notify_tray_minimized_once()
            return
        elif close_action == "exit":
            self._force_quit()
            event.accept()
            return

        # In headless/offscreen test environments, don't block unless explicitly requested
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen" and not getattr(self, "_force_close_dialog", False):
            event.accept()
            return

        # Show prompt dialog
        dialog = CloseActionDialog(self)
        if dialog.exec():
            action = dialog.action
            if dialog.remember_cb.isChecked() and action in ("tray", "exit"):
                self.storage.set_setting("close_action", action)
                if hasattr(self, "settings_view") and hasattr(self.settings_view, "_refresh_close_action_ui"):
                    self.settings_view._refresh_close_action_ui()

            if action == "tray":
                event.ignore()
                self.hide()
                self._notify_tray_minimized_once()
            elif action == "exit":
                self._force_quit()
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    def _on_sidebar_toggled(self, is_collapsed: bool):
        icon_name = "panel_left_open" if is_collapsed else "panel_left"
        self.sidebar_toggle_btn.setIcon(get_icon(icon_name, COLORS['text_secondary'], 16))

    def _switch_page(self, tab_id: str):
        if tab_id in self.views:
            titles = {
                "dashboard": ("dashboard", t("nav_dashboard")),
                "calendar": ("calendar", t("nav_calendar")),
                "notebooks": ("notebooks", t("nav_notebooks")),
                "notes": ("notes", t("nav_notes")),
                "tasks": ("tasks", t("nav_tasks")),
                "settings": ("settings", t("nav_settings"))
            }
            icon_name, title_text = titles.get(tab_id, ("dashboard", "WorkBOXig"))
            self.page_icon_lbl.setPixmap(get_pixmap(icon_name, COLORS['primary_light'], 18))
            self.page_title_lbl.setText(title_text)
            self.page_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            self.stack.setCurrentWidget(self.views[tab_id])

    def _apply_theme(self, theme_name: str):
        """Switches application theme, updates styles and icons without restart."""
        clear_icon_cache()
        new_qss = set_active_theme(theme_name)
        self.setStyleSheet(new_qss)
        self.sidebar.refresh_theme()

        app = QApplication.instance()
        if theme_name == "cyberpunk":
            if app and hasattr(self, "cyber_filter"):
                app.installEventFilter(self.cyber_filter)
        else:
            if app and hasattr(self, "cyber_filter"):
                app.removeEventFilter(self.cyber_filter)
        
        self.top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_root']};
                border-bottom: 1px solid {COLORS['border_subtle']};
            }}
        """)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 4px 14px;
                font-size: 11px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['primary_border']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self.page_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        # Refresh current topbar icon
        cur_tab = self.sidebar.current_tab if hasattr(self.sidebar, "current_tab") else "dashboard"
        titles = {
            "dashboard": "dashboard",
            "calendar": "calendar",
            "notebooks": "notebooks",
            "notes": "notes",
            "tasks": "tasks",
            "settings": "settings"
        }
        ic = titles.get(cur_tab, "dashboard")
        self.page_icon_lbl.setPixmap(get_pixmap(ic, COLORS['primary_light'], 18))
        self.sidebar_toggle_btn.setIcon(get_icon("panel_left" if not self.sidebar.is_collapsed else "panel_left_open", COLORS['text_secondary'], 16))
        is_cyber = (theme_name == "cyberpunk")
        btn_fg = "#000000" if is_cyber else "#FFFFFF"
        if hasattr(self, "quick_add_btn"):
            self.quick_add_btn.setIcon(get_icon("plus", btn_fg, 12))
        if hasattr(self, "dashboard_view"):
            self.dashboard_view.refresh_theme()
        if hasattr(self, "tasks_view"):
            self.tasks_view.refresh_theme()
        if hasattr(self, "calendar_view"):
            self.calendar_view.refresh_theme()
        if hasattr(self, "settings_view"):
            self.settings_view._update_theme_buttons(theme_name)
        self.update()
        for b in self.findChildren(QPushButton):
            b.update()

    def _navigate_to(self, tab_id: str):
        self.sidebar.select_tab(tab_id)
        self._switch_page(tab_id)

    def _show_toast(self, message: str, level: str = "success", icon_type: str = ""):
        if icon_type:
            level = {"check": "success", "zap": "info", "warning": "warning", "close": "error"}.get(icon_type, level)
        self.toast.show_message(message, level)

    show_toast = _show_toast

    def _on_pomodoro_completed(self, mode: str):
        if mode == "focus":
            self._show_toast(t("pomo_focus_finished_toast"), "success")
            self.desktop_notification.notify(
                title=t("pomo_focus_finished_title"),
                message=t("pomo_focus_finished_msg"),
                category="focus",
                badge_text=t("pomo_break_badge"),
                action_type="open_dashboard"
            )
        else:
            self._show_toast(t("pomo_break_finished_toast"), "info")
            self.desktop_notification.notify(
                title=t("pomo_break_finished_title"),
                message=t("pomo_break_finished_msg"),
                category="focus",
                badge_text=t("pomo_focus_badge"),
                action_type="open_dashboard"
            )

    def _show_test_desktop_notification(self):
        """Triggered from Settings to preview the floating desktop notification."""
        self.desktop_notification.notify(
            title=t("notif_test_class"),
            message=t("notif_test_msg"),
            category="lesson",
            badge_text=t("notif_in_min_badge", min=15),
            action_type="open_calendar",
            payload={}
        )

    def _handle_notification_action(self, action_type: str, payload: dict):
        """Navigate to tab and bring window to front when notification button is clicked."""
        if action_type == "open_calendar":
            self._navigate_to("calendar")
        elif action_type == "open_tasks":
            self._navigate_to("tasks")
        elif action_type == "open_notebooks":
            self._navigate_to("notebooks")
        elif action_type == "open_dashboard":
            self._navigate_to("dashboard")

        # Focus window
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _check_reminders(self):
        """Background checker for upcoming lessons and urgent tasks."""
        now = datetime.now()
        today_iso = now.date().isoformat()

        # 1. Lesson Reminders (15 min before)
        if self.storage.get_setting("notif_lessons", True):
            for ev in self.storage.get_events():
                ev_id = ev.get("id")
                if ev.get("date") == today_iso and ev_id not in self._notified_events:
                    time_str = ev.get("time", "")
                    if time_str and ":" in time_str:
                        try:
                            h, m = map(int, time_str.split(":"))
                            ev_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                            diff_min = (ev_time - now).total_seconds() / 60.0
                            if 0 <= diff_min <= 15:
                                self._notified_events.add(ev_id)
                                room_txt = f" • {ev.get('room')}" if ev.get('room') else ""
                                self.desktop_notification.notify(
                                    title=t("notif_lesson_soon_title", title=ev.get('title')),
                                    message=t("notif_lesson_soon_msg", time=time_str, room=room_txt),
                                    category="lesson",
                                    badge_text=t("notif_in_min_badge", min=int(diff_min)),
                                    action_type="open_calendar",
                                    payload={"event_id": ev_id}
                                )
                        except Exception:
                            pass

        # 2. Task Deadlines (Urgent due today)
        if self.storage.get_setting("notif_tasks", True):
            for task_item in self.storage.get_tasks():
                t_id = task_item.get("id")
                if not task_item.get("completed") and task_item.get("priority") == "urgent" and task_item.get("due_date") == today_iso and t_id not in self._notified_tasks:
                    self._notified_tasks.add(t_id)
                    due_txt = f" {task_item.get('due_time')}" if task_item.get('due_time') else ""
                    self.desktop_notification.notify(
                        title=t("notif_deadline_title"),
                        message=f"{task_item.get('title')}{due_txt}",
                        category="task",
                        badge_text=t("notif_deadline_badge"),
                        action_type="open_tasks",
                        payload={"task_id": t_id}
                    )

    def open_command_palette(self):
        palette = CommandPalette(self)
        palette.action_triggered.connect(self._handle_palette_action)
        palette.exec()

    def _handle_palette_action(self, action_type: str, data: dict):
        if action_type == "navigate":
            self._navigate_to(data.get("tab", "dashboard"))
        elif action_type == "create_task":
            self._quick_add_task()
        elif action_type == "create_note":
            self._quick_add_note()
        elif action_type == "create_notebook":
            self._quick_add_notebook()
        elif action_type == "add_grade":
            self._quick_add_grade()
        elif action_type == "open_grades":
            from src.components.grades_dialog import GradesManagementDialog
            dlg = GradesManagementDialog(storage=self.storage, parent=self)
            dlg.exec()
        elif action_type == "start_pomodoro":
            self.pomodoro.open_zen_mode()
        elif action_type == "export_calendar_ics":
            self._navigate_to("calendar")
            self.calendar_view.export_to_ics()
        elif action_type in ("toggle_theme", "set_theme"):
            if action_type == "set_theme":
                new_theme = data.get("theme", "dark")
            else:
                cur = self.storage.get_setting("theme", "dark")
                cycle = ["dark", "light", "cyberpunk"]
                idx = cycle.index(cur) if cur in cycle else 0
                new_theme = cycle[(idx + 1) % len(cycle)]
            self.storage.set_setting("theme", new_theme)
            self._apply_theme(new_theme)
            self.settings_view._update_theme_buttons(new_theme)
            theme_names = {
                "dark": t("theme_dark"),
                "light": t("theme_light"),
                "cyberpunk": "Cyberpunk Neon (Edgerunner)"
            }
            self._show_toast(t("theme_applied", theme=theme_names.get(new_theme, new_theme)), "success")
        elif action_type == "open_task":
            self._navigate_to("tasks")
            self.tasks_view.select_task(data.get("task_id"))
        elif action_type == "open_notebook":
            self._navigate_to("notebooks")
            self.notebooks_view.current_nb_id = data.get("nb_id")
            self.notebooks_view._refresh_notebooks_list()
        elif action_type == "open_page":
            self._navigate_to("notebooks")
            self.notebooks_view.select_page(data.get("nb_id"), data.get("page_id"))
        elif action_type == "open_note":
            self._navigate_to("notes")
            self.notes_view.select_note(data.get("note_id"))

    def _update_badges(self):
        tasks = self.storage.get_tasks()
        pending = sum(1 for tsk in tasks if not tsk.get("completed"))
        self.sidebar.update_task_count(pending)

    def _quick_add_task(self):
        self._navigate_to("tasks")
        self.tasks_view._open_new_task_dialog()

    def _quick_add_note(self):
        self._navigate_to("notes")
        self.notes_view._create_note()

    def _quick_add_notebook(self):
        self._navigate_to("notebooks")
        self.notebooks_view._create_notebook()

    def _quick_add_grade(self):
        from src.components.grades_dialog import AddGradeDialog
        dlg = AddGradeDialog(storage=self.storage, parent=self)
        if dlg.exec():
            self._show_toast(t("grade_added_toast"), "success")

    def _setup_shortcuts(self):
        # Universal Command Palette (Ctrl+K)
        QShortcut(QKeySequence("Ctrl+K"), self, self.open_command_palette)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        # Pomodoro Zen Mode (Ctrl+T)
        QShortcut(QKeySequence("Ctrl+T"), self, self.pomodoro.open_zen_mode)
        # Desktop Mini Widget (F8 and Ctrl+M)
        QShortcut(QKeySequence("F8"), self, self.toggle_mini_widget)
        QShortcut(QKeySequence("Ctrl+M"), self, self.toggle_mini_widget)
        # Toggle Sidebar (Ctrl+B)
        QShortcut(QKeySequence("Ctrl+B"), self, self.sidebar.toggle_collapse)
        # Tabs navigation
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._navigate_to("dashboard"))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._navigate_to("calendar"))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._navigate_to("notebooks"))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self._navigate_to("notes"))
        QShortcut(QKeySequence("Ctrl+5"), self, lambda: self._navigate_to("tasks"))
        QShortcut(QKeySequence("Ctrl+6"), self, lambda: self._navigate_to("settings"))
        QShortcut(QKeySequence("Ctrl+,"), self, lambda: self._navigate_to("settings"))
        QShortcut(QKeySequence("Ctrl+N"), self, self._quick_add_note)
        QShortcut(QKeySequence("Ctrl+S"), self, lambda: (
            self.storage.save_immediately(),
            self._show_toast(t("all_data_saved"), "success")
        ))

    def _focus_search(self):
        current = self.stack.currentWidget()
        if current is self.tasks_view:
            self.tasks_view.search_input.setFocus()
        elif current is self.notes_view:
            self.notes_view.search_input.setFocus()
        else:
            self.open_command_palette()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toast") and self.toast.isVisible():
            self.toast._reposition()

    def _on_language_changed(self, lang: str):
        self.setWindowTitle(t("app_title"))
        self.sidebar_toggle_btn.setToolTip(t("collapse_sidebar"))
        self.search_btn.setText(t("search_placeholder"))
        self.quick_add_btn.setToolTip(t("quick_add"))
        self.tasks_view.quick_task_input.setPlaceholderText(t("quick_task_placeholder"))
        self.tasks_view.quick_task_input.setAccessibleName(t("quick_task_accessible"))
        self.tasks_view.quick_task_input.setToolTip(t("quick_task_hint"))
        self.tasks_view.quick_task_example.setText(t("onboarding_quick_example", date=(date.today() + timedelta(days=1)).isoformat()))
        cur_tab = self.sidebar.current_tab if hasattr(self.sidebar, "current_tab") else "dashboard"
        self._switch_page(cur_tab)
