"""다이얼로그 공통 base class.

여러 다이얼로그가 반복하던 showEvent fade-in과 클릭/Esc 닫기 패턴을
한 곳에 모음. QDialog를 직접 상속하는 대신 이 base class를 상속하면
fade-in이 자동 적용되고, 필요 시 mixin으로 click-to-dismiss를 켤 수 있음.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog


class AnimatedDialog(QDialog):
    """QDialog + 자동 fade-in.

    첫 show 시에만 fade_in_widget을 적용. show/hide 반복 시 애니메이션이
    중복 누적되지 않도록 `_fade_in_done` flag로 1회만 발화. (대부분의
    dialog는 한 번 띄우고 닫기 때문에 충분; 반복 표시 다이얼로그를 위해
    재발화가 필요하면 `_fade_in_done = False`로 명시 reset.)
    """

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_fade_in_done", False):
            from ...utils.animation import fade_in_widget
            fade_in_widget(self)
            self._fade_in_done = True


class ClickDismissMixin:
    """좌클릭과 Esc 키로 다이얼로그를 닫는 mixin.

    PhotoLightbox 같은 풀스크린 미리보기 dialog 용도. QDialog 또는
    AnimatedDialog와 함께 사용:

        class PhotoLightbox(ClickDismissMixin, AnimatedDialog):
            ...

    MRO 상 mixin이 앞에 와야 mousePressEvent/keyPressEvent가 먼저 잡힘.
    """

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
            return
        super().keyPressEvent(event)
