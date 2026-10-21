"""
Unit tests for System Tray Integration, Close Action Prompt, and Persistence in WorkBOXig.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCloseEvent
from src.storage import StorageManager
from src.components.close_dialog import CloseActionDialog
from src.main_window import MainWindow
from src.version import __version__

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestTrayAndCloseAction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_version_is_1_1_5(self):
        self.assertEqual(__version__, "1.1.5")

    def test_close_dialog_tray_selection(self):
        dialog = CloseActionDialog()
        dialog._choose_tray()
        self.assertEqual(dialog.action, "tray")
        self.assertEqual(dialog.result(), 1)  # QDialog.DialogCode.Accepted

    def test_close_dialog_exit_selection(self):
        dialog = CloseActionDialog()
        dialog._choose_exit()
        self.assertEqual(dialog.action, "exit")
        self.assertEqual(dialog.result(), 1)  # QDialog.DialogCode.Accepted

    def test_close_dialog_remember_checkbox(self):
        dialog = CloseActionDialog()
        self.assertFalse(dialog.remember_cb.isChecked())
        dialog.remember_cb.setChecked(True)
        self.assertTrue(dialog.remember_cb.isChecked())

    def test_main_window_close_minimize_to_tray_setting(self):
        with patch("src.main_window.get_storage", return_value=self.storage):
            win = MainWindow()
            self.storage.set_setting("close_action", "tray")

            event = QCloseEvent()
            win.closeEvent(event)

            self.assertFalse(event.isAccepted())  # Event ignored -> window hidden to tray

    def test_main_window_close_exit_setting(self):
        with patch("src.main_window.get_storage", return_value=self.storage):
            win = MainWindow()
            self.storage.set_setting("close_action", "exit")

            with patch.object(win, "_force_quit") as mock_quit:
                event = QCloseEvent()
                win.closeEvent(event)
                mock_quit.assert_called_once()
                self.assertTrue(event.isAccepted())

    def test_main_window_close_ask_remember_tray(self):
        with patch("src.main_window.get_storage", return_value=self.storage):
            win = MainWindow()
            win._force_close_dialog = True
            self.storage.set_setting("close_action", "ask")

            mock_dlg = MagicMock()
            mock_dlg.exec.return_value = 1
            mock_dlg.action = "tray"
            mock_dlg.remember_cb.isChecked.return_value = True

            with patch("src.main_window.CloseActionDialog", return_value=mock_dlg):
                event = QCloseEvent()
                win.closeEvent(event)

                self.assertFalse(event.isAccepted())
                self.assertEqual(self.storage.get_setting("close_action"), "tray")

    def test_settings_view_close_action_sync(self):
        with patch("src.views.settings_view.get_storage", return_value=self.storage):
            from src.views.settings_view import SettingsView
            sv = SettingsView()
            self.assertEqual(sv.storage.get_setting("close_action", "ask"), "ask")

            # Simulate user changing combobox to 'tray'
            idx = sv.close_combo.findData("tray")
            self.assertGreaterEqual(idx, 0)
            sv.close_combo.setCurrentIndex(idx)

            self.assertEqual(self.storage.get_setting("close_action"), "tray")


if __name__ == "__main__":
    unittest.main()
