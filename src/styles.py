"""
Modern Dark Theme Design System for WorkBOXig.
Inspired by modern high-end developer and productivity tools (Linear, Things 3, Raycast, Vercel).
Carefully crafted for high contrast, clean typography, and zero CSS cascade bleed.
"""

DARK_COLORS = {
    # Backgrounds - Executive Slate/Zinc Dark Palette
    "bg_root": "#0A0B10",
    "bg_sidebar": "#0E1017",
    "bg_card": "#131622",
    "bg_card_hover": "#1A1E2E",
    "bg_card_selected": "#23293D",
    "bg_input": "#0E111A",
    "bg_popup": "#151825",
    
    # Borders - Hairline Precision
    "border_subtle": "#1E2335",
    "border_light": "#2B324B",
    "border_focus": "#6366F1",
    "border_glow": "rgba(99, 102, 241, 0.25)",
    
    # Primary & Accents
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_light": "#818CF8",
    "primary_subtle": "rgba(99, 102, 241, 0.12)",
    "primary_border": "rgba(99, 102, 241, 0.30)",
    
    "sky": "#38BDF8",
    "sky_subtle": "rgba(56, 189, 248, 0.12)",
    "emerald": "#10B981",
    "emerald_subtle": "rgba(16, 185, 129, 0.12)",
    "amber": "#F59E0B",
    "amber_subtle": "rgba(245, 158, 11, 0.12)",
    "rose": "#EF4444",
    "rose_subtle": "rgba(239, 68, 68, 0.12)",
    "purple": "#A855F7",
    "purple_subtle": "rgba(168, 85, 247, 0.12)",
    
    # Typography - HIGH CONTRAST DARK MODE
    "text_primary": "#FFFFFF",
    "text_secondary": "#CBD5E1",
    "text_muted": "#8A94A6",
    "text_dim": "#5E687A",
}

LIGHT_COLORS = {
    # Backgrounds - Soft, modern, comfortable off-white (Slate 50 / 100)
    "bg_root": "#F8FAFC",
    "bg_sidebar": "#F1F5F9",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F8FAFC",
    "bg_card_selected": "#E2E8F0",
    "bg_input": "#FFFFFF",
    "bg_popup": "#FFFFFF",
    
    # Borders - Crisp Slate 200 / 300
    "border_subtle": "#E2E8F0",
    "border_light": "#CBD5E1",
    "border_focus": "#4F46E5",
    "border_glow": "rgba(79, 70, 229, 0.25)",
    
    # Primary & Accents - Deep vibrant indigo with high contrast
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_light": "#6366F1",
    "primary_subtle": "rgba(79, 70, 229, 0.10)",
    "primary_border": "rgba(79, 70, 229, 0.30)",
    
    "sky": "#0284C7",
    "sky_subtle": "rgba(2, 132, 199, 0.12)",
    "emerald": "#059669",
    "emerald_subtle": "rgba(5, 150, 105, 0.12)",
    "amber": "#D97706",
    "amber_subtle": "rgba(217, 119, 6, 0.12)",
    "rose": "#DC2626",
    "rose_subtle": "rgba(220, 38, 38, 0.12)",
    "purple": "#9333EA",
    "purple_subtle": "rgba(147, 51, 234, 0.12)",
    
    # Typography - High contrast deep slate for light mode
    "text_primary": "#0F172A",
    "text_secondary": "#334155",
    "text_muted": "#64748B",
    "text_dim": "#94A3B8",
}

CYBERPUNK_COLORS = {
    # Backgrounds - Night City High-Tech Obsidian
    "bg_root": "#08090D",
    "bg_sidebar": "#0C0F17",
    "bg_card": "#111624",
    "bg_card_hover": "#182033",
    "bg_card_selected": "#212B45",
    "bg_input": "#0A0D15",
    "bg_popup": "#131826",
    
    # Borders - Sharp Cyber Tech Lines & Neon Hairlines
    "border_subtle": "#1C2438",
    "border_light": "#2A3754",
    "border_focus": "#00F0FF",
    "border_glow": "rgba(0, 240, 255, 0.35)",
    
    # Primary & Accents - Sandevistan Neon Yellow (#FCEE0A) & Hologram Cyan (#00F0FF)
    "primary": "#FCEE0A",
    "primary_hover": "#FFE500",
    "primary_light": "#FFF24A",
    "primary_subtle": "rgba(252, 238, 10, 0.12)",
    "primary_border": "rgba(252, 238, 10, 0.35)",
    
    "sky": "#00F0FF",
    "sky_subtle": "rgba(0, 240, 255, 0.15)",
    "emerald": "#00FF9F",
    "emerald_subtle": "rgba(0, 255, 159, 0.15)",
    "amber": "#FCEE0A",
    "amber_subtle": "rgba(252, 238, 10, 0.15)",
    "rose": "#FF0055",
    "rose_subtle": "rgba(255, 0, 85, 0.15)",
    "purple": "#9D00FF",
    "purple_subtle": "rgba(157, 0, 255, 0.15)",
    
    # Typography - High contrast Cyberpunk readability
    "text_primary": "#FFFFFF",
    "text_secondary": "#CFD7E6",
    "text_muted": "#8291A8",
    "text_dim": "#4A566E",
}

