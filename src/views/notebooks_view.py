"""
Notebooks (Тетради) View for WorkBOXig.
Multi-subject notebook organization system with comfortable, spacious rich-text editing.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFrame, QSplitter,
    QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QCursor
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.components.rich_editor import RichEditor


class NotebookItemWidget(QWidget):
    """Custom item in Notebooks column."""
    def __init__(self, title: str, color_hex: str, page_count: int, parent=None):
        super().__init__(parent)
        self.setToolTip(f"{title} ({page_count} {t('nb_pages_title').lower()})")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Color indicator dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color_hex}; font-size: 14px; background: transparent;")
        layout.addWidget(dot)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        title_lbl.setObjectName("notebook_item_title")
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl, stretch=1)

        # Count badge
        count_lbl = QLabel(str(page_count))
        count_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        count_lbl.setStyleSheet(f"""
            background-color: {COLORS['bg_card_hover']};
            color: {COLORS['text_muted']};
            border-radius: 8px;
            padding: 2px 7px;
        """)
        layout.addWidget(count_lbl)


class PageItemWidget(QWidget):
    """Custom item in Pages column."""
    def __init__(self, title: str, snippet: str, date_str: str, parent=None):
        super().__init__(parent)
        self.setToolTip(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title_lbl = QLabel(title or t("untitled_page"))
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        title_lbl.setObjectName("notebook_item_title")
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl)

        if snippet:
            # Clean snippet from potential html tags
            clean_snip = snippet.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "").strip()
            clean_snip = clean_snip[:60] + ("..." if len(clean_snip) > 60 else "")
            snip_lbl = QLabel(clean_snip)
            snip_lbl.setFont(QFont("Segoe UI", 8))
            snip_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            layout.addWidget(snip_lbl)

        time_lbl = QLabel(date_str)
        time_lbl.setFont(QFont("Segoe UI", 8))
        time_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(time_lbl)


class NotebooksView(QWidget):
    """
    Notebooks and Rich Page Editing Hub.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.current_nb_id = None
        self.current_page_id = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Master Splitter: [Notebooks List] | [Pages List] | [Editor Canvas]
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border_subtle']};
                width: 1px;
            }}
        """)
        self.is_focus_fullscreen = False

        # ---------------- Column 1: Subjects/Notebooks ----------------
        self.nb_col = QFrame()
        self.nb_col.setObjectName("notebooks_column")
        self.nb_col.setStyleSheet(f"QFrame#notebooks_column {{ background-color: {COLORS['bg_sidebar']}; }}")
        nb_col_layout = QVBoxLayout(self.nb_col)
        nb_col_layout.setContentsMargins(14, 18, 14, 16)
        nb_col_layout.setSpacing(12)

        nb_header = QHBoxLayout()
        nb_title = QLabel(t("nb_col_title"))
        nb_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        nb_header.addWidget(nb_title)
        nb_header.addStretch()

        add_nb_btn = QPushButton(t("nb_add_btn"))
        add_nb_btn.setIcon(get_icon("plus", "#FFFFFF", 16))
        add_nb_btn.setIconSize(QSize(16, 16))
        add_nb_btn.setToolTip(t("nb_add_tooltip"))
        add_nb_btn.setObjectName("primary-btn")
        add_nb_btn.setFixedHeight(32)
        add_nb_btn.clicked.connect(self._create_notebook)
        nb_header.addWidget(add_nb_btn)
        nb_col_layout.addLayout(nb_header)

        self.nb_list_widget = QListWidget()
        self.nb_list_widget.currentRowChanged.connect(self._on_notebook_selected)
        self.nb_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.nb_list_widget.customContextMenuRequested.connect(self._show_nb_context_menu)
        nb_col_layout.addWidget(self.nb_list_widget)

        self.splitter.addWidget(self.nb_col)

        # ---------------- Column 2: Pages in Notebook ----------------
        self.pages_col = QFrame()
        self.pages_col.setObjectName("pages_column")
        self.pages_col.setStyleSheet(f"QFrame#pages_column {{ background-color: {COLORS['bg_root']}; border-right: 1px solid {COLORS['border_subtle']}; }}")
        pages_col_layout = QVBoxLayout(self.pages_col)
        pages_col_layout.setContentsMargins(14, 18, 14, 16)
        pages_col_layout.setSpacing(12)

        pages_header = QHBoxLayout()
        self.pages_col_title = QLabel(t("nb_pages_title"))
        self.pages_col_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        pages_header.addWidget(self.pages_col_title)
        pages_header.addStretch()

        self.add_page_btn = QPushButton(t("nb_add_page_btn"))
        self.add_page_btn.setIcon(get_icon("plus", "#FFFFFF", 16))
        self.add_page_btn.setIconSize(QSize(16, 16))
        self.add_page_btn.setObjectName("primary-btn")
        self.add_page_btn.setFixedHeight(32)
        self.add_page_btn.clicked.connect(self._create_page)
        pages_header.addWidget(self.add_page_btn)
        pages_col_layout.addLayout(pages_header)

        # Search bar for pages
        self.page_search_input = QLineEdit()
        self.page_search_input.setPlaceholderText(t("nb_search_pages"))
        self.page_search_input.textChanged.connect(self._filter_pages)
        pages_col_layout.addWidget(self.page_search_input)

        self.pages_list_widget = QListWidget()
        self.pages_list_widget.currentRowChanged.connect(self._on_page_selected)
        self.pages_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pages_list_widget.customContextMenuRequested.connect(self._show_page_context_menu)
        pages_col_layout.addWidget(self.pages_list_widget)

        self.splitter.addWidget(self.pages_col)

        # ---------------- Column 3: Editor Canvas ----------------
        self.editor_container = QFrame()
        self.editor_container.setObjectName("notebook_editor_container")
        self.editor_container.setStyleSheet(f"QFrame#notebook_editor_container {{ background-color: {COLORS['bg_root']}; }}")
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.rich_editor = RichEditor()
        self.rich_editor.content_changed.connect(self._on_editor_content_changed)
        self.rich_editor.focus_mode_toggled.connect(self._toggle_focus_mode)
        editor_layout.addWidget(self.rich_editor)

        self.splitter.addWidget(self.editor_container)

        self.nb_col.setMinimumWidth(210)
        self.pages_col.setMinimumWidth(240)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setCollapsible(2, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)

        main_layout.addWidget(self.splitter)
        self.splitter.setSizes([220, 260, 560])

        # Storage signal connection
        self.storage.data_changed.connect(self._on_storage_changed)
        self.storage.save_completed.connect(self.rich_editor.mark_saved)

        self._refresh_notebooks_list()

    def showEvent(self, event):
        super().showEvent(event)
        self.splitter.setSizes([220, 260, 560])

    def _refresh_notebooks_list(self):
        self.nb_list_widget.clear()
        notebooks = self.storage.get_notebooks()
        
        if not notebooks:
            self.current_nb_id = None
            self.pages_col_title.setText(t("nb_pages_title"))
            self.add_page_btn.setEnabled(False)
            self.pages_list_widget.clear()
            self.rich_editor.show_empty()
            return

        self.add_page_btn.setEnabled(True)
        target_row = 0
        for i, nb in enumerate(notebooks):
            item = QListWidgetItem(self.nb_list_widget)
            widget = NotebookItemWidget(
                title=nb.get("title", ""),
                color_hex=nb.get("color", "#6366F1"),
                page_count=len(nb.get("pages", []))
            )
            item.setSizeHint(QSize(210, 48))
            self.nb_list_widget.addItem(item)
            self.nb_list_widget.setItemWidget(item, widget)

            if nb.get("id") == self.current_nb_id:
                target_row = i

        if notebooks and self.nb_list_widget.count() > 0:
            self.nb_list_widget.setCurrentRow(target_row)

    def _on_notebook_selected(self, row: int):
        notebooks = self.storage.get_notebooks()
        if 0 <= row < len(notebooks):
            nb = notebooks[row]
            self.current_nb_id = nb["id"]
            self.pages_col_title.setText(nb.get("title", t("nb_pages_title")))
            self._refresh_pages_list()
        else:
            self.current_nb_id = None
            self.pages_list_widget.clear()
            self.rich_editor.show_empty()

    def _refresh_pages_list(self):
        self.pages_list_widget.clear()
        if not self.current_nb_id:
            self.rich_editor.show_empty()
            return

        nb = next((n for n in self.storage.get_notebooks() if n["id"] == self.current_nb_id), None)
        if not nb:
            self.rich_editor.show_empty()
            return

        pages = nb.get("pages", [])
        query = self.page_search_input.text().lower().strip()

        target_row = 0
        found_target = False

        for i, page in enumerate(pages):
            title = page.get("title", "")
            plain = page.get("content_plain", "")
            if query and query not in title.lower() and query not in plain.lower():
                continue

            date_str = page.get("updated_at", "")[:10]
            item = QListWidgetItem(self.pages_list_widget)
            item.setData(Qt.ItemDataRole.UserRole, page["id"])
            widget = PageItemWidget(title, plain, date_str)
            item.setSizeHint(QSize(240, 72))
            self.pages_list_widget.addItem(item)
            self.pages_list_widget.setItemWidget(item, widget)

            if page["id"] == self.current_page_id:
                target_row = self.pages_list_widget.count() - 1
                found_target = True

        if self.pages_list_widget.count() > 0:
            self.pages_list_widget.setCurrentRow(target_row if found_target else 0)
        else:
            self.current_page_id = None
            self.rich_editor.show_empty()

    def _filter_pages(self):
        self._refresh_pages_list()

    def _on_page_selected(self, row: int):
        if row < 0:
            return
        item = self.pages_list_widget.item(row)
        if not item:
            return
        page_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_page_id = page_id

        nb = next((n for n in self.storage.get_notebooks() if n["id"] == self.current_nb_id), None)
        if nb:
            page = next((p for p in nb.get("pages", []) if p["id"] == page_id), None)
            if page:
                self.rich_editor.set_content(page_id, page.get("title", ""), page.get("content_html", ""))
            else:
                self.rich_editor.show_empty()

    def _on_editor_content_changed(self, title: str, html: str, plain: str):
        if self.current_nb_id and self.current_page_id:
            self.storage.update_page(
                nb_id=self.current_nb_id,
                page_id=self.current_page_id,
                title=title,
                content_html=html,
                content_plain=plain
            )
            # Update the page item title in list
            row = self.pages_list_widget.currentRow()
            if row >= 0:
                item = self.pages_list_widget.item(row)
                if item:
                    widget = self.pages_list_widget.itemWidget(item)
                    if isinstance(widget, PageItemWidget):
                        widget.findChild(QLabel).setText(title or t("untitled_page"))

    def _create_notebook(self):
        title, ok = QInputDialog.getText(self, t("nb_dialog_new_title"), t("nb_dialog_new_prompt"))
        if ok and title.strip():
            colors = ["#6366F1", "#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6"]
            color = colors[len(self.storage.get_notebooks()) % len(colors)]
            nb = self.storage.add_notebook(title.strip(), color=color)
            self.current_nb_id = nb["id"]
            self._refresh_notebooks_list()

    def _create_page(self):
        if not self.current_nb_id:
            return
        page = self.storage.add_page(self.current_nb_id, title=t("nb_page_default_title"), content_html="<p></p>")
        if page:
            self.current_page_id = page["id"]
            self._refresh_pages_list()
            self._refresh_notebooks_list()

    def _show_nb_context_menu(self, pos):
        item = self.nb_list_widget.itemAt(pos)
        if not item:
            return
        row = self.nb_list_widget.row(item)
        notebooks = self.storage.get_notebooks()
        if not (0 <= row < len(notebooks)):
            return
        nb = notebooks[row]

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 14px;
                border-radius: 4px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_subtle']};
                color: {COLORS['primary_light']};
            }}
        """)

        rename_act = menu.addAction(get_icon("edit", COLORS['text_primary'], 16), t("nb_rename"))
        delete_act = menu.addAction(get_icon("trash", "#F87171", 16), t("nb_delete"))

        action = menu.exec(self.nb_list_widget.mapToGlobal(pos))
        if action == rename_act:
            new_title, ok = QInputDialog.getText(self, t("nb_rename_title"), t("nb_new_name"), text=nb.get("title", ""))
            if ok and new_title.strip():
                self.storage.update_notebook(nb["id"], title=new_title.strip())
                self._refresh_notebooks_list()
        elif action == delete_act:
            if QMessageBox.question(self, t("nb_delete_confirm_title"), t("nb_delete_confirm_msg", title=nb.get("title"))) == QMessageBox.StandardButton.Yes:
                self.storage.delete_notebook(nb["id"])
                self.current_nb_id = None
                self._refresh_notebooks_list()

    def _show_page_context_menu(self, pos):
        item = self.pages_list_widget.itemAt(pos)
        if not item:
            return
        page_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 14px;
                border-radius: 4px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_subtle']};
                color: {COLORS['primary_light']};
            }}
        """)
        del_act = menu.addAction(get_icon("trash", "#F87171", 16), t("nb_del_page"))
        action = menu.exec(self.pages_list_widget.mapToGlobal(pos))
        if action == del_act:
            if self.current_nb_id and page_id:
                self.storage.delete_page(self.current_nb_id, page_id)
                self.current_page_id = None
                self._refresh_pages_list()
                self._refresh_notebooks_list()

    def _toggle_focus_mode(self):
        self.is_focus_fullscreen = not self.is_focus_fullscreen
        if self.is_focus_fullscreen:
            self._saved_splitter_sizes = self.splitter.sizes()
            self.splitter.setSizes([0, 0, 1000])
        else:
            self.splitter.setSizes(getattr(self, "_saved_splitter_sizes", [210, 250, 620]))

    def select_page(self, nb_id: str, page_id: str):
        self.current_nb_id = nb_id
        self.current_page_id = page_id
        self._refresh_notebooks_list()
        self._refresh_pages_list()

    def _on_storage_changed(self, entity_type: str):
        if entity_type in ("notebooks", "all"):
            pass
