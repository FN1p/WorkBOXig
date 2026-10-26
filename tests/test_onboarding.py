import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QPushButton

from src.components.onboarding_dialog import OnboardingDialog
from src.i18n import set_language


app = QApplication.instance() or QApplication(sys.argv)


class TestOnboarding(unittest.TestCase):
    def test_each_step_opens_its_section(self):
        set_language("en")
        dialog = OnboardingDialog()
        requested = []
        dialog.page_requested.connect(requested.append)
        buttons = [b for b in dialog.findChildren(QPushButton) if b.text() == "Open"]
        self.assertEqual(len(buttons), 3)
        for button, expected in zip(buttons, ("tasks", "notebooks", "calendar")):
            button.click()
            self.assertEqual(requested[-1], expected)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