COLORS = dict(DARK_COLORS)
CURRENT_THEME = "dark"


def get_theme_stylesheet(theme_name: str = "dark") -> str:
    """Generates the full application QSS stylesheet for the given theme."""
    is_light = (theme_name == "light")
    is_cyber = (theme_name == "cyberpunk")
    
    if is_light:
        c = LIGHT_COLORS
        tooltip_bg = "#FFFFFF"
        tooltip_fg = "#0F172A"
        tooltip_bd = c['border_light']
        primary_btn_bg = "#4F46E5"
        primary_btn_fg = "#FFFFFF"
        primary_btn_hover = "#6366F1"
        primary_btn_pressed = "#4338CA"
        primary_btn_border = "rgba(255, 255, 255, 0.15)"
        selection_bg = "#4F46E5"
        selection_fg = "#FFFFFF"
        danger_fg = "#DC2626"
    elif is_cyber:
        c = CYBERPUNK_COLORS
        tooltip_bg = "#0C0F17"
        tooltip_fg = "#00F0FF"
        tooltip_bd = "#00F0FF"
        primary_btn_bg = "#FCEE0A"
        primary_btn_fg = "#000000"
        primary_btn_hover = "#FFE500"
        primary_btn_pressed = "#E6D100"
        primary_btn_border = "#FCEE0A"
        selection_bg = "#00F0FF"
        selection_fg = "#000000"
        danger_fg = "#FF0055"
    else:
        c = DARK_COLORS
        tooltip_bg = "#1A2030"
        tooltip_fg = "#FFFFFF"
        tooltip_bd = c['border_light']
        primary_btn_bg = "#4F46E5"
        primary_btn_fg = "#FFFFFF"
        primary_btn_hover = "#6366F1"
        primary_btn_pressed = "#4338CA"
        primary_btn_border = "rgba(255, 255, 255, 0.15)"
        selection_bg = "#6366F1"
        selection_fg = "#FFFFFF"
        danger_fg = "#EF4444"

    return f"""
/* Windows and Roots */
QMainWindow, QDialog {{
    background-color: {c['bg_root']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Segoe UI Emoji", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: {selection_bg};
    selection-color: {selection_fg};
}}

/* Transparent labels by default so they don't inherit QFrame borders or draw black boxes */
QLabel {{
    background-color: transparent;
    color: {c['text_primary']};
    border: none;
}}

/* ScrollBars - Minimalist & Smooth */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px 0px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {c['border_light']};
    min-height: 35px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_light']};
    min-width: 35px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* Buttons */
QPushButton {{
    background-color: {c['bg_card']};
    color: {c['text_secondary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 500;
    font-size: 13px;
    qproperty-iconSize: 18px 18px;
}}
QPushButton:hover {{
    background-color: {c['bg_card_hover']};
    border-color: {c['border_light']};
    color: {c['text_primary']};
}}
QPushButton:pressed {{
    background-color: {c['bg_card_selected']};
}}
QPushButton:disabled {{
    background-color: {c['bg_input']};
    color: {c['text_dim']};
    border-color: {c['border_subtle']};
}}

QPushButton#primary-btn {{
    background-color: {primary_btn_bg};
    color: {primary_btn_fg};
    border: 1px solid {primary_btn_border};
    font-weight: 700;
    border-radius: 8px;
}}
QPushButton#primary-btn:hover {{
    background-color: {primary_btn_hover};
    border-color: {primary_btn_hover};
}}
QPushButton#primary-btn:pressed {{
    background-color: {primary_btn_pressed};
}}

QPushButton#danger-btn {{
    background-color: {c['rose_subtle']};
    color: {danger_fg};
    border: 1px solid {c['rose']};
    border-radius: 8px;
}}
}}
QPushButton#danger-btn:hover {{
    background-color: {c['rose']};
    color: #FFFFFF;
    border-color: {c['rose']};
}}

QPushButton#ghost-btn {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {c['text_secondary']};
    padding: 6px 12px;
    border-radius: 6px;
}}
QPushButton#ghost-btn:hover {{
    background-color: {c['bg_card_hover']};
    color: {c['text_primary']};
    border-color: {c['border_subtle']};
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {c['border_light']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {c['primary']};
    background-color: {c['bg_card']};
}}
QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
    color: {c['text_dim']};
}}

/* ComboBox */
QComboBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    min-height: 24px;
}}
QComboBox:hover {{
    border-color: {c['border_light']};
}}
QComboBox:focus {{
    border: 1px solid {c['primary']};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}}
QComboBox QAbstractItemView {{
    background-color: {c['bg_popup']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 8px;
    selection-background-color: {c['primary_subtle']};
    selection-color: {c['primary']};
    padding: 6px;
    outline: none;
}}

/* Date, Time and SpinBox Inputs */
QTimeEdit, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 28px;
}}
QTimeEdit:hover, QDateEdit:hover, QDateTimeEdit:hover, QSpinBox:hover {{
    border-color: {c['border_light']};
}}
QTimeEdit:focus, QDateEdit:focus, QDateTimeEdit:focus, QSpinBox:focus {{
    border: 1px solid {c['primary']};
    background-color: {c['bg_card']};
}}
QTimeEdit::up-button, QTimeEdit::down-button,
QDateEdit::up-button, QDateEdit::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    width: 20px;
    background: transparent;
    border: none;
}}
QTimeEdit::up-button:hover, QTimeEdit::down-button:hover,
QDateEdit::up-button:hover, QDateEdit::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {c['bg_card_hover']};
    border-radius: 4px;
}}

/* CheckBoxes */
QCheckBox {{
    spacing: 10px;
    font-size: 13px;
    color: {c['text_primary']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1.8px solid {c['border_light']};
    background-color: {c['bg_input']};
}}
QCheckBox::indicator:hover {{
    border-color: {c['primary_light']};
    background-color: {c['bg_card_hover']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['emerald']};
    border-color: {c['emerald']};
}}

/* Lists & Trees */
QListWidget, QTreeWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListWidget::item, QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: 8px;
    margin-bottom: 3px;
    color: {c['text_primary']};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {c['bg_card_hover']};
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {c['bg_card_selected']};
    color: {c['text_primary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {tooltip_bg};
    color: {tooltip_fg};
    border: 1px solid {tooltip_bd};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Calendar Widget Specific Styling */
QCalendarWidget {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border_subtle']};
    border-radius: 12px;
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {c['bg_sidebar']};
    border-bottom: 1px solid {c['border_subtle']};
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    padding: 6px;
}}
QCalendarWidget QToolButton {{
    color: {c['text_primary']};
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    margin: 2px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 13px;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {c['bg_card_hover']};
    border-color: {c['border_subtle']};
}}
QCalendarWidget QMenu {{
    background-color: {c['bg_popup']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 8px;
    padding: 4px;
}}
QCalendarWidget QSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 6px;
    padding: 4px;
}}
QCalendarWidget QTableView {{
    background-color: {c['bg_card']};
    selection-background-color: {c['primary']};
    selection-color: #FFFFFF;
    gridline-color: {c['border_subtle']};
    border: none;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}}
QCalendarWidget QTableView QHeaderView::section {{
    background-color: {c['bg_sidebar']};
    color: {c['text_muted']};
    padding: 6px;
    border: none;
    font-weight: 600;
    font-size: 11px;
}}
"""


def set_active_theme(theme_name: str) -> str:
    """Updates COLORS in place and returns the new stylesheet."""
    global CURRENT_THEME
    CURRENT_THEME = theme_name
    if theme_name == "light":
        target = LIGHT_COLORS
    elif theme_name == "cyberpunk":
        target = CYBERPUNK_COLORS
    else:
        target = DARK_COLORS
    COLORS.clear()
    COLORS.update(target)
    return get_theme_stylesheet(theme_name)


THEME_STYLESHEET = get_theme_stylesheet("dark")
