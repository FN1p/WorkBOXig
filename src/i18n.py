"""
Internationalization (i18n) Engine for WorkBOXig.
Supports seamless switching between Russian and English with reactive Qt signals.
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        # App & Brand
        "app_title": "WorkBOXig — Рабочая станция и учёба",
        "app_subtitle": "Executive Work & Study OS",
        "workspace_personal": "Личное пространство",
        "workspace_local": "Локально",
        "sections": "РАЗДЕЛЫ",
        
        # Navigation
        "nav_dashboard": "Дашборд",
        "nav_calendar": "Календарь",
        "nav_notebooks": "Тетради",
        "nav_notes": "Заметки",
        "nav_tasks": "Задачи и ДЗ",
        "nav_settings": "Настройки",
        "collapse_sidebar": "Свернуть / развернуть меню (Ctrl+B)",
        
        # Topbar & Quick Actions
        "search_placeholder": "  Поиск или команда...   Ctrl+K",
        "streak_format": "{count} дн. ударного режима",
        "quick_add": "Быстрое добавление",
        "add_task_menu": "Новая задача...",
        "add_note_menu": "Новая заметка...",
        "add_event_menu": "Новое занятие в расписание...",
        
        # Dashboard
        "dashboard_title": "Дашборд продуктивности",
        "dashboard_subtitle": "Обзор ваших задач, расписания и метрик фокуса на сегодня",
        "metric_streak": "Ударный режим",
        "metric_streak_sub": "Дней непрерывного обучения",
        "metric_tasks": "Активные задачи",
        "metric_tasks_sub": "Осталось на сегодня",
        "metric_classes": "Занятия сегодня",
        "metric_classes_sub": "В вашем расписании",
        "metric_notes": "Конспекты и заметки",
        "metric_notes_sub": "В локальном хранилище",
        "section_today_schedule": "Расписание на сегодня",
        "section_urgent_tasks": "Горящие задачи и дедлайны",
        "section_quick_note": "Быстрая мысль",
        "quick_note_placeholder": "Запишите формулу, мысль или идею (Ctrl+Enter для сохранения)...",
        "quick_note_save": "Сохранить мысль",
        "no_classes_today": "На сегодня занятий нет. Отличный день для саморазвития!",
        "no_tasks_today": "Все задачи выполнены! Отличная работа.",
        "start_focus_btn": "Начать фокус-сессию",
        "add_task_btn": "Добавить задачу",
        "add_class_btn": "Добавить пару",
        "view_all_schedule": "Все расписание →",
        "view_all_tasks": "Все задачи →",
        
        # Calendar
        "calendar_title": "Календарь и расписание",
        "calendar_subtitle": "Интерактивная сетка занятий с индикатором реального времени",
        "export_ics": "Экспорт в .ics",
        "today_btn": "Сегодня",
        "view_week": "Неделя",
        "view_month": "Месяц",
        "btn_add_event": "+ Добавить занятие",
        "dialog_event_title": "Новое занятие / событие",
        "day_mon": "Понедельник",
        "day_tue": "Вторник",
        "day_wed": "Среда",
        "day_thu": "Четверг",
        "day_fri": "Пятница",
        "day_sat": "Суббота",
        "day_sun": "Воскресенье",
        
        # Notebooks
        "notebooks_title": "Тетради и предметы",
        "notebooks_subtitle": "Структурированные конспекты по предметам и проектам",
        "btn_new_notebook": "+ Новый предмет / тетрадь",
        "btn_new_page": "+ Новая страница",
        "no_notebooks": "Создайте свою первую тетрадь для записи лекций и конспектов",
        "untitled_page": "Новая страница",
        
        # Notes
        "notes_title": "Быстрые заметки",
        "notes_subtitle": "Моментальные идеи, чек-листы и памятки",
        "btn_new_note": "+ Создать заметку",
        "search_notes": "Поиск заметок...",
        "no_notes": "Нет заметок. Нажмите «+ Создать заметку», чтобы зафиксировать идею.",
        "note_placeholder": "Текст заметки...",
        "note_title_placeholder": "Заголовок заметки...",
        
        # Tasks
        "tasks_title": "Задачи и домашние задания",
        "tasks_subtitle": "Управление приоритетами, дедлайнами и учебными проектами",
        "btn_new_task": "+ Добавить задачу",
        "filter_all": "Все задачи",
        "filter_active": "В процессе",
        "filter_completed": "Завершённые",
        "priority_high": "Срочно / Высокий",
        "priority_medium": "Средний",
        "priority_low": "Низкий",
        "no_tasks": "Список задач пуст. Добавьте первую задачу!",
        "task_title_placeholder": "Что нужно сделать?",
        "task_subject_placeholder": "Предмет или тег (напр. Вышмат)",
        "task_due_date": "Срок выполнения",
        
        # Settings
        "settings_title": "Настройки",
        "settings_subtitle": "Управление языком, внешним видом, автозапуском Windows и резервными копиями",
        "card_language": "Язык интерфейса / Interface Language",
        "card_language_sub": "Выберите язык приложения / Select interface language",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "card_appearance": "Внешний вид и тема",
        "card_appearance_sub": "Выберите цветовую схему рабочего пространства",
        "theme_dark": "Тёмная (Dark Slate)",
        "theme_light": "Светлая (Light Clean)",
        "theme_cyber": "Cyberpunk Neon (Edgerunner)",
        "card_autostart": "Интеграция с Windows",
        "card_autostart_sub": "Автоматический запуск программы при входе в систему",
        "autostart_cb": "Запускать WorkBOXig автоматически при старте Windows",
        "autostart_active": "● АВТОЗАПУСК АКТИВЕН",
        "autostart_disabled": "○ ОТКЛЮЧЕНО",
        "card_focus": "Фокус и таймер Pomodoro",
        "card_focus_sub": "Звуковые оповещения и интервалы продуктивности",
        "sound_alert_cb": "Звуковой сигнал (Windows Beep) при завершении таймера",
        "focus_duration_lbl": "Длительность фокуса:",
        "break_duration_lbl": "Длительность отдыха:",
        "card_notifications": "Всплывающие уведомления",
        "card_notifications_sub": "Напоминания о начале занятий, дедлайнах и таймере фокуса",
        "notif_lessons_cb": "Напоминать о занятиях за 15 минут до начала",
        "notif_tasks_cb": "Оповещать о дедлайнах срочных задач",
        "test_notif_btn": "Проверить уведомление",
        "card_data": "Резервное копирование и данные",
        "card_data_sub": "Сохранение и перенос всех конспектов, расписания и заметок",
        "export_btn": "Экспорт всех данных (.json)",
        "import_btn": "Импорт из бэкапа (.json)",
        "open_folder_btn": "Открыть папку данных в проводнике",
        "card_about": "О программе WorkBOXig",
        "card_about_sub": "Версия и статус локального хранилища",
        "about_privacy": "● 100% локальное хранение данных. Без телеметрии, облачных трекеров и рекламы.",
        
        # Command Palette
        "palette_placeholder": "Поиск разделов, задач, заметок или команд...",
        "palette_category_nav": "Навигация",
        "palette_category_theme": "Темы оформления",
        "palette_category_actions": "Действия",
        
        # Pomodoro
        "pomo_focus": "ФОКУС",
        "pomo_break": "ОТДЫХ",
        "pomo_zen": "Zen Mode (Ctrl+T)",
        
        # Generic & Alerts
        "save": "Сохранить",
        "cancel": "Отмена",
        "delete": "Удалить",
        "edit": "Редактировать",
        "copied": "Скопировано",
        "success": "Успешно",
        "backup_exported": "Резервная копия успешно сохранена",
        "backup_imported": "Данные успешно восстановлены из копии",
    },
    "en": {
        # App & Brand
        "app_title": "WorkBOXig — Executive Work & Study OS",
        "app_subtitle": "Executive Work & Study OS",
        "workspace_personal": "Personal Workspace",
        "workspace_local": "Local Storage",
        "sections": "SECTIONS",
        
        # Navigation
        "nav_dashboard": "Dashboard",
        "nav_calendar": "Calendar",
        "nav_notebooks": "Notebooks",
        "nav_notes": "Notes",
        "nav_tasks": "Tasks & HW",
        "nav_settings": "Settings",
        "collapse_sidebar": "Collapse / Expand Menu (Ctrl+B)",
        
        # Topbar & Quick Actions
        "search_placeholder": "  Search or command...   Ctrl+K",
        "streak_format": "{count}-day study streak",
        "quick_add": "Quick Add",
        "add_task_menu": "New task...",
        "add_note_menu": "New note...",
        "add_event_menu": "New class / event...",
        
        # Dashboard
        "dashboard_title": "Productivity Dashboard",
        "dashboard_subtitle": "Overview of your tasks, schedule, and focus metrics for today",
        "metric_streak": "Daily Streak",
        "metric_streak_sub": "Days of focused work",
        "metric_tasks": "Active Tasks",
        "metric_tasks_sub": "Remaining today",
        "metric_classes": "Classes Today",
        "metric_classes_sub": "In your schedule",
        "metric_notes": "Notebooks & Notes",
        "metric_notes_sub": "In local offline storage",
        "section_today_schedule": "Today's Schedule",
        "section_urgent_tasks": "Urgent Tasks & Deadlines",
        "section_quick_note": "Quick Thought",
        "quick_note_placeholder": "Jot down a formula, idea, or reminder (Ctrl+Enter to save)...",
        "quick_note_save": "Save Thought",
        "no_classes_today": "No classes scheduled for today. Great day to focus!",
        "no_tasks_today": "All tasks completed! Excellent work.",
        "start_focus_btn": "Start Focus Session",
        "add_task_btn": "Add Task",
        "add_class_btn": "Add Class",
        "view_all_schedule": "View Full Schedule →",
        "view_all_tasks": "View All Tasks →",
        
        # Calendar
        "calendar_title": "Calendar & Schedule",
        "calendar_subtitle": "Interactive timetable grid with real-time live indicator",
        "export_ics": "Export to .ics",
        "today_btn": "Today",
        "view_week": "Week",
        "view_month": "Month",
        "btn_add_event": "+ Add Class / Event",
        "dialog_event_title": "New Class / Event",
        "day_mon": "Monday",
        "day_tue": "Tuesday",
        "day_wed": "Wednesday",
        "day_thu": "Thursday",
        "day_fri": "Friday",
        "day_sat": "Saturday",
        "day_sun": "Sunday",
        
        # Notebooks
        "notebooks_title": "Notebooks & Subjects",
        "notebooks_subtitle": "Hierarchical lecture notes, courses, and documentation",
        "btn_new_notebook": "+ New Notebook / Subject",
        "btn_new_page": "+ New Page",
        "no_notebooks": "Create your first notebook to organize lectures and ideas.",
        "untitled_page": "Untitled Page",
        
        # Notes
        "notes_title": "Quick Notes",
        "notes_subtitle": "Instant scratchpad, snippets, and fast reminders",
        "btn_new_note": "+ New Note",
        "search_notes": "Search notes...",
        "no_notes": "No notes yet. Click «+ New Note» to capture an idea.",
        "note_placeholder": "Note content...",
        "note_title_placeholder": "Note title...",
        
        # Tasks
        "tasks_title": "Tasks & Homework",
        "tasks_subtitle": "Manage priorities, deadlines, and academic assignments",
        "btn_new_task": "+ Add Task",
        "filter_all": "All Tasks",
        "filter_active": "In Progress",
        "filter_completed": "Completed",
        "priority_high": "Urgent / High",
        "priority_medium": "Medium",
        "priority_low": "Low",
        "no_tasks": "No tasks in this view. Enjoy your free time!",
        "task_title_placeholder": "What needs to be done?",
        "task_subject_placeholder": "Subject or tag (e.g. Calculus)",
        "task_due_date": "Due Date",
        
        # Settings
        "settings_title": "Settings",
        "settings_subtitle": "Manage language, appearance, Windows autostart, and local backups",
        "card_language": "Interface Language / Язык интерфейса",
        "card_language_sub": "Select interface language / Выберите язык приложения",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "card_appearance": "Appearance & Theme",
        "card_appearance_sub": "Select workspace color scheme and visual styling",
        "theme_dark": "Dark (Slate Mode)",
        "theme_light": "Light (Clean Studio)",
        "theme_cyber": "Cyberpunk Neon (Edgerunner)",
        "card_autostart": "Windows Integration",
        "card_autostart_sub": "Launch WorkBOXig automatically when logging into Windows",
        "autostart_cb": "Start WorkBOXig automatically on Windows boot",
        "autostart_active": "● AUTOSTART ENABLED",
        "autostart_disabled": "○ DISABLED",
        "card_focus": "Focus & Pomodoro Timer",
        "card_focus_sub": "Interval durations and sound alert preferences",
        "sound_alert_cb": "Play alert sound (Windows Beep) on interval completion",
        "focus_duration_lbl": "Focus Duration:",
        "break_duration_lbl": "Break Duration:",
        "card_notifications": "Desktop Notifications",
        "card_notifications_sub": "Upcoming class reminders, deadline alerts, and timer toasts",
        "notif_lessons_cb": "Remind about classes 15 minutes before start",
        "notif_tasks_cb": "Notify about urgent task deadlines",
        "test_notif_btn": "Test Notification",
        "card_data": "Data & Local Backups",
        "card_data_sub": "Export, import, and backup all your notes, schedules, and tasks",
        "export_btn": "Export All Data (.json)",
        "import_btn": "Import from Backup (.json)",
        "open_folder_btn": "Open Data Folder in Explorer",
        "card_about": "About WorkBOXig",
        "card_about_sub": "Version, engine, and local storage status",
        "about_privacy": "● 100% offline local storage. No telemetry, no cloud trackers, no ads.",
        
        # Command Palette
        "palette_placeholder": "Type a command or search tasks, notes, courses...",
        "palette_category_nav": "Navigation",
        "palette_category_theme": "Appearance Themes",
        "palette_category_actions": "Quick Actions",
        
        # Pomodoro
        "pomo_focus": "FOCUS",
        "pomo_break": "BREAK",
        "pomo_zen": "Zen Mode (Ctrl+T)",
        
        # Generic & Alerts
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "copied": "Copied to clipboard",
        "success": "Success",
        "backup_exported": "Backup exported successfully",
        "backup_imported": "Data restored from backup successfully",
    }
}


class I18nManager(QObject):
    """Singleton language manager emitting signals upon language changes."""
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_lang = "ru"

    @property
    def current_language(self) -> str:
        return self._current_lang

    def set_language(self, lang: str):
        if lang not in TRANSLATIONS:
            lang = "ru"
        if self._current_lang != lang:
            self._current_lang = lang
            self.language_changed.emit(lang)

    def t(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["ru"])
        val = lang_dict.get(key)
        if val is None:
            val = TRANSLATIONS["en"].get(key, TRANSLATIONS["ru"].get(key, default or key))
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return val


_i18n_instance: Optional[I18nManager] = None

def get_i18n() -> I18nManager:
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    return _i18n_instance

def t(key: str, default: Optional[str] = None, **kwargs) -> str:
    return get_i18n().t(key, default, **kwargs)

def get_language() -> str:
    return get_i18n().current_language

def set_language(lang: str):
    get_i18n().set_language(lang)


def format_lessons(n: int) -> str:
    lang = get_language()
    if lang == "en":
        return f"{n} class" if n == 1 else f"{n} classes"
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} урок"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} урока"
    return f"{n} уроков"


def format_tasks(n: int) -> str:
    lang = get_language()
    if lang == "en":
        return f"{n} task" if n == 1 else f"{n} tasks"
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} задача"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} задачи"
    return f"{n} задач"


def format_days(n: int) -> str:
    lang = get_language()
    if lang == "en":
        return f"{n} day" if n == 1 else f"{n} days"
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} день"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} дня"
    return f"{n} дней"
