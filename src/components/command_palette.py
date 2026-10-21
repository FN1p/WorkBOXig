"""
Command Palette (Ctrl+K) for WorkBOXig.
Raycast / Spotlight-style universal search and quick command launcher.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame, QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QKeyEvent
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon


class CommandItemWidget(QWidget):
    """Custom item for Command Palette results."""
    def __init__(self, category: str, title: str, subtitle: str = "", badge: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Category icon/badge
        cat_icons = {
            "action": ("zap", COLORS['amber']),
            "task": ("tasks", COLORS['emerald']),
            "notebook": ("notebooks", COLORS['primary_light']),
            "page": ("file_text", COLORS['sky']),
            "note": ("notes", COLORS['purple']),
            "nav": ("command", COLORS['sky']),
        }
        icon_name, col = cat_icons.get(category, ("search", COLORS['primary_light']))

        cat_lbl = QLabel()
        cat_lbl.setPixmap(get_pixmap(icon_name, col, 16))
        cat_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(cat_lbl)

        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        text_layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setFont(QFont("Segoe UI", 8))
            sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            text_layout.addWidget(sub_lbl)

        layout.addLayout(text_layout, stretch=1)

        # Badge pill if present
        if badge:
            badge_lbl = QLabel(badge)
            badge_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            badge_lbl.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                color: {col};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 2px 7px;
            """)
            layout.addWidget(badge_lbl)


