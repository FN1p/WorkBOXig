"""
Render preview of the new Desktop Floating Notification card.
"""

import sys
import os

if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from src.components.desktop_notification import DesktopNotification

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    notif = DesktopNotification()
    notif.notify(
        title="Информатика (Лекция)",
        message="Через 15 минут начинается занятие в Ауд. 402 / Онлайн",
        category="lesson",
        badge_text="Через 15 мин",
        action_type="open_calendar"
    )
    app.processEvents()

    pix = notif.grab()
    os.makedirs("assets", exist_ok=True)
    pix.save("assets/notification_preview.png", "PNG")
    notif.close()
    print("Notification screenshot saved!")

if __name__ == "__main__":
    main()
