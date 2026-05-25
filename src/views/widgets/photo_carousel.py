"""사진 캐러셀 위젯.

detail_panel에서 분리. 사진 썸네일 + prev/next 네비게이션 + counter +
add/remove/set-primary 버튼. 파일 I/O는 host(detail_panel)가 수행하고
이 위젯은 표시·네비게이션·signal emit만 담당.
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...config import PHOTO_THUMBNAIL_SIZE
from ...i18n import tr
from ...utils import logger
from ...utils.photo_manager import load_thumbnail


class _ClickableLabel(QLabel):
    """클릭 가능한 QLabel — 썸네일 클릭 detection."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PhotoCarousel(QWidget):
    """사진 캐러셀 — 인물의 photo_paths를 표시·네비게이션.

    Signals:
        add_photo_requested(): 사용자가 + 버튼 클릭 (host가 파일 다이얼로그 처리)
        remove_photo_requested(str): 사용자가 - 버튼 클릭. 현재 표시 사진 path.
        set_primary_requested(str): 사용자가 ★ 버튼 클릭. 현재 표시 사진 path.
        photo_clicked(str): 썸네일 클릭 (lightbox 열기용). 현재 사진 path.
    """

    add_photo_requested = pyqtSignal()
    remove_photo_requested = pyqtSignal(str)
    set_primary_requested = pyqtSignal(str)
    photo_clicked = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._photo_paths: List[str] = []
        self._photo_index: int = 0
        self._is_editing: bool = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 썸네일
        self.photo_label = _ClickableLabel()
        self.photo_label.setObjectName("photoThumbnail")
        self.photo_label.setFixedSize(PHOTO_THUMBNAIL_SIZE, PHOTO_THUMBNAIL_SIZE)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setText(tr("label.no_photo"))
        self.photo_label.clicked.connect(self._on_photo_clicked)
        layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 네비게이션
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(30)
        self.prev_btn.setToolTip(tr("tooltip.previous_photo"))
        self.prev_btn.setAccessibleName(tr("tooltip.previous_photo"))
        self.prev_btn.clicked.connect(self._prev)
        nav_layout.addWidget(self.prev_btn)

        self.counter_label = QLabel("0 / 0")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setMinimumWidth(50)
        self.counter_label.setAccessibleName(tr("accessibility.photo_counter"))
        nav_layout.addWidget(self.counter_label)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(30)
        self.next_btn.setToolTip(tr("tooltip.next_photo"))
        self.next_btn.setAccessibleName(tr("tooltip.next_photo"))
        self.next_btn.clicked.connect(self._next)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)

        # add / remove / set primary
        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton(tr("button.select_photo"))
        self.select_btn.clicked.connect(self.add_photo_requested)
        btn_layout.addWidget(self.select_btn)

        self.remove_btn = QPushButton(tr("button.remove_photo"))
        self.remove_btn.clicked.connect(self._on_remove)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)

        self.primary_btn = QPushButton(tr("button.set_primary_photo"))
        self.primary_btn.setToolTip(tr("tooltip.set_primary_photo"))
        self.primary_btn.setAccessibleName(tr("button.set_primary_photo"))
        self.primary_btn.clicked.connect(self._on_set_primary)
        self.primary_btn.setEnabled(False)
        btn_layout.addWidget(self.primary_btn)

        layout.addLayout(btn_layout)

    # === Public API ===

    def set_photos(self, photo_paths: List[str]) -> None:
        """새 사진 목록 표시 + 인덱스 0으로 리셋."""
        self._photo_paths = list(photo_paths)
        self._photo_index = 0
        self._render()

    def set_editing(self, is_editing: bool) -> None:
        """edit mode — select/remove/primary 활성 상태 조정."""
        self._is_editing = is_editing
        self._update_button_states()

    def refresh(self) -> None:
        """photo_paths 변경 후 caller가 호출 — 현재 인덱스 보정 + 재렌더."""
        if self._photo_index >= len(self._photo_paths):
            self._photo_index = max(0, len(self._photo_paths) - 1)
        self._render()

    def jump_to_last(self) -> None:
        """사진 추가 직후 caller가 호출 — 새로 추가된 마지막 사진으로 점프."""
        if self._photo_paths:
            self._photo_index = len(self._photo_paths) - 1
        self._render()

    def jump_to_first(self) -> None:
        """set primary 후 caller가 호출 — 인덱스 0으로 (새 primary)."""
        self._photo_index = 0
        self._render()

    def current_photo(self) -> Optional[str]:
        """현재 표시 중인 사진 path. 없으면 None."""
        if not self._photo_paths:
            return None
        if self._photo_index >= len(self._photo_paths):
            self._photo_index = max(0, len(self._photo_paths) - 1)
        return self._photo_paths[self._photo_index]

    def current_index(self) -> int:
        return self._photo_index

    def total_count(self) -> int:
        return len(self._photo_paths)

    def update_ui_texts(self) -> None:
        """언어 변경 시 모든 라벨·툴팁·accessibleName 갱신."""
        self.select_btn.setText(tr("button.select_photo"))
        self.remove_btn.setText(tr("button.remove_photo"))
        self.primary_btn.setText(tr("button.set_primary_photo"))
        self.primary_btn.setToolTip(tr("tooltip.set_primary_photo"))
        self.primary_btn.setAccessibleName(tr("button.set_primary_photo"))
        self.prev_btn.setToolTip(tr("tooltip.previous_photo"))
        self.prev_btn.setAccessibleName(tr("tooltip.previous_photo"))
        self.next_btn.setToolTip(tr("tooltip.next_photo"))
        self.next_btn.setAccessibleName(tr("tooltip.next_photo"))
        self.counter_label.setAccessibleName(tr("accessibility.photo_counter"))
        if not self._photo_paths:
            self.photo_label.setText(tr("label.no_photo"))

    # === 핸들러 ===

    def _prev(self):
        if len(self._photo_paths) < 2:
            return
        self._photo_index = (self._photo_index - 1) % len(self._photo_paths)
        self._render()

    def _next(self):
        if len(self._photo_paths) < 2:
            return
        self._photo_index = (self._photo_index + 1) % len(self._photo_paths)
        self._render()

    def _on_remove(self):
        path = self.current_photo()
        if path and self._is_editing:
            self.remove_photo_requested.emit(path)

    def _on_set_primary(self):
        path = self.current_photo()
        if path and self._is_editing:
            self.set_primary_requested.emit(path)

    def _on_photo_clicked(self):
        path = self.current_photo()
        if path:
            self.photo_clicked.emit(path)

    # === 렌더링 ===

    def _render(self):
        """현재 인덱스의 썸네일 + 카운터 + 버튼 상태 모두 갱신."""
        path = self.current_photo()
        if path is None:
            self.photo_label.clear()
            self.photo_label.setText(tr("label.no_photo"))
            self.photo_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.photo_label.setToolTip("")
        else:
            thumb = load_thumbnail(path, PHOTO_THUMBNAIL_SIZE)
            if thumb:
                self.photo_label.setPixmap(thumb)
                self.photo_label.setCursor(Qt.CursorShape.PointingHandCursor)
                self.photo_label.setToolTip(tr("tooltip.click_to_enlarge"))
            else:
                self.photo_label.clear()
                self.photo_label.setText(tr("label.no_photo"))
                self.photo_label.setCursor(Qt.CursorShape.ArrowCursor)
                self.photo_label.setToolTip("")
                logger.warning(f"Failed to load photo: {path}")
        self._update_counter()
        self._update_button_states()

    def _update_counter(self):
        total = len(self._photo_paths)
        if total == 0:
            self.counter_label.setText("0 / 0")
        else:
            self.counter_label.setText(f"{self._photo_index + 1} / {total}")

    def _update_button_states(self):
        total = len(self._photo_paths)
        has_photo = total > 0
        self.prev_btn.setEnabled(total > 1)
        self.next_btn.setEnabled(total > 1)
        # select는 read-only가 아닐 때만
        self.select_btn.setEnabled(self._is_editing)
        self.remove_btn.setEnabled(self._is_editing and has_photo)
        # primary 변경: 편집 모드 + 2장 이상 + 현재가 primary가 아닐 때
        is_primary = self._photo_index == 0
        self.primary_btn.setEnabled(
            self._is_editing and total > 1 and not is_primary
        )
