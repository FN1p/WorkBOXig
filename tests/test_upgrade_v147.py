"""Migration checks for existing WorkBOXig 1.4.7 user profiles.

The input schema follows the published v1.4.7 src/storage.py DEFAULT_DATA,
without depending on private user files.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from PyQt6.QtCore import QCoreApplication

from src.storage import StorageManager

app = QCoreApplication.instance() or QCoreApplication([])


def legacy_v147_data():
    return {
        "version": "1.4.7",
        "settings": {
            "theme": "light",
            "language": "ru",
            "check_updates_on_startup": True,
            "custom_legacy_setting": "keep this",
        },
        "notebooks": [{
            "id": "legacy-notebook",
            "title": "Archived class notes",
            "pages": [{
                "id": "legacy-page",
                "title": "Formulas",
                "content_html": '<p>My notes</p><img src="file:///C:/old/attachments/legacy.png">',
            }],
        }],
        "notes": [{"id": "legacy-note", "title": "Important", "content": "Never lose me"}],
        "tasks": [{
            "id": "legacy-task", "title": "Homework",
            "status": "todo", "completed": False, "due_date": "2026-10-25",
        }],
        "calendar_events": [{"id": "legacy-event", "title": "Seminar", "date": "2026-10-26"}],
        "recurring_lessons": [{"id": "legacy-recurring", "title": "Math", "weekday": 2}],
        "bell_schedule": [{"number": 1, "start": "08:30", "end": "10:00"}],
        "grades": [{"subject": "Math", "grade": 5}],
        "pomodoro_logs": [{"duration": 25}],
    }


class Legacy147UpgradeTests(unittest.TestCase):
    def test_old_profile_load_preserves_content_and_adds_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            original = legacy_v147_data()
            path = Path(directory, "storage.json")
            path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            storage = StorageManager(storage_dir=directory)
            try:
                self.assertEqual(storage._data["notes"], original["notes"])
                self.assertEqual(storage._data["tasks"], original["tasks"])
                self.assertEqual(storage._data["calendar_events"], original["calendar_events"])
                self.assertEqual(storage._data["recurring_lessons"], original["recurring_lessons"])
                self.assertEqual(storage._data["notebooks"], original["notebooks"])
                self.assertEqual(storage.get_setting("theme"), "light")
                self.assertEqual(storage.get_setting("language"), "ru")
                self.assertEqual(storage.get_setting("custom_legacy_setting"), "keep this")
                self.assertEqual(storage.get_setting("update_channel"), "stable")
                # Reading an existing profile must not rewrite it on startup.
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)
            finally:
                storage._debounce_timer.stop()

    def test_legacy_archive_restores_attachments_and_all_collections(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory, "source")
            target_dir = Path(directory, "target")
            source_dir.mkdir()
            target_dir.mkdir()
            legacy = legacy_v147_data()
            (source_dir / "storage.json").write_text(
                json.dumps(legacy, ensure_ascii=False), encoding="utf-8"
            )
            source = StorageManager(storage_dir=str(source_dir))
            target = StorageManager(storage_dir=str(target_dir))
            try:
                image = Path(source.attachments_dir, "legacy.png")
                image.write_bytes(b"old image data")
                archive = Path(directory, "v147.workboxig")
                source.export_full_backup(str(archive))
                self.assertTrue(target.import_full_backup(str(archive)))
                for collection in (
                    "notes", "tasks", "calendar_events", "recurring_lessons",
                    "grades", "pomodoro_logs", "bell_schedule",
                ):
                    self.assertEqual(target._data[collection], legacy[collection])
                self.assertEqual(target.get_setting("update_channel"), "stable")
                self.assertEqual(target.get_setting("custom_legacy_setting"), "keep this")
                restored_files = list(Path(target.attachments_dir).glob("*"))
                self.assertEqual(len(restored_files), 1)
                self.assertEqual(restored_files[0].read_bytes(), b"old image data")
                html = target._data["notebooks"][0]["pages"][0]["content_html"]
                self.assertIn(restored_files[0].as_uri(), html)
                self.assertTrue(list(target_dir.glob("storage.pre_import_*.workboxig")))
            finally:
                source._debounce_timer.stop()
                target._debounce_timer.stop()

    def test_invalid_backup_does_not_replace_existing_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = StorageManager(storage_dir=directory)
            try:
                before = json.loads(json.dumps(storage._data))
                invalid = Path(directory, "broken.json")
                invalid.write_text('{"settings": {}, "notes": []}', encoding="utf-8")
                self.assertFalse(storage.import_full_backup(str(invalid)))
                self.assertEqual(storage._data, before)
                self.assertFalse(list(Path(directory).glob("storage.pre_import_*.workboxig")))
            finally:
                storage._debounce_timer.stop()


if __name__ == "__main__":
    unittest.main()
