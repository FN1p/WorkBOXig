"""
Unit tests for In-App Updater and Zero-Data-Loss Persistence in WorkBOXig.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from src.utils.updater import parse_version_tuple, is_newer_version, CheckUpdateThread, DownloadUpdateThread
from src.components.update_dialog import UpdateDialog
from src.storage import StorageManager
from src.version import __version__

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_version_tuple_parsing(self):
        self.assertEqual(parse_version_tuple("v1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version_tuple("v2.10.5-beta"), (2, 10, 5))
        self.assertEqual(parse_version_tuple("v0.5"), (0, 5, 0))

    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("v1.0.1", "1.0.0"))
        self.assertTrue(is_newer_version("v1.1.0", "1.0.9"))
        self.assertTrue(is_newer_version("v2.0.0", "1.99.99"))
        self.assertFalse(is_newer_version("v1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("v0.9.9", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.1"))

    def test_pre_update_backup_preserves_data(self):
        # Populate notes and tasks
        self.storage.add_note(title="Важный конспект перед обновлением", content="Формулы и схемы")
        self.storage.add_task(title="Сдать курсовую", priority="urgent")

        backup_file = self.storage.create_pre_update_backup()
        self.assertTrue(os.path.exists(backup_file))

        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data.get("notes", [])), 1)
        self.assertEqual(data["notes"][0]["title"], "Важный конспект перед обновлением")
        self.assertEqual(len(data.get("tasks", [])), 1)
        self.assertEqual(data["tasks"][0]["title"], "Сдать курсовую")

    def test_update_dialog_instantiation(self):
        mock_info = {
            "tag_name": "v1.0.1",
            "title": "WorkBOXig v1.0.1",
            "body": "- Performance improvements\n- Cyberpunk animations enhanced",
            "html_url": "https://github.com/FN1p/WorkBOXig/releases/tag/v1.0.1",
            "installer_url": "https://github.com/FN1p/WorkBOXig/releases/download/v1.0.1/WorkBOXig_Setup.exe",
            "installer_name": "WorkBOXig_Setup.exe",
            "installer_size": 82000000,
            "is_newer": True
        }
        dialog = UpdateDialog(mock_info, storage=self.storage)
        self.assertIsNotNone(dialog)
        self.assertIn("Performance improvements", dialog.notes_browser.toPlainText())
        self.assertEqual(dialog.release_info["tag_name"], "v1.0.1")
        dialog.close()


if __name__ == "__main__":
    unittest.main()
