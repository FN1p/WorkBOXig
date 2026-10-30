"""Regression coverage for the Windows create/edit popup forms."""

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QScrollArea, QWidget

from src.storage import StorageManager, set_storage_instance
from src.views.calendar_view import AddLessonDialog
from src.views.tasks_view import TaskDialog


app = QApplication.instance() or QApplication([])


class ModalFormTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.storage = StorageManager(storage_dir=self.directory.name)
        set_storage_instance(self.storage)
        self.parent = QWidget()
        self.parent.show()

    def tearDown(self):
        self.parent.close()
        self.parent.deleteLater()
        self.storage._debounce_timer.stop()
        set_storage_instance(None)
        self.directory.cleanup()

    def _check_form(self, dialog):
        self.assertIsInstance(dialog, QDialog)
        self.assertIs(dialog.parentWidget(), self.parent)
        self.assertEqual(dialog.windowModality(), Qt.WindowModality.WindowModal)
        self.assertFalse(bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint))
        self.assertIsInstance(dialog.form_scroll, QScrollArea)
        self.assertIs(dialog.form_scroll.widget(), dialog.form_container)
        self.assertTrue(dialog.form_scroll.widgetResizable())

        # At compact sizes, the form scrolls rather than clipping content,
        # while the footer remains a direct non-scrolling child of the dialog.
        dialog.resize(460, 460)
        dialog.show()
        app.processEvents()
        self.assertGreater(dialog.form_scroll.verticalScrollBar().maximum(), 0)
        footer = dialog.findChild(QWidget, "lesson_dialog_footer") or dialog.findChild(
            QWidget, "task_dialog_footer"
        )
        self.assertIsNotNone(footer)
        self.assertIs(footer.parentWidget(), dialog)
        self.assertTrue(footer.findChildren(QPushButton))
        dialog.reject()
        dialog.deleteLater()

    def test_add_lesson_dialog_has_accessible_scrolling_form(self):
        dialog = AddLessonDialog(parent=self.parent)
        self._check_form(dialog)

    def test_task_dialog_has_accessible_scrolling_form(self):
        dialog = TaskDialog(parent=self.parent)
        self._check_form(dialog)

    def test_lesson_color_selection_matches_actual_color(self):
        dialog = AddLessonDialog(parent=self.parent)
        dialog._apply_preset("Literature", "#EC4899")
        self.assertEqual(dialog.selected_color, "#EC4899")
        checked = [button.property("lesson_hex_color") for button
                   in dialog.color_group.buttons() if button.isChecked()]
        self.assertEqual(checked, ["#EC4899"])
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
