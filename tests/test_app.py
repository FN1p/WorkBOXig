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

from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QCheckBox, QPushButton
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont
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

    def test_legacy_json_backup_fills_missing_settings_without_losing_notes(self):
        # Synthetic older-format fixture: required collections exist, newer
        # optional collections/settings are absent.
        legacy = {
            "version": "1.4.0",
            "settings": {"theme": "light", "custom_legacy_setting": "kept"},
            "notebooks": [],
            "notes": [{"id": "legacy-note", "title": "Legacy note", "content": "Retained"}],
            "tasks": [],
            "calendar_events": []
        }
        backup = os.path.join(self.test_dir, "legacy.json")
        with open(backup, "w", encoding="utf-8") as handle:
            json.dump(legacy, handle)

        self.assertTrue(self.storage.import_full_backup(backup))
        self.assertEqual(self.storage.get_notes()[0]["title"], "Legacy note")
        self.assertEqual(self.storage.get_setting("theme"), "light")
        self.assertEqual(self.storage.get_setting("custom_legacy_setting"), "kept")
        self.assertTrue(self.storage.get_setting("check_updates_on_startup"))
        self.assertEqual(self.storage.get_recurring_lessons(), [])

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

    def test_unreadable_storage_is_never_overwritten_when_recovery_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            storage_path = Path(directory, "storage.json")
            storage_path.write_text("{corrupt", encoding="utf-8")
            with patch("src.storage.os.rename", side_effect=PermissionError("access denied")):
                with self.assertRaisesRegex(RuntimeError, "startup aborted to avoid data loss"):
                    StorageManager(storage_dir=directory)
            self.assertEqual(storage_path.read_text(encoding="utf-8"), "{corrupt")

    def test_unreadable_storage_is_preserved_as_recovery_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            storage_path = Path(directory, "storage.json")
            storage_path.write_text("{corrupt", encoding="utf-8")
            recovered = StorageManager(storage_dir=directory)
            try:
                backups = list(Path(directory).glob("storage.json.bak-*"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_text(encoding="utf-8"), "{corrupt")
                self.assertEqual(recovered.get_tasks(), [])
            finally:
                recovered._debounce_timer.stop()

    def test_restore_name_collision_keeps_existing_attachment(self):
        from src.utils.backup import write_archive

        existing = Path(self.storage.get_attachments_dir(), "collision.png")
        existing.write_bytes(b"existing attachment")
        source_attachments = Path(self.test_dir, "incoming_attachments")
        source_attachments.mkdir()
        (source_attachments / "image.png").write_bytes(b"incoming image")
        incoming = json.loads(json.dumps(self.storage._data))
        incoming["notes"] = [{"id": "imported", "title": "Imported"}]
        backup = os.path.join(self.test_dir, "incoming.workboxig")
        write_archive(backup, incoming, str(source_attachments))

        with patch("src.storage.new_attachment_name", return_value="collision.png"):
            with self.assertRaises(FileExistsError):
                self.storage.import_full_backup(backup)

        self.assertEqual(existing.read_bytes(), b"existing attachment")
        self.assertEqual(self.storage.get_notes(), [])

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

    def test_direct_task_completion_updates_timestamp(self):
        task = self.storage.add_task("Timestamp check")
        self.assertIsNone(task["completed_at"])

        updated = self.storage.update_task(task["id"], completed=True)
        self.assertEqual(updated["status"], "done")
        self.assertTrue(updated["completed"])
        self.assertIsNotNone(updated["completed_at"])
        finished_at = updated["completed_at"]

        self.storage.update_task(task["id"], title="Renamed")
        self.assertEqual(task["completed_at"], finished_at)

        reopened = self.storage.update_task(task["id"], completed=False)
        self.assertEqual(reopened["status"], "todo")
        self.assertFalse(reopened["completed"])
        self.assertIsNone(reopened["completed_at"])

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
        self.mock_storage.add_task("Finish report", due_date=date.today().isoformat())
        self.window.dashboard_view._refresh_all()
        self.assertEqual(self.window.dashboard_view.today_tasks_layout.count(), 2)

    def test_today_week_preview_opens_future_plans(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.mock_storage.add_task("Prepare slides", due_date=tomorrow)
        self.mock_storage.add_event("Project meeting", tomorrow, time_str="12:00")
        dash = self.window.dashboard_view
        self.assertEqual(dash.week_layout.count(), 7)
        rows = [dash.upcoming_layout.itemAt(i).widget() for i in range(dash.upcoming_layout.count())]
        self.assertTrue(any("Prepare slides" in row.text() for row in rows))
        self.assertTrue(any("Project meeting" in row.text() for row in rows))
        destinations = []
        dash.navigate_requested.connect(destinations.append)
        next(row for row in rows if "Prepare slides" in row.text()).click()
        self.assertEqual(destinations, ["tasks"])

    def test_today_shows_overdue_and_due_tasks_and_allows_completion(self):
        today = date.today()
        self.mock_storage.add_task("Overdue", due_date=(today - timedelta(days=1)).isoformat())
        task = self.mock_storage.add_task("Today", due_date=today.isoformat())
        self.mock_storage.add_task("Future", due_date=(today + timedelta(days=1)).isoformat(), priority="urgent")
        self.mock_storage.add_task("Done", due_date=today.isoformat(), status="done")
        for i in range(7):
            self.mock_storage.add_task(f"Extra {i}", due_date=today.isoformat())
        dash = self.window.dashboard_view
        labels = [label.text() for label in dash.tasks_container.findChildren(QLabel)]
        self.assertIn("Overdue", labels)
        self.assertIn("Today", labels)
        self.assertIn("Extra 6", labels)
        self.assertNotIn("Future", labels)
        self.assertNotIn("Done", labels)
        self.assertEqual(dash.task_badge_lbl.text(), "9")
        checkbox = next(cb for cb in dash.tasks_container.findChildren(QCheckBox) if cb.accessibleName() == "Today")
        checkbox.setChecked(True)
        self.assertTrue(task["completed"])
        self.assertEqual(dash.task_badge_lbl.text(), "8")

    def test_today_includes_recurring_lessons_for_the_current_week(self):
        today = date.today()
        parity = "even" if today.isocalendar().week % 2 == 0 else "odd"
        other = "odd" if parity == "even" else "even"
        self.mock_storage.add_event("Appointment", today.isoformat(), time_str="11:00")
        self.mock_storage.add_recurring_lesson("Current week", today.weekday(), time_str="09:00", week_parity=parity)
        self.mock_storage.add_recurring_lesson("Other week", today.weekday(), week_parity=other)
        self.mock_storage.add_recurring_lesson("Other day", (today.weekday() + 1) % 7)
        dash = self.window.dashboard_view
        labels = [label.text() for label in dash.sched_container.findChildren(QLabel)]
        self.assertIn("Appointment", labels)
        self.assertIn("Current week", labels)
        self.assertNotIn("Other week", labels)
        self.assertNotIn("Other day", labels)
        self.assertIn("2", dash.summary_lbl.text())

    def test_today_refreshes_after_midnight(self):
        today = date.today()
        self.mock_storage.add_task("Tomorrow", due_date=(today + timedelta(days=1)).isoformat())
        dash = self.window.dashboard_view
        self.assertEqual(dash.task_badge_lbl.text(), "0")
        with patch("src.views.dashboard_view.date", wraps=date) as clock:
            clock.today.return_value = today + timedelta(days=1)
            dash._refresh_day_if_needed()
        self.assertEqual(dash.task_badge_lbl.text(), "1")
        self.assertIn("Tomorrow", [label.text() for label in dash.tasks_container.findChildren(QLabel)])

    def test_task_cards_follow_theme_switch(self):
        self.mock_storage.add_task("Finish report", due_date="2026-10-28")
        self.window._apply_theme("light")
        self.assertIn("#FFFFFF", self.window.tasks_view.card_total.styleSheet())
        cards = self.window.tasks_view.findChildren(QFrame, "taskCard")
        self.assertEqual(len(cards), 1)
        self.assertIn("#FFFFFF", cards[0].styleSheet())

    def test_theme_switch_preserves_notes_and_notebook_content(self):
        note = self.mock_storage.add_note(title="Important", content="Keep this note")
        notebook = self.mock_storage.add_notebook("Physics")
        self.mock_storage.add_page(notebook["id"], title="Page", content_html="<p>Keep this page</p>")
        notes = self.window.notes_view
        notebooks = self.window.notebooks_view
        notes._refresh_list()
        notebooks._refresh_notebooks_list()
        notebooks._on_notebook_selected(0)
        notebooks.pages_list_widget.setCurrentRow(1)
        self.window._apply_theme("light")
        self.assertEqual(notes.current_note_id, note["id"])
        self.assertEqual(notes.body_edit.toPlainText(), "Keep this note")
        self.assertIn("Keep this page", notebooks.rich_editor.editor.toPlainText())
        self.assertIn("#0F172A", notes.title_input.styleSheet())
        self.assertIn("#0F172A", notebooks.rich_editor.editor.styleSheet())
        self.assertIn("background-color: #FFFFFF", notebooks.rich_editor.editor.styleSheet())
        self.assertIn("#F1F5F9", notes.left_panel.styleSheet())
        titles = notebooks.findChildren(QLabel, "notebook_item_title")
        self.assertTrue(titles)
        self.assertTrue(all("#0F172A" in label.styleSheet() for label in titles))
        self.window._apply_theme("dark")
        self.assertEqual(notes.body_edit.toPlainText(), "Keep this note")
        self.assertIn("#0E1017", notes.left_panel.styleSheet())
        self.assertIn("#FFFFFF", notebooks.rich_editor.editor.styleSheet())
        self.assertIn("background-color: #131622", notebooks.rich_editor.editor.styleSheet())

    def test_notes_empty_search_can_be_cleared(self):
        self.mock_storage.add_note(title="Find me", content="content")
        notes = self.window.notes_view
        notes._refresh_list()
        notes.search_input.setText("no matching notes")
        self.assertEqual(notes.notes_list.count(), 0)
        notes.empty_action.click()
        self.assertEqual(notes.search_input.text(), "")
        self.assertEqual(notes.notes_list.count(), 1)

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

    def test_month_inspector_shows_recurring_lesson_for_actual_week(self):
        cv = self.window.calendar_view
        selected = QDate(2026, 11, 2)  # Monday, ISO week 45 (odd)
        self.assertEqual(selected.weekNumber()[0] % 2, 1)
        cv.calendar.setSelectedDate(selected)
        self.mock_storage.add_recurring_lesson("Odd-week class", 0, week_parity="odd")
        self.mock_storage.add_recurring_lesson("Even-week class", 0, week_parity="even")
        labels = [label.text() for label in cv.agenda_container.findChildren(QLabel)]
        self.assertIn("Odd-week class", labels)
        self.assertNotIn("Even-week class", labels)

    def test_month_inspector_shows_tasks_and_updates_when_completed(self):
        cv = self.window.calendar_view
        cv.calendar.setSelectedDate(QDate(2026, 11, 4))
        task = self.mock_storage.add_task("Monthly deadline", due_date="2026-11-04")
        buttons = cv.agenda_container.findChildren(QPushButton, "agenda_task_card")
        self.assertEqual(len(buttons), 1)
        self.assertIn("Monthly deadline", buttons[0].text())
        self.window._navigate_to("calendar")
        buttons[0].click()
        self.assertIs(self.window.stack.currentWidget(), self.window.tasks_view)
        self.mock_storage.toggle_task(task["id"])
        self.assertEqual(cv.agenda_container.findChildren(QPushButton, "agenda_task_card"), [])

    def test_month_highlight_clears_when_deadline_is_completed(self):
        cv = self.window.calendar_view
        selected = QDate(2026, 11, 5)
        task = self.mock_storage.add_task("Highlight deadline", due_date="2026-11-05")
        self.assertEqual(cv.calendar.dateTextFormat(selected).fontWeight(), QFont.Weight.Bold.value)
        self.mock_storage.toggle_task(task["id"])
        self.assertNotEqual(cv.calendar.dateTextFormat(selected).fontWeight(), QFont.Weight.Bold.value)

    def test_month_highlights_recurring_lessons_on_matching_iso_weeks(self):
        cv = self.window.calendar_view
        odd_monday = QDate(2026, 11, 2)  # ISO week 45
        even_monday = QDate(2026, 11, 9)  # ISO week 46
        cv.calendar.setCurrentPage(2026, 11)
        odd = self.mock_storage.add_recurring_lesson(
            "Odd recurring", 0, week_parity="odd"
        )
        self.assertEqual(
            cv.calendar.dateTextFormat(odd_monday).fontWeight(),
            QFont.Weight.Bold.value
        )
        self.assertNotEqual(
            cv.calendar.dateTextFormat(even_monday).fontWeight(),
            QFont.Weight.Bold.value
        )
        self.mock_storage.add_recurring_lesson(
            "Even recurring", 0, week_parity="even"
        )
        self.assertEqual(
            cv.calendar.dateTextFormat(even_monday).fontWeight(),
            QFont.Weight.Bold.value
        )
        self.mock_storage.delete_recurring_lesson(odd["id"])
        self.assertNotEqual(
            cv.calendar.dateTextFormat(odd_monday).fontWeight(),
            QFont.Weight.Bold.value
        )
        cv.calendar.setCurrentPage(2026, 12)
        self.assertNotEqual(
            cv.calendar.dateTextFormat(even_monday).fontWeight(),
            QFont.Weight.Bold.value
        )

    def test_weekly_timetable_uses_actual_parity_by_default(self):
        cv = self.window.calendar_view
        self.mock_storage.add_recurring_lesson(
            "Odd-only class", 0, time_str="09:00", week_parity="odd"
        )
        self.mock_storage.add_recurring_lesson(
            "Even-only class", 0, time_str="09:00", week_parity="even"
        )
        self.mock_storage.add_recurring_lesson(
            "Every-week class", 0, time_str="09:00", week_parity="all"
        )

        def visible_titles():
            return [
                card.event_data["title"]
                for card in cv.timetable.grid_container.findChildren(QFrame, "lesson_card")
            ]

        cv.current_monday = QDate(2026, 11, 2)  # ISO week 45
        cv.timetable.set_monday(cv.current_monday)
        cv.current_parity = "all"
        cv._refresh_timetable()
        self.assertIn("Odd-only class", visible_titles())
        self.assertIn("Every-week class", visible_titles())
        self.assertNotIn("Even-only class", visible_titles())

        cv.current_monday = QDate(2026, 11, 9)  # ISO week 46
        cv.timetable.set_monday(cv.current_monday)
        cv._refresh_timetable()
        self.assertIn("Even-only class", visible_titles())
        self.assertNotIn("Odd-only class", visible_titles())

        cv.current_parity = "odd"  # Explicit preview of odd-week lessons
        cv._refresh_timetable()
        self.assertIn("Odd-only class", visible_titles())
        self.assertNotIn("Even-only class", visible_titles())

    def test_calendar_rollover_advances_followed_week_and_selected_today(self):
        cv = self.window.calendar_view
        old_today = QDate(2026, 11, 1)  # Sunday
        new_today = QDate(2026, 11, 2)  # Monday
        cv._last_seen_today = old_today
        cv.current_monday = QDate(2026, 10, 26)
        cv.timetable.set_monday(cv.current_monday)
        cv.calendar.setSelectedDate(old_today)

        cv._apply_day_rollover(old_today, new_today)

        self.assertEqual(cv.current_monday, new_today)
        self.assertEqual(cv.timetable.monday_date, new_today)
        self.assertEqual(cv.selected_qdate, new_today)
        self.assertEqual(cv._last_seen_today, new_today)

    def test_calendar_rollover_preserves_user_browsed_week(self):
        cv = self.window.calendar_view
        old_today = QDate(2026, 11, 1)
        new_today = QDate(2026, 11, 2)
        browsed_monday = QDate(2026, 10, 19)
        browsed_day = QDate(2026, 10, 20)
        cv._last_seen_today = old_today
        cv.current_monday = browsed_monday
        cv.timetable.set_monday(browsed_monday)
        cv.calendar.setSelectedDate(browsed_day)

        cv._apply_day_rollover(old_today, new_today)

        self.assertEqual(cv.current_monday, browsed_monday)
        self.assertEqual(cv.timetable.monday_date, browsed_monday)
        self.assertEqual(cv.selected_qdate, browsed_day)

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
        self.assertEqual(sidebar.nav_items["dashboard"].item_text, "Today")
        self.assertIn("Quick task", self.window.tasks_view.quick_task_input.placeholderText())
        self.assertEqual(sidebar.nav_items["calendar"].item_text, "Calendar")
        self.assertEqual(sidebar.nav_items["settings"].item_text, "Settings")
        
        # Switch back to Russian
        settings._select_language("ru")
        self.assertEqual(sidebar.nav_items["dashboard"].item_text, "Сегодня")
        self.assertIn("Быстрая задача", self.window.tasks_view.quick_task_input.placeholderText())
        self.assertEqual(sidebar.nav_items["calendar"].item_text, "Календарь")
        self.assertEqual(sidebar.nav_items["settings"].item_text, "Настройки")

class TestI18n(unittest.TestCase):
    def test_i18n_translation_and_formatting(self):
        from src.i18n import set_language, get_language, t, format_lessons, format_tasks, format_days
        
        # Test Russian
        set_language("ru")
        self.assertEqual(get_language(), "ru")
        self.assertEqual(t("nav_dashboard"), "Сегодня")
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
        self.assertEqual(t("nav_dashboard"), "Today")
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
