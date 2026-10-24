"""
Unit and Integration Tests for Sprint 2 Features:
- Activity & Focus Heatmap
- Focus Session Persistence & Subject Distribution
- Academic Grades & Weighted GPA Tracker
"""

import sys
import os
import unittest
from datetime import datetime, date

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from src.storage import StorageManager, set_storage_instance
from src.components.activity_heatmap import ActivityHeatmapWidget, HeatmapCell, SubjectDistributionBar
from src.components.grades_dialog import AddGradeDialog, GradesManagementDialog, GradesTrackerWidget
from src.views.dashboard_view import DashboardView


import tempfile
import shutil

class TestSprint2Features(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)
        set_storage_instance(self.storage)

    def tearDown(self):
        set_storage_instance(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_grades_crud(self):
        """Test adding, retrieving, updating and deleting grades."""
        g1 = self.storage.add_grade("Математика", 5.0, weight=1.0, note="Тест по пределам", grade_type="test")
        self.assertIsNotNone(g1["id"])
        self.assertEqual(g1["grade"], 5.0)
        self.assertEqual(g1["subject"], "Математика")

        g2 = self.storage.add_grade("Физика", 4.0, weight=2.0, note="Лабораторная", grade_type="exam")
        self.assertEqual(len(self.storage.get_grades()), 2)
        self.assertEqual(len(self.storage.get_grades("Физика")), 1)

        # Update
        updated = self.storage.update_grade(g1["id"], grade=4.0, note="Исправлено")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["grade"], 4.0)
        self.assertEqual(updated["note"], "Исправлено")

        # Delete
        self.assertTrue(self.storage.delete_grade(g1["id"]))
        self.assertEqual(len(self.storage.get_grades()), 1)

    def test_02_weighted_gpa_calculation(self):
        """Test weighted GPA calculation per subject and overall."""
        # Math: 5 (x1.0) and 3 (x1.0) -> Average = 4.0
        self.storage.add_grade("Математика", 5.0, weight=1.0)
        self.storage.add_grade("Математика", 3.0, weight=1.0)
        self.assertEqual(self.storage.get_subject_gpa("Математика"), 4.0)

        # Physics: 5 (x1.0) and 4 (x2.0) -> (5*1 + 4*2)/3 = 13/3 = 4.33
        self.storage.add_grade("Физика", 5.0, weight=1.0)
        self.storage.add_grade("Физика", 4.0, weight=2.0)
        self.assertAlmostEqual(self.storage.get_subject_gpa("Физика"), 4.33, places=2)

        # Overall GPA: average of 4.0 and 4.33 = 4.16 or 4.17
        overall = self.storage.get_overall_gpa()
        self.assertAlmostEqual(overall, 4.17, places=1)

    def test_03_pomodoro_logging_and_activity_heatmap(self):
        """Test logging focus sessions and aggregating heatmap data."""
        # Add task and complete it
        t = self.storage.add_task("Решить интегралы", subject="Математика")
        self.storage.toggle_task(t["id"])

        # Log pomodoro session
        self.storage.log_pomodoro_session(duration_min=25, task_id=t["id"], subject="Математика")
        self.storage.log_pomodoro_session(duration_min=30, subject="Информатика")

        logs = self.storage.get_pomodoro_logs()
        self.assertEqual(len(logs), 2)

        # Check activity heatmap data
        heatmap_data = self.storage.get_activity_heatmap_data(weeks=16)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(today_str, heatmap_data)
        today_data = heatmap_data[today_str]
        self.assertGreaterEqual(today_data["pomodoros"], 2)
        self.assertGreaterEqual(today_data["tasks"], 1)
        self.assertGreaterEqual(today_data["score"], 7)

        # Subject time distribution
        dist = self.storage.get_subject_time_distribution()
        self.assertIn("Математика", dist)
        self.assertEqual(dist["Математика"], 25)
        self.assertIn("Информатика", dist)
        self.assertEqual(dist["Информатика"], 30)

    def test_04_activity_heatmap_widgets_rendering(self):
        """Test HeatmapCell, SubjectDistributionBar, and ActivityHeatmapWidget instantiation."""
        cell = HeatmapCell("2026-10-24", score=8, pomos=2, tasks=2)
        self.assertEqual(cell.score, 8)

        bar = SubjectDistributionBar({"Математика": 50, "Физика": 50})
        self.assertIsNotNone(bar)

        heatmap = ActivityHeatmapWidget(self.storage)
        self.assertIsNotNone(heatmap)
        heatmap.refresh_data()

    def test_05_grades_dialogs_and_tracker_widget(self):
        """Test AddGradeDialog, GradesManagementDialog and GradesTrackerWidget."""
        dlg = AddGradeDialog(preset_subject="История", storage=self.storage)
        self.assertEqual(dlg.subj_combo.currentText(), "История")
        dlg.note_edit.setText("Реферат по Петру I")
        dlg._on_save()

        grades = self.storage.get_grades("История")
        self.assertEqual(len(grades), 1)

        # Management dialog
        mgr_dlg = GradesManagementDialog(storage=self.storage)
        self.assertGreaterEqual(mgr_dlg.table.rowCount(), 1)

        # Tracker widget
        tracker = GradesTrackerWidget(storage=self.storage)
        self.assertIsNotNone(tracker)
        tracker.refresh_data()
        self.assertEqual(tracker.gpa_val_lbl.text(), "5.00")
        self.assertIsNotNone(tracker.star_icon)

    def test_06_dashboard_view_with_sprint2_analytics(self):
        """Verify DashboardView includes scrollable analytics row with heatmap and grades."""
        dash = DashboardView()
        self.assertTrue(hasattr(dash, "heatmap_widget"))
        self.assertTrue(hasattr(dash, "grades_widget"))
        self.assertTrue(hasattr(dash, "scroll_area"))
        dash._refresh_all()
        dash.refresh_theme()


if __name__ == "__main__":
    unittest.main()
