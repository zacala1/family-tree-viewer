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

    showEvent가 호출될 때마다 widgets/animation의 fade_in_widget을 적용.
    중복 import 방지를 위해 lazy import.
    """

    def showEvent(self, event):
        super().showEvent(event)
        from ...utils.animation import fade_in_widget
        fade_in_widget(self)


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
