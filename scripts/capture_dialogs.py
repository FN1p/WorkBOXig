"""
Script to capture screenshots of AddLessonDialog and TaskDialog to verify the layout fix.
"""

import sys
import os
from datetime import date

if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QDate, QTime
from src.styles import get_theme_stylesheet
from src.views.calendar_view import AddLessonDialog
from src.views.tasks_view import TaskDialog

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(get_theme_stylesheet("dark"))

    # 1. Lesson Dialog (Edit mode populated as in user's screenshot)
    lesson_data = {
        "title": "Информатика (Лекция)",
        "date": "2026-10-21",
        "start_time": "10:00",
        "end_time": "11:30",
        "badge": "Лекция",
        "room": "Ауд. 402 / Онлайн",
        "description": "Изучение реляционных баз данных и нормализации форм."
    }
    lesson_dlg = AddLessonDialog(existing_event=lesson_data)
    lesson_dlg.show()
    app.processEvents()

    pixmap_dlg = lesson_dlg.grab()
    os.makedirs("assets", exist_ok=True)
    pixmap_dlg.save("assets/lesson_dialog_fixed.png", "PNG")
    lesson_dlg.close()

    # 2. Task Dialog
    task_data = {
        "title": "Подготовить отчет по лабораторной работе №3",
        "subject": "Физика",
        "due_date": "2026-10-25",
        "due_time": "23:59",
        "priority": "urgent"
    }
    task_dlg = TaskDialog(existing_task=task_data)
    task_dlg.show()
    app.processEvents()

    pixmap_task = task_dlg.grab()
    pixmap_task.save("assets/task_dialog_fixed.png", "PNG")
    task_dlg.close()

    print("Dialog screenshots saved to assets/lesson_dialog_fixed.png and assets/task_dialog_fixed.png")

if __name__ == "__main__":
    main()
