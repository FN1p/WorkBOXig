"""
Comprehensive verification test suite for WorkBOXig.
Tests storage engine, business logic, filters, Command Palette, Pomodoro, and UI widget lifecycle.
"""

import sys
import os
import unittest
import tempfile
import shutil
import json
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname
from unittest.mock import patch
from datetime import date, timedelta

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication, QFrame
from PyQt6.QtCore import QDate
from src.storage import StorageManager, set_storage_instance
from src.main_window import MainWindow
from src.components.command_palette import CommandPalette
from src.components.pomodoro import PomodoroManager

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)

    def tearDown(self):
        self.storage._debounce_timer.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_data_populated(self):
        self.assertIn("notebooks", self.storage._data)
        self.assertIn("notes", self.storage._data)
        self.assertIn("tasks", self.storage._data)
        self.assertIn("calendar_events", self.storage._data)
        self.assertEqual(len(self.storage.get_notebooks()), 0)
        self.assertEqual(len(self.storage.get_tasks()), 0)

    def test_invalid_backup_does_not_replace_data(self):
        self.storage.add_note(title="Keep me")
        backup = os.path.join(self.test_dir, "invalid.json")
        invalid_data = json.loads(json.dumps(self.storage._data))
        invalid_data["notes"] = "not a list"
        with open(backup, "w", encoding="utf-8") as handle:
            json.dump(invalid_data, handle)
        self.assertFalse(self.storage.import_full_backup(backup))
        self.assertEqual(self.storage.get_notes()[0]["title"], "Keep me")

    def test_empty_backup_does_not_erase_data(self):
        self.storage.add_note(title="Keep me")
        backup = os.path.join(self.test_dir, "empty.json")
        with open(backup, "w", encoding="utf-8") as handle:
            json.dump({}, handle)
        self.assertFalse(self.storage.import_full_backup(backup))
        self.assertEqual(self.storage.get_notes()[0]["title"], "Keep me")

    def test_import_saves_previous_data_before_replacing_it(self):
        self.storage.add_note(title="Previous note")
        backup = os.path.join(self.test_dir, "import.json")
        imported_data = json.loads(json.dumps(self.storage._data))
        imported_data["notes"] = [{"id": "new", "title": "Imported note"}]
        with open(backup, "w", encoding="utf-8") as handle:
            json.dump(imported_data, handle)
        self.assertTrue(self.storage.import_full_backup(backup))
        self.assertEqual(self.storage.get_notes()[0]["title"], "Imported note")
        snapshots = [name for name in os.listdir(self.test_dir) if name.startswith("storage.pre_import_")]
        self.assertEqual(len(snapshots), 1)
        with zipfile.ZipFile(os.path.join(self.test_dir, snapshots[0])) as archive:
            previous = json.loads(archive.read("storage.json"))
        self.assertEqual(previous["notes"][0]["title"], "Previous note")

    def test_portable_backup_restores_notebook_image(self):
        image_path = Path(self.storage.get_attachments_dir(), "image.png")
        image_path.write_bytes(b"image data")
        notebook = self.storage.add_notebook("Images")
        notebook["pages"][0]["content_html"] = f'<img src="{image_path.as_uri()}">'
        archive_path = os.path.join(self.test_dir, "portable.workboxig")
        self.storage.export_full_backup(archive_path)
        image_path.unlink()
        self.assertTrue(self.storage.import_full_backup(archive_path))
        html = self.storage.get_notebooks()[0]["pages"][0]["content_html"]
        self.assertNotIn(image_path.as_uri(), html)
        restored_name = html.split('src="')[1].split('"')[0]
        self.assertEqual(Path(url2pathname(urlparse(restored_name).path)).read_bytes(), b"image data")

    def test_failed_import_keeps_previous_data_and_cleans_temp_file(self):
        self.storage.add_note(title="Previous note")
        self.storage.save_immediately()
        backup = os.path.join(self.test_dir, "import.json")
        imported_data = json.loads(json.dumps(self.storage._data))
        imported_data["notes"] = []
        with open(backup, "w", encoding="utf-8") as handle:
            json.dump(imported_data, handle)
        real_replace = os.replace

        def fail_storage_write(source, destination):
            if destination == self.storage.file_path:
                raise OSError("disk error")
            return real_replace(source, destination)

        with patch("src.storage.os.replace", side_effect=fail_storage_write):
            self.assertFalse(self.storage.import_full_backup(backup))
        self.assertEqual(self.storage.get_notes()[0]["title"], "Previous note")
        self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(self.test_dir)))

    def test_task_crud(self):
        t = self.storage.add_task(title="Тестовая задача", subject="Тест", priority="urgent")
        self.assertEqual(t["title"], "Тестовая задача")
        self.assertFalse(t["completed"])

        # Toggle
        res = self.storage.toggle_task(t["id"])
        self.assertTrue(res)

        # Update
        updated = self.storage.update_task(t["id"], title="Обновленная задача")
        self.assertEqual(updated["title"], "Обновленная задача")

        # Delete
        del_res = self.storage.delete_task(t["id"])
        self.assertTrue(del_res)

    def test_notebooks_and_pages(self):
        nb = self.storage.add_notebook(title="Химия")
        self.assertEqual(nb["title"], "Химия")
        self.assertEqual(len(nb["pages"]), 1)

        page = self.storage.add_page(nb["id"], title="Органика", content_html="<b>Тест</b>")
        self.assertIsNotNone(page)

        up_res = self.storage.update_page(nb["id"], page["id"], title="Органическая химия")
        self.assertTrue(up_res)

        del_p = self.storage.delete_page(nb["id"], page["id"])
        self.assertTrue(del_p)

        del_nb = self.storage.delete_notebook(nb["id"])
        self.assertTrue(del_nb)

    def test_notes(self):
        n = self.storage.add_note(title="Заметка", content="Текст заметки", tags=["тест", "важное"])
        self.assertEqual(n["title"], "Заметка")
        self.assertIn("тест", n["tags"])

        pin_state = self.storage.toggle_pin_note(n["id"])
        self.assertTrue(pin_state)

        del_n = self.storage.delete_note(n["id"])
        self.assertTrue(del_n)

    def test_notes_are_sorted_pinned_first_and_newest_first(self):
        old = self.storage.add_note(title="Old")
        new = self.storage.add_note(title="New")
        pinned = self.storage.add_note(title="Pinned")
        old["updated_at"] = "2025-01-01T00:00:00"
        new["updated_at"] = "2026-01-01T00:00:00"
        pinned["updated_at"] = "2024-01-01T00:00:00"
        pinned["pinned"] = True
        self.assertEqual([note["title"] for note in self.storage.get_notes()], ["Pinned", "New", "Old"])

    def test_events(self):
        evt = self.storage.add_event(title="Экзамен", date_str="2026-11-01", time_str="09:00")
        self.assertEqual(evt["title"], "Экзамен")
        del_e = self.storage.delete_event(evt["id"])
        self.assertTrue(del_e)


