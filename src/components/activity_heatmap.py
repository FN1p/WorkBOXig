"""
GitHub-Style Activity & Focus Heatmap Widget for WorkBOXig.
Visualizes daily focus sessions, completed tasks, and streak history across 16 weeks.
Includes Subject Study Distribution Breakdown.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGridLayout,
    QProgressBar, QToolTip
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QCursor

from src.styles import COLORS, CURRENT_THEME
from src.icons import get_pixmap, get_icon
from src.i18n import t, get_language
from src.storage import get_storage


class HeatmapCell(QWidget):
    """Single day square in the 16-week contribution calendar."""

    def __init__(self, date_str: str, score: int, pomos: int, tasks: int, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.score = score
        self.pomos = pomos
        self.tasks = tasks

        self.setFixedSize(14, 14)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_tooltip()

    def _update_tooltip(self):
        if self.score > 0:
            msg = t("heatmap_tooltip_format", date=self.date_str, score=self.score, pomos=self.pomos, tasks=self.tasks)
        else:
            msg = t("heatmap_tooltip_empty", date=self.date_str)
        self.setToolTip(msg)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = CURRENT_THEME
        # Determine level 0..4
        if self.score <= 0:
            level = 0
        elif self.score <= 3:
            level = 1
        elif self.score <= 6:
            level = 2
        elif self.score <= 9:
            level = 3
        else:
            level = 4

        # Colors by theme & level
        if theme == "light":
            palette = [
                QColor("#E2E8F0"),  # 0
                QColor("#9BE9A8"),  # 1
                QColor("#40C463"),  # 2
                QColor("#30A14E"),  # 3
                QColor("#216E39")   # 4
            ]
            border_col = QColor("#CBD5E1") if level == 0 else palette[level].darker(115)
        elif theme == "cyberpunk":
            palette = [
                QColor("#111726"),  # 0
                QColor("#064E3B"),  # 1
                QColor("#059669"),  # 2
                QColor("#10B981"),  # 3
                QColor("#00F0FF")   # 4 glowing cyan
            ]
            border_col = QColor("#1E293B") if level == 0 else palette[level]
        else:  # Dark / Slate
            palette = [
                QColor("#1E293B"),  # 0
                QColor("#0E4429"),  # 1
                QColor("#006D32"),  # 2
                QColor("#26A641"),  # 3
                QColor("#39D353")   # 4
            ]
            border_col = QColor("#334155") if level == 0 else palette[level].darker(110)

        fill_color = palette[level]

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_col, 1))
        painter.drawRoundedRect(rect, 3, 3)


class SubjectDistributionBar(QWidget):
    """Horizontal stacked proportion bar showing study time distribution per subject."""

    SUBJECT_COLORS = [
        "#6366F1", "#10B981", "#38BDF8", "#F59E0B",
        "#EC4899", "#A855F7", "#14B8A6", "#F97316"
    ]

    def __init__(self, distribution: Dict[str, int], parent=None):
        super().__init__(parent)
        self.distribution = distribution
        self.setFixedHeight(12)

    def set_data(self, distribution: Dict[str, int]):
        self.distribution = distribution
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        total_mins = sum(self.distribution.values())

        if total_mins <= 0:
            # Empty background
            painter.setBrush(QBrush(QColor(COLORS['bg_input'])))
            painter.setPen(QPen(QColor(COLORS['border_subtle']), 1))
            painter.drawRoundedRect(0, 0, w, h, 6, 6)
            return

        # Draw segmented rounded bar
        curr_x = 0
        segments = list(self.distribution.items())
        for idx, (subj, mins) in enumerate(segments):
            seg_w = int(round((mins / total_mins) * w))
            if idx == len(segments) - 1:
                seg_w = w - curr_x
            if seg_w <= 0:
                continue

            col_str = self.SUBJECT_COLORS[idx % len(self.SUBJECT_COLORS)]
            color = QColor(col_str)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(curr_x, 0, seg_w, h, 4, 4)
            curr_x += seg_w


class ActivityHeatmapWidget(QFrame):
    """Full 16-Week GitHub-style Activity Heatmap & Subject Distribution Card."""

    WEEKS_COUNT = 16

    def __init__(self, storage=None, parent=None):
        super().__init__(parent)
        self.storage = storage or get_storage()
        self.setObjectName("activity_heatmap_card")
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QFrame#activity_heatmap_card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 16, 18, 16)
        self.main_layout.setSpacing(12)

        # 1. Header with Title & Stats Pills
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("streak", COLORS['emerald'], 18))
        icon_lbl.setStyleSheet("background: transparent;")
        top_row.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.title_lbl = QLabel(t("section_heatmap_title"))
        self.title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        title_vbox.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(t("section_heatmap_sub"))
        self.sub_lbl.setFont(QFont("Segoe UI", 8))
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        title_vbox.addWidget(self.sub_lbl)
        top_row.addLayout(title_vbox)

        top_row.addStretch()

        # Stat Badge: Streak
        self.streak_badge = QLabel("")
        self.streak_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.streak_badge.setStyleSheet(f"""
            color: {COLORS['amber']};
            background-color: {COLORS['amber_subtle']};
            border: 1px solid rgba(245, 158, 11, 0.25);
            border-radius: 6px;
            padding: 2px 8px;
        """)
        top_row.addWidget(self.streak_badge)

        # Stat Badge: Total Contributions
        self.total_badge = QLabel("")
        self.total_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.total_badge.setStyleSheet(f"""
            color: {COLORS['emerald']};
            background-color: {COLORS['emerald_subtle']};
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 6px;
            padding: 2px 8px;
        """)
        top_row.addWidget(self.total_badge)

        self.main_layout.addLayout(top_row)

        # 2. Heatmap Grid Container
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 4, 0, 4)
        self.grid_layout.setSpacing(3)
        self.main_layout.addWidget(self.grid_container)

        # 3. Legend Row
        legend_row = QHBoxLayout()
        legend_row.setSpacing(6)

        legend_row.addStretch()
        less_lbl = QLabel(t("heatmap_less"))
        less_lbl.setFont(QFont("Segoe UI", 8))
        less_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        legend_row.addWidget(less_lbl)

        for lvl, score in enumerate([0, 2, 5, 8, 12]):
            sample = HeatmapCell("sample", score, 0, 0, self)
            sample.setToolTip("")
            legend_row.addWidget(sample)

        more_lbl = QLabel(t("heatmap_more"))
        more_lbl.setFont(QFont("Segoe UI", 8))
        more_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        legend_row.addWidget(more_lbl)
        self.main_layout.addLayout(legend_row)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {COLORS['border_subtle']}; margin: 2px 0;")
        self.main_layout.addWidget(div)

        # 4. Subject Study Distribution
        dist_top = QHBoxLayout()
        dist_icon = QLabel()
        dist_icon.setPixmap(get_pixmap("notes", COLORS['sky'], 14))
        dist_top.addWidget(dist_icon)

        self.dist_title = QLabel(t("subject_dist_title"))
        self.dist_title.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.dist_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        dist_top.addWidget(self.dist_title)
        dist_top.addStretch()
        self.main_layout.addLayout(dist_top)

        self.dist_bar = SubjectDistributionBar({}, self)
        self.main_layout.addWidget(self.dist_bar)

        self.dist_legend_layout = QHBoxLayout()
        self.dist_legend_layout.setSpacing(8)
        self.main_layout.addLayout(self.dist_legend_layout)

    def refresh_data(self):
        """Re-render heatmap grid and distribution stats from storage."""
        # 1. Clear previous cells in grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        activity = self.storage.get_activity_heatmap_data(weeks=self.WEEKS_COUNT)

        # Calculate current streak and total
        total_actions = sum(v.get("pomodoros", 0) + v.get("tasks", 0) for v in activity.values())
        streak = self._calculate_current_streak(activity)

        self.streak_badge.setText(t("heatmap_streak_label", count=streak))
        self.total_badge.setText(t("heatmap_total_label", count=total_actions))

        # 2. Setup 16-week date grid
        today = datetime.now().date()
        # End on this Sunday or today
        days_ahead = 6 - today.weekday()
        end_date = today + timedelta(days=days_ahead)
        start_date = end_date - timedelta(weeks=self.WEEKS_COUNT) + timedelta(days=1)

        # Row 0: Month labels
        is_en = (get_language() == "en")
        months = (
            ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            if is_en else
            ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
        )
        days_short = ["Mon", "Wed", "Fri"] if is_en else ["Пн", "Ср", "Пт"]

        # Day of week labels on column 0
        dow_rows = {0: days_short[0], 2: days_short[1], 4: days_short[2]}
        for r_idx, lbl_text in dow_rows.items():
            lbl = QLabel(lbl_text)
            lbl.setFont(QFont("Segoe UI", 7))
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding-right: 4px;")
            self.grid_layout.addWidget(lbl, r_idx + 1, 0, Qt.AlignmentFlag.AlignRight)

        # Iterate 16 weeks
        last_month = -1
        for col in range(self.WEEKS_COUNT):
            col_date = start_date + timedelta(weeks=col)
            # Check if new month starts in this week
            if col_date.month != last_month and col > 0:
                m_lbl = QLabel(months[col_date.month])
                m_lbl.setFont(QFont("Segoe UI", 7))
                m_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
                self.grid_layout.addWidget(m_lbl, 0, col + 1, Qt.AlignmentFlag.AlignLeft)
                last_month = col_date.month

            for row in range(7):  # Mon..Sun
                cell_date = start_date + timedelta(weeks=col, days=row)
                d_str = cell_date.strftime("%Y-%m-%d")

                data = activity.get(d_str, {"pomodoros": 0, "tasks": 0, "score": 0})
                cell = HeatmapCell(
                    date_str=d_str,
                    score=data.get("score", 0),
                    pomos=data.get("pomodoros", 0),
                    tasks=data.get("tasks", 0),
                    parent=self
                )
                self.grid_layout.addWidget(cell, row + 1, col + 1)

        # 3. Update Subject Distribution Bar
        dist = self.storage.get_subject_time_distribution()
        self.dist_bar.set_data(dist)

        # Clear distribution legend
        while self.dist_legend_layout.count():
            item = self.dist_legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not dist:
            empty_lbl = QLabel(t("no_dist_data"))
            empty_lbl.setFont(QFont("Segoe UI", 8))
            empty_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-style: italic;")
            self.dist_legend_layout.addWidget(empty_lbl)
        else:
            total_mins = sum(dist.values())
            for idx, (subj, mins) in enumerate(list(dist.items())[:5]):
                pct = int(round((mins / total_mins) * 100)) if total_mins > 0 else 0
                col_str = SubjectDistributionBar.SUBJECT_COLORS[idx % len(SubjectDistributionBar.SUBJECT_COLORS)]

                pill = QLabel(f"● {subj}: {mins} мин ({pct}%)")
                pill.setFont(QFont("Segoe UI", 8))
                pill.setStyleSheet(f"color: {col_str}; font-weight: 500;")
                self.dist_legend_layout.addWidget(pill)
            self.dist_legend_layout.addStretch()

    def _calculate_current_streak(self, activity: Dict[str, Dict[str, int]]) -> int:
        """Calculate continuous streak ending today or yesterday."""
        today = datetime.now().date()
        streak = 0
        cur = today
        # If no activity today, check yesterday
        if cur.strftime("%Y-%m-%d") not in activity or activity[cur.strftime("%Y-%m-%d")].get("score", 0) == 0:
            cur = today - timedelta(days=1)

        while True:
            d_str = cur.strftime("%Y-%m-%d")
            if d_str in activity and activity[d_str].get("score", 0) > 0:
                streak += 1
                cur = cur - timedelta(days=1)
            else:
                break
        return streak
