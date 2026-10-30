"""Prevent layout refreshes from flashing detached Qt windows on Windows."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

from src.utils.shortcuts import clear_layout


app = QApplication.instance() or QApplication([])


class LayoutCleanupTests(unittest.TestCase):
    def test_visible_calendar_like_cells_are_hidden_not_detached(self):
        parent = QWidget()
        layout = QGridLayout(parent)
        widgets = [QLabel("Monday"), QLabel("Tuesday"), QLabel("Lesson")]
        for index, widget in enumerate(widgets):
            layout.addWidget(widget, index // 2, index % 2)

        parent.show()
        app.processEvents()
        self.assertTrue(all(widget.isVisible() for widget in widgets))

        clear_layout(layout)

        self.assertEqual(layout.count(), 0)
        for widget in widgets:
            self.assertFalse(widget.isVisible())
            # The old widget is detached to avoid stale findChildren() hits,
            # but it must be hidden *before* it becomes a top-level window.
            self.assertIsNone(widget.parentWidget())
            self.assertNotIn(widget, [top for top in QApplication.topLevelWidgets()
                                       if top.isVisible()])

        parent.close()
        parent.deleteLater()

    def test_empty_or_missing_layout_is_safe(self):
        clear_layout(None)
        parent = QWidget()
        layout = QGridLayout(parent)
        clear_layout(layout)
        self.assertEqual(layout.count(), 0)
        parent.deleteLater()


if __name__ == "__main__":
    unittest.main()
