<div align="center">

# 📦 WorkBOXig

### *Executive Work & Study OS for Windows*

<p>
  🇬🇧 <b>English</b> • <a href="README_RU.md">🇷🇺 <b>Русский</b></a>
</p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg?logo=windows&logoColor=white)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Windows checks](https://github.com/FN1p/WorkBOXig/actions/workflows/windows.yml/badge.svg)](https://github.com/FN1p/WorkBOXig/actions/workflows/windows.yml)

**WorkBOXig** is a modern, high-performance, and aesthetically crafted desktop workspace engineered for academics, projects, and personal productivity. Built with PyQt6, it unifies an interactive timetable with real-time tracking, hierarchical notebooks, an assignment and task manager, a Pomodoro focus suite with Zen mode, native Windows desktop alerts, bilingual localization (EN / RU), and a Raycast-style Spotlight Command Palette (`Ctrl+K`).

---

![WorkBOXig Cyberpunk Theme](assets/cyberpunk_dashboard_preview.png)

</div>

---

## ✨ Key Features

### 📊 Productivity Command Dashboard
- **Daily Executive Metrics**: Instant overview of today's classes, active assignments, urgent deadlines, and study streaks.
- **Quick Thought Scratchpad**: Rapid formula and idea capture with one-click storage right from the home screen (`Ctrl+Enter`).
- **Interactive Action Cards**: Launch Pomodoro focus intervals, register assignments, and jump directly to timetable events.

### 📅 Real-Time Interactive Timetable & Calendar
- **Live Minute-Accurate Time Indicator**: Neon timeline marker tracking the current hour and automatically scrolling into view.
- **RFC 5545 iCalendar (`.ics`) Export**: Seamless one-click sync with Google Calendar, Apple Calendar, and Microsoft Outlook.
- **Dual Perspective Views**: Switch between granular weekly timetable schedule and comprehensive monthly calendar grid.

### 📓 Structured Notebooks & Knowledge Base
- **Hierarchical Taxonomy**: Organize courses, modules, lectures, and sub-pages in an intuitive tree structure.
- **Rich-Text Canvas**: Formatted headers, styled lists, blockquotes, syntax-friendly styling, and color highlights.
- **Inline Image & Diagram Embedding**: Insert screenshots, formulas, and visual diagrams without layout degradation.

### ✅ Task & Assignment Tracker
- **Multi-Level Priority Matrix**: Categorize items as *Urgent/High*, *Medium*, or *Low* with visual glowing pills.
- **Smart Deadline Countdown**: Real-time calculation of remaining days and hours until submission.
- **Instant Filtering**: Filter by status (*All*, *In Progress*, *Completed*) or subject tags.
- **Quick Entry**: Type `Finish report @2026-10-28 !high` and press Enter to create a dated task.

### 💾 Portable Backups
- Export a `.workboxig` archive from Settings to include notebook images and data in one file.
- Importing an archive automatically saves the current state first. Older data-only `.json` backups remain importable.

### ⏱ Pomodoro Focus Engine & Zen Mode
- **Persistent Header Capsule**: Integrated 25-minute focus and 5-minute break timers.
- **Fullscreen Zen Mode (`Ctrl+T`)**: Minimalist distraction-free full-screen display for deep concentration sessions.
- **Auditory Notifications**: Configurable interval completion alerts.

### 🎨 3 Handcrafted Themes with Zero-Restart Switching
1. **Dark (Executive Slate)**: Minimalist, low-strain slate aesthetic inspired by Linear and Raycast.
2. **Light (Clean Studio)**: High-contrast daylight workspace crafted for bright office environments.
3. **Cyberpunk Neon (Edgerunner Anime Aesthetic)**:
   - **Procedural Vector Button Engine**: 45° chamfered cut corners, hazard warning diagonal slashes (`///`), Sandevistan Yellow (`#FCEE0A`) accents, and Cyber Cyan (`#00F0FF`) borders.
   - 100% original and legally clean vector geometry without third-party trademark infringement.

### 🌐 Bilingual Localization (EN / RU)
- Reactive language switching directly within Settings without restarting the application.
- Full native translation covering all menus, dialogs, formatting, and notifications.

### 🔔 Native Windows Desktop Notifications
- Modern glassmorphic desktop notification toasts positioned at the bottom-right of your screen.
- Automated reminders triggered 15 minutes before scheduled lectures and classes.
- Urgent deadline alerts for pending assignments due today.

### ⚡ Universal Spotlight (`Ctrl+K`)
- Instant fuzzy search traversing tasks, notebook pages, courses, and quick notes.
- Quick navigation, theme switching, and utility command triggers via keyboard.

---

## 📸 Screenshots Showcase

| Weekly Timetable (Cyberpunk HUD) | Theme & Preferences Settings |
| :---: | :---: |
| ![Calendar Cyberpunk](assets/cyberpunk_calendar_preview.png) | ![Settings Cyberpunk](assets/cyberpunk_settings_preview.png) |

| Slate Dark Mode | Clean Studio Light Mode |
| :---: | :---: |
| ![Dashboard Dark](assets/dashboard_preview.png) | ![Dashboard Light](assets/light_dashboard_preview.png) |

---

## 🚀 Quick Start

### System Requirements
- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: 3.10+ (only required if building or running from source)

### 1. Download Pre-Compiled Executables
Grab the latest standalone release from [GitHub Releases](https://github.com/FN1p/WorkBOXig/releases):
- 📥 **`WorkBOXig_Setup.exe`** (~82 MB): Graphical Windows Installer with desktop shortcuts, start menu integration, and optional Windows autostart.
- 🚀 **`WorkBOXig.exe`** (~40 MB): Zero-installation standalone portable executable.

### 2. Run from Source Code
```bash
# Clone the repository
git clone https://github.com/FN1p/WorkBOXig.git
cd WorkBOXig

# Create and activate a Python virtual environment
python -m venv venv
venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt

# Launch WorkBOXig
python main.py
```

---

## 🛠️ Building Standalone Binaries

The project includes pre-configured PyInstaller specs for compiling both the standalone executable and the setup installer:

```bash
# 1. Compile the portable standalone WorkBOXig.exe
pyinstaller WorkBOXig.spec --noconfirm

# 2. Compile the graphical setup installer WorkBOXig_Setup.exe
pyinstaller installer.spec --noconfirm
```

Compiled binaries will be generated inside the `dist/` directory.

---

## ⌨️ Global Keyboard Shortcuts

| Shortcut | Description |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>K</kbd> | Open Spotlight Command Palette (Global search & quick actions) |
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | Toggle Pomodoro Zen Mode (Distraction-free focus) |
| <kbd>Ctrl</kbd> + <kbd>B</kbd> | Toggle Sidebar (Expand / Collapse to icon-only mode) |
| <kbd>Ctrl</kbd> + <kbd>1</kbd> | Navigate to **Dashboard** |
| <kbd>Ctrl</kbd> + <kbd>2</kbd> | Navigate to **Calendar & Schedule** |
| <kbd>Ctrl</kbd> + <kbd>3</kbd> | Navigate to **Notebooks & Courses** |
| <kbd>Ctrl</kbd> + <kbd>4</kbd> | Navigate to **Quick Notes** |
| <kbd>Ctrl</kbd> + <kbd>5</kbd> | Navigate to **Tasks & Homework** |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Open **Settings** |
| <kbd>Ctrl</kbd> + <kbd>N</kbd> | Create a new Quick Note |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Trigger manual atomic flush to disk |

---

## 📁 Repository Structure

```
WorkBOXig/
├── assets/                 # High-resolution vector & raster icons, previews
├── src/
│   ├── components/         # Reusable UI widgets & engines
│   │   ├── command_palette.py      # Raycast-style Spotlight search (Ctrl+K)
│   │   ├── desktop_notification.py # Windows native desktop alert cards
│   │   ├── pomodoro.py             # Pomodoro focus timer & Zen Mode
│   │   ├── rich_editor.py          # Rich-text editor with inline image embedding
│   │   ├── sidebar.py              # Animated collapsible sidebar navigation
│   │   └── toast.py                # Subtle status toast alerts
│   ├── views/              # Primary application screens
│   │   ├── calendar_view.py        # Weekly timetable & iCalendar (.ics) export
│   │   ├── dashboard_view.py       # Executive overview dashboard & metrics
│   │   ├── notebooks_view.py       # Hierarchical notebooks & lecture canvas
│   │   ├── notes_view.py           # Instant scratchpad notes
│   │   ├── settings_view.py        # Language, themes, autostart & backups
│   │   └── tasks_view.py           # Assignment & task tracker
│   ├── utils/              # Operating system integration
│   │   ├── autostart.py            # Windows registry autostart manager
│   │   └── shortcuts.py            # Safe widget lifecycle & layout cleanup
│   ├── icons.py            # Procedural SVG vector icon generator
│   ├── i18n.py             # Dual-language internationalization engine (EN/RU)
│   ├── main_window.py      # Root application coordinator window
│   ├── storage.py          # Atomic JSON local persistence engine
│   ├── styles.py           # Modern Slate & Light Clean design systems
│   └── styles_cyber.py     # Edgerunners procedural anime HUD button painter
├── tests/                  # Automated test suite (25 unit tests)
├── installer.py            # Standalone GUI installer application source
├── WorkBOXig.spec          # Standalone app PyInstaller build specification
├── installer.spec          # Setup installer PyInstaller build specification
├── requirements.txt        # Python dependency manifest
├── README_RU.md            # Russian documentation
└── README.md               # English documentation
```

---

## 🧪 Automated Testing

WorkBOXig features automated unit and integration tests covering data serialization, UI layout lifecycle, calendar export, i18n formatting, and painter rendering:

```bash
python -m unittest discover -s tests -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — Copyright (c) 2026 **PFT Studio**.  
You are free to use, modify, distribute, and compile this software for personal or commercial purposes.
