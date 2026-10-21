"""
Script to capture screenshots of Installer wizard steps.
"""

import sys
import os

if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from installer import InstallerWindow

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    # 1. Welcome Page
    win = InstallerWindow()
    win.show()
    app.processEvents()

    pix = win.grab()
    pix.save("assets/installer_welcome.png", "PNG")

    # 2. Options Page
    win.stack.setCurrentIndex(1)
    win.back_btn.setVisible(True)
    win.next_btn.setText("Установить")
    app.processEvents()
    pix2 = win.grab()
    pix2.save("assets/installer_options.png", "PNG")

    # 3. Installing progress
    win.stack.setCurrentIndex(2)
    win.prog_bar.setValue(68)
    win.prog_status.setText("Создание ярлыка на Рабочем столе...")
    app.processEvents()
    pix3 = win.grab()
    pix3.save("assets/installer_progress.png", "PNG")

    # 4. Completed
    win.stack.setCurrentIndex(3)
    win.cancel_btn.setVisible(False)
    win.next_btn.setEnabled(True)
    win.next_btn.setText("Готово")
    app.processEvents()
    pix4 = win.grab()
    pix4.save("assets/installer_finish.png", "PNG")

    win.close()
    print("Installer preview screenshots saved!")

if __name__ == "__main__":
    main()