class TestUIWidgets(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_storage = StorageManager(storage_dir=self.test_dir)
        set_storage_instance(self.mock_storage)
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        app.processEvents()
        self.mock_storage._debounce_timer.stop()
        set_storage_instance(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_views_initialization(self):
        self.assertIn("dashboard", self.window.views)
        self.assertIn("calendar", self.window.views)
        self.assertIn("notebooks", self.window.views)
        self.assertIn("notes", self.window.views)
        self.assertIn("tasks", self.window.views)

    def test_dashboard_renders_existing_task(self):
        self.mock_storage.add_task("Finish report", due_date="2026-10-28")
        self.window.dashboard_view._refresh_all()
        self.assertEqual(self.window.dashboard_view.today_tasks_layout.count(), 1)

    def test_task_cards_follow_theme_switch(self):
        self.mock_storage.add_task("Finish report", due_date="2026-10-28")
        self.window._apply_theme("light")
        self.assertIn("#FFFFFF", self.window.tasks_view.card_total.styleSheet())
        cards = self.window.tasks_view.findChildren(QFrame, "taskCard")
        self.assertEqual(len(cards), 1)
        self.assertIn("#FFFFFF", cards[0].styleSheet())

    def test_navigation_switching(self):
        for tab_id in ["calendar", "notebooks", "notes", "tasks", "dashboard"]:
            self.window._switch_page(tab_id)
            self.assertEqual(self.window.stack.currentWidget(), self.window.views[tab_id])

    def test_task_filters(self):
        tv = self.window.tasks_view
        for fid in ["all", "today", "upcoming", "overdue", "urgent", "done"]:
            tv._set_filter(fid)
            self.assertEqual(tv.active_filter, fid)

    def test_notes_tag_filtering(self):
        nv = self.window.notes_view
        nv._select_tag("all")
        self.assertEqual(nv.selected_tag, "all")

    def test_calendar_date_selection(self):
        cv = self.window.calendar_view
        cv.calendar.setSelectedDate(QDate(2026, 12, 31))
        cv._on_date_selected()
        self.assertEqual(cv.selected_qdate, QDate(2026, 12, 31))

    def test_topbar_search_and_create(self):
        self.assertIsNotNone(self.window.search_btn)
        self.assertIsNotNone(self.window.quick_add_btn.menu())

    def test_ctrl_f_targets_current_search(self):
        self.window._navigate_to("tasks")
        with patch.object(self.window.tasks_view.search_input, "setFocus") as focus:
            self.window._focus_search()
            focus.assert_called_once()
        self.window._navigate_to("notes")
        with patch.object(self.window.notes_view.search_input, "setFocus") as focus:
            self.window._focus_search()
            focus.assert_called_once()

    def test_command_palette_search(self):
        palette = CommandPalette(self.window)
        # Test searching static actions (always present)
        from src.i18n import get_language; palette._populate_results("task" if get_language() == "en" else "задач")
        self.assertTrue(palette.results_list.count() > 0)
        # Test empty query returns actions
        palette._populate_results("")
        self.assertTrue(palette.results_list.count() > 0)
        palette.close()

    def test_pomodoro_toggle(self):
        pomo = self.window.pomodoro
        self.assertFalse(pomo.is_running)
        pomo.toggle_timer()
        self.assertTrue(pomo.is_running)
        pomo.toggle_timer()
        self.assertFalse(pomo.is_running)

    def test_notebooks_focus_mode(self):
        nb_view = self.window.notebooks_view
        self.assertFalse(nb_view.is_focus_fullscreen)
        nb_view._toggle_focus_mode()
        self.assertTrue(nb_view.is_focus_fullscreen)
        nb_view._toggle_focus_mode()
        self.assertFalse(nb_view.is_focus_fullscreen)

    def test_sidebar_collapse(self):
        sidebar = self.window.sidebar
        self.assertFalse(sidebar.is_collapsed)
        sidebar.toggle_collapse()
        self.assertTrue(sidebar.is_collapsed)
        sidebar.toggle_collapse()
        self.assertFalse(sidebar.is_collapsed)

    def test_notebook_image_insertion(self):
        from PyQt6.QtGui import QImage, QColor
        editor = self.window.notebooks_view.rich_editor.editor
        test_img = QImage(120, 120, QImage.Format.Format_ARGB32)
        test_img.fill(QColor("blue"))
        editor.insert_qimage(test_img)
        html = editor.toHtml()
        self.assertIn("<img", html)

    def test_settings_view_and_theme_switching(self):
        # Verify settings view is registered
        self.assertIn("settings", self.window.views)
        self.window._navigate_to("settings")
        self.assertEqual(self.window.stack.currentWidget(), self.window.settings_view)

        # Test switching across all themes: light, cyberpunk, dark
        self.window._apply_theme("light")
        from src.styles import COLORS
        self.assertEqual(COLORS["text_primary"], "#0F172A")
        self.assertEqual(COLORS["bg_root"], "#F8FAFC")

        self.window._apply_theme("cyberpunk")
        self.assertEqual(COLORS["primary"], "#FCEE0A")
        self.assertEqual(COLORS["sky"], "#00F0FF")
        self.assertEqual(COLORS["bg_root"], "#08090D")

        self.window._apply_theme("dark")
        self.assertEqual(COLORS["text_primary"], "#FFFFFF")
        self.assertEqual(COLORS["bg_root"], "#0A0B10")

    def test_storage_settings_and_backup(self):
        storage = self.window.storage
        storage.set_setting("test_key", "test_val")
        self.assertEqual(storage.get_setting("test_key"), "test_val")

        # Test full backup export & import
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            backup_path = tf.name

        try:
            storage.export_full_backup(backup_path)
            self.assertTrue(os.path.exists(backup_path))
            self.assertGreater(os.path.getsize(backup_path), 50)
            success = storage.import_full_backup(backup_path)
            self.assertTrue(success)
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)

    def test_autostart_support(self):
        from src.utils.autostart import is_autostart_supported
        # On Windows platform, autostart with winreg is supported
        if sys.platform == "win32":
            self.assertTrue(is_autostart_supported())

    def test_desktop_notification(self):
        notif = self.window.desktop_notification
        notif.notify(
            title="Тест",
            message="Тестовое сообщение",
            category="lesson",
            badge_text="Тест",
            action_type="open_calendar"
        )
        self.assertEqual(notif.title_lbl.text(), "Тест")
        self.assertEqual(notif.action_type, "open_calendar")
        notif.close_animated()


    def test_calendar_ics_export(self):
        cal = self.window.calendar_view
        sample_events = [
            {
                "id": "evt_test_1",
                "title": "Высшая математика",
                "date": "2026-10-25",
                "time": "10:00",
                "end_time": "11:30",
                "room": "Ауд. 401",
                "description": "Лекция по интегралам",
                "type": "Лекция"
            }
        ]
        ics_text = cal._generate_ics_content(sample_events)
        self.assertIn("BEGIN:VCALENDAR", ics_text)
        self.assertIn("VERSION:2.0", ics_text)
        self.assertIn("BEGIN:VEVENT", ics_text)
        self.assertIn("SUMMARY:Высшая математика", ics_text)
        self.assertIn("DTSTART:20261025T100000", ics_text)
        self.assertIn("DTEND:20261025T113000", ics_text)
        self.assertIn("LOCATION:Ауд. 401", ics_text)
        self.assertIn("END:VEVENT", ics_text)
        self.assertIn("END:VCALENDAR", ics_text)

    def test_clear_layout_utility(self):
        from src.utils.shortcuts import clear_layout
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        w = QWidget()
        lay = QVBoxLayout(w)
        lbl1 = QLabel("one")
        lbl2 = QLabel("two")
        lay.addWidget(lbl1)
        lay.addWidget(lbl2)
        self.assertEqual(lay.count(), 2)
        clear_layout(lay)
        self.assertEqual(lay.count(), 0)

    def test_cyberpunk_button_painter(self):
        from src.styles_cyber import CyberpunkButtonPainter
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtGui import QPainter, QPixmap
        btn = QPushButton("Test Primary")
        btn.setObjectName("primary-btn")
        btn.resize(160, 40)
        pix = QPixmap(160, 40)
        painter = QPainter(pix)
        try:
            CyberpunkButtonPainter.paint_button(painter, btn)
        finally:
            painter.end()



    def test_settings_language_reactive_switch(self):
        settings = self.window.settings_view
        sidebar = self.window.sidebar
        
        # Switch to English
        settings._select_language("en")
        self.assertEqual(sidebar.nav_items["dashboard"].item_text, "Dashboard")
        self.assertIn("Quick task", self.window.tasks_view.quick_task_input.placeholderText())
        self.assertEqual(sidebar.nav_items["calendar"].item_text, "Calendar")
        self.assertEqual(sidebar.nav_items["settings"].item_text, "Settings")
        
        # Switch back to Russian
        settings._select_language("ru")
        self.assertEqual(sidebar.nav_items["dashboard"].item_text, "Дашборд")
        self.assertIn("Быстрая задача", self.window.tasks_view.quick_task_input.placeholderText())
        self.assertEqual(sidebar.nav_items["calendar"].item_text, "Календарь")
        self.assertEqual(sidebar.nav_items["settings"].item_text, "Настройки")

class TestI18n(unittest.TestCase):
    def test_i18n_translation_and_formatting(self):
        from src.i18n import set_language, get_language, t, format_lessons, format_tasks, format_days
        
        # Test Russian
        set_language("ru")
        self.assertEqual(get_language(), "ru")
        self.assertEqual(t("nav_dashboard"), "Дашборд")
        self.assertEqual(format_lessons(1), "1 урок")
        self.assertEqual(format_lessons(3), "3 урока")
        self.assertEqual(format_lessons(5), "5 уроков")
        self.assertEqual(format_tasks(1), "1 задача")
        self.assertEqual(format_tasks(4), "4 задачи")
        self.assertEqual(format_tasks(10), "10 задач")
        self.assertEqual(format_days(1), "1 день")
        self.assertEqual(format_days(2), "2 дня")
        self.assertEqual(format_days(7), "7 дней")

        # Test English
        set_language("en")
        self.assertEqual(get_language(), "en")
        self.assertEqual(t("nav_dashboard"), "Dashboard")
        self.assertEqual(format_lessons(1), "1 class")
        self.assertEqual(format_lessons(3), "3 classes")
        self.assertEqual(format_tasks(1), "1 task")
        self.assertEqual(format_tasks(5), "5 tasks")
        self.assertEqual(format_days(1), "1 day")
        self.assertEqual(format_days(5), "5 days")

        # Revert
        set_language("ru")

if __name__ == "__main__":
    unittest.main()
