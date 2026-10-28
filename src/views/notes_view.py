"""
Notes (Заметки) View for WorkBOXig.
Fast, distraction-free scratchpad canvas for snippets, quick thoughts, and ideas.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QFrame,
    QSplitter, QMessageBox, QApplication, QStackedWidget, QScrollArea,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QIcon
from src.styles import COLORS
from src.storage import get_storage
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.utils.shortcuts import clear_layout


COLOR_PALETTE = [
    ("#6366F1", "color_indigo"),
    ("#10B981", "color_emerald"),
    ("#F59E0B", "color_amber"),
    ("#06B6D4", "color_cyan"),
    ("#EC4899", "color_pink"),
    ("#8B5CF6", "color_violet"),
]


class NoteCardItemWidget(QWidget):
    """Custom note card representation in the list."""
    def __init__(self, title: str, snippet: str, color_hex: str, pinned: bool, date_str: str, tags: list, parent=None):
        super().__init__(parent)
        self.setObjectName("note_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top bar: Title + Pin icon
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        title_lbl = QLabel(title or t("untitled_page"))
        title_lbl.setObjectName("note_item_title")
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_layout.addWidget(title_lbl, stretch=1)

        if pinned:
            pin_lbl = QLabel()
            pin_lbl.setPixmap(get_pixmap("pin", COLORS['amber'], 13))
            pin_lbl.setStyleSheet("background: transparent;")
            top_layout.addWidget(pin_lbl)

        layout.addLayout(top_layout)

        # Snippet preview
        if snippet:
            preview_text = snippet.replace("\n", " ").strip()[:80]
            if len(snippet) > 80:
                preview_text += "..."
            snip_lbl = QLabel(preview_text)
            snip_lbl.setFont(QFont("Segoe UI", 9))
            snip_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            snip_lbl.setWordWrap(True)
            layout.addWidget(snip_lbl)

        # Footer: Tags and date
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(6)

        for tag in tags[:3]:
            tag_lbl = QLabel(f"#{tag}")
            tag_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.DemiBold))
            tag_lbl.setStyleSheet(f"""
                background-color: {COLORS['bg_card_hover']};
                color: {color_hex};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 1px 5px;
            """)
            bottom_layout.addWidget(tag_lbl)

        bottom_layout.addStretch()

        time_lbl = QLabel(date_str)
        time_lbl.setFont(QFont("Segoe UI", 8))
        time_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        bottom_layout.addWidget(time_lbl)

        layout.addLayout(bottom_layout)

        # Style card
        self.setStyleSheet(f"""
            QWidget#note_card {{
                border: 1px solid {COLORS['border_subtle']};
                border-left: 3px solid {color_hex};
                border-radius: 8px;
                background-color: {COLORS['bg_card']};
            }}
            QWidget#note_card:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['border_light']};
            }}
        """)


class NotesView(QWidget):
    """
    Scratchpad Canvas and Notes Hub.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = get_storage()
        self.current_note_id = None
        self.selected_tag = "all"
        self._block_signals = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border_subtle']};
                width: 1px;
            }}
        """)

        # ---------------- Left Panel: Notes List & Search ----------------
        left_panel = QFrame()
        self.left_panel = left_panel
        left_panel.setObjectName("notes_left_panel")
        left_panel.setStyleSheet(f"QFrame#notes_left_panel {{ background-color: {COLORS['bg_sidebar']}; }}")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 20, 16, 16)
        left_layout.setSpacing(12)

        header_l = QHBoxLayout()
        title_lbl = QLabel(t("notes_col_title"))
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header_l.addWidget(title_lbl)
        header_l.addStretch()

        new_btn = QPushButton(t("notes_add_btn"))
        new_btn.setIcon(get_icon("plus", "#FFFFFF", 16))
        new_btn.setIconSize(QSize(16, 16))
        new_btn.setObjectName("primary-btn")
        new_btn.clicked.connect(self._create_note)
        header_l.addWidget(new_btn)
        left_layout.addLayout(header_l)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("notes_search_ph"))
        self.search_input.textChanged.connect(self._refresh_list)
        left_layout.addWidget(self.search_input)

        # Tag filter chips container
        self.tags_scroll = QScrollArea()
        self.tags_scroll.setFixedHeight(34)
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setStyleSheet("background: transparent; border: none;")
        self.tags_widget = QWidget()
        self.tags_widget.setStyleSheet("background: transparent;")
        self.tags_chip_layout = QHBoxLayout(self.tags_widget)
        self.tags_chip_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_chip_layout.setSpacing(6)
        self.tags_scroll.setWidget(self.tags_widget)
        left_layout.addWidget(self.tags_scroll)

        # Notes list widget
        self.notes_list = QListWidget()
        self.notes_list.setSpacing(8)
        self.notes_list.currentRowChanged.connect(self._on_note_selected)
        left_layout.addWidget(self.notes_list)

        left_panel.setMinimumWidth(330)
        splitter.addWidget(left_panel)

        # ---------------- Right Panel: Scratchpad Canvas with Stack ----------------
        self.canvas_stack = QStackedWidget()

        # Canvas Page (Active Note)
        self.canvas_panel = QFrame()
        self.canvas_panel.setObjectName("notes_canvas_panel")
        self.canvas_panel.setStyleSheet(f"QFrame#notes_canvas_panel {{ background-color: {COLORS['bg_root']}; }}")
        canvas_layout = QVBoxLayout(self.canvas_panel)
        canvas_layout.setContentsMargins(32, 24, 32, 20)
        canvas_layout.setSpacing(14)

        # Canvas Header Toolbar
        tb_layout = QHBoxLayout()
        tb_layout.setSpacing(8)

        # Color picker buttons
        color_group = QHBoxLayout()
        color_group.setSpacing(6)
        for hex_col, name in COLOR_PALETTE:
            c_btn = QPushButton()
            c_btn.setFixedSize(18, 18)
            c_btn.setToolTip(t(name))
            c_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_col};
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 9px;
                }}
                QPushButton:hover {{
                    border: 2px solid #FFFFFF;
                }}
            """)
            c_btn.clicked.connect(lambda ch, c=hex_col: self._set_current_note_color(c))
            color_group.addWidget(c_btn)
        tb_layout.addLayout(color_group)

        tb_layout.addStretch()

        self.pin_btn = QPushButton(t("notes_pin"))
        self.pin_btn.setIcon(get_icon("pin", COLORS['text_secondary'], 16))
        self.pin_btn.setIconSize(QSize(16, 16))
        self.pin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
            }}
        """)
        self.pin_btn.clicked.connect(self._toggle_pin)
        tb_layout.addWidget(self.pin_btn)

        copy_btn = QPushButton(t("notes_copy"))
        self.copy_btn = copy_btn
        copy_btn.setIcon(get_icon("copy", COLORS['text_secondary'], 16))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setStyleSheet(self.pin_btn.styleSheet())
        copy_btn.clicked.connect(self._copy_note_text)
        tb_layout.addWidget(copy_btn)

        export_btn = QPushButton(t("notes_export"))
        self.export_btn = export_btn
        export_btn.setIcon(get_icon("export", COLORS['text_secondary'], 16))
        export_btn.setIconSize(QSize(16, 16))
        export_btn.setStyleSheet(self.pin_btn.styleSheet())
        export_btn.clicked.connect(self._export_note)
        tb_layout.addWidget(export_btn)

        del_btn = QPushButton(t("notes_delete"))
        del_btn.setIcon(get_icon("trash", "#F87171", 16))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setObjectName("danger-btn")
        del_btn.clicked.connect(self._delete_current_note)
        tb_layout.addWidget(del_btn)

        canvas_layout.addLayout(tb_layout)

        # Note Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(t("notes_title_ph"))
        self.title_input.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_primary']};
                padding: 4px 0px;
            }}
            QLineEdit:focus {{
                border-bottom: 2px solid {COLORS['primary']};
            }}
        """)
        self.title_input.textChanged.connect(self._on_text_edited)
        canvas_layout.addWidget(self.title_input)

        # Tags input
        tags_layout = QHBoxLayout()
        tags_lbl = QLabel(t("notes_tags_lbl"))
        tags_lbl.setFont(QFont("Segoe UI", 9))
        tags_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText(t("notes_tags_ph"))
        self.tags_input.setFont(QFont("Segoe UI", 9))
        self.tags_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 4px 10px;
            }}
        """)
        self.tags_input.textChanged.connect(self._on_text_edited)
        tags_layout.addWidget(tags_lbl)
        tags_layout.addWidget(self.tags_input, stretch=1)
        canvas_layout.addLayout(tags_layout)

        # Scratchpad Body
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText(t("notes_body_ph"))
        self.body_edit.setFont(QFont("Segoe UI", 12))
        self.body_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
                padding: 18px;
                line-height: 1.6;
            }}
        """)
        self.body_edit.textChanged.connect(self._on_text_edited)
        canvas_layout.addWidget(self.body_edit, stretch=1)

        # Footer
        footer_layout = QHBoxLayout()
        self.save_lbl = QLabel(t("editor_saved"))
        self.save_lbl.setFont(QFont("Segoe UI", 9))
        self.save_lbl.setStyleSheet(f"color: {COLORS['emerald']};")
        footer_layout.addWidget(self.save_lbl)

        footer_layout.addStretch()

        self.char_count_lbl = QLabel(f"0 {t('characters')}")
        self.char_count_lbl.setFont(QFont("Segoe UI", 9))
        self.char_count_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        footer_layout.addWidget(self.char_count_lbl)
        canvas_layout.addLayout(footer_layout)

        self.canvas_stack.addWidget(self.canvas_panel)

        # Empty State Page
        self.empty_page = QWidget()
        empty_l = QVBoxLayout(self.empty_page)
        empty_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_l.setSpacing(12)

        icon_ph = QLabel()
        icon_ph.setPixmap(get_pixmap("notes", COLORS['primary_light'], 54))
        icon_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_l.addWidget(icon_ph)

        title_ph = QLabel(t("notes_select_prompt"))
        self.empty_title = title_ph
        title_ph.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_ph.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_l.addWidget(title_ph)

        create_btn_ph = QPushButton(t("btn_new_note"))
        self.empty_action = create_btn_ph
        create_btn_ph.setIcon(get_icon("plus", "#FFFFFF", 16))
        create_btn_ph.setIconSize(QSize(16, 16))
        create_btn_ph.setObjectName("primary-btn")
        create_btn_ph.setFixedWidth(160)
        create_btn_ph.clicked.connect(self._empty_action_clicked)
        empty_l.addWidget(create_btn_ph, alignment=Qt.AlignmentFlag.AlignCenter)

        self.canvas_stack.addWidget(self.empty_page)

        splitter.addWidget(self.canvas_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([350, 680])

        layout.addWidget(splitter)

        self._refresh_tag_chips()
        self._refresh_list()

    def _refresh_tag_chips(self):
        # Clear existing chips
        clear_layout(self.tags_chip_layout)

        # Collect unique tags
        tags = set()
        for n in self.storage.get_notes():
            for tag_item in n.get("tags", []):
                if tag_item.strip():
                    tags.add(tag_item.strip())

        # "Все" chip
        all_btn = QPushButton(t("filter_all"))
        all_btn.setCheckable(True)
        all_btn.setChecked(self.selected_tag == "all")
        self._style_chip_button(all_btn, self.selected_tag == "all")
        all_btn.clicked.connect(lambda: self._select_tag("all"))
        self.tags_chip_layout.addWidget(all_btn)

        for tag_name in sorted(tags):
            btn = QPushButton(f"#{tag_name}")
            btn.setCheckable(True)
            btn.setChecked(self.selected_tag == tag_name)
            self._style_chip_button(btn, self.selected_tag == tag_name)
            btn.clicked.connect(lambda ch, tag=tag_name: self._select_tag(tag))
            self.tags_chip_layout.addWidget(btn)

        self.tags_chip_layout.addStretch()

    def _style_chip_button(self, btn: QPushButton, is_active: bool):
        if is_active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary_subtle']};
                    color: {COLORS['primary_light']};
                    border: 1px solid {COLORS['primary_border']};
                    border-radius: 10px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 10px;
                    padding: 2px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)

    def _select_tag(self, tag: str):
        self.selected_tag = tag
        self._refresh_tag_chips()
        self._refresh_list()

    def _refresh_list(self):
        self.notes_list.clear()
        query = self.search_input.text().lower().strip()
        all_notes = self.storage.get_notes()

        target_row = 0
        found_target = False

        for i, note in enumerate(all_notes):
            title = note.get("title", "")
            content = note.get("content", "")
            tags = note.get("tags", [])
            tags_str = " ".join(tags)

            # Tag filter
            if self.selected_tag != "all" and self.selected_tag not in tags:
                continue

            # Text query
            if query and (query not in title.lower() and query not in content.lower() and query not in tags_str.lower()):
                continue

            date_str = note.get("updated_at", "")[:10]
            item = QListWidgetItem(self.notes_list)
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            widget = NoteCardItemWidget(
                title=title,
                snippet=content,
                color_hex=note.get("color", COLORS['primary']),
                pinned=note.get("pinned", False),
                date_str=date_str,
                tags=tags
            )
            item.setSizeHint(QSize(240, 96 if tags else 82))
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, widget)

            if note["id"] == self.current_note_id:
                target_row = self.notes_list.count() - 1
                found_target = True

        if self.notes_list.count() > 0:
            self.canvas_stack.setCurrentWidget(self.canvas_panel)
            self.notes_list.setCurrentRow(target_row if found_target else 0)
        else:
            self.current_note_id = None
            filtered = bool(all_notes) and (bool(query) or self.selected_tag != "all")
            self.empty_title.setText(t("notes_empty_filter") if filtered else t("notes_select_prompt"))
            self.empty_action.setText(t("notes_reset_filter") if filtered else t("btn_new_note"))
            self.empty_action.setProperty("clear_filters", filtered)
            self.canvas_stack.setCurrentWidget(self.empty_page)

    def _empty_action_clicked(self):
        if self.empty_action.property("clear_filters"):
            self.selected_tag = "all"
            self.search_input.clear()
            self._refresh_tag_chips()
            self._refresh_list()
        else:
            self._create_note()

    def _on_note_selected(self, row: int):
        if row < 0:
            return
        item = self.notes_list.item(row)
        if not item:
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_note_id = note_id

        note = next((n for n in self.storage.get_notes() if n["id"] == note_id), None)
        self._load_note_data(note)

    def _load_note_data(self, note):
        self._block_signals = True
        if note:
            self.canvas_stack.setCurrentWidget(self.canvas_panel)
            self.title_input.setText(note.get("title", ""))
            self.tags_input.setText(", ".join(note.get("tags", [])))
            self.body_edit.setText(note.get("content", ""))
            is_pinned = note.get("pinned", False)
            self.pin_btn.setText(t("notes_unpin") if is_pinned else t("notes_pin"))
            self.pin_btn.setIcon(get_icon("pin", COLORS['amber'] if is_pinned else COLORS['text_secondary'], 16))
            self.save_lbl.setText(t("editor_saved"))
            self.save_lbl.setStyleSheet(f"color: {COLORS['emerald']};")
            self.char_count_lbl.setText(f"{len(note.get('content', ''))} {t('characters')}")
        else:
            self.canvas_stack.setCurrentWidget(self.empty_page)
        self._block_signals = False

    def _on_text_edited(self):
        if self._block_signals or not self.current_note_id:
            return
        
        self.save_lbl.setText(t("saving"))
        self.save_lbl.setStyleSheet(f"color: {COLORS['amber']};")
        
        content = self.body_edit.toPlainText()
        self.char_count_lbl.setText(f"{len(content)} {t('characters')}")

        title = self.title_input.text().strip() or t("notes_untitled")
        raw_tags = [t.strip() for t in self.tags_input.text().split(",") if t.strip()]

        self.storage.update_note(
            self.current_note_id,
            title=title,
            content=content,
            tags=raw_tags
        )

        # Update card in list
        row = self.notes_list.currentRow()
        if row >= 0:
            item = self.notes_list.item(row)
            if item:
                widget = self.notes_list.itemWidget(item)
                if isinstance(widget, NoteCardItemWidget):
                    widget.findChild(QLabel).setText(title)

    def _create_note(self):
        new_note = self.storage.add_note(title=t("btn_new_note"), content="", color=COLORS['primary'])
        self.current_note_id = new_note["id"]
        self._refresh_tag_chips()
        self._refresh_list()
        self.title_input.setFocus()
        self.title_input.selectAll()

    def _set_current_note_color(self, hex_color: str):
        if not self.current_note_id:
            return
        self.storage.update_note(self.current_note_id, color=hex_color)
        self._refresh_list()

    def _toggle_pin(self):
        if not self.current_note_id:
            return
        is_pinned = self.storage.toggle_pin_note(self.current_note_id)
        self.pin_btn.setText(t("notes_unpin") if is_pinned else t("notes_pin"))
        self.pin_btn.setIcon(get_icon("pin", COLORS['amber'] if is_pinned else COLORS['text_secondary'], 16))
        self._refresh_list()

    def _copy_note_text(self):
        text = f"{self.title_input.text()}\n\n{self.body_edit.toPlainText()}"
        QApplication.clipboard().setText(text)
        self.save_lbl.setText(t("notes_copied_toast"))
        self.save_lbl.setStyleSheet(f"color: {COLORS['sky']};")

    def _delete_current_note(self):
        if not self.current_note_id:
            return
        if QMessageBox.question(self, t("notes_delete_confirm_title"), t("notes_delete_confirm_msg")) == QMessageBox.StandardButton.Yes:
            self.storage.delete_note(self.current_note_id)
            self.current_note_id = None
            self._refresh_tag_chips()
            self._refresh_list()

    def _export_note(self):
        if not self.current_note_id:
            return
        title = self.title_input.text().strip() or t("notes_default_title")
        path, _ = QFileDialog.getSaveFileName(self, t("notes_export_title"), f"{title}.md", t("notes_files_filter"))
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{self.body_edit.toPlainText()}")
            self.save_lbl.setText(t("notes_exported_status"))
            self.save_lbl.setStyleSheet(f"color: {COLORS['sky']};")
        except Exception as e:
            print(f"[Note Export Error]: {e}")

    def select_note(self, note_id: str):
        self.current_note_id = note_id
        self._refresh_list()
