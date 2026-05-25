"""환영 다이얼로그 — 첫 실행 시 또는 Help → Welcome으로 표시.

핵심 기능 3-4개를 한 화면에 압축해 첫 사용자가 무엇을 할 수 있는지
파악할 수 있도록. F1 단축키 다이얼로그(reference)와는 다른 layer —
이것은 onboarding (어떤 기능이 있는지), 단축키 dialog는 reference
(어떻게 호출하는지).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..i18n import tr
from .widgets.base_dialog import AnimatedDialog


_SETTINGS_ORG = "FamilyTree"
_SETTINGS_APP = "FamilyTree"
_KEY_WELCOME_DISMISSED = "welcomeDismissed"


class WelcomeDialog(AnimatedDialog):
    """첫 실행 환영 + 핵심 기능 4개 카드 표시 (AnimatedDialog로 fade-in)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("welcome.title"))
        self.setMinimumSize(560, 480)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 20)

        # 제목
        title = QLabel(tr("welcome.heading"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 부제 (한 줄)
        subtitle = QLabel(tr("welcome.subtitle"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 핵심 기능 4개 (수직 카드)
        for i in range(1, 5):
            layout.addWidget(self._make_feature_row(
                tr(f"welcome.feature_{i}_title"),
                tr(f"welcome.feature_{i}_desc"),
            ))

        layout.addStretch()

        # "다시 보지 않기" 체크박스 + 시작 버튼
        bottom = QHBoxLayout()
        self.dont_show_check = QCheckBox(tr("welcome.dont_show_again"))
        self.dont_show_check.setChecked(True)  # 기본 체크 — 한 번 봤으면 충분
        bottom.addWidget(self.dont_show_check)
        bottom.addStretch()

        start_btn = QPushButton(tr("welcome.start_btn"))
        start_btn.setDefault(True)
        start_btn.clicked.connect(self.accept)
        bottom.addWidget(start_btn)

        layout.addLayout(bottom)

    @staticmethod
    def _make_feature_row(title: str, desc: str) -> QLabel:
        """기능 한 줄 — 굵은 제목 + 회색 설명."""
        from ..utils.theme_manager import get_theme_manager
        muted = get_theme_manager().get_tree_colors().get("text_muted", "#777")
        label = QLabel(
            f"<b>{title}</b><br/>"
            f"<span style='color: {muted}; font-size: 12px;'>{desc}</span>"
        )
        label.setWordWrap(True)
        return label

    def accept(self):
        """OK — 사용자 선호 저장."""
        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        settings.setValue(_KEY_WELCOME_DISMISSED, self.dont_show_check.isChecked())
        super().accept()



# === 모듈 레벨 helpers ===

def should_show_welcome() -> bool:
    """첫 실행 또는 dismiss 안 했으면 True."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    dismissed = settings.value(_KEY_WELCOME_DISMISSED, False, type=bool)
    return not dismissed


def reset_welcome_dismissed() -> None:
    """테스트/사용자 요청 시 dismissed flag 초기화."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    settings.setValue(_KEY_WELCOME_DISMISSED, False)
