"""
Spacious, modern Rich-Text Editor for Notebooks in WorkBOXig.
Designed for comfortable long-form reading, note-taking, and studying (Notion / Craft style).
"""

import os
import uuid
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QMenu, QStackedWidget, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor,
    QTextBlockFormat, QTextListFormat, QCursor, QIcon,
    QImage, QTextImageFormat, QTextDocument
)
from src.styles import COLORS
from src.icons import get_pixmap, get_icon
from src.i18n import t
from src.storage import get_storage


class NotebookTextEdit(QTextEdit):
    """
    Subclassed QTextEdit with rich clipboard screenshot pasting (Ctrl+V),
    drag-and-drop photos/images, and responsive auto-scaling image insertion.
    """
    image_inserted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        # 1. Clipboard image (PrintScreen, Win+Shift+S, snipping tool, copied web images)
        if source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                self.insert_qimage(img)
                return

        # 2. File URLs copied or dropped from Windows Explorer
        if source.hasUrls():
            inserted = False
            for url in source.urls():
                lp = url.toLocalFile()
                ext = os.path.splitext(lp)[1].lower()
                if ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'):
                    img = QImage(lp)
                    if not img.isNull():
                        self.insert_qimage(img, source_path=lp)
                        inserted = True
            if inserted:
                return

        super().insertFromMimeData(source)

    def insert_qimage(self, qimage: QImage, source_path: Optional[str] = None):
        """Save image locally into attachments and insert into QTextDocument at cursor."""
        try:
            storage = get_storage()
            att_dir = storage.get_attachments_dir()
            filename = f"screenshot_{uuid.uuid4().hex[:10]}.png"
            dest_path = os.path.join(att_dir, filename)

            # Save PNG file to local attachments directory
            qimage.save(dest_path, "PNG")

            url = QUrl.fromLocalFile(dest_path)

            # Auto-scale image to fit comfortable editor width (max 680px)
            orig_w = qimage.width()
            orig_h = qimage.height()
            max_w = 680

            fmt = QTextImageFormat()
            fmt.setName(url.toString())

            if orig_w > max_w:
                ratio = max_w / orig_w
                fmt.setWidth(max_w)
                fmt.setHeight(int(orig_h * ratio))
            else:
                fmt.setWidth(orig_w)
                fmt.setHeight(orig_h)

            # Register resource into document
            self.document().addResource(QTextDocument.ResourceType.ImageResource, url, qimage)

            cursor = self.textCursor()
            cursor.insertBlock()
            cursor.insertImage(fmt)
            cursor.insertBlock()
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self.image_inserted.emit()
        except Exception as e:
            print(f"[NotebookTextEdit] Failed to insert image: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            self.insertFromMimeData(event.mimeData())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class RichEditor(QWidget):
    """
    Rich text editor with floating modern formatting toolbar, spacious layout,
    empty-state handling, markdown export, and automatic live word count.
    """
    content_changed = pyqtSignal(str, str, str) # title, content_html, content_plain
    focus_mode_toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self._block_signals = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # QStackedWidget: Page 0 = Active Editor, Page 1 = Empty State
        self.stack = QStackedWidget(self)

        # ---------------- Page 0: Active Editor Widget ----------------
        self.editor_page = QWidget()
        layout = QVBoxLayout(self.editor_page)
        layout.setContentsMargins(36, 26, 36, 20)
        layout.setSpacing(14)

        # 1. Header: Page Title Input (Large, modern typography)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(t("editor_title_ph"))
        self.title_input.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_primary']};
                padding: 6px 0px;
            }}
            QLineEdit:focus {{
                border-bottom: 2px solid {COLORS['primary']};
            }}
        """)
        self.title_input.textChanged.connect(self._on_content_changed)
        layout.addWidget(self.title_input)

        # 2. Modern Floating Formatting Toolbar (Linear / Notion style)
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 10px;
                padding: 3px;
            }}
        """)
        tb_layout = QHBoxLayout(self.toolbar_frame)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(5)

        # Text Formatting: B, I, U, S with real QFont properties
        self.btn_bold = self._create_tool_btn("B", t("editor_bold"), self._toggle_bold, bold=True)
        tb_layout.addWidget(self.btn_bold)

        self.btn_italic = self._create_tool_btn("I", t("editor_italic"), self._toggle_italic, italic=True)
        tb_layout.addWidget(self.btn_italic)

        self.btn_underline = self._create_tool_btn("U", t("editor_underline"), self._toggle_underline, underline=True)
        tb_layout.addWidget(self.btn_underline)

        self.btn_strike = self._create_tool_btn("S", t("editor_strike"), self._toggle_strike, strike=True)
        tb_layout.addWidget(self.btn_strike)

        self._add_separator(tb_layout)

        # Headings & Paragraph
        btn_h1 = self._create_tool_btn("H1", t("editor_h1"), lambda: self._apply_heading(1), bold=True)
        tb_layout.addWidget(btn_h1)

        btn_h2 = self._create_tool_btn("H2", t("editor_h2"), lambda: self._apply_heading(2), bold=True)
        tb_layout.addWidget(btn_h2)

        btn_p = self._create_tool_btn("P", t("editor_p"), self._apply_normal_text)
        tb_layout.addWidget(btn_p)

        self._add_separator(tb_layout)

        # Lists & Blocks
        btn_bullet = self._create_tool_btn("•", t("editor_bullet"), self._toggle_bullet_list, bold=True)
        tb_layout.addWidget(btn_bullet)

        btn_num = self._create_tool_btn("1.", t("editor_num"), self._toggle_number_list, bold=True)
        tb_layout.addWidget(btn_num)

        btn_code = self._create_tool_btn("{ }", t("editor_code"), self._apply_code_block, bold=True)
        tb_layout.addWidget(btn_code)

        btn_quote = QPushButton()
        btn_quote.setIcon(get_icon("quote", COLORS['text_primary'], 18))
        btn_quote.setIconSize(QSize(18, 18))
        btn_quote.setToolTip(t("editor_quote"))
        btn_quote.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_quote.setFixedSize(34, 32)
        btn_quote.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['primary_border']};
            }}
        """)
        btn_quote.clicked.connect(self._apply_quote_block)
        tb_layout.addWidget(btn_quote)

        self._add_separator(tb_layout)

        # Color picker button with quick menu
        color_btn = QPushButton()
        self.color_btn = color_btn
        color_btn.setIcon(get_icon("palette", COLORS['text_secondary'], 18))
        color_btn.setIconSize(QSize(18, 18))
        color_btn.setFixedSize(36, 32)
        color_btn.setToolTip(t("editor_text_color"))
        color_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton::menu-indicator {{ image: none; width: 0px; }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['primary_border']};
            }}
        """)
        color_menu = QMenu(self)
        color_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_popup']};
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
        for name, hex_val in [
            (t("editor_color_default"), "#FFFFFF"),
            (t("editor_color_sky"), "#38BDF8"),
            (t("editor_color_emerald"), "#10B981"),
            (t("editor_color_amber"), "#F59E0B"),
            (t("editor_color_coral"), "#FB7185"),
            (t("editor_color_purple"), "#A78BFA"),
        ]:
            act = color_menu.addAction(name)
            act.triggered.connect(lambda ch, c=hex_val: self._set_text_color(c))
        color_btn.setMenu(color_menu)
        tb_layout.addWidget(color_btn)

        # Highlight marker
        hl_btn = QPushButton()
        self.highlight_btn = hl_btn
        hl_btn.setIcon(get_icon("highlighter", COLORS['text_secondary'], 18))
        hl_btn.setIconSize(QSize(18, 18))
        hl_btn.setFixedSize(36, 32)
        hl_btn.setToolTip(t("editor_highlight"))
        hl_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hl_btn.setStyleSheet(color_btn.styleSheet())
        hl_menu = QMenu(self)
        hl_menu.setStyleSheet(color_menu.styleSheet())
        for name, hex_val in [
            (t("editor_hl_none"), "transparent"),
            (t("editor_hl_yellow"), "rgba(245, 158, 11, 0.35)"),
            (t("editor_hl_green"), "rgba(16, 185, 129, 0.35)"),
            (t("editor_hl_blue"), "rgba(56, 189, 248, 0.35)"),
            (t("editor_hl_purple"), "rgba(99, 102, 241, 0.35)"),
        ]:
            act = hl_menu.addAction(name)
            act.triggered.connect(lambda ch, bg=hex_val: self._set_highlight(bg))
        hl_btn.setMenu(hl_menu)
        tb_layout.addWidget(hl_btn)

        # Clear format
        clear_btn = QPushButton()
        clear_btn.setIcon(get_icon("close", COLORS['text_muted'], 16))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setFixedSize(34, 32)
        clear_btn.setToolTip(t("editor_clear"))
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.2);
                border-color: rgba(239, 68, 68, 0.4);
            }}
        """)
        clear_btn.clicked.connect(self._clear_format)
        tb_layout.addWidget(clear_btn)

        self._add_separator(tb_layout)

        # Insert Photo / Screenshot button
        img_btn = QPushButton()
        img_btn.setIcon(get_icon("image", COLORS['sky'], 18))
        img_btn.setIconSize(QSize(18, 18))
        img_btn.setFixedSize(36, 32)
        img_btn.setToolTip(t("editor_insert_img"))
        img_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        img_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['sky']};
            }}
        """)
        img_btn.clicked.connect(self._choose_and_insert_image)
        tb_layout.addWidget(img_btn)

        tb_layout.addStretch()

        self._add_separator(tb_layout)

        # Export dropdown
        export_btn = QPushButton()
        export_btn.setIcon(get_icon("export", COLORS['sky'], 18))
        export_btn.setIconSize(QSize(18, 18))
        export_btn.setFixedSize(36, 32)
        export_btn.setToolTip(t("editor_export_tt"))
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton::menu-indicator {{ image: none; width: 0px; }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['sky']};
            }}
        """)
        exp_menu = QMenu(self)
        exp_menu.setStyleSheet(color_menu.styleSheet())
        act_md = exp_menu.addAction(get_icon("file_text", COLORS['sky'], 16), t("editor_export_md"))
        act_md.triggered.connect(lambda: self._export_file("md"))
        act_html = exp_menu.addAction(get_icon("export", COLORS['sky'], 16), t("editor_export_html"))
        act_html.triggered.connect(lambda: self._export_file("html"))
        export_btn.setMenu(exp_menu)
        tb_layout.addWidget(export_btn)

        # Distraction-free Focus Toggle
        focus_btn = QPushButton()
        focus_btn.setIcon(get_icon("focus", COLORS['emerald'], 18))
        focus_btn.setIconSize(QSize(18, 18))
        focus_btn.setFixedSize(36, 32)
        focus_btn.setToolTip(t("editor_zen"))
        focus_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        focus_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['emerald']};
            }}
        """)
        focus_btn.clicked.connect(self.focus_mode_toggled.emit)
        tb_layout.addWidget(focus_btn)

        layout.addWidget(self.toolbar_frame)

        # 3. Spacious Content Canvas (NotebookTextEdit with screenshots/photos & Notion styling)
        self.editor = NotebookTextEdit()
        self.editor.setFont(QFont("Segoe UI", 12))
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 14px;
                padding: 28px;
                line-height: 1.6;
                selection-background-color: {COLORS['primary']};
            }}
            QTextEdit:focus {{
                border-color: {COLORS['border_light']};
            }}
        """)
        self.editor.textChanged.connect(self._on_content_changed)
        self.editor.cursorPositionChanged.connect(self._update_toolbar_states)
        layout.addWidget(self.editor, stretch=1)

        # 4. Status Footer (Word count, reading time, save status)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(6, 0, 6, 0)

        self.stats_label = QLabel(t("editor_stats", words=0, minutes=0))
        self.stats_label.setFont(QFont("Segoe UI", 9))
        self.stats_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        footer_layout.addWidget(self.stats_label)

        footer_layout.addStretch()

        self.save_status_label = QLabel(t("editor_saved"))
        self.save_status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.save_status_label.setStyleSheet(f"color: {COLORS['emerald']};")
        footer_layout.addWidget(self.save_status_label)

        layout.addLayout(footer_layout)
        self.stack.addWidget(self.editor_page)

        # ---------------- Page 1: Empty Placeholder ----------------
        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(14)

        icon_ph = QLabel()
        icon_ph.setPixmap(get_pixmap("notebooks", COLORS['primary_light'], 54))
        icon_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_ph)

        title_ph = QLabel(t("editor_empty_title"))
        self.empty_title = title_ph
        title_ph.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_ph.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(title_ph)

        desc_ph = QLabel(t("editor_empty_desc"))
        desc_ph.setFont(QFont("Segoe UI", 10))
        desc_ph.setStyleSheet(f"color: {COLORS['text_muted']};")
        desc_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(desc_ph)

        self.stack.addWidget(self.empty_page)
        main_layout.addWidget(self.stack)

        self.show_empty()

    def _create_tool_btn(self, text: str, tooltip: str, callback, bold=False, italic=False, underline=False, strike=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(34, 32)
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        if bold:
            font.setBold(True)
        if italic:
            font.setItalic(True)
        if underline:
            font.setUnderline(True)
        if strike:
            font.setStrikeOut(True)
        btn.setFont(font)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 6px;
                color: {COLORS['text_primary']};
                padding: 0px;
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_selected']};
                border-color: {COLORS['primary_border']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                border: 1px solid {COLORS['primary']};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {COLORS['border_light']}; margin: 2px 4px;")
        layout.addWidget(sep)

    def show_empty(self):
        self.current_page_id = None
        self.stack.setCurrentWidget(self.empty_page)

    def set_content(self, page_id: str, title: str, content_html: str):
        if not page_id:
            self.show_empty()
            return

        self._block_signals = True
        self.current_page_id = page_id
        self.stack.setCurrentWidget(self.editor_page)
        
        self.title_input.setText(title or "")
        self.editor.setHtml(content_html or "")
        self.editor.document().clearUndoRedoStacks()
        self._block_signals = False
        
        self._update_stats()
        self.save_status_label.setText(t("editor_saved"))
        self.save_status_label.setStyleSheet(f"color: {COLORS['emerald']};")
        self._update_toolbar_states()

    def _on_content_changed(self):
        if self._block_signals or not self.current_page_id:
            return
        self.save_status_label.setText(t("editor_saving"))
        self.save_status_label.setStyleSheet(f"color: {COLORS['amber']};")
        self._update_stats()
        title = self.title_input.text()
        html = self.editor.toHtml()
        plain = self.editor.toPlainText()
        self.content_changed.emit(title, html, plain)

    def mark_saved(self):
        self.save_status_label.setText(t("editor_saved"))
        self.save_status_label.setStyleSheet(f"color: {COLORS['emerald']};")

    def _update_stats(self):
        text = self.editor.toPlainText().strip()
        words = len(text.split()) if text else 0
        read_time = max(1, words // 180) if words > 0 else 0
        self.stats_label.setText(t("editor_stats", words=words, minutes=read_time))

    def _update_toolbar_states(self):
        fmt = self.editor.currentCharFormat()
        self.btn_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.btn_italic.setChecked(fmt.fontItalic())
        self.btn_underline.setChecked(fmt.fontUnderline())
        self.btn_strike.setChecked(fmt.fontStrikeOut())

    # --- Formatting Helpers ---
    def _toggle_bold(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        weight = QFont.Weight.Normal if fmt.fontWeight() == QFont.Weight.Bold else QFont.Weight.Bold
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self._update_toolbar_states()

    def _toggle_italic(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self._update_toolbar_states()

    def _toggle_underline(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self._update_toolbar_states()

    def _toggle_strike(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self._update_toolbar_states()

    def _apply_heading(self, level: int):
        cursor = self.editor.textCursor()
        size = 20 if level == 1 else 16
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        fmt.setFontWeight(QFont.Weight.Bold)
        fmt.setForeground(QColor(COLORS['text_primary']))
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _apply_normal_text(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(12)
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setForeground(QColor(COLORS['text_primary']))
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        cursor.setCharFormat(fmt)
        self.editor.setCurrentCharFormat(fmt)

    def _toggle_bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDisc)

    def _toggle_number_list(self):
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDecimal)

    def _apply_code_block(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily("Consolas, Courier New, monospace")
        fmt.setFontPointSize(11)
        fmt.setBackground(QColor("#181D29"))
        fmt.setForeground(QColor("#38BDF8"))
        cursor.mergeCharFormat(fmt)

    def _apply_quote_block(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(True)
        fmt.setForeground(QColor("#A5B4FC"))
        cursor.mergeCharFormat(fmt)

    def _set_text_color(self, hex_val: str):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(hex_val))
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _set_highlight(self, bg_val: str):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        if bg_val == "transparent":
            fmt.setBackground(QColor(0, 0, 0, 0))
        else:
            fmt.setBackground(QColor(bg_val))
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _clear_format(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(12)
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.setForeground(QColor(COLORS['text_primary']))
        fmt.setBackground(QColor(0, 0, 0, 0))
        cursor.setCharFormat(fmt)
        self.editor.setCurrentCharFormat(fmt)
        self._update_toolbar_states()

    def _choose_and_insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("editor_image_select_title"),
            "",
            t("editor_image_filter")
        )
        if file_path:
            img = QImage(file_path)
            if not img.isNull():
                self.editor.insert_qimage(img, source_path=file_path)
                self.save_status_label.setText(t("editor_image_inserted"))
                self.save_status_label.setStyleSheet(f"color: {COLORS['emerald']};")

    def _export_file(self, fmt_type: str):
        title = self.title_input.text().strip() or t("editor_default_note_title")
        default_filename = f"{title}.{fmt_type}"
        
        file_filter = "Markdown (*.md)" if fmt_type == "md" else "HTML (*.html)"
        path, _ = QFileDialog.getSaveFileName(self, t("editor_export_dialog_title"), default_filename, file_filter)
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                if fmt_type == "md":
                    text = f"# {title}\n\n" + self.editor.toPlainText()
                    f.write(text)
                else:
                    html_content = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{self.editor.toHtml()}</body></html>"
                    f.write(html_content)
            self.save_status_label.setText(t("editor_exported"))
            self.save_status_label.setStyleSheet(f"color: {COLORS['sky']};")
        except Exception as e:
            print(f"[Export Error]: {e}")
