"""
Render high-res screenshot of WorkBOXig to visually verify the redesign.
"""

import sys
import os

# Do not force offscreen so GDI font engine renders crisp Cyrillic & emojis
if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from src.main_window import MainWindow

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    win = MainWindow()
    win.resize(1260, 820)
    win.show()
    
    # Switch to tasks view
    win._navigate_to("tasks")
    app.processEvents()

    pixmap = win.grab()
    pixmap.save("assets/tasks_preview.png", "PNG")

    # Capture notebooks view with embedded screenshot/diagram
    win._navigate_to("notebooks")
    app.processEvents()
    
    # Insert sample diagram into the current page if not already present
    from PyQt6.QtGui import QImage
    if os.path.exists("assets/sample_diagram.png"):
        img = QImage("assets/sample_diagram.png")
        if not img.isNull() and "<img" not in win.notebooks_view.rich_editor.editor.toHtml():
            win.notebooks_view.rich_editor.editor.insert_qimage(img)
            app.processEvents()

    pixmap_nb = win.grab()
    pixmap_nb.save("assets/notebooks_preview.png", "PNG")

    # Capture notes view
    win._navigate_to("notes")
    app.processEvents()
    pixmap_notes = win.grab()
    pixmap_notes.save("assets/notes_preview.png", "PNG")

    # Capture dashboard view
    win._navigate_to("dashboard")
    app.processEvents()
    pixmap_dash = win.grab()
    pixmap_dash.save("assets/dashboard_preview.png", "PNG")

    # Capture collapsed sidebar mode (icon-only mode)
    win.sidebar.toggle_collapse(animated=False)
    app.processEvents()
    pixmap_collapsed = win.grab()
    pixmap_collapsed.save("assets/dashboard_collapsed_preview.png", "PNG")

    # Re-expand for subsequent captures
    win.sidebar.toggle_collapse(animated=False)
    app.processEvents()

    # Capture calendar view
    win._navigate_to("calendar")
    app.processEvents()
    pixmap_cal = win.grab()
    pixmap_cal.save("assets/calendar_preview.png", "PNG")

    # Capture Settings view (Dark Mode)
    win._navigate_to("settings")
    app.processEvents()
    pixmap_settings = win.grab()
    pixmap_settings.save("assets/settings_preview.png", "PNG")

    # Switch to Light Mode and capture Light Mode views
    win._apply_theme("light")
    app.processEvents()

    # Capture Settings in Light Mode
    pixmap_set_light = win.grab()
    pixmap_set_light.save("assets/settings_light_preview.png", "PNG")

    # Capture Dashboard in Light Mode
    win._navigate_to("dashboard")
    app.processEvents()
    pixmap_dash_light = win.grab()
    pixmap_dash_light.save("assets/light_dashboard_preview.png", "PNG")

    # Capture Calendar in Light Mode
    win._navigate_to("calendar")
    app.processEvents()
    pixmap_cal_light = win.grab()
    pixmap_cal_light.save("assets/light_calendar_preview.png", "PNG")

    # Switch to Cyberpunk Mode and capture views
    win._apply_theme("cyberpunk")
    win._navigate_to("dashboard")
    app.processEvents()
    pixmap_dash_cyber = win.grab()
    pixmap_dash_cyber.save("assets/cyberpunk_dashboard_preview.png", "PNG")

    win._navigate_to("calendar")
    app.processEvents()
    pixmap_cal_cyber = win.grab()
    pixmap_cal_cyber.save("assets/cyberpunk_calendar_preview.png", "PNG")

    win._navigate_to("settings")
    app.processEvents()
    pixmap_set_cyber = win.grab()
    pixmap_set_cyber.save("assets/cyberpunk_settings_preview.png", "PNG")

    # Revert back to Dark Mode default
    win._apply_theme("dark")
    app.processEvents()

    win.close()
    print("Screenshots saved successfully!")

if __name__ == "__main__":
    main()
