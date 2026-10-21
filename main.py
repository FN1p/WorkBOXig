"""
WorkBOXig — Productivity & Study Studio
Main Application Entry Point.
"""

import sys
import os
import ctypes
import traceback

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main_window import MainWindow


def setup_windows_app_id():
    """Sets explicit AppUserModelID so Windows displays the correct taskbar icon."""
    try:
        myappid = "workboxig.productivity.study.studio.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass


def setup_windows_dpi():
    """Ensure Windows Per-Monitor DPI awareness (v2) so Windows renders native crisp pixels without bitmap scaling."""
    try:
        # Try Per-Monitor V2 (Windows 10 creators update and newer / Windows 11)
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except Exception:
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE = 2 (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass


def excepthook(exc_type, exc_value, exc_traceback):
    """Global exception hook to prevent silent crashes and log error traces."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"[WorkBOXig Unhandled Exception]:\n{err_msg}", file=sys.stderr)


def main():
    sys.excepthook = excepthook
    setup_windows_dpi()
    setup_windows_app_id()

    # Enable smooth high-DPI scaling on Windows
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("WorkBOXig")
    app.setOrganizationName("WorkBOXig")
    app.setApplicationVersion("1.0.0")

    # Set Application Icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Clean modern default font
    app.setFont(QFont("Segoe UI", 10))

    # Initialize and display Main Window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
