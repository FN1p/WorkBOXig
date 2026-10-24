"""
Tests for Sprint 1 Features:
- Bell Schedule storage
- Subtask checklist operations
- Task Kanban status updates
- Calendar parity filter
"""

import unittest
import shutil
import tempfile
import os
from src.storage import StorageManager, set_storage_instance


class TestSprint1Features(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(storage_dir=self.test_dir)
        set_storage_instance(self.storage)

    def tearDown(self):
        set_storage_instance(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_bell_schedule(self):
        sched = self.storage.get_bell_schedule()
        self.assertIsInstance(sched, list)
        self.assertGreaterEqual(len(sched), 6)
        self.assertEqual(sched[0]["number"], 1)
        self.assertEqual(sched[0]["start"], "08:30")

    def test_update_bell_schedule(self):
        custom_sched = [
            {"number": 1, "start": "09:00", "end": "10:30"},
            {"number": 2, "start": "10:45", "end": "12:15"}
        ]
        self.storage.set_bell_schedule(custom_sched)
        loaded = self.storage.get_bell_schedule()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["start"], "09:00")

    def test_task_status_kanban(self):
        task = self.storage.add_task("Test Kanban", status="todo")
        self.assertEqual(task["status"], "todo")
        self.assertFalse(task["completed"])

        # Move to in_progress
        updated = self.storage.update_task_status(task["id"], "in_progress")
        self.assertEqual(updated["status"], "in_progress")
        self.assertFalse(updated["completed"])

        # Move to done
        done_task = self.storage.update_task_status(task["id"], "done")
        self.assertEqual(done_task["status"], "done")
        self.assertTrue(done_task["completed"])
        self.assertIsNotNone(done_task["completed_at"])

    def test_subtasks_lifecycle(self):
        task = self.storage.add_task("Homework with steps")
        task_id = task["id"]

        # Add subtasks
        sub1 = self.storage.add_subtask(task_id, "Read chapter 1")
        sub2 = self.storage.add_subtask(task_id, "Solve exercises 1-5")
        self.assertIsNotNone(sub1)
        self.assertIsNotNone(sub2)

        # Check subtasks stored
        tasks = self.storage.get_tasks()
        current = next(t for t in tasks if t["id"] == task_id)
        self.assertEqual(len(current["subtasks"]), 2)
        self.assertFalse(current["subtasks"][0]["completed"])

        # Toggle first subtask
        res = self.storage.toggle_subtask(task_id, sub1["id"])
        self.assertTrue(res)
        current = next(t for t in tasks if t["id"] == task_id)
        self.assertTrue(current["subtasks"][0]["completed"])

        # Delete second subtask
        deleted = self.storage.delete_subtask(task_id, sub2["id"])
        self.assertTrue(deleted)
        current = next(t for t in tasks if t["id"] == task_id)
        self.assertEqual(len(current["subtasks"]), 1)

    def test_calendar_week_parity_storage(self):
        # Event with odd parity (Числитель)
        ev = self.storage.add_event(
            title="Algebra Lab",
            date_str="2026-10-26",
            week_parity="odd"
        )
        self.assertEqual(ev.get("week_parity"), "odd")

        # Recurring lesson with even parity (Знаменатель)
        rec = self.storage.add_recurring_lesson(
            title="Physics Lecture",
            weekday=0,
            week_parity="even"
        )
        self.assertEqual(rec.get("week_parity"), "even")


if __name__ == "__main__":
    unittest.main()
