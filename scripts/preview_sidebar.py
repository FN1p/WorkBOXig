"""
Preview script to test and refine the sidebar badge and shortcut styling.
"""

import sys
import os

if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from src.components.sidebar import Sidebar

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    sb = Sidebar()
    sb.update_task_count(3)
    sb.select_tab("dashboard")
    sb.show()
    app.processEvents()

    pix = sb.grab()
    os.makedirs("assets", exist_ok=True)
    pix.save("assets/sidebar_current.png", "PNG")
    sb.close()
    print("Saved assets/sidebar_current.png")

if __name__ == "__main__":
    main()
