"""AnimatedDialog + ClickDismissMixin base 패턴 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtCore import QEvent, QPointF


class TestAnimatedDialog:
    def test_show_attaches_fade(self, qapp):
        from src.views.widgets.base_dialog import AnimatedDialog
        dlg = AnimatedDialog()
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()

    def test_event_dialog_inherits_fade(self, qapp):
        from src.views.event_dialog import EventDialog
        dlg = EventDialog()
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()

    def test_welcome_dialog_inherits_fade(self, qapp):
        from src.views.welcome_dialog import WelcomeDialog
        dlg = WelcomeDialog()
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()


class TestClickDismissMixin:
    def test_left_click_accepts(self, qapp):
        from src.views.widgets.base_dialog import (
            AnimatedDialog,
            ClickDismissMixin,
        )

        class TestDialog(ClickDismissMixin, AnimatedDialog):
            pass

        dlg = TestDialog()
        # 좌클릭 시뮬레이션 — accept() 호출 → result()=Accepted
        evt = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            QPointF(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        dlg.mousePressEvent(evt)
        assert dlg.result() == dlg.DialogCode.Accepted
        dlg.deleteLater()

    def test_esc_key_accepts(self, qapp):
        from src.views.widgets.base_dialog import (
            AnimatedDialog,
            ClickDismissMixin,
        )

        class TestDialog(ClickDismissMixin, AnimatedDialog):
            pass

        dlg = TestDialog()
        evt = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        dlg.keyPressEvent(evt)
        assert dlg.result() == dlg.DialogCode.Accepted
        dlg.deleteLater()

    def test_non_esc_key_does_not_close(self, qapp):
        from src.views.widgets.base_dialog import (
            AnimatedDialog,
            ClickDismissMixin,
        )

        class TestDialog(ClickDismissMixin, AnimatedDialog):
            pass

        dlg = TestDialog()
        evt = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
        )
        dlg.keyPressEvent(evt)
        # A 키는 close 트리거 안 함
        assert dlg.result() != dlg.DialogCode.Accepted
        dlg.deleteLater()


class TestPhotoLightboxUsesBaseDialog:
    def test_lightbox_is_animated_and_click_dismissable(self, qapp, tmp_path):
        from src.views.detail_panel import _PhotoLightbox
        from src.views.widgets.base_dialog import (
            AnimatedDialog,
            ClickDismissMixin,
        )

        # mock image
        from PIL import Image
        img_path = tmp_path / "x.png"
        Image.new("RGB", (10, 10)).save(img_path)

        dlg = _PhotoLightbox(str(img_path), "test")
        try:
            assert isinstance(dlg, AnimatedDialog)
            assert isinstance(dlg, ClickDismissMixin)
        finally:
            dlg.deleteLater()
