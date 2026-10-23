import unittest

from src.utils.quick_task import parse_quick_task


class QuickTaskTests(unittest.TestCase):
    def test_title_date_and_priority(self):
        self.assertEqual(
            parse_quick_task("Finish report @2026-10-28 !high"),
            {"title": "Finish report", "due_date": "2026-10-28", "priority": "high"},
        )

    def test_plain_title(self):
        self.assertEqual(parse_quick_task("Read chapter"), {
            "title": "Read chapter", "due_date": None, "priority": "medium",
        })

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_quick_task("Meeting @2026-02-30")


if __name__ == "__main__":
    unittest.main()
