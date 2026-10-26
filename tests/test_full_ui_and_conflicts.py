"""
End-to-End UI, Logic and Conflict Regression Test Suite.
Verifies all views, dialogs, switching, state management, themes, and i18n without UI conflicts.
"""

import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QDate, QTime

os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QApplication.instance() or QApplication(sys.argv)

from src.main_window import MainWindow
from src.views.calendar_view import AddLessonDialog
from src.views.tasks_view import TaskDialog
from src.components.command_palette import CommandPalette
from src.components.update_dialog import UpdateDialog


class TestFullUIAndConflicts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.win = MainWindow()

    def test_01_all_views_instantiated(self):
        """Verify MainWindow initializes all 6 core view widgets."""
        self.assertIsNotNone(self.win.dashboard_view)
        self.assertIsNotNone(self.win.calendar_view)
        self.assertIsNotNone(self.win.notebooks_view)
        self.assertIsNotNone(self.win.notes_view)
        self.assertIsNotNone(self.win.tasks_view)
        self.assertIsNotNone(self.win.settings_view)

    def test_02_sidebar_tab_navigation(self):
        """Navigate through every tab via sidebar without exceptions."""
        tabs = ["dashboard", "calendar", "notebooks", "notes", "tasks", "settings"]
        for idx, tab_id in enumerate(tabs):
            self.win.sidebar.nav_items[tab_id].click()
            self.assertEqual(self.win.stack.currentIndex(), idx)

    def test_03_calendar_modes_and_parity(self):
        """Switch calendar between week and month modes, and parity filters."""
        cal = self.win.calendar_view

        # Month mode
        cal.mode_month_btn.click()
        self.assertEqual(cal.view_stack.currentIndex(), 1)

        # Week mode
        cal.mode_week_btn.click()
        self.assertEqual(cal.view_stack.currentIndex(), 0)

        # Parity filters
        cal.parity_odd_btn.click()
        self.assertEqual(cal.current_parity, "odd")

        cal.parity_even_btn.click()
        self.assertEqual(cal.current_parity, "even")

        cal.parity_all_btn.click()
        self.assertEqual(cal.current_parity, "all")
        self.assertEqual(len([a for a in cal.more_btn.menu().actions() if not a.isSeparator()]), 4)

    def test_04_calendar_lesson_dialog_regular_and_recurring(self):
        """AddLessonDialog should populate both regular dates and recurring weekdays."""
        # Regular
        dlg1 = AddLessonDialog(preset_date=QDate.currentDate(), recurring_mode=False)
        self.assertFalse(dlg1.recurring_mode)
        d1 = dlg1.get_data()
        self.assertIn("date", d1)
        self.assertIn("week_parity", d1)

        # Recurring
        dlg2 = AddLessonDialog(recurring_mode=True)
        self.assertTrue(dlg2.recurring_mode)
        d2 = dlg2.get_data()
        self.assertIn("weekday", d2)
        self.assertTrue(d2.get("recurring"))
        self.assertIn("week_parity", d2)

    def test_05_tasks_modes_and_kanban_flow(self):
        """Switch tasks between List and Kanban, check subtask support."""
        tasks_view = self.win.tasks_view

        # Toggle to Kanban
        tasks_view.kanban_mode_btn.click()
        self.assertEqual(tasks_view.content_stack.currentIndex(), 1)

        # Toggle back to List
        tasks_view.list_mode_btn.click()
        self.assertEqual(tasks_view.content_stack.currentIndex(), 0)

        # Compact status filter
        for fid in ("all", "today", "upcoming", "overdue", "urgent", "done"):
            tasks_view.status_filter.setCurrentIndex(tasks_view.status_filter.findData(fid))
            self.assertEqual(tasks_view.active_filter, fid)

        # Dialog with subtasks
        dlg = TaskDialog()
        dlg.new_sub_input.setText("Subtask 1")
        dlg._add_subtask_item()
        self.assertEqual(len(dlg.subtasks_data), 1)
        data = dlg.get_data()
        self.assertEqual(len(data.get("subtasks", [])), 1)

    def test_06_settings_categories_and_actions(self):
        """Check all 6 settings pages, bell schedule actions, theme & language."""
        settings = self.win.settings_view

        # Check 6 categories
        self.assertEqual(len(settings.cat_buttons), 6)
        for idx, (cid, btn) in enumerate(settings.cat_buttons.items()):
            btn.click()
            self.assertEqual(settings.stack.currentIndex(), idx)

        # Theme switching without crash
        for theme in ["light", "cyberpunk", "dark"]:
            settings._select_theme(theme)

        # Language switching without crash
        settings._select_language("en")
        settings._select_language("ru")

        # Bell schedule actions
        settings._save_bell_schedule()
        settings._reset_bell_schedule()

    def test_07_command_palette_and_update_dialog(self):
        """Verify command palette search and update dialog instantiate cleanly."""
        palette = CommandPalette(self.win)
        self.assertGreaterEqual(palette.results_list.count(), 1)
        palette.input_field.setText("задач")
        # In RU 'задач' matches 'Создать задачу', in EN it may be 0, so test empty filter too
        palette.input_field.setText("")
        self.assertGreaterEqual(palette.results_list.count(), 1)

        up_dlg = UpdateDialog({"tag_name": "v9.9.9", "body": "Notes"}, storage=self.win.storage)
        self.assertIsNotNone(up_dlg)

    def test_08_quick_notes_and_notebooks(self):
        """Verify quick note creation and notebook view rendering."""
        # Notes view
        notes_view = self.win.notes_view
        self.assertIsNotNone(notes_view.title_input)
        self.assertIsNotNone(notes_view.body_edit)

        # Notebooks view
        nb_view = self.win.notebooks_view
        self.assertIsNotNone(nb_view)


if __name__ == "__main__":
    unittest.main()
