"""
Unit tests for Desktop Mini Widget in WorkBOXig.
"""

import os
import sys
import unittest
import tempfile
import shutil

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.components.mini_widget import DesktopMiniWidget
from src.components.pomodoro import PomodoroManager
from src.storage import StorageManager, set_storage_instance

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestMiniWidget(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)
        set_storage_instance(self.storage)
        self.pomodoro = PomodoroManager()
        self.widget = DesktopMiniWidget(self.pomodoro)

    def tearDown(self):
        self.widget.close()
        self.pomodoro.timer.stop()
        set_storage_instance(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_window_flags(self):
        flags = self.widget.windowFlags()
        self.assertTrue(bool(flags & Qt.WindowType.FramelessWindowHint))
        self.assertTrue(bool(flags & Qt.WindowType.Tool))
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint))

    def test_pomodoro_sync(self):
        # Initial format: 25:00
        self.assertEqual(self.widget.time_lbl.text(), "25:00")

        # Emit time update: 1200 seconds (20:00)
        self.pomodoro.time_updated.emit(1200, "focus", True)
        self.assertEqual(self.widget.time_lbl.text(), "20:00")

        # Emit break mode
        self.pomodoro.time_updated.emit(300, "break", False)
        self.assertEqual(self.widget.time_lbl.text(), "05:00")

    def test_task_display_and_completion(self):
        # Add urgent task
        task = self.storage.add_task(title="Сдать проект по базам данных", priority="urgent")
        self.widget._refresh_content()

        self.assertIn("Сдать проект", self.widget.task_lbl.text())
        self.assertFalse(task["completed"])

        # Complete task via mini widget
        self.widget._complete_current_task()
        updated_tasks = [t for t in self.storage.get_tasks() if t["id"] == task["id"]]
        self.assertTrue(updated_tasks[0]["completed"])

    def test_expand_signal(self):
        signal_received = []
        self.widget.expand_requested.connect(lambda: signal_received.append(True))
        self.widget.expand_btn.click()
        self.assertTrue(len(signal_received) > 0)

    def test_timeline_progress(self):
        # 1200 seconds left out of 1500 (300 elapsed = 20%)
        self.pomodoro.time_updated.emit(1200, "focus", True)
        self.assertEqual(self.widget.elapsed_lbl.text(), "05:00")
        self.assertEqual(self.widget.time_lbl.text(), "20:00")
        self.assertEqual(self.widget.timeline_bar.value(), 200)


if __name__ == "__main__":
    unittest.main()
