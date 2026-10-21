"""
Cyberpunk: Edgerunners Anime Drawing Engine for WorkBOXig.
Draws authentic HUD-style chamfered tech buttons, hazard stripes, neon borders, and corner brackets.
Activated exclusively when the 'cyberpunk' theme is active.
"""

from PyQt6.QtCore import QObject, QEvent, Qt, QPointF, QRectF
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPainter, QPolygonF, QColor, QBrush, QPen, QFont


class CyberpunkButtonPainter:
    """Renders authentic Cyberpunk: Edgerunners anime HUD style buttons."""

    @staticmethod
    def paint_button(painter: QPainter, btn: QPushButton):
        w = btn.width()
        h = btn.height()
        if w <= 4 or h <= 4:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_down = btn.isDown()
        is_hover = btn.underMouse()
        is_checked = btn.isChecked()
        is_enabled = btn.isEnabled()
        obj_name = btn.objectName()
        is_primary = (obj_name == "primary-btn")
        is_danger = (obj_name == "danger-btn")
        is_ghost = (obj_name == "ghost-btn")

        # Edgerunner Signature Anime Palette
        c_yellow = QColor("#FCEE0A")       # High-Vis Sandevistan Neon Yellow
        c_yellow_hover = QColor("#FFF152")
        c_cyan = QColor("#00F0FF")         # Hologram Cyber Cyan
        c_pink = QColor("#FF0055")         # Cyber Alert Hot Pink
        c_dark_plate = QColor("#0F1422")   # Obsidian Carbon
        c_dark_hover = QColor("#182035")
        c_border_dim = QColor("#222D42")

        # Dynamic cut corner size based on button dimensions
        is_small = (w < 40 or h < 30)
        cut = 4.0 if is_small else (6.0 if h <= 34 else 9.0)

        # Chamfered polygon: angled cuts at top-left and bottom-right
        poly = QPolygonF([
            QPointF(cut, 0.5),
            QPointF(w - 0.5, 0.5),
            QPointF(w - 0.5, h - cut),
            QPointF(w - cut, h - 0.5),
            QPointF(0.5, h - 0.5),
            QPointF(0.5, cut),
        ])

        # State-based background, border, and text styling
        if not is_enabled:
            bg_col = QColor("#090B10")
            border_col = QColor("#161D2B")
            text_col = QColor("#46526B")
        elif is_primary:
            if is_down:
                bg_col = QColor("#000000")
                border_col = c_yellow
                text_col = c_yellow
            elif is_hover:
                bg_col = c_yellow_hover
                border_col = c_cyan
                text_col = QColor("#000000")
            else:
                bg_col = c_yellow
                border_col = c_cyan
                text_col = QColor("#000000")
        elif is_danger:
            if is_down:
                bg_col = c_pink
                border_col = QColor("#FFFFFF")
                text_col = QColor("#000000")
            elif is_hover:
                bg_col = QColor(255, 0, 85, 45)
                border_col = c_pink
                text_col = c_pink
            else:
                bg_col = QColor(255, 0, 85, 20)
                border_col = c_pink
                text_col = c_pink
        elif is_ghost:
            if is_hover:
                bg_col = QColor(0, 240, 255, 18)
                border_col = c_cyan
                text_col = c_cyan
            else:
                bg_col = QColor(0, 0, 0, 0)
                border_col = QColor(0, 0, 0, 0)
                text_col = QColor("#8291A8")
        else: # Standard / Checkable Action Buttons
            if is_checked:
                bg_col = QColor("#18243A")
                border_col = c_cyan
                text_col = c_cyan
            elif is_down:
                bg_col = QColor("#141D30")
                border_col = c_yellow
                text_col = c_yellow
            elif is_hover:
                bg_col = c_dark_hover
                border_col = c_cyan
                text_col = QColor("#FFFFFF")
            else:
                bg_col = c_dark_plate
                border_col = c_border_dim
                text_col = QColor("#D0D8E8")

        # 1. Fill base polygon
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.8))
        painter.drawPolygon(poly)

        # 3. Draw Icon & Text
        icon = btn.icon()
        text = btn.text()
        font = btn.font()
        font.setFamily("Segoe UI")
        font.setBold(True if (is_primary or is_checked) else False)
        painter.setFont(font)

        isize = btn.iconSize()
        has_icon = not icon.isNull() and isize.width() > 0
        has_text = bool(text)

        fm = painter.fontMetrics()
        t_width = fm.horizontalAdvance(text) if has_text else 0
        gap = 8 if (has_icon and has_text) else 0
        total_w = (isize.width() if has_icon else 0) + gap + t_width

        # Check if slashes fit comfortably without overlapping text
        has_slashes = is_primary and w >= 90 and (w - total_w) >= 36

        if has_slashes:
            start_x = max(10.0, ((w - 20) - total_w) / 2.0)
        else:
            start_x = max(8.0, (w - total_w) / 2.0)

        # 2. Edgerunner Anime Tech Details
        if is_enabled:
            if has_slashes:
                # Signature hazard slashes on right edge (Sandevistan style)
                painter.setPen(QPen(QColor(0, 0, 0, 175), 2.0))
                for i in range(3):
                    sx = w - 20 + i * 5
                    painter.drawLine(QPointF(sx, h - 10), QPointF(sx + 3.5, 10))
            elif is_checked and w >= 80:
                # Active neon accent line
                painter.setPen(QPen(c_yellow, 2.2))
                painter.drawLine(QPointF(w - 20, 3.5), QPointF(w - 6, 3.5))
            elif not is_ghost and not is_small and w >= 65:
                # Tech corner brackets (sharp cyber tick marks)
                tick_col = c_cyan if (is_hover or is_checked) else QColor("#2A3752")
                painter.setPen(QPen(tick_col, 1.8))
                # Top-left corner tick
                painter.drawLine(QPointF(cut, 0.5), QPointF(cut + 6, 0.5))
                painter.drawLine(QPointF(0.5, cut), QPointF(0.5, cut + 6))
                # Bottom-right corner tick
                painter.drawLine(QPointF(w - cut, h - 0.5), QPointF(w - cut - 6, h - 0.5))
                painter.drawLine(QPointF(w - 0.5, h - cut), QPointF(w - 0.5, h - cut - 6))

        if has_icon:
            pix = icon.pixmap(isize)
            icon_y = (h - isize.height()) / 2.0
            painter.drawPixmap(int(start_x), int(icon_y), pix)
            start_x += isize.width() + gap

        if has_text:
            painter.setPen(text_col)
            # Clip text within safe bounds
            text_rect = QRectF(start_x, 0, max(10.0, w - start_x - 6), h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class CyberpunkButtonFilter(QObject):
    """
    Application-level event filter that draws Edgerunner anime HUD buttons.
    Attached exclusively when the active theme is 'cyberpunk'.
    """

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            # Exclude sidebar nav items so their custom row layout & badges are preserved
            if obj.__class__.__name__ == "NavItem":
                return False

            ev_type = event.type()
            # Fast hover & press repaint trigger
            if ev_type in (QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                obj.update()

            if ev_type == QEvent.Type.Paint:
                painter = QPainter(obj)
                CyberpunkButtonPainter.paint_button(painter, obj)
                painter.end()
                return True # Event handled

        return super().eventFilter(obj, event)
