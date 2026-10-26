"""A short, actionable introduction for a new workspace."""

from datetime import date, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

from src.i18n import t
from src.styles import COLORS


class OnboardingDialog(QDialog):
    page_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("onboarding_title"))
        self.setMinimumWidth(560)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(16)

        title = QLabel(t("onboarding_title"))
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        intro = QLabel(t("onboarding_intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(intro)

        for number, key, page in (
            (1, "task", "tasks"),
            (2, "notebook", "notebooks"),
            (3, "calendar", "calendar"),
        ):
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border_subtle']}; border-radius: 10px; }}")
            row = QHBoxLayout(card)
            row.setContentsMargins(14, 12, 14, 12)
            copy = QVBoxLayout()
            heading = QLabel(f"{number}. {t('onboarding_' + key + '_title')}")
            heading.setStyleSheet(f"font-weight: 700; color: {COLORS['text_primary']}; border: none;")
            detail = QLabel(t("onboarding_" + key + "_desc"))
            detail.setWordWrap(True)
            detail.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
            copy.addWidget(heading)
            copy.addWidget(detail)
            row.addLayout(copy, 1)
            button = QPushButton(t("onboarding_open"))
            button.setAccessibleName(t("onboarding_open") + " " + heading.text())
            button.clicked.connect(lambda _checked=False, tab=page: self._open(tab))
            row.addWidget(button)
            layout.addWidget(card)

        example = QLabel(t("onboarding_quick_example", date=(date.today() + timedelta(days=1)).isoformat()))
        example.setWordWrap(True)
        example.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(example)
        footer = QHBoxLayout()
        footer.addStretch()
        done = QPushButton(t("onboarding_done"))
        done.setObjectName("primary-btn")
        done.clicked.connect(self.accept)
        footer.addWidget(done)
        layout.addLayout(footer)

    def _open(self, page):
        self.page_requested.emit(page)
        self.accept()