class CommandPalette(QDialog):
    """Universal search and command runner."""
    action_triggered = pyqtSignal(str, dict) # action_type, payload

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 440)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # Card container with glass/card styling and drop shadow
        self.card = QFrame()
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #131722;
                border: 1px solid {COLORS['border_light']};
                border-radius: 14px;
            }}
        """)
        
        # Soft shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 16, 16, 14)
        card_layout.setSpacing(10)

        # Top search bar
        search_box = QHBoxLayout()
        search_box.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("search", COLORS['text_muted'], 16))
        icon_lbl.setStyleSheet("background: transparent;")
        search_box.addWidget(icon_lbl)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Поиск задач, конспектов, заметок или команд...")
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                padding: 4px 0px;
            }}
        """)
        self.input_field.textChanged.connect(self._on_search_changed)
        search_box.addWidget(self.input_field, stretch=1)

        esc_hint = QLabel("ESC чтобы закрыть")
        esc_hint.setFont(QFont("Segoe UI", 8))
        esc_hint.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            background-color: {COLORS['bg_input']};
            border: 1px solid {COLORS['border_subtle']};
            border-radius: 4px;
            padding: 2px 6px;
        """)
        search_box.addWidget(esc_hint)
        card_layout.addLayout(search_box)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {COLORS['border_subtle']}; margin: 2px 0;")
        card_layout.addWidget(div)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
            }}
            QListWidget::item {{
                border-radius: 8px;
                margin-bottom: 3px;
                padding: 0px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['bg_card_selected']};
                border: 1px solid {COLORS['primary_border']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_card_hover']};
            }}
        """)
        self.results_list.itemActivated.connect(self._on_item_activated)
        card_layout.addWidget(self.results_list, stretch=1)

        # Bottom hint bar
        footer_layout = QHBoxLayout()
        hint = QLabel("↑↓ для выбора • Enter для перехода • Tab для переключения")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet(f"color: {COLORS['text_muted']};")
        footer_layout.addWidget(hint)
        footer_layout.addStretch()

        brand_lbl = QLabel("WorkBOXig Spotlight")
        brand_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        brand_lbl.setStyleSheet(f"color: {COLORS['primary_light']};")
        footer_layout.addWidget(brand_lbl)
        card_layout.addLayout(footer_layout)

        main_layout.addWidget(self.card)

        self._populate_results("")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            curr = self.results_list.currentRow()
            if curr < self.results_list.count() - 1:
                self.results_list.setCurrentRow(curr + 1)
        elif event.key() == Qt.Key.Key_Up:
            curr = self.results_list.currentRow()
            if curr > 0:
                self.results_list.setCurrentRow(curr - 1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr_item = self.results_list.currentItem()
            if curr_item:
                self._on_item_activated(curr_item)
        else:
            super().keyPressEvent(event)

    def _on_search_changed(self, text: str):
        self._populate_results(text.strip().lower())

    def _populate_results(self, query: str):
        self.results_list.clear()
        results = []

        # Standard navigation & actions
        static_actions = [
            {"cat": "action", "title": "Создать задачу или ДЗ", "sub": "Добавить новую задачу с дедлайном", "badge": "Действие", "type": "create_task", "data": {}},
            {"cat": "action", "title": "Создать быструю заметку", "sub": "Открыть чистый холст для записей", "badge": "Действие", "type": "create_note", "data": {}},
            {"cat": "action", "title": "Создать новую тетрадь", "sub": "Добавить предмет или модуль", "badge": "Действие", "type": "create_notebook", "data": {}},
            {"cat": "action", "title": "Запустить таймер фокуса", "sub": "Сессия продуктивности 25 минут", "badge": "Фокус", "type": "start_pomodoro", "data": {}},
            {"cat": "action", "title": "Переключить тему оформления", "sub": "Переключить между Dark, Light и Cyberpunk Neon", "badge": "Тема", "type": "toggle_theme", "data": {}},
            {"cat": "action", "title": "Тема: Cyberpunk Neon (Edgerunner)", "sub": "Неоновый высококонтрастный кибер-стиль", "badge": "Тема", "type": "set_theme", "data": {"theme": "cyberpunk"}},
            {"cat": "action", "title": "Тема: Тёмная (Dark Slate)", "sub": "Строгий современный тёмный интерфейс", "badge": "Тема", "type": "set_theme", "data": {"theme": "dark"}},
            {"cat": "action", "title": "Тема: Светлая (Light Clean)", "sub": "Чистый светлый интерфейс", "badge": "Тема", "type": "set_theme", "data": {"theme": "light"}},
            {"cat": "action", "title": "Экспорт расписания в iCalendar (.ics)", "sub": "Файл для Google, Apple и Яндекс Календаря", "badge": "Экспорт", "type": "export_calendar_ics", "data": {}},
            {"cat": "nav", "title": "Открыть Настройки", "sub": "Темы оформления, автозапуск Windows и бэкапы", "badge": "Навигация", "type": "navigate", "data": {"tab": "settings"}},
            {"cat": "nav", "title": "Открыть Календарь", "sub": "Перейти к сетке расписания и дедлайнов", "badge": "Навигация", "type": "navigate", "data": {"tab": "calendar"}},
            {"cat": "nav", "title": "Открыть Задачи и ДЗ", "sub": "Перейти к трекеру домашних заданий", "badge": "Навигация", "type": "navigate", "data": {"tab": "tasks"}},
            {"cat": "nav", "title": "Открыть Тетради и конспекты", "sub": "Перейти к конспектам лекций", "badge": "Навигация", "type": "navigate", "data": {"tab": "notebooks"}},
            {"cat": "nav", "title": "Открыть Заметки", "sub": "Перейти к быстрым мыслям", "badge": "Навигация", "type": "navigate", "data": {"tab": "notes"}},
            {"cat": "nav", "title": "Открыть Дашборд", "sub": "Обзор дня, метрики и расписание", "badge": "Навигация", "type": "navigate", "data": {"tab": "dashboard"}},
        ]

        # 1. Search Tasks
        for t in self.storage.get_tasks():
            t_title = t.get("title", "")
            t_sub = t.get("subject", "")
            if not query or query in t_title.lower() or query in t_sub.lower():
                status = "Выполнено" if t.get("completed") else f"До {t.get('due_date', '')}"
                results.append({
                    "cat": "task",
                    "title": t_title,
                    "sub": f"Предмет: {t_sub} • {status}",
                    "badge": "Задача",
                    "type": "open_task",
                    "data": {"task_id": t["id"]}
                })

        # 2. Search Notebooks & Pages
        for nb in self.storage.get_notebooks():
            nb_title = nb.get("title", "")
            if not query or query in nb_title.lower():
                results.append({
                    "cat": "notebook",
                    "title": f"Тетрадь: {nb_title}",
                    "sub": f"Страниц: {len(nb.get('pages', []))}",
                    "badge": "Тетрадь",
                    "type": "open_notebook",
                    "data": {"nb_id": nb["id"]}
                })
            for p in nb.get("pages", []):
                p_title = p.get("title", "")
                p_plain = p.get("content_plain", "")
                if query and (query in p_title.lower() or query in p_plain.lower()):
                    results.append({
                        "cat": "page",
                        "title": p_title or "Без названия",
                        "sub": f"В тетради: {nb_title}",
                        "badge": "Конспект",
                        "type": "open_page",
                        "data": {"nb_id": nb["id"], "page_id": p["id"]}
                    })

        # 3. Search Notes
        for n in self.storage.get_notes():
            n_title = n.get("title", "")
            n_body = n.get("content", "")
            if not query or query in n_title.lower() or query in n_body.lower():
                results.append({
                    "cat": "note",
                    "title": n_title or "Без названия",
                    "sub": n_body.replace("\n", " ")[:60],
                    "badge": "Заметка",
                    "type": "open_note",
                    "data": {"note_id": n["id"]}
                })

        # Add matching actions
        for act in static_actions:
            if not query or query in act["title"].lower() or query in act["sub"].lower():
                results.append(act)

        # Render list items
        for item_data in results[:18]:
            item = QListWidgetItem(self.results_list)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            widget = CommandItemWidget(
                category=item_data["cat"],
                title=item_data["title"],
                subtitle=item_data["sub"],
                badge=item_data["badge"]
            )
            item.setSizeHint(widget.sizeHint())
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_item_activated(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.action_triggered.emit(data["type"], data.get("data", {}))
            self.accept()
