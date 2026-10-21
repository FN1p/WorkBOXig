"""
Unit tests for Google Calendar Live iCal Synchronization in WorkBOXig.
"""

import os
import sys
import unittest
import tempfile
import shutil

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from src.utils.google_calendar import (
    normalize_calendar_url, unfold_ical_lines, unescape_ical_text,
    parse_ical_datetime, parse_ical_events
)
from src.components.google_sync_dialog import GoogleSyncDialog
from src.storage import StorageManager

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

SAMPLE_ICS = """BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
DTSTART:20261022T083000Z
DTEND:20261022T100000Z
UID:math_lecture_101@google.com
SUMMARY:Высшая математика (Лекция)
DESCRIPTION:Материалы к лекции:\nГлава 4 интегралы.
LOCATION:Аудитория 402
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261025
DTEND;VALUE=DATE:20261026
UID:all_day_hackathon@google.com
SUMMARY:Cyberpunk Hackathon
DESCRIPTION:Annual coding marathon
LOCATION:Online Zoom
END:VEVENT
END:VCALENDAR"""


class TestGoogleCalendarSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_url_normalization(self):
        self.assertEqual(
            normalize_calendar_url("webcal://calendar.google.com/ical/basic.ics"),
            "https://calendar.google.com/ical/basic.ics"
        )
        self.assertEqual(
            normalize_calendar_url("http://calendar.google.com/ical/basic.ics"),
            "https://calendar.google.com/ical/basic.ics"
        )
        self.assertEqual(
            normalize_calendar_url("  https://calendar.google.com/ical/basic.ics  "),
            "https://calendar.google.com/ical/basic.ics"
        )

    def test_unfold_lines(self):
        raw = "SUMMARY:Длинный заголовок\n предмета и темы\nDESCRIPTION:Описание"
        unfolded = unfold_ical_lines(raw)
        self.assertEqual(len(unfolded), 2)
        self.assertEqual(unfolded[0], "SUMMARY:Длинный заголовокпредмета и темы")

    def test_unescape_text(self):
        raw = r"Line 1\nLine 2\, with commas\; and backslashes\\"
        cleaned = unescape_ical_text(raw)
        self.assertEqual(cleaned, "Line 1\nLine 2, with commas; and backslashes\\")

    def test_parse_datetime(self):
        # All-day
        d, t = parse_ical_datetime("VALUE=DATE:20261025")
        self.assertEqual(d, "2026-10-25")
        self.assertEqual(t, "00:00")

        # Local timestamp
        d2, t2 = parse_ical_datetime("TZID=Europe/Moscow:20261022T143000")
        self.assertEqual(d2, "2026-10-22")
        self.assertEqual(t2, "14:30")

    def test_parse_ical_events(self):
        events = parse_ical_events(SAMPLE_ICS)
        self.assertEqual(len(events), 2)

        e1 = events[0]
        self.assertEqual(e1["google_uid"], "math_lecture_101@google.com")
        self.assertEqual(e1["title"], "Высшая математика (Лекция)")
        self.assertEqual(e1["room"], "Аудитория 402")
        self.assertEqual(e1["source"], "google")

        e2 = events[1]
        self.assertEqual(e2["google_uid"], "all_day_hackathon@google.com")
        self.assertEqual(e2["title"], "Cyberpunk Hackathon")
        self.assertEqual(e2["date"], "2026-10-25")

    def test_sync_deduplication_and_update(self):
        # Initial local event created by user
        self.storage.add_event(title="Моё личное занятие", date_str="2026-10-21")
        self.assertEqual(len(self.storage.get_events()), 1)

        # First sync pass
        events = parse_ical_events(SAMPLE_ICS)
        for ev in events:
            new_e = dict(ev)
            new_e["id"] = ev["google_uid"]
            self.storage._data["calendar_events"].append(new_e)

        self.assertEqual(len(self.storage.get_events()), 3)

        # Second sync pass: modified event
        modified_ics = SAMPLE_ICS.replace("Аудитория 402", "Аудитория 505 (Новая)")
        events_v2 = parse_ical_events(modified_ics)
        existing = {e.get("google_uid"): e for e in self.storage.get_events() if e.get("google_uid")}

        for ev in events_v2:
            uid = ev["google_uid"]
            if uid in existing:
                existing[uid]["room"] = ev["room"]

        # No duplicate events added, room updated!
        self.assertEqual(len(self.storage.get_events()), 3)
        updated_evt = [e for e in self.storage.get_events() if e.get("google_uid") == "math_lecture_101@google.com"][0]
        self.assertEqual(updated_evt["room"], "Аудитория 505 (Новая)")

    def test_dialog_instantiation(self):
        dialog = GoogleSyncDialog(storage=self.storage)
        self.assertIsNotNone(dialog)
        self.assertIn("Google", dialog.windowTitle())
        dialog.close()


if __name__ == "__main__":
    unittest.main()
